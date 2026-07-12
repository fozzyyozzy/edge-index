"""
Edge Index — Live Schedule Wire-Up
Pulls current week NFL games from The Odds API including:
  - Game matchups (home/away)
  - Spreads + totals from DK/FD/BetMGM
  - Game window detection (TNF/SUN_EARLY/SUN_AFT/SNF/MNF)
  - Dome detection
  - Rest days calculation
  - Auto-populates weekly_pipeline.py GAMES dict

Usage:
  python live_schedule.py --week 1 --season 2026
  python live_schedule.py --week 1 --season 2026 --dry-run
"""
import os, sys, json, requests, argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE_URL     = "https://api.the-odds-api.com/v4"
SPORT        = "americanfootball_nfl"
BOOKS        = ["draftkings", "fanduel", "betmgm"]

# ── SEASON STARTS (Thursday of Week 1) ───────────────────────
SEASON_STARTS = {
    2024: "2024-09-05",
    2025: "2025-09-04",
    2026: "2026-09-03",  # projected — update when confirmed
}

# ── DOME TEAMS ────────────────────────────────────────────────
DOME_TEAMS = {
    "Atlanta Falcons", "New Orleans Saints", "Los Angeles Rams",
    "Las Vegas Raiders", "Minnesota Vikings", "Detroit Lions",
    "Indianapolis Colts", "Houston Texans", "Dallas Cowboys",
    "Arizona Cardinals", "Buffalo Bills",
}

# Short name → full name map
TEAM_SHORT = {
    "ATL":"Atlanta Falcons",    "NO":"New Orleans Saints",
    "LAR":"Los Angeles Rams",   "LV":"Las Vegas Raiders",
    "MIN":"Minnesota Vikings",  "DET":"Detroit Lions",
    "IND":"Indianapolis Colts", "HOU":"Houston Texans",
    "DAL":"Dallas Cowboys",     "ARI":"Arizona Cardinals",
    "BUF":"Buffalo Bills",      "KC":"Kansas City Chiefs",
    "BAL":"Baltimore Ravens",   "PHI":"Philadelphia Eagles",
    "SF":"San Francisco 49ers", "CIN":"Cincinnati Bengals",
    "PIT":"Pittsburgh Steelers","GB":"Green Bay Packers",
    "CHI":"Chicago Bears",      "MIA":"Miami Dolphins",
    "NE":"New England Patriots","NYG":"New York Giants",
    "NYJ":"New York Jets",      "WAS":"Washington Commanders",
    "CAR":"Carolina Panthers",  "TB":"Tampa Bay Buccaneers",
    "TEN":"Tennessee Titans",   "JAC":"Jacksonville Jaguars",
    "CLE":"Cleveland Browns",   "DEN":"Denver Broncos",
    "LAC":"Los Angeles Chargers","SEA":"Seattle Seahawks",
}

# Full name → short name
TEAM_ABBR = {v: k for k, v in TEAM_SHORT.items()}

# ── TIMEZONE MAP ─────────────────────────────────────────────
TEAM_TIMEZONE = {
    "NE":"ET","NYG":"ET","NYJ":"ET","PHI":"ET","PIT":"ET",
    "BAL":"ET","WAS":"ET","MIA":"ET","BUF":"ET","CLE":"ET",
    "CIN":"ET","TB":"ET","CAR":"ET","ATL":"ET","NO":"ET",
    "MIN":"CT","GB":"CT","CHI":"CT","DET":"CT","KC":"CT",
    "HOU":"CT","TEN":"CT","IND":"CT","JAC":"ET",
    "DAL":"CT","SF":"PT","LAR":"PT","LAC":"PT","LV":"PT",
    "SEA":"PT","ARI":"PT","DEN":"MT",
}

# ── GAME WINDOW DETECTOR ──────────────────────────────────────
def detect_window(commence_time_utc):
    """
    Classify game into TNF/SUN_EARLY/SUN_AFT/SNF/MNF
    based on UTC kickoff time.
    """
    try:
        dt = datetime.fromisoformat(commence_time_utc.replace("Z","+00:00"))
        et = dt.astimezone(ZoneInfo("America/New_York"))

        weekday = et.weekday()  # 0=Mon, 3=Thu, 6=Sun
        hour_et = et.hour

        if weekday == 3:   # Thursday
            return "TNF"
        elif weekday == 6:  # Sunday
            if hour_et < 14:
                return "SUN_EARLY"
            elif hour_et < 17:
                return "SUN_AFT"
            else:
                return "SNF"
        elif weekday == 0:  # Monday
            return "MNF"
        elif weekday == 5:  # Saturday (late season)
            return "SAT"
        else:
            return "SUN_EARLY"  # fallback
    except Exception:
        return "SUN_EARLY"

