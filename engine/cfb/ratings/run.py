"""Phase 2 ratings pipeline.

    python -m engine.cfb.ratings.run                      # build ratings 2021-2026, evaluate tuning seasons
    python -m engine.cfb.ratings.run --tune               # grid search on 2022-2024 -> params.json
    python -m engine.cfb.ratings.run --as-of 2026 7       # ratings for one upcoming slate
    python -m engine.cfb.ratings.run --holdout            # ONE-TIME 2025 evaluation (params.json must be committed)

Zero API calls: reads data/cfb/clean and data/cfb/derived only.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.pull import completed_weeks
from engine.cfb.ratings import adjust, plays_prep, prior as prior_mod, to_points
from engine.cfb.ratings.adjust import METRICS

HERE = Path(__file__).resolve().parent
PARAMS = HERE / "params.json"
DERIVED = plays_prep.DERIVED
TUNE_SEASONS = [2022, 2023, 2024]
HOLDOUT = 2025
FIRST = 2021
HOLDOUT_LOG = config.ROOT / "docs" / "cfb" / "holdout_2025.json"

DEFAULT_PARAMS = {
    "half_life_games": 4,
    "lambda": {m: 300 for m in METRICS},
    "garbage": dict(plays_prep.DEFAULT_GARBAGE),
    "prior_no_history_factor": 0.6,
    "to_points": None,
}


def load_params() -> dict:
    return json.loads(PARAMS.read_text()) if PARAMS.exists() else json.loads(json.dumps(DEFAULT_PARAMS))


# ------------------------------------------------------------------ data
class Data:
    def __init__(self):
        self.games = pd.read_parquet(config.CLEAN / "games.parquet")
        self.mp = plays_prep.load()
        self.feats = prior_mod.team_features()
        self.ctx = {s: adjust.season_ctx(self.games, s) for s in config.SEASONS}
        self._mp_by_g: dict = {}

    def plays(self, garbage: dict) -> dict:
        """model plays per season with is_garbage_time at these thresholds."""
        key = json.dumps(garbage, sort_keys=True)
        if key not in self._mp_by_g:
            mp = self.mp.copy()
            mp["is_garbage_time"] = plays_prep.garbage_flag(mp.period, mp.abs_margin_pre, garbage).values
            self._mp_by_g = {key: {s: d for s, d in mp.groupby("season")}}
        return self._mp_by_g[key]


def last_ratable_week(d: Data, season: int) -> int | None:
    """In-progress season: last completed week + 1 (the upcoming slate)."""
    if season < config.CURRENT_SEASON:
        return None
    raw = json.loads((config.RAW / "games" / f"{season}.json").read_text(encoding="utf-8"))
    done = [w for st, w in completed_weeks(raw) if st == "regular"]
    return (max(done) if done else 0) + 1


POOLED_FCS = -1


def fcs_pooled(d: Data, mp: dict, params: dict, season: int) -> dict:
    """FCS-wide O/D per rating from one season's FBS-vs-FCS play, relative to
    that season's FBS average.

    All FCS teams are pooled into one pseudo-team for this fit: individually
    each has ~1-2 FBS games and ridge would shrink its rating to ~0, biasing
    the mean. Whole-season fit, zero prior, no recency weighting.
    """
    p0 = {**params, "half_life_games": None}
    ctx = d.ctx[season]
    fcs_ids = set(ctx.teams.team_id[ctx.teams.is_fcs])
    plays = mp[season].copy()
    for c in ("offense_id", "defense_id"):
        plays[c] = plays[c].where(~plays[c].isin(fcs_ids), POOLED_FCS)
    teams = pd.concat([ctx.teams[~ctx.teams.is_fcs], pd.DataFrame(
        {"team_id": [POOLED_FCS], "team": ["FCS (pooled)"], "is_fcs": [True]})],
        ignore_index=True)
    pooled = adjust.SeasonCtx(season, teams, ctx.slots, ctx.team_games)
    f = adjust.fit_asof(plays, pooled, None, prior_mod.zero_prior(teams, None), p0)
    fbs = f[~f.is_fcs]
    row = f[f.team_id == POOLED_FCS].iloc[0]
    return {r: float(row[r] - fbs[r].mean()) for r in prior_mod.RATINGS}


def fcs_constants(d: Data, mp: dict, params: dict) -> dict:
    """FCS prior constant per season, from 2021-2022 (brief §4) but leak-free:
    a season only uses estimates from strictly earlier seasons, except the
    2021 burn-in, which has none and uses its own (2021 is never evaluated).
      2021, 2022 -> 2021 estimate;  2023+ -> mean of 2021 and 2022.
    """
    est = {s: fcs_pooled(d, mp, params, s) for s in (2021, 2022)}
    both = {r: (est[2021][r] + est[2022][r]) / 2 for r in prior_mod.RATINGS}
    return {s: (est[2021] if s <= 2022 else both) for s in config.SEASONS}


def build(d: Data, params: dict, seasons: list[int], last_week: int | None = None) -> dict:
    """Chain seasons from 2021 (priors need the previous final). Returns dict of frames."""
    mp = d.plays(params["garbage"])
    fcs_by = fcs_constants(d, mp, params)
    finals, targets, ratings, priors, infos = {}, {}, [], [], []
    for s in range(FIRST, max(seasons) + 1):
        ctx = d.ctx[s]
        fcs = fcs_by[s]
        if s == FIRST:
            pr = prior_mod.zero_prior(ctx.teams, fcs)
            prow = ctx.teams.assign(season=s, prior_source="burn_in_zero")
            for m in METRICS:
                prow[f"o_{m}"], prow[f"d_{m}"] = pr[m][0].reindex(ctx.teams.team_id).values, \
                    pr[m][1].reindex(ctx.teams.team_id).values
        else:
            pr, prow, info = prior_mod.build_prior(s, finals, targets, d.feats, fcs, params, ctx.teams)
            infos.append(info)
        priors.append(prow)
        lw = last_week if (last_week is not None and s == max(seasons)) else last_ratable_week(d, s)
        r = adjust.season_ratings(mp[s], ctx, pr, params, last_week=lw)
        ratings.append(r)
        if s < config.CURRENT_SEASON:
            post = ctx.slots.week_asof.max()
            targets[s] = r[r.week_asof == post]
            finals[s] = adjust.fit_asof(mp[s], ctx, None, pr, params)
    rt = to_points.add_nets(pd.concat(ratings, ignore_index=True))
    return {"ratings": rt, "priors": pd.concat(priors, ignore_index=True),
            "prior_info": infos, "fcs_const": fcs_by, "finals": finals, "targets": targets}


def eval_games(d: Data, seasons) -> tuple[pd.DataFrame, pd.Series]:
    g = d.games
    g = g[g.season.isin(seasons) & g.both_fbs & (g.completed == True)  # noqa: E712
          & ~(g.is_bowl & ~g.is_cfp) & g.margin_home.notna()]
    slot = pd.concat([adjust.slot_for_game(d.ctx[s], d.games) for s in seasons])
    return g, slot


def score(d: Data, out: dict, seasons, coef: dict | None = None):
    """Fit (or apply) to_points on these seasons' games. Returns (coef, game frame)."""
    g, slot = eval_games(d, seasons)
    gf = to_points.game_frame(g, out["ratings"], slot)
    if coef is None:
        best = None
        for spec in to_points.SPECS:
            c = to_points.fit(gf, spec)
            mae = np.abs(gf.margin_home - to_points.predict(gf, c)).mean()
            if best is None or mae < best[0]:
                best = (mae, c)
        coef = best[1]
    gf["pred_margin"] = to_points.predict(gf, coef)
    return coef, gf


