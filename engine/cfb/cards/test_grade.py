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


def test_edge_list_is_one_bet_per_game_on_models_side():
    """spread_edges keeps only the model's side: home/away edges are exact negatives."""
    from engine.cfb.cards.card import spread_edges
    base = {"game": "A @ H", "market": "SPREAD-CLV", "price": -110, "p_model": .55, "ev": .02}
    L = pd.DataFrame([
        {**base, "game_id": 1, "side": "home", "pick": "H -3", "line": -3.0, "proj_home_margin": 6.0, "dk_home_spread": -3.0},
        {**base, "game_id": 1, "side": "away", "pick": "A +3", "line": 3.0, "proj_home_margin": 6.0, "dk_home_spread": -3.0},
        {**base, "game_id": 2, "side": "home", "pick": "H2 -10", "line": -10.0, "proj_home_margin": 7.0, "dk_home_spread": -10.0},
        {**base, "game_id": 2, "side": "away", "pick": "A2 +10", "line": 10.0, "proj_home_margin": 7.0, "dk_home_spread": -10.0},
        {**base, "game_id": 3, "side": "home", "pick": "H3 -7", "line": -7.0, "proj_home_margin": 8.0, "dk_home_spread": -7.0},
        {**base, "game_id": 3, "side": "away", "pick": "A3 +7", "line": 7.0, "proj_home_margin": 8.0, "dk_home_spread": -7.0},
    ])
    e = spread_edges(None, L)
    assert e.game_id.is_unique
    picks = dict(zip(e.game_id, e.side))
    assert picks == {1: "home", 2: "away"}           # game 1: model +6 vs -3 -> home; game 2: +7 vs -10 -> away
    assert 3 not in picks                            # game 3: edge +1.0 < 1.5 -> no bet


def test_edge_grading_never_counts_both_sides(tmp_path, monkeypatch):
    """Even if a card listed both sides of a game, grading keeps one bet (largest edge)."""
    import json
    from engine.cfb import config
    from engine.cfb.cards import grade
    g = pd.read_parquet(config.CLEAN / "games.parquet")
    r = g[(g.season == 2026) & (g.completed == True) & g.both_fbs].iloc[0]  # noqa: E712
    name = f"{r.away_team} @ {r.home_team}"
    both = [{"game_id": int(r.game_id), "game": name, "pick": "h", "side": "home", "line": -3.0, "price": -110,
             "edge_pts": 2.5, "p_model": .56, "ev": .05},
            {"game_id": int(r.game_id), "game": name, "pick": "a", "side": "away", "line": 3.0, "price": -110,
             "edge_pts": 1.6, "p_model": .52, "ev": .01}]
    (tmp_path / "card_2026_wk98.json").write_text(json.dumps({"week": 98, "snapshot_utc": "x",
                                                               "floor_legs": [], "spread_edges": both}))
    monkeypatch.setattr(grade, "CARDS", tmp_path)
    ed = grade.edge_legs(2026)
    assert len(ed) == 1 and ed.pick.iloc[0] == "h"


def test_each_game_on_at_most_one_ticket():
    from engine.cfb.cards.card import tickets
    rows = []
    for gid in range(1, 9):
        for j, (mkt, p, price) in enumerate([("ALT-SHAPE", .80, -300), ("ML-SHADED", .70, -200)]):
            rows.append({"game_id": gid, "game": f"G{gid}", "pick": f"p{gid}{j}", "market": mkt,
                         "role": "floor" if j == 0 else "second", "price": price, "p_used": p - gid / 100})
    t = tickets(pd.DataFrame(rows))
    games = [leg["game_id"] for tk in t for leg in tk["legs"]]
    assert len(games) == len(set(games))                       # no game on two tickets
    assert all(tk["alt_shape_legs"] <= 2 for tk in t)
    for tk in t:
        assert (tk["price_american"] >= 200) == (tk["label"] == "Bloom (>= +200)")
