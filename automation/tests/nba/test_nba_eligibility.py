"""PREREG §2 eligibility uses only games strictly before the game date (no leakage)."""
import os
import pandas as pd
import pytest
from nba_paths import REPO
from engine.nba import eligibility as el


def log(minutes, season="2025-26", pid="p1", start="2025-10-22"):
    d = pd.date_range(start, periods=len(minutes), freq="2D").strftime("%Y-%m-%d")
    return pd.DataFrame({"espn_id": pid, "season": season, "date": d, "played": [m is not None for m in minutes],
                         "minutes": [m or 0 for m in minutes]})


def test_counts_only_prior_games():
    f = el.prior_form(log([30] * 10))
    assert f.prior_games.tolist() == list(range(10))
    assert f.trail_minutes.isna().iloc[0]                 # first game: nothing before it


def test_ninth_game_is_first_eligible():
    e = el.eligible(log([30] * 10))
    assert e.tolist() == [False] * 8 + [True, True]


def test_current_and_future_games_cannot_change_eligibility():
    base = log([25] * 8 + [25] + [25] * 5)
    changed = base.copy()
    changed.loc[8:, "minutes"] = 0                        # the scored game and everything after it
    a, b = el.prior_form(base), el.prior_form(changed)
    assert a.loc[8, ["prior_games", "trail_minutes"]].tolist() == b.loc[8, ["prior_games", "trail_minutes"]].tolist()
    assert el.eligible(base)[8] == el.eligible(changed)[8]


def test_trailing_ten_minutes_threshold():
    f = el.prior_form(log([10] * 5 + [30] * 10))
    assert f.loc[14, "trail_minutes"] == pytest.approx((10 * 1 + 30 * 9) / 10)   # last 10 before game 15
    assert el.eligible(log([19] * 12)).sum() == 0
    assert el.eligible(log([20] * 12)).sum() == 4


def test_dnp_games_are_not_counted():
    f = el.prior_form(log([30, None, 30, None, 30]))
    assert f.loc[4, "prior_games"] == 2


def test_season_resets():
    two = pd.concat([log([30] * 10, season="2024-25", start="2025-01-01"), log([30] * 3, season="2025-26")],
                    ignore_index=True)
    f = el.prior_form(two)
    assert f.loc[10:, "prior_games"].tolist() == [0, 1, 2]


def test_duplicate_date_row_never_leaks():
    df = log([30] * 9)
    df.loc[8, "date"] = df.loc[7, "date"]                 # malformed: two games on one date
    f = el.prior_form(df)
    assert f.loc[8, "prior_games"] == 7                   # the same-date game is not "before"


@pytest.mark.skipif(not os.path.exists(os.path.join(REPO, "data", "nba", "player_games.parquet")),
                    reason="NBA backfill not built")
def test_real_data_shift_matches_strict_before():
    pg = pd.read_parquet(os.path.join(REPO, "data", "nba", "player_games.parquet"))
    pg = pg[pg.season == "2024-25"]                       # training season only; never the holdout here
    f = el.prior_form(pg)
    p = f[f.played].sort_values(["espn_id", "date"])
    assert (p.groupby("espn_id").cumcount() == p.prior_games).all()
