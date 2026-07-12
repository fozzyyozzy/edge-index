import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Edge Index — The Odds API Full Historical Loader
Pulls real NFL player prop lines from the-odds-api.com

Markets: 12 main + 9 alternate + 1 Q1 + 4 combo = 26 markets
Books: DraftKings, FanDuel, BetMGM
Seasons: 2023, 2024, 2025

Setup:
  set ODDS_API_KEY=your_key   (Windows)
  export ODDS_API_KEY=your_key (Mac/Linux)

Usage:
  python odds_api_loader.py --check
  python odds_api_loader.py --seasons 2024 --test
  python odds_api_loader.py --seasons 2023 2024 2025
  python odds_api_loader.py --coverage
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, json, time, argparse
from datetime import datetime, timedelta
from db_setup import get_conn, init_db

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY  = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT    = "americanfootball_nfl"
REGION   = "us"
TARGET_BOOKS = ["draftkings", "fanduel", "betmgm"]

# ── Correct market keys from official docs ────────────────────────────────────
MAIN_MARKETS = [
    "player_pass_yds",
    "player_pass_attempts",
    "player_pass_tds",
    "player_pass_completions",
    "player_pass_interceptions",
    "player_rush_yds",
    "player_rush_attempts",
    "player_rush_tds",
    "player_receptions",
    "player_reception_yds",
    "player_reception_tds",
    "player_anytime_td",
]

ALT_MARKETS = [
    "player_reception_yds_alternate",
    "player_receptions_alternate",
    "player_reception_tds_alternate",
    "player_rush_yds_alternate",
    "player_rush_attempts_alternate",
    "player_rush_tds_alternate",
    "player_pass_yds_alternate",
    "player_pass_attempts_alternate",
    "player_pass_tds_alternate",
]

COMBO_MARKETS = [
    "player_pass_rush_reception_yds",
    "player_pass_rush_reception_tds",
    "player_rush_reception_yds",
    "player_rush_reception_tds",
]

Q1_MARKETS = [
    "player_pass_yds_q1",
]

# All batches — pull in groups to avoid URL length issues
MARKET_BATCHES = [
    MAIN_MARKETS[:6],
    MAIN_MARKETS[6:],
    ALT_MARKETS[:5],
    ALT_MARKETS[5:],
    COMBO_MARKETS,
    Q1_MARKETS,
]

MARKET_TO_PROP = {
    "player_pass_yds":                   "pass_yds",
    "player_pass_attempts":              "pass_att",
    "player_pass_tds":                   "pass_tds",
    "player_pass_completions":           "pass_cmp",
    "player_pass_interceptions":         "pass_int",
    "player_rush_yds":                   "rush_yds",
    "player_rush_attempts":              "rush_att",
    "player_rush_tds":                   "rush_tds",
    "player_receptions":                 "receptions",
    "player_reception_yds":              "rec_yds",
    "player_reception_tds":              "rec_tds",
    "player_anytime_td":                 "anytime_td",
    "player_reception_yds_alternate":    "rec_yds_alt",
    "player_receptions_alternate":       "receptions_alt",
    "player_reception_tds_alternate":    "rec_tds_alt",
    "player_rush_yds_alternate":         "rush_yds_alt",
    "player_rush_attempts_alternate":    "rush_att_alt",
    "player_rush_tds_alternate":         "rush_tds_alt",
    "player_pass_yds_alternate":         "pass_yds_alt",
    "player_pass_attempts_alternate":    "pass_att_alt",
    "player_pass_tds_alternate":         "pass_tds_alt",
    "player_pass_rush_reception_yds":    "combo_yds",
    "player_pass_rush_reception_tds":    "combo_tds",
    "player_rush_reception_yds":         "rush_rec_yds",
    "player_rush_reception_tds":         "rush_rec_tds",
    "player_pass_yds_q1":                "pass_yds_q1",
}

SEASON_STARTS = {
    2023: "2023-09-07",
    2024: "2024-09-05",
    2025: "2025-09-04",
}

# ── HTTP ──────────────────────────────────────────────────────────────────────
session = requests.Session()

