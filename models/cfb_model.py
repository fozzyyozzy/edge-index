"""
EDGE INDEX — College Football Prediction Model
===============================================
Covers: Spread betting, game totals, team efficiency edges

Architecture:
  - SP+ / team efficiency rating integration (KenPom-style for CFB)
  - Home field advantage calibration by conference and venue type
  - Garbage time filtering (score-adjusted efficiency)
  - Tempo-adjusted pace for total projections
  - Line movement correlation (sharp vs. public money signals)

Usage:
    from cfb_model import CFBModel
    model = CFBModel()
    game_proj = model.project_game(home_team_data, away_team_data, game_context)
    edge = model.find_spread_edge(game_proj, market_spread=-7.0)
"""

import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field
from typing import Optional
import warnings
warnings.filterwarnings("ignore")


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class TeamData:
    """Season-to-date efficiency ratings and stats for a CFB team."""
    name: str
    conference: str                      # 'SEC','B1G','B12','ACC','P12','Ind','GRP5'

    # Efficiency ratings (SP+ style, points above average vs. avg opponent)
    off_efficiency: float = 0.0          # offensive SP+ rating
    def_efficiency: float = 0.0          # defensive SP+ rating (negative = good D)
    st_efficiency: float = 0.0           # special teams

    # Raw averages (garbage-time adjusted)
    points_per_game: float = 28.0
    points_allowed: float = 24.0
    yards_per_play_off: float = 5.5
    yards_per_play_def: float = 5.5
    plays_per_game: float = 70.0         # pace proxy

    # Situational splits
    home_off_boost: float = 0.0          # additional pts/game at home
    away_off_drop: float = 0.0           # reduction away from home
    night_game_factor: float = 0.0       # SEC night game factor etc.

    # Recent form (last 3 games, score-adjusted)
    recent_form_delta: float = 0.0       # + = trending up, - = trending down

    # ATS record for line-value context
    ats_record: tuple = (0, 0, 0)        # W-L-P ATS
    ou_record:  tuple = (0, 0, 0)        # O-U-P


@dataclass
class GameContext:
    """Game-level context for an upcoming CFB matchup."""
    home_team: str
    away_team: str
    neutral_site: bool = False
    dome: bool = False
    night_game: bool = False
    rivalry_game: bool = False           # rivalry games tighten against spread
    conference_game: bool = True
    bowl_game: bool = False
    # Vegas context
    open_spread: float = 0.0             # home team perspective (neg = home fav)
    current_spread: float = 0.0
    open_total: float = 44.0
    current_total: float = 44.0
    # Line movement
    spread_moved_toward_home: bool = False
    total_moved_up: bool = False


@dataclass
class GameProjection:
    """Projected outcome for a CFB game."""
    home_team: str
    away_team: str
    proj_home_score: float = 0.0
    proj_away_score: float = 0.0
    proj_total: float = 0.0
    proj_spread: float = 0.0             # from home team perspective
    # Confidence
    spread_sigma: float = 14.0           # std dev of CFB game outcomes
    home_win_prob: float = 0.5
    cover_prob: float = 0.5              # prob home team covers market spread
    over_prob: float = 0.5
    edges: list = field(default_factory=list)


# ─── Home Field Advantage by Conference ───────────────────────────────────────

HFA_BY_CONF = {
    "SEC":  2.8,
    "B1G":  2.6,
    "B12":  2.4,
    "ACC":  2.3,
    "P12":  2.5,
    "Ind":  2.5,   # Notre Dame etc.
    "GRP5": 2.2,
}

# Night game bonus by conference (crowd energy, tradition)
NIGHT_GAME_BONUS = {
    "SEC": 1.5,   # Death Valley, Swamp, etc.
    "B1G": 0.8,
    "B12": 0.7,
    "default": 0.5,
}


# ─── Core Model ───────────────────────────────────────────────────────────────

