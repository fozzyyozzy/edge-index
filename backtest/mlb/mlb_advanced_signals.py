"""
Edge Index — Advanced MLB Signal Engine
Adds the edges that markets haven't fully priced:
  - Catcher framing scores
  - Pitcher L/R platoon splits
  - Lineup K-rate (projected lineup, not season avg)
  - Total Outs cross-reference
  - Walk-prone pitcher TB fade
  - Alt line EV comparison
  - Lineup spot PA tracker
"""
import os, json
import numpy as np

# ── CATCHER FRAMING SCORES ────────────────────────────────────
# Baseball Savant framing runs above average (2024-2025)
# Positive = better framer = boost pitcher K props
# Source: baseball.savant.mlb.com/leaderboard/catcher-framing
CATCHER_FRAMING = {
    # Elite framers (boost K props +5-8%)
    "Patrick Bailey":      +12.4,
    "Cal Raleigh":         +10.8,
    "Jose Trevino":        +9.2,
    "Austin Hedges":       +8.6,
    "Christian Bethancourt":+7.4,
    "Shea Langeliers":     +6.8,
    "Adley Rutschman":     +6.2,
    "Tyler Stephenson":    +5.8,
    "Jonah Heim":          +5.4,
    "Ryan Jeffers":        +4.8,
    # Average framers (neutral)
    "J.T. Realmuto":       +2.1,
    "Sean Murphy":         +1.8,
    "Will Smith":          +1.4,
    "Salvador Perez":      +0.8,
    "Danny Jansen":        +0.4,
    "Bo Naylor":           -0.2,
    # Poor framers (fade K props -3-6%)
    "Yasmani Grandal":     -4.2,
    "Keibert Ruiz":        -5.6,
    "Gary Sanchez":        -6.8,
    "Travis d'Arnaud":     -3.4,
    "Francisco Mejia":     -7.2,
    "Luis Campusano":      -8.4,
}

def get_framing_adj(catcher_name):
    """
    Convert framing runs to K probability adjustment.
    Scale: ~1 framing run = ~0.004 K probability
    """
    runs = CATCHER_FRAMING.get(catcher_name, 0)
    adj  = runs * 0.004
    return round(adj, 3)

# ── PITCHER PLATOON SPLITS ────────────────────────────────────
# L/R K-rate splits for key pitchers (2024-2025)
# Format: {pitcher: {vs_L: k_rate, vs_R: k_rate}}
PITCHER_SPLITS = {
    "Dylan Cease": {
        "vs_R": 0.318, "vs_L": 0.268,
        "platoon_gap": 0.050,
        "note": "Slider-heavy, better vs RHB"
    },
    "Jesus Luzardo": {
        "vs_R": 0.285, "vs_L": 0.312,
        "platoon_gap": -0.027,
        "note": "Better vs LHB (changeup dominant)"
    },
    "Max Fried": {
        "vs_R": 0.245, "vs_L": 0.198,
        "platoon_gap": 0.047,
        "note": "Curveball vs RHB, standard LHP platoon"
    },
    "Kyle Bradish": {
        "vs_R": 0.292, "vs_L": 0.241,
        "platoon_gap": 0.051,
        "note": "Slider dominant vs RHB"
    },
    "Reid Detmers": {
        "vs_R": 0.268, "vs_L": 0.198,
        "platoon_gap": 0.070,
        "note": "Standard LHP — tough vs LHB"
    },
    "Gerrit Cole": {
        "vs_R": 0.335, "vs_L": 0.288,
        "platoon_gap": 0.047,
        "note": "Elite vs both, slight RHB edge"
    },
    "Zack Wheeler": {
        "vs_R": 0.312, "vs_L": 0.278,
        "platoon_gap": 0.034,
        "note": "Split-finger, effective vs both"
    },
    "Nick Lodolo": {
        "vs_R": 0.298, "vs_L": 0.218,
        "platoon_gap": 0.080,
        "note": "LHP — significant platoon advantage"
    },
    "Chase Dollander": {
        "vs_R": 0.285, "vs_L": 0.252,
        "platoon_gap": 0.033,
        "note": "Young, developing — slight RHB edge"
    },
}

def get_platoon_adj(pitcher_name, lineup_pct_left):
    """
    Adjust K probability based on opposing lineup handedness.
    lineup_pct_left: fraction of lineup that bats left-handed (0.0-1.0)
    """
    splits = PITCHER_SPLITS.get(pitcher_name)
    if not splits:
        return 0.0, "No split data available"

    vs_R = splits["vs_R"]
    vs_L = splits["vs_L"]

    # Weighted K-rate based on lineup composition
    effective_k_rate = (vs_R * (1 - lineup_pct_left) +
                        vs_L * lineup_pct_left)

    # Compare to season average (50/50 baseline)
    baseline = (vs_R + vs_L) / 2
    adj      = (effective_k_rate - baseline) * 1.5  # amplify signal

    direction = "lineup stacked L" if lineup_pct_left > 0.55 else \
                "lineup stacked R" if lineup_pct_left < 0.35 else "balanced"

    note = f"{splits['note']} | {direction} ({lineup_pct_left*100:.0f}% LHB)"
    return round(adj, 3), note

