"""Totals market blend + distribution (Phase 5B). Tuning: 2022-2024 LOSO only.

    actual_total - open_total = c + k_t[bucket] * (T_spec - open_total) + b . extras + e

c absorbs a constant bias of T_spec (e.g. T_epa runs ~+5.6 high). Spec T in
{T_pts, T_ppd, T_epa} is chosen by LOSO MAE; then a drop-one over the extras
(tempo_clash, expl_match; weather once approved) keeps an extra only if it lowers LOSO MAE
and has a sensible sign. projected_total = open_total + fitted adjustment.

Distribution of r = actual_total - projected_total: normal with
sigma_t = a + c_t * open_total (+ d * pace if it helps LOSO log-likelihood), binned to
integer totals (whole-number lines can push). NO recency weighting (Tim, 2026-10-12: the
diagnostics show no variance trend). Key totals are checked empirically. The correlation of
margin and total residuals is fit for 5C's team totals.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, stats

BUCKETS = ["1-3", "4-8", "9+"]
SPECS = ["T_pts", "T_ppd", "T_epa"]
EXTRAS = {"tempo": ["tempo_clash"], "explosive": ["expl_match"]}
EXPECTED_SIGN = {"tempo_clash": None, "expl_match": 1}   # tempo clash: no prior on sign
TUNE = [2022, 2023, 2024]
TSUP = np.arange(0, 161)


def prep(d: pd.DataFrame, spec: str) -> pd.DataFrame:
    d = d.copy()
    d["gap"] = d[spec] - d.total_open
    for b in BUCKETS:
        d[f"kt_{b}"] = d.gap * (d.bucket == b)
    d["const"] = 1.0
    return d


def cols(extras) -> list[str]:
    return ["const"] + [f"kt_{b}" for b in BUCKETS] + [c for e in extras for c in EXTRAS[e]]


def usable(d, c):
    return d.dropna(subset=c + ["total_open", "actual_total"])


def fit(d, extras):
    c = cols(extras)
    x = usable(d, c)
    beta, *_ = np.linalg.lstsq(x[c].to_numpy(float), (x.actual_total - x.total_open).to_numpy(float), rcond=None)
    return {"extras": list(extras), "coef": dict(zip(c, map(float, beta))), "n": len(x)}


def predict(d, m):
    c = list(m["coef"])
    return d.total_open + d[c].fillna(0).to_numpy(float) @ np.array([m["coef"][k] for k in c])


def loso(d, spec, extras, seasons=TUNE) -> pd.Series:
    dd = prep(d, spec)
    out = pd.Series(np.nan, index=dd.index)
    for s in seasons:
        m = fit(dd[dd.season.isin(seasons) & (dd.season != s)], extras)
        te = dd.season == s
        out[te] = predict(dd[te], m)
    return out


def loso_mae(d, spec, extras, seasons=TUNE) -> float:
    p = loso(d, spec, extras, seasons)
    all_c = ["T_pts", "T_ppd", "T_epa", "tempo_clash", "expl_match"]
    x = d.assign(p=p).dropna(subset=["p", "actual_total"] + all_c)
    x = x[x.season.isin(seasons)]
    return float((x.actual_total - x.p).abs().mean())


def bootstrap(d, spec, extras, n=1000, seed=0) -> pd.DataFrame:
    dd = prep(d[d.season.isin(TUNE)], spec)
    c = cols(extras)
    x = usable(dd, c)
    X, y = x[c].to_numpy(float), (x.actual_total - x.total_open).to_numpy(float)
    rng = np.random.default_rng(seed)
    draws = np.array([np.linalg.lstsq(X[i], y[i], rcond=None)[0]
                      for i in (rng.integers(0, len(x), len(x)) for _ in range(n))])
    pt = np.linalg.lstsq(X, y, rcond=None)[0]
    return pd.DataFrame({"term": c, "coef": pt, "ci95_lo": np.percentile(draws, 2.5, 0),
                         "ci95_hi": np.percentile(draws, 97.5, 0)})


def select(d) -> tuple[str, list, pd.DataFrame]:
    rows = []
    best_spec = min(SPECS, key=lambda s: loso_mae(d, s, []))
    for s in SPECS:
        rows.append({"model": f"spec {s} (k only)", "loso_mae": loso_mae(d, s, [])})
    base = loso_mae(d, best_spec, list(EXTRAS))
    rows.append({"model": f"{best_spec} + all extras", "loso_mae": base})
    m_all = fit(prep(d[d.season.isin(TUNE)], best_spec), list(EXTRAS))
    keep = []
    for e in EXTRAS:
        mae = loso_mae(d, best_spec, [x for x in EXTRAS if x != e])
        sign_ok = all(EXPECTED_SIGN[c] is None or np.sign(m_all["coef"][c]) == EXPECTED_SIGN[c]
                      for c in EXTRAS[e])
        helps = mae > base
        rows.append({"model": f"drop {e}", "loso_mae": mae, "delta_vs_all": mae - base,
                     "helps": helps, "sign_ok": sign_ok,
                     "coef": ", ".join(f"{c} {m_all['coef'][c]:+.3f}" for c in EXTRAS[e])})
        if helps and sign_ok:
            keep.append(e)
    x = d[d.season.isin(TUNE)].dropna(subset=["total_open", "actual_total"])
    rows.append({"model": "open total (no model)", "loso_mae": float((x.actual_total - x.total_open).abs().mean())})
    return best_spec, keep, pd.DataFrame(rows)


# ------------------------------------------------------------------ distribution
def sigma_t(p, line, pace=None):
    s = p[0] + p[1] * line + (p[2] * pace if pace is not None and len(p) > 2 else 0.0)
    return np.clip(s, 5.0, None)


def fit_sigma(r, line, pace=None) -> np.ndarray:
    r, line = np.asarray(r, float), np.asarray(line, float)
    pace = None if pace is None else np.asarray(pace, float)

    def nll(p):
        s = sigma_t(p, line, pace)
        return -stats.norm.logpdf(r / s).sum() + np.log(s).sum()
    x0 = [r.std(), 0.0] + ([0.0] if pace is not None else [])
    return optimize.minimize(nll, x0, method="Nelder-Mead", options={"maxiter": 4000}).x


def pmf_total(mu, s) -> np.ndarray:
    mu, s = np.asarray(mu, float)[:, None], np.asarray(s, float)[:, None]
    p = stats.norm.cdf((TSUP[None, :] + 0.5 - mu) / s) - stats.norm.cdf((TSUP[None, :] - 0.5 - mu) / s)
    return p / p.sum(axis=1, keepdims=True)


def over(P, L):
    L = np.asarray(L, float)
    v = TSUP[None, :] - (L[:, None] if L.ndim else L)
    return (P * (v > 0)).sum(1), (P * (v == 0)).sum(1)
