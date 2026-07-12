"""
Edge Index — Master Weekly Pipeline
Runs every Thursday before games start.

Steps:
  1. Pull current week games + lines from The Odds API
  2. Pull player game logs from DB (prior seasons + current)
  3. Calculate context signals (rest, travel, weather, matchup)
  4. Generate streak sheets (Reddit format)
  5. Generate line analysis (newsletter format)
  6. Generate play recommendations + parlays
  7. Output all three to files + console

Usage:
  python weekly_pipeline.py --week 1 --season 2026
  python weekly_pipeline.py --week 1 --season 2026 --dry-run
"""
import sys, os, sqlite3, json, argparse, requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_setup import get_conn

# ── CONFIG ────────────────────────────────────────────────────
ODDS_API_KEY  = os.environ.get("ODDS_API_KEY", "")
ODDS_BASE     = "https://api.the-odds-api.com/v4"
SPORT         = "americanfootball_nfl"
BOOKS         = ["draftkings", "fanduel", "betmgm"]

PROP_MARKETS  = [
    "player_pass_yds", "player_pass_attempts",
    "player_rush_yds", "player_receptions",
    "player_reception_yds",
]
ALT_MARKETS   = [
    "player_reception_yds_alternate", "player_receptions_alternate",
    "player_rush_yds_alternate", "player_pass_yds_alternate",
]

# Map API prop names → our DB names
PROP_MAP = {
    "player_pass_yds":                 "pass_yds",
    "player_pass_attempts":            "pass_att",
    "player_rush_yds":                 "rush_yds",
    "player_receptions":               "receptions",
    "player_reception_yds":            "rec_yds",
    "player_reception_yds_alternate":  "rec_yds",
    "player_receptions_alternate":     "receptions",
    "player_rush_yds_alternate":       "rush_yds",
    "player_pass_yds_alternate":       "pass_yds",
}

# ── DOME / INDOOR STADIUMS ────────────────────────────────────
DOME_TEAMS = {
    "ATL","NO","LAR","LV","MIN","DET","IND","HOU",
    "DAL","ARI","BUF","KC",  # Arrowhead has partial cover
}

# ── TIMEZONE / TRAVEL PENALTIES ───────────────────────────────
TEAM_TIMEZONE = {
    "NE":"ET","NYG":"ET","NYJ":"ET","PHI":"ET","PIT":"ET",
    "BAL":"ET","WAS":"ET","MIA":"ET","BUF":"ET","CLE":"ET",
    "CIN":"ET","TB":"ET","CAR":"ET","ATL":"ET","NO":"ET",
    "MIN":"CT","GB":"CT","CHI":"CT","DET":"CT","KC":"CT",
    "HOU":"CT","TEN":"CT","IND":"CT","JAC":"ET",
    "DAL":"CT","SF":"PT","LAR":"PT","LAC":"PT","LV":"PT",
    "SEA":"PT","ARI":"PT","DEN":"MT",
}

def travel_penalty(away_team, home_team, game_window):
    """
    Estimate fatigue/travel penalty for away team.
    Returns adjustment factor (-0.10 to 0.0)
    """
    away_tz = TEAM_TIMEZONE.get(away_team, "CT")
    home_tz = TEAM_TIMEZONE.get(home_team, "CT")

    tz_diff = {"ET":0, "CT":1, "MT":2, "PT":3}
    diff = abs(tz_diff.get(away_tz,0) - tz_diff.get(home_tz,0))

    penalty = 0.0
    notes   = []

    # East coast team traveling west for early game
    if away_tz == "ET" and home_tz == "PT" and game_window in ("SUN_EARLY","SUN_AFT"):
        penalty -= 0.06
        notes.append(f"EC team to West Coast ({away_team} ET → {home_team} PT) — body clock disadvantage")

    # 3-hour time zone shift any direction
    if diff >= 3:
        penalty -= 0.05
        notes.append(f"3-hour time zone shift — travel fatigue factor")
    elif diff == 2:
        penalty -= 0.02
        notes.append(f"2-hour time zone shift — minor travel factor")

    # Short week (TNF after Sunday game)
    if game_window == "TNF":
        penalty -= 0.04
        notes.append("Short week (TNF) — less prep time, fatigue risk")

    # MNF to TNF (5 days rest only)
    if game_window == "MNF":
        notes.append("MNF — 10+ days of rest advantage if off bye")

    return round(penalty, 3), notes

