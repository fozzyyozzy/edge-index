"""
Edge Index — Pitcher K Model v2
Scores pitchers for OVER and UNDER value.
Primary signals:
  - K/IP rate (actual strikeout rate per inning)
  - L5 K streak vs line
  - Opposing lineup K%
  - Park factor
  - Rest days
  - K trend (improving/declining)

Usage:
  python mlb_pitcher_under.py --date 2026-05-13
  python mlb_pitcher_under.py --test
"""
import os, sys, json, argparse, requests
from datetime import date, datetime, timedelta

try:
    import pybaseball
    pybaseball.cache.enable()
    PYBASEBALL_OK = True
except ImportError:
    PYBASEBALL_OK = False

BASE    = "https://statsapi.mlb.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── PARK K FACTORS ────────────────────────────────────────────
PARK_K_FACTOR = {
    "Colorado Rockies":        0.88,
    "Cincinnati Reds":         0.92,
    "Texas Rangers":           0.93,
    "Minnesota Twins":         0.94,
    "Pittsburgh Pirates":      0.95,
    "Kansas City Royals":      0.95,
    "Chicago White Sox":       0.96,
    "Detroit Tigers":          0.96,
    "Baltimore Orioles":       0.97,
    "Toronto Blue Jays":       0.97,
    "Boston Red Sox":          0.97,
    "Miami Marlins":           1.00,
    "New York Yankees":        1.00,
    "Houston Astros":          1.01,
    "Cleveland Guardians":     1.01,
    "Milwaukee Brewers":       1.02,
    "Atlanta Braves":          1.02,
    "Tampa Bay Rays":          1.03,
    "Oakland Athletics":       1.03,
    "Washington Nationals":    1.03,
    "Philadelphia Phillies":   1.03,
    "New York Mets":           1.04,
    "Chicago Cubs":            1.04,
    "Los Angeles Dodgers":     1.04,
    "Los Angeles Angels":      1.04,
    "Arizona Diamondbacks":    1.04,
    "San Diego Padres":        1.05,
    "St. Louis Cardinals":     1.05,
    "Seattle Mariners":        1.05,
    "San Francisco Giants":    1.06,
}

# ── TEAM K% (batter strikeout rate) ──────────────────────────
# Higher = more Ks for pitcher = OVER friendly
TEAM_K_PCT = {
    "Colorado Rockies":      0.195,
    "St. Louis Cardinals":   0.198,
    "Kansas City Royals":    0.200,
    "Minnesota Twins":       0.205,
    "San Diego Padres":      0.208,
    "Toronto Blue Jays":     0.210,
    "Tampa Bay Rays":        0.210,
    "Boston Red Sox":        0.212,
    "Los Angeles Dodgers":   0.212,
    "New York Mets":         0.215,
    "Houston Astros":        0.215,
    "Baltimore Orioles":     0.218,
    "Atlanta Braves":        0.220,
    "New York Yankees":      0.220,
    "Chicago Cubs":          0.222,
    "Philadelphia Phillies": 0.222,
    "Cleveland Guardians":   0.225,
    "Detroit Tigers":        0.225,
    "San Francisco Giants":  0.228,
    "Texas Rangers":         0.230,
    "Seattle Mariners":      0.230,
    "Los Angeles Angels":    0.232,
    "Washington Nationals":  0.235,
    "Miami Marlins":         0.235,
    "Pittsburgh Pirates":    0.238,
    "Arizona Diamondbacks":  0.240,
    "Oakland Athletics":     0.242,
    "Milwaukee Brewers":     0.244,
    "Cincinnati Reds":       0.245,
    "Chicago White Sox":     0.248,
}

