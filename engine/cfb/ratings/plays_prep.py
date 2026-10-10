"""plays.parquet -> data/cfb/derived/model_plays.parquet (Phase 2 brief §3).

    python -m engine.cfb.ratings.plays_prep

Scope: plays from FBS-involved games (FCS teams enter through their FBS games).
The output keeps every play that passes the fixed filters and carries the
garbage-time inputs (period, pre-snap margin) plus `is_garbage_time` at the
default thresholds, so tuning can re-threshold without rebuilding. The rating
fits drop `is_garbage_time` rows.

Play mapping (CFBD play_type + play_text):
  pass  = Pass Reception, Pass Incompletion, Pass Completion, Passing Touchdown,
          Pass, Sack, Interception, Pass Interception Return, Interception Return
          Touchdown; plus Rush/Rushing Touchdown whose text says "scramble"
  rush  = Rush, Rushing Touchdown (not kneels, not scrambles)
  fumble plays (Fumble Recovery (Own/Opponent), Fumble Return Touchdown) are
          assigned by text: "pass"/"sacked" -> pass, " run " -> rush, else
          kept for overall metrics only (is_rush = is_pass = False)
  dropped: kneels (text "kneel", or a "TEAM run" for <= 0 yards: how older
          feeds write kneels), spikes (text "spike"), down 0 / missing
CFBD tags few scrambles (~360 plays in 6 seasons), so most scrambles stay rush.
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd

from engine.cfb import config

DERIVED = config.DATA / "derived"
MODEL_PLAYS = DERIVED / "model_plays.parquet"
DROP_COUNTS = DERIVED / "plays_prep_counts.json"
DEFAULT_GARBAGE = {"q2": 38, "q3": 28, "q4": 22}

PASS_TYPES = {"Pass Reception", "Pass Incompletion", "Pass Completion",
              "Passing Touchdown", "Pass", "Sack", "Interception",
              "Pass Interception Return", "Interception Return Touchdown"}
RUSH_TYPES = {"Rush", "Rushing Touchdown"}
FUMBLE_TYPES = {"Fumble Recovery (Own)", "Fumble Recovery (Opponent)",
                "Fumble Return Touchdown"}
TURNOVER_TYPES = {"Interception", "Pass Interception Return",
                  "Interception Return Touchdown", "Fumble Recovery (Opponent)",
                  "Fumble Return Touchdown"}

COLS = ["play_id", "game_id", "season", "week", "season_type", "drive_id",
        "drive_number", "play_number",
        "offense", "offense_id", "defense", "defense_id", "home", "period",
        "down", "distance", "yards_gained", "play_type", "play_text", "ppa",
        "offense_score", "defense_score", "is_duplicate"]


def garbage_flag(period: pd.Series, abs_margin: pd.Series, g: dict) -> pd.Series:
    """Garbage time: |margin| at the snap > q2 in Q2, q3 in Q3, q4 in Q4+. Never Q1."""
    thr = np.select([period == 2, period == 3, period >= 4],
                    [g["q2"], g["q3"], g["q4"]], default=np.inf)
    return pd.Series(abs_margin.values > thr, index=abs_margin.index)


def pre_snap_margin(p: pd.DataFrame) -> pd.Series:
    """|home - away| before each play. CFBD play scores are post-play, so the
    pre-snap score is the previous play's score in the same game (0-0 first)."""
    is_home = p.offense.values == p.home.values
    home = np.where(is_home, p.offense_score, p.defense_score).astype(float)
    away = np.where(is_home, p.defense_score, p.offense_score).astype(float)
    s = pd.DataFrame({"g": p.game_id.values, "h": home, "a": away}, index=p.index)
    prev = s.groupby("g")[["h", "a"]].shift(1).fillna(0.0)
    return (prev.h - prev.a).abs()


