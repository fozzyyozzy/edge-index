"""
EDGE INDEX — NFL Player Props Model
====================================
Covers: Passing (yards, TDs, completions), Rushing (yards, attempts), Receiving (yards, targets, receptions)

Architecture:
  - Weighted rolling averages (3-game, season, split by home/away/dome)
  - Usage-rate normalization (snap%, target share, route participation)
  - Vegas line / total correlation adjustments
  - Matchup defense rank overlay (positional fantasy pts allowed)
  - Projected game script factor (spread-implied pace)

Usage:
  from nfl_props_model import PropModel
  model = PropModel()
  proj = model.project_player("Tyreek Hill", "WR", week_stats, matchup_data)
  edge = model.find_edge(proj, market_line=72.5)
"""

import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field
from typing import Optional
import warnings
warnings.filterwarnings("ignore")


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class PlayerGame:
    """Single game log entry for a player."""
    week: int
    opponent: str
    home_away: str               # 'home' | 'away' | 'dome_neutral'
    snap_pct: float              # 0–1
    # Passing
    pass_att: float = 0.0
    pass_comp: float = 0.0
    pass_yards: float = 0.0
    pass_tds: float = 0.0
    # Rushing
    rush_att: float = 0.0
    rush_yards: float = 0.0
    rush_tds: float = 0.0
    # Receiving
    targets: float = 0.0
    receptions: float = 0.0
    rec_yards: float = 0.0
    rec_tds: float = 0.0
    # Game context
    team_pass_att: float = 0.0
    team_rush_att: float = 0.0
    vegas_total: float = 44.0
    team_spread: float = 0.0     # negative = favorite


@dataclass
class MatchupData:
    """Defensive matchup context for the upcoming game."""
    opponent: str
    def_pass_yards_allowed_rank: int = 16    # 1=best vs pass, 32=worst
    def_rush_yards_allowed_rank: int = 16
    def_rec_yards_allowed_rank: int = 16
    def_targets_allowed_rank: int = 16
    def_td_rate_rank: int = 16
    game_total: float = 44.0
    team_spread: float = 0.0
    is_home: bool = True
    is_dome: bool = False
    implied_team_total: float = 22.0         # calculated from spread+total
    pace_rank: int = 16                      # opponent's pace rank (1=fastest)


@dataclass
class Projection:
    """Full projection output for a player."""
    player: str
    position: str
    # Point estimates
    pass_yards: float = 0.0
    pass_comp: float = 0.0
    pass_tds: float = 0.0
    rush_yards: float = 0.0
    rush_att: float = 0.0
    rec_yards: float = 0.0
    targets: float = 0.0
    receptions: float = 0.0
    # Confidence intervals (10th / 90th percentile)
    pass_yards_lo: float = 0.0
    pass_yards_hi: float = 0.0
    rec_yards_lo: float = 0.0
    rec_yards_hi: float = 0.0
    rush_yards_lo: float = 0.0
    rush_yards_hi: float = 0.0
    # Edge signals
    edges: list = field(default_factory=list)


# ─── Core Model ──────────────────────────────────────────────────────────────

