"""A settled slate keeps its results through any later regrade, and a late odds refresh can't regrade a played slate.
2026-10-12: the Monday 7pm refresh ran at 9:16pm ET, after MNF kickoff; upcoming_slate() wrapped to "tnf", the week was
still 5, so it pulled week 6's Thursday game into week 5's files and regraded week 5's played TNF board, wiping its
settled results (and grading it with the game's own stats)."""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import grade_legs
import refresh_odds
import fetch_lines

ET = ZoneInfo("America/New_York")


def row(player, market, grade="A", settled=False, result=None, actual=None):
    r = dict(player=player, market=market, team="TB", rungs=[dict(rung=3.0, grade=grade, **({"result": result} if result else {}))])
    if settled: r.update(settled=True, actual=actual)
    return r


def test_a_regrade_keeps_settled_rows_exactly(tmp_path):
    path = tmp_path / "legs.json"
    old = [row("Godwin", "receptions", settled=True, result="hit", actual=6.0),
           row("Irving", "rush_yds", settled=True, result="miss", actual=31.0),
           row("Otton", "rec_yds")]                                         # not settled: a regrade may replace it
    json.dump(dict(meta={}, players=old), open(path, "w"))
    new = [row("Godwin", "receptions", grade="B"),                           # regraded after the game, results gone
           row("Otton", "rec_yds", grade="C"), row("Evans", "rec_yds")]
    merged = {(p["player"], p["market"]): p for p in grade_legs.keep_settled(new, str(path))}
    assert merged[("Godwin", "receptions")] == old[0]                       # settled row untouched (grade, result, actual)
    assert merged[("Irving", "rush_yds")] == old[1]                          # kept even though the regrade dropped it
    assert merged[("Otton", "rec_yds")]["rungs"][0]["grade"] == "C"          # unsettled rows take the new grade
    assert ("Evans", "rec_yds") in merged


def test_settle_then_regrade_then_settle_is_stable(tmp_path):
    import settle
    path = tmp_path / "legs.json"
    board = [row("Godwin", "receptions"), row("Lamb", "receptions")]
    settle.settle_rows(board, {("godwin", "receptions"): 6.0, ("lamb", "receptions"): 2.0}, {"TB"})
    json.dump(dict(meta={}, players=board), open(path, "w"))
    regraded = grade_legs.keep_settled([row("Godwin", "receptions", grade="F"), row("Lamb", "receptions", grade="F")], str(path))
    assert [(p["player"], p["rungs"][0]["result"], p["rungs"][0]["grade"]) for p in regraded] == \
        [("Godwin", "hit", "A"), ("Lamb", "miss", "A")]


def test_no_settled_file_means_no_change(tmp_path):
    new = [row("A", "rec_yds")]
    assert grade_legs.keep_settled(new, str(tmp_path / "missing.json")) == new


def test_late_monday_refresh_serves_the_slot_slate_not_next_weeks_tnf(monkeypatch):
    monkeypatch.setattr(refresh_odds, "served_slots", lambda: set())
    late = datetime(2026, 10, 12, 21, 16, tzinfo=ET).astimezone(timezone.utc)      # Mon 7pm slot, started 9:16pm ET
    slate, slot = refresh_odds.which_slate(late)
    assert slate == "mnf" and slot.startswith("2026-10-12T19:00")
    assert refresh_odds.upcoming_slate(datetime(2026, 10, 12, 21, 16, tzinfo=ET)) is None   # after MNF kickoff: nothing


def test_fetch_lines_keeps_only_this_weeks_games(monkeypatch):
    import floors
    monkeypatch.setattr(floors, "kickoffs", lambda s, w: {"TB": "2026-10-09T00:15+00:00", "DAL": "2026-10-09T00:15+00:00",
                                                         "BUF": "2026-10-13T00:15+00:00", "LA": "2026-10-13T00:15+00:00"})
    ev = [dict(commence_time="2026-10-13T00:15:00Z"), dict(commence_time="2026-10-16T00:15:00Z")]   # MNF wk5, TNF wk6
    assert fetch_lines.in_week(ev, 2026, 5) == [ev[0]]
