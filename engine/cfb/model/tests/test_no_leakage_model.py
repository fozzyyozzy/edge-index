"""Leakage tests for the Phase 3 features (brief §0, §10).

    python -m pytest engine/cfb/model/tests -q

Everything at or after an as-of cutoff is scrambled: play EPA, field position
(yards to goal), field-goal results, and game scores. Features for every game
whose week slot is at or before that cutoff must be bit-identical.

Documented exception (brief §3): qb_change / qb_delta use THIS game's starter
(who threw the most passes), i.e. they assume injury news is known at bet time.
Passer names are therefore not scrambled; everything the QB terms compute
from (EPA, dropback history) before the cutoff is checked.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.cfb import config
from engine.cfb.model import features

pytestmark = pytest.mark.skipif(
    not (features.DERIVED / "ratings_asof.parquet").exists(), reason="ratings not built")
SEASON, WEEK = 2023, 6
FEATURE_COLS = ["power_home", "power_away", "st_fp_diff", "st_fg_diff", "qb_change_home",
                "qb_change_away", "qb_delta", "rest_diff", "bye_diff", "travel_k",
                "tz_diff", "w2e_diff", "open_margin", "total_bet"]


@pytest.fixture(scope="module")
def inputs():
    games, plays = features.load_inputs()
    ratings = pd.read_parquet(features.DERIVED / "ratings_asof.parquet")
    sl = features.slots(games)
    cut = sl[(sl.season == SEASON) & (sl.week_asof == WEEK)].cutoff.iloc[0]
    return games, plays, ratings, cut


def scramble(games, plays, cut):
    rng = np.random.default_rng(0)
    p = plays.copy()
    late = (p.kickoff_utc >= cut).to_numpy()
    p.loc[late, "ppa"] = rng.normal(3, 2, late.sum())
    ytg = p.loc[late, "yards_to_goal"].astype(float)
    p.loc[late, "yards_to_goal"] = (100 - ytg).clip(1, 99)
    fg = late & p.play_type.isin(["Field Goal Good", "Field Goal Missed"]).to_numpy()
    p.loc[fg, "play_type"] = p.loc[fg, "play_type"].map(
        {"Field Goal Good": "Field Goal Missed", "Field Goal Missed": "Field Goal Good"})
    g = games.copy()
    lg = g.kickoff_utc >= cut
    g.loc[lg, "home_points"] = 0
    g.loc[lg, "away_points"] = 70
    g.loc[lg, "margin_home"] = -70
    return g, p


def test_features_unchanged_when_future_scrambled(inputs):
    games, plays, ratings, cut = inputs
    a = features.build(write=False, games=games, plays=plays, ratings=ratings)
    g2, p2 = scramble(games, plays, cut)
    b = features.build(write=False, games=g2, plays=p2, ratings=ratings)
    a, b = (x.sort_values("game_id").reset_index(drop=True) for x in (a, b))
    early = ((a.season < SEASON) | ((a.season == SEASON) & (a.week_asof <= WEEK))).to_numpy()
    assert early.sum() > 1500
    pd.testing.assert_frame_equal(a.loc[early, FEATURE_COLS].reset_index(drop=True),
                                  b.loc[early, FEATURE_COLS].reset_index(drop=True),
                                  check_exact=True)
    # the scramble is real: later special-teams features move
    late = (a.season == SEASON) & (a.week_asof > WEEK + 1)
    assert not np.allclose(a.loc[late, "st_fp_diff"], b.loc[late, "st_fp_diff"])


def test_fg_make_model_uses_earlier_seasons_only(inputs):
    games, plays, _, _ = inputs
    fg = features.fg_attempts(plays)
    m1 = features.fg_make_models(fg)
    fg2 = fg.copy()
    fg2.loc[fg2.season >= SEASON, "made"] = 1 - fg2.loc[fg2.season >= SEASON, "made"]
    m2 = features.fg_make_models(fg2)
    X = np.column_stack([np.arange(20, 60), np.arange(20, 60) ** 2])
    assert np.array_equal(m1[SEASON].predict_proba(X), m2[SEASON].predict_proba(X))


def test_projection_uses_only_pregame_inputs():
    """projected margin = open + frozen coefficients x features; results never enter."""
    from engine.cfb.model import margin_model as mm, run
    if not run.PARAMS.exists():
        pytest.skip("params not frozen")
    p = run.load_params()
    d = mm.prep(features.load())
    d = d[d.season == SEASON].dropna(subset=["open_margin"]).head(50)
    m = {"groups": p["groups"], "coef": p["coef"]}
    a = mm.predict(d, m)
    b = mm.predict(d.assign(margin_home=999, close_margin=999), m)
    assert np.array_equal(a.to_numpy(), b.to_numpy())