def rest_advantage(team_days_rest, opp_days_rest):
    """
    Teams with more rest have a measurable edge.
    Returns boost for the team with more rest.
    """
    diff = team_days_rest - opp_days_rest
    if diff >= 7:   # Bye week vs normal week
        return 0.06, [f"Bye week advantage (+{diff} days rest vs opponent)"]
    elif diff >= 4:
        return 0.03, [f"Rest advantage (+{diff} days)"]
    elif diff <= -7:
        return -0.06, [f"Opponent off bye — significant rest disadvantage"]
    elif diff <= -4:
        return -0.03, [f"Rest disadvantage ({diff} days vs opponent)"]
    return 0.0, []

# ── MOVING AVERAGE LINE TRACKER ───────────────────────────────
def calc_moving_line(player_name, prop, anchors, prior_values, posted_line):
    """
    Instead of fixed historical avg, use weighted moving average
    that accounts for recent performance AND typical book adjustments.
    
    Books set lines using:
      - Rolling 4-6 week weighted avg (most recent weeks weighted higher)
      - Matchup adjustment (up to ±15%)
      - Public betting % adjustment (sharp money moves line)
      - Injury/status adjustment
    
    We model the book's expected line then find where we differ.
    """
    if len(prior_values) < 3:
        return None

    # Weighted moving average — recent games weighted higher
    n = len(prior_values)
    weights = np.array([1.5**i for i in range(n)])
    weights = weights / weights.sum()
    wma = np.average(prior_values, weights=weights)

    # Simple moving averages
    sma_4  = np.mean(prior_values[-4:])  if n >= 4  else np.mean(prior_values)
    sma_8  = np.mean(prior_values[-8:])  if n >= 8  else np.mean(prior_values)
    sma_16 = np.mean(prior_values[-16:]) if n >= 16 else np.mean(prior_values)

    # Standard deviation (volatility)
    std    = np.std(prior_values[-10:]) if n >= 4 else np.std(prior_values)
    cv     = std / max(sma_8, 1)  # Coefficient of variation

    # Expected book line = weighted blend
    expected_line = sma_4 * 0.40 + sma_8 * 0.35 + sma_16 * 0.25

    # Book discount: books typically set line ~5-8% below true avg
    # to account for variance/vig
    book_discount = 0.92
    modeled_line  = expected_line * book_discount

    # Line gap vs what we'd expect
    line_vs_expected = posted_line - modeled_line
    line_vs_wma      = wma - posted_line

    return {
        "wma":             round(wma, 1),
        "sma_4":           round(sma_4, 1),
        "sma_8":           round(sma_8, 1),
        "sma_16":          round(sma_16, 1),
        "std":             round(std, 1),
        "cv":              round(cv, 3),
        "expected_line":   round(expected_line, 1),
        "modeled_line":    round(modeled_line, 1),
        "line_vs_expected":round(line_vs_expected, 1),
        "line_vs_wma":     round(line_vs_wma, 1),
        "is_high":         line_vs_expected > std * 0.5,
        "is_low":          line_vs_expected < -std * 0.5,
    }

