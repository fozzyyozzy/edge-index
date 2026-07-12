"""
Edge Index — Umpire Tendency Tracker
Pulls HP umpire assignments for today's games and applies historical
K-rate tendencies to pitcher K prop model.

Key signals:
  - Umpire K rate vs league average (K/9 boost or penalty)
  - Umpire strike zone size (measured by called strike % above/below avg)
  - Umpire tendency with specific pitcher handedness
  - Home/away split for umpire (some umps favor home teams)

Data sources:
  1. MLB Stats API - today's umpire assignments (game boxscore/schedule)
  2. Historical ump data cached locally from prior games
  3. UmpScorecards data (if accessible) for zone metrics

Usage:
  python mlb_umpire.py --date 2026-05-21           # show today's umps
  python mlb_umpire.py --update                    # update historical cache
  python mlb_umpire.py --ump "Angel Hernandez"     # single ump lookup
"""
import os, sys, json, time, argparse, requests
from datetime import date, datetime, timedelta
from collections import defaultdict

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
UMP_CACHE = os.path.join(CACHE_DIR, "umpire_stats.json")
UMP_GAMES = os.path.join(CACHE_DIR, "umpire_games.json")

os.makedirs(CACHE_DIR, exist_ok=True)

BASE_API = "https://statsapi.mlb.com/api/v1"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin":  "https://www.mlb.com",
    "Referer": "https://www.mlb.com/",
}

# ── LEAGUE AVERAGE BASELINES (2024-2026) ──────────────────────
# These get updated as we collect more data
LEAGUE_AVG = {
    "k_per_9":         8.4,    # avg Ks per 9 innings league-wide
    "called_strike_pct": 0.172, # called strikes / total pitches
    "bb_per_9":        3.2,    # walks per 9 (loose zone = more walks)
    "strike_pct":      0.634,  # overall strike % (all pitches)
}

def api_get(endpoint, params=None):
    """Make MLB Stats API call."""
    try:
        url = f"{BASE_API}/{endpoint}"
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f"  API {r.status_code}: {url}")
        return None
    except Exception as e:
        print(f"  API error: {e}")
        return None

def get_todays_umpires(game_date):
    """
    Pull HP umpire for each game today.
    Returns dict: {game_pk: {home_team, away_team, umpire_name, umpire_id}}
    """
    # Get schedule
    data = api_get("schedule", {
        "sportId": 1,
        "date": game_date,
        "hydrate": "officials,teams",
    })

    if not data:
        return {}

    games = data.get("dates", [{}])[0].get("games", [])
    result = {}

    for game in games:
        pk   = game.get("gamePk")
        home = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "?")
        away = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "?")

        # Try officials from schedule hydration first
        officials = game.get("officials", [])
        hp_ump = None
        for o in officials:
            if o.get("officialType") == "Home Plate":
                hp_ump = {
                    "name": o.get("official", {}).get("fullName", "Unknown"),
                    "id":   o.get("official", {}).get("id"),
                }
                break

        # Fallback: pull from boxscore
        if not hp_ump:
            box = api_get(f"game/{pk}/boxscore")
            if box:
                for o in box.get("officials", []):
                    if o.get("officialType") == "Home Plate":
                        hp_ump = {
                            "name": o.get("official", {}).get("fullName", "Unknown"),
                            "id":   o.get("official", {}).get("id"),
                        }
                        break
            time.sleep(0.1)

        result[pk] = {
            "home":   home,
            "away":   away,
            "umpire": hp_ump or {"name": "TBD", "id": None},
        }

    return result

def load_ump_cache():
    if os.path.exists(UMP_CACHE):
        with open(UMP_CACHE) as f:
            return json.load(f)
    return {}

def save_ump_cache(cache):
    with open(UMP_CACHE, "w") as f:
        json.dump(cache, f, indent=2)

def load_ump_games():
    if os.path.exists(UMP_GAMES):
        with open(UMP_GAMES) as f:
            return json.load(f)
    return {}

def save_ump_games(games):
    with open(UMP_GAMES, "w") as f:
        json.dump(games, f, indent=2)

