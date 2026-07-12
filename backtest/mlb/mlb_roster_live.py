"""
Edge Index — Live Roster Lookup
Replaces static cache with real-time MLB API team lookups.
Run daily to keep player_ids.json current with trades.

Usage:
  python mlb_roster_live.py --update          # update all tracked players
  python mlb_roster_live.py --player "Name"   # check single player
"""
import os, json, time, argparse, requests
from datetime import date

BASE_API = "https://statsapi.mlb.com/api/v1"
HEADERS  = {
    "User-Agent": "Mozilla/5.0",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
ID_CACHE  = os.path.join(CACHE_DIR, "player_ids.json")

def api_get(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_API}/{endpoint}",
            params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  API error: {e}")
    return None

def search_player(name):
    """Search for player by name, return id + current team."""
    data = api_get("people/search", {"names": name, "sportId": 1})
    if not data:
        return None, None, None
    
    people = data.get("people", [])
    name_lower = name.lower()
    
    # Find best match
    match = None
    for p in people:
        if p.get("fullName", "").lower() == name_lower:
            match = p
            break
    if not match:
        for p in people:
            full = p.get("fullName", "").lower()
            if name_lower in full or full in name_lower:
                match = p
                break
    
    if not match:
        return None, None, None
    
    pid  = match.get("id")
    full = match.get("fullName", name)
    
    # Always get current team from people endpoint — search doesn't hydrate it reliably
    team = get_current_team(pid) or "Unknown"
    time.sleep(0.1)
    
    return pid, team, full

def get_current_team(player_id):
    """Get authoritative current team from API."""
    # Try people endpoint with currentTeam hydration
    data = api_get(f"people/{player_id}", {
        "hydrate": "currentTeam",
        "sportId": 1,
    })
    if data:
        people = data.get("people", [])
        if people:
            team = people[0].get("currentTeam", {}).get("name")
            if team:
                return team
    
    # Fallback: get team from most recent game log
    data2 = api_get(f"people/{player_id}/stats", {
        "stats":    "gameLog",
        "group":    "hitting",
        "season":   2026,
        "gameType": "R",
    })
    if data2:
        splits = data2.get("stats", [{}])[0].get("splits", [])
        if splits:
            return splits[-1].get("team", {}).get("name")
    
    # Try pitching log
    data3 = api_get(f"people/{player_id}/stats", {
        "stats":    "gameLog",
        "group":    "pitching",
        "season":   2026,
        "gameType": "R",
    })
    if data3:
        splits = data3.get("stats", [{}])[0].get("splits", [])
        if splits:
            return splits[-1].get("team", {}).get("name")
    
    return None

def load_cache():
    if os.path.exists(ID_CACHE):
        with open(ID_CACHE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(ID_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def lookup(name, force_refresh=False):
    """
    Look up player — cache first, then API.
    Always verifies current team from API if cached.
    """
    cache = load_cache()
    key   = name.lower().strip()
    
    if key in cache and not force_refresh:
        cached = cache[key]
        pid    = cached.get("id")
        # Always verify current team — trades happen
        current_team = get_current_team(pid)
        time.sleep(0.1)
        if current_team and current_team != cached.get("team"):
            print(f"  TRADE DETECTED: {name} moved from {cached['team']} to {current_team}")
            cached["team"]    = current_team
            cached["updated"] = date.today().isoformat()
            cache[key] = cached
            save_cache(cache)
        return pid, cached.get("team"), cached.get("full_name", name)
    
    # Not in cache — search API
    pid, team, full = search_player(name)
    time.sleep(0.2)
    
    if pid:
        cache[key] = {
            "id":        pid,
            "full_name": full,
            "team":      team,
            "updated":   date.today().isoformat(),
        }
        save_cache(cache)
        print(f"  Added: {full} -> {team} (id: {pid})")
    else:
        print(f"  NOT FOUND: {name}")
    
    return pid, team, full

def update_all(plays_date):
    """Update roster for all players in today's plays file."""
    plays_path = os.path.join(BASE_DIR, f"mlb_plays_{plays_date}.json")
    if not os.path.exists(plays_path):
        print(f"No plays file for {plays_date}")
        return
    
    with open(plays_path, encoding='utf-8') as f:
        plays = json.load(f)
    
    all_players = []
    for p in plays.get("pitcher_plays", []) + plays.get("batter_plays", []):
        if p and p.get("player"):
            all_players.append(p["player"])
    
    print(f"\nROSTER VERIFICATION — {plays_date}")
    print(f"Checking {len(all_players)} players against MLB API...")
    print("="*60)
    
    moves = []
    for name in all_players:
        pid, team, full = lookup(name, force_refresh=True)
        time.sleep(0.15)
        if pid:
            print(f"  {(full or name):30} {team}")
        
    if moves:
        print(f"\nTRADES DETECTED: {len(moves)}")
        for m in moves:
            print(f"  {m}")
    else:
        print(f"\nNo roster changes detected")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--player", default=None)
    parser.add_argument("--date",   default=date.today().isoformat())
    args = parser.parse_args()
    
    if args.player:
        pid, team, full = lookup(args.player, force_refresh=True)
        print(f"{full} -> {team} (id: {pid})")
    elif args.update:
        update_all(args.date)
    else:
        parser.print_help()