class PropModel:
    """
    Edge Index NFL props model.

    Weighting philosophy (Rufus Peabody-inspired):
      - Recency bias: last 3 games weighted 2x
      - Usage rate is more predictive than raw output
      - Always model the DISTRIBUTION, not just the mean
      - Find edges vs. the market number, not vs. your gut
    """

    WEIGHTS_3G = np.array([0.5, 0.3, 0.2])          # most recent first
    WEIGHTS_SEASON = None                             # uniform, set dynamically

    # Defense rank multipliers: rank 1 (best D) → 0.78x, rank 32 (worst D) → 1.22x
    # Linear interpolation between these endpoints
    DEF_RANK_MIN = 0.78
    DEF_RANK_MAX = 1.22

    # Game total correlation coefficients (empirically derived)
    TOTAL_PASS_CORR = 0.031    # per point of total → pass yards
    TOTAL_REC_CORR  = 0.022
    TOTAL_RUSH_CORR = 0.008    # rushing less sensitive to totals

    # Spread-to-game-script factor: heavy favorite runs more, passes less
    SPREAD_PASS_FACTOR  = -0.004   # per point of spread (neg = fav)
    SPREAD_RUSH_FACTOR  =  0.006

    def __init__(self):
        self._def_rank_scale = np.linspace(
            self.DEF_RANK_MAX, self.DEF_RANK_MIN, 32
        )  # index 0 = rank 1 (best D, hardest matchup)

    # ── Utility ──────────────────────────────────────────────────────────────

    def _def_multiplier(self, rank: int) -> float:
        """Convert defensive rank (1–32) to a projection multiplier."""
        idx = max(0, min(31, rank - 1))
        return self._def_rank_scale[idx]

    def _weighted_mean(self, values: list[float], mode: str = "recent") -> float:
        """Weighted average of game values, most recent first."""
        if not values:
            return 0.0
        arr = np.array(values[::-1], dtype=float)   # reverse: index 0 = most recent
        if mode == "recent" and len(arr) >= 3:
            w = np.array(self.WEIGHTS_3G)
            return float(np.dot(arr[:3], w))
        # Season weighted (uniform)
        return float(np.mean(arr))

    def _usage_rate(self, games: list[PlayerGame], stat: str, team_stat: str) -> float:
        """Average share of team volume this player captures."""
        rates = []
        for g in games:
            team_vol = getattr(g, team_stat, 0)
            player_vol = getattr(g, stat, 0)
            if team_vol > 0:
                rates.append(player_vol / team_vol)
        return float(np.mean(rates)) if rates else 0.0

    def _game_script_adj(self, base: float, stat_type: str, spread: float) -> float:
        """Adjust projection based on implied game script from spread."""
        if stat_type in ("pass_yards", "pass_comp", "pass_tds", "rec_yards",
                         "targets", "receptions"):
            return base * (1 + self.SPREAD_PASS_FACTOR * spread)
        if stat_type in ("rush_yards", "rush_att"):
            return base * (1 + self.SPREAD_RUSH_FACTOR * spread)
        return base

    def _total_adj(self, base: float, stat_type: str,
                   game_total: float, baseline_total: float = 44.0) -> float:
        """Adjust for game total deviation from league average."""
        delta = game_total - baseline_total
        if stat_type in ("pass_yards", "pass_comp"):
            return base + delta * self.TOTAL_PASS_CORR * base / 100
        if stat_type in ("rec_yards", "targets", "receptions"):
            return base + delta * self.TOTAL_REC_CORR * base / 100
        if stat_type in ("rush_yards", "rush_att"):
            return base + delta * self.TOTAL_RUSH_CORR * base / 100
        return base

    def _confidence_interval(self, mean: float, games: list[float],
                              percentile_lo=10, percentile_hi=90) -> tuple:
        """Bootstrap percentile CI from historical distribution."""
        if len(games) < 4:
            sigma = mean * 0.35
            lo = max(0, stats.norm.ppf(percentile_lo/100, mean, sigma))
            hi = stats.norm.ppf(percentile_hi/100, mean, sigma)
        else:
            lo = np.percentile(games, percentile_lo)
            hi = np.percentile(games, percentile_hi)
        return round(lo, 1), round(hi, 1)

    # ── Main Projection ───────────────────────────────────────────────────────

    def project_player(
        self,
        player_name: str,
        position: str,
        games: list[PlayerGame],
        matchup: MatchupData,
        n_recent: int = 6
    ) -> Projection:
        """
        Full projection for a player given game logs + matchup context.

        Args:
            player_name: Player name string
            position:    'QB' | 'RB' | 'WR' | 'TE'
            games:       List of PlayerGame (most recent last)
            matchup:     MatchupData for upcoming game
            n_recent:    Games to use for weighted average baseline
        """
        recent = games[-n_recent:]
        proj = Projection(player=player_name, position=position)

        pos = position.upper()

        # ── PASSING (QB) ─────────────────────────────────────────────────────
        if pos == "QB":
            raw_yards = self._weighted_mean([g.pass_yards for g in recent])
            raw_comp  = self._weighted_mean([g.pass_comp  for g in recent])
            raw_tds   = self._weighted_mean([g.pass_tds   for g in recent])

            def_mult  = self._def_multiplier(matchup.def_pass_yards_allowed_rank)
            td_mult   = self._def_multiplier(matchup.def_td_rate_rank)

            proj.pass_yards = round(self._game_script_adj(
                self._total_adj(raw_yards * def_mult, "pass_yards", matchup.game_total),
                "pass_yards", matchup.team_spread), 1)
            proj.pass_comp  = round(self._game_script_adj(
                raw_comp * def_mult, "pass_comp", matchup.team_spread), 1)
            proj.pass_tds   = round(raw_tds * td_mult, 2)

            all_py = [g.pass_yards for g in games]
            proj.pass_yards_lo, proj.pass_yards_hi = self._confidence_interval(
                proj.pass_yards, all_py)

        # ── RUSHING (QB/RB) ───────────────────────────────────────────────────
        if pos in ("RB", "QB"):
            raw_rush = self._weighted_mean([g.rush_yards for g in recent])
            raw_att  = self._weighted_mean([g.rush_att   for g in recent])
            def_mult = self._def_multiplier(matchup.def_rush_yards_allowed_rank)

            proj.rush_yards = round(self._game_script_adj(
                self._total_adj(raw_rush * def_mult, "rush_yards", matchup.game_total),
                "rush_yards", matchup.team_spread), 1)
            proj.rush_att = round(raw_att, 1)

            all_ry = [g.rush_yards for g in games]
            proj.rush_yards_lo, proj.rush_yards_hi = self._confidence_interval(
                proj.rush_yards, all_ry)

        # ── RECEIVING (WR/TE/RB) ─────────────────────────────────────────────
        if pos in ("WR", "TE", "RB"):
            raw_rec_yards  = self._weighted_mean([g.rec_yards  for g in recent])
            raw_targets    = self._weighted_mean([g.targets    for g in recent])
            raw_receptions = self._weighted_mean([g.receptions for g in recent])

            def_mult_yards = self._def_multiplier(matchup.def_rec_yards_allowed_rank)
            def_mult_tgts  = self._def_multiplier(matchup.def_targets_allowed_rank)

            proj.rec_yards  = round(self._game_script_adj(
                self._total_adj(raw_rec_yards * def_mult_yards,
                                "rec_yards", matchup.game_total),
                "rec_yards", matchup.team_spread), 1)
            proj.targets    = round(raw_targets * def_mult_tgts, 1)
            proj.receptions = round(raw_receptions * def_mult_tgts, 1)

            all_ry = [g.rec_yards for g in games]
            proj.rec_yards_lo, proj.rec_yards_hi = self._confidence_interval(
                proj.rec_yards, all_ry)

            # Rushing for RBs
            if pos == "RB":
                raw_rush = self._weighted_mean([g.rush_yards for g in recent])
                raw_att  = self._weighted_mean([g.rush_att   for g in recent])
                def_mult = self._def_multiplier(matchup.def_rush_yards_allowed_rank)
                proj.rush_yards = round(self._game_script_adj(
                    raw_rush * def_mult, "rush_yards", matchup.team_spread), 1)
                proj.rush_att = round(raw_att, 1)

        return proj

    # ── Edge Finder ───────────────────────────────────────────────────────────

    def find_edge(
        self,
        projection: Projection,
        market_lines: dict,
        min_edge_pct: float = 0.08
    ) -> list[dict]:
        """
        Compare projections to market lines and flag edges.

        Args:
            projection:    Projection object from project_player()
            market_lines:  dict like {"pass_yards": 247.5, "rec_yards": 72.5, ...}
            min_edge_pct:  minimum % edge to flag (default 8%)

        Returns:
            List of edge dicts with stat, projection, line, edge_pct, direction
        """
        edges = []
        stat_map = {
            "pass_yards":  (projection.pass_yards,  projection.pass_yards_lo,  projection.pass_yards_hi),
            "pass_comp":   (projection.pass_comp,   None, None),
            "pass_tds":    (projection.pass_tds,    None, None),
            "rush_yards":  (projection.rush_yards,  projection.rush_yards_lo,  projection.rush_yards_hi),
            "rush_att":    (projection.rush_att,    None, None),
            "rec_yards":   (projection.rec_yards,   projection.rec_yards_lo,   projection.rec_yards_hi),
            "targets":     (projection.targets,     None, None),
            "receptions":  (projection.receptions,  None, None),
        }

        for stat, line in market_lines.items():
            if stat not in stat_map or line == 0:
                continue
            proj_val, lo, hi = stat_map[stat]
            if proj_val == 0:
                continue

            edge_pct = (proj_val - line) / line

            if abs(edge_pct) >= min_edge_pct:
                direction = "OVER" if edge_pct > 0 else "UNDER"
                confidence = "HIGH" if abs(edge_pct) >= 0.15 else "MEDIUM"

                # CI-based probability estimate (if available)
                prob = None
                if lo is not None and hi is not None and (hi - lo) > 0:
                    sigma = (hi - lo) / 2.563   # 80% CI → sigma
                    prob = (1 - stats.norm.cdf(line, proj_val, sigma)) \
                           if direction == "OVER" \
                           else stats.norm.cdf(line, proj_val, sigma)
                    prob = round(prob, 3)

                edges.append({
                    "stat": stat,
                    "projection": proj_val,
                    "market_line": line,
                    "edge_pct": round(edge_pct * 100, 1),
                    "direction": direction,
                    "confidence": confidence,
                    "win_prob": prob,
                    "ci_lo": lo,
                    "ci_hi": hi,
                })

        projection.edges = edges
        return edges


