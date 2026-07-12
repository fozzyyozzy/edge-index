"""
Edge Index — Roster Verifier
Cross-checks every player in platoon_splits.json against the live
MLB Stats API to catch stale team assignments.

Run before any card build to ensure park factors and matchups are correct.

Usage:
  python mlb_roster_verify.py              # check all cached players
  python mlb_roster_verify.py --fix        # auto-update team in cache
  python mlb_roster_verify.py --player "Christian Walker"  # single check
  python mlb_roster_verify.py --ids        # dump all player IDs + teams
"""
import os, sys, json, argparse, requests, time
from datetime import date

BASE      = "https://statsapi.mlb.com/api/v1"
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR     = os.path.join(BASE_DIR, "cache")
PLATOON_CACHE = os.path.join(CACHE_DIR, "platoon_splits.json")
TEAM_CACHE    = os.path.join(CACHE_DIR, "current_teams.json")

# -- PARK FACTORS (update when players move) -------------------
PARK_FACTORS = {
    "Arizona Diamondbacks":   1.02,
    "Atlanta Braves":         1.01,
    "Baltimore Orioles":      0.99,
    "Boston Red Sox":         1.05,
    "Chicago Cubs":           1.00,
    "Chicago White Sox":      1.01,
    "Cincinnati Reds":        1.08,
    "Cleveland Guardians":    0.97,
    "Colorado Rockies":       1.18,
    "Detroit Tigers":         0.98,
    "Houston Astros":         1.04,
    "Kansas City Royals":     0.98,
    "Los Angeles Angels":     0.99,
    "Los Angeles Dodgers":    1.00,
    "Miami Marlins":          0.95,
    "Milwaukee Brewers":      1.02,
    "Minnesota Twins":        0.98,
    "New York Mets":          0.97,
    "New York Yankees":       1.03,
    "Athletics":              0.95,
    "Philadelphia Phillies":  1.06,
    "Pittsburgh Pirates":     0.96,
    "San Diego Padres":       0.94,
    "San Francisco Giants":   0.94,
    "Seattle Mariners":       0.93,
    "St. Louis Cardinals":    0.99,
    "Tampa Bay Rays":         0.98,
    "Texas Rangers":          1.02,
    "Toronto Blue Jays":      0.97,
    "Washington Nationals":   0.99,
}