def update_historical_cache(days_back=30):
    """
    Pull last N days of completed games, extract HP ump + game K totals.
    Builds historical K rate profile per umpire.
    """
    print(f"Updating umpire history (last {days_back} days)...")
    ump_games = load_ump_games()
    ump_stats = defaultdict(lambda: {
        "games": 0, "total_ks": 0, "total_innings": 0,
        "called_strikes": 0, "total_pitches": 0,
        "rhe_games": [],
    })

    today = date.today()
    for i in range(1, days_back + 1):
        game_date = (today - timedelta(days=i)).isoformat()

        # Skip if already processed
        if game_date in ump_games:
            continue

        print(f"  Processing {game_date}...")

        # Get schedule
        sched = api_get("schedule", {
            "sportId": 1,
            "date": game_date,
            "hydrate": "officials",
            "gameType": "R",
        })
        if not sched:
            continue

        games = sched.get("dates", [{}])[0].get("games", []) if sched.get("dates") else []
        day_processed = []

        for game in games:
            pk     = game.get("gamePk")
            status = game.get("status", {}).get("abstractGameState", "")
            if status != "Final":
                continue

            # Get HP ump
            officials = game.get("officials", [])
            hp_ump_name = None
            hp_ump_id   = None
            for o in officials:
                if o.get("officialType") == "Home Plate":
                    hp_ump_name = o.get("official", {}).get("fullName")
                    hp_ump_id   = o.get("official", {}).get("id")
                    break

            if not hp_ump_name:
                # Try boxscore
                box_data = api_get(f"game/{pk}/boxscore")
                if box_data:
                    for o in box_data.get("officials", []):
                        if o.get("officialType") == "Home Plate":
                            hp_ump_name = o.get("official", {}).get("fullName")
                            hp_ump_id   = o.get("official", {}).get("id")
                            break
                time.sleep(0.1)

            if not hp_ump_name:
                continue

            # Get game K totals from boxscore
            box_data2 = api_get(f"game/{pk}/boxscore")
            if not box_data2:
                continue

            teams = box_data2.get("teams", {})
            home_ks = teams.get("home", {}).get("teamStats", {}).get("pitching", {}).get("strikeOuts", 0)
            away_ks = teams.get("away", {}).get("teamStats", {}).get("pitching", {}).get("strikeOuts", 0)
            total_ks = int(home_ks) + int(away_ks)

            home_inn = teams.get("home", {}).get("teamStats", {}).get("pitching", {}).get("inningsPitched", 0)
            away_inn = teams.get("away", {}).get("teamStats", {}).get("pitching", {}).get("inningsPitched", 0)

            def ip_to_float(ip):
                try:
                    parts = str(ip).split(".")
                    return int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
                except:
                    return 0

            total_inn = ip_to_float(home_inn) + ip_to_float(away_inn)

            day_processed.append({
                "game_pk":    pk,
                "umpire":     hp_ump_name,
                "umpire_id":  hp_ump_id,
                "total_ks":   total_ks,
                "total_inn":  round(total_inn, 1),
                "k_per_9":    round(total_ks / total_inn * 9, 2) if total_inn > 0 else 0,
            })

            time.sleep(0.05)

        if day_processed:
            ump_games[game_date] = day_processed
            print(f"    {len(day_processed)} games processed")

    save_ump_games(ump_games)
    _rebuild_ump_stats(ump_games)
    print(f"Done — umpire history updated")

def _rebuild_ump_stats(ump_games):
    """Rebuild per-umpire aggregated stats from game history."""
    stats = defaultdict(lambda: {
        "games": 0, "total_ks": 0, "total_innings": 0, "k_per_9_list": []
    })

    for game_date, games in ump_games.items():
        for g in games:
            ump  = g.get("umpire", "Unknown")
            ks   = g.get("total_ks", 0)
            inn  = g.get("total_inn", 0)
            k9   = g.get("k_per_9", 0)

            if inn > 0:
                stats[ump]["games"]         += 1
                stats[ump]["total_ks"]      += ks
                stats[ump]["total_innings"] += inn
                stats[ump]["k_per_9_list"].append(k9)

    # Calculate summary stats
    final = {}
    for ump, data in stats.items():
        if data["games"] < 3:
            continue
        avg_k9  = data["total_ks"] / data["total_innings"] * 9 if data["total_innings"] > 0 else LEAGUE_AVG["k_per_9"]
        diff    = round(avg_k9 - LEAGUE_AVG["k_per_9"], 2)
        pct     = round(diff / LEAGUE_AVG["k_per_9"] * 100, 1)
        final[ump] = {
            "games":           data["games"],
            "avg_k_per_9":     round(avg_k9, 2),
            "vs_league_avg":   diff,
            "pct_vs_avg":      pct,
            "tendency":        "HIGH_K" if diff > 0.4 else "LOW_K" if diff < -0.4 else "NEUTRAL",
            "total_ks":        data["total_ks"],
            "total_innings":   round(data["total_innings"], 1),
        }

    save_ump_cache(final)
    print(f"  Built stats for {len(final)} umpires")
    return final

def get_ump_adjustment(ump_name, ump_cache=None):
    """
    Return K adjustment factor for a given umpire.
    Positive = more Ks expected, negative = fewer.
    Returns dict with adjustment info.
    """
    if ump_cache is None:
        ump_cache = load_ump_cache()

    if not ump_name or ump_name == "TBD":
        return {"adjustment": 0.0, "tendency": "UNKNOWN", "games": 0, "avg_k9": None}

    # Exact match first
    if ump_name in ump_cache:
        data = ump_cache[ump_name]
        return {
            "umpire":     ump_name,
            "adjustment": data["vs_league_avg"],
            "pct_adj":    data["pct_vs_avg"],
            "tendency":   data["tendency"],
            "games":      data["games"],
            "avg_k9":     data["avg_k_per_9"],
        }

    # Fuzzy match on last name
    name_parts = ump_name.lower().split()
    last_name  = name_parts[-1] if name_parts else ""
    for cached_name, data in ump_cache.items():
        if last_name and last_name in cached_name.lower():
            return {
                "umpire":     cached_name,
                "adjustment": data["vs_league_avg"],
                "pct_adj":    data["pct_vs_avg"],
                "tendency":   data["tendency"],
                "games":      data["games"],
                "avg_k9":     data["avg_k_per_9"],
            }

    return {"umpire": ump_name, "adjustment": 0.0, "tendency": "NEW_UMP", "games": 0, "avg_k9": None}

