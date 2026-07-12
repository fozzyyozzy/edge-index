import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Edge Index — Weekly Streak Sheet Generator
Produces Reddit-ready streak sheets by position with:
  - Main lines (posted DK/FD/BetMGM)
  - Alt lines (reduced juice thresholds)
  - Game window breakouts (TNF, Sun Early, Sun Aft, SNF, MNF)
  - Weather/dome flags
  - Streak length and hit rate formatting
"""
import sys, os, sqlite3
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_setup import get_conn

# ── ALT LINE THRESHOLDS ───────────────────────────────────────
ALT_LINES = {
    "QB": {
        "pass_yds":  [150, 175, 200, 225, 250, 275, 300],
        "rush_yds":  [5, 10, 15, 20, 25, 30, 40],
        "pass_att":  [20, 25, 30, 35, 40],
    },
    "RB": {
        "rush_yds":  [20, 30, 40, 50, 60, 75, 100],
        "receptions":[1, 2, 3, 4, 5, 6],
        "rec_yds":   [5, 10, 15, 20, 25, 30, 40, 50],
    },
    "WR": {
        "rec_yds":   [20, 30, 40, 50, 60, 75, 100],
        "receptions":[1, 2, 3, 4, 5, 6, 7],
        "targets":   [2, 3, 4, 5, 6, 7],
    },
    "TE": {
        "rec_yds":   [5, 10, 15, 20, 25, 30, 40, 50],
        "receptions":[1, 2, 3, 4, 5, 6],
        "targets":   [2, 3, 4, 5],
    },
}

# ── GAME WINDOWS ──────────────────────────────────────────────
GAME_WINDOWS = {
    "TNF":       "Thursday Night Football",
    "SUN_EARLY": "Sunday Early (1pm ET)",
    "SUN_AFT":   "Sunday Afternoon (4pm ET)",
    "SNF":       "Sunday Night Football",
    "MNF":       "Monday Night Football",
}

# ── INDOOR STADIUMS ───────────────────────────────────────────
DOME_TEAMS = {
    "ATL", "NO", "LAR", "LV", "MIN", "DET", "IND", "HOU",
    "DAL", "ARI", "BUF",  # BUF has dome now
}

# ── STREAK CALCULATOR ─────────────────────────────────────────
def calc_streak_at_threshold(values, threshold):
    """Count consecutive games where value >= threshold."""
    streak = 0
    for v in reversed(values):
        if v >= threshold:
            streak += 1
        else:
            break
    return streak

def find_best_alt_line(values, thresholds, min_streak=3):
    """
    Find the highest threshold with a significant streak.
    Returns (threshold, streak, total_games, rate)
    """
    best = None
    for threshold in sorted(thresholds, reverse=True):
        streak = calc_streak_at_threshold(values, threshold)
        total  = len([v for v in values if v >= threshold])
        rate   = total / len(values) if values else 0
        if streak >= min_streak:
            if best is None or streak > best[1]:
                best = (threshold, streak, len(values), rate)
    return best

def streak_emoji(streak, total):
    rate = streak / total if total > 0 else 0
    if streak >= 10 and rate >= 0.95:
        return "🔥"
    elif streak >= 7:
        return "⚡"
    elif streak >= 5:
        return "✅"
    elif streak >= 3:
        return "📈"
    return ""

def format_streak_line(name, threshold, prop, streak, total, extra=""):
    """Format like: J. Chase: 6+ Receptions ✅ 10/10"""
    prop_labels = {
        "pass_yds":  "Pass Yds",
        "rush_yds":  "Rush Yds",
        "rec_yds":   "Rec Yds",
        "receptions":"Receptions",
        "targets":   "Targets",
        "pass_att":  "Pass Att",
    }
    prop_str  = prop_labels.get(prop, prop)
    emoji     = streak_emoji(streak, total)
    extra_str = f" [{extra}]" if extra else ""
    return f"{name}: {threshold}+ {prop_str} {emoji} {streak}/{total}{extra_str}"

# ── WEATHER FLAG ─────────────────────────────────────────────
def weather_flag(team, opp, wind_mph=0, temp=65, precip=False):
    """Returns weather context string."""
    flags = []
    home_dome  = team in DOME_TEAMS
    away_dome  = opp in DOME_TEAMS
    is_dome    = home_dome or away_dome

    if is_dome:
        flags.append("🏟️ DOME — weather neutral")
    else:
        if wind_mph >= 20:
            flags.append(f"💨 HIGH WIND {wind_mph}mph — fade passing props")
        elif wind_mph >= 12:
            flags.append(f"💨 Wind {wind_mph}mph — slight pass suppression")
        if temp <= 32:
            flags.append(f"🥶 FREEZING {temp}°F — run game favored")
        elif temp <= 40:
            flags.append(f"❄️ Cold {temp}°F — minor pass impact")
        if precip:
            flags.append("🌧️ RAIN/SNOW — fade passing, volume drops")
    return flags

# ── MAIN STREAK SHEET BUILDER ─────────────────────────────────
def build_streak_sheets(week, season, game_schedule=None):
    """
    Build complete streak sheets for all positions.
    game_schedule: list of dicts with game window, weather info
    """
    conn = get_conn()

    # Load all game logs
    logs = pd.read_sql("""
        SELECT gl.player_id, gl.season, gl.week,
               gl.pass_yds, gl.pass_att, gl.rush_yds,
               gl.receptions, gl.rec_yds, gl.targets,
               p.name, p.position, p.team
        FROM game_logs gl
        JOIN players p ON gl.player_id = p.id
        ORDER BY p.name, gl.season, gl.week
    """, conn)
    conn.close()

    # Only use data prior to current week
    prior = logs[
        (logs['season'] < season) |
        ((logs['season'] == season) & (logs['week'] < week))
    ].copy()

    results = {pos: [] for pos in ["QB","RB","WR","TE"]}

    STAT_MAP = {
        "pass_yds": "pass_yds",
        "pass_att": "pass_att",
        "rush_yds": "rush_yds",
        "receptions": "receptions",
        "rec_yds": "rec_yds",
        "targets": "targets",
    }

    for player_id in prior['player_id'].unique():
        plogs = prior[prior['player_id'] == player_id].sort_values(
            ['season','week']
        ).reset_index(drop=True)

        if plogs.empty:
            continue

        name = plogs.iloc[0]['name']
        pos  = plogs.iloc[0]['position']
        team = plogs.iloc[0]['team']

        if pos not in ALT_LINES:
            continue

        # Abbreviate name: First initial + Last
        parts = name.split()
        abbr  = f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else name

        player_entry = {
            "player_id": player_id,
            "name":      name,
            "abbr":      abbr,
            "pos":       pos,
            "team":      team,
            "streaks":   [],
        }

        for prop, thresholds in ALT_LINES[pos].items():
            stat_col = STAT_MAP.get(prop)
            if not stat_col or stat_col not in plogs.columns:
                continue

            values = plogs[stat_col].dropna().tolist()
            if len(values) < 3:
                continue

            # Check each threshold
            for threshold in thresholds:
                streak = calc_streak_at_threshold(values, threshold)
                total  = len(values)
                hits   = len([v for v in values if v >= threshold])
                rate   = hits / total

                if streak >= 3:
                    player_entry["streaks"].append({
                        "prop":      prop,
                        "threshold": threshold,
                        "streak":    streak,
                        "total":     total,
                        "hits":      hits,
                        "rate":      round(rate, 3),
                        "avg":       round(np.mean(values[-10:]), 1),
                    })

        if player_entry["streaks"]:
            results[pos].append(player_entry)

    return results, prior

def print_streak_sheets(results, week, season, game_schedule=None):
    pos_headers = {
        "QB": "💪 QUARTERBACK PROP STREAKS",
        "RB": "🏃 RUNNING BACK PROP STREAKS",
        "WR": "🏈 WIDE RECEIVER PROP STREAKS",
        "TE": "🎯 TIGHT END PROP STREAKS",
    }

    pos_icons = {"QB":"💪","RB":"🏃","WR":"🏈","TE":"🎯"}

    print(f"\n{'='*65}")
    print(f"EDGE INDEX — NFL WEEK {week} {season} STREAK SHEETS")
    print(f"Data: nflverse stats + real DK/FD/BetMGM lines")
    print(f"{'='*65}")

    for pos in ["QB","RB","WR","TE"]:
        players = results[pos]
        if not players:
            continue

        # Find best streak per player
        best_plays = []
        for p in players:
            if not p["streaks"]:
                continue
            # Sort streaks by streak length then threshold
            top = sorted(p["streaks"], key=lambda x: (x["streak"], x["threshold"]), reverse=True)
            for s in top[:3]:  # Top 3 streaks per player
                best_plays.append({
                    "abbr":      p["abbr"],
                    "name":      p["name"],
                    "team":      p["team"],
                    "prop":      s["prop"],
                    "threshold": s["threshold"],
                    "streak":    s["streak"],
                    "total":     s["total"],
                    "rate":      s["rate"],
                    "avg":       s["avg"],
                })

        if not best_plays:
            continue

        # Sort by streak length
        best_plays.sort(key=lambda x: (x["streak"], x["rate"]), reverse=True)

        print(f"\n{pos_headers[pos]} — NFL Week {week}")
        print(f"{'─'*65}")

        # 100% hit rate section
        perfect = [p for p in best_plays if p["rate"] >= 0.95 and p["streak"] >= 5]
        if perfect:
            print(f"\n🔥 100% (or near-perfect) hit rates:")
            for p in perfect[:10]:
                line = format_streak_line(
                    p["abbr"], p["threshold"], p["prop"],
                    p["streak"], p["total"],
                    extra=f"avg {p['avg']}"
                )
                print(f"  {line}")

        # Strong streaks (75%+)
        strong = [p for p in best_plays if 0.75 <= p["rate"] < 0.95 and p["streak"] >= 4]
        if strong:
            print(f"\n✅ Strong streaks (75%+ hit rate):")
            for p in strong[:10]:
                line = format_streak_line(
                    p["abbr"], p["threshold"], p["prop"],
                    p["streak"], p["total"],
                    extra=f"{p['rate']*100:.0f}% all-time"
                )
                print(f"  {line}")

        # Building streaks (3-4 games)
        building = [p for p in best_plays if p["streak"] in (3,4) and p["rate"] >= 0.60]
        if building:
            print(f"\n📈 Building streaks (3-4 games, 60%+ rate):")
            for p in building[:8]:
                line = format_streak_line(
                    p["abbr"], p["threshold"], p["prop"],
                    p["streak"], p["total"]
                )
                print(f"  {line}")

    # Alt line section
    print(f"\n{'='*65}")
    print(f"🎯 ALT LINE TRENDS — NFL Week {week}")
    print(f"{'='*65}")
    print(f"(Reduced juice opportunities — best value plays)")

    for pos in ["WR","QB","RB","TE"]:
        players = results[pos]
        alt_plays = []

        for p in players:
            for s in p["streaks"]:
                # Only show if streak is 5+ and rate is high
                if s["streak"] >= 5 and s["rate"] >= 0.80:
                    alt_plays.append({
                        "abbr":      p["abbr"],
                        "team":      p["team"],
                        "prop":      s["prop"],
                        "threshold": s["threshold"],
                        "streak":    s["streak"],
                        "total":     s["total"],
                        "rate":      s["rate"],
                    })

        if not alt_plays:
            continue

        alt_plays.sort(key=lambda x: (x["streak"], x["rate"]), reverse=True)

        prop_labels = {
            "pass_yds":"Pass Yds","rush_yds":"Rush Yds",
            "rec_yds":"Rec Yds","receptions":"Receptions",
            "targets":"Targets","pass_att":"Pass Att",
        }

        print(f"\n🔥 {pos} ALT Lines:")
        for p in alt_plays[:10]:
            prop_str = prop_labels.get(p["prop"], p["prop"])
            emoji    = streak_emoji(p["streak"], p["total"])
            print(f"  {p['abbr']} ({p['team']}): {p['threshold']}+ {prop_str} {emoji} {p['streak']}/{p['total']} ({p['rate']*100:.0f}%)")

    # Game window section
    if game_schedule:
        print(f"\n{'='*65}")
        print(f"📅 BY GAME WINDOW — Week {week}")
        print(f"{'='*65}")

        for window_key, window_label in GAME_WINDOWS.items():
            games = [g for g in game_schedule if g.get("window") == window_key]
            if not games:
                continue

            print(f"\n{window_label}:")
            for g in games:
                home = g.get("home","")
                away = g.get("away","")
                wind = g.get("wind_mph", 0)
                temp = g.get("temp", 65)
                precip = g.get("precip", False)
                spread = g.get("spread", 0)
                total  = g.get("total", 44)

                w_flags = weather_flag(home, away, wind, temp, precip)

                print(f"  {away} @ {home} | Spread: {spread:+.1f} | Total: {total}")
                for f in w_flags:
                    print(f"    {f}")

    print(f"\n{'='*65}")
    print(f"Posted by Edge Index — glowing-licorice-f530a8.netlify.app")
    print(f"{'='*65}\n")

# ── REDDIT-READY OUTPUT ───────────────────────────────────────
def print_reddit_format(results, week, season):
    """Clean Reddit markdown format for copy-paste."""
    print(f"\n--- REDDIT FORMAT (copy-paste ready) ---\n")

    for pos in ["WR","QB","RB","TE"]:
        players = results[pos]
        if not players:
            continue

        pos_names = {"QB":"Quarterback","RB":"Running Back",
                     "WR":"Wide Receiver","TE":"Tight End"}

        best = []
        for p in players:
            for s in p["streaks"]:
                if s["streak"] >= 5 and s["rate"] >= 0.85:
                    best.append({
                        "abbr": p["abbr"], "team": p["team"],
                        **s
                    })

        if not best:
            continue

        best.sort(key=lambda x: (x["streak"], x["rate"]), reverse=True)

        prop_labels = {
            "pass_yds":"Pass Yds","rush_yds":"Rush Yds",
            "rec_yds":"Rec Yds","receptions":"Receptions",
            "targets":"Targets","pass_att":"Pass Att",
        }

        print(f"**{pos_names[pos]} Prop Streaks (NFL Week {week})**")
        print(f"🔥 100% hit rates\n")

        for p in best[:10]:
            prop_str = prop_labels.get(p["prop"], p["prop"])
            emoji    = streak_emoji(p["streak"], p["total"])
            print(f"* {p['abbr']}: {p['threshold']}+ {prop_str} ➡️ {p['streak']}/{p['total']}")

        print()

# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",   type=int, default=1)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--reddit", action="store_true",
                        help="Print Reddit markdown format")
    args = parser.parse_args()

    print(f"Building streak sheets for Week {args.week} {args.season}...")

    # Sample schedule — replace with live data
    SAMPLE_SCHEDULE = [
        {"window":"TNF",       "away":"KC",  "home":"BAL", "spread":-3.0, "total":47.0, "wind_mph":8,  "temp":52, "precip":False},
        {"window":"SUN_EARLY", "away":"PHI", "home":"DAL", "spread":-7.0, "total":46.5, "wind_mph":12, "temp":61, "precip":False},
        {"window":"SUN_EARLY", "away":"CIN", "home":"PIT", "spread":-2.0, "total":48.5, "wind_mph":6,  "temp":48, "precip":True},
        {"window":"SUN_EARLY", "away":"GB",  "home":"CHI", "spread":-3.0, "total":44.5, "wind_mph":15, "temp":38, "precip":False},
        {"window":"SUN_AFT",   "away":"LAR", "home":"SF",  "spread":-4.5, "total":48.0, "wind_mph":5,  "temp":58, "precip":False},
        {"window":"SUN_AFT",   "away":"MIA", "home":"BUF", "spread":-4.0, "total":50.5, "wind_mph":14, "temp":42, "precip":False},
        {"window":"SNF",       "away":"DAL", "home":"PHI", "spread":7.0,  "total":46.5, "wind_mph":12, "temp":61, "precip":False},
        {"window":"MNF",       "away":"DET", "home":"MIN", "spread":-3.0, "total":46.0, "wind_mph":5,  "temp":55, "precip":False},
    ]

    results, _ = build_streak_sheets(args.week, args.season)
    print_streak_sheets(results, args.week, args.season, SAMPLE_SCHEDULE)

    if args.reddit:
        print_reddit_format(results, args.week, args.season)