class CFBModel:
    """
    Edge Index CFB prediction model.

    Philosophy:
      - Efficiency ratings beat box scores for future prediction
      - Garbage-time filtering is non-negotiable for accuracy
      - Home field is real but conference-specific
      - Line movement is signal, not noise
    """

    BASE_HFA = 2.5          # baseline home field pts before conf adjustment
    SPREAD_SIGMA = 13.5     # historical std dev of CFB margin outcomes
    TOTAL_SIGMA  = 9.2      # std dev of total outcomes

    # Regression weights: efficiency vs. raw averages
    EFF_WEIGHT  = 0.65
    RAW_WEIGHT  = 0.35

    # Form factor: recent 3-game delta contribution
    FORM_WEIGHT = 0.12

    def __init__(self):
        pass

    # ── Utility ──────────────────────────────────────────────────────────────

    def _get_hfa(self, team: TeamData, context: GameContext) -> float:
        """Calculate home field advantage for this specific game."""
        if context.neutral_site:
            return 0.0
        base = HFA_BY_CONF.get(team.conference, self.BASE_HFA)
        if context.dome:
            base *= 0.75     # dome reduces crowd-noise advantage
        night_bonus = NIGHT_GAME_BONUS.get(
            team.conference, NIGHT_GAME_BONUS["default"]
        ) if context.night_game else 0.0
        rivalry_adj = -0.5 if context.rivalry_game else 0.0  # tighter games
        return base + night_bonus + rivalry_adj

    def _blended_rating(self, team: TeamData, side: str = "off") -> float:
        """Blend efficiency rating with raw averages for robustness."""
        if side == "off":
            eff_pts  = team.off_efficiency
            raw_pts  = team.points_per_game - 28.0   # delta vs. avg
        else:
            eff_pts  = -team.def_efficiency          # flip: better D = positive
            raw_pts  = 24.0 - team.points_allowed    # delta vs. avg
        blended = (self.EFF_WEIGHT * eff_pts) + (self.RAW_WEIGHT * raw_pts)
        blended += team.recent_form_delta * self.FORM_WEIGHT
        return blended

    def _tempo_total_adj(self, home: TeamData, away: TeamData) -> float:
        """Adjust projected total based on pace interaction."""
        avg_pace = 70.0
        home_pace_delta = home.plays_per_game - avg_pace
        away_pace_delta = away.plays_per_game - avg_pace
        combined_pace   = (home_pace_delta + away_pace_delta) / 2
        # Each additional play worth ~0.35 pts to total
        return combined_pace * 0.35

    # ── Main Projection ───────────────────────────────────────────────────────

    def project_game(
        self,
        home: TeamData,
        away: TeamData,
        context: GameContext
    ) -> GameProjection:
        """
        Full game projection: spread + total + win probabilities.
        """
        # Baseline scores
        league_avg_score = 28.0

        # Offense vs. Defense efficiency matchup
        home_off = self._blended_rating(home, "off")
        home_def = self._blended_rating(home, "def")
        away_off = self._blended_rating(away, "off")
        away_def = self._blended_rating(away, "def")

        # Projected scores (offense rating vs. opponent defense rating)
        home_score = league_avg_score + home_off + away_def
        away_score = league_avg_score + away_off + home_def

        # Home field advantage
        hfa = self._get_hfa(home, context)
        home_score += hfa
        away_score -= hfa * 0.3   # slight away suppression

        # Situational adjustments
        if context.bowl_game:
            home_score *= 0.97    # bowl prep equalizes somewhat
            away_score *= 0.97

        # Pace adjustment for total
        pace_adj = self._tempo_total_adj(home, away)

        proj_total  = home_score + away_score + pace_adj
        proj_spread = away_score - home_score  # negative = home favored

        # Win probabilities via normal distribution
        home_win_prob = float(stats.norm.cdf(0, proj_spread, self.SPREAD_SIGMA))
        cover_prob    = None  # set after we have market spread

        proj = GameProjection(
            home_team=home.name,
            away_team=away.name,
            proj_home_score=round(home_score, 1),
            proj_away_score=round(away_score, 1),
            proj_total=round(proj_total, 1),
            proj_spread=round(proj_spread, 1),
            spread_sigma=self.SPREAD_SIGMA,
            home_win_prob=round(home_win_prob, 3),
        )
        return proj

    # ── Edge Finder ───────────────────────────────────────────────────────────

    def find_spread_edge(
        self,
        proj: GameProjection,
        market_spread: float,
        min_edge: float = 2.5,    # minimum point differential to flag
    ) -> Optional[dict]:
        """
        Find spread edge: model spread vs. market spread.

        Args:
            proj:          GameProjection from project_game()
            market_spread: Market spread from home team perspective (neg = home fav)
            min_edge:      Minimum absolute point edge to flag

        Returns:
            Edge dict or None
        """
        edge_pts = market_spread - proj.proj_spread
        cover_prob = float(stats.norm.cdf(
            market_spread, proj.proj_spread, self.SPREAD_SIGMA
        ))

        if abs(edge_pts) < min_edge:
            return None

        direction = "HOME" if edge_pts > 0 else "AWAY"
        confidence = "HIGH" if abs(edge_pts) >= 5 else "MEDIUM"

        return {
            "game":        f"{proj.away_team} @ {proj.home_team}",
            "bet":         f"{proj.home_team if direction=='HOME' else proj.away_team} ATS",
            "market_spread": market_spread,
            "model_spread":  proj.proj_spread,
            "edge_pts":      round(edge_pts, 1),
            "cover_prob":    round(cover_prob, 3),
            "confidence":    confidence,
            "direction":     direction,
        }

    def find_total_edge(
        self,
        proj: GameProjection,
        market_total: float,
        min_edge: float = 3.0,
    ) -> Optional[dict]:
        """
        Find over/under edge.
        """
        edge_pts = proj.proj_total - market_total
        over_prob = float(1 - stats.norm.cdf(
            market_total, proj.proj_total, self.TOTAL_SIGMA
        ))

        if abs(edge_pts) < min_edge:
            return None

        direction = "OVER" if edge_pts > 0 else "UNDER"
        confidence = "HIGH" if abs(edge_pts) >= 6 else "MEDIUM"

        return {
            "game":         f"{proj.away_team} @ {proj.home_team}",
            "bet":          f"{direction} {market_total}",
            "model_total":  proj.proj_total,
            "market_total": market_total,
            "edge_pts":     round(edge_pts, 1),
            "over_prob":    round(over_prob, 3),
            "confidence":   confidence,
            "direction":    direction,
        }

    # ── Line Movement Signal ──────────────────────────────────────────────────

    def line_movement_signal(self, context: GameContext) -> dict:
        """
        Evaluate line movement as a corroborating signal.
        Sharp money typically moves lines 1–2 pts on sides, 1–3 on totals.
        When model + line movement agree, confidence upgrades.
        """
        signals = []

        spread_move = context.open_spread - context.current_spread
        total_move  = context.current_total - context.open_total

        if abs(spread_move) >= 1.5:
            direction = "HOME" if spread_move > 0 else "AWAY"
            signals.append({
                "type":      "spread_movement",
                "direction": direction,
                "magnitude": round(abs(spread_move), 1),
                "note":      f"Line moved {abs(spread_move):.1f} pts toward {direction}"
            })

        if abs(total_move) >= 1.5:
            direction = "OVER" if total_move > 0 else "UNDER"
            signals.append({
                "type":      "total_movement",
                "direction": direction,
                "magnitude": round(abs(total_move), 1),
                "note":      f"Total moved {abs(total_move):.1f} pts toward {direction}"
            })

        return {"signals": signals, "sharp_count": len(signals)}


