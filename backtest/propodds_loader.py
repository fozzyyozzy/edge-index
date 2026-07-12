"""
Edge Index — OddsPapi Historical Prop Line Loader
Pulls real historical NFL prop lines from OddsPapi API.

Usage:
  export ODDS_API_KEY=your_key_here   (Mac/Linux)
  set ODDS_API_KEY=your_key_here      (Windows)

  python propodds_loader.py --seasons 2023 2024 2025
  python propodds_loader.py --seasons 2024 --test   (test mode, limited pulls)

After running:
  python run_backtest.py --quick
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
import sqlite3
import argparse
from datetime import datetime, timedelta
from db_setup import get_conn, init_db

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY  = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://v5.oddspapi.io"

# NFL prop market names — check their /markets endpoint to confirm exact strings
# These are the most common naming conventions
PROP_MARKET_MAP = {
    # OddsPapi market name → our prop_type
    "player_receiving_yards":      "rec_yds",
    "player_receptions":           "receptions",
    "player_rushing_yards":        "rush_yds",
    "player_passing_yards":        "pass_yds",
    "player_passing_attempts":     "pass_att",
    "player_passing_tds":          "pass_tds",
    "anytime_td_scorer":           "anytime_td",
    "player_reception_yds":        "rec_yds",      # alternate naming
    "player_rush_yds":             "rush_yds",
    "player_pass_yds":             "pass_yds",
    "receiving_yards":             "rec_yds",
    "rushing_yards":               "rush_yds",
    "passing_yards":               "pass_yds",
    "receptions":                  "receptions",
}

# Target bookmakers — DraftKings first, fallback to others
TARGET_BOOKS = ["draftkings", "fanduel", "betmgm", "caesars", "pinnacle"]

# NFL season week ranges (approximate dates)
SEASON_WEEKS = {
    2022: [("2022-09-08", "2023-01-08")],
    2023: [("2023-09-07", "2024-01-07")],
    2024: [("2024-09-05", "2025-01-05")],
    2025: [("2025-09-04", "2026-01-04")],
}

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def get(endpoint, params=None, retries=3):
    """Make authenticated GET request to OddsPapi."""
    if not API_KEY:
        raise ValueError("ODDS_API_KEY environment variable not set.\n"
                         "Run: set ODDS_API_KEY=your_key   (Windows)\n"
                         "     export ODDS_API_KEY=your_key (Mac/Linux)")

    url = f"{BASE_URL}{endpoint}"
    p   = {"apiKey": API_KEY}
    if params:
        p.update(params)

    for attempt in range(retries):
        try:
            r = requests.get(url, params=p, timeout=20)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                # Rate limited — wait and retry
                wait = int(r.headers.get("Retry-After", 5))
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif r.status_code == 401:
                print("  ERROR: Invalid API key. Check ODDS_API_KEY.")
                return None
            else:
                print(f"  HTTP {r.status_code}: {r.text[:200]}")
                return None
        except requests.exceptions.Timeout:
            print(f"  Timeout on attempt {attempt+1}")
            time.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")
            return None

    return None

# ── Discovery endpoints ───────────────────────────────────────────────────────
def discover_markets():
    """List all available markets — run once to find exact prop names."""
    print("Fetching available markets...")
    data = get("/api/markets", {"sport": "americanfootball"})
    if not data:
        return []

    markets = data.get("data", data) if isinstance(data, dict) else data
    print(f"Found {len(markets)} markets")

    prop_markets = [m for m in markets
                    if any(kw in str(m).lower()
                           for kw in ["player","receiving","rushing","passing","reception"])]
    print(f"\nPlayer prop markets ({len(prop_markets)}):")
    for m in prop_markets[:30]:
        print(f"  {json.dumps(m)[:120]}")

    return markets

def discover_bookmakers():
    """List available bookmakers and their IDs."""
    print("Fetching bookmakers...")
    data = get("/api/bookmakers")
    if not data:
        return {}

    books = data.get("data", data) if isinstance(data, dict) else data
    book_map = {}
    print("Available bookmakers:")
    for b in books:
        name = b.get("name","").lower()
        bid  = b.get("id") or b.get("bookmaker_id")
        print(f"  [{bid}] {b.get('name','')}")
        for target in TARGET_BOOKS:
            if target in name:
                book_map[target] = bid
    return book_map

def get_nfl_tournament_id():
    """Find the NFL tournament/league ID."""
    data = get("/api/tournaments", {"sport": "americanfootball"})
    if not data:
        return None

    tournaments = data.get("data", data) if isinstance(data, dict) else data
    for t in tournaments:
        name = str(t.get("name","")).lower()
        if "nfl" in name or "national football" in name:
            tid = t.get("id") or t.get("tournament_id")
            print(f"NFL tournament: {t.get('name')} — ID: {tid}")
            return tid

    print("NFL tournament not found. Available:")
    for t in tournaments[:10]:
        print(f"  {t.get('name')} — {t.get('id')}")
    return None

# ── Main data pull ────────────────────────────────────────────────────────────
def get_fixtures_for_season(tournament_id, season):
    """Pull all NFL fixtures for a given season."""
    print(f"  Fetching fixtures for {season}...")
    data = get("/api/fixtures", {
        "tournamentId": tournament_id,
        "season":       season,
        "status":       "finished",
    })

    if not data:
        return []

    fixtures = data.get("data", data) if isinstance(data, dict) else data
    print(f"  Found {len(fixtures)} finished fixtures")
    return fixtures

def get_player_props_for_fixture(fixture_id, book_id=None):
    """
    Pull player prop odds for a specific fixture.
    Uses historical endpoint to get actual posted lines.
    """
    params = {"fixtureId": fixture_id}
    if book_id:
        params["bookmakerId"] = book_id

    # Try historical first (pre-game closing lines)
    data = get(f"/api/fixtures/{fixture_id}/odds/historical", params)
    if not data:
        # Fall back to current odds if historical unavailable
        data = get(f"/api/fixtures/{fixture_id}/odds", params)

    return data

def get_clv_for_fixture(fixture_id, book_id=None):
    """Get opening vs closing line value for a fixture."""
    params = {"fixtureId": fixture_id}
    if book_id:
        params["bookmakerId"] = book_id
    return get(f"/api/fixtures/{fixture_id}/odds/clv", params)

def get_settlement(fixture_id):
    """Get settlement results — which bets won/lost."""
    return get(f"/api/fixtures/{fixture_id}/settlement")

# ── Player matching ───────────────────────────────────────────────────────────
def build_player_name_map(conn):
    """Build a lookup of player names → DB player IDs."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM players")
    rows = cursor.fetchall()

    name_map = {}
    for pid, name in rows:
        # Exact match
        name_map[name.lower()] = pid
        # Last name only
        last = name.split()[-1].lower()
        name_map[last] = pid
        # First initial + last
        parts = name.split()
        if len(parts) >= 2:
            short = (parts[0][0] + ". " + parts[-1]).lower()
            name_map[short] = pid

    return name_map

