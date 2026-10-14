"""price_check.py: ROI at listed prices, voids excluded, and one-rung-per-row picks the row's best rung."""
import pandas as pd
from price_check import summarize, board_split


def test_summarize_roi_at_listed_prices_excludes_voids():
    s = pd.DataFrame(dict(result=["hit", "hit", "miss", "void"], odds=[-200, -200, -200, -200], prob=[0.7, 0.7, 0.7, 0.7]))
    r = summarize(s, "x")
    assert (r["n"], r["record"], r["voids"]) == (3, "2-1", 1)
    assert r["implied"] == 66.7 and r["roi"] == 0.0                     # 2 x +0.5u - 1u = 0 over 3 bets


def test_board_split_counts_every_rung_and_one_per_row():
    b = pd.DataFrame([dict(week=4, slate="sun", player="P", market="rec_yds", rung=t, odds=o, grade=g, edge=e, prob=0.7, result=r)
                      for t, o, g, e, r in [(25, -300, "A", 3.0, "hit"), (40, -200, "C", 2.5, "miss"), (15, -800, "A+", 1.0, "hit")]])
    rows = {(x["group"], x["count"]): x for x in board_split(b)}
    assert rows[("-500 or better, edge >= +2", "every rung")]["n"] == 2
    one = rows[("-500 or better, edge >= +2", "one rung per player/market")]
    assert one["n"] == 1 and one["record"] == "1-0"                       # the A rung (25+) over the C rung
    assert rows[("worse than -500", "every rung")]["n"] == 1


def test_calibration_buckets_one_rung_per_row_for_both_sources():
    from price_check import calibration
    b = pd.DataFrame([dict(week=4, slate="sun", player=f"P{i}", market="rec_yds", rung=25.0, odds=-300, grade="A", edge=3.0,
                           prob=0.82, result="hit" if i < 3 else "miss") for i in range(4)]
                     + [dict(week=4, slate="sun", player="P0", market="rec_yds", rung=15.0, odds=-900, grade="C", edge=1.0,
                             prob=0.90, result="hit")])                   # P0's lower C rung: not the row's best rung
    rows, summary = calibration(b)
    ours = [r for r in rows if r["source"] == "ours"]
    assert ours == [dict(source="ours", bucket="80-85", n=4, predicted=82.0, hit=75.0, gap=-7.0)]
    dk = [r for r in rows if r["source"] == "DK implied"]
    assert dk == [dict(source="DK implied", bucket="75-80", n=4, predicted=75.0, hit=75.0, gap=0.0)]
    assert {s["source"]: s["mean_abs_gap"] for s in summary} == {"ours": 7.0, "DK implied": 0.0}


def test_volume_share_split_is_walk_forward_and_by_team():
    from price_check import share_bucket
    w = pd.DataFrame([
        # week 1-2: JSN leads SEA targets; week 3 (the week being checked) must not count
        dict(season=2026, week=1, team="SEA", key="jaxon smith-njigba", targets=11, carries=0),
        dict(season=2026, week=1, team="SEA", key="cooper kupp", targets=6, carries=0),
        dict(season=2026, week=2, team="SEA", key="jaxon smith-njigba", targets=9, carries=0),
        dict(season=2026, week=2, team="SEA", key="cooper kupp", targets=7, carries=0),
        dict(season=2026, week=3, team="SEA", key="cooper kupp", targets=30, carries=0),
        dict(season=2025, week=17, team="SEA", key="cooper kupp", targets=8, carries=1),
        dict(season=2025, week=17, team="SEA", key="kenneth walker", targets=2, carries=18),
    ])
    assert share_bucket(w, 2026, "Jaxon Smith-Njigba", "rec_yds", 3) == "top-1"
    assert share_bucket(w, 2026, "Cooper Kupp", "receptions", 3) == "rest"          # week 3's 30 targets not seen
    assert share_bucket(w, 2026, "Cooper Kupp", "receptions", 1) == "top-1"         # week 1: last season's share
    assert share_bucket(w, 2026, "Kenneth Walker", "rush_yds", 1) == "top-1"
    assert share_bucket(w, 2026, "Sam Darnold", "pass_yds", 3) == "passer"
