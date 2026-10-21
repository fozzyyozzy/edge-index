"""Official NBA injury report parsing, on a real PDF (10/21/26 07:30 AM, 5 pages)."""
import os
from datetime import datetime
import pandas as pd
import pytest
from nba_paths import FIX
from engine.nba import injuries as inj

pytest.importorskip("pdfplumber")
DF = inj.parse_pdf(open(os.path.join(FIX, "Injury-Report_2026-10-21_07_30AM.pdf"), "rb").read())


def row(player):
    return DF[DF.player == player].iloc[0]


def test_shape_and_timestamp():
    assert len(DF) == 78
    assert (DF.report_time == datetime(2026, 10, 21, 7, 30)).all()
    assert set(DF.status) <= set(inj.STATUSES) | {inj.NYS}
    assert DF.apply(lambda r: r.team in r.matchup.split("@"), axis=1).all()


def test_names_flipped_and_teams_mapped():
    r = row("Mouhamed Gueye")
    assert (r.team, r.status, r.matchup, r.game_date) == ("ATL", "Out", "ATL@ORL", "10/21/2026")
    assert r.reason == "Injury/Illness - Left Foot Fracture"


def test_wrapped_reasons_join_the_right_player():
    # these reasons print on two lines straddling the player's row
    assert row("Jonathan Isaac").reason == "Injury/Illness - Left Knee Injury Management"
    assert row("Izaiyah Nelson").reason == "Injury/Illness - Left Ankle Injury Recovery"
    assert row("Noah Penda").reason == "Injury/Illness - Right Partially torn hamstring"


def test_two_way_reason_keeps_hyphen():
    assert row("RayJ Dennis").reason == "G League - Two-Way"


def test_not_yet_submitted_rows():
    nys = DF[DF.status == inj.NYS]
    assert len(nys) == 4 and nys.player.isna().all()
    assert set(nys.team) == {"CLE", "PHI", "DEN", "OKC"}


def test_player_name():
    assert inj.player_name("Jackson Jr., Jaren") == "Jaren Jackson Jr."
    assert inj.player_name("Dennis, RayJ") == "RayJ Dennis"


def test_report_time_from_url():
    u = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-20_05_00PM.pdf"
    assert inj.report_time_from_url(u) == datetime(2026, 10, 20, 17, 0)


def test_disagreements():
    official = pd.DataFrame({"team": ["ATL", "ATL", "ATL"], "player": ["Mouhamed Gueye", "Jalen Wilson", "Trae Young"],
                             "status": ["Out", "Questionable", "Available"]})
    espn = pd.DataFrame({"team": ["ATL", "ATL", "BOS"], "player": ["Mouhamed Gueye", "Jalen Wilson", "Jayson Tatum"],
                         "status": ["Out", "Out", "Out"]})
    d = inj.disagreements(official, espn)
    # Wilson: Questionable vs Out. Young: Available and absent from ESPN is not a disagreement. BOS isn't playing.
    assert d.player.tolist() == ["Jalen Wilson"]
