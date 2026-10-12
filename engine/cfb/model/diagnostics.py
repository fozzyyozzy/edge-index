"""Season-by-season diagnostics: residual sigma, prior R^2, weeks to stabilize.

    python -m engine.cfb.model.diagnostics       # -> docs/cfb/DIAGNOSTICS.md (0 API calls)

Informational only: nothing here changes a frozen parameter.
FBS vs FBS, non-CFP bowls excluded, completed games; results from games.parquet.
2022-2024 = tuning seasons (the frozen sigma was fit on their residuals), 2025 = holdout,
2026 = to date.
"""
from __future__ import annotations
from datetime import datetime

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.model import backtest as bt, distribution as dist, features, margin_model as mm, run as mrun
from engine.cfb.ratings import adjust, prior as prior_mod, run as rrun, to_points

DOC = config.ROOT / "docs" / "cfb" / "DIAGNOSTICS.md"
SEASONS = [2022, 2023, 2024, 2025, 2026]
RNG = np.random.default_rng(0)


def md(df, fmt="{:.2f}"):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in df.itertuples(index=False))


def boot_sd(x, n=2000):
    x = np.asarray(x, float)
    b = [x[RNG.integers(0, len(x), len(x))].std(ddof=1) for _ in range(n)]
    return np.percentile(b, 2.5), np.percentile(b, 97.5)


def slope(seasons, vals):
    s, v = np.asarray(seasons, float), np.asarray(vals, float)
    return float(np.polyfit(s, v, 1)[0])


