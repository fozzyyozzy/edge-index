"""R6 team changes: a player with 4+ games for his new team is settled - graded on new-team games only (4-game minimum),
no team-change hold, and no longer "new target competition" for teammates. (2026-10-19: Mike Evans, 5 games with SF,
was still held, and Kittle still carried a competition flag from him.)"""
import pandas as pd
from common import grading_history, SETTLED_GAMES, frac_count
from grade_legs import target_competition


def rows(team_by_week, season=2026, targets=6):
    return pd.DataFrame([dict(season=season, week=w, team=t, targets=targets, key="mike evans",
                              player_display_name="Mike Evans", position="WR") for w, t in team_by_week])


LAST_YEAR = [(w, "TB") for w in range(1, 18)]


def test_moved_player_is_held_until_four_games_with_the_new_team():
    g = pd.concat([rows(LAST_YEAR, 2025), rows([(1, "SF"), (2, "SF"), (3, "SF")])])
    kept, hold, minimum = grading_history(g, 2026, "SF", "TB")
    assert hold and minimum == 10 and len(kept) == len(g)              # 3 games: still a team-change hold


def test_settled_mover_is_graded_on_new_team_games_only():
    g = pd.concat([rows(LAST_YEAR, 2025), rows([(w, "SF") for w in range(1, 6)])])
    kept, hold, minimum = grading_history(g, 2026, "SF", "TB")
    assert not hold and minimum == SETTLED_GAMES == 4
    assert set(kept.team) == {"SF"} and len(kept) == 5                  # last season's TB games dropped


def test_games_with_the_new_team_count_every_appearance_not_just_market_involvement():
    played = pd.concat([rows(LAST_YEAR, 2025), rows([(w, "SEA") for w in range(1, 6)])])
    targeted = played[(played.season == 2025) | played.week.isin([2, 4])]     # only 2 of his 5 SEA games had a target
    kept, hold, minimum = grading_history(targeted, 2026, "SEA", "GB", played)
    assert not hold and len(kept) == 2 < minimum                        # settled, but too few targeted games to grade


def test_no_team_change_is_unchanged():
    g = rows([(w, "SF") for w in range(1, 6)])
    kept, hold, minimum = grading_history(g, 2026, "SF", "SF")
    assert not hold and minimum == 10 and len(kept) == 5


def test_newcomer_stops_being_target_competition_after_four_games():
    prev = rows(LAST_YEAR, 2025)
    cur3 = rows([(w, "SF") for w in range(1, 4)], targets=9)
    cur5 = rows([(w, "SF") for w in range(1, 6)], targets=9)
    assert "SF" in target_competition(cur3, prev)                       # 3 games, 9 targets: still new competition
    assert target_competition(cur5, prev) == {}                         # 5 games: settled


def test_clear_rate_strings_carry_real_counts():
    assert frac_count("9/10") == (9, 10) and frac_count("4/5") == (4, 5)