def get_pitcher_logs(pitcher_name, season=2025, n_starts=10):
    """
    Pull pitcher game logs from pybaseball.
    Returns list of {date, ip, ks, k_per_ip} dicts for recent starts.
    """
    if not PYBASEBALL_OK:
        return []

    try:
        # Search for pitcher ID
        resp = requests.get(
            f"{BASE}/sports/1/players",
            params={"season": 2026, "gameType": "R"},
            headers=HEADERS, timeout=10
        )
        pitcher_id = None
        if resp.status_code == 200:
            name_lower = pitcher_name.lower()
            for p in resp.json().get("people", []):
                full = f"{p.get('firstName','')} {p.get('lastName','')}".lower()
                if name_lower in full or full in name_lower:
                    pitcher_id = p["id"]
                    break

        if not pitcher_id:
            return []

        # Pull game log from MLB Stats API
        resp2 = requests.get(
            f"{BASE}/people/{pitcher_id}/stats",
            params={
                "stats":   "gameLog",
                "group":   "pitching",
                "season":  2026,
                "sportId": 1,
            },
            headers=HEADERS, timeout=10
        )

        if resp2.status_code != 200:
            return []

        splits = resp2.json().get("stats",[{}])[0].get("splits",[])
        starts = [s for s in splits
                 if int(s.get("stat",{}).get("gamesStarted",0)) > 0]

        logs = []
        for s in starts[-n_starts:]:
            stat = s.get("stat", {})
            ip_str = stat.get("inningsPitched","0.0")
            # Convert IP format (6.1 = 6 1/3 innings)
            ip_parts = str(ip_str).split(".")
            ip = float(ip_parts[0])
            if len(ip_parts) > 1:
                ip += int(ip_parts[1]) / 3.0
            ks = int(stat.get("strikeOuts", 0))
            k_per_ip = round(ks / max(ip, 0.1), 2)
            logs.append({
                "date":     s.get("date",""),
                "ip":       round(ip, 2),
                "ks":       ks,
                "k_per_ip": k_per_ip,
                "opp":      s.get("opponent",{}).get("name",""),
            })

        return logs

    except Exception as e:
        return []

