"""
Edge Index v2 — Unified play tracking, all sports, one schema.

Every posted play (single or parlay leg) lands in one table with the
model's probability, the price we quoted, and later the closing line
and result. This gives subscribers an auditable record and gives us
the two numbers that matter:
  * ROI at quoted price (are we making money?)
  * CLV — closing line value (are we beating the market? the leading
    indicator of long-term profit even during losing stretches)

Usage:
    from engine.core.tracking import Tracker
    t = Tracker("edge_index_plays.db")
    t.post_play(sport="nfl", ...)          # when card is published
    t.set_closing(play_id, line, odds)     # at kickoff
    t.grade(play_id, actual_value)         # after the game
    t.report()                             # ROI/CLV by sport/market/period
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone

from engine.core.odds import american_to_decimal, american_to_prob, devig_two_way

SCHEMA = """
CREATE TABLE IF NOT EXISTS plays (
    id INTEGER PRIMARY KEY,
    posted_at TEXT NOT NULL,
    sport TEXT NOT NULL,              -- nfl | cfb | mlb | nba
    event_date TEXT NOT NULL,
    game_id TEXT,
    player TEXT,                      -- NULL for team markets (spreads)
    market TEXT NOT NULL,             -- 'rec_yds', 'spread', 'strikeouts'...
    direction TEXT NOT NULL,          -- OVER/UNDER/HOME/AWAY
    line REAL NOT NULL,
    odds REAL NOT NULL,               -- price at post time
    book TEXT,
    model_prob REAL NOT NULL,
    market_prob REAL,                 -- de-vigged at post time
    stake_units REAL DEFAULT 1.0,
    parlay_id TEXT,                   -- non-null groups legs into a parlay
    -- filled later:
    closing_line REAL,
    closing_odds REAL,
    actual_value REAL,
    result TEXT,                      -- win | loss | push | void
    pnl_units REAL
);
CREATE INDEX IF NOT EXISTS ix_plays_sport_date ON plays(sport, event_date);
"""


class Tracker:
    def __init__(self, db_path: str):
        self.con = sqlite3.connect(db_path)
        self.con.executescript(SCHEMA)

    def post_play(self, *, sport, event_date, market, direction, line, odds,
                  model_prob, player=None, game_id=None, book=None,
                  market_prob=None, stake_units=1.0, parlay_id=None) -> int:
        cur = self.con.execute(
            """INSERT INTO plays (posted_at, sport, event_date, game_id, player,
               market, direction, line, odds, book, model_prob, market_prob,
               stake_units, parlay_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now(timezone.utc).isoformat(), sport, event_date, game_id,
             player, market, direction, line, float(odds), book,
             float(model_prob), market_prob, stake_units, parlay_id))
        self.con.commit()
        return cur.lastrowid

    def set_closing(self, play_id: int, closing_line: float, closing_odds: float):
        self.con.execute(
            "UPDATE plays SET closing_line=?, closing_odds=? WHERE id=?",
            (closing_line, closing_odds, play_id))
        self.con.commit()

    def grade(self, play_id: int, actual_value: float):
        row = self.con.execute(
            "SELECT direction, line, odds, stake_units FROM plays WHERE id=?",
            (play_id,)).fetchone()
        if row is None:
            raise KeyError(play_id)
        direction, line, odds, stake = row
        if actual_value == line:
            result, pnl = "push", 0.0
        else:
            won = (actual_value > line) if direction == "OVER" else \
                  (actual_value < line) if direction == "UNDER" else None
            if won is None:
                raise ValueError(f"grade() only handles OVER/UNDER, got {direction}")
            result = "win" if won else "loss"
            pnl = stake * (american_to_decimal(odds) - 1) if won else -stake
        self.con.execute(
            "UPDATE plays SET actual_value=?, result=?, pnl_units=? WHERE id=?",
            (actual_value, result, round(pnl, 4), play_id))
        self.con.commit()

    def clv(self) -> list[tuple]:
        """Average CLV (prob at close minus prob at post) by sport/market."""
        return self.con.execute("""
            SELECT sport, market, COUNT(*) n,
                   ROUND(AVG(
                     (CASE WHEN closing_odds>0 THEN 100.0/(closing_odds+100)
                           ELSE ABS(closing_odds)/(ABS(closing_odds)+100) END) -
                     (CASE WHEN odds>0 THEN 100.0/(odds+100)
                           ELSE ABS(odds)/(ABS(odds)+100) END)), 4) clv
            FROM plays WHERE closing_odds IS NOT NULL
            GROUP BY sport, market""").fetchall()

    def report(self) -> str:
        rows = self.con.execute("""
            SELECT sport, market,
                   SUM(result='win') w, SUM(result='loss') l,
                   SUM(result='push') p, ROUND(SUM(pnl_units),2) pnl,
                   ROUND(SUM(pnl_units)/NULLIF(SUM(CASE WHEN result IN
                     ('win','loss') THEN stake_units END),0),4) roi
            FROM plays WHERE result IS NOT NULL
            GROUP BY sport, market ORDER BY pnl DESC""").fetchall()
        lines = [f"{'sport':<6}{'market':<14}{'W-L-P':<12}{'PnL(u)':>8}{'ROI':>8}"]
        for s, m, w, l, p, pnl, roi in rows:
            lines.append(f"{s:<6}{m:<14}{f'{w}-{l}-{p}':<12}{pnl:>8}"
                         f"{('' if roi is None else f'{roi:+.1%}'):>8}")
        return "\n".join(lines)
