"""
Edge Index v2 — ALT-line backtest (Tim's strategy).

Tests: below-mainline alt overs (receptions, rec/rush/pass yds, attempts)
priced -120 to -500, graded straight AND as 2-leg cross-game parlays.
Alt markets are one-sided, so fair prob comes from the model distribution
(walk-forward, leak-free) rather than a two-way de-vig.

Usage:  python engine/nfl/alt_backtest.py
"""
from __future__ import annotations
import os, sqlite3, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from engine.core.odds import american_to_decimal, american_to_prob, ev_per_unit
from engine.nfl import props_engine as pe

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "..", "..", "backtest", "nfl", "edge_index.db")
# extend engine to attempt markets
pe.PROPS["rush_att"] = ("rush_att", True, 5)

ALT = {"receptions_alt": "receptions", "rec_yds_alt": "rec_yds",
       "rush_yds_alt": "rush_yds", "pass_yds_alt": "pass_yds",
       "pass_att_alt": "pass_att", "rush_att_alt": "rush_att"}
ODDS_LO, ODDS_HI = -500, -120     # the juicy below-mainline band
SEASON = 2024                     # only season with clean pregame lines


def run():
    logs = pe.load_game_logs(DB)
    con = sqlite3.connect(DB)
    q = """SELECT player_id, season, week, prop_type, line, odds,
                  REPLACE(source,'actual_','') book
           FROM prop_lines WHERE source LIKE 'actual_%' AND direction='OVER'
             AND season=? AND week<=18 AND odds BETWEEN ? AND ?
             AND prop_type IN ({})""".format(",".join(f"'{k}'" for k in ALT))
    lines = pd.read_sql(q, con, params=(SEASON, ODDS_LO, ODDS_HI))
    con.close()
    lines = lines.drop_duplicates(
        subset=["player_id", "week", "prop_type", "line", "odds", "book"])
    rows = []
    for week in sorted(lines.week.unique()):
        train = logs[(logs.season < SEASON) |
                     ((logs.season == SEASON) & (logs.week < week))]
        if len(train) < 500:
            continue
        eng = pe.PropsEngine(train)
        actuals = logs[(logs.season == SEASON) & (logs.week == week)] \
            .drop_duplicates("player_id").set_index("player_id")
        wk = lines[lines.week == week]
        for (pid, ptype, line), grp in wk.groupby(
                ["player_id", "prop_type", "line"]):
            base = ALT[ptype]
            if pid not in actuals.index:
                continue
            arow = actuals.loc[pid]
            actual = arow[pe.PROPS[base][0]]
            if pd.isna(actual):
                continue
            proj = eng.project(pid, base, arow["opponent"],
                               asof_hist=train[train.player_id == pid])
            if proj is None or not (0.15 * proj.mean <= line <= 1.1 * proj.mean):
                continue  # sanity: below-mainline alts only, junk filtered
            row = grp.sort_values("odds", ascending=False).iloc[0]  # best price
            p = proj.prob_over(line)
            rows.append(dict(
                week=week, player=proj.player, pos=proj.position, market=base,
                line=line, odds=row.odds, book=row.book,
                model_prob=round(p, 4),
                implied=round(american_to_prob(row.odds), 4),
                ev=round(ev_per_unit(p, row.odds), 4),
                actual=actual, hit=int(actual > line),
                pnl=(american_to_decimal(row.odds) - 1) if actual > line else -1.0))
    return pd.DataFrame(rows)


def report(df: pd.DataFrame):
    print(f"{len(df)} graded alt-line bets, {SEASON}")
    print("\n-- all qualifying alts by market --")
    g = df.groupby("market").agg(n=("hit", "size"), hit=("hit", "mean"),
                                 roi=("pnl", "mean"))
    print(g.round(3).to_string())
    print("\n-- by model EV threshold --")
    print(f"{'ev>=':>6} {'n':>6} {'hit%':>7} {'roi':>8}")
    for thr in (0.00, 0.02, 0.04, 0.06, 0.10):
        b = df[df.ev >= thr]
        if len(b):
            print(f"{thr:>6} {len(b):>6} {b.hit.mean():>7.1%} {b.pnl.mean():>8.2%}")
    print("\n-- 2-leg parlays: top-4 EV legs/week, different players, paired --")
    pnl, n = 0.0, 0
    for week, wk in df[df.ev >= 0.04].groupby("week"):
        legs = wk.sort_values("ev", ascending=False) \
                 .drop_duplicates("player").head(4)
        L = list(legs.itertuples())
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                a, b = L[i], L[j]
                dec = american_to_decimal(a.odds) * american_to_decimal(b.odds)
                pnl += (dec - 1) if (a.hit and b.hit) else -1.0
                n += 1
    if n:
        print(f"{n} parlays, ROI {pnl/n:+.2%} ({pnl:+.1f}u)")


if __name__ == "__main__":
    df = run()
    df.to_csv("nfl_alt_backtest.csv", index=False)
    report(df)
