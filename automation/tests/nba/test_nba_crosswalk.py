"""Player ID crosswalk: name keys (suffixes, accents, punctuation), NBA.com id matching, Odds API names."""
import pandas as pd
import nba_paths  # noqa: F401  (repo root on sys.path)
from engine.nba import crosswalk as cw


def test_name_key_suffixes():
    assert cw.name_key("Jaren Jackson Jr.") == cw.name_key("Jaren Jackson") == "jaren jackson"
    assert cw.name_key("Gary Trent Jr") == cw.name_key("Gary Trent Jr.")
    assert cw.name_key("Robert Williams III") == "robert williams"
    assert cw.name_key("Otto Porter Jr.") == "otto porter"


def test_name_key_accents():
    assert cw.name_key("Nikola Jokić") == cw.name_key("Nikola Jokic")
    assert cw.name_key("Luka Dončić") == "luka doncic"
    assert cw.name_key("Jonas Valančiūnas") == "jonas valanciunas"
    assert cw.name_key("Dāvis Bertāns") == "davis bertans"


def test_name_key_punctuation_and_nicknames():
    assert cw.name_key("P.J. Washington") == cw.name_key("PJ Washington")
    assert cw.name_key("De'Aaron Fox") == cw.name_key("DeAaron Fox")
    assert cw.name_key("Shai Gilgeous-Alexander") == "shai gilgeous alexander"
    assert cw.name_key("Nicolas Claxton") == cw.name_key("Nic Claxton")
    assert cw.name_key("Herbert Jones") == cw.name_key("Herb Jones")
    assert cw.name_key("Moe Wagner") == cw.name_key("Moritz Wagner")


INDEX = pd.DataFrame([
    # espn_id, name, team: a traded player (index still has his old team) and two different Jalen Williamses
    ("4278073", "Kristaps Porziņģis", "BOS"),
    ("4593803", "Jalen Williams", "OKC"),
    ("4433143", "Jalen Williams", "DEN"),
    ("3934672", "Jaren Jackson Jr.", "MEM"),
], columns=["espn_id", "name", "team"]).assign(key=lambda d: d.name.map(cw.name_key))
NO_OV = pd.DataFrame(columns=["source", "name", "espn_id"])


def test_odds_name_suffix_and_accent():
    assert cw.match_odds_name("Jaren Jackson", ("MEM", "LAL"), INDEX, NO_OV) == "3934672"
    assert cw.match_odds_name("Kristaps Porzingis", ("BOS", "NYK"), INDEX, NO_OV) == "4278073"


def test_odds_name_traded_player_resolves_by_unique_name():
    # index lists him on BOS; tonight he plays for ATL
    assert cw.match_odds_name("Kristaps Porzingis", ("ATL", "ORL"), INDEX, NO_OV) == "4278073"


def test_odds_name_same_name_two_players():
    assert cw.match_odds_name("Jalen Williams", ("OKC", "SAS"), INDEX, NO_OV) == "4593803"
    assert cw.match_odds_name("Jalen Williams", ("DEN", "LAL"), INDEX, NO_OV) == "4433143"
    assert cw.match_odds_name("Jalen Williams", ("MIA", "BOS"), INDEX, NO_OV) is None   # ambiguous: no guess


def test_odds_name_override():
    ov = pd.DataFrame([{"source": "odds_api", "name": "JJJ", "espn_id": "3934672"}])
    assert cw.match_odds_name("JJJ", ("MEM", "LAL"), INDEX, ov) == "3934672"


def test_nba_ids_by_name_statline_and_trade():
    espn = pd.DataFrame([
        # a traded player: one id, two teams
        dict(game_id="1", date="2024-01-02", season="2023-24", espn_id="e1", player="Pascal Siakam", team="TOR",
             played=True, minutes=36, pts=20, reb=8, ast=5),
        dict(game_id="2", date="2024-01-20", season="2023-24", espn_id="e1", player="Pascal Siakam", team="IND",
             played=True, minutes=33, pts=21, reb=7, ast=4),
        # a name the sources spell differently: matched on the exact stat line within the team-game
        dict(game_id="3", date="2024-01-20", season="2023-24", espn_id="e2", player="Bub Carrington", team="WAS",
             played=True, minutes=28, pts=11, reb=4, ast=6),
    ])
    nba = pd.DataFrame([
        dict(PLAYER_ID=1627783, PLAYER_NAME="Pascal Siakam", TEAM_ABBREVIATION="TOR", GAME_DATE="2024-01-02",
             MIN=36, PTS=20, REB=8, AST=5),
        dict(PLAYER_ID=1627783, PLAYER_NAME="Pascal Siakam", TEAM_ABBREVIATION="IND", GAME_DATE="2024-01-20",
             MIN=33, PTS=21, REB=7, AST=4),
        dict(PLAYER_ID=1642267, PLAYER_NAME="Carlton Carrington", TEAM_ABBREVIATION="WAS", GAME_DATE="2024-01-20",
             MIN=28, PTS=11, REB=4, AST=6),
    ])
    m = cw.match_nba_ids(espn, nba).set_index("espn_id")
    assert m.loc["e1", "nba_id"] == 1627783 and m.loc["e1", "games"] == 2 and m.loc["e1", "method"] == "name"
    assert m.loc["e2", "nba_id"] == 1642267 and m.loc["e2", "method"] == "statline"
    assert not m.conflict.any()
    built = cw.build(espn, nba).set_index("espn_id")
    assert built.loc["e1", "teams"] == "TOR|IND" and built.loc["e1", "last_team"] == "IND"