# ── CONTEXT ENGINE ────────────────────────────────────────────
def build_context(player, pos, team, opp,
                  prop, posted_line, prior_values,
                  spread=0, total=44,
                  wind=0, temp=65, precip=False,
                  game_window="SUN_EARLY",
                  team_rest=7, opp_rest=7,
                  injury_flag=False,
                  opp_rush_dvoa=0, opp_pass_dvoa=0,
                  opp_slot_coverage_rate=0.0,
                  zone_pct=0.50, blitz_pct=0.25,
                  anchors=None):
    """
    Full context model — combines all known factors.
    Returns a comprehensive play analysis dict.
    """
    if len(prior_values) < 3:
        return None

    # ── MOVING AVERAGE ─────────────────────────────────────────
    ma = calc_moving_line(player, prop, anchors, prior_values, posted_line)
    if not ma:
        return None

    # ── STREAK & HIT RATES ─────────────────────────────────────
    streak = 0
    for v in reversed(prior_values):
        if v >= posted_line:
            streak += 1
        else:
            break

    l6  = sum(1 for v in prior_values[-6:]  if v >= posted_line) / min(6,  len(prior_values))
    l10 = sum(1 for v in prior_values[-10:] if v >= posted_line) / min(10, len(prior_values))

    # ── BASE PROBABILITY ───────────────────────────────────────
    # Start from L6/L10 weighted hit rate
    base_prob = l6 * 0.55 + l10 * 0.25

    # ── STREAK SIGNAL ──────────────────────────────────────────
    if streak >= 10: streak_adj = +0.12
    elif streak >= 6: streak_adj = +0.07
    elif streak >= 3: streak_adj = +0.02
    elif streak == 0: streak_adj = -0.05
    else:             streak_adj = 0.0

    # ── LINE EDGE SIGNAL ───────────────────────────────────────
    # How far is posted line from our modeled line?
    sigma_gap = ma["line_vs_wma"] / max(ma["std"], 1)
    if sigma_gap > 1.5:   line_adj = +0.10
    elif sigma_gap > 0.75: line_adj = +0.06
    elif sigma_gap > 0.25: line_adj = +0.03
    elif sigma_gap < -1.5: line_adj = -0.10
    elif sigma_gap < -0.75:line_adj = -0.06
    elif sigma_gap < -0.25:line_adj = -0.03
    else:                  line_adj = 0.0

    # ── GAME SCRIPT SIGNAL ─────────────────────────────────────
    gs_adj  = 0.0
    gs_notes = []
    is_fav  = spread < -3
    is_dog  = spread > 3

    if pos == "RB" and prop == "rush_yds":
        if spread < -10: gs_adj += 0.07; gs_notes.append(f"Big favorite ({spread:+}) → heavy run game late")
        if spread > 7:   gs_adj -= 0.07; gs_notes.append(f"Big dog ({spread:+}) → trailing = abandon run")
        if total <= 40:  gs_adj += 0.04; gs_notes.append("Low total → defensive game, grind-it-out run offense")
        if total >= 50:  gs_adj -= 0.03; gs_notes.append("High total → pass-heavy pace reduces run share")

    elif pos in ("WR","TE") and prop in ("rec_yds","receptions"):
        if is_dog:       gs_adj += 0.07; gs_notes.append(f"Dog ({spread:+}) → trailing = pass heavy")
        if total >= 48:  gs_adj += 0.05; gs_notes.append(f"High total ({total}) → shootout pace boosts targets")
        if spread < -10: gs_adj -= 0.05; gs_notes.append(f"Big fav ({spread:+}) → game managed, reduced targets")
        if total <= 40:  gs_adj -= 0.04; gs_notes.append("Low total → suppressed passing environment")

    elif pos == "QB" and prop == "pass_yds":
        if is_dog:       gs_adj += 0.08; gs_notes.append(f"Dog ({spread:+}) → trailing QB volume elevated")
        if total >= 48:  gs_adj += 0.06; gs_notes.append(f"Shootout total ({total}) → pass volume premium")
        if spread < -10: gs_adj -= 0.07; gs_notes.append(f"Big fav ({spread:+}) → game management reduces attempts")

    elif pos == "QB" and prop == "rush_yds":
        # Mobile QBs (Lamar, Hurts, Allen) – check position
        gs_adj += 0.02  # slight bonus — mobile QBs scheme in rush regardless

    # ── MATCHUP SIGNALS ────────────────────────────────────────
    mu_adj   = 0.0
    mu_notes = []

    # Defensive DVOA (negative = better defense)
    if pos in ("WR","TE") and prop in ("rec_yds","receptions"):
        if opp_pass_dvoa < -10:
            mu_adj -= 0.06
            mu_notes.append(f"{opp} strong pass D (DVOA {opp_pass_dvoa:+.0f}%) — tough matchup")
        elif opp_pass_dvoa > 10:
            mu_adj += 0.06
            mu_notes.append(f"{opp} weak pass D (DVOA {opp_pass_dvoa:+.0f}%) — favorable matchup")

    elif pos == "RB" and prop == "rush_yds":
        if opp_rush_dvoa < -10:
            mu_adj -= 0.06
            mu_notes.append(f"{opp} strong run D (DVOA {opp_rush_dvoa:+.0f}%) — tough matchup")
        elif opp_rush_dvoa > 10:
            mu_adj += 0.06
            mu_notes.append(f"{opp} weak run D (DVOA {opp_rush_dvoa:+.0f}%) — favorable matchup")

    # Zone vs man for slot WRs/TEs
    if pos in ("WR","TE") and prop in ("rec_yds","receptions"):
        if zone_pct >= 0.60:
            mu_adj += 0.05
            mu_notes.append(f"{opp} zone-heavy ({zone_pct*100:.0f}%) — slot WRs/TEs thrive vs zone")
        elif zone_pct <= 0.35:
            mu_adj -= 0.03
            mu_notes.append(f"{opp} man-heavy ({(1-zone_pct)*100:.0f}% man) — tighter coverage expected")

        if blitz_pct >= 0.35:
            mu_adj += 0.04
            mu_notes.append(f"{opp} blitz-heavy ({blitz_pct*100:.0f}%) — quick routes, volume increases")

    # ── WEATHER SIGNAL ─────────────────────────────────────────
    wx_adj   = 0.0
    wx_notes = []
    is_dome  = team in DOME_TEAMS or opp in DOME_TEAMS

    if not is_dome:
        if wind >= 20:
            if prop in ("pass_yds","rec_yds","receptions"):
                wx_adj -= 0.10
                wx_notes.append(f"HIGH WIND {wind}mph — significant pass suppression")
            elif prop == "rush_yds":
                wx_adj += 0.05
                wx_notes.append(f"Wind {wind}mph → run game shift")
        elif wind >= 12:
            if prop in ("pass_yds","rec_yds","receptions"):
                wx_adj -= 0.04
                wx_notes.append(f"Wind {wind}mph — moderate pass suppression")

        if temp <= 28:
            if prop in ("pass_yds","rec_yds","receptions"):
                wx_adj -= 0.06
                wx_notes.append(f"FREEZING {temp}°F — cold weather significantly suppresses passing")
            elif prop == "rush_yds":
                wx_adj += 0.04
                wx_notes.append(f"Cold {temp}°F — ground game favored")
        elif temp <= 40:
            if prop in ("pass_yds","rec_yds","receptions"):
                wx_adj -= 0.03
                wx_notes.append(f"Cold {temp}°F — mild passing suppression")

        if precip:
            if prop in ("pass_yds","rec_yds","receptions"):
                wx_adj -= 0.06
                wx_notes.append("Rain/snow — wet ball reduces passing volume and accuracy")
            elif prop == "rush_yds":
                wx_adj += 0.03
                wx_notes.append("Wet conditions → run game favored")

        if is_dome:
            wx_notes.append("🏟️ Dome — weather neutral, no adjustments")
    else:
        wx_notes.append("🏟️ Indoor — weather neutral")

    # ── REST / TRAVEL ──────────────────────────────────────────
    rest_adj, rest_notes = rest_advantage(team_rest, opp_rest)
    travel_adj, travel_notes = travel_penalty(team, opp, game_window)

    # Short week penalty (TNF) — apply to both offensive production
    if game_window == "TNF":
        rest_adj -= 0.03
        rest_notes.append("TNF short week — offensive rhythm disrupted")

    # ── INJURY SIGNAL ─────────────────────────────────────────
    inj_adj = -0.08 if injury_flag else 0.0
    if injury_flag:
        mu_notes.append("⚠️ Injury/status flag — monitor practice report")

    # ── FINAL PROBABILITY ──────────────────────────────────────
    total_adj = (streak_adj + line_adj + gs_adj +
                 mu_adj + wx_adj + rest_adj + travel_adj + inj_adj)

    model_prob = min(0.96, max(0.20, base_prob + total_adj))

    # ── TIER ───────────────────────────────────────────────────
    if model_prob >= 0.82 and streak >= 5 and l6 >= 0.75:
        tier = "AUTO"
    elif model_prob >= 0.67 and l6 >= 0.60:
        tier = "T1"
    elif model_prob >= 0.58 and l6 >= 0.55:
        tier = "T2"
    else:
        tier = "SKIP"

    # ── ALT LINES ──────────────────────────────────────────────
    alt_lines = []
    if anchors and player in anchors:
        prop_data = anchors[player]["props"].get(prop, {})
        posted_unique = prop_data.get("posted_unique", [])
        # Show alt lines that are achievable (below main line)
        alt_lines = sorted([l for l in posted_unique
                           if 0.6 * posted_line <= l < posted_line])

    return {
        "player":       player,
        "pos":          pos,
        "team":         team,
        "opp":          opp,
        "prop":         prop,
        "posted_line":  posted_line,
        "tier":         tier,
        "model_prob":   round(model_prob, 3),
        "streak":       streak,
        "l6":           round(l6, 3),
        "l10":          round(l10, 3),

        # Moving average signals
        "wma":          ma["wma"],
        "sma_4":        ma["sma_4"],
        "sma_8":        ma["sma_8"],
        "line_vs_wma":  ma["line_vs_wma"],
        "sigma_gap":    round(sigma_gap, 2),

        # Context
        "game_window":  game_window,
        "spread":       spread,
        "total":        total,
        "is_dome":      is_dome,
        "wind":         wind,
        "temp":         temp,
        "precip":       precip,

        # Adjustments breakdown
        "adj_streak":   round(streak_adj, 3),
        "adj_line":     round(line_adj, 3),
        "adj_gs":       round(gs_adj, 3),
        "adj_matchup":  round(mu_adj, 3),
        "adj_weather":  round(wx_adj, 3),
        "adj_rest":     round(rest_adj, 3),
        "adj_travel":   round(travel_adj, 3),
        "total_adj":    round(total_adj, 3),

        # Notes
        "gs_notes":     gs_notes,
        "mu_notes":     mu_notes,
        "wx_notes":     wx_notes,
        "rest_notes":   rest_notes + travel_notes,

        # Alt lines
        "alt_lines":    alt_lines,
    }

