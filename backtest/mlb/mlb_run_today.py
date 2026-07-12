"""
Edge Index — MLB Daily Runner
Loads today's real lines + pybaseball game logs,
runs context model, outputs ranked plays.

Usage:
  python mlb_run_today.py
  python mlb_run_today.py --date 2026-05-08
  python mlb_run_today.py --min-tier T1
"""
import os, sys, json, argparse
from datetime import date, datetime
import pandas as pd
import numpy as np

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))

# Import platoon splits engine
try:
    from mlb_platoon_splits import apply_platoon_adj, PLATOON_CACHE
    PLATOON_AVAILABLE = os.path.exists(PLATOON_CACHE)
except ImportError:
    PLATOON_AVAILABLE = False

# Import pitcher hand lookup
try:
    from mlb_pitcher_hand import load_hand_cache, get_opposing_hand
    HAND_AVAILABLE = True
except ImportError:
    HAND_AVAILABLE = False

# Import advanced stats (xBA, L7, vsTeam, regression)
try:
    from mlb_savant import get_player_signals, format_signals_for_card
    SAVANT_AVAILABLE = True
except ImportError:
    SAVANT_AVAILABLE = False

PITCHER_HANDS = {}  # populated at runtime

# ── PARK FACTORS ─────────────────────────────────────────────
PARK_FACTORS = {
    "Cincinnati Reds":         1.08,
    "Philadelphia Phillies":   1.06,
    "Boston Red Sox":          1.05,
    "Houston Astros":          1.04,
    "New York Yankees":        1.03,
    "Milwaukee Brewers":       1.02,
    "Texas Rangers":           1.02,
    "Atlanta Braves":          1.01,
    "Los Angeles Dodgers":     1.00,
    "Chicago Cubs":            1.00,
    "St. Louis Cardinals":     0.99,
    "Minnesota Twins":         0.98,
    "Detroit Tigers":          0.98,
    "Toronto Blue Jays":       0.97,
    "Cleveland Guardians":     0.97,
    "Pittsburgh Pirates":      0.96,
    "Miami Marlins":           0.95,
    "Athletics":               0.95,
    "San Francisco Giants":    0.94,
    "San Diego Padres":        0.94,
    "Seattle Mariners":        0.93,
    "Tampa Bay Rays":          0.98,
    "Baltimore Orioles":       0.99,
    "Kansas City Royals":      0.98,
    "Los Angeles Angels":      0.99,
    "Arizona Diamondbacks":    1.02,
    "Colorado Rockies":        1.18,
    "Washington Nationals":    0.99,
    "New York Mets":           0.97,
    "Chicago White Sox":       1.01,
}

# K-friendly adjustment (inverse of offense park factor)
def k_park_adj(home_team):
    pf = PARK_FACTORS.get(home_team, 1.0)
    return 1.0 + (1.0 - pf) * 0.4

# ── TEAM K% ESTIMATES (2025 season) ──────────────────────────
# Team strikeout rate as batters (higher = easier for pitchers)
TEAM_K_PCT = {
    "Oakland Athletics":       0.258,
    "Athletics":               0.258,
    "Colorado Rockies":        0.252,
    "Chicago White Sox":       0.268,
    "Washington Nationals":    0.245,
    "Kansas City Royals":      0.228,
    "Detroit Tigers":          0.222,
    "Miami Marlins":           0.248,
    "Tampa Bay Rays":          0.235,
    "Cincinnati Reds":         0.242,
    "Los Angeles Angels":      0.238,
    "Minnesota Twins":         0.232,
    "Seattle Mariners":        0.228,
    "Houston Astros":          0.218,
    "Boston Red Sox":          0.222,
    "Toronto Blue Jays":       0.232,
    "Philadelphia Phillies":   0.225,
    "Baltimore Orioles":       0.218,
    "Cleveland Guardians":     0.225,
    "New York Yankees":        0.228,
    "Milwaukee Brewers":       0.238,
}

