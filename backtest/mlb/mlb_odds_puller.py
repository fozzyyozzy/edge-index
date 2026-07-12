"""
Edge Index — MLB Live Odds Puller
Pulls today's MLB prop lines from DK/FD/BetMGM via The Odds API.

Usage:
  python mlb_odds_puller.py --date today
  python mlb_odds_puller.py --check          (test API connection)
  python mlb_odds_puller.py --games          (list today's games)
"""
import os, sys, json, argparse, requests
from datetime import date, datetime

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE_URL     = "https://api.the-odds-api.com/v4"
SPORT        = "baseball_mlb"
BOOKS        = ["draftkings", "fanduel", "betmgm"]

# MLB prop markets we care about
PITCHER_MARKETS = [
    "pitcher_strikeouts",
    "pitcher_hits_allowed",
    "pitcher_walks",
    "pitcher_outs",
    "pitcher_earned_runs",
]
BATTER_MARKETS = [
    "batter_hits",
    "batter_total_bases",
    "batter_home_runs",
    "batter_rbis",
    "batter_runs_scored",
    "batter_singles",
    "batter_stolen_bases",
]

# Map API prop names → our internal names
PROP_MAP = {
    "pitcher_strikeouts":   "strikeouts",
    "pitcher_hits_allowed": "hits_allowed",
    "pitcher_walks":        "walks",
    "pitcher_outs":         "outs",
    "pitcher_earned_runs":  "earned_runs",
    "batter_hits":          "hits",
    "batter_total_bases":   "total_bases",
    "batter_home_runs":     "home_runs",
    "batter_rbis":          "rbis",
    "batter_runs_scored":   "runs",
    "batter_singles":       "singles",
    "batter_stolen_bases":  "stolen_bases",
}

def api_get(endpoint, params={}):
    """Make API request and return (data, remaining_requests, used)."""
    if not ODDS_API_KEY:
        print("ERROR: ODDS_API_KEY not set.")
        print("Run: set ODDS_API_KEY=your_key_here")
        return None, 0, 0

    params["apiKey"] = ODDS_API_KEY
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=15)
        remaining = int(resp.headers.get("x-requests-remaining", 0))
        used      = int(resp.headers.get("x-requests-used", 0))

        if resp.status_code == 200:
            return resp.json(), remaining, used
        else:
            print(f"API error {resp.status_code}: {resp.text[:200]}")
            return None, remaining, used
    except Exception as e:
        print(f"Request error: {e}")
        return None, 0, 0

def check_connection():
    """Test API connection and show credit status."""
    print("Checking Odds API connection...")
    data, remaining, used = api_get("/sports", {"all": "false"})
    if data:
        mlb = [s for s in data if "baseball_mlb" in s.get("key","")]
        print(f"  ✓ Connected")
        print(f"  Credits remaining: {remaining:,}")
        print(f"  Credits used: {used:,}")
        print(f"  MLB available: {len(mlb) > 0}")
        return True
    return False

def get_todays_games():
    """Pull today's MLB games."""
    print(f"Pulling today's MLB games...")
    data, remaining, used = api_get(
        f"/sports/{SPORT}/events",
        {"dateFormat": "iso"}
    )

    if not data:
        return []

    today     = date.today().isoformat()
    tomorrow  = (date.today() + __import__('datetime').timedelta(days=1)).isoformat()
    games = []
    for event in data:
        commence = event.get("commence_time","")
        if not commence:
            continue
        # Include today's games (UTC) plus early morning next day (covers night games)
        # But exclude games that start after 6am UTC next day (clearly tomorrow)
        if today in commence:
            games.append({
                "game_id":   event["id"],
                "home":      event.get("home_team",""),
                "away":      event.get("away_team",""),
                "commence":  commence,
            })
        elif tomorrow in commence:
            # Only include if before 06:00 UTC (covers West Coast night games)
            time_part = commence[11:16] if len(commence) > 15 else "99:99"
            if time_part < "06:00":
                games.append({
                    "game_id":   event["id"],
                    "home":      event.get("home_team",""),
                    "away":      event.get("away_team",""),
                    "commence":  commence,
                })

    print(f"  Found {len(games)} games today ({remaining} credits remaining)")
    return games

def pull_game_props(game_id, home, away, markets):
    """Pull prop lines for a specific game."""
    results = []

    for market in markets:
        data, remaining, used = api_get(
            f"/sports/{SPORT}/events/{game_id}/odds",
            {
                "regions":    "us",
                "markets":    market,
                "bookmakers": ",".join(BOOKS),
                "oddsFormat": "american",
            }
        )

        if not data:
            continue

        prop_key = PROP_MAP.get(market, market)

        for book in data.get("bookmakers", []):
            book_key = book["key"]
            for mkt in book.get("markets", []):
                for outcome in mkt.get("outcomes", []):
                    outcome_name = outcome.get("name", "")
                    if outcome_name == "Over":
                        results.append({
                            "player":   outcome.get("description", ""),
                            "prop":     prop_key,
                            "line":     float(outcome.get("point", 0)),
                            "odds":     int(outcome.get("price", -110)),
                            "book":     book_key,
                            "home":     home,
                            "away":     away,
                            "game_id":  game_id,
                            "side":     "over",
                        })
                    elif outcome_name == "Under" and prop_key in ["hits", "total_bases"]:
                        results.append({
                            "player":   outcome.get("description", ""),
                            "prop":     prop_key + "_under",
                            "line":     float(outcome.get("point", 0)),
                            "odds":     int(outcome.get("price", -110)),
                            "book":     book_key,
                            "home":     home,
                            "away":     away,
                            "game_id":  game_id,
                            "side":     "under",
                        })

    return results

