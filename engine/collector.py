"""
Edge Index v2 — timestamped PREGAME odds collector (The Odds API).

The rule that fixes everything that poisoned the 2025 data: an event
whose commence_time has passed is NEVER pulled. Every row stores its
pull timestamp, so closing line = last snapshot before kickoff, and
CLV is computable for every posted play.

Collects mainlines AND full alt ladders (Tim's 40+/50+/60+ depths).

Usage:
  set ODDS_API_KEY=your_key
  python engine\\collector.py --sport americanfootball_nfl
  python engine\\collector.py --sport baseball_mlb
  python engine\\collector.py --ladders            (show latest alt ladders)
Schedule 2-3x daily via agent\\collect_odds.bat.
"""
from __future__ import annotations
import argparse, csv, os, re, sqlite3, sys
from datetime import datetime, timezone

# Every run is logged to automation/lines/odds_usage.csv (the pipeline's ledger) as slate "collector:<sport>", with the
# requests it actually spent. The collector stops for the week once its own spend reaches COLLECTOR_WEEKLY_BUDGET
# (default 1000), so it can't eat the pipeline's share of the weekly cap. Error messages never include the API key.

BASE = "https://api.the-odds-api.com/v4"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "..", "data", "odds_snapshots.db")
BOOKS = "draftkings,fanduel,betmgm"
MARKETS = {
    "americanfootball_nfl": [
        "player_pass_yds", "player_pass_attempts",
        "player_rush_yds", "player_rush_attempts",
        "player_receptions", "player_reception_yds",
        "player_pass_yds_alternate", "player_rush_yds_alternate",
        "player_reception_yds_alternate", "player_receptions_alternate"],
    "baseball_mlb": [
        "pitcher_strikeouts", "pitcher_strikeouts_alternate",
        "batter_total_bases", "batter_hits"],
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots(
  pull_ts TEXT NOT NULL, sport TEXT NOT NULL, event_id TEXT NOT NULL,
  commence TEXT NOT NULL, home TEXT, away TEXT, book TEXT NOT NULL,
  market TEXT NOT NULL, player TEXT, side TEXT, line REAL, odds INTEGER,
  UNIQUE(pull_ts, event_id, book, market, player, side, line));
CREATE INDEX IF NOT EXISTS ix_snap ON snapshots(sport, event_id, market, player);
"""


LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "automation", "lines", "odds_usage.csv")
LEDGER_COLS = ["pulled_at", "season", "week", "slate", "events", "cost", "remaining"]


def _redact(text) -> str:
    """never let the key reach a log: requests' errors quote the full URL, query string included"""
    return re.sub(r"apiKey=[^&\s'\")]+", "apiKey=REDACTED", str(text))


def _get(url, params, session=None):
    import requests
    try:
        return (session or requests).get(url, params=params, timeout=30)
    except requests.RequestException as ex:                  # `from None`: drop the chained traceback that shows the URL
        raise RuntimeError(_redact(f"{type(ex).__name__}: {ex}")) from None


def _nfl_week():
    """(season, week) for the ledger, from the nflverse schedule; (season, 0) if that can't be fetched"""
    season = datetime.now(timezone.utc).year
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "automation", "pipeline"))
        from nfl_week import week_for
        return season, week_for(season, "current")
    except Exception:
        return season, 0


def _collector_spend(season, week):
    if not os.path.exists(LEDGER): return 0
    with open(LEDGER, newline="") as f:
        return sum(int(r["cost"] or 0) for r in csv.DictReader(f)
                   if r["slate"].startswith("collector") and r["season"] == str(season) and r["week"] == str(week))


def _log(row):
    new = not os.path.exists(LEDGER)
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLS)
        if new: w.writeheader()
        w.writerow(row)


