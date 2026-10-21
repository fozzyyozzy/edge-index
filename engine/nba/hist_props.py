"""Historical DraftKings player-prop prices (main + alternate ladders): DRY-RUN ESTIMATE ONLY.

    python -m engine.nba.hist_props --season 2025-26      # plan + credit estimate; makes no paid call
    python -m engine.nba.hist_props --sample --approved-credits 1400   # coverage sample (approved 2026-10-21)
    python -m engine.nba.hist_props --full --approved-credits 240000   # full season (approved 2026-10-21, after
                                                                       # PREREG amendment 1); resumable

Plan: one /v4/historical/sports/basketball_nba/events/{id}/odds call per game, at tip - LEAD, DK only (1 region),
all in-scope markets. Event ids come from the cached spread/total snapshots (data/nba/raw/odds_hist/), so no
paid /historical/events lookups are needed.
Cost (Odds API docs, read 2026-10-21): 10 x [unique markets RETURNED] x [regions]; empty responses are free.
So the true cost depends on which markets DK actually posted per game, which can't be known without paying.
Spend rule (2026-10-21): anything over 2,000 credits needs Tim's approval of the estimate first. Both pull paths are
capped by --approved-credits and stop before x-requests-remaining would fall under the 100,000 reserve:
  --sample  one game per month (first tip on or after the 15th): market availability + ladder depth only
  --full    every game; responses cached in data/nba/raw/odds_hist_props/ (the sample's files are reused), then
            parsed to data/nba/lines/hist_props_<season>.parquet (one row per outcome, with snapshot time)
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import timedelta

from pathlib import Path

import pandas as pd

from engine.nba import http
from engine.nba.hist_lines import DATA, RAW as SNAPSHOTS, RESERVE, log_usage
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


URL = "https://api.the-odds-api.com/v4/historical/sports/basketball_nba/events/{eid}/odds"
SAMPLE_RAW = DATA / "raw" / "odds_hist_props"
SAMPLE_OUT = DATA / "lines" / "props_coverage_sample_{season}.json"


def sample_games(p: pd.DataFrame) -> pd.DataFrame:
    """one game per month, fixed before looking: the earliest tip on the first date >= the 15th that has games"""
    p = p.assign(month=p.date.str[:7]).sort_values(["date", "commence"])
    pick = [g[g.date >= f"{m}-15"].head(1) if (g.date >= f"{m}-15").any() else g.head(1) for m, g in p.groupby("month")]
    return pd.concat(pick)


def coverage(d: dict) -> dict:
    """markets returned, players, ladder depth; prices are deliberately not read"""
    out = {}
    for b in d.get("data", {}).get("bookmakers", []):
        for m in b["markets"]:
            players = {}
            for o in m["outcomes"]:
                players.setdefault(o.get("description"), set()).add((o["name"], o.get("point")))
            out[m["key"]] = {"players": len(players), "outcomes": len(m["outcomes"]),
                             "max_rungs": max(len(v) for v in players.values()),
                             "sides": sorted({n for v in players.values() for n, _ in v})}
    return out


def fetch(g, key: str) -> tuple[dict, int, int | None]:
    """one game's historical props snapshot: (response, credits charged, remaining); cached responses cost 0"""
    path = SAMPLE_RAW / f"{g.event_id}_{g.snapshot_at:%Y%m%dT%H%M}.json"
    if path.exists():
        return json.loads(path.read_text()), 0, None
    r = http.get(URL.format(eid=g.event_id), {"apiKey": key, "regions": "us", "bookmakers": "draftkings",
                                              "markets": ",".join(MAIN + ALT), "oddsFormat": "american",
                                              "date": g.snapshot_at.strftime("%Y-%m-%dT%H:%M:%SZ")}, timeout=60)
    h = r.headers
    log_usage("historical props", 1, h.get("x-requests-used"), h.get("x-requests-remaining"), h.get("x-requests-last"))
    d = r.json()
    path.write_text(json.dumps(d))
    rem = h.get("x-requests-remaining")
    return d, int(h.get("x-requests-last") or 0), int(float(rem)) if rem else None