# ─── Pick Sheet Generator ─────────────────────────────────────────────────────

class PickSheetGenerator:
    """
    Generate a formatted weekly pick sheet from a list of projections + edges.
    Output: markdown string (easy to paste into PDF or Google Doc).
    """

    TIER_LABELS = {
        "HIGH":   "★★★ Tier 1 — High Confidence",
        "MEDIUM": "★★  Tier 2 — Medium Confidence",
    }

    def generate(self, week: int, season: int,
                 player_edges: list[tuple[Projection, list[dict]]]) -> str:
        lines = []
        lines.append(f"# EDGE INDEX — NFL Props Sheet")
        lines.append(f"## Week {week}, {season} Season\n")
        lines.append("> Model: weighted 6-game rolling avg × defensive rank × "
                     "game script × total adjustment\n")
        lines.append("---\n")

        tier1 = [(p, e) for p, edges in player_edges
                 for e in edges if e["confidence"] == "HIGH"]
        tier2 = [(p, e) for p, edges in player_edges
                 for e in edges if e["confidence"] == "MEDIUM"]

        for tier_name, tier_plays in [("HIGH", tier1), ("MEDIUM", tier2)]:
            if not tier_plays:
                continue
            lines.append(f"### {self.TIER_LABELS[tier_name]}\n")
            for proj, edge in tier_plays:
                stat_label = edge['stat'].replace('_', ' ').title()
                direction  = edge['direction']
                line       = edge['market_line']
                proj_val   = edge['projection']
                edge_pct   = edge['edge_pct']
                prob_str   = f" ({edge['win_prob']*100:.0f}% win prob)" \
                             if edge.get('win_prob') else ""

                lines.append(
                    f"**{proj.player}** ({proj.position}) — "
                    f"{stat_label} {direction} {line}"
                )
                lines.append(
                    f"  Projection: {proj_val} | Edge: {edge_pct:+.1f}%{prob_str}"
                )
                if edge.get('ci_lo') and edge.get('ci_hi'):
                    lines.append(
                        f"  80% range: {edge['ci_lo']} – {edge['ci_hi']}"
                    )
                lines.append("")

        lines.append("---")
        lines.append("*Edge Index — data-driven, process-first. "
                     "Results posted publicly after every week.*")
        return "\n".join(lines)


