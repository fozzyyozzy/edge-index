"""ESPN box-score parsing, on a real cached summary: MEM @ POR, 2023-11-03, one overtime, DNPs listed."""
import gzip, json, os
import pandas as pd
from nba_paths import FIX
from engine.nba import espn

SUMM = json.loads(gzip.decompress(open(os.path.join(FIX, "espn_summary_401584095.json.gz"), "rb").read()))


def test_game_info():
    g = espn.game_info(SUMM)
    assert (g["home"], g["away"], g["home_score"], g["away_score"]) == ("POR", "MEM", 115, 113)
    assert g["n_ot"] == 1
    assert g["date"] == "2023-11-03"          # 02:00Z tip is the previous evening in ET
    assert g["season"] == "2023-24"


def test_player_rows():
    df = pd.DataFrame(espn.player_rows(SUMM))
    assert not df.duplicated(["game_id", "espn_id"]).any()
    assert df.groupby("team").pts.sum().to_dict() == {"MEM": 113, "POR": 115}
    assert df[df.played].groupby("team").starter.sum().to_dict() == {"MEM": 5, "POR": 5}
    mins = df.groupby("team").minutes.sum()
    assert ((mins - 265).abs() <= 3).all()   # 240 + 25 per OT; ESPN minutes are whole numbers
    bane = df[df.player == "Desmond Bane"].iloc[0]
    assert (bane.minutes, bane.pts, bane.reb, bane.ast, bane.fg3m, bane.fg3a) == (45, 33, 8, 7, 3, 9)
    assert bane.pra == 48 and bane.pr == 41 and bane.pa == 40 and bane.ra == 15
    assert (bane.stl, bane.blk) == (4, 3)                      # nba_api agrees: 4 stl, 3 blk
    dnp = df[~df.played]
    assert len(dnp) == 6 and (dnp[["minutes", "pts", "reb", "ast"]] == 0).all().all()
    assert dnp.dnp_reason.notna().all()


def test_season_label():
    assert espn.season_label(2024) == "2023-24" and espn.season_label(2027) == "2026-27"