def get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    p   = {"apiKey": API_KEY}
    if params:
        p.update(params)

    for attempt in range(3):
        try:
            r = session.get(url, params=p, timeout=20)
            rem  = r.headers.get("x-requests-remaining", 0)
            used = r.headers.get("x-requests-used", 0)
            cost = r.headers.get("x-requests-last", 0)

            if r.status_code == 200:
                return r.json(), int(rem or 0), int(used or 0), int(cost or 0)
            elif r.status_code == 401:
                print("  ERROR: Invalid API key")
                return None, 0, 0, 0
            elif r.status_code == 422:
                return None, 0, 0, 0  # Invalid market for this event — skip silently
            elif r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 5))
                print(f"  Rate limited — waiting {wait}s")
                time.sleep(wait)
            else:
                return None, 0, 0, 0
        except Exception as e:
            time.sleep(2)
    return None, 0, 0, 0

# ── Player matching ───────────────────────────────────────────────────────────
def build_name_map(conn):
    rows = conn.execute("SELECT id, name FROM players").fetchall()
    m    = {}
    for pid, name in rows:
        m[name.lower().strip()] = pid
        parts = name.split()
        m[parts[-1].lower()] = pid
        if len(parts) >= 2:
            m[(parts[0][0] + ". " + parts[-1]).lower()] = pid
        clean = name.lower()
        for s in [" jr.", " sr.", " ii", " iii", " iv"]:
            clean = clean.replace(s, "")
        m[clean.strip()] = pid
    return m

def match_player(api_name, name_map):
    if not api_name:
        return None
    n = str(api_name).lower().strip()
    if n in name_map:
        return name_map[n]
    last = n.split()[-1]
    if last in name_map:
        return name_map[last]
    clean = n
    for s in [" jr.", " sr.", " ii", " iii", " iv"]:
        clean = clean.replace(s, "")
    if clean.strip() in name_map:
        return name_map[clean.strip()]
    return None

