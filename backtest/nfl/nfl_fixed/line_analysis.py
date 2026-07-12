import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Edge Index — Line Analysis Engine
For each player+prop this week:
  1. Load their historical avg vs posted line
  2. Calculate line gap (why is it set here?)
  3. Apply matchup adjustments
  4. Produce "why this line is mispriced" narrative
  5. Recommend OVER / UNDER / SKIP with confidence
"""
import sys, os, sqlite3, json
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_setup import get_conn

# Load anchors
ANCHOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "alt_line_anchors.json")

def load_anchors():
    if os.path.exists(ANCHOR_PATH):
        with open(ANCHOR_PATH) as f:
            return json.load(f)
    return {}

PROP_LABELS = {
    "rec_yds":    "Rec Yds",
    "receptions": "Receptions",
    "rush_yds":   "Rush Yds",
    "pass_yds":   "Pass Yds",
    "pass_att":   "Pass Att",
    "targets":    "Targets",
    "rush_att":   "Rush Att",
}

PROP_MAIN = ["rec_yds","receptions","rush_yds","pass_yds","pass_att"]

# ── LINE GAP ANALYSIS ─────────────────────────────────────────
def analyze_line_gap(avg, std, line, prop):
    """
    How many standard deviations above/below average is the line?
    Positive = line is ABOVE avg (book pricing player down)
    Negative = line is BELOW avg (book pricing player up, easy OVER)
    """
    if std == 0:
        std = max(avg * 0.15, 1)

    gap       = avg - line  # positive = avg above line = OVER value
    gap_sigma = gap / std   # normalized gap

    if gap_sigma > 1.5:
        verdict   = "STRONG OVER — line significantly below average"
        confidence = 0.88
    elif gap_sigma > 0.75:
        verdict   = "LEAN OVER — line below average"
        confidence = 0.72
    elif gap_sigma > 0.25:
        verdict   = "SLIGHT OVER — line slightly below average"
        confidence = 0.62
    elif gap_sigma > -0.25:
        verdict   = "TOSS UP — line near average"
        confidence = 0.52
    elif gap_sigma > -0.75:
        verdict   = "LEAN UNDER — line above average"
        confidence = 0.38
    else:
        verdict   = "FADE — line well above average"
        confidence = 0.25

    return {
        "gap":        round(gap, 1),
        "gap_sigma":  round(gap_sigma, 2),
        "verdict":    verdict,
        "confidence": confidence,
    }

# ── LINE REASON GENERATOR ─────────────────────────────────────
def explain_line(player, pos, prop, line, avg, gap,
                 opp="", spread=0, total=44,
                 wind=0, temp=65, is_dome=False,
                 streak=0, l6=0):
    """
    Generate human-readable explanation of why book set this line.
    """
    reasons_low  = []  # Why book might have set line low
    reasons_high = []  # Why book might have set line high
    our_edge     = []  # Why we still like it

    # ── GAME SCRIPT ───────────────────────────────────────────
    is_favorite = spread < -3
    is_big_fav  = spread < -10
    is_dog      = spread > 3
    high_total  = total >= 48
    low_total   = total <= 40

    if pos == "RB" and prop == "rush_yds":
        if is_big_fav:
            reasons_low.append("Book pricing in game script — big favorites run more")
            our_edge.append(f"Big favorite ({spread:+.1f}) — run game elevated late")
        if is_dog:
            reasons_high.append("Book pricing in trailing game script — less rushing")
        if low_total:
            reasons_low.append("Low total suggests defensive game — fewer plays overall")

    elif pos in ("WR","TE") and prop in ("rec_yds","receptions"):
        if is_big_fav:
            reasons_high.append("Big favorite — offense may go conservative late")
        if is_dog:
            reasons_low.append("Book may be underpricing — trailing teams pass more")
            our_edge.append("Dog game script historically boosts WR/TE volume")
        if high_total:
            reasons_low.append("High total game — more plays = more targets available")
            our_edge.append(f"High total ({total}) suggests shootout pace")

    elif pos == "QB" and prop in ("pass_yds","pass_att"):
        if is_dog:
            reasons_low.append("Book underpricing trailing QB volume")
            our_edge.append("Trailing QBs historically inflate passing stats")
        if is_big_fav:
            reasons_high.append("Book pricing in game management — fewer attempts late")
        if high_total:
            our_edge.append(f"High total ({total}) pushes QB passing volume up")

    # ── WEATHER ───────────────────────────────────────────────
    if not is_dome:
        if wind >= 20:
            reasons_high.append(f"Wind {wind}mph — books suppressing all passing props")
        elif wind >= 12:
            reasons_high.append(f"Wind {wind}mph — slight passing suppression baked in")
            if prop in ("rush_yds","rush_att"):
                our_edge.append(f"Wind {wind}mph may shift to run game — value for rushers")
        if temp <= 32:
            reasons_high.append(f"Freezing temps ({temp}°F) — book pricing cold weather factor")
            if prop == "rush_yds":
                our_edge.append("Cold weather historically favors run game")
        if temp <= 40 and prop in ("rec_yds","receptions","pass_yds"):
            reasons_high.append(f"Cold weather ({temp}°F) suppresses passing slightly")

    # ── MATCHUP ───────────────────────────────────────────────
    if opp:
        if pos == "WR" and prop in ("rec_yds","receptions"):
            our_edge.append(f"Check {opp} slot coverage % — key for projection")
        elif pos == "RB" and prop == "rush_yds":
            our_edge.append(f"Check {opp} rush DVOA — determines ceiling")
        elif pos == "QB" and prop == "pass_yds":
            our_edge.append(f"Check {opp} pass DVOA and blitz % vs {player}")

    # ── STREAK ────────────────────────────────────────────────
    if streak >= 8:
        our_edge.append(f"Active {streak}-game streak — market slow to adjust")
    elif streak >= 5:
        our_edge.append(f"5+ game streak — consistency signal strong")

    if l6 >= 0.85:
        our_edge.append(f"L6 hit rate {l6*100:.0f}% — book may not be accounting for trend")

    return {
        "reasons_line_low":  reasons_low,
        "reasons_line_high": reasons_high,
        "our_edge":          our_edge,
    }

# ── FULL PLAYER ANALYSIS ──────────────────────────────────────
def analyze_player(name, pos, team, opp, prop, posted_line, odds,
                   prior_values, spread=0, total=44,
                   wind=0, temp=65, is_dome=False,
                   anchors=None):
    """
    Full analysis of a single player prop.
    """
    if len(prior_values) < 3:
        return None

    values = prior_values[-20:]  # Last 20 games
    avg    = np.mean(values)
    std    = np.std(values)
    l6     = sum(1 for v in values[-6:] if v >= posted_line) / min(6, len(values))
    l10    = sum(1 for v in values[-10:] if v >= posted_line) / min(10, len(values))

    # Streak
    streak = 0
    for v in reversed(values):
        if v >= posted_line:
            streak += 1
        else:
            break

    # Line gap analysis
    gap_analysis = analyze_line_gap(avg, std, posted_line, prop)

    # Narrative
    narrative = explain_line(
        name, pos, prop, posted_line, avg, gap_analysis["gap"],
        opp=opp, spread=spread, total=total,
        wind=wind, temp=temp, is_dome=is_dome,
        streak=streak, l6=l6
    )

    # Alt lines from anchors
    alt_lines = []
    if anchors and name in anchors:
        prop_data = anchors[name]["props"].get(prop, {})
        if prop_data:
            posted = prop_data.get("posted_unique", [])
            # Show lines below the main line (reduced juice OVERs)
            alt_lines = [l for l in posted if l < posted_line and l >= posted_line * 0.6]

    # Historical line vs avg comparison
    avg_posted_line = None
    if anchors and name in anchors:
        prop_data = anchors[name]["props"].get(prop, {})
        if prop_data:
            avg_posted_line = prop_data.get("avg_line")

    return {
        "player":          name,
        "pos":             pos,
        "team":            team,
        "opp":             opp,
        "prop":            prop,
        "posted_line":     posted_line,
        "odds":            odds,
        "avg_20":          round(avg, 1),
        "std":             round(std, 1),
        "l6":              round(l6, 3),
        "l10":             round(l10, 3),
        "streak":          streak,
        "gap":             gap_analysis["gap"],
        "gap_sigma":       gap_analysis["gap_sigma"],
        "verdict":         gap_analysis["verdict"],
        "confidence":      gap_analysis["confidence"],
        "avg_posted_line": avg_posted_line,
        "alt_lines":       alt_lines,
        "narrative":       narrative,
    }

# ── PRINT FULL ANALYSIS ───────────────────────────────────────
def print_analysis(plays, week, season):
    print(f"\n{'='*65}")
    print(f"EDGE INDEX — WEEK {week} {season} LINE ANALYSIS")
    print(f"Why each line is set where it is + where the value lies")
    print(f"{'='*65}")

    # Group by verdict strength
    strong  = [p for p in plays if p["gap_sigma"] > 0.75]
    medium  = [p for p in plays if 0.25 < p["gap_sigma"] <= 0.75]
    fade    = [p for p in plays if p["gap_sigma"] < -0.25]

    for section, label in [
        (strong, "🔥 STRONG VALUE — Line Set Too Low"),
        (medium, "✅ LEAN VALUE — Moderate Edge"),
        (fade,   "❌ FADE — Line Set Too High"),
    ]:
        if not section:
            continue

        print(f"\n{label}")
        print(f"{'─'*65}")

        for p in sorted(section, key=lambda x: x["gap_sigma"], reverse=True):
            prop_label = PROP_LABELS.get(p["prop"], p["prop"])
            print(f"\n  {p['player']} ({p['pos']}, {p['team']}) vs {p['opp']}")
            print(f"  {prop_label.upper()} | Line: {p['posted_line']} ({p['odds']}) | Avg: {p['avg_20']} | Gap: {p['gap']:+.1f}")
            print(f"  L6: {p['l6']*100:.0f}%  L10: {p['l10']*100:.0f}%  Streak: {p['streak']} games")

            if p["avg_posted_line"]:
                line_vs_avg = p["posted_line"] - p["avg_posted_line"]
                direction = "ABOVE" if line_vs_avg > 0 else "BELOW"
                print(f"  Line vs season avg posted: {abs(line_vs_avg):.1f} {direction} normal ({p['avg_posted_line']} avg)")

            print(f"  VERDICT: {p['verdict']}")

            narr = p["narrative"]
            if narr["reasons_line_low"]:
                print(f"  Why line might be low:")
                for r in narr["reasons_line_low"]:
                    print(f"    → {r}")
            if narr["reasons_line_high"]:
                print(f"  Why line might be high:")
                for r in narr["reasons_line_high"]:
                    print(f"    → {r}")
            if narr["our_edge"]:
                print(f"  Our edge:")
                for e in narr["our_edge"]:
                    print(f"    ✓ {e}")
            if p["alt_lines"]:
                print(f"  Alt lines (reduced juice): {p['alt_lines']}")

    # Summary table
    print(f"\n{'='*65}")
    print(f"QUICK REFERENCE — Week {week}")
    print(f"{'='*65}")
    print(f"{'Player':<22} {'Prop':<12} {'Line':>6} {'Avg':>6} {'Gap':>6} {'L6':>5} {'Str':>4}  Verdict")
    print(f"{'─'*65}")
    for p in sorted(plays, key=lambda x: x["gap_sigma"], reverse=True):
        prop_l = PROP_LABELS.get(p["prop"], p["prop"])[:11]
        flag = "🔥" if p["gap_sigma"]>0.75 else "✅" if p["gap_sigma"]>0.25 else "⚠️" if p["gap_sigma"]>-0.25 else "❌"
        print(f"  {p['player'][:20]:<20} {prop_l:<12} {p['posted_line']:>6.1f} {p['avg_20']:>6.1f} {p['gap']:>+6.1f} {p['l6']*100:>4.0f}% {p['streak']:>3}  {flag}")

# ── DEMO RUN ──────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",   type=int, default=1)
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()

    anchors = load_anchors()
    print(f"Loaded anchors for {len(anchors)} players")

    # Demo inputs — replace with live DB query + odds feed
    DEMO = [
        # name, pos, team, opp, prop, line, odds, prior_20, spread, total, wind, temp, dome
        ("Travis Kelce",        "TE","KC", "BAL","receptions",4.5,-180, [7,5,6,5,7,6,8,5,7,6,5,7,6,8,5,7,6,5,7,6], 3.0,47.0,8,52,False),
        ("Travis Kelce",        "TE","KC", "BAL","rec_yds",   42.5,-160,[88,54,72,48,94,66,78,58,88,72,64,82,76,94,58,84,70,62,88,74], 3.0,47.0,8,52,False),
        ("Derrick Henry",       "RB","BAL","KC", "rush_yds",  88.5,-150,[148,124,134,98,156,118,142,128,138,122,112,144,136,126,154,116,140,130,148,122], -3.0,47.0,8,52,False),
        ("Ja'Marr Chase",       "WR","CIN","PIT","rec_yds",   88.5,-120,[127,89,156,98,54,112,78,134,88,145,102,118,76,142,94,128,86,158,96,132], -2.0,48.5,6,48,False),
        ("Jalen Hurts",         "QB","PHI","DAL","rush_yds",  48.5,-145,[64,71,82,58,76,84,68,74,91,78,62,88,72,66,84,78,70,86,74,80], -7.0,46.5,12,61,True),
        ("Saquon Barkley",      "RB","PHI","DAL","rush_yds",  88.5,-140,[112,94,128,76,108,98,134,88,104,121,96,116,84,132,102,118,88,126,106,112], -7.0,46.5,12,61,True),
        ("Patrick Mahomes",     "QB","KC", "BAL","pass_yds",  236.5,-130,[274,254,291,264,242,281,268,294,258,284,271,288,262,278,256,294,268,282,272,286], 3.0,47.0,8,52,False),
        ("CeeDee Lamb",         "WR","DAL","PHI","rec_yds",   88.5,-125,[112,78,94,128,68,88,134,72,104,118,82,124,76,138,92,116,86,128,98,122], 7.0,46.5,12,61,True),
        ("Josh Allen",          "QB","BUF","MIA","rush_yds",  38.5,-130,[42,38,44,40,36,43,39,41,44,40,38,46,36,44,42,38,48,40,42,44], -4.0,50.5,14,42,True),
        ("Tyreek Hill",         "WR","MIA","BUF","rec_yds",   78.5,-110,[94,72,58,86,64,78,102,54,88,74,96,68,84,76,92,62,98,72,86,78], 4.0,50.5,14,42,True),
        ("GB Packers D",        "WR","GB", "CHI","rec_yds",   58.5,-115,[78,62,94,48,86,72,68,84,76,88,64,92,74,82,70,88,66,86,78,84], -3.0,44.5,15,38,False),
        ("Sam LaPorta",         "TE","DET","MIN","receptions",4.5,-150, [6,5,7,4,6,5,6,5,7,6,5,6,4,7,5,6,5,7,6,5], -3.0,46.0,5,55,True),
    ]

    plays = []
    for name,pos,team,opp,prop,line,odds,prior,spread,total,wind,temp,dome in DEMO:
        result = analyze_player(
            name=name, pos=pos, team=team, opp=opp,
            prop=prop, posted_line=line, odds=odds,
            prior_values=prior, spread=spread, total=total,
            wind=wind, temp=temp, is_dome=dome,
            anchors=anchors,
        )
        if result:
            plays.append(result)

    print_analysis(plays, args.week, args.season)