# ── TOTAL OUTS CROSS-REFERENCE ────────────────────────────────
def outs_k_sanity_check(k_line, outs_line):
    """
    Cross-reference K line against Total Outs line.
    If market expects short outing but high Ks = risky OVER.

    k_line:   e.g. 6.5
    outs_line: e.g. 15.5 (= ~5.2 innings expected)
    """
    if not outs_line:
        return 0.0, "No outs line available"

    innings_expected = outs_line / 3
    k_per_9 = (k_line / innings_expected) * 9

    if k_per_9 > 11:
        adj  = -0.06
        note = f"HIGH RISK: Needs {k_per_9:.1f} K/9 in only {innings_expected:.1f} IP — book expects short + dominant"
    elif k_per_9 > 9:
        adj  = -0.02
        note = f"Slight risk: {k_per_9:.1f} K/9 needed in {innings_expected:.1f} IP"
    elif k_per_9 < 7:
        adj  = +0.04
        note = f"Favorable: Only {k_per_9:.1f} K/9 needed — long outing expected ({innings_expected:.1f} IP)"
    else:
        adj  = 0.0
        note = f"Neutral: {k_per_9:.1f} K/9 in {innings_expected:.1f} IP expected"

    return round(adj, 3), note

# ── WALK-PRONE TB FADE ────────────────────────────────────────
def walk_prone_tb_fade(pitcher_bb_pct, batter_name):
    """
    If pitcher walks a lot AND batter draws walks,
    TB OVER is risky (walks don't count for TB).
    """
    walk_prone_batters = {
        "Juan Soto":      0.185,
        "Aaron Judge":    0.168,
        "Bryce Harper":   0.156,
        "Yordan Alvarez": 0.142,
        "Freddie Freeman":0.118,
        "Kyle Tucker":    0.138,
        "Mookie Betts":   0.122,
        "Mike Trout":     0.178,
        "Jose Abreu":     0.098,
    }

    batter_bb_pct = walk_prone_batters.get(batter_name, 0.085)

    # If both pitcher BB% and batter BB% are high = fade TB
    combined_walk_risk = pitcher_bb_pct * batter_bb_pct * 100

    if pitcher_bb_pct >= 0.10 and batter_bb_pct >= 0.13:
        adj  = -0.07
        note = f"FADE TB: Walk-prone pitcher ({pitcher_bb_pct*100:.1f}% BB) vs {batter_name} ({batter_bb_pct*100:.1f}% BB) — likely walk(s)"
    elif pitcher_bb_pct >= 0.08 and batter_bb_pct >= 0.12:
        adj  = -0.03
        note = f"Mild TB risk: Walk matchup ({pitcher_bb_pct*100:.1f}% vs {batter_bb_pct*100:.1f}%)"
    else:
        adj  = 0.0
        note = ""

    return round(adj, 3), note

# ── ALT LINE EV CALCULATOR ────────────────────────────────────
def compare_alt_lines(model_prob, lines_and_odds):
    """
    Given model probability, find the highest EV alt line.

    lines_and_odds: list of (line, odds, hit_prob_at_line)
    Returns ranked list by EV.
    """
    results = []
    for line, odds, hit_prob in lines_and_odds:
        if odds < 0:
            decimal = 1 + (100 / abs(odds))
        else:
            decimal = 1 + (odds / 100)

        ev = hit_prob * (decimal - 1) - (1 - hit_prob)
        results.append({
            "line":     line,
            "odds":     odds,
            "hit_prob": round(hit_prob, 3),
            "decimal":  round(decimal, 3),
            "ev":       round(ev, 4),
        })

    results.sort(key=lambda x: x["ev"], reverse=True)
    return results

def find_best_k_line(pitcher_name, model_prob, posted_lines):
    """
    Given a pitcher and their model K probability at main line,
    estimate probabilities at alt lines and find best EV.
    """
    if not posted_lines:
        return []

    main_line, main_odds = posted_lines[0]

    # Model probability at each alt line
    # Use normal distribution around expected K total
    expected_ks = main_line + (model_prob - 0.5) * 3
    std_dev      = max(1.5, expected_ks * 0.25)

    from scipy import stats
    alt_data = []
    for line, odds in posted_lines:
        # P(actual Ks >= line) using normal approximation
        prob = 1 - stats.norm.cdf(line - 0.5, expected_ks, std_dev)
        alt_data.append((line, odds, prob))

    return compare_alt_lines(model_prob, alt_data)

