"""Opponent-adjusted O/D ratings per metric, as of a cutoff (Phase 2 brief §4).

Model per metric, on plays strictly before the cutoff:

    y - (O_prior[off] - D_prior[def]) = mu + dO[off] - dD[def] + h * offense_home + e
    O = O_prior + dO,   D = D_prior + dD   (D > 0 = better defense)

Weighted ridge, penalty lam on dO/dD only (so ratings shrink toward the prior,
not toward zero); mu and h are effectively unpenalized. Solved through the
normal equations on a sparse design ((2T+2) x (2T+2) dense system).

Recency: a play's weight is 0.5 ** (games_ago / H), where games_ago is the
number of the OFFENSE's games played after the play's game, up to the cutoff
(0 = its most recent game). The defense's count is not used (documented
approximation). H = null/inf disables recency.

As-of schedule: a season's slots are its regular weeks 1..N plus a
postseason slot N+1. The cutoff for slot w is the earliest kickoff of any
FBS-involved game in slot w; ratings "as of w" read only plays from games
that kicked off strictly before that cutoff.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.sparse as sp

METRICS = {               # name -> (column, subset flag)
    "epa": ("epa", None),
    "sr": ("success", None),
    "rush_epa": ("epa", "is_rush"),
    "pass_epa": ("epa", "is_pass"),
}
UNPENALIZED = 1e-6


@dataclass
class SeasonCtx:
    season: int
    teams: pd.DataFrame          # team_id, team, is_fcs
    slots: pd.DataFrame          # week_asof, cutoff, season_type, week
    team_games: pd.DataFrame     # team_id, game_id, kickoff_utc, k (0-based order)


def season_ctx(games: pd.DataFrame, season: int) -> SeasonCtx:
    g = games[(games.season == season) & games.fbs_involved]
    h = g[["home_id", "home_team", "home_classification"]].set_axis(
        ["team_id", "team", "cls"], axis=1)
    a = g[["away_id", "away_team", "away_classification"]].set_axis(
        ["team_id", "team", "cls"], axis=1)
    teams = (pd.concat([h, a]).dropna(subset=["team_id"])
             .drop_duplicates("team_id").astype({"team_id": "int64"}))
    teams["is_fcs"] = teams.cls != "fbs"
    teams = teams.drop(columns="cls").sort_values("team_id").reset_index(drop=True)

    reg = g[g.season_type == "regular"]
    n_reg = int(reg.week.max())
    slots = (reg.groupby("week").kickoff_utc.min().rename("cutoff").reset_index()
             .rename(columns={"week": "week_asof"}))
    slots["season_type"], slots["week"] = "regular", slots.week_asof
    post = g[g.season_type == "postseason"]
    if len(post):
        slots = pd.concat([slots, pd.DataFrame({
            "week_asof": [n_reg + 1], "cutoff": [post.kickoff_utc.min()],
            "season_type": ["postseason"], "week": [1]})], ignore_index=True)

    # games that feed ratings (non-CFP bowls never do)
    used = g[~(g.is_bowl & ~g.is_cfp)]
    tg = pd.concat([
        used[["home_id", "game_id", "kickoff_utc"]].set_axis(["team_id", "game_id", "kickoff_utc"], axis=1),
        used[["away_id", "game_id", "kickoff_utc"]].set_axis(["team_id", "game_id", "kickoff_utc"], axis=1),
    ]).dropna(subset=["team_id"]).astype({"team_id": "int64"})
    tg = tg.sort_values(["team_id", "kickoff_utc"]).reset_index(drop=True)
    tg["k"] = tg.groupby("team_id").cumcount()
    return SeasonCtx(season, teams, slots.sort_values("week_asof").reset_index(drop=True), tg)


def slot_for_game(ctx: SeasonCtx, games: pd.DataFrame) -> pd.Series:
    """week_asof slot of each game in this season (postseason -> N+1)."""
    g = games[games.season == ctx.season]
    n_reg = ctx.slots[ctx.slots.season_type == "regular"].week_asof.max()
    return pd.Series(np.where(g.season_type == "postseason", n_reg + 1, g.week),
                     index=g.game_id, name="week_asof")


def recency_weights(plays: pd.DataFrame, ctx: SeasonCtx, cutoff, H) -> np.ndarray:
    if H is None or not np.isfinite(H):
        return np.ones(len(plays))
    tg = ctx.team_games
    n_before = tg[tg.kickoff_utc < cutoff].groupby("team_id").size()
    k = pd.Series(tg.k.values, index=pd.MultiIndex.from_arrays([tg.team_id, tg.game_id]))
    idx = pd.MultiIndex.from_arrays([plays.offense_id.values, plays.game_id.values])
    kk = k.reindex(idx).values
    nb = n_before.reindex(plays.offense_id.values).values
    ago = np.clip(nb - 1 - kk, 0, None)
    return 0.5 ** (ago / H)


def fit_metric(plays: pd.DataFrame, teams: np.ndarray, prior_o: pd.Series,
               prior_d: pd.Series, y: np.ndarray, w: np.ndarray, lam: float):
    """Returns (O, D, mu, h) with O/D as Series over `teams`."""
    T = len(teams)
    if len(plays) == 0:
        return prior_o.reindex(teams).values, prior_d.reindex(teams).values, np.nan, np.nan
    pos = pd.Series(np.arange(T), index=teams)
    oi = pos.reindex(plays.offense_id.values).values
    di = pos.reindex(plays.defense_id.values).values
    r = y - (prior_o.reindex(plays.offense_id.values).values
             - prior_d.reindex(plays.defense_id.values).values)
    n = len(plays)
    rows = np.repeat(np.arange(n), 4)
    cols = np.column_stack([oi, T + di, np.full(n, 2 * T), np.full(n, 2 * T + 1)]).ravel()
    vals = np.column_stack([np.ones(n), -np.ones(n),
                            plays.offense_home.values.astype(float), np.ones(n)]).ravel()
    X = sp.csr_matrix((vals, (rows, cols)), shape=(n, 2 * T + 2))
    Xw = X.multiply(w[:, None]).tocsr()
    A = (X.T @ Xw).toarray()
    A[np.diag_indices(2 * T)] += lam
    A[2 * T, 2 * T] += UNPENALIZED
    A[2 * T + 1, 2 * T + 1] += UNPENALIZED
    b = Xw.T @ r
    beta = np.linalg.solve(A, b)
    O = prior_o.reindex(teams).values + beta[:T]
    D = prior_d.reindex(teams).values + beta[T:2 * T]
    return O, D, beta[2 * T + 1], beta[2 * T]


def fit_asof(model_plays: pd.DataFrame, ctx: SeasonCtx, cutoff, prior: dict,
             params: dict) -> pd.DataFrame:
    """Ratings for every team in ctx using only plays that kicked off < cutoff.

    prior: {metric: (O_prior Series, D_prior Series)} indexed by team_id.
    cutoff: pd.Timestamp (UTC) or None for the whole season.
    """
    p = model_plays[(model_plays.season == ctx.season) & ~model_plays.is_garbage_time]
    if cutoff is not None:
        p = p[p.kickoff_utc < cutoff]
    teams = ctx.teams.team_id.values
    out = ctx.teams.copy()
    w_all = recency_weights(p, ctx, cutoff if cutoff is not None else pd.Timestamp.max.tz_localize("UTC"),
                            params.get("half_life_games"))
    for m, (col, flag) in METRICS.items():
        mask = np.ones(len(p), bool) if flag is None else p[flag].values
        pm = p[mask]
        O, D, mu, h = fit_metric(pm, teams, prior[m][0], prior[m][1],
                                 pm[col].values.astype(float), w_all[mask],
                                 params["lambda"][m])
        out[f"o_{m}"], out[f"d_{m}"] = O, D
        out[f"mu_{m}"], out[f"h_{m}"] = mu, h
    out["n_plays_off"] = out.team_id.map(p.groupby("offense_id").size()).fillna(0).astype(int)
    out["n_plays_def"] = out.team_id.map(p.groupby("defense_id").size()).fillna(0).astype(int)
    return out


def season_ratings(model_plays, ctx: SeasonCtx, prior: dict, params: dict,
                   last_week: int | None = None) -> pd.DataFrame:
    """As-of ratings for every slot (optionally only through last_week)."""
    rows = []
    for s in ctx.slots.itertuples():
        if last_week is not None and s.week_asof > last_week:
            break
        r = fit_asof(model_plays, ctx, s.cutoff, prior, params)
        r.insert(0, "week_asof", s.week_asof)
        r.insert(0, "season", ctx.season)
        r["cutoff"] = s.cutoff
        rows.append(r)
    return pd.concat(rows, ignore_index=True)
