"""Raw CFBD JSON -> clean parquet tables in data/cfb/clean.

    python -m engine.cfb.build_tables

Reads only the raw cache (zero API calls). Never imputes: a value missing
from the API stays null. Column docs live in docs/cfb/PHASE1_REPORT.md.

Spread convention (lines.spread, spread_open, consensus_close_spread):
HOME perspective, negative = home favored -- as CFBD returns it.
"""
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from engine.cfb import config

CLEAN = config.CLEAN

# Single-timezone US states, used only when CFBD's venue timezone is null.
# Split states (FL, IN, KY, TN, MI, ND, SD, NE, KS, TX, ID, OR) are left null.
STATE_TZ = {
    **dict.fromkeys("CT DE DC GA ME MD MA NH NJ NY NC OH PA RI SC VT VA WV".split(),
                    "America/New_York"),
    **dict.fromkeys("AL AR IL IA LA MN MS MO OK WI".split(), "America/Chicago"),
    **dict.fromkeys("CO MT NM UT WY".split(), "America/Denver"),
    "AZ": "America/Phoenix", "CA": "America/Los_Angeles", "NV": "America/Los_Angeles",
    "WA": "America/Los_Angeles", "HI": "Pacific/Honolulu", "AK": "America/Anchorage",
}

RUSH_TYPES = {"Rush", "Rushing Touchdown"}
PASS_TYPES = {"Pass Reception", "Pass Incompletion", "Passing Touchdown", "Sack",
              "Pass Interception Return", "Interception Return Touchdown",
              "Pass Interception", "Interception", "Pass"}
# Fumbles happen on rushes and passes; CFBD doesn't say which. Scrimmage, group 'other'.
FUMBLE_TYPES = {"Fumble Recovery (Own)", "Fumble Recovery (Opponent)",
                "Fumble Return Touchdown"}
SPECIAL_RE = re.compile(r"Punt|Kickoff|Field Goal|Extra Point|Two Point|"
                        r"Blocked|Defensive 2pt|Safety|PAT", re.I)


