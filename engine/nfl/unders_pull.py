"""2024 closing receptions / rec_yds MAIN lines, all US books, for docs/nfl/PREREG_UNDERS.md.

    python -m engine.nfl.unders_pull --dry-run
    python -m engine.nfl.unders_pull --approved-credits 12000     # resumable

One historical /events lookup per 2024 regular-season game date (1 credit) for event ids, then one historical event-odds
snapshot per game at kickoff - 10 min, regions=us (every US book for one region's cost). PREGAME ONLY.
Raw: data/nfl/verify/raw/unders2024/ (gitignored). Output: data/nfl/verify/close_mains_2024.parquet.
"""
from __future__ import annotations
import argparse
import io
import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from engine.nfl import verify_pull as vp

SEASON = 2024
MARKETS = ["player_receptions", "player_reception_yds"]
RAW = vp.RAW / "unders2024"


def schedule(season=SEASON):
    g = pd.read_csv(io.StringIO(vp.get(vp.SCHEDULE, {}).text))
    g = g[(g.season == season) & (g.game_type == "REG")].copy()
    et = ZoneInfo("America/New_York")
    g["kickoff"] = [datetime.fromisoformat(f"{d}T{t}").replace(tzinfo=et).astimezone(timezone.utc)
                    for d, t in zip(g.gameday, g.gametime)]
    g["snapshot_at"] = g.kickoff - timedelta(minutes=10)
    return g[["game_id", "week", "game_type", "gameday", "kickoff", "snapshot_at", "away_team", "home_team"]] \
        .reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approved-credits", type=int, default=0)
    a = ap.parse_args()
    g = schedule()
    worst = len(g) * 10 * len(MARKETS) + g.gameday.nunique()
    print(f"{len(g)} REG games on {g.gameday.nunique()} dates; worst case {worst:,} credits")
    if a.dry_run:
        return
    key = os.environ["ODDS_API_KEY"]
    RAW.mkdir(parents=True, exist_ok=True)
    budget = vp.Budget(a.approved_credits)
    path = RAW / "events_by_date.json"
    seen = json.loads(path.read_text()) if path.exists() else {}
    for day, d in g.groupby("gameday"):
        if day in seen:
            continue
        budget.check(1)
        r = vp.get(f"{vp.BASE}/events", {"apiKey": key, "date": d.snapshot_at.min().strftime("%Y-%m-%dT%H:%M:%SZ")})
        vp.log_usage("unders2024:historical events", r.headers)
        budget.charge(r.headers, 1)
        seen[day] = r.json().get("data", [])
        path.write_text(json.dumps(seen))
    ids = {}
    for evs in seen.values():
        for e in evs:
            if e.get("home_team") in vp.TEAMS and e.get("away_team") in vp.TEAMS:
                ids[(vp.TEAMS[e["home_team"]], vp.TEAMS[e["away_team"]], e["commence_time"][:10])] = e["id"]
    rows, missing = [], []
    for row in g.itertuples():
        eid = vp.lookup(ids, row)
        if not eid:
            missing.append(row.game_id); continue
        f = RAW / f"{row.game_id}_{eid}.json"
        if f.exists():
            d = json.loads(f.read_text())
        else:
            budget.check(10 * len(MARKETS))
            r = vp.get(f"{vp.BASE}/events/{eid}/odds", {"apiKey": key, "regions": "us", "markets": ",".join(MARKETS),
                                                         "oddsFormat": "american",
                                                         "date": row.snapshot_at.strftime("%Y-%m-%dT%H:%M:%SZ")})
            vp.log_usage("unders2024:historical event odds", r.headers)
            budget.charge(r.headers, 10 * len(MARKETS))
            d = r.json()
            f.write_text(json.dumps(d))
        snap = d.get("timestamp")
        if snap and pd.Timestamp(snap) >= pd.Timestamp(row.kickoff):
            raise ValueError(f"{row.game_id}: snapshot {snap} not before kickoff")
        for b in d.get("data", {}).get("bookmakers", []):
            for m in b["markets"]:
                for o in m["outcomes"]:
                    rows.append(dict(game_id=row.game_id, week=int(row.week), kickoff=row.kickoff.isoformat(), snapshot=snap,
                                     book=b["key"], market=m["key"], player=o.get("description"), side=o["name"],
                                     point=o.get("point"), price=o.get("price"), home_team=row.home_team,
                                     away_team=row.away_team))
    df = pd.DataFrame(rows)
    df.to_parquet(vp.OUT / "close_mains_2024.parquet", index=False, compression="zstd")
    print(f"wrote close_mains_2024.parquet: {len(df):,} outcomes, {df.game_id.nunique()} games; {budget.spent:,} credits; "
          f"missing ids {missing}")


if __name__ == "__main__":
    main()
