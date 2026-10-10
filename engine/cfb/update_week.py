"""In-season incremental update (run by hand; safe to run daily).

Refreshes the current season's games, lines (includes the upcoming week's
lines), advanced stats and game PPA, then pulls PBP for any newly completed
week, then rebuilds the clean tables. Typically 5 calls; hard-capped at 10.
Season-level files younger than --min-age hours are not re-fetched, so a
second run the same morning costs zero calls.

    python -m engine.cfb.update_week [--season 2026] [--min-age 6] [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import time

from engine.cfb import config
from engine.cfb.cfbd_client import CFBDClient, calls_used
from engine.cfb.pull import SEASON_DATASETS, completed_weeks, plays_name

REFRESH = ["games", "lines", "advanced", "ppa_games"]
MAX_CALLS = 10


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--min-age", type=float, default=6.0,
                    help="hours before a season-level file is re-fetched")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args(argv)

    client = CFBDClient()
    y = a.season
    budget = MAX_CALLS

    stale = []
    for ds in REFRESH:
        p = client.cache_path(ds, str(y))
        age_h = (time.time() - p.stat().st_mtime) / 3600 if p.exists() else None
        if age_h is None or age_h >= a.min_age:
            stale.append(ds)
    print(f"season {y}: refresh {stale or 'nothing (all fresh)'}")
    if a.dry_run:
        print(f"<= {len(stale)} season calls + 1 per newly completed week")
        return 0

    for ds in stale:
        ep, pfn = SEASON_DATASETS[ds]
        client.get(ds, ep, pfn(y), str(y), refresh=True)
        budget -= 1

    games = json.loads(client.cache_path("games", str(y)).read_text(encoding="utf-8"))
    new = [(st, wk) for st, wk in completed_weeks(games)
           if not client.is_cached("plays", plays_name(y, st, wk))]
    if len(new) > budget:
        print(f"{len(new)} uncached weeks > remaining budget {budget}; "
              f"use engine.cfb.pull for a backfill")
        new = new[:budget]
    for st, wk in new:
        client.get("plays", "/plays", {"year": y, "week": wk, "seasonType": st},
                   plays_name(y, st, wk))
    print(f"live calls: {client.live_calls}; ledger total: {calls_used()}")

    if not a.no_build:
        from engine.cfb import build_tables
        build_tables.main([])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