# ── LINEUP SPOT PA TRACKER ────────────────────────────────────
def lineup_spot_pa_adj(lineup_spot_today, lineup_spot_usual, game_total=8.5):
    """
    Estimate additional PA from batting order change.
    Moving up in lineup = more plate appearances.
    """
    if lineup_spot_today == lineup_spot_usual:
        return 0.0, ""

    # Average PAs per spot in 9-inning game
    pa_by_spot = {1:4.3, 2:4.2, 3:4.1, 4:4.0, 5:3.9,
                  6:3.8, 7:3.7, 8:3.6, 9:3.5}

    pa_today  = pa_by_spot.get(lineup_spot_today, 3.8)
    pa_usual  = pa_by_spot.get(lineup_spot_usual, 3.8)
    pa_diff   = pa_today - pa_usual

    if pa_diff >= 0.4:
        adj  = +0.06
        note = f"Lineup boost: {lineup_spot_usual}→{lineup_spot_today} (+{pa_diff:.1f} PA) — books may be slow to adjust"
    elif pa_diff >= 0.2:
        adj  = +0.03
        note = f"Minor lineup boost: {lineup_spot_usual}→{lineup_spot_today} (+{pa_diff:.1f} PA)"
    elif pa_diff <= -0.4:
        adj  = -0.05
        note = f"Lineup drop: {lineup_spot_usual}→{lineup_spot_today} ({pa_diff:.1f} PA)"
    else:
        adj  = 0.0
        note = ""

    return round(adj, 3), note

# ── FULL ADVANCED SIGNAL PACKAGE ─────────────────────────────
def get_advanced_signals(
    pitcher_name     = "",
    catcher_name     = "",
    lineup_pct_left  = 0.50,
    k_line           = 6.5,
    outs_line        = None,
    pitcher_bb_pct   = 0.08,
    batter_name      = "",
    lineup_spot_today  = None,
    lineup_spot_usual  = None,
):
    """
    Run all advanced signals and return combined adjustment + notes.
    """
    total_adj = 0.0
    all_notes = []

    # 1. Catcher framing
    if catcher_name:
        adj = get_framing_adj(catcher_name)
        if abs(adj) > 0.01:
            runs = CATCHER_FRAMING.get(catcher_name, 0)
            direction = "elite framer" if runs > 5 else "poor framer" if runs < -3 else "average framer"
            all_notes.append(f"Catcher {catcher_name}: {direction} ({runs:+.1f} framing runs, {adj:+.3f} adj)")
            total_adj += adj

    # 2. Platoon splits
    if pitcher_name and lineup_pct_left != 0.50:
        adj, note = get_platoon_adj(pitcher_name, lineup_pct_left)
        if abs(adj) > 0.01:
            all_notes.append(f"Platoon: {note} ({adj:+.3f} adj)")
            total_adj += adj

    # 3. Outs cross-reference
    if outs_line and k_line:
        adj, note = outs_k_sanity_check(k_line, outs_line)
        if note:
            all_notes.append(f"Outs check: {note} ({adj:+.3f} adj)")
            total_adj += adj

    # 4. Walk-prone TB fade
    if batter_name and pitcher_bb_pct:
        adj, note = walk_prone_tb_fade(pitcher_bb_pct, batter_name)
        if note:
            all_notes.append(f"Walk risk: {note}")
            total_adj += adj

    # 5. Lineup spot
    if lineup_spot_today and lineup_spot_usual and lineup_spot_today != lineup_spot_usual:
        adj, note = lineup_spot_pa_adj(lineup_spot_today, lineup_spot_usual)
        if note:
            all_notes.append(f"PA boost: {note} ({adj:+.3f} adj)")
            total_adj += adj

    return round(total_adj, 3), all_notes

# ── DEMO ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*65)
    print("EDGE INDEX — Advanced Signal Engine Demo")
    print("="*65)

    # Dylan Cease tonight
    print("\nDylan Cease — K OVER 7.5 vs TOR")
    adj, notes = get_advanced_signals(
        pitcher_name    = "Dylan Cease",
        catcher_name    = "Cal Raleigh",
        lineup_pct_left = 0.44,  # TOR lineup: 4 of 9 bat left
        k_line          = 7.5,
        outs_line       = 17.5,  # book expects ~5.8 innings
        pitcher_bb_pct  = 0.072,
    )
    print(f"  Total adjustment: {adj:+.3f}")
    for n in notes:
        print(f"  → {n}")

    # Alt line EV comparison
    print("\nAlt Line EV — Dylan Cease Ks:")
    alt_results = find_best_k_line("Dylan Cease", 0.72, [
        (5.5, -220), (6.5, -165), (7.5, -144),
        (8.5, +115), (9.5, +200), (10.5, +380),
    ])
    for r in alt_results:
        flag = " ← BEST EV" if r == alt_results[0] else ""
        print(f"  K OVER {r['line']} ({r['odds']:+}) | Hit prob: {r['hit_prob']*100:.0f}% | EV: {r['ev']:+.3f}{flag}")

    # Walk-prone TB check
    print("\nJuan Soto TB OVER 1.5 vs walk-prone pitcher:")
    adj, note = walk_prone_tb_fade(0.112, "Juan Soto")
    print(f"  Adjustment: {adj:+.3f}")
    print(f"  Note: {note}")

    # Lineup spot boost
    print("\nBatter moved 7→2 in lineup:")
    adj, note = lineup_spot_pa_adj(2, 7)
    print(f"  Adjustment: {adj:+.3f}")
    print(f"  Note: {note}")

    print("\n" + "="*65)
    print("Wire into mlb_run_today.py via get_advanced_signals()")
    print("="*65)
