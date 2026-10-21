"""Historical DraftKings player-prop prices (main + alternate ladders): DRY-RUN ESTIMATE ONLY.

    python -m engine.nba.hist_props --season 2025-26      # plan + credit estimate; makes no paid call

Plan: one /v4/historical/sports/basketball_nba/events/{id}/odds call per game, at tip - LEAD, DK only (1 region),
all in-scope markets. Event ids come from the cached spread/total snapshots (data/nba/raw/odds_hist/), so no
paid /historical/events lookups are needed.
Cost (Odds API docs, read 2026-10-21): 10 x [unique markets RETURNED] x [regions]; empty responses are free.
So the true cost depends on which markets DK actually posted per game, which can't be known without paying.
There is deliberately no pull path here: spend rule (2026-10-21) = anything over 2,000 credits needs Tim's
approval of this estimate first.
"""
from __future__ import annotations
import argparse
import json
from datetime import timedelta

import pandas as pd

from engine.nba.hist_lines import DATA, RAW as SNAPSHOTS
from engine.nba.teams import from_name

STATS = ["points", "rebounds", "assists", "threes", "points_rebounds", "points_assists", "rebounds_assists",
         "points_rebounds_assists", "steals", "blocks"]
MAIN = [f"player_{s}" for s in STATS]
ALT = [f"player_{s}_alternate" for s in STATS]
SEEN_PHASE0 = {"player_points", "player_rebounds", "player_assists", "player_points_rebounds_assists",
               "player_points_alternate", "player_rebounds_alternate", "player_assists_alternate",
               "player_points_rebounds_assists_alternate", "player_threes_alternate"}   # DK returned these for 13/13
LEAD = timedelta(minutes=10)
PER_MARKET = 10                                                                        # x 1 region (DK only)


def event_ids() -> pd.DataFrame:
    """event id per (ET date, home, away) from the cached historical snapshots"""
    rows = []
    for p in SNAPSHOTS.glob("*.json"):
        for e in json.loads(p.read_text()).get("data", []):
            rows.append({"event_id": e["id"], "commence": e["commence_time"],
                         "home": from_name(e["home_team"]), "away": from_name(e["away_team"])})
    ev = pd.DataFrame(rows).drop_duplicates("event_id")
    ev["date"] = pd.to_datetime(ev.commence, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    return ev


def plan(season: str) -> pd.DataFrame:
    g = pd.read_parquet(DATA / "games.parquet")
    g = g[g.season == season]
    ev = event_ids().drop(columns=["commence"])
    p = g[["game_id", "date", "home", "away", "commence"]].merge(ev, on=["date", "home", "away"], how="left")
    p["snapshot_at"] = pd.to_datetime(p.commence, utc=True) - LEAD
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2025-26")
    a = ap.parse_args()
    p = plan(a.season)
    n, missing = len(p), int(p.event_id.isna().sum())
    seen_main = [m for m in MAIN if m in SEEN_PHASE0]
    seen_alt = [m for m in ALT if m in SEEN_PHASE0]
    out = {
        "season": a.season, "games": n, "dates": int(p.date.nunique()), "games_without_event_id": missing,
        "markets_requested": len(MAIN) + len(ALT),
        "per_game_max": PER_MARKET * (len(MAIN) + len(ALT)),
        "total_max_all_20_returned": n * PER_MARKET * (len(MAIN) + len(ALT)),
        "total_if_only_phase0_markets_returned": n * PER_MARKET * len(SEEN_PHASE0),
        "event_id_lookup_cost": 0,
        "markets_seen_live_in_phase0": sorted(SEEN_PHASE0),
        "markets_never_checked": sorted(set(MAIN + ALT) - SEEN_PHASE0),
        "by_month_games": p.groupby(p.date.str[:7]).size().to_dict(),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
