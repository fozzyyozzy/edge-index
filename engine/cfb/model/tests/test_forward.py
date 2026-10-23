"""Forward-test scoring rules (docs/cfb/FORWARD_TEST.md), on a tiny fixture log.

    python -m pytest engine/cfb/model/tests/test_forward.py -q
"""
from __future__ import annotations

import numpy as np
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


def _snap_rows(ts, label, gid, spread, kick="2026-10-17T20:00:00+00:00"):
    return {"captured_at_utc": ts, "label": label, "event_id": "e", "game_id": gid, "week": 7,
            "commence_time": kick, "home_team": "H", "away_team": "A", "cfbd_home": "H",
            "market": "spreads", "team": "H", "is_home": 1, "point": spread, "price": -110}


def test_bet_snapshot_is_never_the_close(tmp_path, monkeypatch):
    """Week 7 bug: a later 'bet' recovery snapshot was graded as the close (zero moves).
    Only 'close'-labeled pregame snapshots count; otherwise CFBD's DK close (close_source=cfbd)."""
    import warnings
    from engine.cfb import config
    snap = tmp_path / "snapshots"; snap.mkdir()
    clean = tmp_path / "clean"; clean.mkdir()
    pd.DataFrame([
        _snap_rows("2026-10-13T14:32:23+00:00", "bet", 1, -3.0), _snap_rows("2026-10-13T14:36:58+00:00", "bet", 1, -3.0),
        _snap_rows("2026-10-13T14:32:23+00:00", "bet", 2, -7.0), _snap_rows("2026-10-17T15:10:00+00:00", "close", 2, -9.0),
    ]).to_csv(snap / "dk_main_2026_wk07.csv", index=False)
    pd.DataFrame({"game_id": [1, 2], "provider": ["DraftKings"] * 2, "spread": [-4.5, -8.0]}) \
        .to_parquet(clean / "lines.parquet", index=False)
    pd.DataFrame([_proj("2026-10-12T15:00:00+00:00", 1, -3.0, 6.0), _proj("2026-10-12T15:00:00+00:00", 2, -7.0, 9.0)]) \
        .to_csv(tmp_path / forward.PROJ_LOG, index=False)
    monkeypatch.setattr(forward, "SNAP", snap)
    monkeypatch.setattr(config, "CLEAN", clean)
    g = forward.dk_snapshot_games(tmp_path).set_index("game_id")
    assert g.loc[1, "close_source"] == "cfbd" and g.loc[1, "close_spread"] == -4.5     # not the 10:36 bet snapshot
    assert g.loc[2, "close_source"] == "dk_snapshot" and g.loc[2, "close_spread"] == -9.0
    with warnings.catch_warnings():
        warnings.simplefilter("error")                                                 # no zero-variance warnings
        assert np.isnan(forward.safe_corr([1, 2, 3], [0, 0, 0]))


def test_late_bet_rule(tmp_path, monkeypatch):
    """Tim, 2026-10-23: a 'bet' snapshot counts if taken the week's Tuesday before 18:00 ET (lag shown);
    later, the first snapshot on/after that Tuesday is the line, source bet_late."""
    from engine.cfb import config
    snap = tmp_path / "snapshots"; snap.mkdir()
    clean = tmp_path / "clean"; clean.mkdir()
    pd.DataFrame([
        _snap_rows("2026-10-12T21:00:00+00:00", "open_watch", 1, -2.0),   # Monday: before the Tuesday
        _snap_rows("2026-10-13T17:03:00+00:00", "bet", 1, -3.0),          # Tue 13:03 ET: counts, 183 min late
        _snap_rows("2026-10-13T22:02:00+00:00", "close", 2, -6.5),        # Tue 18:02 ET close: first on/after Tue
        _snap_rows("2026-10-14T14:02:00+00:00", "bet", 2, -7.0),          # Wed 10 AM bet: after Tue 18:00
        _snap_rows("2026-10-17T15:00:00+00:00", "close", 2, -9.0),
    ]).to_csv(snap / "dk_main_2026_wk07.csv", index=False)
    pd.DataFrame({"game_id": [1, 2], "provider": ["DraftKings"] * 2, "spread": [-4.5, -8.0]}) \
        .to_parquet(clean / "lines.parquet", index=False)
    pd.DataFrame([_proj("2026-10-12T15:00:00+00:00", 1, -3.0, 6.0), _proj("2026-10-12T15:00:00+00:00", 2, -7.0, 9.0)]) \
        .to_csv(tmp_path / forward.PROJ_LOG, index=False)
    monkeypatch.setattr(forward, "SNAP", snap)
    monkeypatch.setattr(config, "CLEAN", clean)
    g = forward.dk_snapshot_games(tmp_path).set_index("game_id")
    assert g.loc[1, "source"] == "dk_tue_bet" and g.loc[1, "dk_spread"] == -3.0
    assert round(g.loc[1, "bet_lag_min"]) == 183 and bool(g.loc[1, "late_bet"])
    assert g.loc[2, "source"] == "bet_late" and g.loc[2, "dk_spread"] == -6.5 and bool(g.loc[2, "late_bet"])
    assert g.loc[2, "close_spread"] == -9.0                       # the bet_late snapshot is never the close
