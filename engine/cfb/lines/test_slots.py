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


def test_manual_recovery_any_lag():
    tag, lag, args = slots.resolve("tue10", at("2026-10-13 14:00"))
    assert tag == "2026-10-13:tue10" and lag == 240 and "--label bet" in args
