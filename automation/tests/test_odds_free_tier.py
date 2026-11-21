"""Free-tier Odds API mode (Tim, 2026-11-21): automatic NFL pulls are paused and every paid call is capped."""
import sys
import pytest
import fetch_lines
from engine.core import odds_budget


def test_paused_nfl_pull_exits_before_any_call(monkeypatch):
    monkeypatch.setenv("ODDS_API_KEY", "dummy")
    monkeypatch.delenv("NFL_ODDS_MANUAL", raising=False)
    monkeypatch.setattr(odds_budget, "cfg", lambda: {"nfl_auto_pulls": False, "monthly_cap": 450})
    monkeypatch.setattr(fetch_lines, "download", lambda *a, **k: pytest.fail("no Odds API call while paused"))
    monkeypatch.setattr(sys, "argv", ["fetch_lines.py", "--season", "2026", "--week", "12", "--slate", "sun"])
    with pytest.raises(SystemExit) as e:
        fetch_lines.main()
    assert e.value.code == 3


def test_paid_call_is_capped_before_it_is_made(monkeypatch):
    monkeypatch.setattr(odds_budget, "cfg", lambda: {"monthly_cap": 450})
    monkeypatch.setattr(fetch_lines, "download", lambda *a, **k: pytest.fail("capped call must not be made"))
    fetch_lines.LAST_H.clear(); fetch_lines.LAST_H.update(used="440", remaining="60")
    with pytest.raises(odds_budget.BudgetStop):
        fetch_lines.get("/events/x/odds", cost=14)
