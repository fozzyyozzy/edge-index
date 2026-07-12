"""
Edge Index — Platoon Splits Engine
Pulls LHP/RHP batting splits from MLB Stats API.
Adjusts model probability based on batter vs pitcher handedness.

Usage:
  python mlb_platoon_splits.py --test
  python mlb_platoon_splits.py --player "Aaron Judge" --hand L
  python mlb_platoon_splits.py --update-cache --date 2026-05-12
  python mlb_platoon_splits.py --summary
"""
import os, sys, json, argparse, requests
from datetime import date, datetime

BASE      = "https://statsapi.mlb.com/api/v1"
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
    "Origin":     "https://www.mlb.com",
}
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
PLATOON_CACHE = os.path.join(CACHE_DIR, "platoon_splits.json")

# ── ADJUSTMENT LOGIC ─────────────────────────────────────────
# If batter's avg vs pitcher hand is significantly different
# from their overall avg, adjust model probability accordingly.
# e.g. Judge hits .340 vs RHP but .220 vs LHP
# If today's starter is LHP, downgrade his model prob

def platoon_adj(overall_avg, split_avg, model_prob):
    """
    Calculate probability adjustment based on platoon split.
    Returns adjusted model_prob and adjustment description.
    """
    if not overall_avg or not split_avg or overall_avg == 0:
        return model_prob, "no split data"

    ratio = split_avg / overall_avg

    if ratio >= 1.15:
        # Batter is 15%+ better vs this hand — boost
        adj = min(model_prob * 1.08, 0.98)
        desc = f"BOOST +{(ratio-1)*100:.0f}% vs this hand"
    elif ratio <= 0.85:
        # Batter is 15%+ worse vs this hand — fade
        adj = model_prob * 0.92
        desc = f"FADE -{(1-ratio)*100:.0f}% vs this hand"
    elif ratio <= 0.75:
        # Severe platoon disadvantage
        adj = model_prob * 0.85
        desc = f"STRONG FADE -{(1-ratio)*100:.0f}% vs this hand"
    else:
        # Within 15% — neutral
        adj = model_prob
        desc = "neutral split"

    return round(adj, 3), desc

def get_player_id(name):
    """Look up MLB player ID."""
    try:
        resp = requests.get(
            f"{BASE}/people/search",
            params={"names": name, "sportId": 1, "season": 2026},
            headers=HEADERS, timeout=10
        )
        if resp.status_code == 200:
            people = resp.json().get("people", [])
            if people:
                return people[0]["id"]

        # Fallback: search active roster
        resp2 = requests.get(
            f"{BASE}/sports/1/players",
            params={"season": 2026, "gameType": "R"},
            headers=HEADERS, timeout=10
        )
        if resp2.status_code == 200:
            name_lower = name.lower()
            for p in resp2.json().get("people", []):
                full = f"{p.get('firstName','')} {p.get('lastName','')}".lower()
                if name_lower in full or full in name_lower:
                    return p["id"]
    except Exception as e:
        print(f"  Player lookup error: {e}")
    return None

def get_platoon_splits(player_id, season=2025):
    """
    Derive LHP/RHP splits from pybaseball statcast data.
    Uses p_throws column — already in our pipeline data.
    season=2025 since pybaseball has that data.
    """
    try:
        import pybaseball
        pybaseball.cache.enable()

        data = pybaseball.statcast_batter(
            f"{season}-03-01", f"{season}-11-01",
            player_id=player_id
        )

        if data is None or data.empty:
            return {}

        # Filter to plate appearance results only
        pa_events = [
            'single','double','triple','home_run',
            'field_out','strikeout','walk','hit_by_pitch',
            'grounded_into_double_play','fielders_choice',
            'force_out','sac_fly','sac_bunt',
            'strikeout_double_play','double_play',
            'field_error','fielders_choice_out',
        ]
        pas = data[data['events'].isin(pa_events)].copy()

        if pas.empty:
            return {}

        hit_events = ['single','double','triple','home_run']

        results = {}

        # Overall
        total_ab = len(pas[~pas['events'].isin(['walk','hit_by_pitch','sac_fly','sac_bunt'])])
        total_h  = pas['events'].isin(hit_events).sum()
        results['overall'] = {
            'avg':    round(total_h / max(total_ab, 1), 3),
            'hits':   int(total_h),
            'ab':     int(total_ab),
        }

        # vs LHP and vs RHP
        for hand, label in [('L', 'vs_lhp'), ('R', 'vs_rhp')]:
            subset = pas[pas['p_throws'] == hand]
            ab = len(subset[~subset['events'].isin(
                ['walk','hit_by_pitch','sac_fly','sac_bunt'])])
            h  = subset['events'].isin(hit_events).sum()
            avg = round(h / max(ab, 1), 3)
            results[label] = {
                'avg':      avg,
                'hits':     int(h),
                'ab':       int(ab),
                'reliable': ab >= 20,
            }

        return results

    except Exception as e:
        print(f"  Platoon pull error: {e}")
        return {}