# ── LIVE ODDS PULLER ─────────────────────────────────────────
def pull_live_lines(week, season, dry_run=False):
    """
    Pull current week prop lines from The Odds API.
    Returns dict: {player_name: {prop: {line, odds, book}}}
    """
    if dry_run or not ODDS_API_KEY:
        print("  [DRY RUN] Skipping live odds pull — using DB lines")
        return {}

    try:
        # Get this week's games
        resp = requests.get(
            f"{ODDS_BASE}/sports/{SPORT}/events",
            params={"apiKey": ODDS_API_KEY, "dateFormat": "iso"},
            timeout=10
        )
        if resp.status_code != 200:
            print(f"  Odds API error: {resp.status_code}")
            return {}

        events = resp.json()
        print(f"  Found {len(events)} upcoming games")

        lines = {}
        for event in events[:16]:  # Cap at 16 games per week
            game_id   = event["id"]
            home_team = event.get("home_team","")
            away_team = event.get("away_team","")

            for market in PROP_MARKETS + ALT_MARKETS:
                try:
                    odds_resp = requests.get(
                        f"{ODDS_BASE}/sports/{SPORT}/events/{game_id}/odds",
                        params={
                            "apiKey":  ODDS_API_KEY,
                            "regions": "us",
                            "markets": market,
                            "bookmakers": ",".join(BOOKS),
                            "oddsFormat": "american",
                        },
                        timeout=10
                    )
                    if odds_resp.status_code != 200:
                        continue

                    data = odds_resp.json()
                    prop_key = PROP_MAP.get(market, market)

                    for book in data.get("bookmakers", []):
                        for mkt in book.get("markets", []):
                            for outcome in mkt.get("outcomes", []):
                                if outcome.get("name") == "Over":
                                    pname = outcome.get("description","")
                                    line  = outcome.get("point", 0)
                                    price = outcome.get("price", -110)

                                    if pname not in lines:
                                        lines[pname] = {}
                                    if prop_key not in lines[pname]:
                                        lines[pname][prop_key] = []

                                    lines[pname][prop_key].append({
                                        "line":  line,
                                        "odds":  price,
                                        "book":  book["key"],
                                        "home":  home_team,
                                        "away":  away_team,
                                    })
                except Exception as e:
                    continue

        print(f"  Pulled lines for {len(lines)} players")
        return lines

    except Exception as e:
        print(f"  Error pulling live odds: {e}")
        return {}