# ─── Pick Sheet Generator (CFB) ───────────────────────────────────────────────

class CFBPickSheetGenerator:

    def generate(self, week: int, season: int,
                 spread_edges: list[dict], total_edges: list[dict]) -> str:
        lines = []
        lines.append(f"# EDGE INDEX — CFB Spread & Totals Sheet")
        lines.append(f"## Week {week}, {season} Season\n")
        lines.append("> Model: SP+ efficiency blend × HFA × pace × recent form\n")
        lines.append("---\n")

        tier1_s = [e for e in spread_edges if e and e["confidence"] == "HIGH"]
        tier2_s = [e for e in spread_edges if e and e["confidence"] == "MEDIUM"]
        tier1_t = [e for e in total_edges  if e and e["confidence"] == "HIGH"]
        tier2_t = [e for e in total_edges  if e and e["confidence"] == "MEDIUM"]

        if tier1_s or tier1_t:
            lines.append("### ★★★ Tier 1 — High Confidence\n")
            for e in tier1_s + tier1_t:
                lines.append(f"**{e['game']}**")
                lines.append(f"  Play: {e['bet']}")
                if 'edge_pts' in e:
                    lines.append(f"  Model edge: {e['edge_pts']:+.1f} pts | "
                                 f"Cover prob: {e.get('cover_prob',e.get('over_prob',0))*100:.0f}%")
                lines.append("")

        if tier2_s or tier2_t:
            lines.append("### ★★  Tier 2 — Medium Confidence\n")
            for e in tier2_s + tier2_t:
                lines.append(f"**{e['game']}**")
                lines.append(f"  Play: {e['bet']}")
                if 'edge_pts' in e:
                    lines.append(f"  Model edge: {e['edge_pts']:+.1f} pts | "
                                 f"Cover prob: {e.get('cover_prob',e.get('over_prob',0))*100:.0f}%")
                lines.append("")

        lines.append("---")
        lines.append("*Edge Index — process over picks. Results posted weekly.*")
        return "\n".join(lines)


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = CFBModel()

    alabama = TeamData(
        name="Alabama", conference="SEC",
        off_efficiency=22.4, def_efficiency=-18.1, st_efficiency=2.1,
        points_per_game=38.2, points_allowed=16.4,
        yards_per_play_off=6.8, yards_per_play_def=4.2,
        plays_per_game=72, recent_form_delta=1.5
    )
    auburn = TeamData(
        name="Auburn", conference="SEC",
        off_efficiency=8.3, def_efficiency=-6.2, st_efficiency=0.8,
        points_per_game=29.1, points_allowed=22.8,
        yards_per_play_off=5.9, yards_per_play_def=5.1,
        plays_per_game=68, recent_form_delta=-0.5
    )
    context = GameContext(
        home_team="Alabama", away_team="Auburn",
        night_game=True, conference_game=True, rivalry_game=True,
        neutral_site=False,
        open_spread=-13.5, current_spread=-14.5,
        open_total=52.0,   current_total=51.0,
        spread_moved_toward_home=True
    )

    proj = model.project_game(alabama, auburn, context)
    print(f"\n{'='*50}")
    print(f"PROJECTION: {proj.away_team} @ {proj.home_team}")
    print(f"  Proj score:  {proj.home_team} {proj.proj_home_score} — "
          f"{proj.away_team} {proj.proj_away_score}")
    print(f"  Proj spread: {proj.proj_spread:+.1f} (home perspective)")
    print(f"  Proj total:  {proj.proj_total}")
    print(f"  Home win prob: {proj.home_win_prob*100:.1f}%")

    spread_edge = model.find_spread_edge(proj, market_spread=context.current_spread)
    total_edge  = model.find_total_edge(proj,  market_total=context.current_total)
    lm          = model.line_movement_signal(context)

    print(f"\nSPREAD EDGE: {spread_edge}")
    print(f"TOTAL EDGE:  {total_edge}")
    print(f"LINE MOVEMENT: {lm}")

    gen = CFBPickSheetGenerator()
    sheet = gen.generate(13, 2025,
                         [spread_edge] if spread_edge else [],
                         [total_edge]  if total_edge  else [])
    print(f"\n{sheet}")
