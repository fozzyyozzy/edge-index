"""Build the NBA player-game table from ESPN box scores.

    python -m engine.nba.backfill                     # 2023-24, 2024-25, 2025-26 regular seasons
    python -m engine.nba.backfill --seasons 2026-27   # current season to date (re-run daily; cache makes it cheap)

Writes (committed):
    data/nba/player_games.parquet   one row per rostered player per game (DNPs kept, played=False)
    data/nba/games.parquet          one row per game
Context columns: team_games_played (games before this one), days_since_prev (team), b2b, margin,
player_days_since_prev (player's previous game played). Pregame spread/total are joined from
data/nba/lines/pregame_spreads_totals.parquet when it exists (engine.nba.hist_lines).
"""
from __future__ import annotations
import argparse
import gzip
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from engine.nba import espn

ROOT = espn.ROOT
OUT = ROOT / "data" / "nba"
SEASONS = ["2023-24", "2024-25", "2025-26"]
WORKERS = 4


def season_dates(season: str) -> list[date]:
    """Oct 1 .. Apr 30 of the season (ESPN's season.type filters out pre/post-season), never past yesterday ET."""
    y = int(season[:4])
    end = min(date(y + 1, 4, 30), datetime.now(espn.ET).date() - timedelta(days=1))
    d, out = date(y, 10, 1), []
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def events_for(season: str) -> list[dict]:
    cache = espn.CACHE / f"scoreboard_{season}.json.gz"
    seen = json.loads(gzip.decompress(cache.read_bytes())) if cache.exists() else {}
    days = [d for d in season_dates(season) if d.isoformat() not in seen]
    with ThreadPoolExecutor(WORKERS) as pool:
        for d, evs in zip(days, pool.map(espn.scoreboard, days)):
            seen[d.isoformat()] = evs
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(gzip.compress(json.dumps(seen).encode()))
    evs = [e for day in seen.values() for e in day if e["season"] == season]
    return [e for e in evs if e["status"] == "STATUS_FINAL"]


def add_context(pg: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    tg = pd.concat([games.assign(team=games.home), games.assign(team=games.away)])[["game_id", "season", "date", "team"]]
    tg = tg.sort_values(["season", "team", "date", "game_id"])
    tg["team_games_played"] = tg.groupby(["season", "team"]).cumcount()
    d = pd.to_datetime(tg.date)
    tg["days_since_prev"] = (d - d.groupby([tg.season, tg.team]).shift()).dt.days
    tg["b2b"] = tg.days_since_prev.eq(1)
    pg = pg.merge(tg.drop(columns=["season", "date"]), on=["game_id", "team"], how="left")
    pg["margin"] = pg.team_score - pg.opp_score
    played = pg[pg.played].sort_values(["espn_id", "date"])
    pd_ = pd.to_datetime(played.date)
    played = played.assign(player_days_since_prev=(pd_ - pd_.groupby(played.espn_id).shift()).dt.days)
    return pg.merge(played[["game_id", "espn_id", "player_days_since_prev"]], on=["game_id", "espn_id"], how="left")


def join_lines(pg: pd.DataFrame) -> pd.DataFrame:
    p = OUT / "lines" / "pregame_spreads_totals.parquet"
    if not p.exists():
        return pg.assign(team_spread=float("nan"), game_total=float("nan"))
    ln = pd.read_parquet(p)[["game_id", "home_spread", "total"]]
    pg = pg.merge(ln, on="game_id", how="left")
    pg["team_spread"] = pg.home_spread.where(pg.home_away == "H", -pg.home_spread)
    return pg.drop(columns=["home_spread"]).rename(columns={"total": "game_total"})


def build(seasons: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, games = [], []
    for s in seasons:
        evs = events_for(s)
        print(f"{s}: {len(evs)} final regular-season games", flush=True)
        with ThreadPoolExecutor(WORKERS) as pool:
            for summ in pool.map(lambda e: espn.summary(e["event_id"]), evs):
                games.append(espn.game_info(summ))
                rows.extend(espn.player_rows(summ))
    g = pd.DataFrame(games).drop_duplicates("game_id").sort_values(["date", "game_id"])
    pg = add_context(pd.DataFrame(rows), g)
    pg = join_lines(pg).sort_values(["date", "game_id", "team", "starter", "minutes"],
                                    ascending=[True, True, True, False, False])
    return pg.reset_index(drop=True), g.reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", default=SEASONS)
    a = ap.parse_args()
    pg, g = build(a.seasons)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in (("player_games", pg), ("games", g)):
        path = OUT / f"{name}.parquet"
        if path.exists():                       # keep seasons not rebuilt this run
            old = pd.read_parquet(path)
            df = pd.concat([old[~old.season.isin(a.seasons)], df], ignore_index=True)
        df.to_parquet(path, index=False)
        print(f"wrote {path.relative_to(ROOT)}: {len(df):,} rows", flush=True)
    issues = pd.DataFrame(espn.ISSUES, columns=["game_id", "date", "team", "short_name", "did_not_play", "stats", "issue"])
    path = OUT / "espn_issues.csv"
    if path.exists():
        old = pd.read_csv(path, dtype={"game_id": str})
        issues = pd.concat([old, issues]).drop_duplicates(["game_id", "team", "short_name", "issue"])
    issues.sort_values(["date", "game_id"]).to_csv(path, index=False)
    print(f"wrote {path.relative_to(ROOT)}: {len(issues)} ESPN data issues", flush=True)


if __name__ == "__main__":
    main()
