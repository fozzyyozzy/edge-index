"""5C team totals (Tim's spec, 2026-10-12): calibration on 2022-24 team scores.

    python -m engine.cfb.totals.team_totals       # -> TEAMTOTALS block of PHASE5_REPORT.md

Centers: home = (market total + projected margin) / 2, away = (market total - projected margin) / 2.
Projected margin = frozen Phase 3 model (LOSO for 2022-24); market total = the provider's open.
(margin, total) ~ bivariate normal, rho = the fitted residual correlation (+0.075), so
  Var(home) = (sT^2 + sM^2 + 2 rho sT sM) / 4,  Var(away) = (sT^2 + sM^2 - 2 rho sT sM) / 4
sM = frozen spread sigma (a + b|line| + c*total), sT = frozen market-anchored totals sigma.
Team points are integers >= 0 (normal binned to integers, mass below 0 folded to 0).
Calibration: over/under at every x.5 team-total rung within +-20 of the center, split by side.
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd
from scipy import stats

from engine.cfb.model import backtest as bt, distribution as dist, features as mfeat, margin_model as mm, \
    moneyline as ml, run as mrun
from engine.cfb.totals import anchored, features as tf, model as tm

PTS = np.arange(0, 101)
BINS = [(50, 60), (60, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95), (95, 100.01)]
RNG = np.random.default_rng(0)


def team_pmf(center, sd) -> np.ndarray:
    c, s = np.asarray(center, float)[:, None], np.asarray(sd, float)[:, None]
    p = stats.norm.cdf((PTS[None, :] + 0.5 - c) / s) - stats.norm.cdf((PTS[None, :] - 0.5 - c) / s)
    p[:, 0] += stats.norm.cdf((-0.5 - c[:, 0]) / s[:, 0])          # fold mass below 0
    return p / p.sum(1, keepdims=True)


def frame():
    params = mrun.load_params()
    dp = mrun.dist_params(params)
    tp = json.loads(anchored.PARAMS.read_text())
    md = mm.prep(mfeat.load())
    md = md[md.margin_home.notna()]
    g, _ = bt.loso_frames(md, params["groups"], mrun.TUNE, dp["shape"], list(dp.get("spikes", {})))
    t = tf.load()[["game_id", "actual_total"]]          # g already carries the provider open total
    x = g.merge(t, on="game_id").dropna(subset=["total_open", "actual_total"])
    gm = pd.read_parquet(mfeat.config.CLEAN / "games.parquet").set_index("game_id")
    x["home_pts"] = x.game_id.map(gm.home_points)
    x["away_pts"] = x.game_id.map(gm.away_points)
    x["sM"] = dist.sigma([dp["a"], dp["b"], dp["c"]], x.open_margin.abs(), x.total_bet)
    x["sT"] = tm.sigma_t([tp["sigma_t"]["a"], tp["sigma_t"]["c"]], x.total_open)
    return x, tp


def rungs(x, rho):
    out = []
    for side, sign in (("home", 1), ("away", -1)):
        center = (x.total_open + sign * x.proj) / 2
        var = (x.sT ** 2 + x.sM ** 2 + sign * 2 * rho * x.sT * x.sM) / 4
        P = team_pmf(center, np.sqrt(var))
        pts = x[f"{side}_pts"].to_numpy()
        base = np.round(center.to_numpy())
        for off in range(-20, 21):
            L = base + off + 0.5
            over = (P * (PTS[None, :] > L[:, None])).sum(1)
            out.append(pd.DataFrame({"game_id": x.game_id.to_numpy(), "side": side, "L": L,
                                     "p_over": over, "y_over": (pts > L).astype(float)}))
    r = pd.concat(out, ignore_index=True)
    a = pd.DataFrame({"game_id": r.game_id, "kind": "over", "p": r.p_over, "y": r.y_over})
    b = pd.DataFrame({"game_id": r.game_id, "kind": "under", "p": 1 - r.p_over, "y": 1 - r.y_over})
    return pd.concat([a, b], ignore_index=True).query("p >= 0.5")


def reliability(r):
    r = r.copy()
    r["bin"] = pd.cut(100 * r.p, [b[0] for b in BINS] + [BINS[-1][1]], right=False,
                      labels=[f"{a}-{min(b, 100):.0f}" for a, b in BINS])
    t = r.groupby(["kind", "bin"], observed=True).agg(n=("y", "size"), pred=("p", "mean"),
                                                      actual=("y", "mean")).reset_index()
    t["pred"] *= 100
    t["actual"] *= 100
    t["gap"] = t.actual - t.pred
    return t


def band(r, lo=.75, hi=.90):
    x = r[(r.p >= lo) & (r.p < hi)]
    games = x.game_id.unique()
    idx = x.groupby("game_id").indices
    b = []
    for _ in range(1000):
        pick = RNG.choice(games, len(games))
        ix = np.concatenate([idx[g] for g in pick])
        b.append(x.y.to_numpy()[ix].mean() - x.p.to_numpy()[ix].mean())
    return {"pairs": len(x), "games": len(games), "pred_%": 100 * x.p.mean(), "actual_%": 100 * x.y.mean(),
            "gap_pts": 100 * (x.y.mean() - x.p.mean()),
            "ci95": f"{100 * np.percentile(b, 2.5):+.1f} to {100 * np.percentile(b, 97.5):+.1f}"}


def main() -> int:
    x, tp = frame()
    rM = x.margin_home - x.proj
    rT = x.actual_total - x.total_open
    rho_market = float(np.corrcoef(rM, rT)[0, 1])
    rho = tp["rho_margin_total_resid"]
    r = rungs(x, rho)
    rows = [{"kind": k, **band(g)} for k, g in r.groupby("kind")]
    # bias + spread of team scores around centers
    hc, ac = (x.total_open + x.proj) / 2, (x.total_open - x.proj) / 2
    bias = {"home_mean_resid": float((x.home_pts - hc).mean()), "away_mean_resid": float((x.away_pts - ac).mean()),
            "home_sd_resid": float((x.home_pts - hc).std()), "away_sd_resid": float((x.away_pts - ac).std()),
            "home_model_sd": float(np.sqrt(((x.sT ** 2 + x.sM ** 2 + 2 * rho * x.sT * x.sM) / 4)).mean()),
            "away_model_sd": float(np.sqrt(((x.sT ** 2 + x.sM ** 2 - 2 * rho * x.sT * x.sM) / 4)).mean())}
    # exact team scores: observed vs implied
    scores = np.concatenate([x.home_pts, x.away_pts]).astype(int)
    P = np.vstack([team_pmf(hc, np.sqrt((x.sT ** 2 + x.sM ** 2 + 2 * rho * x.sT * x.sM) / 4)),
                   team_pmf(ac, np.sqrt((x.sT ** 2 + x.sM ** 2 - 2 * rho * x.sT * x.sM) / 4))])
    obs = pd.Series(scores).value_counts(normalize=True)
    keys = pd.DataFrame({"score": PTS[:50], "observed_%": [100 * obs.get(k, 0) for k in PTS[:50]],
                         "implied_%": 100 * P.mean(0)[:50]})
    keys["ratio"] = keys["observed_%"] / keys["implied_%"]
    T = ["_Generated by `python -m engine.cfb.totals.team_totals` (2022-24, LOSO projected margin; "
         f"market total = provider open; {len(x)} games, {2 * len(x)} team scores)._\n",
         f"Residual correlation (margin, total) measured around the MARKET total: **{rho_market:+.3f}** "
         f"(model-total version {rho:+.3f}, used per Tim).\n",
         "**75-90% band, over vs under (game-clustered CI)**\n", ml.md(pd.DataFrame(rows), "{:.2f}"),
         "\n**Centering and spread**\n", ml.md(pd.DataFrame([bias]), "{:.2f}"),
         "\n**Reliability by band**\n", ml.md(reliability(r), "{:.1f}"),
         "\n<details><summary>Exact team scores: observed vs implied (key scores)</summary>\n\n",
         ml.md(keys.sort_values("ratio", ascending=False).head(15), "{:.2f}"), "\n</details>\n"]
    ml.write_block("TEAMTOTALS", "\n".join(T))
    print("\n".join(T[:8]))
    print(ml.md(keys.sort_values("ratio", ascending=False).head(12), "{:.2f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