def analyze_pitcher(pitcher_name, pitcher_id, home_team,
                    away_team, k_line, over_odds, under_odds=None):
    """
    Full pitcher K analysis — OVER and UNDER scoring.
    Returns dict with scores, signals, recommendation.
    """
    signals   = []
    over_score  = 0
    under_score = 0

    # Pull game logs
    logs = get_pitcher_logs(pitcher_name)

    # ── K/IP RATE (most important signal) ────────────────────
    if logs:
        recent_logs = logs[-5:]  # L5 starts
        avg_ks    = sum(l["ks"] for l in recent_logs) / len(recent_logs)
        avg_ip    = sum(l["ip"] for l in recent_logs) / len(recent_logs)
        avg_k_ip  = sum(l["k_per_ip"] for l in recent_logs) / len(recent_logs)

        # L5 K streak vs line
        over_streak  = sum(1 for l in recent_logs if l["ks"] > k_line)
        under_streak = sum(1 for l in recent_logs if l["ks"] <= k_line)

        signals.append(f"L5 avg: {avg_ks:.1f} Ks | {avg_ip:.1f} IP | "
                      f"{avg_k_ip:.2f} K/IP")
        signals.append(f"L5 vs line {k_line}: {over_streak} OVER / "
                      f"{under_streak} UNDER")

        # K/IP rate signal
        if avg_k_ip >= 1.5:
            over_score  += 4
            signals.append(f"⚡ ELITE K/IP: {avg_k_ip:.2f} — dominant stuff")
        elif avg_k_ip >= 1.2:
            over_score  += 2
            signals.append(f"✓ Strong K/IP: {avg_k_ip:.2f}")
        elif avg_k_ip >= 1.0:
            signals.append(f"📋 Average K/IP: {avg_k_ip:.2f}")
        else:
            under_score += 2
            signals.append(f"⚠️ Low K/IP: {avg_k_ip:.2f} — contact pitcher")

        # L5 streak vs line
        if over_streak >= 4:
            over_score  += 3
            signals.append(f"🔥 OVER streak: {over_streak}/5 starts over {k_line}")
        elif over_streak >= 3:
            over_score  += 1
            signals.append(f"📋 Moderate OVER: {over_streak}/5 over {k_line}")
        elif under_streak >= 4:
            under_score += 3
            signals.append(f"📉 UNDER streak: {under_streak}/5 under {k_line}")

        # Avg Ks vs line
        if avg_ks > k_line + 1.5:
            over_score  += 2
            signals.append(f"✓ Avg Ks ({avg_ks:.1f}) well above line ({k_line})")
        elif avg_ks > k_line:
            over_score  += 1
            signals.append(f"✓ Avg Ks ({avg_ks:.1f}) above line ({k_line})")
        elif avg_ks < k_line - 1.5:
            under_score += 2
            signals.append(f"⚠️ Avg Ks ({avg_ks:.1f}) well below line ({k_line})")
        elif avg_ks < k_line:
            under_score += 1
            signals.append(f"📋 Avg Ks ({avg_ks:.1f}) below line ({k_line})")

        # K trend (last 3 vs prior 2)
        if len(recent_logs) >= 5:
            l3_avg = sum(l["ks"] for l in recent_logs[-3:]) / 3
            p2_avg = sum(l["ks"] for l in recent_logs[:2]) / 2
            trend  = l3_avg - p2_avg
            if trend >= 2.0:
                over_score  += 1
                signals.append(f"📈 K trending UP: +{trend:.1f} Ks vs prior starts")
            elif trend <= -2.0:
                under_score += 1
                signals.append(f"📉 K trending DOWN: {trend:.1f} Ks vs prior starts")

    else:
        signals.append("⚠️ No game log data available")

    # ── OPPOSING LINEUP K% ────────────────────────────────────
    # Pitcher on home team faces away batters, and vice versa
    opp_team  = away_team
    opp_k_pct = TEAM_K_PCT.get(away_team,
                TEAM_K_PCT.get(home_team, 0.220))

    if opp_k_pct >= 0.240:
        over_score  += 3
        signals.append(f"⚡ HIGH K% LINEUP: {opp_k_pct*100:.1f}% "
                      f"({opp_team}) — strikeout-prone")
    elif opp_k_pct >= 0.225:
        over_score  += 2
        signals.append(f"✓ Above avg K% lineup: {opp_k_pct*100:.1f}%")
    elif opp_k_pct >= 0.215:
        over_score  += 1
        signals.append(f"✓ Avg K% lineup: {opp_k_pct*100:.1f}%")
    elif opp_k_pct <= 0.205:
        under_score += 2
        signals.append(f"⚠️ LOW K% LINEUP: {opp_k_pct*100:.1f}% "
                      f"({opp_team}) — makes contact")
    else:
        signals.append(f"📋 Neutral lineup K%: {opp_k_pct*100:.1f}%")

    # ── PARK FACTOR ───────────────────────────────────────────
    park_factor = PARK_K_FACTOR.get(home_team, 1.00)
    if park_factor >= 1.04:
        over_score  += 2
        signals.append(f"✓ Pitcher-friendly park: {home_team} ({park_factor:.2f}x)")
    elif park_factor >= 1.01:
        over_score  += 1
        signals.append(f"✓ Slight pitcher park: {park_factor:.2f}x")
    elif park_factor <= 0.93:
        under_score += 2
        signals.append(f"⚠️ HITTER PARK: {home_team} ({park_factor:.2f}x)")
    elif park_factor <= 0.96:
        under_score += 1
        signals.append(f"📋 Mild hitter park: {park_factor:.2f}x")
    else:
        signals.append(f"📋 Neutral park: {park_factor:.2f}x")

    # ── K LINE HEIGHT ─────────────────────────────────────────
    if k_line >= 8.5:
        under_score += 3
        signals.append(f"⚠️ VERY HIGH LINE ({k_line}) — elite bar to clear")
    elif k_line >= 7.5:
        under_score += 2
        signals.append(f"⚠️ HIGH LINE ({k_line}) — elevated bar")
    elif k_line <= 3.5:
        over_score  += 2
        signals.append(f"✓ LOW LINE ({k_line}) — easy bar, OVER value")
    elif k_line <= 4.5:
        over_score  += 1
        signals.append(f"✓ Moderate line ({k_line})")

    # ── RECOMMENDATION ────────────────────────────────────────
    net = over_score - under_score

    # ── K UNDER GATE: require BOTH signals ────────────────────
    # Data shows single-signal K unders hit ~50% — not edge
    # Requiring both K/IP < 0.85 AND 4/5 under raises to ~75%+
    # Burke (May 15): had K/IP 0.75 but only 4/5 under → should have qualified
    # Rodriguez (May 16): 0.75 K/IP AND 4/5 under → correct LEAN UNDER
    # Sean Burke had 5 Ks going OVER despite 0.75 K/IP — single signal fail
    k_under_qualified = False
    if logs:
        recent_logs   = logs[-5:]
        avg_k_ip_chk  = sum(l["k_per_ip"] for l in recent_logs) / len(recent_logs)
        under_cnt_chk = sum(1 for l in recent_logs if l["ks"] <= k_line)
        # Both gates must pass for a LEAN UNDER or stronger recommendation
        k_under_qualified = (avg_k_ip_chk < 0.85 and under_cnt_chk >= 4)

    # Override net score for UNDER recommendations
    # If net says UNDER but both gates don't pass — downgrade to SLIGHT or NEUTRAL
    if net <= -3 and not k_under_qualified:
        # Downgrade: LEAN UNDER → SLIGHT UNDER (single signal — lower confidence)
        net = max(net, -2)
        signals.append("⚠️ K UNDER GATE: only 1 of 2 signals — downgraded confidence")
        signals.append("  Need BOTH: K/IP < 0.85 AND 4/5 starts under the line")

    if net >= 6:
        rec   = "STRONG OVER ⚡"
        side  = "OVER"
        score = over_score
    elif net >= 3:
        rec   = "LEAN OVER"
        side  = "OVER"
        score = over_score
    elif net >= 1:
        rec   = "SLIGHT OVER EDGE"
        side  = "OVER"
        score = over_score
    elif net <= -6:
        rec   = "STRONG UNDER 📉"
        side  = "UNDER"
        score = under_score
    elif net <= -3:
        rec   = "LEAN UNDER"
        side  = "UNDER"
        score = under_score
    elif net <= -1:
        rec   = "SLIGHT UNDER EDGE"
        side  = "UNDER"
        score = under_score
    else:
        rec   = "NEUTRAL — skip"
        side  = "NONE"
        score = 0

    return {
        "pitcher":      pitcher_name,
        "home":         home_team,
        "away":         away_team,
        "k_line":       k_line,
        "over_odds":    over_odds,
        "under_odds":   under_odds,
        "over_score":   over_score,
        "under_score":  under_score,
        "net":          net,
        "side":         side,
        "score":        score,
        "signals":      signals,
        "rec":          rec,
        "logs":         logs[-5:] if logs else [],
    }

