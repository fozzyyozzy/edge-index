"""
Edge Index — Accurate Hit/K Streak Tracker
Pulls actual game-by-game results from MLB Stats API.
No inference. No averaging. Real consecutive game results only.

For batters: counts consecutive games WITH a hit (AB > 0)
For pitchers: counts consecutive starts OVER the K line

Usage:
  python mlb_streak_tracker.py --date 2026-05-25
  python mlb_streak_tracker.py --date 2026-05-25 --player "Corbin Carroll"
"""
import os, sys, json, time, argparse, requests
from datetime import date, timedelta

BASE_API = "https://statsapi.mlb.com/api/v1"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept":     "application/json",
    "Origin":     "https://www.mlb.com",
    "Referer":    "https://www.mlb.com/",
}
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

STREAK_CACHE = os.path.join(CACHE_DIR, "streak_cache.json")
ROSTER_CACHE = os.path.join(CACHE_DIR, "player_ids.json")

def api_get(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_API}/{endpoint}",
            params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  API error {endpoint}: {e}")
    return None

def get_player_id(name, season=2026):
    """Look up player ID by name."""
    # Check cache first
    cache = {}
    if os.path.exists(ROSTER_CACHE):
        with open(ROSTER_CACHE, encoding='utf-8') as f:
            cache = json.load(f)
    
    name_lower = name.lower().strip()
    if name_lower in cache:
        return cache[name_lower]["id"], cache[name_lower]["team"]
    
    # Search API
    data = api_get("people/search", {"names": name, "sportId": 1})
    if not data:
        return None, None
    
    people = data.get("people", [])
    if not people:
        return None, None
    
    # Find best match
    for p in people:
        full_name = p.get("fullName", "").lower()
        if name_lower in full_name or full_name in name_lower:
            pid  = p.get("id")
            team = p.get("currentTeam", {}).get("name", "Unknown")
            # Save to cache
            cache[name_lower] = {"id": pid, "name": p.get("fullName"), "team": team}
            with open(ROSTER_CACHE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
            return pid, team
    
    return None, None

def get_current_team(player_id):
    """Get player's current team directly from API."""
    data = api_get(f"people/{player_id}", {"hydrate": "currentTeam"})
    if not data:
        return None
    people = data.get("people", [])
    if people:
        return people[0].get("currentTeam", {}).get("name")
    return None

def get_hit_streak(player_id, player_name, before_date, season=2026, max_games=30):
    """
    Calculate actual consecutive game hit streak.
    Walks backward through game log, stops at first hitless AB game.
    Returns streak count and game-by-game details.
    """
    data = api_get(f"people/{player_id}/stats", {
        "stats":    "gameLog",
        "group":    "hitting",
        "season":   season,
        "gameType": "R",
    })
    if not data:
        return 0, []
    
    splits = data.get("stats", [{}])[0].get("splits", [])
    
    # Filter to games before today, sort newest first
    games = [s for s in splits if s.get("date", "") < before_date]
    games.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    streak = 0
    details = []
    
    for g in games[:max_games]:
        stat = g.get("stat", {})
        ab   = stat.get("atBats", 0) or 0
        hits = stat.get("hits", 0) or 0
        
        # Skip games with no AB (rest, DH off day, etc.)
        if ab == 0:
            details.append({
                "date": g.get("date"),
                "opp":  g.get("opponent", {}).get("name", "?"),
                "hits": hits, "ab": ab,
                "result": "no_ab"
            })
            continue
        
        # Has AB — did they get a hit?
        if hits > 0:
            streak += 1
            details.append({
                "date": g.get("date"),
                "opp":  g.get("opponent", {}).get("name", "?"),
                "hits": hits, "ab": ab,
                "result": "hit"
            })
        else:
            # Hitless with AB — streak ends
            details.append({
                "date": g.get("date"),
                "opp":  g.get("opponent", {}).get("name", "?"),
                "hits": 0, "ab": ab,
                "result": "out"
            })
            break
    
    return streak, details

def get_k_streak(player_id, player_name, line, before_date, season=2026, max_starts=10):
    """
    Calculate actual consecutive start K OVER streak.
    Walks backward through pitcher game log.
    Returns streak count and start-by-start details.
    """
    data = api_get(f"people/{player_id}/stats", {
        "stats":    "gameLog",
        "group":    "pitching",
        "season":   season,
        "gameType": "R",
    })
    if not data:
        return 0, 0.0, []
    
    splits = data.get("stats", [{}])[0].get("splits", [])
    
    # Filter to starts before today
    starts = [s for s in splits
              if s.get("stat", {}).get("gamesStarted", 0) > 0
              and s.get("date", "") < before_date]
    starts.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    streak  = 0
    k_total = 0
    details = []
    
    for s in starts[:max_starts]:
        stat = s.get("stat", {})
        ks   = stat.get("strikeOuts", 0) or 0
        
        raw_ip = str(stat.get("inningsPitched", "0"))
        try:
            parts = raw_ip.split(".")
            ip = int(parts[0]) + (int(parts[1])/3 if len(parts)>1 and parts[1] else 0)
        except:
            ip = 0
        
        k_total += ks
        over = ks > line
        
        details.append({
            "date":   s.get("date"),
            "opp":    s.get("opponent", {}).get("name", "?"),
            "ks":     ks,
            "ip":     round(ip, 1),
            "k_per_ip": round(ks/ip, 2) if ip > 0 else 0,
            "result": "over" if over else "under",
            "line":   line,
        })
        
        if over:
            streak += 1
        else:
            break
    
    avg_ks = round(k_total / len(details), 1) if details else 0
    return streak, avg_ks, details

def update_all_streaks(game_date, season=2026):
    """
    Update streak cache for all tracked players.
    Loads existing plays file to get today's batter/pitcher list.
    """
    plays_path = os.path.join(BASE_DIR, f"mlb_plays_{game_date}.json")
    if not os.path.exists(plays_path):
        print(f"No plays file for {game_date} — run mlb_run_today.py first")
        return {}
    
    with open(plays_path, encoding='utf-8') as f:
        plays = json.load(f)
    
    # Load existing streak cache
    streaks = {}
    if os.path.exists(STREAK_CACHE):
        with open(STREAK_CACHE, encoding='utf-8') as f:
            streaks = json.load(f)
    
    print(f"\nSTREAK TRACKER — {game_date}")
    print("="*65)
    
    # ── BATTER HIT STREAKS ────────────────────────────────────
    batters = [p for p in plays.get("batter_plays", [])
               if p and p.get("tier") in ("AUTO", "T1")]
    
    print(f"\nBATTER HIT STREAKS ({len(batters)} players):")
    print(f"{'PLAYER':28} {'TEAM':20} {'STREAK':8} {'LAST 5'}")
    print("-"*65)
    
    for play in batters:
        name = play.get("player", "")
        pid, team = get_player_id(name, season)
        time.sleep(0.15)
        
        if not pid:
            print(f"  {name:28} {'NOT FOUND':20}")
            continue
        
        # Get current team from API (authoritative)
        current_team = get_current_team(pid) or team
        time.sleep(0.1)
        
        streak, details = get_hit_streak(pid, name, game_date, season)
        time.sleep(0.15)
        
        # Show last 5 results
        last5 = ""
        for d in details[:5]:
            if d["result"] == "hit":
                last5 += "H"
            elif d["result"] == "out":
                last5 += "0"
            else:
                last5 += "-"
        
        status = "ACTIVE" if streak > 0 else "NO STREAK"
        print(f"  {name:28} {current_team:20} {streak}g {status:10} {last5}")
        
        streaks[name] = {
            "type":         "batter",
            "player":       name,
            "team":         current_team,
            "player_id":    pid,
            "hit_streak":   streak,
            "last_games":   details[:10],
            "updated":      game_date,
        }
    
    # ── PITCHER K STREAKS ─────────────────────────────────────
    pitchers = [p for p in plays.get("pitcher_plays", [])
                if p and p.get("tier") in ("AUTO", "T1")]
    
    print(f"\nPITCHER K STREAKS ({len(pitchers)} pitchers):")
    print(f"{'PITCHER':28} {'TEAM':20} {'LINE':6} {'STREAK':8} {'AVG Ks'}")
    print("-"*65)
    
    for play in pitchers:
        name = play.get("player", "")
        line = float(play.get("line", 4.5))
        pid, team = get_player_id(name, season)
        time.sleep(0.15)
        
        if not pid:
            print(f"  {name:28} {'NOT FOUND':20}")
            continue
        
        current_team = get_current_team(pid) or team
        time.sleep(0.1)
        
        streak, avg_ks, details = get_k_streak(pid, name, line, game_date, season)
        time.sleep(0.15)
        
        last5 = ""
        for d in details[:5]:
            last5 += "O" if d["result"] == "over" else "U"
        
        print(f"  {name:28} {current_team:20} {line:<6} {streak}g streak   {avg_ks} avg Ks  {last5}")
        
        streaks[name] = {
            "type":       "pitcher",
            "player":     name,
            "team":       current_team,
            "player_id":  pid,
            "k_line":     line,
            "k_streak":   streak,
            "avg_ks":     avg_ks,
            "last_starts": details[:10],
            "updated":    game_date,
        }
    
    # Save
    with open(STREAK_CACHE, 'w', encoding='utf-8') as f:
        json.dump(streaks, f, indent=2)
    
    print(f"\n  Saved to {STREAK_CACHE}")
    return streaks

def check_single_player(name, game_date, line=None, season=2026):
    """Check streak for a single player by name."""
    print(f"\nChecking: {name}")
    pid, team = get_player_id(name, season)
    if not pid:
        print(f"  Player not found: {name}")
        return
    
    current_team = get_current_team(pid)
    print(f"  Current team: {current_team}")
    
    if line is not None:
        streak, avg_ks, details = get_k_streak(pid, name, float(line), game_date, season)
        print(f"  K OVER {line} streak: {streak} starts")
        print(f"  Avg Ks: {avg_ks}")
        for d in details[:7]:
            marker = "[O]" if d["result"] == "over" else "[U]"
            print(f"    {marker} {d['date']}  {d['ks']} Ks / {d['ip']} IP  vs {d['opp']}")
    else:
        streak, details = get_hit_streak(pid, name, game_date, season)
        print(f"  Hit streak: {streak} games")
        for d in details[:10]:
            if d["result"] == "no_ab":
                print(f"    [-] {d['date']}  no AB  vs {d['opp']}")
            elif d["result"] == "hit":
                print(f"    [H] {d['date']}  {d['hits']}-for-{d['ab']}  vs {d['opp']}")
            else:
                print(f"    [0] {d['date']}  0-for-{d['ab']}  vs {d['opp']}  STREAK ENDED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",   default=date.today().isoformat())
    parser.add_argument("--player", default=None, help="Check single player")
    parser.add_argument("--line",   default=None, help="K line for pitcher check")
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()
    
    if args.player:
        check_single_player(args.player, args.date, args.line, args.season)
    else:
        update_all_streaks(args.date, args.season)