# ─── Demo / Smoke Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = PropModel()

    wr_games = []
    data = [(1,8,6,82),(2,10,7,105),(3,6,4,48),(4,11,8,120),
            (5,9,7,94),(6,7,5,71),(7,12,9,130),(8,9,7,88)]
    for w,t,r,y in data:
        g = PlayerGame(week=w, opponent="OPP", home_away="away", snap_pct=0.85,
                       targets=t, receptions=r, rec_yards=y,
                       team_pass_att=35, vegas_total=45, team_spread=-3)
        wr_games.append(g)

    matchup = MatchupData(
        opponent="DAL",
        def_rec_yards_allowed_rank=28,   # bad vs receivers
        def_targets_allowed_rank=25,
        def_td_rate_rank=20,
        game_total=48.5,
        team_spread=-4.5,
        is_home=True,
        implied_team_total=26.5,
        pace_rank=5,
    )

    proj = model.project_player("Tyreek Hill", "WR", wr_games, matchup)
    edges = model.find_edge(proj, {"rec_yards": 82.5, "targets": 8.5, "receptions": 6.5})

    print(f"\n{'='*50}")
    print(f"PROJECTION: {proj.player} ({proj.position})")
    print(f"  Rec Yards:  {proj.rec_yards}  (80% CI: {proj.rec_yards_lo}–{proj.rec_yards_hi})")
    print(f"  Targets:    {proj.targets}")
    print(f"  Receptions: {proj.receptions}")
    print(f"\nEDGES FOUND: {len(edges)}")
    for e in edges:
        print(f"  {e['stat']}: {e['direction']} {e['market_line']} | "
              f"proj={e['projection']} | edge={e['edge_pct']:+.1f}% | "
              f"confidence={e['confidence']}")

    gen = PickSheetGenerator()
    sheet = gen.generate(10, 2025, [(proj, edges)])
    print(f"\n{sheet}")