def pull_game_runlines(game_id, home, away):
    """Pull -1.5/+1.5 run line odds for a game using the spreads market."""
    data, remaining, used = api_get(
        f"/sports/{SPORT}/events/{game_id}/odds",
        {
            "regions":    "us",
            "markets":    "spreads",
            "bookmakers": ",".join(BOOKS),
            "oddsFormat": "american",
        }
    )
    if not data:
        return []

    results = []
    seen = {}  # team -> best odds (favor closer to even)

    for book in data.get("bookmakers", []):
        for mkt in book.get("markets", []):
            if mkt.get("key") != "spreads":
                continue
            for outcome in mkt.get("outcomes", []):
                team  = outcome.get("name", "")
                point = float(outcome.get("point", 0))
                odds  = int(outcome.get("price", 0))
                # Only care about -1.5 and +1.5
                if abs(point) != 1.5:
                    continue
                key = (team, point)
                # Keep best odds per team/line combo
                if key not in seen or abs(odds) < abs(seen[key]["odds"]):
                    seen[key] = {
                        "team":    team,
                        "opp":     away if team == home else home,
                        "home":    home,
                        "away":    away,
                        "game_id": game_id,
                        "prop":    "run_line",
                        "line":    point,
                        "odds":    odds,
                        "side":    "home_rl" if team == home else "away_rl",
                    }

    return list(seen.values())


def pull_todays_props(save=True):
    """Pull all props for today's games."""
    games = get_todays_games()
    if not games:
        print("No games found today.")
        return []

    all_props  = []
    pitcher_props = []
    batter_props  = []
    runline_props = []

    for g in games:
        print(f"  Pulling props: {g['away']} @ {g['home']}...")

        # Pitcher props
        p_props = pull_game_props(
            g["game_id"], g["home"], g["away"],
            PITCHER_MARKETS
        )
        pitcher_props.extend(p_props)

        # Batter props
        b_props = pull_game_props(
            g["game_id"], g["home"], g["away"],
            BATTER_MARKETS
        )
        batter_props.extend(b_props)

        # Run lines
        rl_props = pull_game_runlines(g["game_id"], g["home"], g["away"])
        runline_props.extend(rl_props)

        all_props.extend(p_props + b_props)

    # Deduplicate — keep best line (lowest) per player/prop/book
    import pandas as pd
    if all_props:
        df = pd.DataFrame(all_props)

        # Best line per player/prop combination
        # (lowest line = easiest OVER to hit)
        best = df.sort_values("line").groupby(
            ["player","prop"], as_index=False
        ).first()

        print(f"\n  Total props pulled: {len(df)}")
        print(f"  Unique player/prop combos: {len(best)}")
        print(f"  Pitchers: {len(best[best['prop'].isin(['strikeouts','hits_allowed','outs'])])}")
        print(f"  Batters:  {len(best[best['prop'].isin(['hits','total_bases','home_runs'])])}")

        # Show sample
        print(f"\nSAMPLE PROPS:")
        sample = best[best["prop"]=="strikeouts"].head(10)
        if not sample.empty:
            print("  PITCHER K LINES:")
            for _, row in sample.iterrows():
                print(f"    {row['player']:25} K OVER {row['line']}  ({row['odds']})")

        sample_h = best[best["prop"]=="hits"].head(10)
        if not sample_h.empty:
            print("  BATTER HIT LINES:")
            for _, row in sample_h.iterrows():
                print(f"    {row['player']:25} H OVER {row['line']}  ({row['odds']})")

        if save:
            today = date.today().isoformat()
            out_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"mlb_lines_{today}.json"
            )
            out = {
                "date":      today,
                "generated": datetime.now().isoformat(),
                "games":     games,
                "props":     best.to_dict(orient="records"),
                "run_lines": runline_props,
            }
            with open(out_path, "w") as f:
                json.dump(out, f, indent=2)
            print(f"\nSaved to mlb_lines_{today}.json")

        return best.to_dict(orient="records")

    return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check",  action="store_true", help="Test API connection")
    parser.add_argument("--games",  action="store_true", help="List today's games")
    parser.add_argument("--date",   default="today")
    parser.add_argument("--save",   action="store_true", default=True)
    args = parser.parse_args()

    if args.check:
        check_connection()
    elif args.games:
        games = get_todays_games()
        print(f"\nToday's games:")
        for g in games:
            print(f"  {g['away']:25} @ {g['home']:25}  {g['commence'][:16]}")
    else:
        if not ODDS_API_KEY:
            print("Set your API key first:")
            print("  set ODDS_API_KEY=your_key_here")
            print("  python mlb_odds_puller.py --check")
        else:
            pull_todays_props(save=args.save)