# ── DB GAME LOG PULLER ────────────────────────────────────────
def pull_player_logs(season, week):
    """
    Pull all player game logs from DB prior to this week.
    Returns dict: {player_name: {prop: [values]}}
    """
    conn = get_conn()

    logs = pd.read_sql(f"""
        SELECT p.name, p.position, p.team,
               gl.season, gl.week,
               gl.pass_yds, gl.pass_att, gl.rush_yds,
               gl.receptions, gl.rec_yds, gl.targets
        FROM game_logs gl
        JOIN players p ON gl.player_id = p.id
        WHERE (gl.season < {season})
           OR (gl.season = {season} AND gl.week < {week})
        ORDER BY p.name, gl.season, gl.week
    """, conn)
    conn.close()

    STAT_COLS = {
        "pass_yds": "pass_yds", "pass_att": "pass_att",
        "rush_yds": "rush_yds", "receptions": "receptions",
        "rec_yds": "rec_yds", "targets": "targets",
    }

    player_data = {}
    for name, grp in logs.groupby("name"):
        grp = grp.sort_values(["season","week"])
        pos  = grp.iloc[-1]["position"]
        team = grp.iloc[-1]["team"]

        player_data[name] = {"pos": pos, "team": team, "props": {}}
        for prop, col in STAT_COLS.items():
            if col in grp.columns:
                vals = grp[col].dropna().tolist()
                if vals:
                    player_data[name]["props"][prop] = vals

    return player_data

# ── BEST LINE SELECTOR ────────────────────────────────────────
def best_line(lines_list):
    """Pick the best (lowest) line with best odds from multiple books."""
    if not lines_list:
        return None, None, None

    # Sort by line ascending (lower line = easier OVER)
    sorted_lines = sorted(lines_list, key=lambda x: (x["line"], x["odds"]))
    best = sorted_lines[0]

    # Check if multiple books agree on the line
    main_line = best["line"]
    agreeing  = [l for l in lines_list if l["line"] == main_line]
    consensus = len(agreeing) >= 2

    return best["line"], best["odds"], consensus

