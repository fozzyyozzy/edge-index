"""Preseason prior for each team's O/D ratings (Phase 2 brief §5).

Target: season s end-of-regular-season ("pre-bowl") adjusted rating, i.e. the
as-of rating at the postseason slot. Features, all known before s kicks off:
  prev      season s-1 final rating (whole season minus non-CFP bowls)
  ret_ppa   returning production, share of PPA (CFBD: offense only)
  ret_pass  returning passing PPA share (QB proxy)
  talent    247 talent composite, season s (z-scored within season)
  recruit   recruiting points, mean of classes s-3..s that exist (z-scored)
  new_coach first-year head coach flag
Transfer portal net is skipped: Phase 1 has only name-matched counts with no
quality, which isn't a clean team-level measure.

One ridge model per rating (o/d x metric), trained only on target seasons
strictly before s. With fewer than MIN_PAIR_SEASONS training seasons the prior
falls back to mean + f * (prev - mean), f fit on the available pairs; with no
pairs at all (2022) f = params["prior_no_history_factor"].
Missing feature values are filled with that season's FBS mean (flagged).
FCS teams (and FBS teams with no prior-season rating) get the FCS constant.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from engine.cfb import config
from engine.cfb.ratings.adjust import METRICS

FEATURES = ["prev", "ret_ppa", "ret_pass", "talent", "recruit", "new_coach"]
MIN_PAIR_SEASONS = 2
RIDGE_ALPHA = 1.0
RATINGS = [f"{side}_{m}" for m in METRICS for side in ("o", "d")]


def team_features() -> pd.DataFrame:
    ts = pd.read_parquet(config.CLEAN / "team_season.parquet")
    ts = ts.sort_values(["team_id", "season"])
    ts["recruit_raw"] = (ts.groupby("team_id").recruiting_points
                         .transform(lambda s: s.rolling(4, min_periods=1).mean()))
    out = ts[["season", "team_id", "team"]].copy()
    out["ret_ppa"] = ts.ret_pct_ppa
    out["ret_pass"] = ts.ret_pct_passing_ppa
    out["new_coach"] = ts.coach_first_year.astype("float")
    for raw, name in (("talent", "talent"), ("recruit_raw", "recruit")):
        g = ts.groupby("season")[raw]
        out[name] = (ts[raw] - g.transform("mean")) / g.transform("std")
    feats = ["ret_ppa", "ret_pass", "talent", "recruit", "new_coach"]
    out["n_filled"] = out[feats].isna().sum(axis=1)
    for f in feats:
        out[f] = out[f].fillna(out.groupby("season")[f].transform("mean"))
    out["new_coach"] = out.new_coach.fillna(0.0)
    return out


def design(season: int, prev_final: pd.DataFrame | None, feats: pd.DataFrame,
           fcs_const: dict) -> pd.DataFrame:
    """One row per FBS team in `season` with features; prev_* per rating."""
    f = feats[feats.season == season].copy()
    for r in RATINGS:
        col = (prev_final.set_index("team_id")[r] if prev_final is not None
               else pd.Series(dtype=float))
        f[f"prev_{r}"] = f.team_id.map(col)
        f[f"prev_missing_{r}"] = f[f"prev_{r}"].isna()
        f[f"prev_{r}"] = f[f"prev_{r}"].fillna(fcs_const[r])
    return f


def build_prior(season: int, finals: dict, targets: dict, feats: pd.DataFrame,
                fcs_const: dict, params: dict, teams: pd.DataFrame):
    """Prior for `season`. finals/targets: {season: ratings df} for earlier seasons.

    Returns (prior {metric: (O Series, D Series)}, rows df, info dict).
    """
    cur = design(season, finals.get(season - 1), feats, fcs_const)
    pair_seasons = [s for s in sorted(targets) if s < season and (s - 1) in finals]
    info = {"season": season, "pair_seasons": pair_seasons, "coef": {}}
    pred = pd.DataFrame({"team_id": cur.team_id.values})
    for r in RATINGS:
        x_cols = [f"prev_{r}"] + FEATURES[1:]
        if len(pair_seasons) >= MIN_PAIR_SEASONS:
            tr = []
            for s in pair_seasons:
                d = design(s, finals[s - 1], feats, fcs_const)
                d["y"] = d.team_id.map(targets[s].set_index("team_id")[r])
                tr.append(d.dropna(subset=["y"]))
            tr = pd.concat(tr)
            mdl = Ridge(alpha=RIDGE_ALPHA).fit(tr[x_cols].values, tr.y.values)
            pred[r] = mdl.predict(cur[x_cols].values)
            info["coef"][r] = {"intercept": float(mdl.intercept_), "n": len(tr),
                               **{c.replace(f"_{r}", ""): float(v)
                                  for c, v in zip(x_cols, mdl.coef_)}}
            info["method"] = "ridge"
        else:
            if pair_seasons:
                xs, ys = [], []
                for s in pair_seasons:
                    d = design(s, finals[s - 1], feats, fcs_const)
                    d["y"] = d.team_id.map(targets[s].set_index("team_id")[r])
                    d = d.dropna(subset=["y"])
                    xs.append(d[f"prev_{r}"] - d[f"prev_{r}"].mean())
                    ys.append(d.y - d.y.mean())
                x, y = pd.concat(xs), pd.concat(ys)
                f = float((x * y).sum() / (x * x).sum())
                info["method"] = "regress_to_mean_fit"
            else:
                f = params["prior_no_history_factor"]
                info["method"] = "regress_to_mean_default"
            prev = cur[f"prev_{r}"]
            mean = prev[~cur[f"prev_missing_{r}"]].mean() if prev.notna().any() else 0.0
            pred[r] = mean + f * (prev.values - mean) if len(prev) else []
            info["coef"][r] = {"factor": f}

    # assemble priors for every team in the season: FBS from model, FCS constant
    allteams = teams[["team_id", "team", "is_fcs"]].copy()
    allteams = allteams.merge(pred, on="team_id", how="left")
    for r in RATINGS:
        allteams[r] = allteams[r].fillna(fcs_const[r])
    allteams["prior_source"] = np.where(allteams.team_id.isin(pred.team_id),
                                        info.get("method", "fcs_const"), "fcs_const")
    allteams.insert(0, "season", season)
    prior = {m: (allteams.set_index("team_id")[f"o_{m}"],
                 allteams.set_index("team_id")[f"d_{m}"]) for m in METRICS}
    return prior, allteams, info


def zero_prior(teams: pd.DataFrame, fcs_const: dict | None):
    """2021 burn-in prior: 0 for FBS, FCS constant for FCS (or 0)."""
    t = teams.set_index("team_id")
    out = {}
    for m in METRICS:
        o = pd.Series(0.0, index=t.index)
        d = pd.Series(0.0, index=t.index)
        if fcs_const:
            o[t.is_fcs] = fcs_const[f"o_{m}"]
            d[t.is_fcs] = fcs_const[f"d_{m}"]
        out[m] = (o, d)
    return out
