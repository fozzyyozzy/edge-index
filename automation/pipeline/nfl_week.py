"""
nfl_week.py — which NFL week it is, from the nflverse schedule (replaces the CURRENT_WEEK repo variable, which the
workflows' GITHUB_TOKEN can't update).
  python pipeline/nfl_week.py --season 2026 --mode current   the week being carded: earliest week whose last game day is
                                                             today or later (ET). Tue-Mon of week N -> N.
  python pipeline/nfl_week.py --season 2026 --mode graded    the week to grade: latest week whose last game day is before
                                                             today (ET). Tuesday after week N -> N.
Prints the week number only.
"""
import argparse, os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from floors import schedule_all

def week_for(season, mode, today=None):
    today = today or datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York")).date().isoformat()
    g = schedule_all(season)
    g = g[g.game_type == "REG"] if "game_type" in g else g
    last_day = g.groupby("week").gameday.max()                        # ISO dates sort as strings
    if mode == "current":
        weeks = last_day[last_day >= today].index
        return int(weeks.min()) if len(weeks) else int(last_day.index.max())
    weeks = last_day[last_day < today].index
    return int(weeks.max()) if len(weeks) else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--mode", choices=["current", "graded"], required=True)
    ap.add_argument("--today", help="override (YYYY-MM-DD, ET) for testing")
    a = ap.parse_args()
    print(week_for(a.season, a.mode, a.today))
