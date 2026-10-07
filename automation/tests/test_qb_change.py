"""QB-change watch: the team's leading passer in its most recent game isn't the QB who led most of its last 10 ->
every receiving and passing leg on that team gets "QB change: history from a different QB" (a watch: one ticket max)."""
import pandas as pd
from availability import qb_changes, reasons
from conftest import write_slate, run_card, row, GAMES
import card_qa


def games(team, leaders, season=2026):
    """one row per game: the passer with the most attempts, plus a backup with fewer"""
    rows = []
    for i, qb in enumerate(leaders):
        rows.append(dict(team=team, season=season, week=i + 1, player_display_name=qb, attempts=30))
        rows.append(dict(team=team, season=season, week=i + 1, player_display_name="Backup", attempts=2))
    return pd.DataFrame(rows)


def test_new_starter_in_the_latest_game_is_flagged():
    st = games("TB", ["Mayfield"] * 9 + ["Daniels"])
    q = qb_changes(st, 2026, 11)
    assert q["TB"]["recent"] == "Daniels" and q["TB"]["usual"] == "Mayfield" and q["TB"]["usual_games"] == 9


def test_same_starter_or_a_new_majority_is_not_flagged():
    assert qb_changes(games("TB", ["Mayfield"] * 10), 2026, 11) == {}
    assert qb_changes(games("TB", ["Mayfield"] * 4 + ["Daniels"] * 6), 2026, 11) == {}     # his history now


def test_walk_forward_only_games_before_the_week_count():
    st = games("TB", ["Mayfield"] * 9 + ["Daniels"])                        # Daniels led week 10
    assert qb_changes(st, 2026, 10) == {}                                   # building week 10: week 10 isn't known yet


def test_flag_touches_receiving_and_passing_legs_only():
    snap = dict(players={}, team_games={}, qb_change={"TB": dict(recent="Daniels", usual="Mayfield", usual_games=9, games=10, week="2026 wk 4")})
    for m in ("rec_yds", "receptions", "pass_yds", "pass_att", "pass_cmps"):
        holds, flags = reasons(snap, "Mike Evans", m, "TB")
        assert holds == [] and flags and flags[0].startswith("QB change: history from a different QB")
    assert reasons(snap, "Bucky Irving", "rush_yds", "TB") == ([], [])
    assert reasons(snap, "CeeDee Lamb", "rec_yds", "DAL") == ([], [])


def test_qb_change_is_a_watch_one_ticket_max_and_qa_checks_it(slate_root):
    avail = dict(season=2026, week=9, fetched_at="t", sources=dict(snap_counts="test", injuries="test"), team_games={},
                 qb_change={GAMES[0][0]: dict(recent="New", usual="Old", usual_games=9, games=10, week="2026 wk 8")}, players={})
    star = row("Star WR", GAMES[0], grade="A+", edge=9, market="rec_yds", floor=50)
    filler = [row(f"Fill{i}", GAMES[(i % 6) + 1], grade="A-", odds=-250, edge=3.0) for i in range(12)]
    write_slate(slate_root, [star] + filler, avail=avail)
    card = run_card(slate_root)
    on = sum(1 for t in card["tickets"] for l in t["legs"] if l["player"] == "Star WR")
    assert on == 1                                                           # a floor star, but capped at one ticket
    leg = next(l for t in card["tickets"] for l in t["legs"] if l["player"] == "Star WR")
    assert any(f.startswith("QB change") for f in leg["injury_watch"])
    import copy, json, os
    legs = json.load(open(os.path.join(slate_root, "cards", "legs_2026_w9_sun.json")))
    doctored = copy.deepcopy(card)
    doctored["tickets"][1]["legs"][0] = dict(leg)                           # force a second ticket for the flagged star
    assert any(r.startswith("R11") and not ok for r, ok, _ in card_qa.check(doctored, legs, avail))
