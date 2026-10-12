"""Per team-game stats for the totals model (Phase 5B), from games.parquet + plays.

One row per (game, team) in FBS-involved games (non-CFP bowls excluded, like the ratings):
  pts        points scored (games.parquet: official, not PBP)
  drives     offensive drives (CFBD advanced game stats)
  ppd        points per drive = official points / drives
  plays      offensive scrimmage plays, garbage time excluded (Phase 2 model plays)
  spp        median seconds per offensive play (clock delta between consecutive plays in a
             drive, same period, 0 < delta < 60; garbage time excluded)
  xpl        explosiveness: mean EPA on successful offensive plays (garbage excluded)
Results come from completed games only; every downstream use is as-of (kickoff < cutoff).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.ratings import plays_prep

DERIVED = plays_prep.DERIVED
TEAM_GAMES = DERIVED / "team_games.parquet"


def build(write: bool = True, games: pd.DataFrame | None = None,
          plays: pd.DataFrame | None = None, model_plays: pd.DataFrame | None = None) -> pd.DataFrame:
    games = games if games is not None else pd.read_parquet(config.CLEAN / "games.parquet")
    plays = plays if plays is not None else pd.read_parquet(config.CLEAN / "plays.parquet", columns=[
        "game_id", "drive_id", "drive_number", "play_number", "period", "clock_minutes",
        "clock_seconds", "offense", "offense_id", "home", "offense_score", "defense_score",
        "play_type", "is_scrimmage", "is_duplicate"])
    mp = model_plays if model_plays is not None else plays_prep.load()

    g = games[games.fbs_involved & (games.completed == True) & ~(games.is_bowl & ~games.is_cfp)]  # noqa: E712
    base = pd.concat([
        g[["game_id", "season", "kickoff_utc", "home_id", "away_id", "home_points", "neutral_site"]]
        .rename(columns={"home_id": "team_id", "away_id": "opp_id", "home_points": "pts"}).assign(home=1),
        g[["game_id", "season", "kickoff_utc", "away_id", "home_id", "away_points", "neutral_site"]]
        .rename(columns={"away_id": "team_id", "home_id": "opp_id", "away_points": "pts"}).assign(home=-1),
    ]).dropna(subset=["team_id", "opp_id"])
    base["home"] = np.where(base.neutral_site.astype(bool), 0, base.home)
    base = base.astype({"team_id": "int64", "opp_id": "int64"}).drop(columns="neutral_site")

    p = plays[plays.game_id.isin(g.game_id) & ~plays.is_duplicate.fillna(False)].dropna(subset=["offense_id"])
    p = p.sort_values(["game_id", "drive_number", "play_number"], kind="stable")
    # drives: CFBD advanced game stats (the PBP drive/offense labels are unreliable in some
    # feeds, e.g. punts credited to the receiving team); ppd = official points / drives
    gts = pd.read_parquet(config.CLEAN / "game_team_stats.parquet", columns=["game_id", "team", "adv_offense_drives"])
    names = pd.concat([g[["game_id", "home_team", "home_id"]].set_axis(["game_id", "team", "team_id"], axis=1),
                       g[["game_id", "away_team", "away_id"]].set_axis(["game_id", "team", "team_id"], axis=1)])
    dg = gts.merge(names, on=["game_id", "team"], how="inner").dropna(subset=["team_id"])
    dg = dg.rename(columns={"adv_offense_drives": "drives"})[["game_id", "team_id", "drives"]]         .astype({"team_id": "int64"})
    # seconds per play
    sc = p[p.is_scrimmage.fillna(False)].copy()
    sc["t"] = sc.clock_minutes * 60 + sc.clock_seconds
    sc["dt"] = sc.groupby(["game_id", "drive_id", "period"]).t.shift(1) - sc.t
    ok = sc.dt.between(1, 59)
    spp = sc[ok].groupby(["game_id", "offense_id"]).dt.median().rename("spp").reset_index() \
        .rename(columns={"offense_id": "team_id"})
    # plays + explosiveness from Phase 2 model plays (garbage excluded)
    m = mp[~mp.is_garbage_time]
    pl = m.groupby(["game_id", "offense_id"]).agg(plays=("epa", "size"), xpl=("explosive", "mean")) \
        .reset_index().rename(columns={"offense_id": "team_id"})

    out = base.merge(dg, on=["game_id", "team_id"], how="left") \
              .merge(spp.astype({"team_id": "int64"}), on=["game_id", "team_id"], how="left") \
              .merge(pl.astype({"team_id": "int64"}), on=["game_id", "team_id"], how="left")
    out["ppd"] = np.where(out.drives > 0, out.pts / out.drives, np.nan)
    if write:
        DERIVED.mkdir(parents=True, exist_ok=True)
        out.to_parquet(TEAM_GAMES, index=False)
    return out


def load() -> pd.DataFrame:
    if not TEAM_GAMES.exists():
        build()
    return pd.read_parquet(TEAM_GAMES)


if __name__ == "__main__":
    t = build()
    print(t.groupby("season")[["pts", "drives", "ppd", "plays", "spp", "xpl"]].mean().round(2).to_string())
    print(f"{len(t):,} team-games -> {TEAM_GAMES}")
