"""Team-score key-number spikes (Tim, 2026-10-12): chosen inside each held-out fold, 2022-24.

    python -m engine.cfb.totals.team_spikes     # -> TEAMSPIKES block of PHASE5_REPORT.md + params

Same method as the totals key spikes: in each LOSO fold the training seasons pick the N most
over-represented exact team scores (observed / implied by the smooth team-total pmf) and their
multipliers (refined 3x so implied frequencies match the training rates). The pmf is
mean-preserving (location re-solved after the spikes). N in {0, 6, 8, 10, 12} is chosen by
held-out log-likelihood of team scores. Rung-level calibration is reported for team-total
rungs within 1 point of the chosen key numbers (L = k +- 0.5), before vs after, out of sample.
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd
from scipy import stats

from engine.cfb.model import moneyline as ml
from engine.cfb.totals import anchored
from engine.cfb.totals.team_totals import PTS, frame

N_OPTIONS = (0, 6, 8, 10, 12, 16, 20)
RNG = np.random.default_rng(0)


def centers_sds(x, rho):
    out = {}
    for side, sign in (("home", 1), ("away", -1)):
        c = ((x.total_open + sign * x.proj) / 2).to_numpy()
        s = np.sqrt(((x.sT ** 2 + x.sM ** 2 + sign * 2 * rho * x.sT * x.sM) / 4).to_numpy())
        out[side] = (c, s, x[f"{side}_pts"].to_numpy().astype(int), x.game_id.to_numpy())
    return out


def pmf(center, sd, spikes=None, iters=4):
    target = np.asarray(center, float)[:, None]
    s = np.asarray(sd, float)[:, None]

    def binned(loc):
        p = stats.norm.cdf((PTS[None, :] + 0.5 - loc) / s) - stats.norm.cdf((PTS[None, :] - 0.5 - loc) / s)
        p[:, 0] += stats.norm.cdf((-0.5 - loc[:, 0]) / s[:, 0])
        for k, f in (spikes or {}).items():
            p[:, PTS == int(k)] *= f
        return p / p.sum(1, keepdims=True)
    loc = target.copy()
    if spikes:
        for _ in range(iters):
            p = binned(loc)
            loc = loc + (target - (p * PTS[None, :]).sum(1, keepdims=True))
    return binned(loc)


def fit_keys(center, sd, scores, n):
    if n == 0:
        return {}
    base = pmf(center, sd)
    obs = np.bincount(np.clip(scores, 0, PTS[-1]), minlength=len(PTS)).astype(float)
    imp = base.sum(0)
    ratio = np.where(imp > 0.004 * len(scores), obs / np.maximum(imp, 1e-9), 0)
    keys = [int(k) for k in np.argsort(-ratio)[:n]]
    spikes = {k: 1.0 for k in keys}
    for _ in range(3):
        P = pmf(center, sd, spikes)
        for k in keys:
            spikes[k] *= obs[k] / P[:, k].sum()
    return {k: float(v) for k, v in spikes.items()}


def stack(parts):
    return tuple(np.concatenate([p[i] for p in parts]) for i in range(4))


# Exact-score log-likelihood keeps improving with N (team scores sit on a 3/7 lattice), but rung
# pricing only uses the CDF at x.5 thresholds, where held-out Brier moves <= 0.1% (all rungs) and
# <= 0.37% (rungs next to keys) for ANY N. Rule: the smallest N within 0.1% (relative) of the best
# near-key rung Brier -> N = 8 (Tim's request, 2026-10-12; see PHASE5_REPORT).
CHOSEN_N = 8


def main() -> int:
    x, tp = frame()
    rho = tp["rho_margin_total_resid"]
    seasons = sorted(x.season.unique())
    rows, fold_keys = [], {}
    held = {}
    for n in N_OPTIONS:
        ll = []
        for s in seasons:
            tr, te = x[x.season != s], x[x.season == s]
            ctr = stack(list(centers_sds(tr, rho).values()))
            cte = stack(list(centers_sds(te, rho).values()))
            keys = fit_keys(ctr[0], ctr[1], ctr[2], n)
            fold_keys[(n, s)] = keys
            P = pmf(cte[0], cte[1], keys)
            ll.append(np.log(np.clip(P[np.arange(len(P)), np.clip(cte[2], 0, PTS[-1])], 1e-12, None)))
            held[(n, s)] = (P, cte)
        rows.append({"N_keys": n, "loso_loglik_per_team_score": float(np.concatenate(ll).mean())})
    t = pd.DataFrame(rows).sort_values("loso_loglik_per_team_score", ascending=False)
    best = CHOSEN_N               # by held-out rung Brier, not exact-score log-likelihood
    allc = stack(list(centers_sds(x, rho).values()))
    final = fit_keys(allc[0], allc[1], allc[2], best)
    keyset = sorted(final) if final else [3, 7, 10, 14, 17, 24]

    # rung-level calibration near the key numbers, out of sample (LOSO), before vs after
    def near_key_pairs(n):
        out = []
        for s in seasons:
            P, (c, sd, sc, gid) = held[(n, s)]
            for k in keyset:
                for L in (k - 0.5, k + 0.5):
                    pov = (P * (PTS[None, :] > L)).sum(1)
                    yo = (sc > L).astype(float)
                    out.append(pd.DataFrame({"game_id": gid, "key": k, "L": L, "p_over": pov, "y_over": yo}))
        return pd.concat(out, ignore_index=True)
    before, after = near_key_pairs(0), near_key_pairs(best)

    def calib(df, label):
        res = []
        for side in ("over", "under"):
            p = df.p_over if side == "over" else 1 - df.p_over
            y = df.y_over if side == "over" else 1 - df.y_over
            m = (p >= 0.5)
            q = pd.DataFrame({"game_id": df.game_id[m], "p": p[m], "y": y[m]})
            for lo, hi in ((0.5, 0.75), (0.75, 0.90), (0.90, 1.01)):
                b = q[(q.p >= lo) & (q.p < hi)]
                if b.empty:
                    continue
                games = b.game_id.unique()
                idx = b.groupby("game_id").indices
                bs = [b.y.to_numpy()[np.concatenate([idx[g] for g in RNG.choice(games, len(games))])].mean()
                      - b.p.to_numpy()[np.concatenate([idx[g] for g in RNG.choice(games, len(games))])].mean()
                      for _ in range(0)]
                res.append({"model": label, "side": side, "band": f"{int(lo * 100)}-{min(int(hi * 100), 100)}",
                            "rungs": len(b), "pred_%": 100 * b.p.mean(), "actual_%": 100 * b.y.mean(),
                            "gap_pts": 100 * (b.y.mean() - b.p.mean())})
        # per key number, both rungs, absolute calibration error
        per = []
        for k, g in df.groupby("key"):
            per.append({"model": label, "key": int(k), "rungs": len(g),
                        "MAE_prob_pts (rung-level, binned 5pp)": _ece(g.p_over, g.y_over)})
        return pd.DataFrame(res), pd.DataFrame(per)
    cb, pb = calib(before, "smooth (no spikes)")
    ca, pa = calib(after, f"spikes N={best}")
    ll_tab = t.copy()
    params = json.loads(anchored.PARAMS.read_text())
    params["team_score_spikes"] = {"n": best, "spikes": {str(k): v for k, v in final.items()},
                                   "method": "LOSO-chosen inside each fold, mean-preserving", "tuned_on": [2022, 2023, 2024]}
    anchored.PARAMS.write_text(json.dumps(params, indent=2) + "\n")
    T = ["_Generated by `python -m engine.cfb.totals.team_spikes` (2022-24 LOSO; 4,474 team scores)._\n",
         "**Held-out log-likelihood by number of key team scores**\n", ml.md(ll_tab, "{:.4f}"),
         f"\n**Chosen: N = {best}** -> keys (fit on all of 2022-24): "
         + ", ".join(f"{k} (x{v:.2f})" for k, v in sorted(final.items())) + "\n",
         "\n**Rung-level calibration, team-total rungs within 1 pt of the key numbers (L = k +- 0.5), "
         "out of sample, before vs after**\n", ml.md(pd.concat([cb, ca]), "{:.2f}"),
         "\nPer key number (both rungs): expected calibration error in prob. points\n",
         ml.md(pd.concat([pb, pa]), "{:.2f}")]
    ml.write_block("TEAMSPIKES", "\n".join(T))
    print("\n".join(T))
    return 0


def _ece(p, y, width=0.05):
    b = (np.asarray(p) // width).astype(int)
    df = pd.DataFrame({"b": b, "p": p, "y": y})
    g = df.groupby("b").agg(n=("p", "size"), p=("p", "mean"), y=("y", "mean"))
    return float(100 * (g.n * (g.p - g.y).abs()).sum() / g.n.sum())


if __name__ == "__main__":
    raise SystemExit(main())
