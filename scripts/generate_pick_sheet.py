"""
EDGE INDEX — Weekly Pick Sheet Generator
=========================================
Called by GitHub Actions after the scraper completes.
Loads parquet data → runs models → outputs PDF-ready markdown.

Usage:
    python scripts/generate_pick_sheet.py --week 10 --season 2025

Output:
    outputs/pick_sheet_2025_w10.md   ← paste into Google Doc → export PDF
    outputs/pick_sheet_2025_w10.json ← machine-readable for future dashboard
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import date

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.pfr_scraper import ModelDataLoader
from models.nfl_props_model import PropModel, MatchupData, PickSheetGenerator
from models.cfb_model import CFBModel, TeamData, GameContext, CFBPickSheetGenerator

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Weekly Matchup Config ─────────────────────────────────────────────────────
# You fill this in each week — takes ~15 minutes
# Pull Vegas lines from Action Network, DraftKings, or FanDuel
# Pull team spreads from the same source

def get_this_weeks_matchups(week: int, season: int) -> dict:
    """
    EDIT THIS EACH WEEK.
    Returns the matchup config dict for props + CFB games.

    For NFL props:
      - market_lines: the actual market lines from your sportsbook
      - matchup: MatchupData with defensive ranks (auto-loaded from parquet)

    For CFB:
      - team data: update off/def efficiency from ESPN SP+ each Friday
      - context: pull spreads/totals from Action Network
    """

    # ── NFL PROPS CONFIG ─────────────────────────────────────────────────────
    # Add/remove players each week based on matchup quality
    nfl_targets = [
        {
            "player":   "Tyreek Hill",
            "position": "WR",
            "opponent_abbr": "DAL",        # 3-letter PFR abbreviation
            "market_lines": {
                "rec_yards":   82.5,
                "targets":     8.5,
                "receptions":  6.5,
            },
            "matchup_overrides": {
                # Optional: override auto-loaded ranks if you have better info
                # "def_rec_yards_allowed_rank": 28,
                "game_total":     51.5,
                "team_spread":    -6.5,
                "is_home":        True,
                "implied_team_total": 29.0,
            }
        },
        {
            "player":   "Lamar Jackson",
            "position": "QB",
            "opponent_abbr": "PIT",
            "market_lines": {
                "pass_yards": 267.5,
                "pass_tds":   2.5,
                "rush_yards": 42.5,
            },
            "matchup_overrides": {
                "game_total":     44.5,
                "team_spread":    -7.0,
                "is_home":        True,
                "implied_team_total": 25.75,
            }
        },
        # ── Add more players here ──
        # {
        #     "player":   "CeeDee Lamb",
        #     "position": "WR",
        #     "opponent_abbr": "PHI",
        #     "market_lines": {"rec_yards": 89.5, "targets": 9.5},
        #     "matchup_overrides": {"game_total": 48.0, "team_spread": 3.0}
        # },
    ]

    # ── CFB GAMES CONFIG ─────────────────────────────────────────────────────
    # Update SP+ ratings each Friday from: https://www.espn.com/college-football/statistics/teamratings
    cfb_games = [
        {
            "home": TeamData(
                name="Georgia", conference="SEC",
                off_efficiency=18.2, def_efficiency=-20.1, st_efficiency=1.8,
                points_per_game=36.4, points_allowed=14.2,
                plays_per_game=71, recent_form_delta=0.8
            ),
            "away": TeamData(
                name="Tennessee", conference="SEC",
                off_efficiency=12.4, def_efficiency=-9.3, st_efficiency=0.5,
                points_per_game=31.1, points_allowed=19.8,
                plays_per_game=74, recent_form_delta=1.2
            ),
            "context": GameContext(
                home_team="Georgia", away_team="Tennessee",
                night_game=True, conference_game=True,
                open_spread=-10.0, current_spread=-11.5,
                open_total=50.5,   current_total=51.5,
                spread_moved_toward_home=True,
            )
        },
        # ── Add more CFB games here ──
    ]

    return {"nfl": nfl_targets, "cfb": cfb_games, "week": week, "season": season}


# ── Generator ─────────────────────────────────────────────────────────────────

def generate(week: int, season: int) -> None:
    print(f"\nGenerating pick sheet — Week {week}, {season}")

    loader      = ModelDataLoader(season=season)
    nfl_model   = PropModel()
    cfb_model   = CFBModel()
    config      = get_this_weeks_matchups(week, season)

    all_nfl_edges  = []
    all_cfb_spread = []
    all_cfb_total  = []
    json_output    = {"week": week, "season": season, "nfl": [], "cfb": []}

    # ── NFL Props ─────────────────────────────────────────────────────────────
    for target in config["nfl"]:
        player_name = target["player"]
        position    = target["position"]
        opp_abbr    = target["opponent_abbr"]
        overrides   = target.get("matchup_overrides", {})

        # Load game logs from parquet
        games = loader.get_player_games(player_name, n_games=8)
        if not games:
            print(f"  [skip] {player_name} — no game log data")
            continue

        # Build matchup with auto-loaded def ranks + manual overrides
        def_pass_rank = loader.get_defense_rank(opp_abbr, "passing")
        def_rush_rank = loader.get_defense_rank(opp_abbr, "rushing")
        def_rec_rank  = loader.get_defense_rank(opp_abbr, "receiving")

        matchup = MatchupData(
            opponent=opp_abbr,
            def_pass_yards_allowed_rank = overrides.get("def_pass_yards_allowed_rank", def_pass_rank),
            def_rush_yards_allowed_rank = overrides.get("def_rush_yards_allowed_rank", def_rush_rank),
            def_rec_yards_allowed_rank  = overrides.get("def_rec_yards_allowed_rank",  def_rec_rank),
            def_targets_allowed_rank    = overrides.get("def_targets_allowed_rank",    def_rec_rank),
            def_td_rate_rank            = overrides.get("def_td_rate_rank", 16),
            game_total                  = overrides.get("game_total", 44.0),
            team_spread                 = overrides.get("team_spread", 0.0),
            is_home                     = overrides.get("is_home", True),
            implied_team_total          = overrides.get("implied_team_total", 22.0),
            pace_rank                   = overrides.get("pace_rank", 16),
        )

        proj  = nfl_model.project_player(player_name, position, games, matchup)
        edges = nfl_model.find_edge(proj, target["market_lines"])

        if edges:
            all_nfl_edges.append((proj, edges))
            json_output["nfl"].append({
                "player":     player_name,
                "position":   position,
                "projection": {
                    "pass_yards":  proj.pass_yards,
                    "rush_yards":  proj.rush_yards,
                    "rec_yards":   proj.rec_yards,
                    "targets":     proj.targets,
                    "receptions":  proj.receptions,
                },
                "edges": edges,
            })
            print(f"  [nfl] {player_name}: {len(edges)} edge(s) found")
        else:
            print(f"  [nfl] {player_name}: no edges above threshold")

    # ── CFB ───────────────────────────────────────────────────────────────────
    for game in config["cfb"]:
        proj         = cfb_model.project_game(game["home"], game["away"], game["context"])
        spread_edge  = cfb_model.find_spread_edge(proj, game["context"].current_spread)
        total_edge   = cfb_model.find_total_edge(proj,  game["context"].current_total)
        lm           = cfb_model.line_movement_signal(game["context"])

        if spread_edge:
            # Upgrade confidence if line movement agrees
            if lm["sharp_count"] > 0:
                mv_dir = lm["signals"][0]["direction"]
                if mv_dir == spread_edge["direction"]:
                    spread_edge["confidence"] = "HIGH"
                    spread_edge["note"] = "Model + sharp line movement agree"
            all_cfb_spread.append(spread_edge)

        if total_edge:
            all_cfb_total.append(total_edge)

        game_name = f"{game['away'].name} @ {game['home'].name}"
        print(f"  [cfb] {game_name}: spread={spread_edge is not None}, "
              f"total={total_edge is not None}")

        json_output["cfb"].append({
            "game":         game_name,
            "projection":   {"spread": proj.proj_spread, "total": proj.proj_total},
            "spread_edge":  spread_edge,
            "total_edge":   total_edge,
            "line_movement": lm,
        })

    # ── Save Outputs ──────────────────────────────────────────────────────────
    # Markdown pick sheet
    nfl_gen = PickSheetGenerator()
    cfb_gen = CFBPickSheetGenerator()

    nfl_sheet = nfl_gen.generate(week, season, all_nfl_edges)
    cfb_sheet = cfb_gen.generate(week, season, all_cfb_spread, all_cfb_total)

    full_sheet = f"{nfl_sheet}\n\n---\n\n{cfb_sheet}"
    full_sheet += f"\n\n---\n*Generated: {date.today().isoformat()}*"

    md_path   = OUTPUT_DIR / f"pick_sheet_{season}_w{week}.md"
    json_path = OUTPUT_DIR / f"pick_sheet_{season}_w{week}.json"

    md_path.write_text(full_sheet)
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2, default=str)

    print(f"\n[output] Markdown → {md_path}")
    print(f"[output] JSON     → {json_path}")
    print(f"\n{'='*40}")
    print(full_sheet[:800] + "...")
    print(f"{'='*40}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",   type=int, required=True)
    parser.add_argument("--season", type=int, default=2025)
    args = parser.parse_args()
    generate(args.week, args.season)
