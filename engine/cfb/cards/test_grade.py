"""Card-leg grading rules.  python -m pytest engine/cfb/cards -q"""
import pandas as pd

from engine.cfb.cards.grade import outcome

G = pd.Series({"home_points": 24.0, "away_points": 17.0, "completed": True})   # home by 7
GAME = "Away U @ Home U"


def leg(**k):
    return {"game": GAME, **k}


def test_spreads_and_push():
    assert outcome(leg(market="SPREAD-CLV", side="away", line=7.5, pick="Away U +7.5"), G) == 1.0
    assert outcome(leg(market="ALT-SHAPE", side="away", line=7.0, pick="Away U +7"), G) is None   # push
    assert outcome(leg(market="ALT-SHAPE", side="home", line=-7.5, pick="Home U -7.5"), G) == 0.0


def test_ml_totals_team_totals():
    assert outcome(leg(market="ML-SHADED", side="home", line=None, pick="Home U ML"), G) == 1.0
    assert outcome(leg(market="PAPER-UNPROVEN", side="Under", line=41.5, pick="Under 41.5 (game)"), G) == 1.0
    assert outcome(leg(market="TEAM-TOTAL", side="Over", line=20.5, pick="Home U Over 20.5"), G) == 1.0
    assert outcome(leg(market="TEAM-TOTAL", side="Over", line=20.5, pick="Away U Over 20.5"), G) == 0.0


def test_ungraded_when_not_final():
    g = pd.Series({"home_points": None, "away_points": None, "completed": False})
    assert outcome(leg(market="ML-SHADED", side="home", line=None, pick="Home U ML"), g) is None
