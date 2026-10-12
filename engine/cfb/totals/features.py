"""As-of totals features (Phase 5B), built the Phase 2 way.

For each stat X in {pts, ppd, drives, plays, spp, xpl} and every (season, week slot), a ridge
fit on team-games that kicked off strictly before the slot cutoff:
    X[team, game] = mu + O[team] - D[opp] + h * home + e        (D > 0: opponents get less X)
shrunk toward a prior of PRIOR_FACTOR x last season's final O/D (FCS teams: 0), with a
fixed ridge strength (LAMBDA_GAMES, in team-games). No tuning here.

Per game (home H vs away A), expected X for H = mu + O_H - D_A + h*home_H, and:
  T_pts = E_H[pts] + E_A[pts]
  T_ppd = E_H[ppd] * E_H[drives] + E_A[ppd] * E_A[drives]
  T_epa = sum over teams of E[plays] * (mu_pts / mu_plays + dEPA), where dEPA is the Phase 2
          as-of EPA matchup (o_epa_off - d_epa_def, centered on the FBS means at that slot)
  tempo_clash = |E_H[plays] - E_A[plays]|
  expl_match  = O_xpl_H * (-D_xpl_A) + O_xpl_A * (-D_xpl_H)   (explosive offense vs a defense
                that gives up explosive plays)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.model import features as mfeat
from engine.cfb.ratings import adjust
from engine.cfb.totals import team_games as tg_mod

STATS = ["pts", "ppd", "drives", "plays", "spp", "xpl"]
PRIOR_FACTOR = 0.5
LAMBDA_GAMES = 4.0
TOTALS_GAMES = tg_mod.DERIVED / "totals_games.parquet"


def team_ratings(games: pd.DataFrame, tg: pd.DataFrame) -> pd.DataFrame:
    """(season, week_asof, team_id) -> o_X, d_X, mu_X, h_X for every stat."""
    rows, prev = [], None
    for s in mfeat.SEASONS:
        ctx = adjust.season_ctx(games, s)
        teams = ctx.teams.team_id.values
        fcs = ctx.teams.set_index("team_id").is_fcs.reindex(teams).values
        d = tg[tg.season == s].rename(columns={"team_id": "offense_id", "opp_id": "defense_id",
                                               "home": "offense_home"})
        priors = {}
        for x in STATS:
            if prev is None:
                po, pd_ = pd.Series(0.0, index=teams), pd.Series(0.0, index=teams)
                mu0 = float(d[x].mean())            # 2021 burn-in only (never evaluated)
            else:
                po = (PRIOR_FACTOR * prev[f"o_{x}"]).reindex(teams).fillna(0.0)
                pd_ = (PRIOR_FACTOR * prev[f"d_{x}"]).reindex(teams).fillna(0.0)
                mu0 = float(prev[f"mu_{x}"].iloc[0])
            po[fcs], pd_[fcs] = 0.0, 0.0
            priors[x] = (po, pd_, mu0)

        def fit(cut):
            dd = d if cut is None else d[d.kickoff_utc < cut]
            out = pd.DataFrame({"team_id": teams})
            for x in STATS:
                po, pd_, mu0 = priors[x]
                z = dd.dropna(subset=[x])
                O, D, mu, h = adjust.fit_metric(z, teams, po, pd_, z[x].to_numpy(float),
                                                np.ones(len(z)), LAMBDA_GAMES)
                out[f"o_{x}"], out[f"d_{x}"] = O, D
                out[f"mu_{x}"] = mu if np.isfinite(mu) else mu0
                out[f"h_{x}"] = h if np.isfinite(h) else 0.0
            return out

        for w, cut in ctx.slots[["week_asof", "cutoff"]].itertuples(index=False):
            r = fit(cut)
            r["season"], r["week_asof"] = s, w
            rows.append(r)
        prev = fit(None).set_index("team_id")
    return pd.concat(rows, ignore_index=True)


def game_features(mg: pd.DataFrame, tr: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    """mg: Phase 3 model_games rows. Adds T_pts, T_ppd, T_epa, tempo_clash, expl_match."""
    key = ["season", "week_asof"]
    out = mg.copy()
    for side in ("home", "away"):
        t = tr.rename(columns={"team_id": f"{side}_id", **{c: f"{side}_{c}" for c in tr.columns
                                                          if c not in ("team_id", "season", "week_asof")}})
        out = out.merge(t, on=key + [f"{side}_id"], how="left")
    hh = np.where(out.neutral_site.astype(bool), 0.0, 1.0)

    def E(x, side):
        opp = "away" if side == "home" else "home"
        sign = hh if side == "home" else -hh
        return (out[f"home_mu_{x}"] + out[f"{side}_o_{x}"] - out[f"{opp}_d_{x}"]
                + out[f"home_h_{x}"] * sign)
    for x in ("pts", "ppd", "drives", "plays"):
        out[f"E_home_{x}"], out[f"E_away_{x}"] = E(x, "home"), E(x, "away")
    out["T_pts"] = out.E_home_pts + out.E_away_pts
    out["T_ppd"] = out.E_home_ppd * out.E_home_drives + out.E_away_ppd * out.E_away_drives
    # Phase 2 EPA matchup, centered on FBS means at the slot
    r = ratings[["season", "week_asof", "team_id", "o_epa", "d_epa", "is_fcs"]]
    means = r[~r.is_fcs].groupby(key)[["o_epa", "d_epa"]].mean().rename(columns=lambda c: f"m_{c}")
    for side in ("home", "away"):
        out = out.merge(r.drop(columns="is_fcs").rename(columns={"team_id": f"{side}_id", "o_epa": f"{side}_o_epa",
                                                                  "d_epa": f"{side}_d_epa"}),
                        on=key + [f"{side}_id"], how="left")
    out = out.merge(means.reset_index(), on=key, how="left")
    ppp = out.home_mu_pts / out.home_mu_plays
    d_home = (out.home_o_epa - out.m_o_epa) - (out.away_d_epa - out.m_d_epa)
    d_away = (out.away_o_epa - out.m_o_epa) - (out.home_d_epa - out.m_d_epa)
    out["T_epa"] = out.E_home_plays * (ppp + d_home) + out.E_away_plays * (ppp + d_away)
    out["tempo_clash"] = (out.E_home_plays - out.E_away_plays).abs()
    out["expl_match"] = out.home_o_xpl * (-out.away_d_xpl) + out.away_o_xpl * (-out.home_d_xpl)
    out["E_plays_sum"] = out.E_home_plays + out.E_away_plays
    out["actual_total"] = out.margin_home * np.nan
    return out


def build(write: bool = True, games=None, tg=None, mg=None, ratings=None) -> pd.DataFrame:
    games = games if games is not None else pd.read_parquet(config.CLEAN / "games.parquet")
    tg = tg if tg is not None else tg_mod.load()
    mg = mg if mg is not None else mfeat.load()
    ratings = ratings if ratings is not None else pd.read_parquet(mfeat.DERIVED / "ratings_asof.parquet")
    tr = team_ratings(games, tg)
    out = game_features(mg, tr, ratings)
    pts = games.set_index("game_id")
    out["actual_total"] = out.game_id.map(pts.home_points + pts.away_points)
    keep = ["game_id", "season", "week", "week_asof", "bucket", "kickoff_utc", "neutral_site",
            "home_id", "home_team", "away_id", "away_team", "margin_home", "actual_total",
            "provider", "total_open", "total_close", "total_bet", "spread_open", "open_margin",
            "T_pts", "T_ppd", "T_epa", "tempo_clash", "expl_match", "E_plays_sum",
            "E_home_pts", "E_away_pts"]
    out = out[keep]
    if write:
        out.to_parquet(TOTALS_GAMES, index=False)
    return out


def load() -> pd.DataFrame:
    if not TOTALS_GAMES.exists():
        build()
    return pd.read_parquet(TOTALS_GAMES)


if __name__ == "__main__":
    t = build()
    # tuning seasons only: 2025 is the totals holdout, 2026 informational
    x = t[t.season.isin([2022, 2023, 2024])].dropna(subset=["actual_total", "total_open"])
    for c in ("T_pts", "T_ppd", "T_epa"):
        e = x.dropna(subset=[c])
        print(c, "MAE vs actual %.2f | open MAE %.2f | corr(T-open, actual-open) %.3f | n %d" % (
            (e.actual_total - e[c]).abs().mean(), (e.actual_total - e.total_open).abs().mean(),
            np.corrcoef(e[c] - e.total_open, e.actual_total - e.total_open)[0, 1], len(e)))