# ── PYBASEBALL GAME LOG PULLER ────────────────────────────────
def get_pitcher_logs(player_name, season=2026):
    """
    Pull pitcher K totals per start from MLB Stats API 2026.
    Replaces pybaseball 2025 — 45+ games into 2026, current data only.
    """
    try:
        import requests as _req
        BASE_API = "https://statsapi.mlb.com/api/v1"
        HEADERS  = {
            "User-Agent": "Mozilla/5.0",
            "Accept":     "application/json",
            "Referer":    "https://www.mlb.com/",
        }

        # Load player ID from roster verify cache first (fast)
        team_cache_path = os.path.join(CACHE_DIR, "current_teams.json")
        pid = None
        if os.path.exists(team_cache_path):
            with open(team_cache_path) as f:
                team_cache = json.load(f)
            name_lower = player_name.lower()
            for k, v in team_cache.items():
                if name_lower in v.get("name","").lower():
                    pid = int(k)
                    break

        # Fallback: search API
        if not pid:
            resp = _req.get(
                f"{BASE_API}/people/search",
                params={"names": player_name, "sportId": 1, "season": season},
                headers=HEADERS, timeout=10
            )
            if resp.status_code == 200:
                people = resp.json().get("people", [])
                if people:
                    pid = people[0]["id"]

        if not pid:
            return []

        # Pull 2026 game log
        resp = _req.get(
            f"{BASE_API}/people/{pid}/stats",
            params={
                "stats":    "gameLog",
                "group":    "pitching",
                "season":   season,
                "sportId":  1,
                "gameType": "R",
            },
            headers=HEADERS, timeout=10
        )

        if resp.status_code != 200:
            return []

        splits = resp.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            return []

        # Return Ks per start, chronological order
        ks_per_start = []
        for s in splits:
            stat = s.get("stat", {})
            gs   = int(stat.get("gamesStarted", 0))
            ks   = int(stat.get("strikeOuts", 0))
            if gs > 0:  # only count starts, not relief
                ks_per_start.append(ks)

        return ks_per_start

    except Exception as e:
        return []

def get_batter_logs(player_name, season=2026):
    """
    Pull batter hit/TB totals per game from MLB Stats API 2026.
    Replaces pybaseball 2025 — current season data only.
    Returns dict with 'hits' and 'total_bases' lists, chronological.
    """
    try:
        import requests as _req
        BASE_API = "https://statsapi.mlb.com/api/v1"
        HEADERS  = {
            "User-Agent": "Mozilla/5.0",
            "Accept":     "application/json",
            "Referer":    "https://www.mlb.com/",
        }

        # Load player ID from roster verify cache first (fast)
        team_cache_path = os.path.join(CACHE_DIR, "current_teams.json")
        pid = None
        if os.path.exists(team_cache_path):
            with open(team_cache_path) as f:
                team_cache = json.load(f)
            name_lower = player_name.lower()
            for k, v in team_cache.items():
                if name_lower in v.get("name","").lower():
                    pid = int(k)
                    break

        # Fallback: search API
        if not pid:
            resp = _req.get(
                f"{BASE_API}/people/search",
                params={"names": player_name, "sportId": 1, "season": season},
                headers=HEADERS, timeout=10
            )
            if resp.status_code == 200:
                people = resp.json().get("people", [])
                if people:
                    pid = people[0]["id"]

        if not pid:
            return {}

        # Pull 2026 game log
        resp = _req.get(
            f"{BASE_API}/people/{pid}/stats",
            params={
                "stats":    "gameLog",
                "group":    "hitting",
                "season":   season,
                "sportId":  1,
                "gameType": "R",
            },
            headers=HEADERS, timeout=10
        )

        if resp.status_code != 200:
            return {}

        splits = resp.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {}

        hits_list = []
        tb_list   = []

        for s in splits:
            stat = s.get("stat", {})
            ab   = int(stat.get("atBats", 0))
            # Only count games where player batted
            if ab == 0 and int(stat.get("plateAppearances", 0)) == 0:
                continue
            hits_list.append(int(stat.get("hits", 0)))
            tb_list.append(int(stat.get("totalBases", 0)))

        return {
            "hits":        hits_list,
            "total_bases": tb_list,
        }

    except Exception as e:
        return {}

# ── STREAK + HIT RATE ─────────────────────────────────────────
def calc_streak(values, line):
    streak = 0
    for v in reversed(values):
        if v >= line:
            streak += 1
        else:
            break
    return streak

def calc_rate(values, line, n):
    recent = values[-n:] if len(values) >= n else values
    if not recent:
        return 0
    return sum(1 for v in recent if v >= line) / len(recent)