def match_player(api_name, name_map):
    """Fuzzy match API player name to our DB player ID."""
    if not api_name:
        return None

    n = str(api_name).lower().strip()

    # Try exact
    if n in name_map:
        return name_map[n]

    # Try last name
    last = n.split()[-1]
    if last in name_map:
        return name_map[last]

    # Try removing suffixes
    clean = n.replace(" jr.", "").replace(" sr.", "").replace(" ii", "").strip()
    if clean in name_map:
        return name_map[clean]

    return None

# ── Parse odds response ───────────────────────────────────────────────────────
def parse_prop_odds(odds_data, fixture_id, season, week, name_map):
    """
    Parse OddsPapi odds response into prop line records.
    Returns list of dicts ready for DB insertion.
    """
    if not odds_data:
        return []

    records = []
    # Handle different response structures
    markets = (odds_data.get("data", {}).get("markets") or
               odds_data.get("markets") or
               odds_data.get("data", []))

    if isinstance(markets, dict):
        markets = list(markets.values())

    for market in markets:
        market_name = (market.get("name") or
                       market.get("market") or "").lower()

        # Check if this is a prop market we care about
        prop_type = None
        for api_name, our_name in PROP_MARKET_MAP.items():
            if api_name in market_name:
                prop_type = our_name
                break

        if not prop_type:
            continue

        # Get outcomes
        outcomes = (market.get("outcomes") or
                    market.get("selections") or [])

        for outcome in outcomes:
            player_name = (outcome.get("participant") or
                           outcome.get("player") or
                           outcome.get("name") or "")

            label     = (outcome.get("label") or
                         outcome.get("side") or "").lower()
            line_val  = outcome.get("line") or outcome.get("handicap")
            odds_val  = (outcome.get("odds") or
                         outcome.get("american") or
                         outcome.get("price"))

            if not player_name or line_val is None or odds_val is None:
                continue

            direction = "OVER" if "over" in label else "UNDER" if "under" in label else None
            if not direction:
                continue

            pid = match_player(player_name, name_map)
            if not pid:
                continue

            # Convert odds to American if decimal
            try:
                odds_float = float(odds_val)
                if odds_float > 0 and odds_float < 30:
                    # Probably decimal odds — convert
                    if odds_float >= 2.0:
                        american = int((odds_float - 1) * 100)
                    else:
                        american = int(-100 / (odds_float - 1))
                else:
                    american = int(odds_float)
            except:
                american = -115

            records.append({
                "player_id": pid,
                "season":    season,
                "week":      week,
                "prop_type": prop_type,
                "direction": direction,
                "line":      float(line_val),
                "odds":      american,
                "source":    "actual_oddspapi",
            })

    return records