def collect(sport: str, key: str, books: str = BOOKS) -> None:
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    now = datetime.now(timezone.utc)
    pull = now.isoformat(timespec="seconds")
    season, week = _nfl_week()
    budget = int(os.environ.get("COLLECTOR_WEEKLY_BUDGET", "1000"))
    spent = _collector_spend(season, week)
    if spent >= budget:
        print(f"[{pull}] {sport}: collector already spent {spent}/{budget} this week (wk {week}); skipping")
        return
    r = _get(f"{BASE}/sports/{sport}/events", {"apiKey": key})   # the events list is free
    if r.status_code != 200:
        sys.exit(_redact(f"events: HTTP {r.status_code}"))
    stored = skipped = cost = pulled = 0
    remaining = "?"
    for ev in r.json():
        commence = datetime.fromisoformat(
            ev["commence_time"].replace("Z", "+00:00"))
        if commence <= now:
            skipped += 1
            continue                       # PREGAME ONLY — no exceptions
        ro = _get(f"{BASE}/sports/{sport}/events/{ev['id']}/odds",
                  {"apiKey": key, "regions": "us", "oddsFormat": "american",
                   "markets": ",".join(MARKETS[sport]), "bookmakers": books})
        if ro.status_code != 200:
            print(f"  skip {ev['id']}: HTTP {ro.status_code}")
            continue
        remaining = ro.headers.get("x-requests-remaining", "?")
        cost += int(ro.headers.get("x-requests-last", 0) or 0); pulled += 1
        for bk in ro.json().get("bookmakers", []):
            for m in bk.get("markets", []):
                for o in m.get("outcomes", []):
                    con.execute(
                        "INSERT OR IGNORE INTO snapshots VALUES "
                        "(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (pull, sport, ev["id"], ev["commence_time"],
                         ev["home_team"], ev["away_team"], bk["key"],
                         m["key"], o.get("description"), o.get("name"),
                         o.get("point"), o.get("price")))
                    stored += 1
        con.commit()
    _log(dict(pulled_at=now.isoformat(timespec="minutes"), season=season, week=week, slate=f"collector:{sport}",
              events=pulled, cost=cost, remaining=remaining))
    print(f"[{pull}] {sport}: {stored} rows stored, {skipped} started events skipped, "
          f"{cost} requests spent (collector week total {spent + cost}/{budget}), API quota left: {remaining}")


def closing_lines(sport: str) -> list[tuple]:
    """Last pregame snapshot per event/book/market/player/side/line."""
    con = sqlite3.connect(DB)
    return con.execute("""
        SELECT event_id, book, market, player, side, line, odds,
               MAX(pull_ts) last_pull
        FROM snapshots WHERE sport=? AND pull_ts < commence
        GROUP BY event_id, book, market, player, side, line""",
        (sport,)).fetchall()


def show_ladders(sport: str, min_depths: int = 3) -> None:
    """Print alt ladders from the most recent pull (Tim's 40+/50+/60+ view)."""
    con = sqlite3.connect(DB)
    rows = con.execute("""
        WITH latest AS (SELECT MAX(pull_ts) t FROM snapshots WHERE sport=?)
        SELECT player, market, book, line, odds FROM snapshots, latest
        WHERE sport=? AND pull_ts=latest.t AND market LIKE '%alternate%'
          AND side='Over' ORDER BY player, market, book, line""",
        (sport, sport)).fetchall()
    cur, ladder = None, []
    for p, m, b, ln, od in rows:
        if (p, m, b) != cur:
            if cur and len(ladder) >= min_depths:
                print(f"{cur[0]:<24} {cur[1]:<28} {cur[2]:<10} " +
                      "  ".join(f"{l}+ ({o:+d})" for l, o in ladder))
            cur, ladder = (p, m, b), []
        ladder.append((ln, od))
    if cur and len(ladder) >= min_depths:
        print(f"{cur[0]:<24} {cur[1]:<28} {cur[2]:<10} " +
              "  ".join(f"{l}+ ({o:+d})" for l, o in ladder))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sport", default="americanfootball_nfl",
                    choices=list(MARKETS))
    ap.add_argument("--books", default=BOOKS)
    ap.add_argument("--ladders", action="store_true")
    args = ap.parse_args()
    if args.ladders:
        show_ladders(args.sport)
        sys.exit(0)
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        sys.exit("Set ODDS_API_KEY first")
    collect(args.sport, key, args.books)
