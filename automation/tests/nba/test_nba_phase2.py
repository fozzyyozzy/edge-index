"""Phase 2 machinery: the holdout guard, the calibration-slope fit, the naive baseline, the blend rule inputs."""
import numpy as np
import pandas as pd
import pytest
import nba_paths  # noqa: F401  (repo root on sys.path)
from engine.nba import model as M
from engine.nba import phase2 as P


def test_dev_code_refuses_holdout_rows():
    pg = pd.DataFrame({"season": ["2024-25", "2025-26"]})
    with pytest.raises(RuntimeError):
        M.guard(pg, holdout=False)
    M.guard(pg, holdout=True)                               # only the registered run may pass holdout=True


def test_logistic_slope_recovers_known_slope():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.5, 0.97, 200_000)
    logit = np.log(p / (1 - p))
    for b in (1.0, 0.8):
        y = rng.uniform(size=p.size) < 1 / (1 + np.exp(-(b * logit)))
        assert P.logistic_slope(p, y.astype(float))[1] == pytest.approx(b, abs=0.03)


def test_naive_rate_uses_only_prior_games():
    d = pd.date_range("2025-01-01", periods=12, freq="2D").strftime("%Y-%m-%d")
    pg = pd.DataFrame({"game_id": [str(i) for i in range(12)], "espn_id": "p", "season": "2024-25", "date": d,
                       "played": True, "pts": [10] * 11 + [99]})
    e = pg.iloc[[10, 11]].reset_index(drop=True)
    r = P.naive_rates(e, pg, "pts", 12).reshape(2, 12)
    assert r[0, 9] == 1.0 and r[0, 10] == 0.0              # 10 prior games of 10 pts: 10+ always, 11+ never
    assert r[1, 10] == 0.0                                  # game 12's own 99 points never count for itself


def test_implied_probability():
    assert P.implied([-200])[0] == pytest.approx(2 / 3)
    assert P.implied([150])[0] == pytest.approx(0.4)


def test_sf_families_are_valid_probabilities():
    mu = np.array([[0.5], [5.0], [25.0]])
    k = np.arange(1, 40)[None, :]
    for fam, par in (("poisson", {}), ("nbinom", {"theta": 5.0}), ("dnorm", {"a": 3.0, "b": 0.01}), ("dgamma", {"a": 3.0, "b": 0.01})):
        p = M.sf(fam, par, mu, k)
        assert ((p >= 0) & (p <= 1)).all() and (np.diff(p, axis=1) <= 1e-12).all()   # P(Y>=k) falls with k
