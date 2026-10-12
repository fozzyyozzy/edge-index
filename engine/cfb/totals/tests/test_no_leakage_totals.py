"""Leakage tests for the Phase 5B totals features.

    python -m pytest engine/cfb/totals/tests -q

Everything at or after an as-of cutoff is scrambled: team-game points, drives, plays,
seconds per play, explosiveness, and game scores. Every totals feature for games whose
week slot is at or before that cutoff must be bit-identical.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.cfb import config
from engine.cfb.model import features as mfeat
from engine.cfb.totals import features as tf, team_games

pytestmark = pytest.mark.skipif(not (mfeat.DERIVED / "ratings_asof.parquet").exists(),
                                reason="ratings not built")
SEASON, WEEK = 2023, 6
COLS = ["T_pts", "T_ppd", "T_epa", "tempo_clash", "expl_match", "E_plays_sum"]


def test_totals_features_unchanged_when_future_scrambled():
    games = pd.read_parquet(config.CLEAN / "games.parquet")
    tg = team_games.load()
    mg = mfeat.load()
    ratings = pd.read_parquet(mfeat.DERIVED / "ratings_asof.parquet")
    sl = mfeat.slots(games)
    cut = sl[(sl.season == SEASON) & (sl.week_asof == WEEK)].cutoff.iloc[0]

    a = tf.build(write=False, games=games, tg=tg, mg=mg, ratings=ratings)
    rng = np.random.default_rng(0)
    tg2 = tg.copy()
    late = (tg2.kickoff_utc >= cut).to_numpy()
    for c in ("pts", "drives", "ppd", "plays", "spp", "xpl"):
        tg2.loc[late, c] = rng.normal(50, 20, late.sum())
    g2 = games.copy()
    lg = g2.kickoff_utc >= cut
    g2.loc[lg, ["home_points", "away_points"]] = [99, 0]
    b = tf.build(write=False, games=g2, tg=tg2, mg=mg, ratings=ratings)

    a, b = (x.sort_values("game_id").reset_index(drop=True) for x in (a, b))
    early = ((a.season < SEASON) | ((a.season == SEASON) & (a.week_asof <= WEEK))).to_numpy()
    assert early.sum() > 1500
    pd.testing.assert_frame_equal(a.loc[early, COLS].reset_index(drop=True),
                                  b.loc[early, COLS].reset_index(drop=True), check_exact=True)
    later = (a.season == SEASON) & (a.week_asof > WEEK + 1)
    assert not np.allclose(a.loc[later, "T_pts"], b.loc[later, "T_pts"], equal_nan=True)