def get_current_team(player_id):
    """Pull current team from MLB API."""
    try:
        resp = requests.get(
            f"{BASE}/people/{player_id}",
            params={"hydrate": "currentTeam"},
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code == 200:
            person = resp.json().get("people", [{}])[0]
            team   = person.get("currentTeam", {}).get("name", "Unknown")
            active = person.get("active", False)
            return team, active
    except Exception as e:
        print(f"    API error for {player_id}: {e}")
    return None, False

def load_platoon_cache():
    if not os.path.exists(PLATOON_CACHE):
        print(f"No platoon cache at {PLATOON_CACHE}")
        print("Run: python build_platoon_cache.py")
        return {}
    with open(PLATOON_CACHE) as f:
        return json.load(f)

def load_team_cache():
    if os.path.exists(TEAM_CACHE):
        with open(TEAM_CACHE) as f:
            return json.load(f)
    return {}

def save_team_cache(cache):
    with open(TEAM_CACHE, "w") as f:
        json.dump(cache, f, indent=2)

def verify_all(fix=False):
    """
    Check every player in platoon cache against live API.
    Prints mismatches and optionally updates cache.
    """
    platoon = load_platoon_cache()
    teams   = load_team_cache()

    if not platoon:
        return

    print(f"\nVerifying {len(platoon)} players against live MLB API...")
    print(f"(Using cached team data where available — API calls only for unknowns)")
    print(f"{'='*70}")

    mismatches  = []
    confirmed   = []
    unknown     = []
    inactive    = []

    for name, data in sorted(platoon.items()):
        pid          = data.get("player_id")
        cached_team  = data.get("team", "unknown")

        if not pid:
            unknown.append(name)
            continue

        # Use team cache to avoid hammering API
        cache_key = str(pid)
        if cache_key in teams:
            current_team = teams[cache_key]["team"]
            active       = teams[cache_key]["active"]
        else:
            current_team, active = get_current_team(pid)
            if current_team:
                teams[cache_key] = {
                    "name":   name,
                    "team":   current_team,
                    "active": active,
                    "checked": date.today().isoformat(),
                }
                save_team_cache(teams)
            time.sleep(0.1)  # rate limit courtesy

        if not current_team:
            unknown.append(name)
            continue

        if not active:
            inactive.append((name, cached_team, current_team))
            continue

        # Compare cached vs actual
        if cached_team == "unknown" or cached_team != current_team:
            mismatches.append((name, pid, cached_team, current_team))
            old_pf = PARK_FACTORS.get(cached_team, "?")
            new_pf = PARK_FACTORS.get(current_team, "?")
            print(f"  ⚠️  {name:28} "
                  f"{cached_team or 'unknown':28} → {current_team:28} "
                  f"PF: {old_pf} → {new_pf}")

            if fix:
                platoon[name]["team"] = current_team
        else:
            confirmed.append(name)

    print(f"\n{'-'*70}")
    print(f"  ✓ Confirmed correct: {len(confirmed)}")
    print(f"  ⚠️  Mismatches found: {len(mismatches)}")
    print(f"  — Inactive/unknown:  {len(inactive) + len(unknown)}")

    if mismatches:
        print(f"\n{'-'*70}")
        print(f"PLAYERS ON WRONG TEAM:")
        print(f"{'-'*70}")
        print(f"  {'PLAYER':28} {'WAS':28} {'NOW':20} {'PF IMPACT'}")
        print(f"  {'-'*65}")
        for name, pid, old_team, new_team in mismatches:
            old_pf = PARK_FACTORS.get(old_team, 1.00)
            new_pf = PARK_FACTORS.get(new_team, 1.00)
            diff   = new_pf - old_pf
            impact = f"{diff:+.2f}" if old_team != "unknown" else "new"
            print(f"  {name:28} {old_team or 'unknown':28} "
                  f"{new_team:20} {impact}")

        if fix:
            with open(PLATOON_CACHE, "w") as f:
                json.dump(platoon, f, indent=2)
            print(f"\n  ✓ Platoon cache updated — {len(mismatches)} team assignments fixed")
            print(f"  Park factors will now apply correctly to updated players")
        else:
            print(f"\n  Run with --fix to auto-update the platoon cache")
            print(f"  python mlb_roster_verify.py --fix")

    if inactive:
        print(f"\n  INACTIVE PLAYERS (consider removing from cache):")
        for name, old_team, current_team in inactive:
            print(f"    {name:28} last known: {old_team}")

    # Daily summary for morning routine
    print(f"\n{'='*70}")
    if not mismatches:
        print(f"✓ ALL CLEAR — all {len(confirmed)} active players on correct teams")
    else:
        print(f"⚠️  {len(mismatches)} players on wrong teams — "
              f"run --fix before building today's card")
    print(f"  Checked: {date.today().isoformat()}")

def verify_single(player_name):
    """Quick check for one player."""
    platoon = load_platoon_cache()
    teams   = load_team_cache()

    match = None
    for name, data in platoon.items():
        if player_name.lower() in name.lower():
            match = (name, data)
            break

    if not match:
        print(f"  {player_name} not in platoon cache")
        print(f"  Doing live lookup...")
        # Try direct API search
        try:
            resp = requests.get(
                f"{BASE}/people/search",
                params={"names": player_name, "sportId": 1},
                headers=HEADERS, timeout=10
            )
            if resp.status_code == 200:
                people = resp.json().get("people", [])
                if people:
                    pid  = people[0]["id"]
                    team, active = get_current_team(pid)
                    print(f"  {player_name}: {team} (active={active})")
                    return
        except Exception as e:
            print(f"  Error: {e}")
        return

    name, data = match
    pid = data.get("player_id")
    cached_team = data.get("team", "unknown")

    cache_key = str(pid)
    if cache_key in teams:
        current_team = teams[cache_key]["team"]
        active       = teams[cache_key]["active"]
    else:
        current_team, active = get_current_team(pid)

    pf_cached  = PARK_FACTORS.get(cached_team, "?")
    pf_current = PARK_FACTORS.get(current_team, "?")

    print(f"\n  {'-'*50}")
    print(f"  Player:       {name}")
    print(f"  Player ID:    {pid}")
    print(f"  Cached team:  {cached_team} (park factor: {pf_cached})")
    print(f"  Current team: {current_team} (park factor: {pf_current})")
    print(f"  Active:       {active}")

    if cached_team != current_team:
        print(f"\n  ⚠️  MISMATCH — run: python mlb_roster_verify.py --fix")
    else:
        print(f"\n  ✓ Correct")

def dump_all_ids():
    """Print all player IDs and current teams — useful for debugging."""
    platoon = load_platoon_cache()
    teams   = load_team_cache()

    print(f"\n{'='*65}")
    print(f"  {'PLAYER':28} {'ID':8} {'TEAM':30} {'PF'}")
    print(f"  {'-'*60}")

    for name, data in sorted(platoon.items()):
        pid  = data.get("player_id", "?")
        team = teams.get(str(pid), {}).get("team", data.get("team", "unknown"))
        pf   = PARK_FACTORS.get(team, "?")
        print(f"  {name:28} {str(pid):8} {team:30} {pf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix",    action="store_true",
                        help="Auto-update team assignments in platoon cache")
    parser.add_argument("--player", default=None,
                        help="Check a single player")
    parser.add_argument("--ids",    action="store_true",
                        help="Dump all player IDs and current teams")
    args = parser.parse_args()

    if args.player:
        verify_single(args.player)
    elif args.ids:
        dump_all_ids()
    else:
        verify_all(fix=args.fix)

    print(f"\nAdd to morning routine (after trade tracker):")
    print(f"  python mlb_roster_verify.py --fix")