# ------------------------------------------------------------------ tuning
def tune(d: Data) -> dict:
    results = []

    def run(p, label):
        t0 = time.time()
        out = build(d, p, TUNE_SEASONS)
        coef, gf = score(d, out, TUNE_SEASONS)
        mae = float(np.abs(gf.margin_home - gf.pred_margin).mean())
        results.append({"label": label, "H": p["half_life_games"], **{f"lam_{k}": v for k, v in p["lambda"].items()},
                        **{f"g_{k}": v for k, v in p["garbage"].items()}, "spec": coef["spec"],
                        "mae": round(mae, 4), "n": len(gf), "sec": round(time.time() - t0, 1)})
        print(f"  {label:<34} MAE {mae:.4f}  ({coef['spec']}, {time.time() - t0:.0f}s)", flush=True)
        return mae, coef

    base = load_params() if PARAMS.exists() else json.loads(json.dumps(DEFAULT_PARAMS))
    base["to_points"] = None
    print("stage A: half-life x shared lambda")
    best = None
    for H in (2, 4, 8, None):
        for lam in (30, 100, 300, 1000):
            p = json.loads(json.dumps(base))
            p["half_life_games"], p["lambda"] = H, {m: lam for m in METRICS}
            mae, coef = run(p, f"A H={H} lam={lam}")
            if best is None or mae < best[0]:
                best = (mae, p, coef)
    print("stage B: per-metric lambda (x1/3, x3)")
    for m in METRICS:
        for f in (1 / 3, 3):
            p = json.loads(json.dumps(best[1]))
            p["lambda"][m] = round(p["lambda"][m] * f)
            mae, coef = run(p, f"B {m} lam={p['lambda'][m]}")
            if mae < best[0]:
                best = (mae, p, coef)
    print("stage C: garbage thresholds +-1 per quarter")
    for q in ("q2", "q3", "q4"):
        for dlt in (-1, 1):
            p = json.loads(json.dumps(best[1]))
            p["garbage"][q] += dlt
            mae, coef = run(p, f"C {q}={p['garbage'][q]}")
            if mae < best[0]:
                best = (mae, p, coef)
    frozen = best[1]
    frozen["to_points"] = best[2]
    frozen["tuned_on"] = TUNE_SEASONS
    frozen["tuning_mae"] = round(best[0], 4)
    frozen["frozen_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    PARAMS.write_text(json.dumps(frozen, indent=2) + "\n")
    pd.DataFrame(results).to_csv(DERIVED / "tuning_grid.csv", index=False)
    print(f"best MAE {best[0]:.4f} -> {PARAMS}")
    return frozen


# ------------------------------------------------------------------ outputs
def finalize(d: Data, params: dict, seasons) -> dict:
    out = build(d, params, seasons)
    r = out["ratings"]
    r["power_pts"] = to_points.power_points(r, params["to_points"])
    keep = ["season", "week_asof", "cutoff", "team_id", "team", "is_fcs"] + \
           [f"{s}_{m}" for m in METRICS for s in ("o", "d")] + \
           [f"net_{m}" for m in METRICS] + ["power_pts", "n_plays_off", "n_plays_def"]
    out["ratings"] = r[keep]
    DERIVED.mkdir(parents=True, exist_ok=True)
    out["ratings"].to_parquet(DERIVED / "ratings_asof.parquet", index=False)
    out["priors"].to_parquet(DERIVED / "priors.parquet", index=False)
    (DERIVED / "prior_info.json").write_text(json.dumps(
        {"fcs_const": out["fcs_const"], "info": out["prior_info"]}, indent=1, default=str))
    return out


def params_committed() -> bool:
    rel = PARAMS.relative_to(config.ROOT).as_posix()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=config.ROOT,
                             capture_output=True).returncode == 0
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=config.ROOT).returncode == 0
    return tracked and clean


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seasons", default=f"{FIRST}-{config.CURRENT_SEASON}")
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--as-of", nargs=2, type=int, metavar=("SEASON", "WEEK"))
    ap.add_argument("--holdout", action="store_true",
                    help="evaluate 2025 (one time; params.json must be committed and unchanged)")
    a = ap.parse_args(argv)
    from engine.cfb.pull import parse_seasons
    seasons = parse_seasons(a.seasons)

    d = Data()
    if a.tune:
        tune(d)
        return 0
    params = load_params()
    if not params.get("to_points"):
        print("params.json has no frozen to_points; run --tune first")
        return 1

    if a.as_of:
        s, w = a.as_of
        from engine.cfb.ratings import evaluate
        r = evaluate.asof_slate(d, params, s, w)
        path = DERIVED / f"ratings_{s}_wk{w:02d}.parquet"
        r.to_parquet(path, index=False)
        print(r[~r.is_fcs].sort_values("power_pts", ascending=False)
              .head(25)[["team", "power_pts", "net_epa", "net_sr", "n_plays_off"]].to_string(index=False))
        print(f"-> {path}")
        return 0

    if a.holdout:
        if not params_committed():
            print("refusing: commit engine/cfb/ratings/params.json (unchanged) before the holdout run")
            return 2
        if HOLDOUT_LOG.exists():
            print(f"refusing: 2025 holdout already evaluated ({HOLDOUT_LOG.name}); it runs once")
            return 2

    out = finalize(d, params, seasons)
    from engine.cfb.ratings import evaluate
    evaluate.report(d, out, params, holdout=a.holdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