# ── PRINT REPORT ──────────────────────────────────────────────
def print_report(plays, week, season):
    PROP_LABELS = {
        "rec_yds":"Rec Yds","receptions":"Receptions",
        "rush_yds":"Rush Yds","pass_yds":"Pass Yds",
        "pass_att":"Pass Att","targets":"Targets",
    }

    print(f"\n{'='*68}")
    print(f"EDGE INDEX — WEEK {week} {season} FULL PLAYBOOK")
    print(f"{'='*68}")

    for tier, label in [
        ("AUTO", "⚡ AUTO-PLAY — Highest Confidence"),
        ("T1",   "★  TIER 1 — Strong Edge"),
        ("T2",   "◆  TIER 2 — Moderate Edge"),
    ]:
        tier_plays = sorted(
            [p for p in plays if p["tier"] == tier],
            key=lambda x: x["model_prob"], reverse=True
        )
        if not tier_plays:
            continue

        print(f"\n{label}")
        print(f"{'─'*68}")

        for p in tier_plays:
            prop_l = PROP_LABELS.get(p["prop"], p["prop"])
            dome   = "🏟️" if p["is_dome"] else ""
            print(f"\n  {p['player']} ({p['pos']}, {p['team']}) vs {p['opp']} {dome}")
            print(f"  {prop_l.upper()} OVER {p['posted_line']}  |  Model: {p['model_prob']*100:.0f}%")
            print(f"  WMA: {p['wma']}  SMA4: {p['sma_4']}  Gap vs line: {p['line_vs_wma']:+.1f} ({p['sigma_gap']:+.1f}σ)")
            print(f"  Streak: {p['streak']}g  L6: {p['l6']*100:.0f}%  Spread: {p['spread']:+.1f}  Total: {p['total']}")

            # Show adjustment breakdown
            adjs = []
            if p["adj_streak"] != 0: adjs.append(f"streak{p['adj_streak']:+.0%}")
            if p["adj_line"]   != 0: adjs.append(f"line{p['adj_line']:+.0%}")
            if p["adj_gs"]     != 0: adjs.append(f"script{p['adj_gs']:+.0%}")
            if p["adj_matchup"]!= 0: adjs.append(f"matchup{p['adj_matchup']:+.0%}")
            if p["adj_weather"]!= 0: adjs.append(f"weather{p['adj_weather']:+.0%}")
            if p["adj_rest"]   != 0: adjs.append(f"rest{p['adj_rest']:+.0%}")
            if p["adj_travel"] != 0: adjs.append(f"travel{p['adj_travel']:+.0%}")
            if adjs:
                print(f"  Adjustments: {' | '.join(adjs)}")

            all_notes = p["gs_notes"] + p["mu_notes"] + p["wx_notes"] + p["rest_notes"]
            for note in all_notes[:3]:
                print(f"    → {note}")

            if p["alt_lines"]:
                print(f"  Alt lines (reduced juice): {p['alt_lines']}")

    # Quick ref table
    print(f"\n{'='*68}")
    print(f"QUICK REFERENCE")
    print(f"{'='*68}")
    print(f"{'Player':<22} {'Prop':<12} {'Line':>6} {'WMA':>6} {'Gap':>6} {'L6':>5} {'Str':>4} {'Adj':>6}  Tier")
    print(f"{'─'*68}")
    for p in sorted(plays, key=lambda x: x["model_prob"], reverse=True):
        if p["tier"] == "SKIP":
            continue
        prop_l = PROP_LABELS.get(p["prop"],"")[:11]
        tier_icon = {"AUTO":"⚡","T1":"★","T2":"◆"}.get(p["tier"],"")
        print(f"  {p['player'][:20]:<20} {prop_l:<12} "
              f"{p['posted_line']:>6.1f} {p['wma']:>6.1f} "
              f"{p['line_vs_wma']:>+6.1f} {p['l6']*100:>4.0f}% "
              f"{p['streak']:>3}  {p['total_adj']:>+5.2f}  {tier_icon} {p['tier']}")