# ── Week / date helpers ───────────────────────────────────────────────────────
def date_to_week(date_str, season):
    start = datetime.fromisoformat(SEASON_STARTS.get(season, f"{season}-09-07"))
    try:
        d     = datetime.fromisoformat(str(date_str)[:10])
        delta = (d - start).days
        return max(1, min(22, (delta // 7) + 1))
    except:
        return 0

def game_query_time(kickoff_str):
    """
    Return timestamp 2 hours before kickoff.
    This is when props are fully posted on all books.
    """
    try:
        kickoff   = datetime.fromisoformat(kickoff_str[:19].replace("Z", ""))
        query_time = kickoff - timedelta(hours=2)
        return query_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    except:
        return kickoff_str[:10] + "T14:00:00Z"

# ── Get historical events for a week ─────────────────────────────────────────
def get_week_events(season, week):
    """
    Get all NFL games for a given week using historical events endpoint.
    Query on the Sunday of that week.
    """
    start  = datetime.fromisoformat(SEASON_STARTS[season])
    sunday = start + timedelta(weeks=week - 1, days=3)  # Thursday + 3 = Sunday
    date_z = sunday.strftime("%Y-%m-%dT18:00:00Z")

    data, rem, used, cost = get(
        f"/historical/sports/{SPORT}/events",
        {"date": date_z, "dateFormat": "iso"}
    )
    if not data:
        return [], rem

    events = data.get("data", [])

    # Filter to games that start within this week window
    week_start = start + timedelta(weeks=week - 1)
    week_end   = week_start + timedelta(days=8)

    week_events = []
    for e in events:
        ct = e.get("commence_time", "")[:10]
        try:
            d = datetime.fromisoformat(ct)
            if week_start <= d <= week_end:
                week_events.append(e)
        except:
            pass

    return week_events, rem

# ── Parse outcomes from historical event odds response ────────────────────────
def parse_outcomes(response_data, season, week, name_map):
    """
    The historical event odds response is:
    {
      "timestamp": "...",
      "data": {           ← single game object, NOT a list
        "bookmakers": [...]
      }
    }
    """
    if not response_data:
        return []

    # Unwrap the snapshot envelope
    game_data  = response_data.get("data", {})
    bookmakers = game_data.get("bookmakers", [])

    records = []
    for bm in bookmakers:
        book_key = bm.get("key", "")
        if book_key not in TARGET_BOOKS:
            continue

        for market in bm.get("markets", []):
            market_key = market.get("key", "")
            prop_type  = MARKET_TO_PROP.get(market_key)
            if not prop_type:
                continue

            for outcome in market.get("outcomes", []):
                # Player name is in 'description' field for prop markets
                player_name = outcome.get("description", "")
                direction   = outcome.get("name", "").upper()
                line        = outcome.get("point")
                price       = outcome.get("price")

                if not player_name or line is None or price is None:
                    continue
                if direction not in ("OVER", "UNDER"):
                    continue

                pid = match_player(player_name, name_map)
                if not pid:
                    continue

                # Convert decimal to American if needed
                try:
                    price_f = float(price)
                    if 1.0 < price_f < 30.0:  # looks like decimal odds
                        if price_f >= 2.0:
                            american = int((price_f - 1) * 100)
                        else:
                            american = int(-100 / (price_f - 1))
                    else:
                        american = int(price_f)
                except:
                    american = -115

                records.append({
                    "player_id": pid,
                    "season":    season,
                    "week":      week,
                    "prop_type": prop_type,
                    "direction": direction,
                    "line":      float(line),
                    "odds":      american,
                    "source":    f"actual_{book_key}",
                })

    return records

# ── Pull one game's props ─────────────────────────────────────────────────────
def pull_game(event_id, kickoff, season, week, name_map, cursor, tracker):
    """Pull all prop markets for one game."""
    query_time = game_query_time(kickoff)
    stored     = 0

    for batch in MARKET_BATCHES:
        if not batch:
            continue

        data, rem, used, cost = get(
            f"/historical/sports/{SPORT}/events/{event_id}/odds",
            {
                "date":       query_time,
                "regions":    REGION,
                "markets":    ",".join(batch),
                "oddsFormat": "american",
            }
        )

        tracker["credits_used"]      += cost
        tracker["credits_remaining"]  = rem

        if not data:
            time.sleep(0.3)
            continue

        records = parse_outcomes(data, season, week, name_map)

        for r in records:
            cursor.execute("""
                INSERT OR REPLACE INTO prop_lines
                (player_id, season, week, prop_type,
                 direction, line, odds, source)
                VALUES (?,?,?,?,?,?,?,?)
            """, (r["player_id"], r["season"], r["week"],
                  r["prop_type"],  r["direction"],
                  r["line"],       r["odds"], r["source"]))
            stored += 1

        time.sleep(0.4)

    return stored

# ── Main ingestion ────────────────────────────────────────────────────────────
def ingest_seasons(seasons, test_mode=False):
    if not API_KEY:
        print("Set ODDS_API_KEY first.")
        return

    init_db()
    conn     = get_conn()
    cursor   = conn.cursor()
    name_map = build_name_map(conn)

    tracker = {"credits_used": 0, "credits_remaining": 0}
    total_lines = 0
    total_games = 0

    print(f"Players in DB:  {len(set(name_map.values()))}")
    print(f"Seasons:        {seasons}")
    print(f"Market batches: {sum(len(b) for b in MARKET_BATCHES)} markets total")
    print(f"Books:          {', '.join(TARGET_BOOKS)}")

    for season in seasons:
        if season < 2023:
            print(f"Skipping {season} — player props available from 2023-05-03")
            continue

        print(f"\n{'='*55}")
        print(f"SEASON {season}")
        print(f"{'='*55}")

        weeks = range(1, 3) if test_mode else range(1, 23)

        for week in weeks:
            events, rem = get_week_events(season, week)
            tracker["credits_remaining"] = rem

            if not events:
                continue

            print(f"\nWeek {week}: {len(events)} games  "
                  f"[credits remaining: {tracker['credits_remaining']:,}]")

            for event in events:
                event_id = event.get("id", "")
                home     = event.get("home_team", "")
                away     = event.get("away_team", "")
                kickoff  = event.get("commence_time", "")

                if not event_id or not kickoff:
                    continue

                game_week = date_to_week(kickoff, season)
                print(f"  {away:<22} @ {home:<22}", end=" ")

                n = pull_game(event_id, kickoff, season, game_week,
                              name_map, cursor, tracker)

                print(f"→ {n:4d} lines  "
                      f"[~{tracker['credits_used']:,} credits used]")

                conn.commit()
                total_lines += n
                total_games += 1
                time.sleep(0.5)

    conn.close()
    print(f"\n{'='*55}")
    print(f"COMPLETE")
    print(f"  Games:          {total_games:,}")
    print(f"  Lines stored:   {total_lines:,}")
    print(f"  Credits used:   ~{tracker['credits_used']:,}")
    print(f"  Credits left:   ~{tracker['credits_remaining']:,}")
    print(f"\nNext: python run_backtest.py --quick")

# ── Coverage report ───────────────────────────────────────────────────────────
def show_coverage():
    conn = get_conn()
    rows = conn.execute("""
        SELECT season,
               SUM(CASE WHEN source LIKE '%draftkings%' THEN 1 ELSE 0 END) dk,
               SUM(CASE WHEN source LIKE '%fanduel%'    THEN 1 ELSE 0 END) fd,
               SUM(CASE WHEN source LIKE '%betmgm%'     THEN 1 ELSE 0 END) mgm,
               SUM(CASE WHEN source = 'estimated'       THEN 1 ELSE 0 END) est,
               COUNT(*) total
        FROM prop_lines GROUP BY season ORDER BY season
    """).fetchall()
    conn.close()
    print(f"\n{'Season':<8} {'DK':>8} {'FD':>8} {'BetMGM':>8} {'Est':>8} {'Total':>8}")
    print("-" * 50)
    for r in rows:
        print(f"{r[0]:<8} {r[1]:>8,} {r[2]:>8,} {r[3]:>8,} {r[4]:>8,} {r[5]:>8,}")

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not API_KEY:
        print("Set ODDS_API_KEY: set ODDS_API_KEY=your_key")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons",  nargs="+", type=int, default=[2024, 2025])
    parser.add_argument("--test",     action="store_true", help="Weeks 1-2 only")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--check",    action="store_true")
    parser.add_argument("--newonly",  action="store_true",
                        help="Only pull lines for players missing from prop_lines")
    args = parser.parse_args()

    if args.coverage:
        show_coverage()
    elif args.check:
        data, rem, used, cost = get("/sports")
        if data:
            print(f"✓ API key valid")
            print(f"  Credits remaining: {rem:,}")
            print(f"  Credits used:      {used:,}")
            print(f"  NFL active:        {any(s.get('key')==SPORT for s in data)}")
            print(f"  Markets planned:   {sum(len(b) for b in MARKET_BATCHES)}")
            est = 570 * sum(len(b) for b in MARKET_BATCHES) * 10
            print(f"  Est cost 2024+25:  ~{est:,} credits")
            print(f"  Credits after:     ~{rem - est:,}")
    elif args.newonly:
        # Rebuild name_map with only players missing from prop_lines
        init_db()
        conn = get_conn()
        existing_names = set(r[0].lower() for r in conn.execute("""
            SELECT DISTINCT p.name FROM prop_lines pl
            JOIN players p ON pl.player_id = p.id
            WHERE pl.source LIKE 'actual%'
        """).fetchall())
        all_players = conn.execute(
            "SELECT id, name FROM players"
        ).fetchall()
        missing = [(pid, name) for pid, name in all_players
                   if name.lower() not in existing_names]
        conn.close()
        print(f"Pulling lines for {len(missing)} players missing from prop_lines:")
        for pid, name in missing[:10]:
            print(f"  {name}")
        if len(missing) > 10:
            print(f"  ... and {len(missing)-10} more")
        print()
        ingest_seasons(args.seasons, test_mode=args.test)
    else:
        ingest_seasons(args.seasons, test_mode=args.test)
