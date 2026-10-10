"""Market-blend margin model (Phase 3 brief §4).

    margin - open_margin = sum_b k_b * 1[bucket=b] * (ratings_margin - open_margin)
                           + features . beta + e

No intercept. open_margin = -spread_open (home perspective, provider per game).
ratings_margin = power_home - power_away + HFA * (not neutral), HFA from the
Phase 2 frozen to_points fit. projected_margin = open_margin + fitted adjustment.
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd

from engine.cfb.ratings.run import PARAMS as RATINGS_PARAMS

BUCKETS = ["1-3", "4-8", "9+"]
GROUPS = {
    "st": ["st_fp_diff", "st_fg_diff"],
    "qb": ["qb_delta"],
    "rest": ["rest_diff", "bye_diff"],
    "travel": ["travel_k", "tz_diff", "w2e_diff"],
}
# sign a feature should have (home perspective) for it to "make sense"
EXPECTED_SIGN = {"st_fp_diff": 1, "st_fg_diff": 1, "qb_delta": 1, "rest_diff": 1,
                 "bye_diff": 1, "travel_k": 1, "tz_diff": 1, "w2e_diff": 1}


def ratings_hfa() -> float:
    return json.loads(RATINGS_PARAMS.read_text())["to_points"]["hfa"]


def prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["ratings_margin"] = (d.power_home - d.power_away
                           + ratings_hfa() * (~d.neutral_site.astype(bool)))
    d["gap"] = d.ratings_margin - d.open_margin
    for b in BUCKETS:
        d[f"k_{b}"] = d.gap * (d.bucket == b)
    return d


def columns(groups: list[str]) -> list[str]:
    return [f"k_{b}" for b in BUCKETS] + [c for g in groups for c in GROUPS[g]]


def usable(d: pd.DataFrame, cols) -> pd.DataFrame:
    return d.dropna(subset=list(cols) + ["open_margin", "power_home", "power_away"])


def fit(d: pd.DataFrame, groups: list[str]) -> dict:
    cols = columns(groups)
    x = usable(d.dropna(subset=["margin_home"]), cols)
    X, y = x[cols].to_numpy(float), (x.margin_home - x.open_margin).to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {"groups": groups, "coef": dict(zip(cols, map(float, beta))), "n": len(x)}


def predict(d: pd.DataFrame, model: dict) -> pd.Series:
    cols = list(model["coef"])
    adj = d[cols].fillna(0).to_numpy(float) @ np.array([model["coef"][c] for c in cols])
    return pd.Series(d.open_margin.to_numpy() + adj, index=d.index)


def bootstrap(d: pd.DataFrame, groups: list[str], n: int = 1000, seed: int = 0) -> pd.DataFrame:
    """Game-level bootstrap 95% CIs for every coefficient."""
    cols = columns(groups)
    x = usable(d.dropna(subset=["margin_home"]), cols)
    X, y = x[cols].to_numpy(float), (x.margin_home - x.open_margin).to_numpy(float)
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        draws.append(np.linalg.lstsq(X[i], y[i], rcond=None)[0])
    draws = np.array(draws)
    point = np.linalg.lstsq(X, y, rcond=None)[0]
    return pd.DataFrame({"term": cols, "coef": point,
                         "ci95_lo": np.percentile(draws, 2.5, axis=0),
                         "ci95_hi": np.percentile(draws, 97.5, axis=0),
                         "boot_se": draws.std(axis=0)})


def loso(d: pd.DataFrame, groups: list[str], seasons: list[int]) -> pd.Series:
    """Leave-one-season-out projected margins for `seasons`."""
    out = pd.Series(np.nan, index=d.index)
    for s in seasons:
        m = fit(d[d.season.isin(seasons) & (d.season != s)], groups)
        te = d.season == s
        out[te] = predict(d[te], m)
    return out


def loso_mae(d: pd.DataFrame, groups: list[str], seasons: list[int]) -> float:
    p = loso(d, groups, seasons)
    e = usable(d.assign(p=p), columns(list(GROUPS))).dropna(subset=["margin_home", "p"])
    return float((e.margin_home - e.p).abs().mean())


def select(d: pd.DataFrame, seasons: list[int]) -> tuple[list[str], pd.DataFrame]:
    """Drop-one table on LOSO MAE; keep a group if dropping it hurts and signs make sense.

    Every row is scored on the same games (rows with all candidate features), so
    MAEs are comparable.
    """
    full = list(GROUPS)
    base = loso_mae(d, full, seasons)
    rows = [{"model": "all groups", "loso_mae": base, "delta_vs_all": 0.0}]
    m_all = fit(d[d.season.isin(seasons)], full)
    keep = []
    for g in full:
        mae = loso_mae(d, [x for x in full if x != g], seasons)
        signs_ok = all(np.sign(m_all["coef"][c]) == EXPECTED_SIGN[c] for c in GROUPS[g])
        helps = mae > base
        rows.append({"model": f"drop {g}", "loso_mae": mae, "delta_vs_all": mae - base,
                     "group_helps": helps, "signs_ok": signs_ok,
                     "coefs": ", ".join(f"{c} {m_all['coef'][c]:+.3f}" for c in GROUPS[g])})
        if helps and signs_ok:
            keep.append(g)
    rows.append({"model": "ratings gap only (k)", "loso_mae": loso_mae(d, [], seasons),
                 "delta_vs_all": np.nan})
    if keep != full:
        km = loso_mae(d, keep, seasons)
        rows.append({"model": f"selected: {', '.join(keep) or 'k only'}", "loso_mae": km,
                     "delta_vs_all": km - base})
    return keep, pd.DataFrame(rows)
