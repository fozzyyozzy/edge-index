"""Settling the Legs board (settle.py) and grading tickets (grade.py) from fixed box scores."""
import pandas as pd
import pytest
import settle, grade


def board():
    return [dict(player="Hit Man", team="AAA", market="receptions", rungs=[dict(rung=3.0), dict(rung=5.0)]),
            dict(player="Miss Man", team="AAA", market="rec_yds", rungs=[dict(rung=40.0)]),
            dict(player="Scratched", team="BBB", market="rush_yds", rungs=[dict(rung=30.0)]),
            dict(player="Not Final", team="CCC", market="receptions", rungs=[dict(rung=2.0)])]


BOX = {("hit man", "receptions"): 5, ("miss man", "rec_yds"): 39, ("not final", "receptions"): 7}


def test_settle_rows_hit_miss_void_and_unsettled():
    p = board()
    n = settle.settle_rows(p, BOX, {"AAA", "BBB"})
    assert n == 3
    assert [r["result"] for r in p[0]["rungs"]] == ["hit", "hit"]          # 5 clears 3+ and 5+ (exactly on = hit)
    assert p[1]["rungs"][0]["result"] == "miss" and p[1]["actual"] == 39.0
    assert p[2]["actual"] is None and p[2]["rungs"][0]["result"] == "void"  # final game, no stat row
    assert "result" not in p[3]["rungs"][0] and "settled" not in p[3]       # game not final: untouched


def test_settle_rows_is_idempotent():
    a, b = board(), board()
    settle.settle_rows(a, BOX, {"AAA", "BBB"}); settle.settle_rows(b, BOX, {"AAA", "BBB"}); settle.settle_rows(b, BOX, {"AAA", "BBB"})
    assert a == b


def test_settled_teams_needs_final_score_and_stats(monkeypatch):
    sch = pd.DataFrame(dict(home_team=["AAA", "CCC", "EEE"], away_team=["BBB", "DDD", "FFF"], result=[3.0, None, 7.0]))
    monkeypatch.setattr(settle, "schedule", lambda s, w: sch)
    stats = pd.DataFrame(dict(team=["AAA", "BBB", "CCC"]))                  # EEE/FFF final but stats not in yet
    assert settle.settled_teams(2026, 9, stats) == {"AAA", "BBB"}


@pytest.mark.parametrize("hits,expected", [
    ([True, True, True], ("WIN", round(1.4 * 1.5 * 2.0 - 1, 2))),
    ([True, False, True], ("LOSS", -1.0)),
    ([True, None, True], ("VOID", 0.0)),
])
def test_ticket_settles(hits, expected):
    assert grade.settle(hits, [1.4, 1.5, 2.0]) == expected


def test_early_exit_leg_drops_out_and_the_rest_decide():
    t = dict(est_american=300)
    prices = [(-250, None), (-200, None), (-150, None)]
    res, units = grade.official(t, [True, None, True], [False, True, False], prices)
    assert res == "WIN" and units == round(grade.dec(-250) * grade.dec(-150) - 1, 2)   # repriced without the exit leg
    assert grade.official(t, [False, None, True], [False, True, False], prices)[0] == "LOSS"
    assert grade.official(t, [None, None, None], [True, True, True], prices) == ("VOID", 0.0)


def test_win_with_no_early_exit_pays_the_published_ticket_price():
    assert grade.official(dict(est_american=300), [True, True], [False, False], [(-250, None), (-200, None)]) == ("WIN", 3.0)


def test_clv_points_positive_when_the_price_shortened():
    assert grade.clv_pts(-250, -300) > 0 and grade.clv_pts(-250, -200) < 0 and grade.clv_pts(-250, None) is None


def test_closing_price_is_the_last_point_before_kickoff():
    leg = dict(team="AAA", price_history=[dict(at="2026-10-04T13:00Z", odds=-250), dict(at="2026-10-04T16:00Z", odds=-280),
                                         dict(at="2026-10-04T18:00Z", odds=-400)])
    assert grade.closing_odds(leg, {"AAA": "2026-10-04T17:00Z"}) == -280