def parse_props(d: dict, g) -> list[dict]:
    """one row per DK outcome; PREGAME ONLY: refuses a snapshot taken at or after the tip"""
    snap = d.get("timestamp")
    if snap and pd.Timestamp(snap) >= pd.Timestamp(g.commence):
        raise ValueError(f"{g.game_id}: snapshot {snap} is not before tip {g.commence}")
    rows = []
    for b in d.get("data", {}).get("bookmakers", []):
        for m in b["markets"]:
            for o in m["outcomes"]:
                rows.append({"game_id": g.game_id, "event_id": g.event_id, "snapshot": snap, "commence": g.commence,
                             "market": m["key"], "player": o.get("description"), "side": o["name"],
                             "point": o.get("point"), "price": o.get("price"), "market_update": m.get("last_update")})
    return rows


def run_full(season: str, approved: int):
    key = os.environ["ODDS_API_KEY"]
    games = plan(season)
    per_call = PER_MARKET * (len(MAIN) + len(ALT))
    SAMPLE_RAW.mkdir(parents=True, exist_ok=True)
    spent, rows = 0, []
    for i, g in enumerate(games.itertuples()):
        cached = (SAMPLE_RAW / f"{g.event_id}_{g.snapshot_at:%Y%m%dT%H%M}.json").exists()
        if not cached and spent + per_call > approved:
            raise SystemExit(f"stopping at game {i}: next call could pass the approved {approved:,} (spent {spent:,})")
        d, cost, rem = fetch(g, key)
        spent += cost
        if rem is not None and rem - per_call < RESERVE:
            raise SystemExit(f"stopping at game {i}: remaining {rem:,} is near the {RESERVE:,} reserve")
        rows += parse_props(d, g)
        if i % 100 == 0:
            print(f"  {i}/{len(games)} games, {spent:,} credits", flush=True)
    df = pd.DataFrame(rows)
    out = DATA / "lines" / f"hist_props_{season}.parquet"
    df.to_parquet(out, index=False, compression="zstd")
    print(f"wrote {out.relative_to(DATA.parents[1])}: {len(df):,} outcomes from {df.game_id.nunique()} games; "
          f"{spent:,} credits this run")


def run_sample(season: str, approved: int):
    key = os.environ["ODDS_API_KEY"]
    games = sample_games(plan(season))
    planned = len(games) * PER_MARKET * (len(MAIN) + len(ALT))
    if planned > approved:
        raise SystemExit(f"refusing: worst case {planned:,} credits > approved {approved:,}")
    SAMPLE_RAW.mkdir(parents=True, exist_ok=True)
    spent, rows = 0, []
    for g in games.itertuples():
        if spent + PER_MARKET * (len(MAIN) + len(ALT)) > approved:
            raise SystemExit(f"stopping: next call could pass the approved {approved:,} (spent {spent})")
        ts = g.snapshot_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        r = http.get(URL.format(eid=g.event_id), {"apiKey": key, "regions": "us", "bookmakers": "draftkings",
                                                  "markets": ",".join(MAIN + ALT), "oddsFormat": "american",
                                                  "date": ts}, timeout=60)
        h = r.headers
        log_usage("historical props coverage sample", 1, h.get("x-requests-used"), h.get("x-requests-remaining"),
                  h.get("x-requests-last"))
        spent += int(h.get("x-requests-last") or 0)
        d = r.json()
        (SAMPLE_RAW / f"{g.event_id}_{g.snapshot_at:%Y%m%dT%H%M}.json").write_text(json.dumps(d))
        cov = coverage(d)
        rows.append({"date": g.date, "game": f"{g.away}@{g.home}", "game_id": g.game_id, "snapshot_requested": ts,
                     "snapshot_returned": d.get("timestamp"), "credits": int(h.get("x-requests-last") or 0),
                     "markets_returned": sorted(cov), "detail": cov})
        print(f"{g.date} {g.away}@{g.home}: {len(cov)} markets, {h.get('x-requests-last')} credits", flush=True)
    keys = MAIN + ALT
    summary = {"season": season, "games": len(rows), "credits_spent": spent, "approved": approved,
               "market_games_returned": {k: sum(k in r["markets_returned"] for r in rows) for k in keys},
               "games": rows}
    out = Path(str(SAMPLE_OUT).format(season=season))
    out.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out}: {spent} credits")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2025-26")
    ap.add_argument("--sample", action="store_true", help="pull the approved one-game-per-month coverage sample")
    ap.add_argument("--full", action="store_true", help="pull every game of the season (approved)")
    ap.add_argument("--approved-credits", type=int, default=0)
    a = ap.parse_args()
    if a.full:
        return run_full(a.season, a.approved_credits)
    if a.sample:
        return run_sample(a.season, a.approved_credits)
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
