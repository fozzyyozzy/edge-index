"""Phase 3 game model: tune, report, one-time 2025 holdout.

    python -m engine.cfb.model.run --tune      # select features + distribution on 2022-2024 -> params.json
    python -m engine.cfb.model.run             # report: tuning (LOSO) + 2026 to date
    python -m engine.cfb.model.run --holdout   # ONE-TIME 2025 evaluation (params.json committed)

Zero API calls. Inputs: data/cfb/derived/ratings_asof.parquet (Phase 2) and
the clean tables; features are (re)built by engine.cfb.model.features.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.model import backtest as bt, distribution as dist, features, margin_model as mm

HERE = Path(__file__).resolve().parent
PARAMS = HERE / "params.json"
TUNE = [2022, 2023, 2024]
HOLDOUT = 2025
LIVE = config.CURRENT_SEASON
REPORT = config.ROOT / "docs" / "cfb" / "PHASE3_REPORT.md"
HOLDOUT_LOG = config.ROOT / "docs" / "cfb" / "holdout_2025_model.json"


def data() -> pd.DataFrame:
    return mm.prep(features.build())


def load_params() -> dict:
    return json.loads(PARAMS.read_text())


def dist_params(p: dict) -> dict:
    d = dict(p["distribution"])
    d["spikes"] = {int(k): v for k, v in d.get("spikes", {}).items()}
    return d


# ------------------------------------------------------------------ tune
def tune(d: pd.DataFrame) -> dict:
    keep, drop_tab = mm.select(d, TUNE)
    print(drop_tab.to_string())
    shape, keys, dtab = bt.choose_distribution(d, keep, TUNE)
    print(dtab.to_string())
    tr = d[d.season.isin(TUNE)]
    model = mm.fit(tr, keep)
    dparams = bt.fit_dist(tr, model, shape, keys)
    params = {
        "groups": keep,
        "coef": model["coef"],
        "n_fit": model["n"],
        "distribution": {k: v for k, v in dparams.items()
                         if not (not shape.startswith("kde") and k.startswith("kde"))},
        "ratings_hfa": mm.ratings_hfa(),
        "lines": {"history": ["Bovada", "DraftKings"], "live": ["DraftKings", "Bovada"],
                  "bet_time_line": "open (live: current line)"},
        "feature_constants": {
            "st_prior_factor": features.ST_PRIOR_FACTOR, "fp_lambda": features.FP_LAMBDA,
            "fg_n0": features.FG_N0, "qb_min_starts": features.QB_MIN_STARTS,
            "qb_n0_backup": features.QB_N0_BACKUP, "qb_n0_starter": features.QB_N0_STARTER,
            "rest_cap": features.REST_CAP, "bye_days": features.BYE_DAYS},
        "tuned_on": TUNE,
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    PARAMS.write_text(json.dumps(params, indent=2) + "\n")
    drop_tab.to_csv(features.DERIVED / "model_drop_one.csv", index=False)
    dtab.to_csv(features.DERIVED / "model_dist_choice.csv", index=False)
    print(f"-> {PARAMS}")
    return params


# ------------------------------------------------------------------ report helpers
def md(df: pd.DataFrame, fmt="{:.2f}") -> str:
    if df is None or df.empty:
        return "_(none)_\n"
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in df.itertuples(index=False))


def write_block(name: str, text: str) -> None:
    doc = REPORT.read_text(encoding="utf-8") if REPORT.exists() else "# CFB Phase 3 Report\n"
    b, e = f"<!-- AUTO:{name}:BEGIN -->", f"<!-- AUTO:{name}:END -->"
    blk = f"{b}\n{text}\n{e}"
    doc = (doc[:doc.index(b)] + blk + doc[doc.index(e) + len(e):]) if b in doc and e in doc \
        else doc + f"\n{blk}\n"
    REPORT.write_text(doc, encoding="utf-8")


def calibration_section(r: pd.DataFrame, title: str) -> list[str]:
    out = [f"\n**{title}**\n"]
    rows = []
    for kind, x in [("all", r)] + list(r.groupby("kind")):
        rows.append({"rungs": kind, **bt.scores(x), **{f"75-90 {k}": v for k, v in bt.band(x).items()}})
    out.append(md(pd.DataFrame(rows), "{:.4g}"))
    for kind, x in r.groupby("kind"):
        out += [f"\nReliability, {kind}:\n", md(bt.reliability(x), "{:.1f}")]
    return out


def headline(g: pd.DataFrame, r: pd.DataFrame, label: str) -> list[str]:
    c = bt.clv(g, label)
    out = [f"**CLV, {label}** (corr(proj - open, close - open) = {c.attrs['corr']:+.3f})\n", md(c, "{:.1f}")]
    rows = [{"rungs": kind, **bt.band(x)} for kind, x in [("all", r)] + list(r.groupby("kind"))]
    out += [f"\n**Calibration, 75-90% band, {label}** (game-bootstrap CI on actual - predicted)\n",
            md(pd.DataFrame(rows), "{:.1f}")]
    return out


def fair_ladders(g: pd.DataFrame, P: np.ndarray, season=2024, n=10, seed=11) -> list[str]:
    gs = g.reset_index(drop=True)
    pick = gs[gs.season == season].sample(n, random_state=seed).index
    out = []
    for i in pick:
        row = gs.loc[i]
        fav_home = row.proj >= 0
        side = "home" if fav_home else "away"
        team = row.home_team if fav_home else row.away_team
        lad = dist.ladder(P[i])
        lad = lad[(lad.side == side) & lad.rung.between(-28, 10) & lad.cover.between(0.03, 0.985)]
        lad = lad[(lad.rung * 2) % 2 == 1]        # x.5 rungs (no pushes)
        out += [f"\n**{row.away_team} @ {row.home_team}** ({row.season} wk {row.week}): open "
                f"{row.spread_open:+.1f} ({row.provider}), projected home margin {row.proj:+.1f}, "
                f"sigma {row.sigma:.1f}, final {int(row.margin_home):+d}. Ladder for **{team}**:\n",
                md(lad.assign(rung=lad.rung.map(lambda v: f"{v:+.1f}"), cover_pct=100 * lad.cover,
                              fair_odds=lad.fair_american.map(lambda v: f"{v:+.0f}"))
                   [["rung", "cover_pct", "fair_odds"]], "{:.1f}")]
    return out


def iowa(d: pd.DataFrame) -> pd.DataFrame:
    st = features.st_ratings(*_st_inputs())
    games = pd.read_parquet(config.CLEAN / "games.parquet")
    iowa_id = int(games.loc[games.home_team == "Iowa", "home_id"].iloc[0])
    rows = []
    for s in (2024, 2025, LIVE):
        x = st[(st.season == s)]
        w = x.week_asof.max()
        x = x[x.week_asof == w].copy()
        fbs = x.team_id.isin(games[(games.season == s) & (games.home_classification == "fbs")].home_id)
        x = x[fbs]
        x["fp_rank"] = x.st_fp.rank(ascending=False)
        x["fg_rank"] = x.st_fg.rank(ascending=False)
        i = x[x.team_id == iowa_id].iloc[0]
        rows.append({"season": s, "as_of_week": int(w), "teams": len(x),
                     "net_start_fp_yds": i.st_fp, "fp_rank": int(i.fp_rank),
                     "fg_poe_per_game": i.st_fg, "fg_rank": int(i.fg_rank)})
    return pd.DataFrame(rows)


def _st_inputs():
    games, plays = features.load_inputs()
    return games, features.drive_starts(plays), features.fg_attempts(plays), features.slots(games)


# ------------------------------------------------------------------ report
def report(d: pd.DataFrame, params: dict, holdout: bool) -> None:
    groups, dp = params["groups"], dist_params(params)
    model = {"groups": groups, "coef": params["coef"]}
    P_ = [f"_Generated by `python -m engine.cfb.model.run` at {datetime.now():%Y-%m-%d %H:%M}._\n"]

    # LOSO tuning frames (model + distribution refit without the test season)
    g, P = bt.loso_frames(d, groups, TUNE, dp["shape"], list(dp.get("spikes", {})))
    r = bt.rung_pairs(g, P)
    boot = mm.bootstrap(d[d.season.isin(TUNE)], groups, n=1000)
    kb = boot[boot.term.str.startswith("k_")].assign(term=lambda x: x.term.str.replace("k_", "weeks "))

    P_ += ["## 1. k by week bucket (2022-2024 fit; game bootstrap 95% CI)\n",
           "k = weight on (ratings margin - open). 0 = the ratings add nothing beyond the opener.\n",
           md(kb.rename(columns={"term": "bucket", "coef": "k"}), "{:+.3f}"),
           "\n## 2. CLV (LOSO out of sample, 2022-2024)\n"]
    P_ += headline(g, r, "2022-2024 LOSO")

    live = d[(d.season == LIVE) & d.margin_home.notna()]
    gl, Pl = bt.project(live, model, dp)
    rl = bt.rung_pairs(gl, Pl)
    P_ += ["\n**2026 to date (informational; frozen params; DK open/close)**\n"]
    P_ += headline(gl, rl, "2026 to date")

    # robustness: the QB feature uses the game's actual starter (news may post-date the open)
    g0, _ = bt.loso_frames(d, [], TUNE, dp["shape"], list(dp.get("spikes", {})))
    c0 = bt.clv(g0, "k only, 2022-2024 LOSO")
    P_ += ["\n**Robustness: ratings gap only (no QB feature).** The QB feature assumes the "
           "starter is known at the open; these rows remove it.\n",
           f"corr(proj - open, close - open) = {c0.attrs['corr']:+.3f}\n", md(c0, "{:.1f}"),
           md(bt.ats(g0, "k only, 2022-2024 LOSO", "open"), "{:.1f}")]

    P_ += ["\n## 3. Calibration, all rungs (LOSO, 2022-2024)\n"]
    P_ += calibration_section(r, "2022-2024 LOSO")
    lay = r[(r.kind == "fav (laying)") & (r.p >= 0.75) & (r.p < 0.90)].merge(
        g[["game_id", "season", "proj", "open_margin"]], on="game_id")
    lay["model_vs_open_toward_team"] = np.where(lay.side == "home", 1, -1) * (lay.proj - lay.open_margin)
    lay["direction"] = pd.cut(lay.model_vs_open_toward_team, [-99, -1.5, 0, 1.5, 99],
                              labels=["model <= -1.5", "-1.5 to 0", "0 to +1.5", "model >= +1.5"])

    def gap(x):
        return pd.Series({"pairs": len(x), "games": x.game_id.nunique(),
                          "pred_pct": 100 * x.p.mean(), "actual_pct": 100 * x.y.mean(),
                          "gap_pts": 100 * (x.y.mean() - x.p.mean())})
    P_ += ["\n**Diagnostic: laying rungs, 75-90% band, by season and by model-vs-open direction "
           "(how much more the model likes the laying team than the opener does)**\n",
           md(lay.groupby("season").apply(gap).reset_index(), "{:.1f}"),
           md(lay.groupby("direction", observed=True).apply(gap).reset_index(), "{:.1f}")]

    P_ += ["\n## Feature selection: drop-one (LOSO MAE, 2022-2024)\n",
           "A group is kept if dropping it raises LOSO MAE and its coefficient signs make sense.\n",
           md(pd.read_csv(features.DERIVED / "model_drop_one.csv"), "{:.4f}")]
    allb = mm.bootstrap(d[d.season.isin(TUNE)], list(mm.GROUPS), n=1000)
    P_ += ["\n## Coefficients\n", f"Frozen model (groups: {groups or 'k only'}):\n", md(boot, "{:+.3f}"),
           "\nFor reference, all candidate features (not used):\n", md(allb, "{:+.3f}")]

    e = g.dropna(subset=["margin_home"])
    P_ += ["\n## Distribution\n",
           md(pd.read_csv(features.DERIVED / "model_dist_choice.csv"), "{:.4f}"),
           f"\nChosen: **{dp['shape']}**, sigma = {dp['a']:.2f} + {dp['b']:.4f}·|line| + "
           f"{dp['c']:.4f}·total" + (f", df {dp['df']:.1f}" if "df" in dp else "")
           + f"; spikes {dp.get('spikes') or 'none'}.\n",
           "\nKey numbers, LOSO 2022-2024 (observed vs implied by the chosen distribution):\n",
           md(dist.key_number_table(e.margin_home, P, 21), "{:.2f}")]

    P_ += ["\n## Margin accuracy (LOSO 2022-2024; same games in every column)\n",
           md(bt.accuracy(g)), "\nBy season:\n", md(bt.accuracy(g, "season")),
           "\nBy bucket:\n", md(bt.accuracy(g, "bucket")),
           "\n2026 to date:\n", md(bt.accuracy(gl, "bucket"))]

    P_ += ["\n## ATS (diagnostic; -110 pricing)\n",
           md(pd.concat([bt.ats(g, "2022-2024 LOSO", "open"), bt.ats(g, "2022-2024 LOSO", "close"),
                         bt.ats(gl, "2026", "open"), bt.ats(gl, "2026", "close")]), "{:.1f}")]

    P_ += ["\n## Fair-ladder samples (10 random 2024 games, LOSO; favorite side, x.5 rungs)\n"]
    P_ += fair_ladders(g, P)

    P_ += ["\n## Iowa check (special-teams ratings, end of season / as of now)\n",
           md(iowa(d), "{:+.2f}")]
    write_block("TUNING", "\n".join(P_))

    if holdout:
        h = d[(d.season == HOLDOUT) & d.margin_home.notna()]
        gh, Ph = bt.project(h, model, dp)
        rh = bt.rung_pairs(gh, Ph)
        sha = hashlib.sha256(PARAMS.read_bytes()).hexdigest()
        H = [f"_2025 held-out evaluation, run once at {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, "
             f"params.json sha256 {sha[:12]}._\n"]
        H += headline(gh, rh, "2025 holdout")
        H += ["\n**Margin accuracy, 2025**\n", md(bt.accuracy(gh)), md(bt.accuracy(gh, "bucket"))]
        H += calibration_section(rh, "2025 holdout")
        H += ["\n**ATS, 2025**\n", md(pd.concat([bt.ats(gh, "2025", "open"),
                                                 bt.ats(gh, "2025", "close")]), "{:.1f}")]
        write_block("HOLDOUT", "\n".join(H))
        c = bt.clv(gh, "2025")
        HOLDOUT_LOG.write_text(json.dumps({
            "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "params_sha256": sha, "games": len(gh),
            "clv_corr": c.attrs["corr"],
            "band_75_90": bt.band(rh),
            **{k: float(v) for k, v in bt.accuracy(gh).iloc[0].items()}}, indent=2, default=str) + "\n")
    print(f"report -> {REPORT.relative_to(config.ROOT)}")


def params_committed() -> bool:
    rel = PARAMS.relative_to(config.ROOT).as_posix()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=config.ROOT,
                             capture_output=True).returncode == 0
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=config.ROOT).returncode == 0
    return tracked and clean


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--holdout", action="store_true")
    a = ap.parse_args(argv)
    d = data()
    if a.tune:
        tune(d)
        return 0
    if not PARAMS.exists():
        print("no params.json; run --tune first")
        return 1
    if a.holdout:
        if not params_committed():
            print("refusing: commit engine/cfb/model/params.json (unchanged) before the holdout run")
            return 2
        if HOLDOUT_LOG.exists():
            print(f"refusing: 2025 model holdout already evaluated ({HOLDOUT_LOG.name})")
            return 2
    report(d, load_params(), a.holdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
