"""
Edge Index — Trade Tracker
Checks for recent roster moves using the MLB Stats API.
Runs once daily, caches results, flags traded players in pipeline.

Usage:
  python mlb_trade_tracker.py --update          # refresh cache
  python mlb_trade_tracker.py --check "Lenyn Sosa"
  python mlb_trade_tracker.py --show            # show all recent moves
  python mlb_trade_tracker.py --days 7          # moves in last N days
"""
import os, sys, json, argparse, requests
from datetime import date, datetime, timedelta

BASE      = "https://statsapi.mlb.com/api/v1"
HEADERS   = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

ROSTER_CACHE  = os.path.join(CACHE_DIR, "rosters.json")
TRADE_CACHE   = os.path.join(CACHE_DIR, "recent_trades.json")
TRADE_STAMP   = os.path.join(CACHE_DIR, "trade_stamp.txt")

# All 30 MLB team IDs
MLB_TEAMS = {
    108:"LAA", 109:"ARI", 110:"BAL", 111:"BOS", 112:"CHC",
    113:"CIN", 114:"CLE", 115:"COL", 116:"DET", 117:"HOU",
    118:"KC",  119:"LAD", 120:"WSH", 121:"NYM", 133:"OAK",
    134:"PIT", 135:"SD",  136:"SEA", 137:"SF",  138:"STL",
    139:"TB",  140:"TEX", 141:"TOR", 142:"MIN", 143:"PHI",
    144:"ATL", 145:"CWS", 146:"MIA", 147:"NYY", 158:"MIL",
}

def get_team_roster(team_id):
    """Pull current 40-man roster for a team."""
    try:
        resp = requests.get(
            f"{BASE}/teams/{team_id}/roster",
            params={"rosterType": "40Man", "season": 2026},
            headers=HEADERS, timeout=10
        )
        if resp.status_code != 200:
            return {}

        roster = {}
        for p in resp.json().get("roster", []):
            pid  = p["person"]["id"]
            name = p["person"]["fullName"]
            pos  = p.get("position", {}).get("abbreviation", "")
            roster[pid] = {"name": name, "pos": pos, "team_id": team_id,
                          "team": MLB_TEAMS.get(team_id, str(team_id))}
        return roster

    except Exception as e:
        return {}

def build_roster_snapshot():
    """Pull all 30 rosters and build name→team mapping."""
    print("Building roster snapshot (30 teams)...")
    all_players = {}

    for team_id, abbr in MLB_TEAMS.items():
        roster = get_team_roster(team_id)
        all_players.update(roster)
        print(f"  {abbr}: {len(roster)} players", end="\r")

    print(f"\nTotal: {len(all_players)} players on 40-man rosters")
    return all_players

def detect_trades(old_snapshot, new_snapshot):
    """Compare two snapshots and find players who changed teams."""
    moves = []

    for pid, new_info in new_snapshot.items():
        if pid in old_snapshot:
            old_info = old_snapshot[pid]
            if old_info["team_id"] != new_info["team_id"]:
                moves.append({
                    "player":   new_info["name"],
                    "player_id": pid,
                    "from_team": old_info["team"],
                    "to_team":   new_info["team"],
                    "detected":  date.today().isoformat(),
                    "pos":       new_info["pos"],
                })

    # New players not in old snapshot (call-ups/trades from minors)
    new_pids = set(new_snapshot.keys()) - set(old_snapshot.keys())
    for pid in new_pids:
        info = new_snapshot[pid]
        moves.append({
            "player":    info["name"],
            "player_id": pid,
            "from_team": "UNKNOWN",
            "to_team":   info["team"],
            "detected":  date.today().isoformat(),
            "pos":       info["pos"],
            "note":      "New to 40-man roster",
        })

    return moves

