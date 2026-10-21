"""NBA floor model (Phase 2): P(stat >= k) = minutes projection x per-minute rate -> count distribution.

Everything a projection uses comes from games strictly before the game's date (PREREG §1, rule 4):
features are computed on each player's played games in date order and shifted one game, and an NBA player can't
play twice on a date. The target game's own starter flag is never used (lineups aren't known pregame); the role
signal is the share of the player's last 5 games he started.

    minutes  m_hat = b0 + b1*m_ewma + b2*start5 + b3*b2b + b4*abs_spread + b5*abs_spread*start5
    rate     r = (sum_w stat + kappa * r_prior) / (sum_w minutes + kappa)      w = EWMA weights, halflife h_r games
             r_prior = the player's previous-season rate (>= 300 min), else the position group's league rate
             (previous season; for 2023-24, the first season loaded, that season's own league rate: train only)
    matchup  mu *= (opp allowed rate / league rate) ** gamma   (gamma chosen on 2024-25 validation; 0 = off)
    mean     mu = m_hat * r
    dist     per market: Poisson, negative binomial (theta), or a discretised normal, gamma, or empirical-residual
             shape with var = a*mu + b*mu^2. gamma and dresid (the training residuals' own standardised shape, as
             401 quantiles) were added during 2024-25 validation: the normal was too timid at both ends for
             points and its combos, and the gamma overcorrected
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd
from scipy import stats as st

STATS = ["pts", "reb", "ast", "fg3m", "pr", "pa", "ra", "pra", "stl", "blk"]
HOLDOUT = "2025-26"
GROUP = {"G": "G", "PG": "G", "SG": "G", "F": "F", "SF": "F", "PF": "F", "C": "C"}
PRIOR_MIN_MINUTES = 300
KMAX = {"pts": 70, "reb": 30, "ast": 25, "fg3m": 14, "pr": 80, "pa": 80, "ra": 45, "pra": 95, "stl": 10, "blk": 12}


@dataclass
class Config:
    h_m: float = 10.0                     # minutes EWMA halflife (games)
    h_r: dict = field(default_factory=lambda: {s: 20.0 for s in STATS})        # rate halflife per market
    kappa: dict = field(default_factory=lambda: {s: 300.0 for s in STATS})     # shrinkage, minutes-equivalent
    gamma: dict = field(default_factory=lambda: {s: 0.0 for s in STATS})       # matchup exponent
    minutes_coef: list = field(default_factory=list)
    dist: dict = field(default_factory=dict)          # market -> {"family": ..., params}

    def to_dict(self):
        return asdict(self)


def guard(pg: pd.DataFrame, holdout: bool):
    """development code must never see a holdout outcome"""
    if not holdout and (pg.season == HOLDOUT).any():
        raise RuntimeError("holdout season present outside the registered holdout run")


def _ewm_sum(s: pd.Series, keys, h: float) -> pd.Series:
    """EWMA-weighted sum of strictly-earlier values within each player-season (current game excluded)"""
    return s.groupby(keys).transform(lambda x: x.shift().ewm(halflife=h).sum())


def base_frame(pg: pd.DataFrame) -> pd.DataFrame:
    p = pg[pg.played].sort_values(["espn_id", "season", "date"]).copy()
    p["grp"] = p.position.map(GROUP).fillna("F")
    p["abs_spread"] = p.team_spread.abs().fillna(p.team_spread.abs().median())
    keys = [p.espn_id, p.season]
    p["start5"] = p.groupby(["espn_id", "season"]).starter.transform(
        lambda x: x.astype(float).shift().rolling(5, min_periods=1).mean())
    p["n_prior"] = p.groupby(["espn_id", "season"]).cumcount()
    return p


def prior_rates(pg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """player-season totals (for the next season's prior) and position-group league rates per season"""
    p = pg[pg.played].assign(grp=pg.position.map(GROUP).fillna("F"))
    tot = p.groupby(["espn_id", "season"])[["minutes"] + STATS].sum().reset_index()
    lg = p.groupby(["season", "grp"])[["minutes"] + STATS].sum()
    lg = lg[STATS].div(lg.minutes, axis=0).reset_index()
    return tot, lg


def prev_season(s: str) -> str:
    y = int(s[:4]) - 1
    return f"{y}-{str(y + 1)[-2:]}"


def opp_factors(pg: pd.DataFrame, h: float = 15.0) -> pd.DataFrame:
    """per (game, team-as-opponent): EWMA of stat allowed per 240 minutes in strictly-earlier games / league"""
    p = pg[pg.played]
    allowed = p.groupby(["game_id", "date", "season", "opp"])[["minutes"] + STATS].sum().reset_index()
    allowed = allowed.sort_values(["opp", "season", "date"])
    out = allowed[["game_id", "opp"]].copy()
    for s in STATS:
        num = _ewm_sum(allowed[s], [allowed.opp, allowed.season], h)
        den = _ewm_sum(allowed.minutes, [allowed.opp, allowed.season], h)
        lg = allowed.groupby("season")[s].transform("sum") / allowed.groupby("season").minutes.transform("sum")
        out[f"opp_{s}"] = (num / den) / lg
    return out


def features(pg: pd.DataFrame, cfg: Config, holdout: bool = False) -> pd.DataFrame:
    guard(pg, holdout)
    p = base_frame(pg)
    keys = [p.espn_id, p.season]
    p["m_ewma"] = p.groupby(["espn_id", "season"]).minutes.transform(lambda x: x.shift().ewm(halflife=cfg.h_m).mean())
    tot, lg = prior_rates(pg)
    prev = tot.assign(season=tot.season.map(lambda s: f"{int(s[:4]) + 1}-{str(int(s[:4]) + 2)[-2:]}"))
    p = p.merge(prev.rename(columns={c: f"prev_{c}" for c in ["minutes"] + STATS}), on=["espn_id", "season"],
                how="left")
    lg_prev = lg.assign(season=lg.season.map(lambda s: f"{int(s[:4]) + 1}-{str(int(s[:4]) + 2)[-2:]}"))
    first = lg[lg.season == lg.season.min()]                 # first loaded season has no previous: its own (train)
    lg_prev = pd.concat([lg_prev, first]).drop_duplicates(["season", "grp"], keep="first")
    p = p.merge(lg_prev.rename(columns={s: f"lg_{s}" for s in STATS}), on=["season", "grp"], how="left")
    p = p.merge(opp_factors(pg), on=["game_id", "opp"], how="left")
    keys = [p.espn_id, p.season]
    for s in STATS:
        own = p[f"prev_{s}"] / p.prev_minutes
        prior = own.where(p.prev_minutes >= PRIOR_MIN_MINUTES, p[f"lg_{s}"])
        num = _ewm_sum(p[s].astype(float), keys, cfg.h_r[s])
        den = _ewm_sum(p.minutes.astype(float), keys, cfg.h_r[s])
        k = cfg.kappa[s]
        p[f"rate_{s}"] = (num.fillna(0) + k * prior) / (den.fillna(0) + k)
    return p


MIN_X = ["m_ewma", "start5", "b2b", "abs_spread", "spread_x_start"]


def _min_design(p: pd.DataFrame) -> np.ndarray:
    x = p.assign(spread_x_start=p.abs_spread * p.start5, b2b=p.b2b.astype(float))[MIN_X].to_numpy(float)
    return np.column_stack([np.ones(len(x)), x])


def fit_minutes(p: pd.DataFrame) -> list:
    X, y = _min_design(p), p.minutes.to_numpy(float)
    return np.linalg.lstsq(X, y, rcond=None)[0].tolist()


def mu(p: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    m_hat = np.clip(_min_design(p) @ np.asarray(cfg.minutes_coef), 1.0, 48.0)
    out = pd.DataFrame(index=p.index)
    out["m_hat"] = m_hat
    for s in STATS:
        f = p[f"opp_{s}"].fillna(1.0).clip(0.7, 1.4) ** cfg.gamma[s]
        out[f"mu_{s}"] = np.maximum(m_hat * p[f"rate_{s}"] * f, 0.05)
    return out


# ---------- distributions ----------
def sf(family: str, params: dict, mu_: np.ndarray, k: np.ndarray) -> np.ndarray:
    """P(Y >= k) for arrays mu_ (n,1) and k (1,K)"""
    if family == "poisson":
        return st.poisson.sf(k - 1, mu_)
    if family == "nbinom":
        th = params["theta"]
        return st.nbinom.sf(k - 1, th, th / (th + mu_))
    if family == "dnorm":
        sd = np.sqrt(np.maximum(params["a"] * mu_ + params["b"] * mu_ ** 2, 0.25))
        return st.norm.sf((k - 0.5 - mu_) / sd)
    if family == "dresid":
        sd = np.sqrt(np.maximum(params["a"] * mu_ + params["b"] * mu_ ** 2, 0.25))
        z = (k - 0.5 - mu_) / sd
        F = np.interp(z, np.asarray(params["zq"]), np.linspace(0, 1, len(params["zq"])))
        return np.clip(1 - F, 5e-4, 1 - 5e-4)
    if family == "dgamma":
        var = np.maximum(params["a"] * mu_ + params["b"] * mu_ ** 2, 0.25)
        shape, scale = mu_ ** 2 / var, var / mu_
        return st.gamma.sf(np.maximum(k - 0.5, 0), shape, scale=scale)
    raise ValueError(family)


def fit_family(family: str, mu_: np.ndarray, y: np.ndarray) -> dict:
    if family == "poisson":
        return {}
    if family == "nbinom":
        best = None
        for th in np.exp(np.linspace(np.log(0.5), np.log(500), 60)):
            ll = st.nbinom.logpmf(y, th, th / (th + mu_)).sum()
            if best is None or ll > best[0]:
                best = (ll, th)
        return {"theta": float(best[1])}
    if family in ("dnorm", "dgamma", "dresid"):
        r2 = (y - mu_) ** 2
        X = np.column_stack([mu_, mu_ ** 2])
        a, b = np.linalg.lstsq(X, r2, rcond=None)[0]
        par = {"a": float(max(a, 0.1)), "b": float(max(b, 0.0))}
        if family == "dresid":          # shape from the training residuals, standardised by the fitted sd
            sd = np.sqrt(np.maximum(par["a"] * mu_ + par["b"] * mu_ ** 2, 0.25))
            par["zq"] = np.quantile((y - mu_) / sd, np.linspace(0, 1, 401)).round(5).tolist()
        return par
    raise ValueError(family)


def rps(family: str, params: dict, mu_: np.ndarray, y: np.ndarray, kmax: int) -> float:
    """mean ranked probability score over thresholds 1..kmax (proper; row set independent of the model)"""
    k = np.arange(1, kmax + 1)[None, :]
    p = sf(family, params, mu_[:, None], k)
    return float(((p - (y[:, None] >= k)) ** 2).sum(axis=1).mean())


def prob_table(p: pd.DataFrame, m: pd.DataFrame, cfg: Config, stat: str, kmax: int | None = None) -> pd.DataFrame:
    """long table: one row per (player-game, rung k) with model p and outcome"""
    kmax = kmax or KMAX[stat]
    k = np.arange(1, kmax + 1)
    d = cfg.dist[stat]
    probs = sf(d["family"], d, m[f"mu_{stat}"].to_numpy()[:, None], k[None, :])
    n = len(p)
    out = pd.DataFrame({"row": np.repeat(p.index.to_numpy(), kmax), "k": np.tile(k, n), "p": probs.ravel(),
                        "y": (np.repeat(p[stat].to_numpy(), kmax) >= np.tile(k, n)).astype(int)})
    return out
