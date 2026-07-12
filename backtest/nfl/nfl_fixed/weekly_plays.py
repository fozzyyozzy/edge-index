import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Edge Index — Weekly Play Generator
Produces a ranked playbook for the upcoming week combining:
  1. Streak signal (L6/L10 hit rates)
  2. Line edge (avg vs posted line gap)
  3. Game script (spread/total overlay)
  4. Scheme matchup (zone%, blitz%, slot grade)
  5. Correlated player combos (same-game)
  6. Heavy juice parlay builder (-300 to -600)

Usage:
  python weekly_plays.py --week 1 --season 2026
"""
import sys, os, sqlite3, json, argparse
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_setup import get_conn

# ── TIER THRESHOLDS ───────────────────────────────────────────
TIERS = {
    "AUTO":    {"min_prob": 0.80, "min_streak": 5,  "min_l6": 0.75},
    "T1":      {"min_prob": 0.65, "min_streak": 3,  "min_l6": 0.65},
    "T2":      {"min_prob": 0.58, "min_streak": 2,  "min_l6": 0.58},
    "PARLAY":  {"min_prob": 0.75, "min_streak": 0,  "min_l6": 0.60},
}

# ── AMERICAN ODDS MATH ────────────────────────────────────────
def american_to_decimal(odds):
    if odds < 0:
        return 1 + (100 / abs(odds))
    return 1 + (odds / 100)

def decimal_to_american(dec):
    if dec >= 2.0:
        return f"+{round((dec-1)*100)}"
    return f"{round(-100/(dec-1))}"

def parlay_odds(odds_list):
    dec = 1.0
    for o in odds_list:
        dec *= american_to_decimal(o)
    return decimal_to_american(dec), dec

def implied_prob(odds):
    d = american_to_decimal(odds)
    return 1 / d

def edge(model_prob, market_odds):
    market_p = implied_prob(market_odds)
    return model_prob - market_p

# ── CORE SIGNAL CALCULATOR ────────────────────────────────────
def calc_streak(values, line):
    streak = 0
    for v in reversed(values):
        if v >= line:
            streak += 1
        else:
            break
    return streak

def calc_l6(values, line):
    recent = values[-6:] if len(values) >= 6 else values
    if not recent:
        return 0
    return sum(1 for v in recent if v >= line) / len(recent)

def calc_l10(values, line):
    recent = values[-10:] if len(values) >= 10 else values
    if not recent:
        return 0
    return sum(1 for v in recent if v >= line) / len(recent)

# ── LINE EDGE DETECTOR ────────────────────────────────────────
def line_edge_score(avg_val, line, std_dev):
    """
    How far above the line is the player's average?
    Normalized by standard deviation.
    >1.0 = strong edge, >0.5 = moderate, <0 = fade
    """
    if std_dev == 0:
        return (avg_val - line) / max(line * 0.1, 1)
    return (avg_val - line) / std_dev

# ── GAME SCRIPT SIGNAL ────────────────────────────────────────
def game_script_signal(pos, prop_type, spread, total):
    """
    Returns probability boost/fade based on game context.
    spread: negative = team favored (e.g., -7)
    total: over/under for the game
    """
    boost = 0.0
    notes = []

    is_favorite   = spread < -3
    is_big_fav    = spread < -10
    is_dog        = spread > 3
    is_high_total = total >= 48
    is_low_total  = total <= 40

    if pos == "RB" and prop_type == "rush_yds":
        if is_big_fav:
            boost += 0.08
            notes.append(f"Big favorite → run game clock")
        if is_low_total:
            boost += 0.04
            notes.append(f"Low total → ground game")
        if is_dog:
            boost -= 0.06
            notes.append(f"Trailing team abandons run")

    elif pos == "RB" and prop_type in ("receptions", "rec_yds"):
        if is_big_fav:
            boost += 0.10
            notes.append(f"Big fav → checkdown heavy late")
        if is_dog:
            boost += 0.05
            notes.append(f"Trailing → dump-offs increase")
        if is_high_total:
            boost += 0.04
            notes.append(f"High total → more plays = more targets")

    elif pos in ("WR", "TE") and prop_type in ("rec_yds", "receptions"):
        if is_dog:
            boost += 0.07
            notes.append(f"Dog → pass-heavy game script")
        if is_high_total:
            boost += 0.06
            notes.append(f"High total → shootout pace")
        if is_big_fav:
            boost -= 0.05
            notes.append(f"Big fav → game managed late")
        if is_low_total:
            boost -= 0.04
            notes.append(f"Low total → suppresses passing")

    elif pos == "QB" and prop_type in ("pass_yds", "pass_att"):
        if is_dog:
            boost += 0.08
            notes.append(f"Trailing QB → volume increases")
        if is_high_total:
            boost += 0.07
            notes.append(f"Shootout → QB volume elevated")
        if is_big_fav:
            boost -= 0.07
            notes.append(f"Managing game → attempts drop")
        if is_low_total:
            boost -= 0.04
            notes.append(f"Defensive game → conservative")

    return round(boost, 3), notes

# ── SCHEME SIGNAL ─────────────────────────────────────────────
def scheme_signal(pos, prop_type, def_team, season):
    """
    Load scheme data if available, return boost and notes.
    """
    try:
        from coaching_data import get_matchup_edges
        result = get_matchup_edges(
            offense_team="",
            defense_team=def_team,
            year=season,
            player_pos=pos,
            prop_type=prop_type,
        )
        return result.get("adjustment", 0.0), result.get("notes", [])
    except Exception:
        return 0.0, []

# ── MAIN PLAY EVALUATOR ───────────────────────────────────────
def evaluate_play(player_name, pos, team, opp, prop_type,
                  line, odds, prior_values,
                  spread=0.0, total=44.0, season=2026):
    """
    Full multi-signal evaluation for a single prop.
    Returns a scored play dict.
    """
    if len(prior_values) < 3:
        return None

    avg   = np.mean(prior_values[-10:])
    std   = np.std(prior_values[-10:]) if len(prior_values) >= 4 else max(avg*0.2, 1)
    l6    = calc_l6(prior_values, line)
    l10   = calc_l10(prior_values, line)
    streak = calc_streak(prior_values, line)
    le    = line_edge_score(avg, line, std)

    # Base probability from L6 rate
    base_prob = l6 * 0.55 + l10 * 0.25

    # Streak bonus
    if streak >= 10:
        streak_bonus = 0.15
    elif streak >= 6:
        streak_bonus = 0.08
    elif streak >= 3:
        streak_bonus = 0.02
    elif streak == 0:
        streak_bonus = -0.05
    else:
        streak_bonus = 0.0

    # Line edge bonus
    if le > 1.5:
        line_bonus = 0.10
    elif le > 0.75:
        line_bonus = 0.06
    elif le > 0.25:
        line_bonus = 0.03
    elif le < -0.5:
        line_bonus = -0.08
    else:
        line_bonus = 0.0

    # Game script
    gs_boost, gs_notes = game_script_signal(pos, prop_type, spread, total)

    # Scheme
    sc_boost, sc_notes = scheme_signal(pos, prop_type, opp, season)

    # Final probability
    model_prob = min(0.97, max(0.20,
        base_prob + streak_bonus + line_bonus + gs_boost + sc_boost
    ))

    # Edge vs market
    mkt_edge = edge(model_prob, odds)

    # Tier
    if model_prob >= TIERS["AUTO"]["min_prob"] and streak >= TIERS["AUTO"]["min_streak"] and l6 >= TIERS["AUTO"]["min_l6"]:
        tier = "AUTO"
    elif model_prob >= TIERS["T1"]["min_prob"] and l6 >= TIERS["T1"]["min_l6"]:
        tier = "T1"
    elif model_prob >= TIERS["T2"]["min_prob"] and l6 >= TIERS["T2"]["min_l6"]:
        tier = "T2"
    else:
        tier = "SKIP"

    # Build play
    return {
        "player":      player_name,
        "pos":         pos,
        "team":        team,
        "opp":         opp,
        "prop":        prop_type,
        "direction":   "OVER",
        "line":        line,
        "odds":        odds,
        "tier":        tier,
        "model_prob":  round(model_prob, 3),
        "mkt_edge":    round(mkt_edge, 3),
        "streak":      streak,
        "l6":          round(l6, 3),
        "l10":         round(l10, 3),
        "avg_val":     round(avg, 1),
        "line_edge":   round(le, 2),
        "gs_boost":    gs_boost,
        "sc_boost":    sc_boost,
        "notes":       gs_notes + sc_notes,
        "implied_prob": round(implied_prob(odds), 3),
    }

# ── PARLAY BUILDER ────────────────────────────────────────────
def build_parlays(plays, min_legs=2, max_legs=3,
                  target_american_min=-120, target_american_max=300):
    """
    Build parlays from high-confidence plays.
    Target: even money to +300 range.
    Prioritize heavy juice plays (-300 to -600) that combine to even money.
    """
    # Filter parlay candidates — high prob regardless of odds
    candidates = [p for p in plays
                  if p["model_prob"] >= TIERS["PARLAY"]["min_prob"]
                  and p["tier"] in ("AUTO","T1")]

    # Sort by model prob
    candidates.sort(key=lambda x: x["model_prob"], reverse=True)

    parlays = []
    used = set()

    # Build 2-leg and 3-leg parlays
    for i, p1 in enumerate(candidates):
        for j, p2 in enumerate(candidates):
            if j <= i:
                continue
            # Avoid same player different props
            if p1["player"] == p2["player"]:
                continue

            legs_2 = [p1, p2]
            odds_2, dec_2 = parlay_odds([p1["odds"], p2["odds"]])
            hit_prob_2 = p1["model_prob"] * p2["model_prob"]

            # Check if 2-leg is in target range
            am_2 = (dec_2-1)*100 if dec_2 >= 2 else -100/(dec_2-1)
            if target_american_min <= am_2 <= target_american_max:
                parlays.append({
                    "legs": legs_2,
                    "odds": odds_2,
                    "decimal": round(dec_2, 3),
                    "hit_prob": round(hit_prob_2, 3),
                    "ev": round(hit_prob_2 * (dec_2-1) - (1-hit_prob_2), 3),
                    "type": "2-leg",
                })

            # Try adding a 3rd leg
            for k, p3 in enumerate(candidates):
                if k <= j:
                    continue
                if p3["player"] in (p1["player"], p2["player"]):
                    continue

                legs_3 = [p1, p2, p3]
                odds_3, dec_3 = parlay_odds([p1["odds"], p2["odds"], p3["odds"]])
                hit_prob_3 = p1["model_prob"] * p2["model_prob"] * p3["model_prob"]

                am_3 = (dec_3-1)*100 if dec_3 >= 2 else -100/(dec_3-1)
                if target_american_min <= am_3 <= target_american_max:
                    parlays.append({
                        "legs": legs_3,
                        "odds": odds_3,
                        "decimal": round(dec_3, 3),
                        "hit_prob": round(hit_prob_3, 3),
                        "ev": round(hit_prob_3 * (dec_3-1) - (1-hit_prob_3), 3),
                        "type": "3-leg",
                    })

    # Sort by EV
    parlays.sort(key=lambda x: x["ev"], reverse=True)
    return parlays[:10]

# ── REPORT PRINTER ────────────────────────────────────────────
def print_playbook(plays, parlays, week, season):
    print(f"\n{'='*65}")
    print(f"EDGE INDEX — WEEK {week} {season} PLAYBOOK")
    print(f"{'='*65}")

    for tier in ["AUTO", "T1", "T2"]:
        tier_plays = [p for p in plays if p["tier"]==tier]
        if not tier_plays:
            continue

        tier_label = {
            "AUTO": "⚡ AUTO-PLAY (Highest confidence)",
            "T1":   "★ TIER 1 (Strong edge)",
            "T2":   "◆ TIER 2 (Solid play)",
        }[tier]

        print(f"\n{tier_label}")
        print(f"{'─'*65}")

        for p in sorted(tier_plays, key=lambda x: x["model_prob"], reverse=True):
            print(f"\n  {p['player']} ({p['pos']}, {p['team']}) vs {p['opp']}")
            print(f"  {p['prop'].upper()} OVER {p['line']}  |  Odds: {p['odds']}  |  Model: {p['model_prob']*100:.0f}%")
            print(f"  Streak: {p['streak']} games  |  L6: {p['l6']*100:.0f}%  |  Avg: {p['avg_val']}  |  Edge: {p['mkt_edge']*100:+.1f}%")
            if p['notes']:
                for note in p['notes'][:2]:
                    print(f"  → {note}")

    if parlays:
        print(f"\n{'='*65}")
        print(f"🎯 PARLAY BUILDER — Target even money to +300")
        print(f"{'='*65}")

        for i, parl in enumerate(parlays[:5], 1):
            print(f"\n  Parlay #{i} — {parl['type']} | {parl['odds']} | Hit prob: {parl['hit_prob']*100:.1f}% | EV: {parl['ev']:+.2f}")
            for leg in parl['legs']:
                print(f"    • {leg['player']} {leg['prop'].upper()} OVER {leg['line']} ({leg['odds']}) — {leg['model_prob']*100:.0f}%")

    print(f"\n{'='*65}")
    total_auto = len([p for p in plays if p['tier']=='AUTO'])
    total_t1   = len([p for p in plays if p['tier']=='T1'])
    print(f"Summary: {total_auto} AUTO plays, {total_t1} T1 plays, {len(parlays)} parlay combos")
    print(f"{'='*65}\n")

# ── SAMPLE WEEK DEMO ──────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",   type=int, default=1)
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()

    print(f"Edge Index Play Generator — Week {args.week} {args.season}")
    print("Running sample with demo data (replace with live lines)...\n")

    # Demo plays — replace with real DB query + live odds feed
    DEMO_PLAYS_INPUT = [
        # (player, pos, team, opp, prop, line, odds, prior_10_values, spread, total)
        ("Lamar Jackson",       "QB", "BAL", "KC",  "rush_yds",  38.5, -130, [54,62,48,71,38,44,58,67,42,55], -3.0, 47.0),
        ("Saquon Barkley",      "RB", "PHI", "DAL", "rush_yds",  88.5, -140, [112,94,128,76,108,98,134,88,104,121], -7.0, 46.5),
        ("Saquon Barkley",      "RB", "PHI", "DAL", "receptions",4.5,  -180, [6,5,7,4,6,5,6,5,7,6], -7.0, 46.5),
        ("Ja'Marr Chase",       "WR", "CIN", "PIT", "rec_yds",   72.5, -120, [127,89,156,98,54,112,78,134,88,145], -2.0, 48.5),
        ("Travis Kelce",        "TE", "KC",  "BAL", "receptions",4.5,  -200, [7,5,6,5,7,6,8,5,7,6], 3.0, 47.0),
        ("Jalen Hurts",         "QB", "PHI", "DAL", "rush_yds",  48.5, -145, [64,71,82,58,76,84,68,74,91,78], -7.0, 46.5),
        ("Mark Andrews",        "TE", "BAL", "KC",  "rec_yds",   48.5, -160, [88,72,94,76,108,68,84,78,92,86], -3.0, 47.0),
        ("Christian McCaffrey", "RB", "SF",  "LAR", "receptions",5.5,  -175, [7,8,6,7,8,7,8,6,7,8], -4.5, 48.0),
        ("Davante Adams",       "WR", "GB",  "CHI", "rec_yds",   58.5, -115, [78,62,94,48,86,72,68,84,76,88], -3.0, 44.5),
        ("Josh Allen",          "QB", "BUF", "MIA", "pass_att",  37.5, -130, [42,38,44,40,36,43,39,41,44,40], -4.0, 50.5),
        ("Tyreek Hill",         "WR", "MIA", "BUF", "rec_yds",   68.5, -110, [94,72,58,86,64,78,102,54,88,74], 4.0, 50.5),
        ("Derrick Henry",       "RB", "BAL", "KC",  "rush_yds",  78.5, -150, [148,124,134,98,156,118,142,128,138,122], -3.0, 47.0),
        ("CeeDee Lamb",         "WR", "DAL", "PHI", "rec_yds",   78.5, -125, [112,78,94,128,68,88,134,72,104,118], 7.0, 46.5),
        ("Brock Purdy",         "QB", "SF",  "LAR", "pass_yds", 268.5, -130, [274,291,264,281,268,294,258,284,271,288], -4.5, 48.0),
        ("Amon-Ra St. Brown",   "WR", "DET", "MIN", "receptions",5.5,  -160, [7,6,8,7,6,9,7,8,6,8], -3.0, 46.0),
    ]

    plays = []
    for player, pos, team, opp, prop, line, odds, prior, spread, total in DEMO_PLAYS_INPUT:
        result = evaluate_play(
            player_name=player, pos=pos, team=team, opp=opp,
            prop_type=prop, line=line, odds=odds,
            prior_values=prior, spread=spread, total=total,
            season=args.season,
        )
        if result and result["tier"] != "SKIP":
            plays.append(result)

    plays.sort(key=lambda x: x["model_prob"], reverse=True)
    parlays = build_parlays(plays)
    print_playbook(plays, parlays, args.week, args.season)

    # Show parlay math demo
    print("PARLAY MATH EXAMPLES:")
    print("─"*40)
    examples = [
        ([-180, -175, -160], "Kelce + CMC + Andrews"),
        ([-140, -145, -130], "Barkley rush + Hurts rush + Allen att"),
        ([-200, -160],       "Kelce + Andrews (2-leg)"),
    ]
    for odds_list, label in examples:
        result_odds, dec = parlay_odds(odds_list)
        legs_str = " + ".join(str(o) for o in odds_list)
        hit_prob = 0.88 ** len(odds_list)
        ev = hit_prob * (dec-1) - (1-hit_prob)
        print(f"  {label}")
        print(f"    Legs: {legs_str}")
        print(f"    Parlay odds: {result_odds}  (decimal: {dec:.3f})")
        print(f"    Est hit prob at 88% each: {hit_prob*100:.1f}%")
        print(f"    EV per $100: ${ev*100:+.2f}")
        print()