def update_cache():
    """Pull fresh rosters, detect trades vs yesterday's cache."""
    new_snapshot = build_roster_snapshot()

    trades = []
    if os.path.exists(ROSTER_CACHE):
        with open(ROSTER_CACHE) as f:
            old_data = json.load(f)
        old_snapshot = old_data.get("players", {})
        # Convert keys back to int
        old_snapshot = {int(k): v for k, v in old_snapshot.items()}
        new_snapshot_int = {int(k): v for k, v in new_snapshot.items()}

        trades = detect_trades(old_snapshot, new_snapshot_int)

        if trades:
            print(f"\n🔄 ROSTER MOVES DETECTED: {len(trades)}")
            for m in trades:
                note = m.get("note", "")
                print(f"  {m['player']:28} {m['from_team']} → {m['to_team']} {note}")
        else:
            print("\n✓ No roster changes detected")

    # Save new snapshot
    with open(ROSTER_CACHE, "w") as f:
        json.dump({
            "updated": date.today().isoformat(),
            "players": {str(k): v for k, v in new_snapshot.items()},
        }, f, indent=2)

    # Append to trade history
    if trades:
        existing = []
        if os.path.exists(TRADE_CACHE):
            with open(TRADE_CACHE) as f:
                existing = json.load(f)
        existing.extend(trades)
        # Keep last 90 days
        cutoff = (date.today() - timedelta(days=90)).isoformat()
        existing = [t for t in existing if t.get("detected","") >= cutoff]
        with open(TRADE_CACHE, "w") as f:
            json.dump(existing, f, indent=2)

    with open(TRADE_STAMP, "w") as f:
        f.write(date.today().isoformat())

    return trades

def check_player(name):
    """Check current team for a player and recent trade history."""
    if not os.path.exists(ROSTER_CACHE):
        print("No roster cache — run --update first")
        return

    with open(ROSTER_CACHE) as f:
        data = json.load(f)

    players = data.get("players", {})
    name_lower = name.lower()

    # Find player
    found = [(pid, info) for pid, info in players.items()
             if name_lower in info["name"].lower()]

    if not found:
        print(f"  {name} — not found on any 40-man roster")
        return

    for pid, info in found:
        print(f"\n  {info['name']:28} {info['pos']:3} — {info['team']}")

    # Check trade history
    if os.path.exists(TRADE_CACHE):
        with open(TRADE_CACHE) as f:
            trades = json.load(f)

        player_trades = [t for t in trades
                        if name_lower in t["player"].lower()]
        if player_trades:
            print(f"  Recent moves:")
            for t in player_trades[-3:]:
                print(f"    {t['detected']}: {t['from_team']} → {t['to_team']}")

def get_traded_players(days=14):
    """Return list of players traded in last N days."""
    if not os.path.exists(TRADE_CACHE):
        return []

    cutoff = (date.today() - timedelta(days=days)).isoformat()
    with open(TRADE_CACHE) as f:
        trades = json.load(f)

    return [t for t in trades if t.get("detected", "") >= cutoff]

def flag_traded_players(player_names, days=30):
    """
    Given a list of player names, return dict of name→trade_info
    for any who changed teams recently. Used by mlb_run_today.py.
    """
    recent = get_traded_players(days)
    flagged = {}

    for name in player_names:
        name_lower = name.lower()
        for trade in recent:
            if name_lower in trade["player"].lower():
                flagged[name] = trade
                break

    return flagged

def show_recent(days=14):
    """Print recent roster moves."""
    moves = get_traded_players(days)
    if not moves:
        print(f"No roster moves in last {days} days")
        print("Run --update to build cache first")
        return

    print(f"\nROSTER MOVES — Last {days} days")
    print(f"{'─'*55}")
    for m in sorted(moves, key=lambda x: x["detected"], reverse=True):
        note = f"  [{m.get('note','')}]" if m.get("note") else ""
        print(f"  {m['detected']}  {m['player']:26} {m['from_team']} → {m['to_team']}{note}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true",
                        help="Pull fresh rosters and detect trades")
    parser.add_argument("--check",  default="",
                        help="Check current team for a player")
    parser.add_argument("--show",   action="store_true",
                        help="Show recent roster moves")
    parser.add_argument("--days",   type=int, default=14,
                        help="Days to look back for trades")
    args = parser.parse_args()

    if args.update:
        trades = update_cache()
        print(f"\n✓ Cache updated — {date.today().isoformat()}")
        print(f"  Run daily to track all moves automatically")
        print(f"  Add to morning routine before mlb_odds_puller.py")

    elif args.check:
        check_player(args.check)

    elif args.show:
        show_recent(args.days)

    else:
        # Default: show cache status
        if os.path.exists(TRADE_STAMP):
            stamp = open(TRADE_STAMP).read().strip()
            print(f"Last updated: {stamp}")
            recent = get_traded_players(args.days)
            print(f"Moves in last {args.days} days: {len(recent)}")
            if recent:
                show_recent(args.days)
        else:
            print("No cache yet — run: python mlb_trade_tracker.py --update")
            print("Takes ~2 minutes to pull all 30 rosters")
