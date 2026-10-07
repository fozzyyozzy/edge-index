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
