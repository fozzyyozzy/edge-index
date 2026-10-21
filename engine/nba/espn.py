"""ESPN public JSON: the single source for NBA box scores, historical and daily (Phase 1 decision, 2026-10-21).

    scoreboard(date)   -> regular-season games on an ET date (NBA Cup final and All-Star games excluded)
    summary(event_id)  -> trimmed summary JSON, cached gzipped under data/nba/raw/espn/ (gitignored)
    player_rows(summ)  -> one dict per rostered player (DNPs included, played=False)

Works from GitHub Actions (verified in Phase 0); stats.nba.com and cdn.nba.com do not.
"""
from __future__ import annotations
import gzip
import json
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from engine.nba import http
from engine.nba.teams import from_espn

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "nba" / "raw" / "espn"
ET = ZoneInfo("America/New_York")
REGULAR = 2                           # ESPN season.type
NOT_COUNTED = {"CC", "ALLSTAR"}       # competition.type.abbreviation ESPN files under season.type 2: the NBA Cup final
                                      # and All-Star games are not among a team's 82
KEEP = ("header", "boxscore", "gameInfo")
ISSUES: list[dict] = []               # data defects found while parsing (written by backfill)
PAUSE = 0.15                          # seconds between uncached calls; ESPN has no published limit


def season_label(espn_year: int) -> str:
    """ESPN labels a season by its ending year: 2024 -> '2023-24'."""
    return f"{espn_year - 1}-{str(espn_year)[-2:]}"


def scoreboard(day: date) -> list[dict]:
    """Final regular-season games tipping on `day` (ET), as small dicts."""
    d = http.get_json(f"{BASE}/scoreboard", {"dates": day.strftime("%Y%m%d"), "limit": 50})
    out = []
    for e in d.get("events", []):
        comp = e["competitions"][0]
        if e["season"]["type"] != REGULAR or comp.get("type", {}).get("abbreviation") in NOT_COUNTED:
            continue
        out.append({"event_id": e["id"], "season": season_label(e["season"]["year"]),
                    "status": comp["status"]["type"]["name"], "commence": comp["date"]})
    return out


def summary(event_id: str, refresh: bool = False) -> dict:
    """Trimmed /summary for one game; cached once the game is final."""
    path = CACHE / f"{event_id}.json.gz"
    if path.exists() and not refresh:
        return json.loads(gzip.decompress(path.read_bytes()))
    full = http.get_json(f"{BASE}/summary", {"event": event_id})
    time.sleep(PAUSE)
    trimmed = {k: full.get(k) for k in KEEP}
    if trimmed["header"]["competitions"][0]["status"]["type"]["name"] == "STATUS_FINAL":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(json.dumps(trimmed).encode()))
    return trimmed


def _int(s) -> int:
    try:
        return int(str(s).split("-")[0])
    except ValueError:
        return 0


def game_info(summ: dict) -> dict:
    """Game-level facts: ET date, teams, final score, overtime periods."""
    comp = summ["header"]["competitions"][0]
    side = {c["homeAway"]: c for c in comp["competitors"]}
    periods = max(len(c.get("linescores", [])) for c in comp["competitors"])
    tip = datetime.fromisoformat(comp["date"].replace("Z", "+00:00"))
    return {"game_id": summ["header"]["id"], "season": season_label(summ["header"]["season"]["year"]),
            "date": tip.astimezone(ET).date().isoformat(), "commence": comp["date"],
            "home": from_espn(side["home"]["team"]["abbreviation"]),
            "away": from_espn(side["away"]["team"]["abbreviation"]),
            "home_score": _int(side["home"]["score"]), "away_score": _int(side["away"]["score"]),
            "n_ot": max(periods - 4, 0), "neutral": bool(comp.get("neutralSite")),
            "status": comp["status"]["type"]["name"]}


def player_rows(summ: dict) -> list[dict]:
    g = game_info(summ)
    rows = []
    for team in summ["boxscore"]["players"]:
        code = from_espn(team["team"]["abbreviation"])
        home = code == g["home"]
        block = team["statistics"][0]
        idx = {k: i for i, k in enumerate(block["keys"])}
        for a in block["athletes"]:
            s = a.get("stats") or []
            played = bool(s) and not a.get("didNotPlay")
            if "id" not in a["athlete"]:
                # ESPN sometimes lists a player with no athlete record (and '--' minutes). Unkeyable: dropped and
                # logged; the game's box no longer sums to the final score, which the data gate allows only for
                # games in data/nba/espn_issues.csv. Never filled in from another source.
                ISSUES.append({"game_id": g["game_id"], "date": g["date"], "team": code,
                               "short_name": a["athlete"].get("shortName"), "did_not_play": bool(a.get("didNotPlay")),
                               "stats": "|".join(s), "issue": "athlete without ESPN id"})
                continue
            v =(lambda k: _int(s[idx[k]])) if played else (lambda k: 0)
            pts, reb, ast = v("points"), v("rebounds"), v("assists")
            rows.append({
                "game_id": g["game_id"], "date": g["date"], "season": g["season"],
                "espn_id": a["athlete"]["id"], "player": a["athlete"]["displayName"],
                "position": (a["athlete"].get("position") or {}).get("abbreviation"),
                "team": code, "opp": g["away"] if home else g["home"], "home_away": "H" if home else "A",
                "starter": bool(a.get("starter")), "played": played,
                "dnp_reason": None if played else (a.get("reason") or None),
                "minutes": v("minutes"), "pts": pts, "reb": reb, "ast": ast,
                "fg3m": v("threePointFieldGoalsMade-threePointFieldGoalsAttempted"),
                "fg3a": _int(s[idx["threePointFieldGoalsMade-threePointFieldGoalsAttempted"]].split("-")[1]) if played else 0,
                "stl": v("steals"), "blk": v("blocks"),
                "pra": pts + reb + ast, "pr": pts + reb, "pa": pts + ast, "ra": reb + ast,
                "team_score": g["home_score"] if home else g["away_score"],
                "opp_score": g["away_score"] if home else g["home_score"],
                "n_ot": g["n_ot"],
            })
    return rows
