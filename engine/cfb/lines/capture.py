"""DraftKings CFB line capture via The Odds API (Phase 4 brief §2).

    python -m engine.cfb.lines.capture --label open_watch --ladders first_seen
    python -m engine.cfb.lines.capture --label bet --ladders targets
    python -m engine.cfb.lines.capture --label close --ladders before_next --next-hours 4
    python -m engine.cfb.lines.capture --label late --ladders none
    add --dry-run to spend 0 credits (free /events call only; prints the plan)

Costs (verified in the v4 docs and response headers, 2026-10-12):
  /events                         free
  /odds (bulk), DK only           1 per market: spreads+totals+h2h = 3 per snapshot
  /events/{id}/odds alt spreads   1 per event, only when DK returns the market
Every paid call is logged to data/cfb/lines/odds_usage_cfb.csv, a separate file
from automation/lines/odds_usage.csv (NFL's weekly budget guard sums that file).

Guards (protect the NFL card pulls on the shared key):
  * refuses any paid call if x-requests-remaining < CFB_ODDS_RESERVE (default 100,000)
  * refuses if this cycle's CFB credits would pass CFB_ODDS_CYCLE_CAP (default 3,000)
  * ladder calls per snapshot capped at --ladder-cap (default 30)
PREGAME ONLY: games that have kicked off are never written.

Inputs (committed, so GitHub Actions can run this without the CFBD cache):
  data/cfb/lines/schedule_<season>.csv          written by update_week
  data/cfb/lines/targets/targets_<season>_wk<NN>.csv  written by project_week
  data/cfb/manual/ladder_watch.csv              Tim's flags (game_id or team, week, note)
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
LINES = ROOT / "data" / "cfb" / "lines"
SNAP = LINES / "snapshots"
TARGETS = LINES / "targets"
USAGE = LINES / "odds_usage_cfb.csv"
UNMAPPED = LINES / "unmapped_events.csv"
WATCH = ROOT / "data" / "cfb" / "manual" / "ladder_watch.csv"
API = "https://api.the-odds-api.com/v4"
SPORT = "americanfootball_ncaaf"
MAIN_MARKETS = "spreads,totals,h2h"
EDGE_MIN = 1.5
RESERVE = int(os.environ.get("CFB_ODDS_RESERVE", "100000"))
CYCLE_CAP = int(os.environ.get("CFB_ODDS_CYCLE_CAP", "3000"))
USAGE_COLS = ["captured_at_utc", "label", "endpoint", "events", "cost", "used", "remaining"]

# CFBD name -> how the Odds API starts the team name, where they differ
ALIASES = {
    "massachusetts": "umass", "southern miss": "southern mississippi",
    "uconn": "uconn", "app state": "appalachian state", "louisiana": "louisiana ragin",
    "nc state": "nc state", "ole miss": "ole miss", "sam houston": "sam houston",
    "hawaii": "hawaii", "san jose state": "san jose state", "utsa": "utsa", "utep": "utep",
    "ucf": "ucf", "smu": "smu", "tcu": "tcu", "byu": "byu", "lsu": "lsu", "usc": "usc",
    "ucla": "ucla", "unlv": "unlv", "fiu": "florida international", "florida international": "florida international",
    "miami": "miami hurricanes", "miami oh": "miami oh",
}


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", "").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def key() -> str:
    k = os.environ.get("ODDS_API_KEY", "")
    if not k:
        env = ROOT / ".env"
        if env.exists():
            from dotenv import dotenv_values
            k = dotenv_values(env).get("ODDS_API_KEY") or ""
    k = k.strip()
    if not k:
        sys.exit("ODDS_API_KEY not set")
    return k


def call(path: str, params: dict):
    import requests
    r = requests.get(API + path, params={**params, "apiKey": key()}, timeout=60)
    h = {x: r.headers.get(x) for x in ("x-requests-used", "x-requests-remaining", "x-requests-last")}
    if r.status_code != 200:
        raise RuntimeError(f"Odds API {path} -> HTTP {r.status_code}: {r.text[:200]}")
    return r.json(), h


def log_usage(label, endpoint, events, h):
    LINES.mkdir(parents=True, exist_ok=True)
    new = not USAGE.exists()
    with open(USAGE, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(USAGE_COLS)
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), label, endpoint,
                    events, h.get("x-requests-last"), h.get("x-requests-used"),
                    h.get("x-requests-remaining")])


def cycle_spent(used_now: int) -> int:
    """CFB credits since the current quota cycle began (x-requests-used resets each cycle)."""
    if not USAGE.exists():
        return 0
    u = pd.read_csv(USAGE)
    if u.empty:
        return 0
    u = u.dropna(subset=["used"])
    # rows from the current cycle: 'used' never exceeds the current value within a cycle
    cur = u[u.used.astype(int) <= used_now]
    after_reset = cur.index[cur.used.astype(int).diff().fillna(0) < 0]
    if len(after_reset):
        cur = cur.loc[after_reset[-1]:]
    return int(pd.to_numeric(cur.cost, errors="coerce").fillna(0).sum())


def guard(h: dict, planned: int):
    rem, used = int(h["x-requests-remaining"]), int(h["x-requests-used"])
    spent = cycle_spent(used)
    if rem - planned < RESERVE:
        sys.exit(f"STOP: {rem} credits left; spending ~{planned} would go under the "
                 f"{RESERVE:,} NFL reserve")
    if spent + planned > CYCLE_CAP:
        sys.exit(f"STOP: CFB has spent {spent} this cycle; ~{planned} more passes the "
                 f"{CYCLE_CAP:,} CFB cap")
    return spent


# ------------------------------------------------------------------ mapping
def schedule(season: int) -> pd.DataFrame:
    p = LINES / f"schedule_{season}.csv"
    if not p.exists():
        sys.exit(f"missing {p}; run python -m engine.cfb.update_week")
    s = pd.read_csv(p)
    s["kickoff_utc"] = pd.to_datetime(s.kickoff_utc, utc=True)
    return s


def team_matcher(cfbd_names):
    keys = {}
    for n in cfbd_names:
        k = norm(n)
        keys[n] = ALIASES.get(k, k)

    def match(odds_name: str):
        o = norm(odds_name)
        hits = [(len(v), n) for n, v in keys.items() if o == v or o.startswith(v + " ")]
        return max(hits)[1] if hits else None
    return match


def map_events(events: list, sched: pd.DataFrame) -> pd.DataFrame:
    match = team_matcher(set(sched.home_team) | set(sched.away_team))
    rows, bad = [], []
    for e in events:
        h, a = match(e["home_team"]), match(e["away_team"])
        t = pd.Timestamp(e["commence_time"])
        cand = sched[(sched.kickoff_utc - t).abs() <= pd.Timedelta(hours=36)]
        g = cand[((cand.home_team == h) & (cand.away_team == a)) |
                 ((cand.home_team == a) & (cand.away_team == h))] if h and a else cand.iloc[0:0]
        if len(g) == 1:
            r = g.iloc[0]
            rows.append({"event_id": e["id"], "game_id": int(r.game_id), "week": int(r.week),
                         "season_type": r.season_type, "cfbd_home": r.home_team,
                         "both_fbs": bool(r.both_fbs)})
        else:
            bad.append({"event_id": e["id"], "commence_time": e["commence_time"],
                        "home_team": e["home_team"], "away_team": e["away_team"],
                        "cfbd_home": h, "cfbd_away": a, "candidates": len(g)})
    return pd.DataFrame(rows), pd.DataFrame(bad)


# ------------------------------------------------------------------ targets
def targets(season: int, weeks, main: pd.DataFrame) -> pd.DataFrame:
    """Games to ladder: |frozen-model edge vs the DK line in THIS snapshot| >= 1.5, or watch-listed."""
    rows = []
    for w in weeks:
        p = TARGETS / f"targets_{season}_wk{w:02d}.csv"
        if p.exists():
            rows.append(pd.read_csv(p))
    t = pd.concat(rows) if rows else pd.DataFrame(columns=["game_id"])
    dk = main[(main.market == "spreads") & (main.is_home == 1)][["game_id", "point"]]
    t = t.merge(dk, on="game_id", how="inner") if len(t) else t
    if len(t):
        line_m = -t.point
        t["edge"] = t.k * (t.ratings_margin - line_m) + t.b_qb * t.qb_delta
        t = t[(t.edge.abs() >= EDGE_MIN) & t.both_fbs & (t.week >= 4)]
    watch = set()
    if WATCH.exists():
        wl = pd.read_csv(WATCH, dtype=str).fillna("")
        for r in wl.itertuples():
            if r.game_id:
                watch.add(int(r.game_id))
            elif r.team:
                watch |= set(main[(main.cfbd_home.str.lower() == r.team.lower())].game_id)
    ids = list(t.sort_values("edge", key=abs, ascending=False).game_id) if len(t) else []
    ids += [g for g in watch if g not in ids]
    return pd.DataFrame({"game_id": ids, "watch": [g in watch for g in ids]})


# ------------------------------------------------------------------ snapshot
def write_rows(df: pd.DataFrame, prefix: str, season: int):
    SNAP.mkdir(parents=True, exist_ok=True)
    for w, part in df.groupby(df.week.fillna(0).astype(int)):
        name = f"{prefix}_{season}_wk{w:02d}.csv" if w else f"{prefix}_{season}_unmapped.csv"
        path = SNAP / name
        part.to_csv(path, mode="a", header=not path.exists(), index=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--label", required=True, choices=["open_watch", "bet", "late", "close", "manual"])
    ap.add_argument("--ladders", default="none",
                    choices=["none", "targets", "all", "first_seen", "before_next"])
    ap.add_argument("--skip-if-idle", action="store_true",
                    help="close slots: make no paid call if nothing kicks off within --next-hours")
    ap.add_argument("--next-hours", type=float, default=4.0,
                    help="before_next: ladder target games kicking off within this many hours")
    ap.add_argument("--ladder-cap", type=int, default=int(os.environ.get("CFB_LADDER_CAP", "70")))
    ap.add_argument("--dry-run", action="store_true", help="free /events call only")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    ts = now.isoformat(timespec="seconds")

    events, h = call(f"/sports/{SPORT}/events", {})            # free
    events = [e for e in events if pd.Timestamp(e["commence_time"]) > now]
    sched = schedule(a.season)
    m, bad = map_events(events, sched)
    if len(bad):
        bad.assign(seen_at_utc=ts).to_csv(UNMAPPED, mode="a", header=not UNMAPPED.exists(), index=False)
    print(f"{ts}: {len(events)} upcoming DK/NCAAF events, {len(m)} mapped, {len(bad)} unmapped "
          f"(logged); quota used {h['x-requests-used']}, remaining {h['x-requests-remaining']}")
    if a.skip_if_idle:
        soon = [e for e in events if pd.Timestamp(e["commence_time"]) <= now + timedelta(hours=a.next_hours)]
        if not soon:
            print(f"no kickoffs in the next {a.next_hours:g}h: skipping (0 credits)")
            return 0
    planned = 3 + (min(a.ladder_cap, len(m)) if a.ladders != "none" else 0)
    spent = guard(h, planned)
    print(f"CFB spent this cycle: {spent}; this run plans up to {planned} credits")
    if a.dry_run:
        if len(bad):
            print(bad.to_string(index=False))
        return 0

    data, h = call(f"/sports/{SPORT}/odds", {"regions": "us", "bookmakers": "draftkings",
                                              "markets": MAIN_MARKETS, "oddsFormat": "american"})
    log_usage(a.label, "odds:spreads,totals,h2h", len(data), h)
    emap = m.set_index("event_id")
    rows = []
    for e in data:
        if pd.Timestamp(e["commence_time"]) <= now:
            continue                                            # pregame only
        info = emap.loc[e["id"]] if e["id"] in emap.index else None
        for b in e.get("bookmakers", []):
            for mk in b["markets"]:
                for o in mk["outcomes"]:
                    rows.append({"captured_at_utc": ts, "label": a.label, "event_id": e["id"],
                                 "game_id": None if info is None else int(info.game_id),
                                 "week": None if info is None else int(info.week),
                                 "commence_time": e["commence_time"], "home_team": e["home_team"],
                                 "away_team": e["away_team"],
                                 "cfbd_home": None if info is None else info.cfbd_home,
                                 "market": mk["key"], "team": o["name"],
                                 "is_home": int(o["name"] == e["home_team"]),
                                 "point": o.get("point"), "price": o.get("price"),
                                 "dk_last_update": mk.get("last_update")})
    main_df = pd.DataFrame(rows)
    write_rows(main_df, "dk_main", a.season)
    print(f"main: {main_df.event_id.nunique() if len(main_df) else 0} games, cost {h['x-requests-last']}")

    if a.ladders != "none" and len(main_df):
        mapped = main_df.dropna(subset=["game_id"]).copy()
        mapped["game_id"] = mapped.game_id.astype(int)
        mapped = mapped.merge(m[["game_id", "both_fbs"]].drop_duplicates(), on="game_id", how="left")
        weeks = sorted(set(mapped.week.dropna().astype(int)))
        if a.ladders in ("all", "before_next"):     # every FBS-vs-FBS game, week >= 4
            allg = mapped[(mapped.both_fbs == True) & (mapped.week >= 4)].drop_duplicates("game_id")  # noqa: E712
            tg = pd.DataFrame({"game_id": allg.sort_values("commence_time").game_id, "watch": False})
        else:
            tg = targets(a.season, weeks, mapped)
        ev = mapped.drop_duplicates("game_id").set_index("game_id")
        if a.ladders == "first_seen":
            seen = set()
            for w in weeks:
                p = SNAP / f"dk_ladders_{a.season}_wk{w:02d}.csv"
                if p.exists():
                    seen |= set(pd.read_csv(p, usecols=["game_id"]).game_id.dropna().astype(int))
            tg = tg[~tg.game_id.isin(seen)]
        elif a.ladders == "before_next":
            soon = ev[pd.to_datetime(ev.commence_time, utc=True) <= now + timedelta(hours=a.next_hours)].index
            tg = tg[tg.game_id.isin(soon)]
        tg = tg.head(a.ladder_cap)
        lrows, spent_l = [], 0
        for gid in tg.game_id:
            eid = ev.loc[gid, "event_id"]
            d, h = call(f"/sports/{SPORT}/events/{eid}/odds",
                        {"regions": "us", "bookmakers": "draftkings",
                         "markets": "alternate_spreads", "oddsFormat": "american"})
            log_usage(a.label, "event:alternate_spreads", 1, h)
            spent_l += int(h.get("x-requests-last") or 0)
            for b in d.get("bookmakers", []):
                for mk in b["markets"]:
                    for o in mk["outcomes"]:
                        lrows.append({"captured_at_utc": ts, "label": a.label, "event_id": eid,
                                      "game_id": gid, "week": int(ev.loc[gid, "week"]),
                                      "commence_time": d.get("commence_time"),
                                      "home_team": d.get("home_team"), "away_team": d.get("away_team"),
                                      "team": o["name"], "is_home": int(o["name"] == d.get("home_team")),
                                      "rung": o.get("point"), "price": o.get("price"),
                                      "dk_last_update": mk.get("last_update")})
        if lrows:
            write_rows(pd.DataFrame(lrows), "dk_ladders", a.season)
        print(f"ladders: {len(tg)} games requested, {len({r['game_id'] for r in lrows})} returned, "
              f"cost {spent_l}")
    print(f"quota remaining {h['x-requests-remaining']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