def _raw(dataset: str) -> list[tuple[str, object]]:
    d = config.RAW / dataset
    if not d.exists():
        return []
    return [(p.stem, json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(d.glob("*.json"))]


def _seasons(dataset: str) -> list[tuple[int, list]]:
    return [(int(stem), rows) for stem, rows in _raw(dataset) if stem.isdigit()]


# ---------------------------------------------------------------- venues
def build_venues() -> pd.DataFrame:
    rows = []
    for _, data in _raw("venues"):
        for v in data:
            tz = v.get("timezone")
            src = "cfbd" if tz else None
            if not tz and v.get("countryCode") == "US" and v.get("state") in STATE_TZ:
                tz, src = STATE_TZ[v["state"]], "state"
            rows.append({
                "venue_id": v["id"], "name": v.get("name"), "city": v.get("city"),
                "state": v.get("state"), "country": v.get("countryCode"),
                "timezone": tz, "timezone_source": src,
                "latitude": v.get("latitude"), "longitude": v.get("longitude"),
                "elevation": v.get("elevation"), "dome": v.get("dome"),
                "grass": v.get("grass"), "capacity": v.get("capacity"),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- games
def build_games(venues: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    tz = ({v: z for v, z in zip(venues.venue_id, venues.timezone) if isinstance(z, str)}
          if len(venues) else {})
    rows = []
    for season, data in _seasons("games"):
        for g in data:
            po = g.get("playoff") or {}
            kick = pd.to_datetime(g.get("startDate"), utc=True)
            vtz = tz.get(g.get("venueId"))
            local_hour = (kick.tz_convert(ZoneInfo(vtz)).hour
                          if vtz and not pd.isna(kick) and not g.get("startTimeTBD")
                          else None)
            hc, ac = g.get("homeClassification"), g.get("awayClassification")
            post = g.get("seasonType") == "postseason"
            rows.append({
                "game_id": g["id"], "season": g.get("season", season),
                "week": g.get("week"), "season_type": g.get("seasonType"),
                "kickoff_utc": kick, "start_time_tbd": g.get("startTimeTBD"),
                "kickoff_local_hour": local_hour,
                "completed": g.get("completed"),
                "neutral_site": bool(g.get("neutralSite")),
                "conference_game": g.get("conferenceGame"),
                "venue_id": g.get("venueId"), "venue": g.get("venue"),
                "attendance": g.get("attendance"),
                "home_id": g.get("homeId"), "home_team": g.get("homeTeam"),
                "home_conference": g.get("homeConference"),
                "home_classification": hc, "home_points": g.get("homePoints"),
                "away_id": g.get("awayId"), "away_team": g.get("awayTeam"),
                "away_conference": g.get("awayConference"),
                "away_classification": ac, "away_points": g.get("awayPoints"),
                "home_line_scores": g.get("homeLineScores"),
                "away_line_scores": g.get("awayLineScores"),
                "home_pregame_elo": g.get("homePregameElo"),
                "away_pregame_elo": g.get("awayPregameElo"),
                "both_fbs": hc == "fbs" and ac == "fbs",
                "fbs_vs_fcs": {hc, ac} == {"fbs", "fcs"},
                "fbs_involved": "fbs" in (hc, ac),
                "is_postseason": post,
                "is_bowl": post and hc == "fbs" and ac == "fbs",
                "is_cfp": po.get("competition") == "cfp",
                "cfp_round": po.get("round"),
                "bowl_name": (po.get("bowlName") or g.get("notes")) if post else None,
                "notes": g.get("notes"),
            })
    games = pd.DataFrame(rows)
    games["margin_home"] = games.home_points - games.away_points

    # consensus close: median spread across every provider row, completed games
    # only (for upcoming games the line has not closed yet).
    if len(lines):
        agg = (lines.dropna(subset=["spread"]).groupby("game_id")
               .agg(consensus_close_spread=("spread", "median"),
                    n_spread_providers=("provider", "nunique")).reset_index())
        games = games.merge(agg, on="game_id", how="left")
        games.loc[games.completed != True, "consensus_close_spread"] = np.nan  # noqa: E712
    return games


# ---------------------------------------------------------------- lines
def build_lines() -> pd.DataFrame:
    rows = []
    for season, data in _seasons("lines"):
        for g in data:
            for ln in g.get("lines") or []:
                rows.append({
                    "game_id": g["id"], "season": g.get("season", season),
                    "week": g.get("week"), "season_type": g.get("seasonType"),
                    "home_team": g.get("homeTeam"), "away_team": g.get("awayTeam"),
                    "provider": ln.get("provider"),
                    "spread": ln.get("spread"), "spread_open": ln.get("spreadOpen"),
                    "total": ln.get("overUnder"), "total_open": ln.get("overUnderOpen"),
                    "home_ml": ln.get("homeMoneyline"), "away_ml": ln.get("awayMoneyline"),
                    "formatted_spread": ln.get("formattedSpread"),
                })
    df = pd.DataFrame(rows)
    for c in ["spread", "spread_open", "total", "total_open", "home_ml", "away_ml"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ---------------------------------------------------------------- plays
def _group(pt: str | None) -> str:
    if not pt:
        return "other"
    if pt in RUSH_TYPES:
        return "rush"
    if pt in PASS_TYPES:
        return "pass"
    if "Penalty" in pt:
        return "penalty"
    if SPECIAL_RE.search(pt):
        return "special"
    return "other"


def build_plays(games: pd.DataFrame) -> pd.DataFrame:
    gmap = games.set_index("game_id")[["home_team", "home_id", "away_team", "away_id"]]
    frames = []
    for stem, data in _raw("plays"):
        m = re.match(r"(\d{4})_(post_)?wk(\d+)$", stem)
        if not m or not data:
            continue
        df = pd.DataFrame(data)
        df["season"] = int(m.group(1))
        df["season_type"] = "postseason" if m.group(2) else "regular"
        df["week"] = int(m.group(3))
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    p = pd.concat(frames, ignore_index=True)
    clock = p.pop("clock").apply(lambda c: c if isinstance(c, dict) else {})
    p["clock_minutes"] = clock.map(lambda c: c.get("minutes"))
    p["clock_seconds"] = clock.map(lambda c: c.get("seconds"))
    p = p.rename(columns={
        "gameId": "game_id", "driveId": "drive_id", "id": "play_id",
        "driveNumber": "drive_number", "playNumber": "play_number",
        "offenseConference": "offense_conference",
        "defenseConference": "defense_conference",
        "offenseScore": "offense_score", "defenseScore": "defense_score",
        "offenseTimeouts": "offense_timeouts", "defenseTimeouts": "defense_timeouts",
        "yardsToGoal": "yards_to_goal", "yardsGained": "yards_gained",
        "playType": "play_type", "playText": "play_text"})
    p["game_id"] = p.game_id.astype("int64")

    # team ids: match the play's offense/defense name to the game's home/away
    g = gmap.reindex(p.game_id)
    for side in ("offense", "defense"):
        p[f"{side}_id"] = np.where(p[side].values == g.home_team.values, g.home_id.values,
                          np.where(p[side].values == g.away_team.values, g.away_id.values,
                                   np.nan))
        p[f"{side}_id"] = pd.to_numeric(p[f"{side}_id"]).astype("Int64")

    p["play_type_group"] = p.play_type.map(_group)
    p["is_scrimmage"] = (p.play_type_group.isin(["rush", "pass"])
                         | p.play_type.isin(FUMBLE_TYPES))
    p["is_garbage_time"] = pd.Series(pd.NA, index=p.index, dtype="boolean")  # Phase 2
    # CFBD feeds sometimes repeat a scrimmage play under a new play_id (same
    # clock, down, distance, spot, text). Rows are kept; repeats are flagged.
    dup_key = ["game_id", "period", "clock_minutes", "clock_seconds", "down",
               "distance", "yards_to_goal", "play_text"]
    p["is_duplicate"] = p.is_scrimmage & p.duplicated(dup_key)
    p["ppa"] = pd.to_numeric(p.ppa, errors="coerce")
    p["wallclock"] = pd.to_datetime(p.get("wallclock"), utc=True, errors="coerce")
    lead = ["play_id", "game_id", "season", "week", "season_type", "drive_id",
            "drive_number", "play_number", "offense", "offense_id", "defense",
            "defense_id", "period", "clock_minutes", "clock_seconds", "down",
            "distance", "yardline", "yards_to_goal", "play_type", "play_type_group",
            "is_scrimmage", "is_garbage_time", "is_duplicate", "ppa", "yards_gained",
            "scoring"]
    return p[lead + [c for c in p.columns if c not in lead]]


# ---------------------------------------------------------------- game-team stats
def _flat(prefix: str, d, out: dict) -> None:
    if isinstance(d, dict):
        for k, v in d.items():
            _flat(f"{prefix}_{k}" if prefix else k, v, out)
    else:
        out[prefix] = d


def _snake(s: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s).lower()   # totalPPA -> total_ppa


def build_game_team_stats() -> pd.DataFrame:
    def frame(ds: str, prefix: str) -> pd.DataFrame:
        rows = []
        for _, data in _seasons(ds):
            for r in data:
                flat: dict = {}
                _flat("", {k: v for k, v in r.items()
                           if k in ("offense", "defense")}, flat)
                rows.append({"game_id": r["gameId"], "season": r.get("season"),
                             "week": r.get("week"), "season_type": r.get("seasonType"),
                             "team": r.get("team"), "opponent": r.get("opponent"),
                             **{f"{prefix}{_snake(k)}": v for k, v in flat.items()}})
        return pd.DataFrame(rows)
    adv, ppa = frame("advanced", "adv_"), frame("ppa_games", "ppa_")
    if adv.empty:
        return ppa
    if ppa.empty:
        return adv
    keys = ["game_id", "season", "week", "season_type", "team", "opponent"]
    return adv.merge(ppa.drop(columns=["season", "week", "season_type", "opponent"]),
                     on=["game_id", "team"], how="outer")[
        keys + [c for c in adv.columns if c not in keys]
        + [c for c in ppa.columns if c not in keys]]


# ---------------------------------------------------------------- team-season
def team_ids(games: pd.DataFrame) -> pd.DataFrame:
    """(season, team) -> team_id from game participants; used for name joins."""
    h = games[["season", "home_team", "home_id", "home_conference", "home_classification"]]
    a = games[["season", "away_team", "away_id", "away_conference", "away_classification"]]
    cols = ["season", "team", "team_id", "conference", "classification"]
    h.columns = a.columns = cols
    t = pd.concat([h, a]).dropna(subset=["team_id"]).drop_duplicates(["season", "team"])
    t["team_id"] = t.team_id.astype("int64")
    return t


def _named(ds: str, fields: dict, year_key: str = "year") -> pd.DataFrame:
    rows = []
    for season, data in _seasons(ds):
        for r in data:
            out = {"season": r.get(year_key, season), "team": r.get("team")}
            flat: dict = {}
            _flat("", r, flat)
            out.update({new: flat.get(old) for old, new in fields.items()})
            rows.append(out)
    return pd.DataFrame(rows, columns=["season", "team", *fields.values()])


def build_coaches() -> pd.DataFrame:
    rows = []
    for season, data in _seasons("coaches"):
        for c in data:
            for s in c.get("seasons") or []:
                if s.get("year") != season:
                    continue
                rows.append({"season": season, "team_id": s.get("teamId"),
                             "team": s.get("school"), "coach_id": c.get("id"),
                             "coach": f"{c.get('firstName')} {c.get('lastName')}",
                             "hire_date": c.get("hireDate"), "games": s.get("games")})
    return pd.DataFrame(rows)


def build_team_season(games: pd.DataFrame) -> pd.DataFrame:
    ids = team_ids(games)
    fbs = ids[ids.classification == "fbs"][["season", "team", "team_id", "conference"]]

    talent = _named("talent", {"talent": "talent"})
    recruit = _named("recruiting", {"rank": "recruiting_rank",
                                    "points": "recruiting_points"})
    ret = _named("returning", {
        "totalPPA": "ret_total_ppa", "percentPPA": "ret_pct_ppa",
        "percentPassingPPA": "ret_pct_passing_ppa",
        "percentReceivingPPA": "ret_pct_receiving_ppa",
        "percentRushingPPA": "ret_pct_rushing_ppa", "usage": "ret_usage",
        "passingUsage": "ret_passing_usage", "receivingUsage": "ret_receiving_usage",
        "rushingUsage": "ret_rushing_usage"}, year_key="season")

    ts = fbs
    for df in (talent, recruit, ret):
        ts = ts.merge(df, on=["season", "team"], how="left")

    # coaches: primary = most games that season; first-year = different coach
    # than last season's primary (for the first season we have, fall back to
    # a hire date within the 12 months before Sept 1).
    co = build_coaches()
    if len(co):
        co = co.sort_values(["season", "team_id", "games"], ascending=[True, True, False])
        n = co.groupby(["season", "team_id"]).coach_id.nunique().rename("n_head_coaches")
        prim = co.drop_duplicates(["season", "team_id"]).set_index(["season", "team_id"])
        prev = prim.coach_id.rename("prev_coach_id").reset_index()
        prev["season"] += 1
        prim = prim.reset_index().merge(prev, on=["season", "team_id"], how="left")
        first_season = prim.season.min()

        def first_year(r):
            if r.season > first_season:
                return pd.NA if pd.isna(r.prev_coach_id) else r.coach_id != r.prev_coach_id
            if not r.hire_date:
                return pd.NA
            hd = pd.to_datetime(r.hire_date, utc=True)
            return hd > pd.Timestamp(f"{r.season - 1}-09-01", tz="UTC")
        prim["coach_first_year"] = prim.apply(first_year, axis=1).astype("boolean")
        prim["coach_first_year_source"] = np.where(prim.season > first_season,
                                                   "prev_season", "hire_date")
        prim = prim.merge(n.reset_index(), on=["season", "team_id"])
        ts = ts.merge(prim[["season", "team_id", "coach_id", "coach", "coach_first_year",
                            "coach_first_year_source", "n_head_coaches"]],
                      on=["season", "team_id"], how="left")

    # transfer portal counts (name match on origin/destination)
    rows = []
    for season, data in _seasons("portal"):
        for r in data:
            rows.append({"season": season, "origin": r.get("origin"),
                         "destination": r.get("destination")})
    pt = pd.DataFrame(rows)
    if len(pt):
        out_ = pt.groupby(["season", "origin"]).size().rename("portal_out")
        in_ = pt.dropna(subset=["destination"]).groupby(["season", "destination"]).size() \
                .rename("portal_in")
        ts = ts.merge(out_.rename_axis(["season", "team"]).reset_index(),
                      on=["season", "team"], how="left")
        ts = ts.merge(in_.rename_axis(["season", "team"]).reset_index(),
                      on=["season", "team"], how="left")
    return ts


def build_benchmarks(games: pd.DataFrame) -> pd.DataFrame:
    ids = team_ids(games)[["season", "team", "team_id"]]
    sp = _named("sp", {"rating": "sp_rating", "ranking": "sp_rank",
                       "offense_rating": "sp_off", "defense_rating": "sp_def",
                       "specialTeams_rating": "sp_st"})
    fpi = _named("fpi", {"fpi": "fpi", "efficiencies_overall": "fpi_eff_overall",
                         "efficiencies_offense": "fpi_eff_off",
                         "efficiencies_defense": "fpi_eff_def",
                         "efficiencies_specialTeams": "fpi_eff_st"})
    elo = _named("elo", {"elo": "elo"})
    b = sp.merge(fpi, on=["season", "team"], how="outer") \
          .merge(elo, on=["season", "team"], how="outer")
    return ids.merge(b, on=["season", "team"], how="right")


# ---------------------------------------------------------------- main
def write(df: pd.DataFrame, name: str) -> None:
    path = CLEAN / f"{name}.parquet"
    df.to_parquet(path, index=False)
    print(f"  {name:<16}{len(df):>9,} rows  {path.stat().st_size / 1e6:6.1f} MB")


def main(argv=None) -> int:
    CLEAN.mkdir(parents=True, exist_ok=True)
    print(f"build_tables {datetime.now():%Y-%m-%d %H:%M} (raw cache only, 0 calls)")
    venues = build_venues()
    lines = build_lines()
    games = build_games(venues, lines)
    write(venues, "venues")
    write(lines, "lines")
    write(games, "games")
    write(build_plays(games), "plays")
    write(build_game_team_stats(), "game_team_stats")
    write(build_team_season(games), "team_season")
    write(build_benchmarks(games), "benchmarks")
    if _raw("weather"):
        print("  weather raw present but no builder yet (Patreon endpoint; off)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
