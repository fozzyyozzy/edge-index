"""
matchups.py — defense-vs-position board for the Matchups tab (heat map) + this week's Edge Leans.
  python pipeline/matchups.py --season 2026 --week 3
Writes cards/matchups_<season>_w<week>.json:
  defenses[]: team, per slot {yds_pg, rank, home_yds_pg, away_yds_pg, n_games}; slots = QB RB WR1 WR2 TE RUN PASS
  edge_leans[]: every slate player/slot facing a bottom-8 defense (soft) or top-8 (tough), with home/away
Slot definitions (per game, per opposing offense):
  QB  = passing yards by the opponent's QB(s)         RUN  = opponent rushing yards (team)
  RB  = rushing yards by opponent RBs                  PASS = opponent passing yards (team)
  WR1 = rec yds of the opponent WR with the most targets that game; WR2 = second-most; TE = opponent TEs' rec yds
Blend: prev season weighted (1-w), current w = min(0.6, games/8). Ranks: 1 = fewest allowed (tough) ... 32 = most (soft).
"""
import argparse, json, os, sys
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fetch_season, norm_name, P
from floors import schedule

SLOTS = ["QB", "RB", "WR1", "WR2", "TE", "RUN", "PASS"]

def slot_table(w):
    """rows: (defense, season, week, slot, yds, home) — yards allowed by that defense to that slot in that game"""
    rows = []
    # need home/away for the defense: nflverse weekly lacks it directly; derive from schedules later, here mark None
    for (opp, season, week), g in w.groupby(["opponent_team", "season", "week"]):
        team_pass = g.passing_yards.fillna(0).sum(); team_rush = g.rushing_yards.fillna(0).sum()
        qb = g[g.position == "QB"].passing_yards.fillna(0).sum()
        rb = g[g.position == "RB"].rushing_yards.fillna(0).sum()
        te = g[g.position == "TE"].receiving_yards.fillna(0).sum()
        wrs = g[g.position == "WR"].sort_values("targets", ascending=False)
        wr1 = float(wrs.receiving_yards.iloc[0]) if len(wrs) > 0 else 0.0
        wr2 = float(wrs.receiving_yards.iloc[1]) if len(wrs) > 1 else 0.0
        for slot, v in zip(SLOTS, (qb, rb, wr1, wr2, te, team_rush, team_pass)):
            rows.append(dict(defense=opp, season=season, week=week, offense=g.team.iloc[0], slot=slot, yds=float(v)))
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    w = pd.concat([fetch_season(a.season - 1), fetch_season(a.season)])
    w = w[w.position.isin(["QB", "RB", "WR", "TE"])]
    t = slot_table(w)
    # home/away for the DEFENSE from the schedule

    import io, urllib.request
    req = urllib.request.Request("https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv", headers={"User-Agent": "Mozilla/5.0"})
    games = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()), low_memory=False)
    games = games[games.season.isin([a.season - 1, a.season])][["season", "week", "home_team", "away_team", "roof"]]
    home = {(r.season, r.week, r.home_team): True for r in games.itertuples()}
    home.update({(r.season, r.week, r.away_team): False for r in games.itertuples()})
    t["home"] = [home.get((r.season, r.week, r.defense)) for r in t.itertuples()]
    cur = t[t.season == a.season]; prev = t[t.season == a.season - 1]
    gp = cur.week.nunique() if len(cur) else 0; wgt = min(0.6, gp / 8)

    out = []
    for d in sorted(t.defense.unique()):
        row = dict(team=d, slots={})
        for s in SLOTS:
            p = prev[(prev.defense == d) & (prev.slot == s)].yds; c = cur[(cur.defense == d) & (cur.slot == s)].yds
            blend = (1 - wgt) * p.mean() + wgt * (c.mean() if len(c) else p.mean())
            allr = t[(t.defense == d) & (t.slot == s)]
            row["slots"][s] = dict(yds_pg=round(float(blend), 1), cur_pg=round(float(c.mean()), 1) if len(c) else None,
                                   prev_pg=round(float(p.mean()), 1),
                                   home_pg=round(float(allr[allr.home == True].yds.mean()), 1) if (allr.home == True).any() else None,
                                   away_pg=round(float(allr[allr.home == False].yds.mean()), 1) if (allr.home == False).any() else None,
                                   n_cur=int(len(c)))
        out.append(row)
    # ranks: 1 = fewest allowed
    for s in SLOTS:
        order = sorted(out, key=lambda r: r["slots"][s]["yds_pg"])
        for i, r in enumerate(order, 1): r["slots"][s]["rank"] = i

    # this week's edge leans from the schedule
    sch = schedule(a.season, a.week)
    rank = {r["team"]: {s: r["slots"][s]["rank"] for s in SLOTS} for r in out}
    cur_players = w[w.season == a.season].groupby(["player_display_name", "team", "position"]).agg(
        targets=("targets", "mean"), carries=("carries", "mean"), games=("week", "nunique")).reset_index()
    leans = []
    for g in sch.itertuples():
        for tm, opp, is_home in ((g.away_team, g.home_team, False), (g.home_team, g.away_team, True)):
            roster = cur_players[cur_players.team == tm]
            wrs = roster[roster.position == "WR"].sort_values("targets", ascending=False)
            slots_for = []
            for r in roster.itertuples():
                if r.position == "QB" and r.targets == r.targets: slots_for += [(r.player_display_name, "QB"), (r.player_display_name, "PASS")]
                elif r.position == "RB" and r.carries >= 8: slots_for += [(r.player_display_name, "RB"), (r.player_display_name, "RUN")]
                elif r.position == "TE" and r.targets >= 3: slots_for.append((r.player_display_name, "TE"))
            if len(wrs) > 0: slots_for.append((wrs.player_display_name.iloc[0], "WR1"))
            if len(wrs) > 1: slots_for.append((wrs.player_display_name.iloc[1], "WR2"))
            for player, s in slots_for:
                rk = rank.get(opp, {}).get(s)
                if rk is None: continue
                tag = "SOFT" if rk >= 25 else "TOUGH" if rk <= 8 else None
                if tag:
                    leans.append(dict(player=player, team=tm, opp=opp, home=is_home, slot=s, opp_rank=rk,
                                      opp_yds_pg=[x for x in out if x["team"] == opp][0]["slots"][s]["yds_pg"], tag=tag,
                                      game=f"{g.away_team}@{g.home_team}", day=g.weekday, roof=g.roof))
    leans.sort(key=lambda x: (x["tag"] != "SOFT", -x["opp_rank"] if x["tag"] == "SOFT" else x["opp_rank"]))
    meta = dict(season=a.season, week=a.week, blend=f"{1-wgt:.0%} {a.season-1} / {wgt:.0%} {a.season} ({gp} wks)",
                rank_key="1 = fewest yards allowed to that slot (tough for the offense); 32 = most (soft). WR1/WR2 = most/second-most targeted opposing WR that game.",
                slots=SLOTS)
    path = P("cards", f"matchups_{a.season}_w{a.week}.json")
    json.dump(dict(meta=meta, defenses=out, edge_leans=leans), open(path, "w"), indent=1)
    print(f"wrote {path}: {len(out)} defenses, {len(leans)} edge leans ({sum(1 for l in leans if l['tag']=='SOFT')} soft)")
    soft = [l for l in leans if l["tag"] == "SOFT"][:12]
    for l in soft: print(f"  SOFT  {l['player']:<22} {l['slot']:<4} {l['team']} {'vs' if l['home'] else '@'} {l['opp']:<3} rank {l['opp_rank']:>2} ({l['opp_yds_pg']} allowed)  {l['day']}")

if __name__ == "__main__":
    main()
