"""Data gate for the committed ESPN backfill (data/nba/*.parquet): real box scores, complete seasons, sane minutes."""
import os
import pandas as pd
import pytest
from nba_paths import REPO

PG = os.path.join(REPO, "data", "nba", "player_games.parquet")
GAMES = os.path.join(REPO, "data", "nba", "games.parquet")
pytestmark = pytest.mark.skipif(not os.path.exists(PG), reason="NBA backfill not built")
DONE = ["2023-24", "2024-25", "2025-26"]          # complete regular seasons


@pytest.fixture(scope="module")
def pg():
    return pd.read_parquet(PG)


@pytest.fixture(scope="module")
def known():
    """team-games with a logged ESPN defect (data/nba/espn_issues.csv): a player row ESPN can't key"""
    issues = pd.read_csv(os.path.join(REPO, "data", "nba", "espn_issues.csv"), dtype={"game_id": str})
    assert issues.short_name.nunique() <= 3      # a known ESPN gap (one player in 2025-26), not a broken parser
    return set(zip(issues.game_id, issues.team))


@pytest.fixture(scope="module")
def games():
    return pd.read_parquet(GAMES)


def test_full_seasons(games):
    g = games[games.season.isin(DONE)]
    assert g.groupby("season").size().to_dict() == {s: 1230 for s in DONE}
    per_team = pd.concat([g.assign(t=g.home), g.assign(t=g.away)]).groupby(["season", "t"]).size()
    assert len(per_team) == 90 and (per_team == 82).all()


def test_no_duplicate_player_games(pg):
    assert not pg.duplicated(["game_id", "espn_id"]).any()


def test_points_match_final_score(pg, known):
    """box points sum to the final score, except logged ESPN-defect team-games"""
    t = pg.groupby(["game_id", "team"]).agg(pts=("pts", "sum"), score=("team_score", "first"))
    off = t[t.pts != t.score]
    assert set(off.index) <= known, off[~off.index.isin(known)].head()


def test_minutes_sum_per_team_game(pg, known):
    """240 per team-game + 25 per OT, within whole-minute rounding, except logged ESPN-defect team-games"""
    t = pg.groupby(["game_id", "team"]).agg(m=("minutes", "sum"), ot=("n_ot", "first"))
    off = (t.m - (240 + 25 * t.ot)).abs()
    off = off[~off.index.isin(known)]
    assert (off <= 3).mean() >= 0.995, off.describe()
    assert off.max() <= 5


def test_five_starters(pg):
    s = pg[pg.played].groupby(["game_id", "team"]).starter.sum()
    assert (s == 5).mean() >= 0.999


def test_stats_organic(pg):
    """rule 3 (verify data is organic): no synthetic patterns such as all-even values"""
    p = pg[pg.played & pg.season.isin(DONE)]
    for c in ("pts", "reb", "ast", "minutes"):
        assert 0.4 < (p[c] % 2 == 0).mean() < 0.65, c
    assert p.minutes.between(0, 65).all()


def test_pregame_lines(pg):
    """rule 1 (pregame only): every spread/total was snapped before its game tipped"""
    p = os.path.join(REPO, "data", "nba", "lines", "pregame_spreads_totals.parquet")
    if not os.path.exists(p):
        pytest.skip("historical lines not pulled")
    ln = pd.read_parquet(p)
    assert (pd.to_datetime(ln.snapshot, utc=True) < pd.to_datetime(ln.commence, utc=True)).all()
    assert not ln.game_id.duplicated().any()
    done = pg[pg.season.isin(DONE)]
    assert done.team_spread.notna().mean() > 0.99 and done.game_total.notna().mean() > 0.99
    one = done.drop_duplicates(["game_id", "team"]).groupby("game_id").team_spread.sum()
    assert (one == 0).all()                      # home and away spreads mirror each other


def test_combo_columns_equal_component_sums(pg):
    """the combo markets are derived, never sourced: P+R, P+A, R+A, PRA equal their parts on every row"""
    assert (pg.pr == pg.pts + pg.reb).all()
    assert (pg.pa == pg.pts + pg.ast).all()
    assert (pg.ra == pg.reb + pg.ast).all()
    assert (pg.pra == pg.pts + pg.reb + pg.ast).all()


def test_steals_blocks_present_and_sane(pg):
    p = pg[pg.played & pg.season.isin(DONE)]
    for c in ("stl", "blk"):
        assert p[c].notna().all() and p[c].between(0, 15).all(), c
        assert 0.3 < p[c].mean() < 1.5, c                 # league per-game averages, ~0.7 stl / ~0.5 blk
    t = pg.groupby(["game_id", "team"])[["stl", "blk"]].sum()
    assert t.stl.between(0, 25).all() and t.blk.between(0, 25).all()
