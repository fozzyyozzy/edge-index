"""Slot guard: 90-min grace, intended-slot tagging, manual recovery.  python -m pytest engine/cfb/lines -q"""
from datetime import datetime
from zoneinfo import ZoneInfo

from engine.cfb.lines import slots

ET = ZoneInfo("America/New_York")


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=ET)


def test_late_run_within_grace_gets_intended_slot(monkeypatch):
    monkeypatch.setattr(slots, "served", lambda: set())
    assert slots.which(at("2026-10-13 11:20"))[:2] == ("2026-10-13:tue10", 80)
    assert slots.which(at("2026-10-13 11:40")) is None          # beyond 90 min
    assert slots.which(at("2026-10-12 17:41")) is None          # Monday's 8-hour-late run


def test_served_slot_is_skipped(monkeypatch):
    monkeypatch.setattr(slots, "served", lambda: {"2026-10-13:tue10"})
    assert slots.which(at("2026-10-13 10:37")) is None


def test_manual_recovery_any_lag(monkeypatch):
    monkeypatch.setattr(slots, "served", lambda: set())
    tag, lag, args = slots.resolve("tue10", at("2026-10-13 14:00"))
    assert tag == "2026-10-13:tue10" and lag == 240 and "--label bet" in args


def test_close_slots_accept_late_runs(monkeypatch):
    monkeypatch.setattr(slots, "served", lambda: set())
    tag, lag, args = slots.which(at("2026-10-17 13:40"))          # Sat 11 AM close, 2 h 40 m late
    assert tag == "2026-10-17:sat11" and "--label close" in args
    assert slots.which(at("2026-10-14 15:30")) is not None and "wed10" not in slots.which(at("2026-10-14 15:30"))[0]


def test_named_slot_already_served_is_skipped(monkeypatch):
    monkeypatch.setattr(slots, "served", lambda: {"2026-10-20:tue10"})
    assert slots.resolve("tue10", at("2026-10-20 10:03")) is None
    assert slots.resolve("tue18", at("2026-10-20 18:03"))[0] == "2026-10-20:tue18"


def test_rung_log_uses_bet_time_ladder_once_per_week(tmp_path, monkeypatch):
    """Tim, 2026-10-25: a week is logged once, from its Tue 'bet' ladder before 18:00 ET only."""
    import pandas as pd
    from engine.cfb.lines import ladder_edge as le
    monkeypatch.setattr(le, "LINES", tmp_path)
    kick = "2026-10-24T19:00:00Z"
    def row(ts, label, week=8, gid=1):
        return {"captured_at_utc": ts, "label": label, "game_id": gid, "week": week, "commence_time": kick,
                "home_team": "H", "away_team": "A", "side": "home", "team": "H", "kind": "getting",
                "rung": 3.5, "price": -200, "main_spread": -1.5, "proj": 3.0, "p_shape": 0.8, "p_full": 0.8,
                "p_dk": 0.7, "shape_edge_pp": 10.0, "full_edge_pp": 10.0, "ev_shape": 0.2, "ev_full": 0.2}
    e = pd.DataFrame([row("2026-10-19T19:00:00Z", "open_watch"),       # Monday: before the Tuesday
                      row("2026-10-20T17:03:26Z", "bet"),              # Tue 13:03 ET: the bet ladder
                      row("2026-10-21T14:02:00Z", "bet"),              # Wednesday bet: later price
                      row("2026-10-22T22:02:00Z", "close")])
    n, _ = le.update_paper_log(e, 2026)
    log = pd.read_csv(tmp_path / "paper_rungs_2026.csv")
    assert n == 1 and list(log.captured_at_utc) == ["2026-10-20T17:03:26Z"]
    assert le.update_paper_log(e, 2026)[0] == 0                         # week already logged: never again
    late = pd.DataFrame([row("2026-10-28T14:00:00Z", "bet", week=9, gid=2) | {"commence_time": "2026-10-31T19:00:00Z"},
                         row("2026-10-29T22:00:00Z", "close", week=9, gid=2) | {"commence_time": "2026-10-31T19:00:00Z"}])
    le.update_paper_log(late, 2026)                                     # no Tue bet: first on/after Tue
    assert pd.read_csv(tmp_path / "paper_rungs_2026.csv").captured_at_utc.iloc[-1] == "2026-10-28T14:00:00Z"
