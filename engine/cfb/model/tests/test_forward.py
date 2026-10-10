"""Forward-test scoring rules (docs/cfb/FORWARD_TEST.md), on a tiny fixture log.

    python -m pytest engine/cfb/model/tests/test_forward.py -q
"""
from __future__ import annotations

import pandas as pd
import pytest

from engine.cfb.model import forward


def _proj(ts, gid, spread, proj, kick="2026-10-17T20:00:00+00:00", week=7):
    return {"capture_ts_utc": ts, "game_id": gid, "season": 2026, "week": week,
            "home_team": "H", "away_team": "A", "kickoff_utc": kick, "dk_spread": spread,
            "dk_total": 50.0, "provider": "DraftKings", "line_used": spread,
            "ratings_margin": proj, "qb_delta": 0.0, "qb_note": "",
            "proj_primary": proj, "proj_ratings_only": proj, "sigma": 15.0,
            "params_sha256": "x"}


def _close(ts, gid, spread, kick="2026-10-17T20:00:00+00:00"):
    return {"capture_ts_utc": ts, "season": 2026, "week": 7, "game_id": gid,
            "home_team": "H", "away_team": "A", "kickoff_utc": kick,
            "dk_spread": spread, "dk_total": 50.0, "providers": "DraftKings"}


@pytest.fixture
def logs(tmp_path):
    p = pd.DataFrame([
        _proj("2026-10-12T15:00:00+00:00", 1, -3.0, 6.0),     # bet: home -3, model home by 6 (edge +3)
        _proj("2026-10-14T15:00:00+00:00", 1, -5.0, 6.0),     # later capture: ignored
        _proj("2026-10-12T15:00:00+00:00", 2, -7.0, 3.0),     # edge -4 (model likes away)
        _proj("2026-10-12T15:00:00+00:00", 3, -1.0, 1.5),     # edge +0.5: not qualifying
        _proj("2026-10-18T15:00:00+00:00", 4, -3.0, 9.0),     # captured AFTER kickoff: never scored
        _proj("2026-09-20T15:00:00+00:00", 5, -3.0, 9.0, kick="2026-09-21T20:00:00+00:00", week=3),
    ])
    c = pd.DataFrame([
        _close("2026-10-17T15:00:00+00:00", 1, -4.5),          # moved toward model (+1.5)
        _close("2026-10-17T19:00:00+00:00", 1, -5.5),          # last pre-kickoff close: -5.5 (+2.5)
        _close("2026-10-17T21:00:00+00:00", 1, -9.0),          # after kickoff: ignored
        _close("2026-10-17T19:00:00+00:00", 2, -8.0),          # moved toward home = away from model (-1)
        _close("2026-10-17T19:00:00+00:00", 3, -1.0),
    ])
    p.to_csv(tmp_path / forward.PROJ_LOG, index=False)
    c.to_csv(tmp_path / forward.CLOSE_LOG, index=False)
    return tmp_path


def test_bet_time_is_first_pregame_capture_and_close_is_last_pregame(logs):
    g = forward.scored_games(logs).set_index("game_id")
    assert set(g.index) == {1, 2, 3}                 # game 4 post-kickoff, game 5 week < 4
    assert g.loc[1, "dk_spread"] == -3.0
    assert g.loc[1, "close_spread"] == -5.5


def test_clv_stats(logs):
    g = forward.scored_games(logs)
    s = forward.clv_stats(g, "proj_primary")
    assert s["games_edge"] == 2                      # games 1 and 2 have |edge| >= 1.5
    assert s["toward_share_pct"] == pytest.approx(50.0)
    assert s["avg_move_toward_model"] == pytest.approx((2.5 + -1.0) / 2)


def test_status_in_progress_below_150(logs):
    out = forward.score(logs, write_doc=False)
    assert out["status"].startswith("IN PROGRESS: 2/150")


def test_pregame_filter():
    df = pd.DataFrame({"kickoff_utc": ["2026-10-17T20:00:00+00:00", "2026-10-17T16:00:00+00:00"]})
    kept = forward.pregame(df, "2026-10-17T17:00:00+00:00")
    assert len(kept) == 1