def analyze_todays_pitchers(game_date):
    hand_path  = os.path.join(CACHE_DIR, f"pitcher_hands_{game_date}.json")
    lines_path = os.path.join(BASE_DIR,  f"mlb_lines_{game_date}.json")

    if not os.path.exists(hand_path):
        print(f"No pitcher cache — run mlb_pitcher_hand.py --date {game_date}")
        return []
    if not os.path.exists(lines_path):
        print(f"No lines file — run mlb_odds_puller.py first")
        return []

    with open(hand_path)  as f: starters    = json.load(f)
    with open(lines_path) as f: lines_data  = json.load(f)

    try:
        import pandas as pd
        props   = pd.DataFrame(lines_data["props"])
        k_props = props[props["prop"] == "strikeouts"].copy()
        k_under = props[props["prop"] == "strikeouts_under"].copy()
    except Exception as e:
        print(f"Error loading props: {e}")
        return []

    results = []
    print(f"Analyzing {len(starters)} pitchers for K value...")
    print(f"{'─'*65}")

    for home_team, info in starters.items():
        pitcher_name = info.get("pitcher","")
        pitcher_id   = info.get("id", 0)

        pitcher_props = k_props[
            k_props["player"].str.lower() == pitcher_name.lower()
        ]
        if pitcher_props.empty:
            continue

        k_line    = float(pitcher_props.iloc[0]["line"])
        over_odds = int(pitcher_props.iloc[0]["odds"])
        game_home = pitcher_props.iloc[0].get("home", home_team)
        game_away = pitcher_props.iloc[0].get("away", "")

        # Under odds
        under_row  = k_under[
            k_under["player"].str.lower() == pitcher_name.lower()
        ]
        under_odds = int(under_row.iloc[0]["odds"]) \
                     if not under_row.empty else None

        result = analyze_pitcher(
            pitcher_name, pitcher_id,
            game_home, game_away,
            k_line, over_odds, under_odds
        )
        results.append(result)
        print(f"  {pitcher_name:28} K {result['side']:5} "
              f"(net:{result['net']:+d}) — {result['rec']}")

    results.sort(key=lambda x: x["net"], reverse=True)
    return results

