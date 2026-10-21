"""Descriptive check (no PREREG, no credits): 2025 closing MAIN-line receptions / rec_yds Overs and Unders, flat return at
DK's price vs the best price across the 8 US books at the same line; vig by market; and the legs the factor study's
combined model (game script + weather, docs/nfl/FACTOR_STUDY_RESULTS.md) favors.

    python -m engine.nfl.main_lines_check     -> data/nfl/verify/main_lines_check.json
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd

from engine.nfl import verify_replay as vr
from engine.nfl import factor_study as fs
from engine.nfl.early_tests import clean, clustered_mean_ci

OUT = vr.OUT
MAIN = {"player_receptions": "receptions", "player_reception_yds": "rec_yds"}
COMBINED = ["implied_total", "team_spread", "wind", "precip"]          # factor study's passing features


def flat(d, dec_col):
    """flat 1u: WIN pays dec-1, LOSS -1, PUSH 0"""
    ret = np.where(d.res == "WIN", d[dec_col] - 1, np.where(d.res == "PUSH", 0.0, -1.0))
    mu, ci = clustered_mean_ci(ret, d.game_id)
    return {"n": int(len(d)), "games": int(d.game_id.nunique()), "hit": round(float((d.res == "WIN").mean()) * 100, 2),
            "roi_pct": round(mu * 100, 2), "ci95_pct": [round(c * 100, 2) for c in ci]}


def main():
    e = pd.read_parquet(OUT / "early_props_2025.parquet")
    c = e[(e.snap == "CLOSE_ALL") & e.market.isin(MAIN)].copy()
    c["stat"] = c.market.map(MAIN)
    c["dec"] = vr.dec(c.price)
    key = ["game_id", "week", "player", "stat", "point", "home_team", "away_team"]
    dk = c[c.book == "draftkings"].pivot_table(index=key, columns="side", values="price", aggfunc="first") \
        .reset_index().dropna(subset=["Over", "Under"])
    best = c.groupby(key + ["side"]).agg(best_dec=("dec", "max"), books=("book", "nunique")).reset_index() \
        .pivot_table(index=key, columns="side", values=["best_dec", "books"], aggfunc="first")
    best.columns = [f"{a}_{b}" for a, b in best.columns]
    m = dk.merge(best.reset_index(), on=key, how="left")
    # settle: Over wins if stat > point; integer point -> push on equality
    w, played, known = vr.outcomes(2025)
    s = vr.settle(m.assign(market=m.stat, rung=m.point, teams=list(zip(m.home_team, m.away_team))), w, played, known, 2025)
    s = s[s.result.isin(["WIN", "LOSS"])].copy()                       # result here = value >= point (raw)
    s["over"] = np.where(s.value > s.point, "WIN", np.where(s.value == s.point, "PUSH", "LOSS"))
    s["under"] = np.where(s.value < s.point, "WIN", np.where(s.value == s.point, "PUSH", "LOSS"))
    io, iu = vr.implied(s.Over), vr.implied(s.Under)
    s["dk_hold"] = io + iu - 1
    s["best_hold"] = 1 / s.best_dec_Over + 1 / s.best_dec_Under - 1
    s["q_dk"] = io / (io + iu)
    res = {"rows": int(len(s)), "games": int(s.game_id.nunique()), "integer_lines": int((s.point % 1 == 0).sum()),
           "books_per_line_median": {"Over": float(s.books_Over.median()), "Under": float(s.books_Under.median())}}
    legs = pd.concat([s.assign(side="Over", res=s.over, dk_dec=vr.dec(s.Over), best=s.best_dec_Over),
                      s.assign(side="Under", res=s.under, dk_dec=vr.dec(s.Under), best=s.best_dec_Under)])
    legs["best"] = np.maximum(legs.best.fillna(legs.dk_dec), legs.dk_dec)
    out = {}
    for name, g in [("all", legs)] + [(f"{st}:{sd}", x) for (st, sd), x in legs.groupby(["stat", "side"])] + \
                   [(st, x) for st, x in legs.groupby("stat")]:
        out[name] = {"dk_price": flat(g, "dk_dec"), "best_price": flat(g, "best")}
    res["flat_returns"] = out
    res["vig"] = {st: {"dk_hold_mean_pct": round(float(x.dk_hold.mean()) * 100, 2),
                       "best_price_hold_mean_pct": round(float(x.best_hold.mean()) * 100, 2),
                       "share_lines_best_hold_negative": round(float((x.best_hold < 0).mean()) * 100, 2)}
                  for st, x in s.groupby("stat")}
    res["vig"]["all"] = {"dk_hold_mean_pct": round(float(s.dk_hold.mean()) * 100, 2),
                         "best_price_hold_mean_pct": round(float(s.best_hold.mean()) * 100, 2),
                         "share_lines_best_hold_negative": round(float((s.best_hold < 0).mean()) * 100, 2)}
    # combined factor model: refit exactly as registered (rows A, weeks 1-9, offset logit(p_hold), per market),
    # applied to main lines with DK's main-line de-vig as the offset; favored = EV > 0 at the price
    A = pd.read_parquet(OUT / "factor_rows_A.parquet")
    B = pd.read_parquet(OUT / "factor_rows_B.parquet")
    fitA = A.week.isin(fs.FIT_WEEKS).to_numpy()
    XA = A[COMBINED].astype(float)
    mu, sd = XA[fitA].mean(), XA[fitA].std().replace(0, 1)
    coefs = {}
    for st in A.stat.unique():
        sm = (A.stat == st).to_numpy()
        coefs[st] = fs.fit_offset(((XA - mu) / sd).fillna(0).to_numpy()[fitA & sm], A.y.to_numpy()[fitA & sm],
                                  fs.logit(A.p_hold.to_numpy()[fitA & sm]))
    feat = B[["game_id", "player", "stat"] + COMBINED].drop_duplicates(["game_id", "player", "stat"])
    t = legs.merge(feat, on=["game_id", "player", "stat"], how="left")
    X = ((t[COMBINED].astype(float) - mu) / sd).fillna(0).to_numpy()
    shift = np.array([X[i] @ coefs[st] for i, st in enumerate(t.stat)])
    p_over = 1 / (1 + np.exp(-(fs.logit(t.q_dk.to_numpy()) + shift)))
    t["p_side"] = np.where(t.side == "Over", p_over, 1 - p_over)
    t["ev_dk"], t["ev_best"] = t.p_side * t.dk_dec - 1, t.p_side * t.best - 1
    te = t[t.week.isin(fs.TEST_WEEKS)]
    fav = {}
    for label, col, dcol in (("ev_positive_at_dk_price", "ev_dk", "dk_dec"), ("ev_positive_at_best_price", "ev_best", "best")):
        f = te[te[col] > 0].sort_values(col, ascending=False).drop_duplicates(["game_id", "player", "stat"])
        fav[label] = {"legs": flat(f, dcol), "also_at_dk_price": flat(f, "dk_dec"),
                      "sides": f.side.value_counts().to_dict(), "by_market": {st: flat(x, dcol) for st, x in f.groupby("stat")},
                      "mean_model_p_pct": round(float(f.p_side.mean()) * 100, 2) if len(f) else None}
    fav["test_weeks_all_legs"] = {"dk_price": flat(te, "dk_dec"), "best_price": flat(te, "best")}
    fav["coefficients_per_sd"] = {st: dict(zip(COMBINED, map(float, b))) for st, b in coefs.items()}
    res["combined_factor_model_weeks_10_18"] = fav
    (OUT / "main_lines_check.json").write_text(json.dumps(clean(res), indent=1))
    print(json.dumps(clean(res), indent=1)[:9000])


if __name__ == "__main__":
    main()
