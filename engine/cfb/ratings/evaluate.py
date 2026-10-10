"""Phase 2 evaluation + report (brief §7, §10).

Called by run.py. All evaluation uses as-of-week ratings, FBS-vs-FBS games,
non-CFP bowls excluded. 2025 numbers are produced only by the one-time
`run.py --holdout`, into their own report block and docs/cfb/holdout_2025.json.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr

from engine.cfb import config
from engine.cfb.ratings import plays_prep, to_points
from engine.cfb.ratings import run as run_mod

REPORT = config.ROOT / "docs" / "cfb" / "PHASE2_REPORT.md"
BLOCKS = ("TUNING", "HOLDOUT")


# ------------------------------------------------------------------ live slate
def asof_slate(d, params: dict, season: int, week: int) -> pd.DataFrame:
    """Ratings for (season, week) using only games that kicked off before the cutoff."""
    out = run_mod.build(d, params, list(range(run_mod.FIRST, season + 1)), last_week=week)
    r = out["ratings"]
    r = r[(r.season == season) & (r.week_asof == week)].copy()
    if r.empty:
        raise SystemExit(f"no slot {week} in {season}")
    r["power_pts"] = to_points.power_points(r, params["to_points"])
    cut = r.cutoff.iloc[0]
    g = d.games
    need = g[(g.season == season) & g.fbs_involved & (g.kickoff_utc < cut)
             & (g.completed == True) & ~(g.is_bowl & ~g.is_cfp)]  # noqa: E712
    missing = need[~need.game_id.isin(d.mp.game_id)]
    if len(missing):
        print(f"WARNING: {len(missing)} completed FBS games before the cutoff have no "
              f"plays yet (run python -m engine.cfb.update_week): "
              f"{', '.join((missing.away_team + ' @ ' + missing.home_team).head(8))}")
    return r


# ------------------------------------------------------------------ helpers
def md(df: pd.DataFrame, fmt: str = "{:.2f}") -> str:
    if df.empty:
        return "_(none)_\n"
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in df.itertuples(index=False))


def bucket(w: pd.Series, season_type: pd.Series) -> pd.Series:
    b = np.select([w <= 3, w <= 8], ["wk 1-3", "wk 4-8"], default="wk 9+")
    return pd.Series(np.where(season_type == "postseason", "post (CFP)", b), index=w.index)


def eval_frame(d, out: dict, params: dict, seasons) -> pd.DataFrame:
    """Games with ratings pred, prior-only pred, HFA-only pred, closing spread."""
    coef = params["to_points"]
    r = out["ratings"]
    g, slot = run_mod.eval_games(d, seasons)
    gf = to_points.game_frame(g, r, slot)
    gf["pred_margin"] = to_points.predict(gf, coef)
    # prior-only: week-1 ratings carried all season
    r1 = r[r.week_asof == 1].drop(columns="week_asof")
    nets = [c for c in r.columns if c.startswith("net_")]
    pf = g.copy()
    for side in ("home", "away"):
        pf = pf.merge(r1[["season", "team_id"] + nets].rename(
            columns={"team_id": f"{side}_id", **{c: f"{side}_{c}" for c in nets}}),
            on=["season", f"{side}_id"], how="inner")
    pf["hfa"] = (~pf.neutral_site.astype(bool)).astype(float)
    pf["prior_margin"] = to_points.predict(pf, coef)
    gf = gf.merge(pf[["game_id", "prior_margin"]], on="game_id", how="left")
    gf["hfa_margin"] = coef["hfa"] * gf.hfa
    gf["close_margin"] = -gf.consensus_close_spread
    gf["bucket"] = bucket(gf.week_asof, gf.season_type)
    return gf


def accuracy(gf: pd.DataFrame, by) -> pd.DataFrame:
    g = gf.dropna(subset=["close_margin", "prior_margin"])

    def f(x):
        e = lambda col: x.margin_home - x[col]  # noqa: E731
        return pd.Series({
            "games": len(x),
            "ratings_MAE": e("pred_margin").abs().mean(),
            "ratings_RMSE": np.sqrt((e("pred_margin") ** 2).mean()),
            "close_MAE": e("close_margin").abs().mean(),
            "prior_only_MAE": e("prior_margin").abs().mean(),
            "hfa_only_MAE": e("hfa_margin").abs().mean(),
        })
    if by is None:
        return f(g).to_frame().T
    return g.groupby(by).apply(f).reset_index()


def against_number(gf: pd.DataFrame, label: str) -> pd.DataFrame:
    g = gf.dropna(subset=["consensus_close_spread"])
    rows = []
    for thr in (3, 5, 7):
        diff = g.pred_margin - g.close_margin           # ratings minus market, home pts
        x = g[diff.abs() >= thr]
        side_home = (x.pred_margin > x.close_margin)
        res = x.margin_home + x.consensus_close_spread   # >0 home covers
        push = res == 0
        win = np.where(side_home, res > 0, res < 0)[~push.values]
        n, k = len(win), int(win.sum())
        ci = binomtest(k, n).proportion_ci(method="wilson") if n else None
        rows.append({"games": label, "|ratings - close| >=": thr, "bets": n, "wins": k,
                     "win_pct": 100 * k / n if n else np.nan,
                     "ci95_lo": 100 * ci.low if ci else np.nan,
                     "ci95_hi": 100 * ci.high if ci else np.nan, "pushes": int(push.sum())})
    return pd.DataFrame(rows)


def top25(d, out: dict, season: int, week_asof: int | None = None):
    r = out["ratings"]
    s = r[(r.season == season) & ~r.is_fcs]
    w = week_asof or s.week_asof.max()
    s = s[s.week_asof == w].sort_values("power_pts", ascending=False).reset_index(drop=True)
    s["rank"] = np.arange(1, len(s) + 1)
    b = pd.read_parquet(config.CLEAN / "benchmarks.parquet")
    b = b[b.season == season][["team_id", "sp_rank", "sp_rating"]]
    s = s.merge(b, on="team_id", how="left")
    s["gap"] = s["rank"] - s.sp_rank
    return w, s


def stability(out: dict, seasons) -> pd.DataFrame:
    r = out["ratings"]
    rows = []
    for s in seasons:
        x = r[(r.season == s) & ~r.is_fcs].pivot(index="team_id", columns="week_asof",
                                                 values="power_pts")
        cors = [spearmanr(x[a], x[b], nan_policy="omit")[0]
                for a, b in zip(x.columns[:-1], x.columns[1:])]
        cors = pd.Series(cors, index=x.columns[1:])
        rows.append({"season": s, "weeks": len(cors), "mean_rho": cors.mean(),
                     "min_rho": cors.min(), "min_at_week": int(cors.idxmin()),
                     "rho_wk2": cors.iloc[0], "rho_late_mean": cors.iloc[-6:].mean()})
    return pd.DataFrame(rows)


def prior_accuracy(out: dict, seasons) -> pd.DataFrame:
    pr, rows = out["priors"], []
    for s in seasons:
        t = out["targets"].get(s)
        if t is None:
            continue
        m = pr[(pr.season == s)].merge(t, on="team_id", suffixes=("_prior", ""))
        m = m[~m.is_fcs]
        row = {"season": s, "teams": len(m), "method": pr[pr.season == s].prior_source.mode()[0]}
        for col in ("o_epa", "d_epa", "o_sr", "d_sr", "net_epa"):
            if col == "net_epa":
                yp = m.o_epa_prior + m.d_epa_prior
                y = m.o_epa + m.d_epa
            else:
                yp, y = m[f"{col}_prior"], m[col]
            row[f"R2_{col}"] = 1 - ((y - yp) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ report
def write_block(name: str, text: str) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    doc = REPORT.read_text(encoding="utf-8") if REPORT.exists() else "# CFB Phase 2 Report\n"
    b, e = f"<!-- AUTO:{name}:BEGIN -->", f"<!-- AUTO:{name}:END -->"
    block = f"{b}\n{text}\n{e}"
    if b in doc and e in doc:
        doc = doc[:doc.index(b)] + block + doc[doc.index(e) + len(e):]
    else:
        doc += f"\n{block}\n"
    REPORT.write_text(doc, encoding="utf-8")


def report(d, out: dict, params: dict, holdout: bool = False) -> None:
    tune, live = run_mod.TUNE_SEASONS, [config.CURRENT_SEASON]
    P = [f"_Generated by `python -m engine.cfb.ratings.run` at {datetime.now():%Y-%m-%d %H:%M}._\n"]

    counts = json.loads(plays_prep.DROP_COUNTS.read_text())["counts"]
    c = pd.DataFrame(counts).fillna(0).astype(int)      # reasons x seasons
    order = ["kept", "garbage_time", "not_scrimmage", "non_cfp_bowl", "kneel_or_spike",
             "duplicate", "null_ppa", "bad_down"]
    c = c.reindex([o for o in order if o in c.index])
    P += ["### Play filtering (plays from FBS-involved games; first matching reason)\n",
          md(c.rename_axis("reason").reset_index(), "{:.0f}")]
    P.append(f"Garbage-time rows above are at the default thresholds; the frozen thresholds "
             f"are {params['garbage']}.\n")

    P += ["\n### Frozen parameters (`engine/cfb/ratings/params.json`)\n",
          "```json\n" + json.dumps(params, indent=2) + "\n```\n"]
    grid = plays_prep.DERIVED / "tuning_grid.csv"
    if grid.exists():
        gr = pd.read_csv(grid).sort_values("mae")
        P += [f"\n### Tuning grid ({len(gr)} configs, 2022-2024 margin MAE; best first)\n",
              md(gr.drop(columns=["sec"]), "{:.4g}")]

    P.append("\n### Prior model\n")
    P.append(f"FCS constants (vs FBS average): "
             + "; ".join(f"{s}: o_epa {v['o_epa']:+.3f}, d_epa {v['d_epa']:+.3f}"
                         for s, v in out["fcs_const"].items() if s in (2021, 2023)) + "\n")
    for info in out["prior_info"]:
        cf = pd.DataFrame(info["coef"]).T.reset_index().rename(columns={"index": "rating"})
        if "n" in cf:
            cf["n"] = cf.n.astype(int)
        P += [f"\n**{info['season']} prior** ({info.get('method')}, trained on target seasons "
              f"{info['pair_seasons'] or 'none'})\n", md(cf, "{:+.3f}")]
    P += ["\nPrior accuracy (prior vs end-of-regular-season rating, FBS teams, out of sample):\n",
          md(prior_accuracy(out, tune), "{:.3f}")]

    gf = eval_frame(d, out, params, tune + live)
    gt_ = gf[gf.season.isin(tune)]
    P += ["\n### Margin accuracy: tuning seasons 2022-2024 (in-sample for the hyperparameters)\n",
          "Same games in every column: FBS-vs-FBS, non-CFP bowls excluded, with a consensus close.\n",
          md(accuracy(gt_, None).assign(slice="2022-2024 all")[
              ["slice", "games", "ratings_MAE", "ratings_RMSE", "close_MAE",
               "prior_only_MAE", "hfa_only_MAE"]]),
          "\nBy season:\n", md(accuracy(gt_, "season")),
          "\nBy week bucket:\n", md(accuracy(gt_, "bucket"))]
    gl = gf[gf.season.isin(live)]
    P += [f"\n**2026 to date (informational, partial season):**\n",
          md(accuracy(gl, "bucket"))]

    P += ["\n### Against the number (UNCALIBRATED DIAGNOSTIC, not a betting result)\n",
          "Ratings side vs consensus close when they disagree by the threshold; pushes excluded; "
          "Wilson 95% CI.\n",
          md(pd.concat([against_number(gt_, "2022-2024"), against_number(gl, "2026 to date")]),
             "{:.1f}")]

    P.append("\n### Sanity top 25 vs CFBD SP+ (SP+ = leaky benchmark, end-of-season)\n")
    for s in [2024] + live:
        w, t = top25(d, out, s)
        label = "end of regular season" if s < config.CURRENT_SEASON else f"as of week {w}"
        P += [f"\n**{s}, {label}** (SP+ rank is season-final)\n",
              md(t.head(25)[["rank", "team", "power_pts", "sp_rank"]], "{:+.1f}")]
        dis = t[t["rank"] <= 40].dropna(subset=["sp_rank"])
        dis = dis.reindex(dis.gap.abs().sort_values(ascending=False).index).head(5)
        P += ["Biggest disagreements (top 40 by power):\n",
              md(dis[["rank", "team", "power_pts", "sp_rank", "gap"]], "{:+.1f}")]

    P += ["\n### Stability (Spearman rho of power ratings, consecutive as-of weeks, FBS)\n",
          md(stability(out, [2022, 2023, 2024] + live), "{:.3f}")]
    write_block("TUNING", "\n".join(P))

    if holdout:
        gh = gf_h = eval_frame(d, out, params, [run_mod.HOLDOUT])
        H = [f"_2025 held-out evaluation, run once at {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
             f"with params.json sha256 {sha(run_mod.PARAMS)[:12]}._\n",
             md(accuracy(gh, None).assign(slice="2025 held out")[
                 ["slice", "games", "ratings_MAE", "ratings_RMSE", "close_MAE",
                  "prior_only_MAE", "hfa_only_MAE"]]),
             "\nBy week bucket:\n", md(accuracy(gh, "bucket")),
             "\nPrior accuracy, 2025:\n", md(prior_accuracy(out, [run_mod.HOLDOUT]), "{:.3f}"),
             "\nAgainst the number, 2025 (UNCALIBRATED DIAGNOSTIC):\n",
             md(against_number(gh, "2025"), "{:.1f}"),
             "\nStability, 2025:\n", md(stability(out, [run_mod.HOLDOUT]), "{:.3f}")]
        w, t = top25(d, out, run_mod.HOLDOUT)
        H += [f"\n**2025 top 25, end of regular season** (SP+ = leaky benchmark, season-final)\n",
              md(t.head(25)[["rank", "team", "power_pts", "sp_rank"]], "{:+.1f}")]
        dis = t[t["rank"] <= 40].dropna(subset=["sp_rank"])
        dis = dis.reindex(dis.gap.abs().sort_values(ascending=False).index).head(5)
        H += ["Biggest disagreements:\n", md(dis[["rank", "team", "power_pts", "sp_rank", "gap"]], "{:+.1f}")]
        write_block("HOLDOUT", "\n".join(H))
        acc = accuracy(gh, None).iloc[0].to_dict()
        run_mod.HOLDOUT_LOG.write_text(json.dumps({
            "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "params_sha256": sha(run_mod.PARAMS), **{k: float(v) for k, v in acc.items()}},
            indent=2) + "\n")
    print(f"report -> {REPORT.relative_to(config.ROOT)}")


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
