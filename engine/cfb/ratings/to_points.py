"""Ratings -> points (Phase 2 brief §6).

    pred_margin_home = b_hfa * (not neutral) + sum_k b_k * (net_k[home] - net_k[away])
    net_k = O_k + D_k            (D > 0 = better defense)

Specs (chosen by tuning MAE):
  epa_sr : net EPA/play, net success rate
  rp_sr  : net rush EPA/play, net pass EPA/play, net success rate
Fit by OLS without intercept on FBS-vs-FBS games (non-CFP bowls excluded)
using each game's as-of-week ratings. power_pts = sum_k b_k * (net_k - mean of
FBS teams at that as-of), i.e. points vs an average FBS team, neutral field.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SPECS = {"epa_sr": ["epa", "sr"], "rp_sr": ["rush_epa", "pass_epa", "sr"]}


def add_nets(r: pd.DataFrame) -> pd.DataFrame:
    r = r.copy()
    for m in ("epa", "sr", "rush_epa", "pass_epa"):
        r[f"net_{m}"] = r[f"o_{m}"] + r[f"d_{m}"]
    return r


def game_frame(games: pd.DataFrame, ratings: pd.DataFrame, slot: pd.Series) -> pd.DataFrame:
    """Games joined to home/away as-of ratings. Ratings must carry net_* columns."""
    g = games.copy()
    g["week_asof"] = g.game_id.map(slot)
    g = g.dropna(subset=["week_asof"]).astype({"week_asof": "int64"})
    nets = [c for c in ratings.columns if c.startswith("net_")] + ["power_pts"] * ("power_pts" in ratings)
    r = ratings[["season", "week_asof", "team_id"] + nets]
    for side in ("home", "away"):
        g = g.merge(r.rename(columns={"team_id": f"{side}_id",
                                      **{c: f"{side}_{c}" for c in nets}}),
                    on=["season", "week_asof", f"{side}_id"], how="inner")
    g["hfa"] = (~g.neutral_site.astype(bool)).astype(float)
    return g


def design(g: pd.DataFrame, spec: str) -> np.ndarray:
    cols = [g.hfa.values] + [(g[f"home_net_{m}"] - g[f"away_net_{m}"]).values
                             for m in SPECS[spec]]
    return np.column_stack(cols)


def fit(g: pd.DataFrame, spec: str) -> dict:
    X = design(g, spec)
    beta, *_ = np.linalg.lstsq(X, g.margin_home.values.astype(float), rcond=None)
    return {"spec": spec, "hfa": float(beta[0]),
            **{m: float(b) for m, b in zip(SPECS[spec], beta[1:])}}


def predict(g: pd.DataFrame, coef: dict) -> np.ndarray:
    beta = np.array([coef["hfa"]] + [coef[m] for m in SPECS[coef["spec"]]])
    return design(g, coef["spec"]) @ beta


def power_points(ratings: pd.DataFrame, coef: dict) -> pd.Series:
    """Points vs an average FBS team on a neutral field, per (season, week_asof)."""
    raw = sum(coef[m] * ratings[f"net_{m}"] for m in SPECS[coef["spec"]])
    fbs_mean = raw.where(~ratings.is_fcs).groupby(
        [ratings.season, ratings.week_asof]).transform("mean")
    return raw - fbs_mean