# ── REST DAYS CALCULATOR ──────────────────────────────────────
def calc_rest_days(team_abbr, week, season, game_window,
                   prev_game_window=None):
    """
    Estimate rest days for a team.
    Default is 7 days. Adjustments:
      - TNF: ~4 days
      - Off bye (week prior was BYE): 14 days
      - MNF to TNF next week: ~4 days
    """
    if game_window == "TNF":
        return 4
    elif prev_game_window == "MNF":
        return 4  # Short week — played Monday, now Thursday/Sunday
    else:
        return 7  # Standard week

# ── ODDS API FETCHER ──────────────────────────────────────────
def fetch_games(week, season):
    """
    Pull current week games with spreads and totals.
    Returns list of game dicts.
    """
    if not ODDS_API_KEY:
        print("  No ODDS_API_KEY set — using demo data")
        return None

    try:
        # Get upcoming events
        resp = requests.get(
            f"{BASE_URL}/sports/{SPORT}/events",
            params={
                "apiKey":     ODDS_API_KEY,
                "dateFormat": "iso",
            },
            timeout=15
        )

        if resp.status_code != 200:
            print(f"  Events API error: {resp.status_code} — {resp.text[:200]}")
            return None

        events = resp.json()
        print(f"  Found {len(events)} upcoming NFL events")

        if not events:
            return []

        games = []
        for event in events:
            game_id    = event["id"]
            home_full  = event.get("home_team", "")
            away_full  = event.get("away_team", "")
            commence   = event.get("commence_time", "")

            home_abbr  = TEAM_ABBR.get(home_full, home_full[:3].upper())
            away_abbr  = TEAM_ABBR.get(away_full, away_full[:3].upper())
            window     = detect_window(commence)

            # Pull odds for this game
            odds_resp = requests.get(
                f"{BASE_URL}/sports/{SPORT}/events/{game_id}/odds",
                params={
                    "apiKey":     ODDS_API_KEY,
                    "regions":    "us",
                    "markets":    "spreads,totals",
                    "bookmakers": ",".join(BOOKS),
                    "oddsFormat": "american",
                },
                timeout=10
            )

            spread = 0.0
            total  = 44.0

            if odds_resp.status_code == 200:
                odds_data = odds_resp.json()
                for book in odds_data.get("bookmakers", []):
                    if book["key"] in BOOKS:
                        for mkt in book.get("markets", []):
                            if mkt["key"] == "spreads":
                                for out in mkt.get("outcomes", []):
                                    if out.get("name") == home_full:
                                        spread = float(out.get("point", 0))
                            elif mkt["key"] == "totals":
                                for out in mkt.get("outcomes", []):
                                    if out.get("name") == "Over":
                                        total = float(out.get("point", 44))
                        break  # Use first available book

            is_dome    = home_full in DOME_TEAMS or away_full in DOME_TEAMS
            home_rest  = calc_rest_days(home_abbr, week, season, window)
            away_rest  = calc_rest_days(away_abbr, week, season, window)

            games.append({
                "game_id":    game_id,
                "home":       home_abbr,
                "away":       away_abbr,
                "home_full":  home_full,
                "away_full":  away_full,
                "commence":   commence,
                "window":     window,
                "spread":     spread,        # from home team perspective
                "total":      total,
                "is_dome":    is_dome,
                "home_rest":  home_rest,
                "away_rest":  away_rest,
                "wind":       0,             # filled by weather module
                "temp":       65,            # filled by weather module
                "precip":     False,         # filled by weather module
            })

        # Sort by game window order
        window_order = {"TNF":0,"SUN_EARLY":1,"SUN_AFT":2,"SNF":3,"MNF":4,"SAT":5}
        games.sort(key=lambda g: window_order.get(g["window"], 9))

        return games

    except Exception as e:
        print(f"  Error fetching games: {e}")
        return None