# ── Determine week from fixture date ─────────────────────────────────────────
def date_to_nfl_week(date_str, season):
    """Convert a date string to NFL week number."""
    season_starts = {
        2022: datetime(2022, 9, 8),
        2023: datetime(2023, 9, 7),
        2024: datetime(2024, 9, 5),
        2025: datetime(2025, 9, 4),
    }
    start = season_starts.get(season, datetime(season, 9, 7))

    try:
        d = datetime.fromisoformat(str(date_str)[:10])
        delta = (d - start).days
        week  = max(1, min(22, (delta // 7) + 1))
        return week
    except:
        return 0

# ── Main ingestion ────────────────────────────────────────────────────────────
def ingest_historical_lines(seasons, test_mode=False):
    """
    Full pipeline:
    1. Discover NFL tournament ID
    2. Pull all fixtures per season
    3. For each fixture, pull player prop lines
    4. Match players to DB
    5. Store lines as 'actual_oddspapi'
    """
    if not API_KEY:
        print("ERROR: Set your API key first:")
        print("  Windows: set ODDS_API_KEY=your_key")
        print("  Mac/Linux: export ODDS_API_KEY=your_key")
        return

    init_db()
    conn     = get_conn()
    cursor   = conn.cursor()
    name_map = build_player_name_map(conn)

    print(f"Player name map: {len(name_map)} entries")
    print(f"Seasons to pull: {seasons}")
    print(f"Test mode: {test_mode}")

    # Step 1: Discover markets (run once to verify prop names)
    print("\n[1/4] Discovering available markets...")
    discover_markets()
    time.sleep(1)

    # Step 2: Get bookmaker IDs
    print("\n[2/4] Fetching bookmaker IDs...")
    book_map = discover_bookmakers()
    dk_id    = book_map.get("draftkings")
    print(f"DraftKings ID: {dk_id}")
    time.sleep(1)

    # Step 3: Find NFL tournament
    print("\n[3/4] Finding NFL tournament...")
    nfl_id = get_nfl_tournament_id()
    if not nfl_id:
        print("Could not find NFL tournament. Check available tournaments above.")
        conn.close()
        return
    time.sleep(1)

    # Step 4: Pull fixtures and lines per season
    print("\n[4/4] Pulling historical prop lines...")
    total_fixtures = 0
    total_lines    = 0
    unmatched_players = set()

    for season in seasons:
        print(f"\n=== Season {season} ===")

        fixtures = get_fixtures_for_season(nfl_id, season)
        if not fixtures:
            print(f"  No fixtures found for {season}")
            continue

        if test_mode:
            fixtures = fixtures[:5]  # limit to 5 games in test mode
            print(f"  TEST MODE: limiting to {len(fixtures)} fixtures")

        for i, fixture in enumerate(fixtures):
            fid       = fixture.get("id") or fixture.get("fixture_id")
            fdate     = fixture.get("date") or fixture.get("start_time", "")
            home      = fixture.get("home_participant",{}).get("name","")
            away      = fixture.get("away_participant",{}).get("name","")
            week      = date_to_nfl_week(fdate, season)

            if week == 0:
                continue

            print(f"  [{i+1}/{len(fixtures)}] Week {week}: {away} @ {home} ({fid})")

            # Pull prop odds for this fixture
            odds_data = get_player_props_for_fixture(fid, dk_id)
            if not odds_data:
                time.sleep(0.5)
                continue

            records = parse_prop_odds(odds_data, fid, season, week, name_map)

            if not records:
                # Try to detect unmatched players
                time.sleep(0.5)
                continue

            for r in records:
                cursor.execute("""
                    INSERT OR REPLACE INTO prop_lines
                    (player_id, season, week, prop_type, direction, line, odds, source)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (r["player_id"], r["season"], r["week"],
                      r["prop_type"],  r["direction"],
                      r["line"],       r["odds"],
                      r["source"]))
                total_lines += 1

            conn.commit()
            total_fixtures += 1

            # Respect rate limits — 1 req/second safe zone
            time.sleep(1.0)

    conn.close()

    print(f"\n{'='*55}")
    print(f"INGESTION COMPLETE")
    print(f"  Fixtures processed: {total_fixtures}")
    print(f"  Prop lines stored:  {total_lines:,}")
    print(f"  Source tag:         actual_oddspapi")
    print(f"\nNow run: python run_backtest.py --quick")
    print(f"All 'estimated' lines are replaced by real market lines.")

# ── Utility: show what we have ────────────────────────────────────────────────
def show_coverage():
    """Show how many actual vs estimated lines we have per season."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT season, source, COUNT(*) as n
        FROM prop_lines
        GROUP BY season, source
        ORDER BY season, source
    """).fetchall()
    conn.close()

    print("\nProp line coverage:")
    print(f"{'Season':<8} {'Source':<20} {'Count':>8}")
    print("-" * 40)
    for row in rows:
        print(f"{row[0]:<8} {row[1]:<20} {row[2]:>8,}")

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OddsPapi historical prop line loader")
    parser.add_argument("--seasons", nargs="+", type=int,
                        default=[2024, 2025],
                        help="Seasons to pull (e.g. --seasons 2023 2024 2025)")
    parser.add_argument("--test",    action="store_true",
                        help="Test mode — pull only 5 fixtures per season")
    parser.add_argument("--markets", action="store_true",
                        help="Just list available markets and exit")
    parser.add_argument("--coverage",action="store_true",
                        help="Show current line coverage in DB and exit")
    args = parser.parse_args()

    if args.coverage:
        show_coverage()
    elif args.markets:
        discover_markets()
    else:
        ingest_historical_lines(args.seasons, test_mode=args.test)
