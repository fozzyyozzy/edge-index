"""
settle.py — write each final game's results into the week's legs JSON, so the Legs tab can show hits and misses the
morning after a game instead of waiting for Tuesday.
  python pipeline/settle.py --season 2026 --week 4            (every slate's legs file for that week)
Adds, per player/market row: `actual` (the stat, or null when the game is final but the player has no stat row =
void) and `settled: true`; per rung: `result` = "hit" | "miss" | "void". Nothing else is touched — grades, prices and
published fields stay as they are. A game is settled only when the nflverse schedule shows it final AND the weekly stats
file already has rows for its teams; otherwise its rows are left unsettled. Idempotent: re-running rewrites the same
values. Also refreshes the site copy (cfb-app/public/data/nfl_legs_<slate>.json) when it is the same week.
"""
import argparse, json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import norm_name, COL, fetch_week, P
from floors import schedule

SLATES = ("tnf", "sun", "mnf")
SITE = os.path.join(os.path.dirname(P("cards", "x.json")), "..", "..", "cfb-app", "public", "data")

def settled_teams(season, week, w):
    """teams whose game is final in the schedule and present in the weekly stats file"""
    sch = schedule(season, week)
    final = sch[sch.result.notna()] if "result" in sch else sch.iloc[0:0]
    in_stats = set(w.team.dropna()) if len(w) else set()
    out = set()
    for g in final.itertuples():
        if g.home_team in in_stats or g.away_team in in_stats:      # stats file has caught up with this game
            out.update((g.home_team, g.away_team))
    return out

def settle_rows(players, act, teams):
    """mutates players in place; returns how many rows were settled"""
    n = 0
    for p in players:
        if p.get("team") not in teams: continue
        v = act.get((norm_name(p["player"]), p["market"]))
        actual = None if v is None or pd.isna(v) else float(v)
        p["actual"], p["settled"] = actual, True
        for r in p["rungs"]:
            r["result"] = "void" if actual is None else ("hit" if actual >= r["rung"] else "miss")
        n += 1
    return n

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    try:
        w = fetch_week(a.season, a.week)
    except Exception as ex:                                            # stats release not there yet
        print(f"no nflverse stats for {a.season} w{a.week} yet ({ex}); nothing settled"); return
    act = {(k, m): v for m, c in COL.items() for k, v in zip(w.key, w[c])}
    teams = settled_teams(a.season, a.week, w)
    for s in SLATES:
        path = P("cards", f"legs_{a.season}_w{a.week}_{s}.json")
        if not os.path.exists(path): continue
        d = json.load(open(path)); before = json.dumps(d, sort_keys=True)
        n = settle_rows(d["players"], act, teams)
        after = json.dumps(d, sort_keys=True)
        if after != before:
            json.dump(d, open(path, "w"), separators=(",", ":"), allow_nan=False)
        site = os.path.join(SITE, f"nfl_legs_{s}.json")
        if os.path.exists(site) and json.load(open(site)).get("meta", {}).get("week") == a.week and after != before:
            json.dump(d, open(site, "w"), separators=(",", ":"), allow_nan=False)
        print(f"w{a.week} {s}: {n} rows settled" + ("" if after != before else " (no change)"))

if __name__ == "__main__":
    main()
