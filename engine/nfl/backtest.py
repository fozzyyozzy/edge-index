"""
Edge Index v2 — Leak-free NFL props backtest against REAL book lines.

Walk-forward: for every (season, week), the engine is fit only on games
strictly before that week. Bets are placed only where a real DK/FD/MGM
line exists with both sides quoted (so we can de-vig). PnL is settled
at the offered price against the actual stat line.

2024 = calibration season (choose edge threshold here)
2025 = holdout (report this, untouched by threshold selection)

Usage:
  python backtest.py --db ../../backtest/nfl/edge_index.db
"""
from __future__ import annotations
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from engine.core.odds import devig_two_way, ev_per_unit, american_to_decimal
from engine.nfl.props_engine import PropsEngine, PROPS, load_game_logs, load_real_lines

MAX_ODDS = 150      # skip longshot alt lines
MIN_ODDS = -200     # skip heavy juice (parlay killers, tiny edges get eaten)

# The historical puller sometimes ran DURING games, storing live-suppressed
# lines (e.g. Tyreek Hill rec_yds 4.5 at -110). A line far below/above the
# player's pregame expectation is a contaminated snapshot, not a market we
# could actually have bet pregame. Uses only past data -> not leakage.
SANE_LO, SANE_HI = 0.65, 1.55


def build_bets(db_path: str) -> pd.DataFrame:
    logs = load_game_logs(db_path)
    lines = load_real_lines(db_path)
    lines = lines[(lines.week <= 18)]  # regular season only
    lines = lines.drop_duplicates(
        subset=["player_id", "season", "week", "prop_type", "direction",
                "line", "odds", "book"])

    # a player-week-book quoting MULTIPLE distinct mainlines for one market
    # means the puller captured live in-game snapshots -> drop them all,
    # we can't know which (if any) was the pregame closing line
    key = ["player_id", "season", "week", "prop_type", "book"]
    nline = lines.groupby(key).line.transform("nunique")
    lines = lines[nline == 1]

    # best price per player/week/prop/direction/line across books
    over = lines[lines.direction == "OVER"]
    under = lines[lines.direction == "UNDER"]
    m = over.merge(
        under,
        on=["player_id", "season", "week", "prop_type", "line", "book"],
        suffixes=("_o", "_u"))

    rows = []
    for (season, week), _ in m.groupby(["season", "week"]):
        train = logs[(logs.season < season) |
                     ((logs.season == season) & (logs.week < week))]
        if len(train) < 500:
            continue
        engine = PropsEngine(train)
        wk = m[(m.season == season) & (m.week == week)]
        actual_wk = logs[(logs.season == season) & (logs.week == week)]
        actuals = actual_wk.set_index("player_id")

        # median line per player/prop (books mostly agree; median = consensus)
        for (pid, prop), grp in wk.groupby(["player_id", "prop_type"]):
            if pid not in actuals.index:
                continue
            arow = actuals.loc[pid]
            if isinstance(arow, pd.DataFrame):
                arow = arow.iloc[0]
            col = PROPS[prop][0]
            actual = arow[col]
            if pd.isna(actual):
                continue
            hist = train[train.player_id == pid]
            proj = engine.project(pid, prop, arow["opponent"], asof_hist=hist)
            if proj is None:
                continue
            # sanity filter: drop live/alt-contaminated lines far from the
            # player's pregame expectation (raw baseline, pre-defense-adj)
            base = proj.mean
            grp = grp[(grp.line >= SANE_LO * base) & (grp.line <= SANE_HI * base)]
            if len(grp) == 0:
                continue
            # consensus line = the line closest to the median across books
            med = grp.line.median()
            grp2 = grp.iloc[(grp.line - med).abs().argsort()]
            row = grp2.iloc[0]
            fair_o, fair_u = devig_two_way(row.odds_o, row.odds_u)
            p_over = proj.prob_over(row.line)
            for direction, p_model, p_mkt, odds in (
                    ("OVER", p_over, fair_o, row.odds_o),
                    ("UNDER", 1 - p_over, fair_u, row.odds_u)):
                if not (MIN_ODDS <= odds <= MAX_ODDS):
                    continue
                hit = (actual > row.line) if direction == "OVER" else (actual < row.line)
                push = actual == row.line
                rows.append(dict(
                    season=season, week=week, player=proj.player, pos=proj.position,
                    prop=prop, direction=direction, line=row.line, odds=odds,
                    book=row.book, model_prob=round(p_model, 4),
                    market_prob=round(p_mkt, 4),
                    edge=round(p_model - p_mkt, 4),
                    ev=round(ev_per_unit(p_model, odds), 4),
                    actual=actual, hit=int(hit), push=int(push),
                    pnl=0.0 if push else
                        (american_to_decimal(odds) - 1 if hit else -1.0),
                    n_games=proj.n_games))
        print(f"  {season} w{week}: {len(rows)} cumulative candidate bets")
    return pd.DataFrame(rows)


def report(bets: pd.DataFrame, threshold_grid=(0.02, 0.03, 0.04, 0.05, 0.07, 0.10)):
    print("\n=== CALIBRATION (does model_prob mean anything?) ===")
    bets = bets[bets.push == 0].copy()
    bets["bucket"] = pd.cut(bets.model_prob, np.arange(0.2, 0.85, 0.05))
    cal = bets.groupby("bucket", observed=True).agg(
        n=("hit", "size"), predicted=("model_prob", "mean"), actual=("hit", "mean"))
    print(cal.round(3).to_string())

    for season, tag in ((2024, "CALIBRATION"), (2025, "HOLDOUT")):
        s = bets[bets.season == season]
        print(f"\n=== {season} ({tag}) — edge threshold sweep ===")
        print(f"{'thr':>5} {'n':>6} {'hit%':>6} {'roi':>8} {'pnl(u)':>8}")
        for thr in threshold_grid:
            b = s[s.edge >= thr]
            if len(b) == 0:
                continue
            print(f"{thr:>5} {len(b):>6} {b.hit.mean():>6.1%} "
                  f"{b.pnl.sum()/len(b):>8.2%} {b.pnl.sum():>8.1f}")
        print(f"\n  by market at edge>=0.05:")
        b = s[s.edge >= 0.05]
        if len(b):
            g = b.groupby(["prop", "direction"]).agg(
                n=("hit", "size"), hit=("hit", "mean"), pnl=("pnl", "sum"))
            g["roi"] = g.pnl / g.n
            print(g.round(3).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "backtest", "nfl", "edge_index.db"))
    ap.add_argument("--out", default="nfl_backtest_v2.csv")
    args = ap.parse_args()
    bets = build_bets(args.db)
    bets.to_csv(args.out, index=False)
    print(f"\nSaved {len(bets)} candidate bets -> {args.out}")
    report(bets)
