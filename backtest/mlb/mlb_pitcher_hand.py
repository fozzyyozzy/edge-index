"""
Edge Index — Pitcher Hand Lookup
Pulls today's starting pitcher throwing hand from MLB Stats API.
Maps each game's starter hand so batter platoon adjustments apply.

Usage:
  python mlb_pitcher_hand.py --date 2026-05-12
  python mlb_pitcher_hand.py --test
"""
import os, sys, json, argparse, requests
from datetime import date

BASE    = "https://statsapi.mlb.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}
CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_todays_starters(game_date):
    """
    Pull today's probable starters and their throwing hand.
    Returns dict: {home_team: {pitcher, hand}, away_team: {pitcher, hand}}
    """
    try:
        resp = requests.get(
            f"{BASE}/schedule",
            params={
                "sportId":  1,
                "date":     game_date,
                "hydrate":  "probablePitcher(note),team",
                "gameType": "R",
            },
            headers=HEADERS, timeout=10
        )

        if resp.status_code != 200:
            print(f"  Schedule error: {resp.status_code}")
            return {}

        data  = resp.json()
        dates = data.get("dates", [])
        if not dates:
            print(f"  No games found for {game_date}")
            return {}

        starters = {}
        games    = dates[0].get("games", [])

        for game in games:
            home_team = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "")
            away_team = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "")

            for side in ["home", "away"]:
                team_name = home_team if side == "home" else away_team
                pitcher   = game.get("teams", {}).get(side, {}).get("probablePitcher", {})

                if not pitcher:
                    continue

                pitcher_name = pitcher.get("fullName", "")
                pitcher_id   = pitcher.get("id", 0)

                # Get pitcher hand
                hand = get_pitcher_hand(pitcher_id)

                starters[team_name] = {
                    "pitcher": pitcher_name,
                    "hand":    hand or "R",  # default R if unknown
                    "id":      pitcher_id,
                }

                print(f"  {team_name:30} → {pitcher_name:25} ({hand}HP)")

        return starters

    except Exception as e:
        print(f"  Schedule error: {e}")
        return {}

def get_pitcher_hand(pitcher_id):
    """Look up pitcher throwing hand from MLB people API."""
    if not pitcher_id:
        return "R"

    try:
        resp = requests.get(
            f"{BASE}/people/{pitcher_id}",
            headers=HEADERS, timeout=10
        )

        if resp.status_code == 200:
            person = resp.json().get("people", [{}])[0]
            hand   = person.get("pitchHand", {}).get("code", "R")
            return hand

    except:
        pass

    return "R"

def get_batter_pitcher_hand(batter_team, starters):
    """
    Given a batter's team, find the opposing starter's hand.
    Batter faces the OTHER team's pitcher.
    """
    # Find which game the batter's team is in
    # and return the opposing pitcher's hand
    for team, info in starters.items():
        # We need to find the opponent
        # starters dict has all teams, find batter's opponent
        pass

    # Simpler approach: return from the lines data
    return starters

def build_hand_cache(game_date):
    """Build and save pitcher hand cache for today."""
    print(f"Pulling starter hands for {game_date}...")
    starters = get_todays_starters(game_date)

    cache_path = os.path.join(CACHE_DIR, f"pitcher_hands_{game_date}.json")
    with open(cache_path, "w") as f:
        json.dump(starters, f, indent=2)

    print(f"\n✓ Saved {len(starters)} teams to cache")
    return starters

def get_opposing_hand(batter_team, home_team, away_team, starters):
    """
    Get the throwing hand of the pitcher facing a batter.
    If batter is on home team → they face away pitcher.
    If batter is on away team → they face home pitcher.
    Uses fuzzy matching on team names.
    """
    if not batter_team:
        return "R", "Unknown"

    bt = batter_team.lower()
    ht = home_team.lower()
    at = away_team.lower()

    def team_match(a, b):
        """Fuzzy match — check if any word overlaps."""
        a_words = set(a.split())
        b_words = set(b.split())
        return bool(a_words & b_words)

    # Is batter on home or away team?
    batter_is_home = team_match(bt, ht)
    batter_is_away = team_match(bt, at)

    # Opponent team is the other side
    if batter_is_home:
        opp_team = away_team
    elif batter_is_away:
        opp_team = home_team
    else:
        # Can't determine — try partial match in starters
        opp_team = home_team  # default to home pitcher

    opp_lower = opp_team.lower()

    # Find opponent's starter
    for team_name, info in starters.items():
        if team_match(opp_lower, team_name.lower()):
            return info.get("hand", "R"), info.get("pitcher", "")

    # Last resort — just return home team pitcher hand
    for team_name, info in starters.items():
        if team_match(ht, team_name.lower()):
            return info.get("hand", "R"), info.get("pitcher", "")

    return "R", "Unknown"

def load_hand_cache(game_date):
    """Load pitcher hand cache for a date."""
    cache_path = os.path.join(CACHE_DIR, f"pitcher_hands_{game_date}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    return {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",  default=date.today().isoformat())
    parser.add_argument("--test",  action="store_true")
    args = parser.parse_args()

    if args.test:
        print("Testing MLB Stats API schedule endpoint...")
        resp = requests.get(
            f"{BASE}/schedule",
            params={"sportId":1,"date":args.date,"hydrate":"probablePitcher,team","gameType":"R"},
            headers=HEADERS, timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            dates = resp.json().get("dates",[])
            if dates:
                games = dates[0].get("games",[])
                print(f"Games today: {len(games)}")
                for g in games[:3]:
                    home = g["teams"]["home"]["team"]["name"]
                    away = g["teams"]["away"]["team"]["name"]
                    hp   = g["teams"]["home"].get("probablePitcher",{}).get("fullName","TBD")
                    ap   = g["teams"]["away"].get("probablePitcher",{}).get("fullName","TBD")
                    print(f"  {away} @ {home}: {ap} vs {hp}")
            print("✓ API accessible")
        else:
            print(f"✗ Error: {resp.status_code}")
    else:
        starters = build_hand_cache(args.date)
        print("\nSTARTER HANDS:")
        for team, info in sorted(starters.items()):
            print(f"  {team:30} {info['pitcher']:25} {info['hand']}HP")
