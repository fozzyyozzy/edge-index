"""Pregame DraftKings spread + total for every backfilled game (context for the blowout study), from The Odds API
historical snapshots.

    python -m engine.nba.hist_lines --dry-run      # plan + credit estimate, spends nothing
    python -m engine.nba.hist_lines                # pull (resumable; snapshots cached in data/nba/raw/odds_hist/)

One snapshot per game date, taken 10 minutes before that date's first tip, so every game in it is pregame.
PREGAME ONLY: an event is kept only if its commence_time is after the snapshot timestamp (the historical endpoint
also returns live games). Cost: 10 credits x markets x regions = 20 per snapshot (spreads, totals; DK only).
Guards: refuses to start if x-requests-remaining would fall under NBA_ODDS_RESERVE (default 100,000), and
any run planned over 2,000 credits needs Tim's approval first (spend rule, 2026-10-21): show him the --dry-run
estimate, then rerun with --approved-credits N (N >= the planned cost).
Writes data/nba/lines/pregame_spreads_totals.parquet; every call is logged to data/nba/lines/odds_usage_nba.csv.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from engine.nba import http
from engine.nba.teams import from_name

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "nba"
RAW = DATA / "raw" / "odds_hist"
OUT = DATA / "lines" / "pregame_spreads_totals.parquet"
USAGE = DATA / "lines" / "odds_usage_nba.csv"
URL = "https://api.the-odds-api.com/v4/historical/sports/basketball_nba/odds"
RESERVE = int(os.environ.get("NBA_ODDS_RESERVE", "100000"))
COST = 20
APPROVAL_OVER = 2000          # credits; larger pulls need Tim's explicit approval (pass --approved-credits)
LEAD = timedelta(minutes=10)


def log_usage(kind: str, n: int, used, remaining, last):
    new = not USAGE.exists()
    USAGE.parent.mkdir(parents=True, exist_ok=True)
    with USAGE.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["pulled_at", "kind", "calls", "x_requests_used", "x_requests_remaining", "x_requests_last"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), kind, n, used, remaining, last])


def snapshot(ts: datetime, key: str) -> dict:
    path = RAW / f"{ts:%Y%m%dT%H%M}.json"
    if path.exists():
        return json.loads(path.read_text())
    r = http.get(URL, {"apiKey": key, "regions": "us", "bookmakers": "draftkings", "markets": "spreads,totals",
                       "oddsFormat": "american", "date": ts.strftime("%Y-%m-%dT%H:%M:%SZ")}, timeout=60)
    h = r.headers
    log_usage("historical spreads,totals", 1, h.get("x-requests-used"), h.get("x-requests-remaining"),
              h.get("x-requests-last"))
    d = r.json()
    RAW.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d))
    return d


def parse(snap: dict, ts: datetime) -> list[dict]:
    rows = []
    for e in snap.get("data", []):
        start = datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
        if start <= ts:                                   # live or finished at snapshot time: never stored
            continue
        home, away = from_name(e["home_team"]), from_name(e["away_team"])
        row = {"home": home, "away": away, "commence": e["commence_time"], "snapshot": snap.get("timestamp"),
               "home_spread": None, "total": None, "spread_price": None}
        for b in e.get("bookmakers", []):
            for m in b["markets"]:
                if m["key"] == "spreads":
                    o = next(o for o in m["outcomes"] if o["name"] == e["home_team"])
                    row["home_spread"], row["spread_price"] = o.get("point"), o.get("price")
                elif m["key"] == "totals":
                    row["total"] = next(o["point"] for o in m["outcomes"] if o["name"] == "Over")
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approved-credits", type=int, default=0, help="credits Tim approved for this run")
    a = ap.parse_args()
    games = pd.read_parquet(DATA / "games.parquet")
    games["tip"] = pd.to_datetime(games.commence, utc=True)
    first = games.groupby("date").tip.min()
    stamps = [(t - LEAD).to_pydatetime().replace(second=0, microsecond=0) for t in first]
    todo = [t for t in stamps if not (RAW / f"{t:%Y%m%dT%H%M}.json").exists()]
    print(f"{len(games)} games on {len(stamps)} dates; {len(todo)} snapshots to pull = {len(todo) * COST:,} credits")
    if a.dry_run:
        return
    planned = len(todo) * COST
    if planned > APPROVAL_OVER and a.approved_credits < planned:
        raise SystemExit(f"refusing: {planned:,} credits planned is over {APPROVAL_OVER:,}; needs Tim's approval "
                         f"(--approved-credits {planned})")
    key = os.environ["ODDS_API_KEY"]
    if todo:
        probe = http.get("https://api.the-odds-api.com/v4/sports/basketball_nba/events", {"apiKey": key})
        rem = int(probe.headers.get("x-requests-remaining", 0))
        if rem - len(todo) * COST < RESERVE:
            raise SystemExit(f"refusing: {rem:,} remaining - {len(todo) * COST:,} planned < reserve {RESERVE:,}")
    rows = []
    for i, ts in enumerate(stamps):
        rows += parse(snapshot(ts.replace(tzinfo=timezone.utc), key), ts.replace(tzinfo=timezone.utc))
        if i % 50 == 0:
            print(f"  {i}/{len(stamps)}", flush=True)
    ln = pd.DataFrame(rows)
    ln["date"] = pd.to_datetime(ln.commence, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    # a snapshot also lists later days' games: keep each game's latest pregame snapshot (closest to tip)
    ln = ln.sort_values("snapshot").drop_duplicates(["date", "home", "away"], keep="last")
    m =games[["game_id", "date", "home", "away"]].merge(ln, on=["date", "home", "away"], how="left")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    m.drop(columns=["date", "home", "away"]).to_parquet(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {m.home_spread.notna().sum()}/{len(m)} games with a spread, "
          f"{m.total.notna().sum()} with a total")


if __name__ == "__main__":
    main()
