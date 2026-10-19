"""Slip checker: boost math and grading on Tim's week-7 ML flier (games final)."""
import json
from pathlib import Path

import numpy as np
import pytest

from engine.cfb import config

FLIER = config.ROOT / "data" / "cfb" / "slips" / "2026_wk07_ml_flier.json"


@pytest.mark.skipif(not FLIER.exists(), reason="flier slip file missing")
def test_week7_flier():
    from engine.cfb.slips.check import check
    r = check(json.loads(FLIER.read_text()))
    s, L = r["summary"], r["legs"]
    assert s["legs"] == 10 and s["result"] == "LOSS" and (s["legs_won"], s["legs_lost"]) == (6, 4)
    dec = float(np.prod(L.decimal))
    assert np.isclose(s["p_joint_model"], np.prod(L.p_model))
    assert np.isclose(s["ev_model_boosted"], s["p_joint_model"] * (1 + (dec - 1) * 1.5) - 1)   # boost on profit
    assert set(L[L.result == 0].leg) == {"Texas ML", "Notre Dame ML", "Oklahoma ML", "Georgia ML"}