def build(garbage: dict | None = None, write: bool = True):
    garbage = garbage or DEFAULT_GARBAGE
    games = pd.read_parquet(config.CLEAN / "games.parquet")
    plays = pd.read_parquet(config.CLEAN / "plays.parquet", columns=COLS)

    g = games.set_index("game_id")
    plays = plays[plays.game_id.isin(g.index[g.fbs_involved])].copy()
    # chronological order within game (play_id formats vary by season)
    plays = plays.sort_values(["game_id", "drive_number", "play_number"], kind="stable")
    plays["abs_margin_pre"] = pre_snap_margin(plays)

    t = plays.play_text.fillna("").str.lower()
    pt = plays.play_type
    scramble = pt.isin(RUSH_TYPES) & t.str.contains("scramble")
    # older feeds (mostly 2021-22) write kneels as "TEAM run for a loss of N"
    team_kneel = pt.isin(RUSH_TYPES) & t.str.match(r"^team run") & (plays.yards_gained <= 0)
    kneel = (t.str.contains("kneel") & ~pt.isin(TURNOVER_TYPES)) | team_kneel
    spike = t.str.contains("spike") & pt.isin(PASS_TYPES - TURNOVER_TYPES)
    fumble_pass = pt.isin(FUMBLE_TYPES) & t.str.contains(r"\bpass\b|sacked")
    fumble_rush = pt.isin(FUMBLE_TYPES) & ~fumble_pass & t.str.contains(r"\brun\b")
    scrimmage = pt.isin(PASS_TYPES | RUSH_TYPES | FUMBLE_TYPES)

    bowl_out = g.is_bowl & ~g.is_cfp
    reasons = [  # first matching reason wins
        ("not_scrimmage", ~scrimmage),
        ("duplicate", plays.is_duplicate.fillna(False)),
        ("kneel_or_spike", kneel | spike),
        ("non_cfp_bowl", plays.game_id.map(bowl_out).fillna(False)),
        ("bad_down", ~plays.down.isin([1, 2, 3, 4])),
        ("null_ppa", plays.ppa.isna()),
    ]
    reason = pd.Series(pd.NA, index=plays.index, dtype="object")
    for name, mask in reasons:
        reason = reason.mask(reason.isna() & mask.values, name)
    plays["is_garbage_time"] = garbage_flag(plays.period, plays.abs_margin_pre, garbage)
    reason = reason.mask(reason.isna() & plays.is_garbage_time, "garbage_time")

    counts = (pd.DataFrame({"season": plays.season, "reason": reason.fillna("kept")})
              .value_counts().unstack("season", fill_value=0))

    keep = reason.isna() | (reason == "garbage_time")
    m = plays[keep].copy()
    kp = m.play_type
    kt = m.play_text.fillna("").str.lower()
    m_scr = scramble[keep]
    m["is_pass"] = kp.isin(PASS_TYPES) | m_scr | fumble_pass[keep]
    m["is_rush"] = (kp.isin(RUSH_TYPES) & ~m_scr) | fumble_rush[keep]
    m["epa"] = m.ppa.astype(float)
    turnover = kp.isin(TURNOVER_TYPES)
    gain, dist, down = m.yards_gained.astype(float), m.distance.astype(float), m.down
    need = np.select([down == 1, down == 2], [0.5 * dist, 0.7 * dist], default=dist)
    m["success"] = ((gain >= need) & ~turnover).astype(float)
    m["explosive"] = m.epa.where(m.success == 1)

    gi = g.reindex(m.game_id)
    m["kickoff_utc"] = pd.to_datetime(gi.kickoff_utc.values, utc=True)
    neutral = gi.neutral_site.values.astype(bool)
    m["offense_home"] = np.where(neutral, 0,
                                 np.where(m.offense_id.values == gi.home_id.values, 1, -1))
    out = m[["play_id", "game_id", "season", "week", "season_type", "kickoff_utc",
             "offense_id", "offense", "defense_id", "defense", "offense_home",
             "period", "abs_margin_pre", "is_garbage_time", "down", "distance",
             "yards_gained", "play_type", "is_rush", "is_pass", "epa", "success",
             "explosive"]].reset_index(drop=True)
    out["offense_id"] = out.offense_id.astype("int64")
    out["defense_id"] = out.defense_id.astype("int64")
    if write:
        DERIVED.mkdir(parents=True, exist_ok=True)
        out.to_parquet(MODEL_PLAYS, index=False)
        DROP_COUNTS.write_text(json.dumps(
            {"garbage": garbage, "counts": counts.to_dict()}, indent=1, default=int))
    return out, counts


def load() -> pd.DataFrame:
    if not MODEL_PLAYS.exists():
        build()
    return pd.read_parquet(MODEL_PLAYS)


if __name__ == "__main__":
    df, c = build()
    print(c.to_string())
    print(f"model_plays: {len(df):,} rows (incl. garbage-flagged) -> {MODEL_PLAYS}")
