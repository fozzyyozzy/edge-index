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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))

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
def get_pitcher_logs(player_name, season=2025):
    """Pull pitcher K totals per start via pybaseball."""
    try:
        import pybaseball
        pybaseball.cache.enable()

        parts = player_name.split()
        if len(parts) < 2:
            return []

        # Try last name, first name
        # Normalize special characters (Jesús → Jesus etc)
        import unicodedata
        def normalize(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s)
                          if unicodedata.category(c) != 'Mn').lower()

        # Try exact lookup first
        lookup = pybaseball.playerid_lookup(parts[-1], parts[0])

        # Try normalized (strips accents)
        if lookup.empty:
            norm_last  = normalize(parts[-1])
            norm_first = normalize(parts[0])
            lookup = pybaseball.playerid_lookup(norm_last, norm_first)

        # Try last name only for common names
        if lookup.empty and len(parts) > 1:
            lookup = pybaseball.playerid_lookup(parts[-1])
            if not lookup.empty:
                # Filter by first name match (normalized)
                lookup = lookup[lookup['name_first'].apply(
                    lambda x: normalize(str(x))) == normalize(parts[0])]

        if lookup.empty:
            print(f"    No ID found for {player_name}")
            return []
        
        # Filter to active players (born after 1985)
        if 'birth_year' in lookup.columns:
            lookup = lookup[lookup['birth_year'] >= 1985]
        if lookup.empty:
            return []

        mlb_id = lookup.iloc[0].get('key_mlbam')
        if not mlb_id:
            return []

        start = f"{season}-03-01"
        end   = f"{season}-11-01"
        data  = pybaseball.statcast_pitcher(start, end, player_id=int(mlb_id))

        if data.empty:
            return []

        data['game_date'] = pd.to_datetime(data['game_date']).dt.date.astype(str)
        grouped = data.groupby('game_date').apply(lambda g: (
            g['events'].isin(['strikeout','strikeout_double_play']).sum()
        )).reset_index()
        grouped.columns = ['game_date','strikeouts']
        grouped = grouped.sort_values('game_date')

        return grouped['strikeouts'].tolist()

    except Exception as e:
        return []

def get_batter_logs(player_name, season=2025):
    """Pull batter hit totals per game via pybaseball."""
    try:
        import pybaseball
        pybaseball.cache.enable()

        parts = player_name.split()
        if len(parts) < 2:
            return []

        lookup = pybaseball.playerid_lookup(parts[-1], parts[0])
        if lookup.empty:
            return []

        mlb_id = lookup.iloc[0].get('key_mlbam')
        if not mlb_id:
            return []

        start = f"{season}-03-01"
        end   = f"{season}-11-01"
        data  = pybaseball.statcast_batter(start, end, player_id=int(mlb_id))

        if data.empty:
            return []

        data['game_date'] = pd.to_datetime(data['game_date']).dt.date.astype(str)
        grouped = data.groupby('game_date').apply(lambda g:
            g['events'].isin(['single','double','triple','home_run']).sum()
        ).reset_index()
        grouped.columns = ['game_date','hits']

        tb_grouped = data.groupby('game_date').apply(lambda g: (
            g['events'].isin(['single']).sum() * 1 +
            g['events'].isin(['double']).sum() * 2 +
            g['events'].isin(['triple']).sum() * 3 +
            g['events'].isin(['home_run']).sum() * 4
        )).reset_index()
        tb_grouped.columns = ['game_date','total_bases']

        merged = grouped.merge(tb_grouped, on='game_date').sort_values('game_date')
        return {
            'hits':        merged['hits'].tolist(),
            'total_bases': merged['total_bases'].tolist(),
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

    if model_prob >= 0.80 and streak >= 5:
        tier = "AUTO"
    elif model_prob >= 0.65:
        tier = "T1"
    elif model_prob >= 0.55:
        tier = "T2"
    else:
        tier = "SKIP"

    return {
        "player":      row['player'],
        "prop":        prop_type,
        "line":        line,
        "odds":        odds,
        "tier":        tier,
        "model_prob":  round(model_prob, 3),
        "streak":      streak,
        "l5":          round(l5, 3),
        "l10":         round(l10, 3),
        "home":        home,
        "alt_lines":   [max(0.5, line - 1.0), max(0.5, line - 0.5)],
        "prior_games": len(prior_values),
        "parlay_only": parlay_only,
    }

# ── PRINT REPORT ──────────────────────────────────────────────
def print_plays(pitcher_plays, batter_plays, game_date):
    TIER_ORDER = {"AUTO":0, "T1":1, "T2":2, "SKIP":3}

    print(f"\n{'='*65}")
    print(f"EDGE INDEX MLB — {game_date}")
    print(f"Real DK/FD/BetMGM lines + pybaseball game logs")
    print(f"{'='*65}")

    p_plays = [p for p in pitcher_plays if p and p["tier"] != "SKIP"]
    b_plays = [p for p in batter_plays  if p and p["tier"] != "SKIP"]

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
            print(f"  Alt lines: {p['alt_lines'][0]}+ / {p['alt_lines'][1]}+")

    if b_plays:
        print(f"\n🏃 BATTER HIT/TOTAL BASE PROPS ({len(b_plays)} plays)")
        print(f"{'─'*65}")
        for p in b_plays[:20]:  # Cap at 20
            tier_icon = {"AUTO":"⚡","T1":"★","T2":"◆"}.get(p["tier"],"")
            flag_str  = " ⚠️ VERIFY CURRENT FORM" if p.get("sanity_flag") else ""
            print(f"\n  {p['player']:28} {tier_icon} {p['tier']}{flag_str}")
            print(f"  {p['prop'].upper()} OVER {p['line']}  |  Odds: {p['odds']:+}  |  Model: {p['model_prob']*100:.0f}%")
            print(f"  Streak: {p['streak']}g  |  L5: {p['l5']*100:.0f}%  L10: {p['l10']*100:.0f}%")

    print(f"\n{'='*65}")
    auto = len([p for p in p_plays+b_plays if p["tier"]=="AUTO"])
    t1   = len([p for p in p_plays+b_plays if p["tier"]=="T1"])
    print(f"Summary: {auto} AUTO plays, {t1} T1 plays")
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
            prior_ks = get_pitcher_logs(player, season=2025)
            print(f" {len(prior_ks)} starts")

        if len(prior_ks) >= 3:
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
        processed.add(player)

        if args.no_pybaseball:
            prior_hits = [int(np.random.binomial(4, 0.28))
                         for _ in range(20)]
        else:
            logs = get_batter_logs(player, season=2025)
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

    # Save output
    out = {
        "date":          args.date,
        "generated":     datetime.now().isoformat(),
        "pitcher_plays": [p for p in pitcher_plays if p],
        "batter_plays":  [p for p in batter_plays  if p],
    }
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_plays_{args.date}.json"
    )
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved to mlb_plays_{args.date}.json")
