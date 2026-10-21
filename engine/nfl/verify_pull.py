"""2025 DraftKings receptions / rec_yds prices (main + alternate) for the NFL floor verification (docs/nfl/PREREG_NFL.md).

    python -m engine.nfl.verify_pull --dry-run                       # plan + cost, no paid call
    python -m engine.nfl.verify_pull --approved-credits 12000        # pull (approved 2026-10-21); resumable

One historical /events lookup per game date (1 credit) finds the Odds API event ids; then one historical event-odds
snapshot per game at kickoff - 10 minutes, DK only. PREGAME ONLY: a snapshot taken at or after kickoff is refused.
Stops before passing --approved-credits (lookups included) or letting x-requests-remaining fall under 100,000.
Raw responses: data/nfl/verify/raw/ (gitignored). Output: data/nfl/verify/hist_props_2025.parquet, one row per outcome.
Every paid call is logged to data/nfl/verify/odds_usage_nfl_verify.csv.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "nfl" / "verify"
RAW = OUT / "raw"
USAGE = OUT / "odds_usage_nfl_verify.csv"
SEASON = 2025
BASE = "https://api.the-odds-api.com/v4/historical/sports/americanfootball_nfl"
MARKETS = ["player_receptions", "player_receptions_alternate", "player_reception_yds", "player_reception_yds_alternate"]
LEAD = timedelta(minutes=10)
RESERVE = 100_000
SCHEDULE = "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
TEAMS = {"Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
         "Carolina Panthers": "CAR", "Chicago Bears": "CHI", "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
         "Dallas Cowboys": "DAL", "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
         "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
         "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LA", "Miami Dolphins": "MIA",
         "Minnesota Vikings": "MIN", "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
         "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
         "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN", "Washington Commanders": "WAS"}


def get(url, params, tries=3):
    """GET with the pipeline's retry policy (5s, 15s; no retry on 4xx); the key never appears in an error"""
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
            if r.status_code in (400, 401, 403, 404, 410, 422):
                break
        except requests.RequestException as e:
            last = type(e).__name__
        if i < tries - 1:
            time.sleep(5 * 3 ** i)
    raise RuntimeError(f"{url} failed: {last}")


def log_usage(kind, h):
    new = not USAGE.exists()
    with USAGE.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["pulled_at", "kind", "x_requests_used", "x_requests_remaining", "x_requests_last"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), kind, h.get("x-requests-used"),
                    h.get("x-requests-remaining"), h.get("x-requests-last")])


def schedule() -> pd.DataFrame:
    g = pd.read_csv(io.StringIO(get(SCHEDULE, {}).text))
    g = g[g.season == SEASON].copy()
    et = ZoneInfo("America/New_York")
    g["kickoff"] = [datetime.fromisoformat(f"{d}T{t}").replace(tzinfo=et).astimezone(timezone.utc)
                    for d, t in zip(g.gameday, g.gametime)]
    g["snapshot_at"] = g.kickoff - LEAD
    return g[["game_id", "week", "game_type", "gameday", "weekday", "kickoff", "snapshot_at", "away_team", "home_team"]]


class Budget:
    def __init__(self, approved):
        self.approved, self.spent = approved, 0

    def charge(self, h, worst):
        self.spent += int(h.get("x-requests-last") or 0)
        rem = h.get("x-requests-remaining")
        if rem is not None and int(float(rem)) - worst < RESERVE:
            raise SystemExit(f"stopping: remaining {rem} is near the {RESERVE:,} reserve")

    def check(self, worst):
        if self.spent + worst > self.approved:
            raise SystemExit(f"stopping: next call could pass the approved {self.approved:,} (spent {self.spent:,})")


def event_ids(g: pd.DataFrame, key: str, budget: Budget) -> dict:
    """{(home, away): event_id} from one /events lookup per game date, at that date's first kickoff - 10 min"""
    path = RAW / "events_by_date.json"
    seen = json.loads(path.read_text()) if path.exists() else {}
    for day, d in g.groupby("gameday"):
        if day in seen:
            continue
        budget.check(1)
        ts = d.snapshot_at.min().strftime("%Y-%m-%dT%H:%M:%SZ")
        r = get(f"{BASE}/events", {"apiKey": key, "date": ts})
        log_usage("historical events", r.headers)
        budget.charge(r.headers, 1)
        seen[day] = r.json().get("data", [])
        path.write_text(json.dumps(seen))
    ids = {}
    for evs in seen.values():
        for e in evs:
            if e.get("home_team") in TEAMS and e.get("away_team") in TEAMS:
                ids[(TEAMS[e["home_team"]], TEAMS[e["away_team"]], e["commence_time"][:10])] = e["id"]
    return ids


def lookup(ids, row):
    """event id by teams and kickoff date (UTC date, falling back one day for late ET kickoffs)"""
    for d in (row.kickoff.date(), row.kickoff.date() - timedelta(days=1), row.kickoff.date() + timedelta(days=1)):
        e = ids.get((row.home_team, row.away_team, d.isoformat()))
        if e:
            return e
    return None


def parse(d: dict, row) -> list[dict]:
    snap = d.get("timestamp")
    if snap and pd.Timestamp(snap) >= pd.Timestamp(row.kickoff):
        raise ValueError(f"{row.game_id}: snapshot {snap} is not before kickoff {row.kickoff}")
    out = []
    for b in d.get("data", {}).get("bookmakers", []):
        for m in b["markets"]:
            for o in m["outcomes"]:
                out.append({"game_id": row.game_id, "week": int(row.week), "game_type": row.game_type,
                            "kickoff": row.kickoff.isoformat(), "snapshot": snap, "market": m["key"],
                            "player": o.get("description"), "side": o["name"], "point": o.get("point"),
                            "price": o.get("price"), "home_team": row.home_team, "away_team": row.away_team})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approved-credits", type=int, default=0)
    a = ap.parse_args()
    g = schedule()
    worst = 10 * len(MARKETS)
    print(f"{len(g)} games ({g.game_type.value_counts().to_dict()}) on {g.gameday.nunique()} dates; worst case "
          f"{len(g) * worst + g.gameday.nunique():,} credits")
    if a.dry_run:
        return
    key = os.environ["ODDS_API_KEY"]
    RAW.mkdir(parents=True, exist_ok=True)
    budget = Budget(a.approved_credits)
    ids = event_ids(g, key, budget)
    rows, missing = [], []
    for row in g.itertuples():
        eid = lookup(ids, row)
        if not eid:
            missing.append(row.game_id)
            continue
        path = RAW / f"{row.game_id}_{eid}.json"
        if path.exists():
            d = json.loads(path.read_text())
        else:
            budget.check(worst)
            r = get(f"{BASE}/events/{eid}/odds", {"apiKey": key, "regions": "us", "bookmakers": "draftkings",
                                                   "markets": ",".join(MARKETS), "oddsFormat": "american",
                                                   "date": row.snapshot_at.strftime("%Y-%m-%dT%H:%M:%SZ")})
            log_usage("historical event odds", r.headers)
            budget.charge(r.headers, worst)
            d = r.json()
            path.write_text(json.dumps(d))
        rows += parse(d, row)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / f"hist_props_{SEASON}.parquet", index=False, compression="zstd")
    print(f"wrote hist_props_{SEASON}.parquet: {len(df):,} outcomes, {df.game_id.nunique()} games; "
          f"{budget.spent:,} credits this run; no event id for {len(missing)} games: {missing}")


if __name__ == "__main__":
    main()