# ── PITCHER K MODEL ───────────────────────────────────────────
def evaluate_pitcher(row, prior_ks):
    line = row['line']
    odds = row['odds']
    home = row['home']
    opp  = row['away'] if row['player_name_in_home'] else row['home']

    if len(prior_ks) < 3:
        return None

    l5  = calc_rate(prior_ks, line, 5)
    l10 = calc_rate(prior_ks, line, 10)
    streak = calc_streak(prior_ks, line)
    l5_avg = round(np.mean(prior_ks[-5:]), 1)

    # Base probability
    base = l5 * 0.60 + l10 * 0.25

    # Adjustments
    streak_adj = 0.12 if streak >= 5 else 0.07 if streak >= 3 else 0.02 if streak >= 1 else -0.05
    park_adj   = (k_park_adj(home) - 1.0) * 0.5
    opp_k_pct  = TEAM_K_PCT.get(opp, 0.235)
    matchup_adj = (opp_k_pct - 0.235) * 0.5  # vs league avg

    model_prob = min(0.95, max(0.20, base + streak_adj + park_adj + matchup_adj))

    # ── UMPIRE ADJUSTMENT ─────────────────────────────────────
    # Apply HP umpire K tendency if available
    ump_name = row.get("umpire", None)
    ump_adj  = 0.0
    ump_info = {}
    if ump_name:
        try:
            from mlb_umpire import get_ump_adjustment, load_ump_cache
            _cache   = load_ump_cache()
            _adj     = get_ump_adjustment(ump_name, _cache)
            if _adj.get("games", 0) >= 5:
                # +1.0 K/9 above avg ≈ +4% probability
                ump_adj  = _adj.get("adjustment", 0) * 0.04
                ump_info = _adj
        except ImportError:
            pass
    model_prob = min(0.97, max(0.20, model_prob + ump_adj))

    if model_prob >= 0.80 and streak >= 4 and l5 >= 0.70:
        tier = "AUTO"
    elif model_prob >= 0.65 and l5 >= 0.55:
        tier = "T1"
    elif model_prob >= 0.55:
        tier = "T2"
    else:
        tier = "SKIP"

    return {
        "player":      row['player'],
        "team":        row.get('team', None),
        "prop":        "strikeouts",
        "line":        line,
        "odds":        odds,
        "tier":        tier,
        "model_prob":  round(model_prob, 3),
        "streak":      streak,
        "l5":          round(l5, 3),
        "l10":         round(l10, 3),
        "l5_avg":      l5_avg,
        "home":        home,
        "opp":         opp,
        "opp_k_pct":   round(opp_k_pct, 3),
        "park_adj":    round(park_adj, 3),
        "alt_lines":   [line - 1.0, line - 0.5],
        "prior_games": len(prior_ks),
        "umpire":      ump_name,
        "ump_adj":     round(ump_adj, 3),
        "ump_tendency":ump_info.get("tendency", "UNKNOWN"),
    }

# ── BATTER HIT MODEL ──────────────────────────────────────────
def evaluate_batter(row, prior_values, prop_type):
    line = row['line']
    odds = row['odds']
    home = row['home']

    parlay_only = row.get("parlay_only", False)
    
    if len(prior_values) < 3:
        return None

    l5  = calc_rate(prior_values, line, 5)
    l10 = calc_rate(prior_values, line, 10)
    streak = calc_streak(prior_values, line)

    base = l5 * 0.60 + l10 * 0.25
    streak_adj = 0.10 if streak >= 7 else 0.06 if streak >= 4 else 0.02 if streak >= 2 else -0.03
    park_adj   = (PARK_FACTORS.get(home, 1.0) - 1.0) * 0.3

    model_prob = min(0.95, max(0.20, base + streak_adj + park_adj))

    # ── BOOK IMPLIED PROBABILITY ──────────────────────────────
    # Used to filter plays — only post where we have real edge
    # Edge = model_prob - book_implied >= 0.05 (5% minimum)
    o = int(odds)
    book_implied = abs(o) / (abs(o) + 100) if o < 0 else 100 / (o + 100)
    book_implied = round(book_implied, 4)
    edge = round(model_prob - book_implied, 4)

    # ── TIER ASSIGNMENT ───────────────────────────────────────
    # Requires BOTH model threshold AND positive edge vs book
    # This is the key change: we only tier plays where we
    # have a measurable edge, not just high model_prob
    has_edge = edge >= 0.05  # minimum 5% edge over book

    if model_prob >= 0.80 and streak >= 5 and has_edge:
        tier = "AUTO"
    elif model_prob >= 0.65 and has_edge:
        tier = "T1"
    elif model_prob >= 0.55 and has_edge:
        tier = "T2"
    elif model_prob >= 0.55:
        # Has model signal but no book edge — mark as JUICE TRAP
        tier = "JUICE"  # visible in output but not posted
    else:
        tier = "SKIP"

    # ── VALUE_TB OVERRIDE ─────────────────────────────────────
    # Audit (23 graded cards) found a profitable pattern hidden in SKIP:
    #   total_bases + plus-money odds + model_prob 30-60% hit at 69.2%
    #   with +$45/bet EV.
    #
    # IMPORTANT — audit edge distribution:
    #   Only 4 of 15 audited winners had edge >= +5%.
    #   11 of 15 winners had NEGATIVE edge (model said they were worse than book).
    #   The edge gate filters out plays the audit suggests are still winning.
    #
    # CURRENT POLICY (under observation, expect to widen after 14-day re-audit):
    #   VALUE_TB:        the tight subset (edge >= 5%) — bet on the card
    #   VALUE_TB_SHADOW: looser pattern, no edge gate — TRACKED ONLY, not bet
    # Shadow plays get graded normally; we audit their performance vs VALUE_TB
    # after 7-14 days. If shadows consistently win, widen the gate.
    matches_pattern = (prop_type == "total_bases"
                       and o >= 100
                       and 0.30 <= model_prob < 0.60)
    if matches_pattern:
        if edge >= 0.05:
            tier = "VALUE_TB"
        else:
            tier = "VALUE_TB_SHADOW"  # tracked, not auto-posted

    return {
        "player":       row['player'],
        "team":         row.get('team', None),
        "prop":         prop_type,
        "line":         line,
        "odds":         odds,
        "tier":         tier,
        "model_prob":   round(model_prob, 3),
        "book_implied": book_implied,
        "edge":         edge,
        "streak":       streak,
        "l5":           round(l5, 3),
        "l10":          round(l10, 3),
        "home":         home,
        "alt_lines":    [max(0.5, line - 1.0), max(0.5, line - 0.5)],
        "prior_games":  len(prior_values),
        "parlay_only":  parlay_only,
    }

