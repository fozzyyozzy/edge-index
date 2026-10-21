"""One player ID crosswalk: ESPN athlete id <-> NBA.com person id <-> The Odds API player name.

    python -m engine.nba.crosswalk          # rebuild data/nba/player_crosswalk.csv

ESPN id is the primary key (ESPN is the box-score source). NBA.com ids come from the one-time local nba_api
cross-check pull (data/nba/raw/nba_api/, gitignored); they are matched per game on (date, team, name key), then on
an exact stat line (minutes, pts, reb, ast) within the team-game for names that differ.
Odds API outcomes carry only a display name, so match_odds_name() resolves a name against the players on the two
teams in that event; manual fixes go in data/nba/crosswalk_overrides.csv (source,name,espn_id).
Keys are per player, never per team: a traded player keeps one row with every team he appeared for.
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "nba"
OUT = DATA / "player_crosswalk.csv"
OVERRIDES = DATA / "crosswalk_overrides.csv"
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
# first-name variants seen across books and box scores; applied to the first token only
NICKNAMES = {"nicolas": "nic", "herbert": "herb", "cameron": "cam", "moe": "moritz", "mohamed": "mo",
             "mohammed": "mo", "alexandre": "alex", "nahshon": "bones", "sviatoslav": "svi"}


def name_key(name: str) -> str:
    """Accent-, case-, punctuation- and suffix-insensitive key: 'Nikola Jokić' == 'nikola jokic',
    'Jaren Jackson Jr.' == 'Jaren Jackson', 'P.J. Washington' == 'PJ Washington'."""
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'’`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).split()
    s = [t for t in s if t not in SUFFIXES]
    if s and s[0] in NICKNAMES:
        s[0] = NICKNAMES[s[0]]
    return " ".join(s)


def load_overrides() -> pd.DataFrame:
    if OVERRIDES.exists():
        return pd.read_csv(OVERRIDES, dtype=str)
    return pd.DataFrame(columns=["source", "name", "espn_id"])


def match_nba_ids(espn_pg: pd.DataFrame, nba_log: pd.DataFrame) -> pd.DataFrame:
    """espn_pg: player_games (played rows). nba_log: LeagueGameLog P rows. Returns espn_id -> nba_id with method."""
    e = espn_pg[espn_pg.played].assign(key=lambda d: d.player.map(name_key))
    n = nba_log.rename(columns={"PLAYER_ID": "nba_id", "PLAYER_NAME": "nba_name", "TEAM_ABBREVIATION": "team",
                                "GAME_DATE": "date", "MIN": "minutes", "PTS": "pts", "REB": "reb", "AST": "ast"})
    n = n.assign(key=n.nba_name.map(name_key), date=pd.to_datetime(n.date).dt.strftime("%Y-%m-%d"))
    by_name = e.merge(n[["date", "team", "key", "nba_id", "nba_name"]], on=["date", "team", "key"])
    by_name["method"] = "name"
    claimed = set(zip(by_name.date, by_name.team, by_name.nba_id))
    rest = e[~e.set_index(["game_id", "espn_id"]).index.isin(by_name.set_index(["game_id", "espn_id"]).index)]
    n_rest = n[[k not in claimed for k in zip(n.date, n.team, n.nba_id)]]
    stat = ["date", "team", "minutes", "pts", "reb", "ast"]
    # a stat line identifies a player only if it's distinctive (not a 1-minute 0/0/0) and unique on both sides
    rest = rest[(rest.minutes >= 5) & ~rest.duplicated(stat, keep=False)]
    n_rest = n_rest[(n_rest.minutes >= 5) & ~n_rest.duplicated(stat, keep=False)]
    by_stat = rest.merge(n_rest[stat + ["nba_id", "nba_name"]], on=stat)
    by_stat["method"] = "statline"
    votes = pd.concat([by_name, by_stat])
    agg = (votes.groupby(["espn_id", "nba_id"])
           .agg(games=("game_id", "size"), method=("method", lambda m: "name" if (m == "name").any() else "statline"),
                nba_name=("nba_name", "last"))
           .reset_index().sort_values("games", ascending=False))
    agg["conflict"] = agg.duplicated("espn_id", keep=False) | agg.duplicated("nba_id", keep=False)
    return agg.drop_duplicates("espn_id")


def build(espn_pg: pd.DataFrame, nba_log: pd.DataFrame | None) -> pd.DataFrame:
    played = espn_pg[espn_pg.played].sort_values("date")
    base = (played.groupby("espn_id")
            .agg(espn_name=("player", "last"), teams=("team", lambda t: "|".join(dict.fromkeys(t))),
                 seasons=("season", lambda s: "|".join(sorted(set(s)))), first_game=("date", "min"),
                 last_game=("date", "max"), last_team=("team", "last"), games=("game_id", "size"))
            .reset_index())
    base["name_key"] = base.espn_name.map(name_key)
    if nba_log is not None and len(nba_log):
        ids = match_nba_ids(espn_pg, nba_log)
        base = base.merge(ids[["espn_id", "nba_id", "nba_name", "method", "conflict"]], on="espn_id", how="left")
        base["nba_id"] = base.nba_id.astype("Int64")
    return base


def roster_index(crosswalk: pd.DataFrame, rosters: pd.DataFrame | None = None) -> pd.DataFrame:
    """espn_id, name, team rows to resolve names against: the crosswalk's last team plus current rosters."""
    idx = crosswalk[["espn_id", "espn_name", "last_team"]].rename(columns={"espn_name": "name", "last_team": "team"})
    if rosters is not None and len(rosters):
        idx = pd.concat([rosters[["espn_id", "name", "team"]], idx]).drop_duplicates(["espn_id", "team"])
    return idx.assign(key=idx.name.map(name_key))


