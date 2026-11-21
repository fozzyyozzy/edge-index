"""Free-tier credit cap (Tim, 2026-11-21).  python -m pytest engine/core -q"""
import pytest

from engine.core import odds_budget as ob


def test_cap_stops_before_overdrawing(monkeypatch):
    monkeypatch.setattr(ob, "cfg", lambda: {"monthly_cap": 450})
    ob.check(440, 60, 10, "t")                                # exactly reaches 450: allowed
    with pytest.raises(ob.BudgetStop):
        ob.check(441, 59, 10, "t")                            # would pass 450
    with pytest.raises(ob.BudgetStop):
        ob.check(None, None, 3, "t")                          # never call blind
    with pytest.raises(ob.BudgetStop):
        ob.check(10, 2, 3, "t")                               # remaining would go negative
    with pytest.raises(SystemExit):                           # a stop ends the run
        ob.check(449, 51, 3, "t")


def test_config_is_free_tier():
    c = ob.cfg()
    assert c["monthly_cap"] == 450 and c["nfl_auto_pulls"] is False and c["cfb_ladders"] is False
    assert set(c["cfb_slots"]) == {"tue10", "sat11", "sat15", "sat19"}
