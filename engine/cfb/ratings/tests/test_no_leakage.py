"""Leakage tests (Phase 2 brief §0, §11).

    python -m pytest engine/cfb/ratings/tests -q

A rating as of (season, week w) must not change when anything at or after
w's cutoff changes: play EPA/success, game results, or later seasons.
Runs on the real cached data (no API calls).
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd
import pytest

from engine.cfb import config
from engine.cfb.ratings import adjust, prior as prior_mod, run

pytestmark = pytest.mark.skipif(not (config.CLEAN / "games.parquet").exists(),
                                reason="clean tables not built")
SEASON, WEEK = 2022, 6


@pytest.fixture(scope="module")
def data():
    return run.Data()


def params():
    p = run.load_params()
    p["to_points"] = p.get("to_points")
    return p


def cutoff_of(d, season, week):
    s = d.ctx[season].slots
    return s.loc[s.week_asof == week, "cutoff"].iloc[0]


def perturb(d: run.Data, cutoff) -> run.Data:
    """Copy of d with every play/result at or after cutoff scrambled."""
    rng = np.random.default_rng(0)
    p = run.Data.__new__(run.Data)
    p.__dict__.update(d.__dict__)
    p._mp_by_g = {}
    mp = d.mp.copy()
    late = mp.kickoff_utc >= cutoff
    mp.loc[late, "epa"] = rng.normal(5, 3, late.sum())
    mp.loc[late, "success"] = 1.0 - mp.loc[late, "success"]
    mp.loc[late, "abs_margin_pre"] = 0.0
    p.mp = mp
    g = d.games.copy()
    lateg = g.kickoff_utc >= cutoff
    g.loc[lateg, "home_points"] = g.loc[lateg, "away_points"] + 50
    g.loc[lateg, "margin_home"] = 50
    p.games = g
    return p


def test_fit_asof_never_reads_plays_after_cutoff(data):
    """Plays at/after the cutoff carry NaN: any read would poison the fit."""
    cut = cutoff_of(data, SEASON, WEEK)
    mp = data.plays(params()["garbage"])[SEASON].copy()
    mp.loc[mp.kickoff_utc >= cut, ["epa", "success"]] = np.nan
    ctx = data.ctx[SEASON]
    r = adjust.fit_asof(mp, ctx, cut, prior_mod.zero_prior(ctx.teams, None), params())
    rating_cols = [c for c in r.columns if c[:2] in ("o_", "d_")]
    assert r[rating_cols].notna().all().all()


def test_ratings_unchanged_when_future_perturbed(data):
    cut = cutoff_of(data, SEASON, WEEK)
    p = params()
    base = run.build(data, p, [SEASON])["ratings"]
    pert = run.build(perturb(data, cut), p, [SEASON])["ratings"]
    cols = [c for c in base.columns if c[:2] in ("o_", "d_") or c.startswith("net_")]
    for df in (base, pert):
        df.sort_values(["season", "week_asof", "team_id"], inplace=True)
    early_b = base[(base.season < SEASON) | (base.week_asof <= WEEK)].reset_index(drop=True)
    early_p = pert[(pert.season < SEASON) | (pert.week_asof <= WEEK)].reset_index(drop=True)
    assert len(early_b) and len(early_b) == len(early_p)
    pd.testing.assert_frame_equal(early_b[cols], early_p[cols], check_exact=True)
    # sanity: the perturbation is real -- later weeks do move
    late_b = base[(base.season == SEASON) & (base.week_asof > WEEK)][cols].to_numpy()
    late_p = pert[(pert.season == SEASON) & (pert.week_asof > WEEK)][cols].to_numpy()
    assert not np.allclose(late_b, late_p)


def test_prior_uses_only_earlier_seasons(data):
    """Season s prior is identical when all of season s (and later) is scrambled."""
    first_kick = data.ctx[SEASON].slots.cutoff.min()
    p = params()
    a = run.build(data, p, [SEASON])
    b = run.build(perturb(data, first_kick), p, [SEASON])
    pa = a["priors"][a["priors"].season == SEASON].sort_values("team_id").reset_index(drop=True)
    pb = b["priors"][b["priors"].season == SEASON].sort_values("team_id").reset_index(drop=True)
    cols = [c for c in pa.columns if c[:2] in ("o_", "d_")]
    pd.testing.assert_frame_equal(pa[cols], pb[cols], check_exact=True)


def test_asof_slate_cutoff(data):
    """The live entry point (run.py --as-of) reads nothing at/after its cutoff."""
    from engine.cfb.ratings import evaluate
    p = run.load_params()
    if not p.get("to_points"):
        pytest.skip("params not frozen yet")
    cut = cutoff_of(data, SEASON, WEEK)
    a = evaluate.asof_slate(data, p, SEASON, WEEK)
    b = evaluate.asof_slate(perturb(data, cut), p, SEASON, WEEK)
    cols = [c for c in a.columns if c[:2] in ("o_", "d_") or c == "power_pts"]
    pd.testing.assert_frame_equal(a.sort_values("team_id")[cols].reset_index(drop=True),
                                  b.sort_values("team_id")[cols].reset_index(drop=True),
                                  check_exact=True)