# ── MAIN PIPELINE ─────────────────────────────────────────────
def run_pipeline(week, season, dry_run=False):
    print(f"\nEDGE INDEX WEEKLY PIPELINE — Week {week} {season}")
    print(f"{'─'*68}")

    # Load anchors
    anchor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "alt_line_anchors.json")
    anchors = {}
    if os.path.exists(anchor_path):
        with open(anchor_path) as f:
            anchors = json.load(f)
        print(f"[1] Loaded alt-line anchors: {len(anchors)} players")
    else:
        print("[1] No anchors found — run build_alt_line_anchors.py first")

    # Load defense data
    defense_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_defense.json")
    defense_data = {}
    if os.path.exists(defense_path):
        with open(defense_path) as f:
            defense_data = json.load(f)
        print(f"[2] Loaded defense data: {len(defense_data.get('pass_dvoa',{}))} teams")
    else:
        print("[2] No team_defense.json — run nfl_dvoa_proxy.py --save first")

    # Pull game logs from DB
    print(f"[3] Loading player game logs from DB...")
    player_data = pull_player_logs(season, week)
    print(f"    {len(player_data)} players with prior game logs")

    # Pull live lines
    print(f"[4] Pulling live prop lines...")
    live_lines = pull_live_lines(week, season, dry_run=dry_run)

    # ── LOAD SCHEDULE (from live_schedule.py output) ────────────
    schedule_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"schedule_w{week}_{season}.json"
    )
    if os.path.exists(schedule_path):
        with open(schedule_path) as f:
            schedule_data = json.load(f)
        GAMES = schedule_data["games"]
        print(f"    Loaded {len(GAMES)} games from schedule_w{week}_{season}.json")
    else:
        print(f"    No schedule file found — run: python live_schedule.py --week {week} --season {season}")
        print(f"    Using demo games...")
        from live_schedule import demo_games
        GAMES = demo_games()

    # Build team→game lookup
    team_game = {}
    for g in GAMES:
        team_game[g["home"]] = g
        team_game[g["away"]] = {**g, "spread": -g["spread"]}  # flip spread for away

    # ── PROCESS EACH PLAYER ────────────────────────────────────
    print(f"[5] Building context model for each player+prop...")
    plays = []

    # Demo plays with matchup data
    DEMO_MATCHUPS = {
        ("Travis Kelce",   "receptions"): {"opp_pass_dvoa":-5,  "zone_pct":0.55, "blitz_pct":0.20, "injury":False},
        ("Travis Kelce",   "rec_yds"):    {"opp_pass_dvoa":-5,  "zone_pct":0.55, "blitz_pct":0.20, "injury":False},
        ("Derrick Henry",  "rush_yds"):   {"opp_rush_dvoa":-12, "zone_pct":0.50, "blitz_pct":0.30, "injury":False},
        ("Patrick Mahomes","pass_yds"):   {"opp_pass_dvoa":-8,  "zone_pct":0.45, "blitz_pct":0.35, "injury":False},
        ("Ja'Marr Chase",  "rec_yds"):    {"opp_pass_dvoa":+8,  "zone_pct":0.60, "blitz_pct":0.28, "injury":False},
        ("Jalen Hurts",    "rush_yds"):   {"opp_rush_dvoa":+5,  "zone_pct":0.50, "blitz_pct":0.25, "injury":False},
        ("Saquon Barkley", "rush_yds"):   {"opp_rush_dvoa":+3,  "zone_pct":0.50, "blitz_pct":0.22, "injury":False},
        ("CeeDee Lamb",    "rec_yds"):    {"opp_pass_dvoa":-15, "zone_pct":0.42, "blitz_pct":0.20, "injury":False},
        ("Josh Allen",     "rush_yds"):   {"opp_rush_dvoa":+8,  "zone_pct":0.55, "blitz_pct":0.30, "injury":False},
        ("Tyreek Hill",    "rec_yds"):    {"opp_pass_dvoa":-10, "zone_pct":0.40, "blitz_pct":0.18, "injury":True},
        ("Sam LaPorta",    "receptions"): {"opp_pass_dvoa":+2,  "zone_pct":0.62, "blitz_pct":0.25, "injury":False},
        ("Josh Allen",     "pass_yds"):   {"opp_pass_dvoa":+12, "zone_pct":0.55, "blitz_pct":0.30, "injury":False},
    }

    DEMO_PRIOR = {
        "Travis Kelce":   {"receptions":[7,5,6,5,7,6,8,5,7,6,5,7,6,8,5,7,6,5,7,6], "rec_yds":[88,54,72,48,94,66,78,58,88,72,64,82,76,94,58,84,70,62,88,74]},
        "Derrick Henry":  {"rush_yds":[148,124,134,98,156,118,142,128,138,122,112,144,136,126,154,116,140,130,148,122]},
        "Patrick Mahomes":{"pass_yds":[274,254,291,264,242,281,268,294,258,284,271,288,262,278,256,294,268,282,272,286]},
        "Ja'Marr Chase":  {"rec_yds":[127,89,156,98,54,112,78,134,88,145,102,118,76,142,94,128,86,158,96,132]},
        "Jalen Hurts":    {"rush_yds":[64,71,82,58,76,84,68,74,91,78,62,88,72,66,84,78,70,86,74,80]},
        "Saquon Barkley": {"rush_yds":[112,94,128,76,108,98,134,88,104,121,96,116,84,132,102,118,88,126,106,112]},
        "CeeDee Lamb":    {"rec_yds":[112,78,94,128,68,88,134,72,104,118,82,124,76,138,92,116,86,128,98,122]},
        "Josh Allen":     {"rush_yds":[42,38,44,40,36,43,39,41,44,40,38,46,36,44,42,38,48,40,42,44],
                           "pass_yds":[312,298,334,278,318,304,342,286,324,308,298,338,282,326,312,294,344,302,318,328]},
        "Tyreek Hill":    {"rec_yds":[94,72,58,86,64,78,102,54,88,74,96,68,84,76,92,62,98,72,86,78]},
        "Sam LaPorta":    {"receptions":[6,5,7,4,6,5,6,5,7,6,5,6,4,7,5,6,5,7,6,5]},
    }

    DEMO_LINES = {
        ("Travis Kelce",   "receptions"): (4.5,  -180, "KC",  "BAL"),
        ("Travis Kelce",   "rec_yds"):    (42.5, -160, "KC",  "BAL"),
        ("Derrick Henry",  "rush_yds"):   (88.5, -150, "BAL", "KC"),
        ("Patrick Mahomes","pass_yds"):   (236.5,-130, "KC",  "BAL"),
        ("Ja'Marr Chase",  "rec_yds"):    (88.5, -120, "CIN", "PIT"),
        ("Jalen Hurts",    "rush_yds"):   (48.5, -145, "PHI", "DAL"),
        ("Saquon Barkley", "rush_yds"):   (88.5, -140, "PHI", "DAL"),
        ("CeeDee Lamb",    "rec_yds"):    (88.5, -125, "DAL", "PHI"),
        ("Josh Allen",     "rush_yds"):   (38.5, -130, "BUF", "MIA"),
        ("Josh Allen",     "pass_yds"):   (298.5,-130, "BUF", "MIA"),
        ("Tyreek Hill",    "rec_yds"):    (78.5, -110, "MIA", "BUF"),
        ("Sam LaPorta",    "receptions"): (4.5,  -150, "DET", "MIN"),
    }

    for (player, prop), (line, odds, team, opp) in DEMO_LINES.items():
        # Use real DB logs if available, fall back to demo
        if player in player_data and prop in player_data[player]["props"]:
            prior = player_data[player]["props"][prop]
            print(f"    ✓ Real DB logs: {player} {prop} ({len(prior)} games)")
        else:
            prior = DEMO_PRIOR.get(player, {}).get(prop, [])
        if not prior:
            continue

        matchup = DEMO_MATCHUPS.get((player, prop), {})
        # Override with real defense data if available
        if defense_data and opp in defense_data.get("pass_dvoa", {}):
            if prop in ("rec_yds","receptions","targets","pass_yds","pass_att"):
                matchup["opp_pass_dvoa"] = defense_data["pass_dvoa"].get(opp, 0)
                matchup["zone_pct"]      = defense_data.get("zone_pct", {}).get(opp, 0.50)
                matchup["blitz_pct"]     = defense_data.get("blitz_pct", {}).get(opp, 0.25)
            elif prop in ("rush_yds","rush_att"):
                matchup["opp_rush_dvoa"] = defense_data["rush_dvoa"].get(opp, 0)
        game    = team_game.get(team, {})

        result = build_context(
            player=player, pos="TE" if player in ("Travis Kelce","Sam LaPorta") else
                           "QB" if player in ("Patrick Mahomes","Josh Allen","Jalen Hurts") else
                           "WR" if player in ("Ja'Marr Chase","CeeDee Lamb","Tyreek Hill") else "RB",
            team=team, opp=opp,
            prop=prop, posted_line=line, prior_values=prior,
            spread=game.get("spread", 0),
            total=game.get("total", 44),
            wind=game.get("wind", 0),
            temp=game.get("temp", 65),
            precip=game.get("precip", False),
            game_window=game.get("window","SUN_EARLY"),
            team_rest=game.get("home_rest" if team==game.get("home") else "away_rest", 7),
            opp_rest=game.get("away_rest" if team==game.get("home") else "home_rest", 7),
            injury_flag=matchup.get("injury", False),
            opp_rush_dvoa=matchup.get("opp_rush_dvoa", 0),
            opp_pass_dvoa=matchup.get("opp_pass_dvoa", 0),
            zone_pct=matchup.get("zone_pct", 0.50),
            blitz_pct=matchup.get("blitz_pct", 0.25),
            anchors=anchors,
        )
        if result:
            plays.append(result)

    print(f"    Evaluated {len(plays)} plays")

    # Print report
    print_report(plays, week, season)

    # Save output
    out = {
        "week": week, "season": season,
        "generated": datetime.now().isoformat(),
        "plays": plays,
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"weekly_plays_w{week}_{season}.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n[5] Saved to weekly_plays_w{week}_{season}.json")

    return plays

# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",    type=int, default=1)
    parser.add_argument("--season",  type=int, default=2026)
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip live API calls, use DB data only")
    args = parser.parse_args()

    run_pipeline(args.week, args.season, dry_run=args.dry_run)
