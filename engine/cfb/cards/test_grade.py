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


def test_tracks_end_to_end(tmp_path, monkeypatch):
    """Fake published card on a real completed game: edge list + ALT-SHAPE split grade correctly."""
    import json
    import numpy as np
    from engine.cfb import config
    from engine.cfb.cards import grade
    g = pd.read_parquet(config.CLEAN / "games.parquet")
    r = g[(g.season == 2026) & (g.completed == True) & g.both_fbs].iloc[0]  # noqa: E712
    margin = r.home_points - r.away_points
    home = f"{r.away_team} @ {r.home_team}"
    card = {"week": int(r.week), "snapshot_utc": "x", "floor_legs": [
        {"game_id": int(r.game_id), "game": home, "pick": "h", "market": "ALT-SHAPE", "role": "floor",
         "side": "home", "line": float(-margin + 0.5), "price": -300, "p_used": .8, "ev": .05,
         "dk_home_spread": -20.0}],
        "spread_edges": [{"game_id": int(r.game_id), "game": home, "pick": "a", "side": "away",
                          "line": float(margin - 0.5), "price": -110, "edge_pts": 2.0, "p_model": .56, "ev": .05}]}
    (tmp_path / "card_2026_wk99.json").write_text(json.dumps(card))
    monkeypatch.setattr(grade, "CARDS", tmp_path)
    fl = grade.legs(2026)
    assert fl.result.iloc[0] == 1.0                       # home +(-margin+0.5) covers by 0.5
    assert list(grade.alt_shape_split(fl)) == ["|spread| > 14"]
    ed = grade.edge_legs(2026)
    assert ed.result.iloc[0] == 0.0                       # away +(margin-0.5) loses by 0.5
    assert np.isclose(ed.units.iloc[0], -1.0)
