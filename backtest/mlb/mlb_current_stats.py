"""
Edge Index — MLB 2026 Current Season Stats
Uses the official MLB Stats API (free, no key required).
Pulls real 2026 batting and pitching stats to replace
stale 2025 pybaseball cache.

Usage:
  python mlb_current_stats.py --test
  python mlb_current_stats.py --player "Addison Barger"
  python mlb_current_stats.py --player "Addison Barger" --days 14
  python mlb_current_stats.py --update-cache
"""
import os, sys, json, argparse, requests
from datetime import date, datetime, timedelta

BASE    = "https://statsapi.mlb.com/api/v1"
SEASON  = 2026
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── PLAYER ID LOOKUP ─────────────────────────────────────────
def get_player_id(name):
    """Look up MLB player ID by name."""
    parts = name.strip().split()
    if len(parts) < 2:
        return None

    try:
        resp = requests.get(f"{BASE}/people/search", params={
            "names":   name,
            "sportId": 1,
            "season":  SEASON,
        }, headers=HEADERS, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            people = data.get("people", [])
            if people:
                return people[0]["id"]

        # Fallback: search by last name
        resp2 = requests.get(f"{BASE}/sports/1/players", params={
            "season":  SEASON,
            "gameType": "R",
        }, headers=HEADERS, timeout=10)

        if resp2.status_code == 200:
            players = resp2.json().get("people", [])
            name_lower = name.lower()
            for p in players:
                full = f"{p.get('firstName','')} {p.get('lastName','')}".lower()
                if name_lower in full or full in name_lower:
                    return p["id"]

    except Exception as e:
        print(f"  Player ID lookup error: {e}")

    return None

# ── CURRENT SEASON STATS ─────────────────────────────────────
def get_batter_season_stats(player_id):
    """Pull 2026 season batting stats for a player."""
    try:
        resp = requests.get(
            f"{BASE}/people/{player_id}/stats",
            params={
                "stats":   "season",
                "group":   "hitting",
                "season":  SEASON,
                "sportId": 1,
            },
            headers=HEADERS, timeout=10
        )

        if resp.status_code != 200:
            return None

        data   = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None

        s = splits[0].get("stat", {})
        def parse_rate(val, default="0"):
            try:
                v = str(val).strip()
                return float(v) if float(v) <= 1.0 else float(v)/1000
            except:
                return 0.0

        return {
            "avg":    parse_rate(s.get("avg",   "0")),
            "hits":   int(s.get("hits",   0)),
            "ab":     int(s.get("atBats", 0)),
            "games":  int(s.get("gamesPlayed", 0)),
            "ops":    parse_rate(s.get("ops",  "0")),
            "slg":    parse_rate(s.get("slg",  "0")),
            "obp":    parse_rate(s.get("obp",  "0")),
            "hr":     int(s.get("homeRuns", 0)),
            "rbi":    int(s.get("rbi", 0)),
            "bb":     int(s.get("baseOnBalls", 0)),
            "so":     int(s.get("strikeOuts", 0)),
        }

    except Exception as e:
        print(f"  Season stats error: {e}")
        return None

def get_batter_last_n_days(player_id, days=14):
    """Pull last N days batting stats — key for slump detection."""
    end_date   = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    try:
        resp = requests.get(
            f"{BASE}/people/{player_id}/stats",
            params={
                "stats":     "byDateRange",
                "group":     "hitting",
                "startDate": start_date,
                "endDate":   end_date,
                "season":    SEASON,
                "sportId":   1,
            },
            headers=HEADERS, timeout=10
        )

        if resp.status_code != 200:
            return None

        data   = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None

        s   = splits[0].get("stat", {})
        ab  = int(s.get("atBats", 0))
        hits= int(s.get("hits", 0))
        avg = hits / max(ab, 1)
        return {
            "period":  f"L{days}",
            "avg":     round(avg, 3),
            "hits":    hits,
            "ab":      ab,
            "games":   int(s.get("gamesPlayed", 0)),
            "hr":      int(s.get("homeRuns", 0)),
            "bb":      int(s.get("baseOnBalls", 0)),
            "so":      int(s.get("strikeOuts", 0)),
            "slump":   avg < 0.150 and ab >= 10,  # original threshold
        }

    except Exception as e:
        print(f"  Last {days} days error: {e}")
        return None

def get_pitcher_last_n_days(player_id, days=30):
    """Pull last N days pitching stats for K trend."""
    end_date   = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    try:
        resp = requests.get(
            f"{BASE}/people/{player_id}/stats",
            params={
                "stats":     "byDateRange",
                "group":     "pitching",
                "startDate": start_date,
                "endDate":   end_date,
                "season":    SEASON,
                "sportId":   1,
            },
            headers=HEADERS, timeout=10
        )

        if resp.status_code != 200:
            return None

        data   = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None

        s = splits[0].get("stat", {})
        ip    = float(s.get("inningsPitched", "0.0"))
        so    = int(s.get("strikeOuts", 0))
        k9    = round((so / max(ip, 0.1)) * 9, 1) if ip > 0 else 0

        return {
            "period":   f"L{days}d",
            "gs":       int(s.get("gamesStarted", 0)),
            "ip":       ip,
            "so":       so,
            "k_per_9":  k9,
            "era":      float(s.get("era", "0.00")),
            "whip":     float(s.get("whip", "0.00")),
            "bb":       int(s.get("baseOnBalls", 0)),
        }

    except Exception as e:
        print(f"  Pitcher stats error: {e}")
        return None

# ── SLUMP DETECTOR ────────────────────────────────────────────
def check_batter_form(player_name, player_id=None):
    """
    Full current form check for a batter.
    Returns form assessment and recommendation.
    """
    if not player_id:
        print(f"  Looking up {player_name}...")
        player_id = get_player_id(player_name)
        if not player_id:
            return {"error": f"Player ID not found for {player_name}"}

    season = get_batter_season_stats(player_id)
    l14    = get_batter_last_n_days(player_id, 14)
    l7     = get_batter_last_n_days(player_id, 7)

    result = {
        "player":  player_name,
        "id":      player_id,
        "season":  season,
        "l14":     l14,
        "l7":      l7,
    }

    # Assess form
    flags = []
    if l7 and l7.get("slump"):
        flags.append(f"⚠️ SLUMP: {l7['hits']}-for-{l7['ab']} last 7 days (.{int(l7['avg']*1000):03d})")
    if l14 and l14.get("slump"):
        flags.append(f"⚠️ COLD: {l14['hits']}-for-{l14['ab']} last 14 days (.{int(l14['avg']*1000):03d})")
    if season and season.get("avg", 0) < 0.200:
        flags.append(f"⚠️ WEAK SEASON: .{int(season['avg']*1000):03d} avg")

    result["flags"]      = flags
    result["exclude"]    = len(flags) >= 2
    result["fade_signal"] = len(flags) >= 1

    return result

# ── BATCH UPDATE CACHE ────────────────────────────────────────
def update_todays_batters(game_date=None):
    """
    Pull current form for all batters with props today.
    Updates the slump exclusion list automatically.
    """
    if not game_date:
        game_date = date.today().isoformat()

    lines_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_lines_{game_date}.json"
    )

    if not os.path.exists(lines_path):
        print(f"No lines file for {game_date}")
        return {}

    import pandas as pd
    with open(lines_path) as f:
        data = json.load(f)

    props  = pd.DataFrame(data["props"])
    batters = props[props["prop"]=="hits"]["player"].unique().tolist()
    print(f"Checking current form for {len(batters)} batters...")

    slumping = {}
    for name in batters:
        pid = get_player_id(name)
        if not pid:
            continue

        l14 = get_batter_last_n_days(pid, 14)
        if l14 and l14.get("slump"):
            slumping[name] = f"{l14['hits']}-for-{l14['ab']} L14 (.{int(l14['avg']*1000):03d})"
            print(f"  ⚠️ {name}: {slumping[name]}")
        else:
            avg_str = f".{int(l14['avg']*1000):03d}" if l14 else "unknown"
            print(f"  ✓ {name}: {avg_str} L14")

    # Save exclusion list
    cache_path = os.path.join(CACHE_DIR, f"slump_list_{game_date}.json")
    with open(cache_path, "w") as f:
        json.dump(slumping, f, indent=2)

    print(f"\nSlumping players ({len(slumping)}):")
    for name, note in slumping.items():
        print(f"  EXCLUDE: {name} — {note}")

    return slumping

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test",         action="store_true")
    parser.add_argument("--player",       default="")
    parser.add_argument("--days",         type=int, default=14)
    parser.add_argument("--update-cache", action="store_true")
    parser.add_argument("--date",         default=date.today().isoformat())
    args = parser.parse_args()

    if args.test:
        print("Testing MLB Stats API connection...")
        resp = requests.get(f"{BASE}/sports", headers=HEADERS, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✓ API accessible")
            print(f"Sports: {[s['name'] for s in resp.json().get('sports',[])[:3]]}")
        else:
            print("✗ API blocked — try from local machine")

    elif args.player:
        print(f"Checking form: {args.player}")
        result = check_batter_form(args.player)
        print(f"\nSEASON: {result.get('season')}")
        print(f"L14:    {result.get('l14')}")
        print(f"L7:     {result.get('l7')}")
        print(f"FLAGS:  {result.get('flags')}")
        print(f"EXCLUDE: {result.get('exclude')}")

    elif args.update_cache:
        slumping = update_todays_batters(args.date)
        print(f"\nAdd these to EXCLUDE_PLAYERS in mlb_run_today.py:")
        for name, note in slumping.items():
            print(f'    "{name}": "{note}",')

    else:
        print("Usage:")
        print("  python mlb_current_stats.py --test")
        print("  python mlb_current_stats.py --player 'Addison Barger'")
        print("  python mlb_current_stats.py --update-cache --date 2026-05-10")
