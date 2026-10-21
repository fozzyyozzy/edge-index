"""Pre-registered eligibility for scoring a player-game (docs/nba/PREREG.md §2).

A player-game is eligible when, using only games STRICTLY BEFORE its date:
  * the player has >= MIN_PRIOR games played this season (any team), and
  * his mean minutes over his last <= 10 played games this season is >= MIN_TRAIL_MINUTES.
The game itself and anything after it never enter either filter. An NBA player can't play twice on one date, so
"rows before this one in date order" and "games strictly before this date" are the same set; the code still
compares dates explicitly so a duplicate-date row could never leak.
"""
from __future__ import annotations

import pandas as pd

MIN_PRIOR = 8
TRAIL_N = 10
MIN_TRAIL_MINUTES = 20.0


def prior_form(pg: pd.DataFrame) -> pd.DataFrame:
    """prior_games, trail_minutes for every row of pg, from played games strictly before the row's date."""
    played = pg[pg.played].sort_values(["espn_id", "season", "date"])
    out = []
    for (pid, season), g in played.groupby(["espn_id", "season"], sort=False):
        dates, mins = g.date.to_numpy(), g.minutes.to_numpy(dtype=float)
        for i, d in enumerate(dates):
            before = dates[:i] < d                      # explicit strict-before on the date
            m = mins[:i][before][-TRAIL_N:]
            out.append((g.index[i], int(before.sum()), float(m.mean()) if len(m) else float("nan")))
    f = pd.DataFrame(out, columns=["idx", "prior_games", "trail_minutes"]).set_index("idx")
    return pg.join(f)


def eligible(pg: pd.DataFrame) -> pd.Series:
    f = prior_form(pg)
    return f.played & (f.prior_games >= MIN_PRIOR) & (f.trail_minutes >= MIN_TRAIL_MINUTES)