def get_pitcher_hand(pitcher_name):
    """Look up pitcher throwing hand from MLB API."""
    try:
        pid = get_player_id(pitcher_name)
        if not pid:
            return None

        resp = requests.get(
            f"{BASE}/people/{pid}",
            headers=HEADERS, timeout=10
        )
        if resp.status_code == 200:
            person = resp.json().get("people", [{}])[0]
            hand   = person.get("pitchHand", {}).get("code", "")
            return hand  # "L" or "R"
    except:
        pass
    return None

def update_platoon_cache(game_date, season=2026):
    """
    Pull platoon splits for all batters with props today.
    Saves to cache for use by mlb_run_today.py
    """
    lines_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_lines_{game_date}.json"
    )
    if not os.path.exists(lines_path):
        print(f"No lines file for {game_date}")
        return {}

    with open(lines_path) as f:
        data = json.load(f)

    import pandas as pd
    props   = pd.DataFrame(data["props"])
    batters = props[props["prop"]=="hits"]["player"].unique().tolist()
    games   = data.get("games", [])

    # Build pitcher hand lookup from today's games
    pitcher_hands = {}
    for g in games:
        home = g.get("home_team", "")
        away = g.get("away_team", "")
        # Pitcher hand needs to come from lineup data
        # For now we'll pull from individual pitcher lookup

    print(f"Pulling platoon splits for {len(batters)} batters...")
    cache = {}

    for name in batters:
        pid = get_player_id(name)
        if not pid:
            print(f"  {name}: no ID")
            continue

        splits = get_platoon_splits(pid, season)
        if splits:
            cache[name] = {
                "player_id": pid,
                "splits":    splits,
                "updated":   game_date,
            }

            overall  = splits.get("overall", {}).get("avg", 0)
            vs_lhp   = splits.get("vs_lhp", {}).get("avg", 0)
            vs_rhp   = splits.get("vs_rhp", {}).get("avg", 0)
            lhp_ab   = splits.get("vs_lhp", {}).get("ab", 0)
            rhp_ab   = splits.get("vs_rhp", {}).get("ab", 0)

            flag = ""
            if vs_lhp and overall and abs(vs_lhp - overall) > 0.050:
                flag = f"LHP split: .{int(vs_lhp*1000):03d} vs .{int(overall*1000):03d} overall"
            if vs_rhp and overall and abs(vs_rhp - overall) > 0.050:
                flag += f" | RHP split: .{int(vs_rhp*1000):03d}"

            print(f"  {name:28} "
                  f"L:{vs_lhp:.3f}({lhp_ab}AB) "
                  f"R:{vs_rhp:.3f}({rhp_ab}AB) "
                  f"{'⚠️ '+flag if flag else ''}")

    with open(PLATOON_CACHE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\n✓ Platoon cache saved — {len(cache)} batters")
    return cache

def apply_platoon_adj(player_name, pitcher_hand, model_prob):
    """
    Load from cache and apply platoon adjustment.
    Called by mlb_run_today.py for each batter.
    Returns (adjusted_prob, note, split_data)
    """
    if not os.path.exists(PLATOON_CACHE):
        return model_prob, "no platoon cache", {}

    with open(PLATOON_CACHE) as f:
        cache = json.load(f)

    if player_name not in cache:
        return model_prob, "no split data", {}

    splits  = cache[player_name].get("splits", {})
    overall = splits.get("overall", {}).get("avg", 0)

    if pitcher_hand == "L":
        split_data = splits.get("vs_lhp", {})
        label      = "vs LHP"
    elif pitcher_hand == "R":
        split_data = splits.get("vs_rhp", {})
        label      = "vs RHP"
    else:
        return model_prob, "unknown pitcher hand", {}

    split_avg = split_data.get("avg", 0)
    ab        = split_data.get("ab", 0)
    reliable  = split_data.get("reliable", False)

    if not reliable or not split_avg:
        return model_prob, f"insufficient AB ({ab}) {label}", split_data

    adj_prob, desc = platoon_adj(overall, split_avg, model_prob)

    note = (f"{label}: .{int(split_avg*1000):03d} "
            f"vs .{int(overall*1000):03d} overall — {desc}")

    return adj_prob, note, split_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test",         action="store_true")
    parser.add_argument("--player",       default="")
    parser.add_argument("--hand",         default="R", choices=["L","R"])
    parser.add_argument("--update-cache", action="store_true")
    parser.add_argument("--date",         default=date.today().isoformat())
    parser.add_argument("--summary",      action="store_true")
    args = parser.parse_args()

    if args.test:
        print("Testing pybaseball platoon splits for Aaron Judge (592450)...")
        splits = get_platoon_splits(592450, season=2025)
        if splits:
            overall = splits.get("overall", {})
            vs_lhp  = splits.get("vs_lhp", {})
            vs_rhp  = splits.get("vs_rhp", {})
            print(f"Overall: .{int(overall.get('avg',0)*1000):03d} ({overall.get('hits',0)}-for-{overall.get('ab',0)})")
            print(f"vs LHP:  .{int(vs_lhp.get('avg',0)*1000):03d} ({vs_lhp.get('hits',0)}-for-{vs_lhp.get('ab',0)})")
            print(f"vs RHP:  .{int(vs_rhp.get('avg',0)*1000):03d} ({vs_rhp.get('hits',0)}-for-{vs_rhp.get('ab',0)})")
            print("✓ Platoon splits working via pybaseball")
        else:
            print("✗ No data returned")

    elif args.player:
        print(f"Checking platoon splits: {args.player}")
        pid = get_player_id(args.player)
        if not pid:
            print("  Player not found")
        else:
            splits = get_platoon_splits(pid)
            overall  = splits.get("overall",{})
            vs_lhp   = splits.get("vs_lhp",{})
            vs_rhp   = splits.get("vs_rhp",{})

            print(f"\n{'='*50}")
            print(f"PLATOON SPLITS: {args.player}")
            print(f"{'='*50}")
            if overall:
                print(f"Overall:  .{int(overall.get('avg',0)*1000):03d} "
                      f"({overall.get('hits',0)}-for-{overall.get('ab',0)})")
            if vs_lhp:
                print(f"vs LHP:   .{int(vs_lhp.get('avg',0)*1000):03d} "
                      f"({vs_lhp.get('hits',0)}-for-{vs_lhp.get('ab',0)}) "
                      f"{'✓ reliable' if vs_lhp.get('reliable') else '⚠ small sample'}")
            if vs_rhp:
                print(f"vs RHP:   .{int(vs_rhp.get('avg',0)*1000):03d} "
                      f"({vs_rhp.get('hits',0)}-for-{vs_rhp.get('ab',0)}) "
                      f"{'✓ reliable' if vs_rhp.get('reliable') else '⚠ small sample'}")

            # Show adjustment for specified hand
            adj, note, _ = apply_platoon_adj(args.player, args.hand, 0.80)
            print(f"\nModel adj (0.80 base vs {args.hand}HP): {adj:.3f}")
            print(f"Note: {note}")

    elif args.update_cache:
        update_platoon_cache(args.date)

    elif args.summary:
        if not os.path.exists(PLATOON_CACHE):
            print("No cache — run --update-cache first")
        else:
            with open(PLATOON_CACHE) as f:
                cache = json.load(f)
            print(f"\nPlatoon cache — {len(cache)} batters")
            print(f"{'─'*65}")
            print(f"{'PLAYER':28} {'vs LHP':10} {'vs RHP':10} {'DIFF':8}")
            print(f"{'─'*65}")
            for name, data in sorted(cache.items()):
                splits  = data.get("splits", {})
                lhp_avg = splits.get("vs_lhp",{}).get("avg", 0)
                rhp_avg = splits.get("vs_rhp",{}).get("avg", 0)
                if lhp_avg and rhp_avg:
                    diff = lhp_avg - rhp_avg
                    flag = "⚠️ PLATOON" if abs(diff) > 0.050 else ""
                    print(f"  {name:26} .{int(lhp_avg*1000):03d}       "
                          f".{int(rhp_avg*1000):03d}       "
                          f"{diff:+.3f}  {flag}")
