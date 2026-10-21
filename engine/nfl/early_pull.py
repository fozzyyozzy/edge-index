"""Early-line / cross-book / game-line pulls for docs/nfl/PREREG_EARLY_LINES.md (2025 regular season, all US books).

    python -m engine.nfl.early_pull --dry-run
    python -m engine.nfl.early_pull --approved-credits 42000      # resumable; one shared budget for all three pulls

Order (cheapest first): game lines (bulk spreads/totals at OPEN, E72, E24, CLOSE per kickoff window), props at CLOSE
with all US books, props at E24, props at E72. regions=us returns every US book for the cost of one region.
The approved cap covers every call logged here with kind starting "early:" (resumes count what's already spent).
Event ids come from the cached /events lookups (data/nfl/verify/raw/events_by_date.json): no id lookups are paid.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from engine.nfl import verify_pull as vp

RAW = vp.RAW / "early"
MARKETS = vp.MARKETS
PROPS = {"E72": timedelta(hours=72), "E24": timedelta(hours=24), "CLOSE_ALL": timedelta(minutes=10)}
ET = ZoneInfo("America/New_York")


def spent_so_far() -> int:
    if not vp.USAGE.exists():
        return 0
    u = pd.read_csv(vp.USAGE)
    u = u[u.kind.astype(str).str.startswith("early:")]
    return int(pd.to_numeric(u.x_requests_last, errors="coerce").fillna(0).sum())


def game_line_times(g: pd.DataFrame) -> list[tuple[str, datetime]]:
    """(tag, UTC time): OPEN per week (previous Sunday 23:55 ET before the week's first kickoff), then per kickoff
    window E72, E24, CLOSE (kickoff - 10 min)"""
    out = []
    for wk, d in g.groupby("week"):
        first = d.kickoff.min().astimezone(ET)
        sunday = (first - timedelta(days=(first.weekday() + 1) % 7 or 7)).date()
        out.append((f"OPEN_w{wk}", datetime.combine(sunday, datetime.min.time(), ET).replace(hour=23, minute=55)
                    .astimezone(timezone.utc)))
    for ko in sorted(g.kickoff.unique()):
        ko = pd.Timestamp(ko).to_pydatetime()
        for tag, lead in (("E72", timedelta(hours=72)), ("E24", timedelta(hours=24)), ("CLOSE", timedelta(minutes=10))):
            out.append((f"{tag}_{ko:%Y%m%dT%H%M}", ko - lead))
    seen, uniq = set(), []
    for tag, t in out:
        k = t.strftime("%Y%m%dT%H%M")
        if k not in seen:
            seen.add(k); uniq.append((tag, t))
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approved-credits", type=int, default=0)
    a = ap.parse_args()
    g = vp.schedule()
    g = g[g.game_type == "REG"].reset_index(drop=True)
    lines_t = game_line_times(g)
    worst = len(lines_t) * 20 + len(g) * len(PROPS) * 40
    print(f"{len(g)} REG games; {len(lines_t)} game-line snapshots (<= {len(lines_t) * 20:,}); "
          f"{len(g) * len(PROPS)} prop calls (<= {len(g) * len(PROPS) * 40:,}); worst case {worst:,}; "
          f"already spent on early: {spent_so_far():,}")
    if a.dry_run:
        return
    key = os.environ["ODDS_API_KEY"]
    (RAW / "lines").mkdir(parents=True, exist_ok=True)
    (RAW / "props").mkdir(parents=True, exist_ok=True)
    budget = vp.Budget(a.approved_credits)
    budget.spent = spent_so_far()

    def call(url, params, kind, worst_cost):
        budget.check(worst_cost)
        r = vp.get(url, {"apiKey": key, **params})
        vp.log_usage(f"early:{kind}", r.headers)
        budget.charge(r.headers, worst_cost)
        return r.json()

    for tag, t in lines_t:                                           # 1. game lines (bulk)
        f = RAW / "lines" / f"{t:%Y%m%dT%H%M}_{tag.split('_')[0]}.json"
        if not f.exists():
            d = call(f"{vp.BASE}/odds", {"regions": "us", "markets": "spreads,totals", "oddsFormat": "american",
                                         "date": t.strftime("%Y-%m-%dT%H:%M:%SZ")}, "game lines", 20)
            f.write_text(json.dumps(d))
    ids = json.loads((vp.RAW / "events_by_date.json").read_text())
    idmap = {}
    for evs in ids.values():
        for e in evs:
            if e.get("home_team") in vp.TEAMS and e.get("away_team") in vp.TEAMS:
                idmap[(vp.TEAMS[e["home_team"]], vp.TEAMS[e["away_team"]], e["commence_time"][:10])] = e["id"]
    missing = []
    for snap in ("CLOSE_ALL", "E24", "E72"):                          # 2-4. props, all US books
        for row in g.itertuples():
            eid = vp.lookup(idmap, row)
            if not eid:
                missing.append((snap, row.game_id)); continue
            f = RAW / "props" / f"{row.game_id}_{snap}.json"
            if f.exists():
                continue
            t = row.kickoff - PROPS[snap]
            d = call(f"{vp.BASE}/events/{eid}/odds", {"regions": "us", "markets": ",".join(MARKETS),
                                                       "oddsFormat": "american", "date": t.strftime("%Y-%m-%dT%H:%M:%SZ")},
                     f"props {snap}", 40)
            f.write_text(json.dumps(d))
        print(f"  {snap}: done; spent {budget.spent:,}", flush=True)
    # parse
    prows = []
    for row in g.itertuples():
        for snap in PROPS:
            f = RAW / "props" / f"{row.game_id}_{snap}.json"
            if not f.exists():
                continue
            d = json.loads(f.read_text())
            ts = d.get("timestamp")
            if ts and pd.Timestamp(ts) >= pd.Timestamp(row.kickoff):
                raise ValueError(f"{row.game_id} {snap}: snapshot {ts} not before kickoff")
            for b in d.get("data", {}).get("bookmakers", []):
                for m in b["markets"]:
                    for o in m["outcomes"]:
                        prows.append(dict(game_id=row.game_id, week=int(row.week), snap=snap, kickoff=row.kickoff.isoformat(),
                                          snapshot=ts, book=b["key"], market=m["key"], player=o.get("description"),
                                          side=o["name"], point=o.get("point"), price=o.get("price"),
                                          home_team=row.home_team, away_team=row.away_team))
    pd.DataFrame(prows).to_parquet(vp.OUT / "early_props_2025.parquet", index=False, compression="zstd")
    lrows = []
    for f in sorted((RAW / "lines").glob("*.json")):
        d = json.loads(f.read_text())
        tag = f.stem.split("_", 1)[1]
        for e in d.get("data", []):
            if e.get("home_team") not in vp.TEAMS or e.get("away_team") not in vp.TEAMS:
                continue
            if pd.Timestamp(e["commence_time"]) <= pd.Timestamp(d.get("timestamp")):
                continue                                                # started: never stored (rule 1)
            for b in e.get("bookmakers", []):
                for m in b["markets"]:
                    for o in m["outcomes"]:
                        lrows.append(dict(snap_tag=tag, snapshot=d.get("timestamp"), event_id=e["id"],
                                          commence=e["commence_time"], home_team=vp.TEAMS[e["home_team"]],
                                          away_team=vp.TEAMS[e["away_team"]], book=b["key"], market=m["key"],
                                          name=o["name"], point=o.get("point"), price=o.get("price")))
    pd.DataFrame(lrows).to_parquet(vp.OUT / "game_lines_2025.parquet", index=False, compression="zstd")
    print(f"wrote early_props_2025.parquet ({len(prows):,} outcomes) and game_lines_2025.parquet ({len(lrows):,}); "
          f"spent {budget.spent:,} of {a.approved_credits:,}; missing ids: {len(missing)}")


if __name__ == "__main__":
    main()