# ── PRINT REPORT ──────────────────────────────────────────────
def print_plays(pitcher_plays, batter_plays, game_date):
    TIER_ORDER = {"AUTO":0, "VALUE_TB":1, "VALUE_TB_SHADOW":2, "T1":3, "T2":4, "SKIP":5}

    print(f"\n{'='*65}")
    print(f"EDGE INDEX MLB — {game_date}")
    print(f"Real DK/FD/BetMGM lines + pybaseball game logs")
    print(f"{'='*65}")

    p_plays = [p for p in pitcher_plays if p and p["tier"] not in ("SKIP","JUICE","VALUE_TB_SHADOW")]
    b_plays = [p for p in batter_plays  if p and p["tier"] not in ("SKIP","JUICE","VALUE_TB_SHADOW")]
    j_plays = [p for p in pitcher_plays+batter_plays
               if p and p["tier"] == "JUICE"]
    shadow_plays = [p for p in pitcher_plays+batter_plays
                    if p and p["tier"] == "VALUE_TB_SHADOW"]

    p_plays.sort(key=lambda x: (TIER_ORDER.get(x["tier"],9), -x["model_prob"]))
    b_plays.sort(key=lambda x: (TIER_ORDER.get(x["tier"],9), -x["model_prob"]))

    if p_plays:
        print(f"\n⚾ PITCHER STRIKEOUT PROPS ({len(p_plays)} plays)")
        print(f"{'─'*65}")
        for p in p_plays:
            tier_icon = {"AUTO":"⚡","T1":"★","T2":"◆"}.get(p["tier"],"")
            print(f"\n  {p['player']:28} {tier_icon} {p['tier']}")
            print(f"  K OVER {p['line']}  |  Odds: {p['odds']:+}  |  Model: {p['model_prob']*100:.0f}%")
            print(f"  L5 avg: {p['l5_avg']} Ks  |  Streak: {p['streak']} starts  |  L5: {p['l5']*100:.0f}%  L10: {p['l10']*100:.0f}%")
            print(f"  vs {p['opp']} (K%: {p['opp_k_pct']*100:.1f}%)  |  Park adj: {p['park_adj']:+.2f}")
            if p.get("umpire") and p.get("ump_tendency") not in ("UNKNOWN","NEW_UMP",None):
                ump_icon = "\u2b06\ufe0f" if p["ump_tendency"]=="HIGH_K" else "\u2b07\ufe0f" if p["ump_tendency"]=="LOW_K" else ""
                print(f"  Umpire: {p['umpire']} {ump_icon} {p['ump_tendency']} (adj: {p.get('ump_adj',0):+.3f})")
            print(f"  Alt lines: {p['alt_lines'][0]}+ / {p['alt_lines'][1]}+")

    if b_plays:
        print(f"\n🏃 BATTER HIT/TOTAL BASE PROPS ({len(b_plays)} plays)")
        print(f"{'─'*65}")
        for p in b_plays[:20]:  # Cap at 20
            tier_icon  = {"AUTO":"⚡","T1":"★","T2":"◆"}.get(p["tier"],"")
            flag_str   = " ⚠️ VERIFY CURRENT FORM" if p.get("sanity_flag") else ""
            edge       = p.get("edge", 0)
            book_impl  = p.get("book_implied", 0)
            print(f"\n  {p['player']:28} {tier_icon} {p['tier']}{flag_str}")
            print(f"  {p['prop'].upper()} OVER {p['line']}  |  Odds: {p['odds']:+}  |  Model: {p['model_prob']*100:.0f}%")
            print(f"  Book implied: {book_impl*100:.0f}%  |  Edge: {edge*100:+.1f}%  |  Streak: {p['streak']}g")
            print(f"  L5: {p['l5']*100:.0f}%  L10: {p['l10']*100:.0f}%")
            if p.get('platoon_note'):
                print(f"  Platoon: {p['platoon_note']}")
            if SAVANT_AVAILABLE:
                adv_notes = format_signals_for_card(p['player'])
                for note in adv_notes[:2]:
                    print(f"  Advanced: {note}")

    # ── JUICE TRAPS — model signal but no book edge ────────────
    if j_plays:
        print(f"\n⚠️  JUICE TRAPS — model sees signal but book has it priced right")
        print(f"{'─'*65}")
        print(f"  DO NOT BET these — edge is zero or negative vs the book")
        for p in sorted(j_plays, key=lambda x: -x.get("model_prob",0))[:10]:
            edge = p.get("edge", 0)
            print(f"  {p['player']:28} {p['odds']:+6}  "
                  f"model:{p['model_prob']*100:.0f}%  "
                  f"book:{p.get('book_implied',0)*100:.0f}%  "
                  f"edge:{edge*100:+.1f}%")

    # ── VALUE_TB_SHADOW — tracked but not auto-posted ─────────
    # These match the audit pattern (TB + plus money + model_prob 30-60%)
    # but fail the edge >= 5% gate. We grade them anyway to check whether
    # the gate is too tight. If shadows consistently win, widen the gate.
    if shadow_plays:
        print(f"\n👻 VALUE_TB_SHADOW — tracking only, not posted (n={len(shadow_plays)})")
        print(f"{'─'*65}")
        print(f"  Match audit pattern but edge < 5%. Re-audit in 14 days to verify.")
        for p in sorted(shadow_plays, key=lambda x: -x.get("edge", -99))[:10]:
            edge = p.get("edge", 0)
            print(f"  {p['player']:28} {p['odds']:+6}  "
                  f"model:{p['model_prob']*100:.0f}%  "
                  f"edge:{edge*100:+.1f}%")
        if len(shadow_plays) > 10:
            print(f"  ... and {len(shadow_plays)-10} more")

    print(f"\n{'='*65}")
    auto = len([p for p in p_plays+b_plays if p["tier"]=="AUTO"])
    t1   = len([p for p in p_plays+b_plays if p["tier"]=="T1"])
    vtb  = len([p for p in p_plays+b_plays if p["tier"]=="VALUE_TB"])
    shadow = len(shadow_plays)
    print(f"Summary: {auto} AUTO, {t1} T1, {vtb} VALUE_TB plays (+ {shadow} shadow tracked)")
    print(f"{'='*65}")

# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",     default=date.today().isoformat())
    parser.add_argument("--min-tier", default="T2", choices=["AUTO","T1","T2"])
    parser.add_argument("--no-pybaseball", action="store_true",
                        help="Skip pybaseball pulls (faster, less accurate)")
    args = parser.parse_args()

    # Load today's lines
    lines_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_lines_{args.date}.json"
    )

    if not os.path.exists(lines_path):
        print(f"No lines file found: {lines_path}")
        print(f"Run: python mlb_odds_puller.py --date {args.date}")
        sys.exit(1)

    with open(lines_path) as f:
        data = json.load(f)

    props = data["props"]
    games = data["games"]
    df    = pd.DataFrame(props)

    print(f"Loaded {len(df)} props for {args.date}")
    print(f"Games: {len(games)}")

    # Load slump exclusions
    import json as _j, os as _o
    _sp = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "cache", f"slump_list_{args.date}.json")
    _raw_exclude = _j.load(open(_sp, encoding="utf-8")) if _o.path.exists(_sp) else {}

    # ── TIGHTENED L14 THRESHOLD: .120 (was .150) ─────────────
    # Data shows .135-.150 players hit at ~45% — not reliable enough to fade
    # .120 and below shows consistent UNDER signal (78%+ in our sample)
    # Filter the slump list to only include players at .120 or below
    EXCLUDE_PLAYERS = {}
    for _name, _reason in _raw_exclude.items():
        # Reason string typically contains the L14 avg e.g. "L14: .134 (8-for-60)"
        import re as _re
        _avg_match = _re.search(r'L14[:\s]+\.?(\d+)', _reason)
        if _avg_match:
            _avg = float("0." + _avg_match.group(1).lstrip("0") or "0")
            if _avg <= 0.120:
                EXCLUDE_PLAYERS[_name] = _reason
        else:
            # Can't parse avg — include at original threshold to be safe
            EXCLUDE_PLAYERS[_name] = _reason

    if EXCLUDE_PLAYERS:
        print(f"  Loaded {len(_raw_exclude)} slump candidates → "
              f"{len(EXCLUDE_PLAYERS)} pass tightened .120 threshold")
        print(f"  Excluding {len(EXCLUDE_PLAYERS)} slumping players (L14 ≤ .120):")
        for _n, _r in EXCLUDE_PLAYERS.items():
            print(f"    x {_n}: {_r}")
    else:
        print("  No slump cache found or no players below .120 L14")

    # Load pitcher hand cache
    _hp = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "cache", f"pitcher_hands_{args.date}.json")
    PITCHER_HANDS = _j.load(open(_hp, encoding="utf-8")) if _o.path.exists(_hp) else {}
    if PITCHER_HANDS:
        print(f"  Loaded pitcher hands for {len(PITCHER_HANDS)} teams")

    # Load roster verify cache — source of truth for player teams
    _tcp = os.path.join(CACHE_DIR, "current_teams.json")
    teams_cache = json.load(open(_tcp)) if os.path.exists(_tcp) else {}
    if teams_cache:
        print(f"  Loaded {len(teams_cache)} verified team assignments")

    # Load today's umpire assignments
    ump_assignments = {}  # {home_team_lower: umpire_name}
    try:
        from mlb_umpire import get_todays_umpires
        _umps = get_todays_umpires(args.date)
        for pk, game in _umps.items():
            home_lower = game["home"].lower()
            ump_assignments[home_lower] = game["umpire"]["name"]
        if ump_assignments:
            print(f"  Loaded {len(ump_assignments)} umpire assignments")
    except Exception as e:
        print(f"  Umpire data unavailable: {e}")
    else:
        print(f"  No pitcher hand cache — run: python mlb_pitcher_hand.py --date {args.date}")


    # ── PROCESS PITCHERS ──────────────────────────────────────
    k_lines = df[(df["prop"] == "strikeouts") & (df["line"] >= 4.5)].copy()
    print(f"\nEvaluating {len(k_lines)} pitcher K props...")

    pitcher_plays = []
    for _, row in k_lines.iterrows():
        player = row["player"]

        if args.no_pybaseball:
            # Use estimated K avg based on line
            estimated_prior = [row["line"] + np.random.normal(0.5, 1.5)
                               for _ in range(10)]
            prior_ks = [max(0, round(v)) for v in estimated_prior]
        else:
            print(f"  Pulling logs: {player}...", end="", flush=True)
            prior_ks = get_pitcher_logs(player, season=2026)
            print(f" {len(prior_ks)} starts")

        if len(prior_ks) >= 3:
            row = row.copy()
            # Inject team from roster verify cache
            pitcher_team = None
            name_lower = player.lower()
            for k, v in teams_cache.items():
                if name_lower in v.get("name","").lower():
                    pitcher_team = v.get("team")
                    break
            row['team'] = pitcher_team
            # Inject HP umpire for this game
            home_lower = row.get("home", "").lower()
            row['umpire'] = ump_assignments.get(home_lower)
            row['player_name_in_home'] = player in row.get('home','')
            result = evaluate_pitcher(row, prior_ks)
            if result:
                pitcher_plays.append(result)

    # ── PROCESS BATTERS ───────────────────────────────────────
    # Singles: 1.5+ minimum (meaningful props)
    # Parlay candidates: include 0.5 lines at heavy juice (for combining)
    hit_lines_single = df[(df["prop"] == "hits") & (df["line"] >= 1.5)].copy()
    hit_lines_parlay = df[(df["prop"] == "hits") & (df["line"] == 0.5)].copy()
    tb_lines_single  = df[(df["prop"] == "total_bases") & (df["line"] >= 1.5)].copy()
    tb_lines_parlay  = df[(df["prop"] == "total_bases") & (df["line"] == 0.5)].copy()
    
    # Combine — tag each with intended use
    hit_lines = hit_lines_single.copy()
    hit_lines["parlay_only"] = False
    hit_parlay_df = hit_lines_parlay.copy()
    hit_parlay_df["parlay_only"] = True
    hit_lines = pd.concat([hit_lines, hit_parlay_df], ignore_index=True)
    
    tb_lines = tb_lines_single.copy()
    tb_lines["parlay_only"] = False

    print(f"\nEvaluating {len(hit_lines)} batter hit props...")

    batter_plays = []
    processed = set()

    for _, row in hit_lines.iterrows():
        player = row["player"]
        if player in processed:
            continue
        if player in EXCLUDE_PLAYERS:
            continue
        processed.add(player)

        # Validate player is in today's games
        home_team = row.get("home", "")
        away_team = row.get("away", "")
        if home_team and away_team:
            pass  # valid game found
        else:
            print(f"  ⚠️ {player}: missing game matchup — skipping")
            continue

        # Get opposing pitcher hand for platoon adjustment
        opp_hand = "R"  # default
        if HAND_AVAILABLE and PITCHER_HANDS:
            home_team = row.get("home", "")
            away_team = row.get("away", "")

            # Determine batter's actual team from roster cache
            batter_team = ""
            if os.path.exists(os.path.join(CACHE_DIR, "rosters.json")):
                import json as _rj
                _rc = _rj.load(open(os.path.join(CACHE_DIR, "rosters.json")))
                _players = _rc.get("players", {})
                _pname   = player.lower()
                for _pid, _pinfo in _players.items():
                    if _pname in _pinfo.get("name","").lower():
                        _team = _pinfo.get("team","")
                        # Match to home or away team
                        if _team.lower() in home_team.lower() or home_team.lower() in _team.lower():
                            batter_team = home_team
                        elif _team.lower() in away_team.lower() or away_team.lower() in _team.lower():
                            batter_team = away_team
                        break

            # Fallback: use away team (original behavior)
            if not batter_team:
                batter_team = away_team or home_team

            opp_hand, opp_pitcher = get_opposing_hand(
                batter_team, home_team, away_team, PITCHER_HANDS)

            # Store correct opponent team for display
            opp_team_display = away_team if batter_team == home_team else home_team
            row["opp_team"] = opp_team_display

        # Store opp hand in row for evaluate_batter
        row = row.copy()
        row["pitcher_hand"] = opp_hand
        # Inject verified team from roster cache — never trust odds file team
        verified_team = None
        name_lower = player.lower()
        for k, v in teams_cache.items():
            if name_lower in v.get("name","").lower():
                verified_team = v.get("team")
                break
        row["team"] = verified_team or batter_team

        if args.no_pybaseball:
            prior_hits = [int(np.random.binomial(4, 0.28))
                         for _ in range(20)]
        else:
            logs = get_batter_logs(player, season=2026)
            prior_hits = logs.get("hits", []) if logs else []

        if len(prior_hits) >= 3:
            result = evaluate_batter(row, prior_hits, "hits")
            if result:
                batter_plays.append(result)

        # Also evaluate total bases if available
        tb_row = tb_lines[tb_lines["player"] == player]
        if not tb_row.empty and prior_hits:
            # Estimate TB from hits (avg ~1.5 TB per hit)
            prior_tb = [int(h * 1.5) for h in prior_hits]
            result = evaluate_batter(tb_row.iloc[0], prior_tb, "total_bases")
            if result:
                batter_plays.append(result)

    print_plays(pitcher_plays, batter_plays, args.date)

    # ── BUILD FADE PLAYS — simple original system ────────────
    # What was working May 8-13 before over-engineering:
    #   1. L14 avg <= .150 with 10+ AB (book hasn't adjusted)
    #   2. OVER still priced at -150 or worse
    #   3. UNDER is plus money (+100 or better) — value built in
    #   4. Sort by consecutive hitless games (active cold streak first)
    #      then L14 avg ascending (coldest bat second)
    #
    # xBA shown as informational label only — not a gate or sort key
    # K UNDERs handled separately by mlb_pitcher_under.py — not mixed in
    #
    # SECONDARY MODEL (experimental, runs in parallel, saved separately):
    #   Tiered system with xBA gates, .120 threshold, edge ranking
    #   Graded daily vs primary — if it outperforms over 30+ days, promote

    import re as _re

    fade_plays     = []   # primary — simple cold streak system
    fade_plays_exp = []   # experimental — tiered/xBA system

    for name, reason in EXCLUDE_PLAYERS.items():
        player_props = df[df["player"] == name]
        hit_over     = player_props[player_props["prop"] == "hits"]
        hit_under    = player_props[player_props["prop"] == "hits_under"]

        if hit_over.empty:
            continue

        over_odds  = int(hit_over.iloc[0]["odds"])
        under_odds = int(hit_under.iloc[0]["odds"]) if not hit_under.empty else (
            abs(over_odds)-75 if over_odds <= -200 else
            abs(over_odds)-40 if over_odds <= -150 else -110
        )

        # ── PRIMARY GATE: OVER must be -150 or worse ──────────
        # If book has already adjusted to +100 OVER, fade value is gone
        if over_odds > -150:
            continue

        # ── PRIMARY GATE: UNDER must be plus money ────────────
        if under_odds <= 0:
            continue

        # Parse L14 avg
        avg_match = _re.search(r'\.(\d{3})', reason)
        l14_avg   = float("0." + avg_match.group(1)) if avg_match else 0.150

        # Get xBA as informational label only
        xba_diff  = 0.0
        xba_lucky = False
        if SAVANT_AVAILABLE:
            signals  = get_player_signals(name)
            xba_diff = signals.get("xba_diff", 0.0) or 0.0
            xba_lucky = xba_diff < -0.030

        # Estimate hitless streak from L5 rate
        # Used for sorting — most active cold streak gets top billing
        player_play = next(
            (p for p in batter_plays
             if p and p.get("player","").lower() == name.lower()),
            None
        )
        hitless_streak = 0
        if player_play:
            hit_streak = player_play.get("streak", 0)
            if hit_streak == 0:
                l5 = player_play.get("l5", 0.5)
                if l5 == 0.0:
                    hitless_streak = 5
                elif l5 <= 0.20:
                    hitless_streak = 3
                else:
                    hitless_streak = 1

        entry = {
            "player":         name,
            "prop":           "hits",
            "line":           float(hit_over.iloc[0]["line"]),
            "over_odds":      over_odds,
            "under_odds":     under_odds,
            "reason":         reason,
            "type":           "FADE",
            "l14_avg":        l14_avg,
            "hitless_streak": hitless_streak,
            # xBA informational only — shown on card, not used for sorting
            "xba_lucky":      xba_lucky,
            "xba_diff":       round(xba_diff, 3),
        }
        fade_plays.append(entry)

        # ── EXPERIMENTAL v2: pitcher-matchup composite ─────────
        # Loosened l14 gate (.150) since pitcher signal now gates quality.
        # Ranks by cold_severity * pitcher_K_factor instead of pure edge.
        if l14_avg <= 0.150:
            b_row = next((b for b in batter_plays
                          if b and b.get("player","").lower() == name.lower()),
                         None)
            if not b_row:
                continue
            home_team = b_row.get("home", "")
            opp_pitcher_name = None
            if HAND_AVAILABLE and PITCHER_HANDS:
                try:
                    from mlb_pitcher_hand import get_opposing_hand
                    _, opp_pitcher_name = get_opposing_hand(
                        b_row.get("team", ""), home_team, PITCHER_HANDS
                    )
                except Exception:
                    opp_pitcher_name = None
            if not opp_pitcher_name:
                continue
            opp_p = next((p for p in pitcher_plays
                          if p and p.get("player","").lower() == opp_pitcher_name.lower()),
                         None)
            if not opp_p:
                continue
            cold_severity    = max(0.0, (0.250 - l14_avg) / 0.250)
            pitcher_K_factor = float(opp_p.get("l5_avg", 5.5)) / 5.5
            fade_score       = round(cold_severity * pitcher_K_factor, 4)
            if under_odds > 0:
                u_implied = 100 / (under_odds + 100)
            else:
                u_implied = abs(under_odds) / (abs(under_odds) + 100)
            exp_entry = {**entry}
            exp_entry["model"]             = "experimental_v2_pitcher_matchup"
            exp_entry["opp_pitcher"]       = opp_pitcher_name
            exp_entry["opp_pitcher_l5"]    = opp_p.get("l5_avg")
            exp_entry["opp_pitcher_k_pct"] = opp_p.get("opp_k_pct")
            exp_entry["cold_severity"]     = round(cold_severity, 3)
            exp_entry["pitcher_K_factor"]  = round(pitcher_K_factor, 3)
            exp_entry["fade_score"]        = fade_score
            exp_entry["fade_edge"]         = round(1.0 - u_implied - l14_avg, 4)
            fade_plays_exp.append(exp_entry)

    # ── PRIMARY SORT: active cold streak first, then coldest L14 ──
    fade_plays.sort(key=lambda x: (
        -x["hitless_streak"],   # most consecutive hitless first
        x["l14_avg"],           # coldest L14 avg second
    ))

    # ── EXPERIMENTAL SORT: cold × pitcher composite ───────────
    fade_plays_exp.sort(key=lambda x: -x.get("fade_score", 0))

    # ── PRINT PRIMARY FADES ───────────────────────────────────
    if fade_plays:
        print("\n" + "="*65)
        print(f"📉 FADE PLAYS — Cold Streak Batters (original system)")
        print(f"  Gate: OVER <= -150, UNDER plus money, L14 <= .150")
        print(f"  Sort: active hitless streak first, coldest L14 second")
        print(f"{'='*65}")
        print(f"  {'PLAYER':26} {'OVER':8} {'UNDER':8} "
              f"{'L14':6} {'FLAG'}")
        print(f"  {'─'*60}")
        for p in fade_plays[:10]:
            over_str   = f"{p['over_odds']:+d}"
            under_str  = f"{p['under_odds']:+d}"
            l14_str    = f".{int(p['l14_avg']*1000):03d}"
            xba_flag   = " ⚠️ LUCKY" if p["xba_lucky"] else ""
            streak_flag = f" {p['hitless_streak']}g hitless" if p["hitless_streak"] >= 3 else ""
            print(f"  {p['player']:26} {over_str:8} {under_str:8} "
                  f"{l14_str:6}{xba_flag}{streak_flag}")

        if fade_plays_exp:
            print(f"\n  [experimental v2 (pitcher matchup): {len(fade_plays_exp)} "
                  f"plays — top 5 by fade_score:")
            for p in fade_plays_exp[:5]:
                print(f"    {p['player']:24} vs {p['opp_pitcher']:20} "
                      f"L14:{p['l14_avg']:.3f}  P_K:{p['opp_pitcher_l5']:.1f}  "
                      f"score:{p['fade_score']:.3f}")

    out = {
        "date":          args.date,
        "generated":     datetime.now().isoformat(),
        "pitcher_plays": [p for p in pitcher_plays if p],
        "batter_plays":  [p for p in batter_plays  if p],
        "fade_plays":    fade_plays,
    }
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_plays_{args.date}.json"
    )
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved to mlb_plays_{args.date}.json")

    # ── SAVE EXPERIMENTAL MODEL SEPARATELY ────────────────────
    if fade_plays_exp:
        exp_out = {
            "date":      args.date,
            "model":     "experimental_tiered",
            "note":      "Tighter .120 threshold + edge ranking. "
                         "Grade daily vs primary to validate.",
            "fade_plays": fade_plays_exp,
        }
        exp_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"mlb_plays_experimental_{args.date}.json"
        )
        with open(exp_path, "w") as f:
            json.dump(exp_out, f, indent=2, default=str)
        print(f"Saved experimental model → mlb_plays_experimental_{args.date}.json")