def match_odds_name(name: str, teams: tuple[str, str], index: pd.DataFrame,
                    overrides: pd.DataFrame | None = None) -> str | None:
    """ESPN id for an Odds API player name in a game between `teams`; None when unknown or ambiguous."""
    ov = overrides if overrides is not None else load_overrides()
    hit = ov[(ov.source == "odds_api") & (ov.name == name)]
    if len(hit):
        return str(hit.espn_id.iloc[0])
    k = name_key(name)
    cand = index[(index.key == k) & index.team.isin(teams)]
    if cand.espn_id.nunique() == 1:
        return str(cand.espn_id.iloc[0])
    if cand.empty:                                   # traded since the index was built: any team, if unique
        cand = index[index.key == k]
        if cand.espn_id.nunique() == 1:
            return str(cand.espn_id.iloc[0])
    return None


def espn_rosters() -> pd.DataFrame:
    """Current ESPN rosters (all 30 teams): espn_id, name, team."""
    from engine.nba import http
    from engine.nba.espn import BASE
    from engine.nba.teams import from_espn
    teams = http.get_json(f"{BASE}/teams")["sports"][0]["leagues"][0]["teams"]
    rows = []
    for t in teams:
        tid, code = t["team"]["id"], from_espn(t["team"]["abbreviation"])
        for a in http.get_json(f"{BASE}/teams/{tid}/roster").get("athletes", []):
            rows.append({"espn_id": str(a["id"]), "name": a["displayName"], "team": code})
    return pd.DataFrame(rows)


def main():
    pg = pd.read_parquet(DATA / "player_games.parquet")
    logs = sorted((DATA / "raw" / "nba_api").glob("leaguegamelog_P_*.parquet"))
    nba = pd.concat([pd.read_parquet(p) for p in logs]) if logs else None
    cw = build(pg, nba)
    ros = espn_rosters()
    ros.to_csv(DATA / "rosters_espn.csv", index=False)
    new = ros[~ros.espn_id.isin(cw.espn_id)]
    cw = pd.concat([cw, new.rename(columns={"name": "espn_name", "team": "last_team"})
                   .assign(teams=new.team, name_key=new.name.map(name_key), games=0)], ignore_index=True)
    cw.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(cw)} players "
          f"({cw.nba_id.notna().sum() if 'nba_id' in cw else 0} with NBA.com id, {len(new)} roster-only)")


if __name__ == "__main__":
    main()