def print_report(results, game_date):
    print(f"\n{'='*65}")
    print(f"EDGE INDEX — PITCHER K REPORT — {game_date}")
    print(f"{'='*65}")

    categories = [
        ("⚡ STRONG OVER",  lambda r: r["net"] >= 6),
        ("✅ LEAN OVER",    lambda r: 3 <= r["net"] < 6),
        ("⚪ SLIGHT OVER",  lambda r: 1 <= r["net"] < 3),
        ("📉 STRONG UNDER", lambda r: r["net"] <= -6),
        ("🟡 LEAN UNDER",   lambda r: -6 < r["net"] <= -3),
        ("⚪ SLIGHT UNDER", lambda r: -3 < r["net"] <= -1),
    ]

    for label, fn in categories:
        group = [r for r in results if fn(r)]
        if not group:
            continue
        print(f"\n{label}")
        print(f"{'─'*65}")
        for r in group:
            over_str  = f"{r['over_odds']:+d}"
            under_str = f"{r['under_odds']:+d}" if r['under_odds'] else "N/A"
            print(f"\n  {r['pitcher']:28} K OVER {r['k_line']}")
            print(f"  {r['away']:20} @ {r['home']}")
            print(f"  Over:{over_str:8} Under:{under_str:8} "
                  f"Net score: {r['net']:+d}")
            print(f"  → {r['rec']}")
            for sig in r["signals"]:
                print(f"    {sig}")
            # Show recent log
            if r["logs"]:
                print(f"  Recent starts:")
                for l in reversed(r["logs"][-3:]):
                    marker = "✓" if l["ks"] > r["k_line"] else "✗"
                    print(f"    {marker} {l['date'][:10]}  "
                          f"{l['ks']} Ks / {l['ip']} IP  "
                          f"({l['k_per_ip']:.2f} K/IP)  "
                          f"vs {l['opp']}")

    out_path = os.path.join(BASE_DIR, f"mlb_k_unders_{game_date}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✓ Saved to mlb_k_unders_{game_date}.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        print("Testing pitcher K model...")
        result = analyze_pitcher(
            "Test Pitcher", 0,
            "Milwaukee Brewers",
            "San Diego Padres",
            k_line=7.5,
            over_odds=-144,
            under_odds=None,
        )
        print(f"Net: {result['net']:+d} | {result['rec']}")
        for s in result["signals"]:
            print(f"  {s}")
    else:
        results = analyze_todays_pitchers(args.date)
        if results:
            print_report(results, args.date)
        else:
            print("No results — check caches exist")