def show_todays_umps(game_date, verbose=False):
    """Print today's HP umpires with their K tendency."""
    print(f"\nHP UMPIRES — {game_date}")
    print("="*70)

    games = get_todays_umpires(game_date)
    if not games:
        print("  No games found or API unavailable")
        return {}

    ump_cache = load_ump_cache()

    print(f"  {'MATCHUP':35} {'UMPIRE':22} {'K ADJ':7} {'TENDENCY'}")
    print(f"  {'-'*65}")

    results = {}
    for pk, game in games.items():
        ump_name = game["umpire"]["name"]
        adj      = get_ump_adjustment(ump_name, ump_cache)
        matchup  = f"{game['away']} @ {game['home']}"

        tendency_color = {
            "HIGH_K":   "⬆️ ",
            "LOW_K":    "⬇️ ",
            "NEUTRAL":  "→ ",
            "UNKNOWN":  "? ",
            "NEW_UMP":  "NEW",
        }.get(adj.get("tendency", "UNKNOWN"), "?")

        adj_str = f"{adj['adjustment']:+.1f}" if adj.get("games", 0) > 0 else "N/A"
        games_str = f"({adj.get('games', 0)}g)" if adj.get("games", 0) > 0 else ""

        print(f"  {matchup:35} {ump_name:22} {adj_str:7} {tendency_color} {adj.get('tendency','?')} {games_str}")

        results[pk] = {
            **game,
            "ump_adjustment": adj,
        }

    print(f"\n  Adj = K/9 vs league avg ({LEAGUE_AVG['k_per_9']} baseline)")
    print(f"  HIGH_K (>+0.4): More Ks expected — favor OVER bets")
    print(f"  LOW_K  (<-0.4): Fewer Ks expected — favor UNDER or lower lines")

    return results

def apply_ump_to_pitcher(pitcher_name, ump_name, base_model_prob, ump_cache=None):
    """
    Adjust pitcher K model probability based on umpire tendency.
    Returns adjusted probability and explanation.
    """
    adj = get_ump_adjustment(ump_name, ump_cache)

    if adj.get("games", 0) < 5:
        return base_model_prob, adj, "insufficient data"

    # Convert K/9 adjustment to probability adjustment
    # Rule of thumb: +1.0 K/9 ≈ +4% on K over probability
    # This is conservative — actual impact varies by line
    k9_adj    = adj.get("adjustment", 0)
    prob_adj  = k9_adj * 0.04
    new_prob  = min(0.97, max(0.30, base_model_prob + prob_adj))

    explanation = (
        f"Ump {adj.get('tendency','?')}: {adj.get('avg_k9','?')} K/9 avg "
        f"({k9_adj:+.1f} vs league) → prob {base_model_prob:.0%} → {new_prob:.0%}"
    )

    return round(new_prob, 3), adj, explanation

def show_single_ump(ump_name):
    """Show detailed stats for one umpire."""
    cache = load_ump_cache()
    adj   = get_ump_adjustment(ump_name, cache)

    print(f"\nUMPIRE PROFILE: {ump_name}")
    print("="*50)
    if adj.get("games", 0) == 0:
        print(f"  No data found for '{ump_name}'")
        print(f"  Run: python mlb_umpire.py --update")
        return

    print(f"  Games tracked:   {adj['games']}")
    print(f"  Avg K/9:         {adj['avg_k9']}")
    print(f"  vs League avg:   {adj['adjustment']:+.2f} K/9")
    print(f"  % vs avg:        {adj.get('pct_adj',0):+.1f}%")
    print(f"  Tendency:        {adj['tendency']}")
    print()
    if adj["tendency"] == "HIGH_K":
        print(f"  → FAVOR K OVERS in games with {ump_name}")
        print(f"  → Add +{abs(adj['adjustment']):.1f} K/9 to pitcher projections")
    elif adj["tendency"] == "LOW_K":
        print(f"  → FADE K OVERS in games with {ump_name}")
        print(f"  → Subtract {abs(adj['adjustment']):.1f} K/9 from pitcher projections")
    else:
        print(f"  → Neutral zone — no significant adjustment needed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",   default=date.today().isoformat())
    parser.add_argument("--update", action="store_true", help="Update historical cache")
    parser.add_argument("--days",   type=int, default=60, help="Days back for history")
    parser.add_argument("--ump",    default=None, help="Look up single umpire")
    parser.add_argument("--verbose",action="store_true")
    args = parser.parse_args()

    if args.update:
        update_historical_cache(days_back=args.days)
    elif args.ump:
        show_single_ump(args.ump)
    else:
        show_todays_umps(args.date, verbose=args.verbose)
        print(f"\nTo build history: python mlb_umpire.py --update --days 60")
