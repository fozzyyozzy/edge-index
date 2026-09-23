"""
usage.py — per-game usage for every player in this week's legs files, for the usage row in the Legs tab's expanded ladder.
  python pipeline/usage.py --season 2026 --week 3
Reads  cards/legs_<season>_w<week>_*.json (every slate graded so far this week)
Writes cards/usage_<season>_w<week>.json  -> site: public/data/nfl_usage.json
Per player, two windows: current season (weeks strictly before --week; walk-forward) and the previous season.
  tgt rec recyd car rushyd att passyd = per game played
  tgt_share / car_share = player's targets (carries) / his team's targets (carries), summed over the games he played, in %
"""
import argparse, glob, json, os, sys
from datetime import datetime, timezone
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fetch_season, norm_name, P

STATS = {"tgt": "targets", "rec": "receptions", "recyd": "receiving_yards", "car": "carries",
         "rushyd": "rushing_yards", "att": "attempts", "passyd": "passing_yards"}

def window(rows, team_tot):
    """rows: one player's game rows in one season -> per-game usage dict, or None if he did not play."""
    if not len(rows): return None
    out = {"games": int(rows.week.nunique()), "team": rows.sort_values("week").team.iloc[-1]}
    for k, col in STATS.items():
        out[k] = round(float(rows[col].fillna(0).mean()), 1)
    tot = rows.merge(team_tot, on=["season", "week", "team"], how="left")
    for k, col in (("tgt_share", "targets"), ("car_share", "carries")):
        den = tot[col + "_team"].sum()
        out[k] = round(100 * float(rows[col].fillna(0).sum()) / den, 1) if den else None
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    files = sorted(glob.glob(P("cards", f"legs_{a.season}_w{a.week}_*.json")))
    if not files: raise SystemExit(f"no legs files for w{a.week}: run grade_legs.py first")
    wanted = {}                                                    # key -> (display name, current team)
    for f in files:
        for p in json.load(open(f))["players"]:
            wanted.setdefault(norm_name(p["player"]), (p["player"], p.get("team")))

    prev, cur = fetch_season(a.season - 1), fetch_season(a.season)
    cur = cur[cur.week < a.week]                                   # walk-forward: nothing from this week or later
    w = pd.concat([prev, cur])
    team_tot = (w.groupby(["season", "week", "team"])[["targets", "carries"]].sum()
                 .add_suffix("_team").reset_index())

    players, missing = [], []
    for key, (name, team) in sorted(wanted.items(), key=lambda kv: kv[1][0]):
        g = w[w.key == key]
        if not len(g): missing.append(name); continue
        players.append(dict(player=name, team=team, pos=g.sort_values(["season", "week"]).position.iloc[-1],
                            cur=window(g[g.season == a.season], team_tot),
                            prev=window(g[g.season == a.season - 1], team_tot)))
    gp = int(cur.week.nunique())
    meta = dict(season=a.season, week=a.week, generated=datetime.now(timezone.utc).isoformat(timespec="minutes"),
                windows={"cur": f"{a.season} wks 1-{gp}" if gp else f"{a.season} (no games yet)", "prev": str(a.season - 1)},
                note="per game played; shares = player's targets/carries over his team's, in the games he played")
    out = P("cards", f"usage_{a.season}_w{a.week}.json")
    json.dump(dict(meta=meta, players=players), open(out, "w"), indent=1, allow_nan=False)
    print(f"wrote {out}: {len(players)} players from {len(files)} legs file(s)" + (f"; no nflverse rows for {missing}" if missing else ""))

if __name__ == "__main__":
    main()