# ── DEMO DATA FALLBACK ────────────────────────────────────────
def demo_games():
    """Sample week schedule for dry-run testing."""
    return [
        {"game_id":"demo1","home":"BAL","away":"KC", "home_full":"Baltimore Ravens",  "away_full":"Kansas City Chiefs",
         "commence":"2026-09-03T23:20:00Z","window":"TNF",       "spread":-3.0,"total":47.0,"is_dome":False,"home_rest":7,"away_rest":7,"wind":8, "temp":72,"precip":False},
        {"game_id":"demo2","home":"DAL","away":"PHI","home_full":"Dallas Cowboys",     "away_full":"Philadelphia Eagles",
         "commence":"2026-09-07T17:00:00Z","window":"SUN_EARLY", "spread":-3.0,"total":46.5,"is_dome":True, "home_rest":7,"away_rest":7,"wind":0, "temp":72,"precip":False},
        {"game_id":"demo3","home":"PIT","away":"CIN","home_full":"Pittsburgh Steelers","away_full":"Cincinnati Bengals",
         "commence":"2026-09-07T17:00:00Z","window":"SUN_EARLY", "spread":-2.0,"total":48.5,"is_dome":False,"home_rest":7,"away_rest":7,"wind":6, "temp":68,"precip":True},
        {"game_id":"demo4","home":"CHI","away":"GB", "home_full":"Chicago Bears",      "away_full":"Green Bay Packers",
         "commence":"2026-09-07T17:00:00Z","window":"SUN_EARLY", "spread":-3.0,"total":44.5,"is_dome":False,"home_rest":7,"away_rest":7,"wind":15,"temp":62,"precip":False},
        {"game_id":"demo5","home":"SF", "away":"LAR","home_full":"San Francisco 49ers","away_full":"Los Angeles Rams",
         "commence":"2026-09-07T20:25:00Z","window":"SUN_AFT",   "spread":-4.5,"total":48.0,"is_dome":False,"home_rest":7,"away_rest":7,"wind":5, "temp":68,"precip":False},
        {"game_id":"demo6","home":"BUF","away":"MIA","home_full":"Buffalo Bills",      "away_full":"Miami Dolphins",
         "commence":"2026-09-07T20:25:00Z","window":"SUN_AFT",   "spread":-4.0,"total":50.5,"is_dome":True, "home_rest":7,"away_rest":14,"wind":0,"temp":72,"precip":False},
        {"game_id":"demo7","home":"PHI","away":"DAL","home_full":"Philadelphia Eagles","away_full":"Dallas Cowboys",
         "commence":"2026-09-07T23:20:00Z","window":"SNF",        "spread":3.0, "total":46.5,"is_dome":True, "home_rest":7,"away_rest":7,"wind":0, "temp":72,"precip":False},
        {"game_id":"demo8","home":"MIN","away":"DET","home_full":"Minnesota Vikings",  "away_full":"Detroit Lions",
         "commence":"2026-09-08T00:15:00Z","window":"MNF",        "spread":-3.0,"total":46.0,"is_dome":True, "home_rest":7,"away_rest":7,"wind":0, "temp":72,"precip":False},
    ]

# ── PRINT SCHEDULE ────────────────────────────────────────────
def print_schedule(games, week, season):
    WINDOW_LABEL = {
        "TNF":"Thursday Night Football",
        "SUN_EARLY":"Sunday Early (1pm ET)",
        "SUN_AFT":"Sunday Afternoon (4pm ET)",
        "SNF":"Sunday Night Football",
        "MNF":"Monday Night Football",
        "SAT":"Saturday",
    }

    print(f"\n{'='*65}")
    print(f"NFL WEEK {week} {season} — GAME SCHEDULE")
    print(f"{'='*65}")

    current_window = None
    for g in games:
        if g["window"] != current_window:
            current_window = g["window"]
            print(f"\n{WINDOW_LABEL.get(current_window, current_window)}")
            print(f"{'─'*65}")

        dome_flag = "🏟️" if g["is_dome"] else ""
        wx_flags  = []
        if not g["is_dome"]:
            if g["wind"] >= 20:  wx_flags.append(f"💨{g['wind']}mph")
            elif g["wind"] >= 12: wx_flags.append(f"💨{g['wind']}mph")
            if g["temp"] <= 32:  wx_flags.append(f"🥶{g['temp']}°F")
            elif g["temp"] <= 45: wx_flags.append(f"❄️{g['temp']}°F")
            if g["precip"]:      wx_flags.append("🌧️")

        wx_str = " ".join(wx_flags)
        rest_note = ""
        if g["away_rest"] >= 14:  rest_note = f" [OFF BYE: {g['away']}]"
        elif g["home_rest"] >= 14: rest_note = f" [OFF BYE: {g['home']}]"
        elif g["window"] == "TNF": rest_note = " [SHORT WEEK]"

        print(f"  {g['away']:3} @ {g['home']:3}  "
              f"Spread: {g['spread']:+.1f}  Total: {g['total']:.1f}  "
              f"{dome_flag} {wx_str}{rest_note}")

    print(f"\n{'='*65}")
    print(f"Total: {len(games)} games")

# ── SAVE FOR PIPELINE ─────────────────────────────────────────
def save_schedule(games, week, season):
    """Save schedule JSON for weekly_pipeline.py to consume."""
    out = {
        "week":      week,
        "season":    season,
        "generated": datetime.now().isoformat(),
        "games":     games,
    }
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"schedule_w{week}_{season}.json"
    )
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved to schedule_w{week}_{season}.json")
    return path

# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",    type=int, default=1)
    parser.add_argument("--season",  type=int, default=2026)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"Edge Index — Live Schedule Pull")
    print(f"Week {args.week} | Season {args.season}")
    print(f"{'─'*65}")

    if args.dry_run or not ODDS_API_KEY:
        print("Using demo schedule data...")
        games = demo_games()
    else:
        print(f"Pulling from The Odds API...")
        games = fetch_games(args.week, args.season)
        if games is None:
            print("API failed — falling back to demo data")
            games = demo_games()

    print_schedule(games, args.week, args.season)
    path = save_schedule(games, args.week, args.season)

    print(f"\nNext: run weekly_pipeline.py --week {args.week} "
          f"--season {args.season}")
    print(f"      It will auto-load schedule_w{args.week}_{args.season}.json")
