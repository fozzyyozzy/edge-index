"""Margin distribution and cover probabilities (Phase 3 brief §5).

Residual r = margin - projected_margin. Scale per game:
    sigma = a + b * |line| + c * total        (line = bet-time spread, total = bet-time total)
Shapes: normal, Student-t (df fitted), KDE on standardized residuals, and
"kde_fav": KDE on residuals oriented toward the projected favorite (lets big
favorites' fatter downside tail show up; symmetric shapes can't).
Outcomes are whole numbers and never 0 (CFB has overtime): the continuous
distribution is binned to integers (m +- 0.5), the mass at 0 is removed and
the rest renormalized. Optional key-number spikes multiply P(|m| = k) by a
fitted factor (symmetric), then renormalize.

Cover for a team at alt spread L (team perspective): P(team_margin + L > 0);
push P(team_margin + L = 0) exists only for whole-number L.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, stats

M = np.arange(-90, 91)            # support (0 removed in pmf)
KEYS = [3, 7, 10, 14]
SHAPES = ("normal", "t", "kde")   # tuning candidates (brief §5)
# "kde_fav" is supported but NOT a tuning candidate: it was tried after looking at
# the tuning-season calibration (see PHASE3_REPORT, hypotheses).


# ------------------------------------------------------------------ scale + shape fit
def sigma(params, absline, total):
    a, b, c = params
    return np.clip(a + b * absline + c * total, 4.0, None)


def _nll(theta, r, absline, total, shape):
    s = sigma(theta[:3], absline, total)
    if shape == "normal":
        return -stats.norm.logpdf(r / s).sum() + np.log(s).sum()
    df = np.exp(theta[3]) + 2.0
    return -stats.t.logpdf(r / s, df).sum() + np.log(s).sum()


def fit(r, absline, total, shape: str, orient=None) -> dict:
    """orient: +1/-1 per game (sign of the projected margin), used by kde_fav."""
    r, absline, total = map(lambda v: np.asarray(v, float), (r, absline, total))
    x0 = [r.std(), 0.0, 0.0] + ([np.log(8.0)] if shape == "t" else [])
    base = "normal" if shape.startswith("kde") else shape
    res = optimize.minimize(_nll, x0, args=(r, absline, total, base), method="Nelder-Mead",
                            options={"maxiter": 4000, "xatol": 1e-5, "fatol": 1e-6})
    out = {"shape": shape, "a": float(res.x[0]), "b": float(res.x[1]), "c": float(res.x[2])}
    if shape == "t":
        out["df"] = float(np.exp(res.x[3]) + 2.0)
    if shape.startswith("kde"):
        z = r / sigma(res.x[:3], absline, total)
        if shape == "kde_fav":
            z = z * np.where(np.asarray(orient, float) < 0, -1.0, 1.0)
        kde = stats.gaussian_kde(z)
        grid = np.linspace(-8, 8, 3201)
        cdf = np.cumsum(kde(grid))
        cdf = (cdf - cdf[0]) / (cdf[-1] - cdf[0])
        out["kde_grid"], out["kde_cdf"] = grid.tolist(), cdf.tolist()
        out["kde_bw"] = float(kde.factor)
    out["spikes"] = {}
    return out


def _cdf(z, dist: dict):
    if dist["shape"] == "normal":
        return stats.norm.cdf(z)
    if dist["shape"] == "t":
        return stats.t.cdf(z, dist["df"])
    return np.interp(z, dist["kde_grid"], dist["kde_cdf"], left=0.0, right=1.0)


# ------------------------------------------------------------------ discrete pmf
def _binned(mu, s, dist: dict, sgn=None) -> np.ndarray:
    if dist["shape"] == "kde_fav":           # evaluate in favorite-margin coordinates
        u, c = sgn * M[None, :], sgn * mu
        p = _cdf((u + 0.5 - c) / s, dist) - _cdf((u - 0.5 - c) / s, dist)
    else:
        p = _cdf((M[None, :] + 0.5 - mu) / s, dist) - _cdf((M[None, :] - 0.5 - mu) / s, dist)
    p[:, M == 0] = 0.0
    for k, f in dist.get("spikes", {}).items():
        p[:, np.abs(M) == int(k)] *= f
    return p / p.sum(axis=1, keepdims=True)


def pmf(mu, absline, total, dist: dict, recenter_iters: int = 4) -> np.ndarray:
    """games x len(M) probability matrix over integer home margins (0 excluded).

    Removing the 0 mass and the key-number spikes both move the mean; the
    location is re-solved so the pmf's mean equals the projected margin `mu`
    (the margin model is a mean model).
    """
    target = np.asarray(mu, float)[:, None]
    s = sigma([dist["a"], dist["b"], dist["c"]], np.asarray(absline, float),
              np.asarray(total, float))[:, None]
    sgn = np.where(target < 0, -1.0, 1.0)
    loc = target.copy()
    for _ in range(recenter_iters):
        p = _binned(loc, s, dist, sgn)
        loc = loc + (target - (p * M[None, :]).sum(axis=1, keepdims=True))
    return _binned(loc, s, dist, sgn)


def loglik(margin, P) -> np.ndarray:
    idx = np.clip(np.asarray(margin, int) - M[0], 0, len(M) - 1)
    return np.log(np.clip(P[np.arange(len(P)), idx], 1e-12, None))


def fit_spikes(margin, mu, absline, total, dist: dict, keys=KEYS, iters=4) -> dict:
    """Multiplier per key number so implied P(|m|=k) matches the observed rate
    (implied under the mean-preserving pmf)."""
    margin = np.abs(np.asarray(margin, int))
    spikes = {int(k): 1.0 for k in keys}
    for _ in range(iters):
        Q = pmf(mu, absline, total, {**dist, "spikes": spikes})
        for k in keys:
            spikes[int(k)] *= (margin == k).sum() / Q[:, np.abs(M) == k].sum()
    return {int(k): float(v) for k, v in spikes.items()}


def key_number_table(margin, P, upto=21) -> pd.DataFrame:
    margin = np.abs(np.asarray(margin, int))
    n = len(margin)
    rows = []
    for k in range(1, upto + 1):
        obs = (margin == k).sum()
        imp = P[:, np.abs(M) == k].sum()
        rows.append({"|margin|": k, "observed_pct": 100 * obs / n, "implied_pct": 100 * imp / n,
                     "ratio": obs / imp if imp else np.nan})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ covers / ladders
def cover(P, L, side: str = "home"):
    """(cover, push) for `side` at alt spread L (team perspective), per game."""
    team_m = M if side == "home" else -M
    L = np.asarray(L, float)
    v = team_m[None, :] + (L[:, None] if L.ndim else L)      # scalar or one L per game
    return (P * (v > 0)).sum(axis=1), (P * (v == 0)).sum(axis=1)


def american(p):
    p = np.asarray(p, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(p >= 0.5, -100 * p / (1 - p), 100 * (1 - p) / p)


def ladder(P_row: np.ndarray, rungs=np.arange(-35.5, 36.0, 0.5)) -> pd.DataFrame:
    """Full alt ladder for one game, both sides. Push-adjusted fair odds on whole numbers."""
    P = P_row[None, :]
    rows = []
    for side in ("home", "away"):
        for L in rungs:
            c, push = cover(P, L, side)
            c, push = float(c[0]), float(push[0])
            lose = 1 - c - push
            fair_p = c / (c + lose) if (c + lose) > 0 else np.nan   # pushes refunded
            rows.append({"side": side, "rung": float(L), "cover": c, "push": push,
                         "fair_american": float(np.round(american(fair_p), 0))})
    return pd.DataFrame(rows)