# ------------------------------------------------------------------ 1. residual sigma
def residual_sigma(d: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    dp = mrun.dist_params(params)
    model = {"groups": params["groups"], "coef": params["coef"]}
    rows = []
    for s in SEASONS:
        x = d[(d.season == s) & d.margin_home.notna()].dropna(subset=["open_margin", "close_margin"])
        g, _ = bt.project(x, model, dp)
        r = g.margin_home - g.proj
        sig = dist.sigma([dp["a"], dp["b"], dp["c"]], g.absline, g.total_bet)
        z = r / sig
        lo, hi = boot_sd(r)
        rows.append({"season": s, "games": len(g),
                     "resid_sd_model": r.std(ddof=1), "ci95": f"{lo:.2f}-{hi:.2f}",
                     "robust_sd_model (1.4826*MAD)": 1.4826 * np.median(np.abs(r - np.median(r))),
                     "sd_vs_open": (g.margin_home - g.open_margin).std(ddof=1),
                     "sd_vs_close": (g.margin_home - g.close_margin).std(ddof=1),
                     "mean_total": g.total_bet.mean(),
                     "frozen_sigma_mean": sig.mean(),
                     "sd_of_z (want 1.00)": z.std(ddof=1),
                     "P(|z|>2) % (normal 4.6)": 100 * (z.abs() > 2).mean()})
    t = pd.DataFrame(rows)
    full = t[t.season <= 2025]
    sl = slope(full.season, full.resid_sd_model)
    slz = slope(full.season, full["sd_of_z (want 1.00)"])
    note = (f"Linear trend 2022-2025: residual SD {sl:+.2f} pts/season; SD of z {slz:+.3f}/season.")
    return t, note


# ------------------------------------------------------------------ 2. prior R^2
def prior_r2() -> pd.DataFrame:
    r = pd.read_parquet(plays_derived("ratings_asof.parquet"))
    pr = pd.read_parquet(plays_derived("priors.parquet"))
    rows = []
    for s in SEASONS:
        x = r[(r.season == s) & ~r.is_fcs]
        last = x.week_asof.max()
        w1 = x[x.week_asof == 1].set_index("team_id")
        end = x[x.week_asof == last].set_index("team_id")
        j = w1[["power_pts"]].join(end[["power_pts", "net_epa", "net_sr"]], lsuffix="_prior", how="inner")
        p = pr[pr.season == s].set_index("team_id")
        j = j.join(p[["o_epa", "d_epa", "o_sr", "d_sr", "prior_source"]], how="inner")

        def r2(y, yp):
            y, yp = np.asarray(y), np.asarray(yp)
            return 1 - ((y - yp) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        rows.append({"season": s, "teams": len(j),
                     "end_point": f"wk {int(last)}" + (" (partial season)" if s == config.CURRENT_SEASON else
                                                       " (pre-bowl)"),
                     "prior_method": j.prior_source.mode()[0],
                     "R2_power_pts": r2(j.power_pts, j.power_pts_prior),
                     "corr_power_pts": float(np.corrcoef(j.power_pts, j.power_pts_prior)[0, 1]),
                     "R2_net_epa": r2(j.net_epa, j.o_epa + j.d_epa),
                     "R2_net_sr": r2(j.net_sr, j.o_sr + j.d_sr)})
    return pd.DataFrame(rows)


def plays_derived(name):
    from engine.cfb.ratings.plays_prep import DERIVED
    return DERIVED / name


# ------------------------------------------------------------------ 3. weeks to stabilize
def data_only_ratings(data: rrun.Data, params: dict, s: int) -> pd.DataFrame:
    """As-of ratings with a ZERO prior (FCS teams at the FCS constant), same lambda."""
    mp = data.plays(params["garbage"])
    fcs = rrun.fcs_constants(data, mp, params)[s]
    ctx = data.ctx[s]
    pr = prior_mod.zero_prior(ctx.teams, fcs)
    r = adjust.season_ratings(mp[s], ctx, pr, params, last_week=rrun.last_ratable_week(data, s))
    r = to_points.add_nets(r)
    r["power_pts"] = to_points.power_points(r, params["to_points"])
    return r


def stabilize(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rp = rrun.load_params()
    hfa = rp["to_points"]["hfa"]
    blended = pd.read_parquet(plays_derived("ratings_asof.parquet"))
    data = rrun.Data()
    per_week, summary = [], []
    for s in SEASONS:
        x = d[(d.season == s) & d.margin_home.notna() & (d.season_type == "regular")].copy()
        b = blended[blended.season == s]
        do = data_only_ratings(data, rp, s)
        pw = lambda r, w: r[r.week_asof == w].set_index("team_id").power_pts  # noqa: E731
        prior = pw(b, 1)
        preds = {}
        for name, src in (("prior_only", None), ("blended", b), ("data_only", do)):
            vals = []
            for row in x.itertuples():
                if src is None:
                    ph, pa = prior.get(row.home_id, np.nan), prior.get(row.away_id, np.nan)
                else:
                    t = pw(src, row.week_asof)
                    ph, pa = t.get(row.home_id, np.nan), t.get(row.away_id, np.nan)
                vals.append(ph - pa + hfa * (not row.neutral_site))
            preds[name] = np.array(vals)
        x["err_prior"] = np.abs(x.margin_home - preds["prior_only"])
        x["err_blend"] = np.abs(x.margin_home - preds["blended"])
        x["err_data"] = np.abs(x.margin_home - preds["data_only"])
        x["err_open"] = np.abs(x.margin_home - x.open_margin)
        x = x.dropna(subset=["err_prior", "err_blend", "err_data"])
        wk = x.groupby("week_asof").agg(games=("game_id", "size"), prior=("err_prior", "mean"),
                                        blended=("err_blend", "mean"), data_only=("err_data", "mean"),
                                        open_line=("err_open", "mean")).reset_index()
        wk.insert(0, "season", s)
        per_week.append(wk)

        def first_stable(col):
            """first week w such that, for every 3-week window starting at w or later
            (through week 12), pooled MAE(col) < pooled MAE(prior)."""
            weeks = sorted(x.week_asof.unique())
            weeks = [w for w in weeks if w <= 12]
            for w in weeks:
                ok = True
                for v in [u for u in weeks if u >= w]:
                    win = x[x.week_asof.between(v, v + 2)]
                    if len(win) == 0 or win[col].mean() >= win.err_prior.mean():
                        ok = False
                        break
                if ok:
                    return int(w)
            return None
        summary.append({"season": s, "weeks_available": int(x.week_asof.max()),
                        "blended_beats_prior_from_wk": first_stable("err_blend"),
                        "data_only_beats_prior_from_wk": first_stable("err_data"),
                        "wk1-3 MAE prior / blended / data-only":
                            " / ".join(f"{x[x.week_asof <= 3][c].mean():.2f}"
                                       for c in ("err_prior", "err_blend", "err_data")),
                        "wk4-6 MAE prior / blended / data-only":
                            " / ".join(f"{x[x.week_asof.between(4, 6)][c].mean():.2f}"
                                       for c in ("err_prior", "err_blend", "err_data"))})
    return pd.DataFrame(summary), pd.concat(per_week, ignore_index=True)


def main() -> int:
    params = mrun.load_params()
    d = mm.prep(features.load())
    sig, sig_note = residual_sigma(d, params)
    r2 = prior_r2()
    stab, per_week = stabilize(d)
    T = [f"# CFB season diagnostics\n\n_Generated {datetime.now():%Y-%m-%d %H:%M} by "
         f"`python -m engine.cfb.model.diagnostics`. Informational; no parameter changes. "
         f"2022-24 tuning (the frozen sigma was fit on these residuals), 2025 holdout, 2026 to date._\n",
         "## 1. Residual sigma by season (frozen Phase 3 projection)\n", md(sig), f"\n{sig_note}\n",
         "\n## 2. Preseason prior R^2 by season (prior vs end-of-regular-season rating, FBS)\n",
         md(r2, "{:.3f}"),
         "\n## 3. Weeks to stabilize\n",
         "MAE of a ratings-only margin (power_home - power_away + HFA) on each week's games. "
         "`prior` = week-1 ratings carried all season; `blended` = the as-of ratings we use "
         "(prior + data); `data_only` = the same fit with a zero prior (data alone). "
         "'Beats prior from week w' = every 3-week window from w through week 12 has a lower "
         "pooled MAE than the prior.\n", md(stab),
         "\n<details><summary>Per-week MAE</summary>\n\n", md(per_week), "\n</details>\n"]
    DOC.write_text("\n".join(T), encoding="utf-8")
    print("\n".join(T[:8]))
    print(md(stab))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
