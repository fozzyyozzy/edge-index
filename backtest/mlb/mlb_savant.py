"""
Edge Index — Baseball Savant + Advanced Stats Module
Pulls xBA, hard hit %, exit velocity, L7 splits, vsTeam
from Baseball Savant CSV API and MLB Stats API.

Signals added to each play:
  - xBA (expected batting average) vs actual BA
  - Hard hit % (quality contact indicator)
  - Exit velocity avg
  - L7 avg (trend within streak)
  - Career vs today's opponent
  - Trend direction (L7 vs L14 — heating up or cooling)

Usage:
  python mlb_savant.py --date 2026-05-14
  python mlb_savant.py --player "Ernie Clement" --opp-team "Tampa Bay Rays"
  python mlb_savant.py --update-cache --date 2026-05-14
"""
import os, sys, json, argparse, requests, time
from datetime import date, datetime, timedelta

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

BASE    = "https://statsapi.mlb.com/api/v1"
SAVANT  = "https://baseballsavant.mlb.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json, text/csv",
    "Referer":    "https://baseballsavant.mlb.com/",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

SAVANT_CACHE = os.path.join(CACHE_DIR, "savant_stats.json")

# ── XBA + HARD HIT FROM BASEBALL SAVANT ──────────────────────
# ── SAVANT LEADERBOARD CACHE ─────────────────────────────────
# Downloaded once per day — all batters with 10+ PA
SAVANT_XBA_CACHE     = os.path.join(CACHE_DIR, "savant_xba.json")
SAVANT_XBA_STAMP     = os.path.join(CACHE_DIR, "savant_xba_date.txt")

def download_savant_leaderboard(season=2026):
    """
    Download full xBA leaderboard from Baseball Savant.
    Returns dict keyed by player_id: {xba, xslg, xwoba, ba, diff}
    Run once per day — covers all batters with 10+ PA.
    """
    if not PANDAS_OK:
        print("pandas required for savant download")
        return {}

    today = date.today().isoformat()

    # Check if already downloaded today
    if os.path.exists(SAVANT_XBA_STAMP):
        stamp = open(SAVANT_XBA_STAMP).read().strip()
        if stamp == today and os.path.exists(SAVANT_XBA_CACHE):
            with open(SAVANT_XBA_CACHE) as f:
                return json.load(f)

    print(f"Downloading Baseball Savant xBA leaderboard ({season})...")

    try:
        resp = requests.get(
            f"{SAVANT}/leaderboard/expected_statistics",
            params={
                "type":     "batter",
                "year":     season,
                "position": "",
                "team":     "",
                "min":      10,
                "csv":      "true",
            },
            headers=HEADERS, timeout=20
        )

        if resp.status_code != 200:
            print(f"  Savant returned {resp.status_code}")
            return {}

        import io
        # Strip BOM if present
        text = resp.text.lstrip("﻿")
        df   = pd.read_csv(io.StringIO(text))

        # Normalize column names
        df.columns = [c.strip().strip('"').lower().replace(", ","_")
                     .replace(" ","_") for c in df.columns]

        result = {}
        for _, row in df.iterrows():
            pid = str(row.get("player_id",""))
            if not pid:
                continue
            result[pid] = {
                "last_name":  row.get("last_name_first_name","").split(",")[0].strip(),
                "first_name": row.get("last_name_first_name","").split(",")[-1].strip()
                              if "," in str(row.get("last_name_first_name","")) else "",
                "pa":         int(row.get("pa", 0)),
                "ba":         float(row.get("ba", 0)),
                "xba":        float(row.get("est_ba", 0)),
                "xba_diff":   float(row.get("est_ba_minus_ba_diff", 0)),
                "slg":        float(row.get("slg", 0)),
                "xslg":       float(row.get("est_slg", 0)),
                "xslg_diff":  float(row.get("est_slg_minus_slg_diff", 0)),
                "woba":       float(row.get("woba", 0)),
                "xwoba":      float(row.get("est_woba", 0)),
                "xwoba_diff": float(row.get("est_woba_minus_woba_diff", 0)),
            }

        with open(SAVANT_XBA_CACHE, "w") as f:
            json.dump(result, f, indent=2)
        with open(SAVANT_XBA_STAMP, "w") as f:
            f.write(today)

        print(f"  ✓ Downloaded {len(result)} batters")
        return result

    except Exception as e:
        print(f"  Savant download error: {e}")
        return {}

def get_savant_stats(player_name, season=2026):
    """
    Pull xBA, xSLG, xwOBA for a player from cached leaderboard.
    """
    player_id = get_player_id(player_name)
    if not player_id:
        return {}

    # Load leaderboard
    leaderboard = download_savant_leaderboard(season)
    pid_str     = str(player_id)

    if pid_str not in leaderboard:
        return {}

    row = leaderboard[pid_str]
    return {
        "xba":      round(row["xba"],   3),
        "xba_diff": round(row["xba_diff"], 3),
        "xslg":     round(row["xslg"],  3),
        "xwoba":    round(row["xwoba"], 3),
        "ba":       round(row["ba"],    3),
        "pa":       row["pa"],
    }

def get_player_id(name):
    """Look up MLB player ID from Stats API."""
    try:
        resp = requests.get(
            f"{BASE}/sports/1/players",
            params={"season": 2026, "gameType": "R"},
            headers={**HEADERS, "Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            name_lower = name.lower()
            for p in resp.json().get("people", []):
                full = (p.get("firstName","")+" "+p.get("lastName","")).lower()
                if name_lower in full or full in name_lower:
                    return p["id"]
    except:
        pass
    return None

# ── L7 TREND SIGNAL ───────────────────────────────────────────
def get_l7_stats(player_id, season=2026):
    """
    Pull last 7 games batting average from Stats API.
    Compare to L14 to determine trend direction.
    Returns {avg, hits, ab, trend_vs_l14}
    """
    try:
        resp = requests.get(
            f"{BASE}/people/{player_id}/stats",
            params={"stats": "lastXGames", "group": "hitting",
                   "season": season, "sportId": 1,
                   "limit": 7},
            headers={**HEADERS, "Accept": "application/json"},
            timeout=10
        )

        if resp.status_code == 200:
            splits = resp.json().get("stats",[{}])[0].get("splits",[])
            if splits:
                s  = splits[0].get("stat", {})
                ab = int(s.get("atBats", 0))
                h  = int(s.get("hits", 0))
                return {
                    "avg":  round(h/max(ab,1), 3),
                    "hits": h,
                    "ab":   ab,
                }
    except:
        pass
    return {}

# ── VS TEAM (career) ──────────────────────────────────────────
def get_vs_team(player_id, opp_team_id, season=2026):
    """
    Pull career stats vs a specific opponent team.
    Returns {avg, hits, ab, hr, ops}
    """
    try:
        # Try current season first
        for s in [season, season-1, "career"]:
            params = {
                "stats":   "vsTeam",
                "group":   "hitting",
                "sportId": 1,
                "opposingTeamId": opp_team_id,
            }
            if s != "career":
                params["season"] = s
            else:
                params["stats"] = "vsTeamTotal"

            resp = requests.get(
                f"{BASE}/people/{player_id}/stats",
                params=params,
                headers={**HEADERS, "Accept": "application/json"},
                timeout=10
            )

            if resp.status_code == 200:
                splits = resp.json().get("stats",[{}])[0].get("splits",[])
                if splits:
                    st = splits[0].get("stat", {})
                    ab = int(st.get("atBats", 0))
                    h  = int(st.get("hits", 0))
                    if ab >= 5:
                        return {
                            "avg":    round(h/max(ab,1), 3),
                            "hits":   h,
                            "ab":     ab,
                            "hr":     int(st.get("homeRuns", 0)),
                            "ops":    st.get("ops", ".000"),
                            "season": s,
                        }
    except:
        pass
    return {}

# ── TEAM ID LOOKUP ────────────────────────────────────────────
TEAM_IDS = {
    "Los Angeles Angels":    108, "Arizona Diamondbacks": 109,
    "Baltimore Orioles":     110, "Boston Red Sox":       111,
    "Chicago Cubs":          112, "Cincinnati Reds":      113,
    "Cleveland Guardians":   114, "Colorado Rockies":     115,
    "Detroit Tigers":        116, "Houston Astros":       117,
    "Kansas City Royals":    118, "Los Angeles Dodgers":  119,
    "Washington Nationals":  120, "New York Mets":        121,
    "Oakland Athletics":     133, "Pittsburgh Pirates":   134,
    "San Diego Padres":      135, "Seattle Mariners":     136,
    "San Francisco Giants":  137, "St. Louis Cardinals":  138,
    "Tampa Bay Rays":        139, "Texas Rangers":        140,
    "Toronto Blue Jays":     141, "Minnesota Twins":      142,
    "Philadelphia Phillies": 143, "Atlanta Braves":       144,
    "Chicago White Sox":     145, "Miami Marlins":        146,
    "New York Yankees":      147, "Milwaukee Brewers":    158,
}

# ── REGRESSION SIGNAL ─────────────────────────────────────────
def regression_signal(actual_avg, xba, l7_avg, l14_avg):
    """
    Combine xBA, L7, L14 into a regression/trend signal.
    Returns (signal_score, direction, notes)

    signal_score:
      +2 = strong OVER signal (due for positive regression)
      +1 = mild OVER signal
       0 = neutral
      -1 = mild UNDER/caution signal
      -2 = strong UNDER signal (due for negative regression)
    """
    score = 0
    notes = []

    # xBA vs actual BA
    if xba and actual_avg:
        try:
            xba_f = float(xba)
            act_f = float(actual_avg)
            diff  = xba_f - act_f

            if diff >= 0.040:
                score += 2
                notes.append(f"xBA {xba} vs .{int(act_f*1000):03d} actual "
                             f"— hitting BELOW true skill (+{diff*1000:.0f} pts)")
            elif diff >= 0.020:
                score += 1
                notes.append(f"xBA {xba} slightly above actual .{int(act_f*1000):03d}")
            elif diff <= -0.040:
                score -= 2
                notes.append(f"xBA {xba} vs .{int(act_f*1000):03d} actual "
                             f"— LUCKY, regression risk ({diff*1000:.0f} pts)")
            elif diff <= -0.020:
                score -= 1
                notes.append(f"xBA {xba} slightly below actual — mild regression risk")
        except:
            pass

    # L7 vs L14 trend
    if l7_avg and l14_avg and l7_avg > 0 and l14_avg > 0:
        trend = l7_avg - l14_avg
        if trend >= 0.060:
            score += 2
            notes.append(f"L7 .{int(l7_avg*1000):03d} vs L14 .{int(l14_avg*1000):03d} "
                        f"— HEATING UP +{trend*1000:.0f} pts")
        elif trend >= 0.030:
            score += 1
            notes.append(f"L7 .{int(l7_avg*1000):03d} trending UP vs L14 .{int(l14_avg*1000):03d}")
        elif trend <= -0.060:
            score -= 2
            notes.append(f"L7 .{int(l7_avg*1000):03d} vs L14 .{int(l14_avg*1000):03d} "
                        f"— COOLING OFF {trend*1000:.0f} pts")
        elif trend <= -0.030:
            score -= 1
            notes.append(f"L7 .{int(l7_avg*1000):03d} trending DOWN vs L14")

    direction = "POSITIVE" if score > 0 else "NEGATIVE" if score < 0 else "NEUTRAL"
    return score, direction, notes

# ── MAIN ENRICHMENT FUNCTION ──────────────────────────────────
def enrich_player(player_name, opp_team, l14_avg=None, season=2026):
    """
    Pull all advanced signals for a player.
    Returns enriched dict with all signals and regression score.
    """
    player_id = get_player_id(player_name)
    if not player_id:
        return {"error": "player not found", "player": player_name}

    result = {
        "player":     player_name,
        "player_id":  player_id,
        "opp_team":   opp_team,
    }

    # 1. Expected stats (xBA)
    print(f"  {player_name}: pulling expected stats...", end="", flush=True)
    exp_stats = get_savant_stats(player_name, season)
    result["expected"] = exp_stats
    xba = exp_stats.get("xba")
    print(f" xBA:{xba or 'N/A'}", end="")

    # 2. L7 trend
    l7 = get_l7_stats(player_id, season)
    result["l7"] = l7
    l7_avg = l7.get("avg", 0)
    print(f" L7:{l7_avg or 'N/A'}", end="")

    # 3. vs Opponent team
    opp_id = TEAM_IDS.get(opp_team)
    if opp_id:
        vs = get_vs_team(player_id, opp_id, season)
        result["vs_team"] = vs
        if vs:
            print(f" vsTeam:{vs.get('avg','N/A')}({vs.get('ab','?')}AB)", end="")
    else:
        result["vs_team"] = {}

    # 4. Regression signal
    actual_avg = l14_avg
    score, direction, notes = regression_signal(
        actual_avg, xba, l7_avg, l14_avg)
    result["regression"] = {
        "score":     score,
        "direction": direction,
        "notes":     notes,
    }
    print(f" Regression:{score:+d}({direction})")

    time.sleep(0.3)  # rate limiting
    return result

def update_cache(game_date, season=2026):
    """
    Pull advanced stats for all batters in today's lineup.
    """
    lines_path = os.path.join(BASE_DIR, f"mlb_lines_{game_date}.json")
    if not os.path.exists(lines_path):
        print(f"No lines file for {game_date}")
        return {}

    with open(lines_path) as f:
        data = json.load(f)

    if not PANDAS_OK:
        print("pandas not available")
        return {}

    import pandas as pd
    props   = pd.DataFrame(data["props"])
    batters = props[props["prop"]=="hits"]["player"].unique().tolist()
    games   = {g.get("home_team",""):g.get("away_team","")
               for g in data.get("games",[])}

    print(f"Enriching {len(batters)} batters with advanced stats...")
    print(f"{'─'*60}")

    cache = {}
    if os.path.exists(SAVANT_CACHE):
        with open(SAVANT_CACHE) as f:
            cache = json.load(f)

    for name in batters:
        if name in cache and cache[name].get("date") == game_date:
            print(f"  {name}: cached ✓")
            continue

        # Find opponent from props
        batter_props = props[(props["player"]==name) & (props["prop"]=="hits")]
        if batter_props.empty:
            continue
        home = batter_props.iloc[0].get("home","")
        away = batter_props.iloc[0].get("away","")

        result = enrich_player(name, away, season=season)
        result["date"] = game_date
        cache[name]    = result

    with open(SAVANT_CACHE, "w") as f:
        json.dump(cache, f, indent=2, default=str)

    print(f"\n✓ Saved {len(cache)} players to savant cache")
    return cache

def get_player_signals(player_name):
    """Load cached signals for a player."""
    if not os.path.exists(SAVANT_CACHE):
        return {}
    with open(SAVANT_CACHE) as f:
        cache = json.load(f)
    return cache.get(player_name, {})

def format_signals_for_card(player_name):
    """
    Format advanced signals for display in play card dropdown.
    Returns list of note strings.
    """
    data = get_player_signals(player_name)
    if not data:
        return []

    notes = []

    # xBA signal
    exp      = data.get("expected", {})
    xba      = exp.get("xba")
    xba_diff = exp.get("xba_diff")
    xwoba    = exp.get("xwoba")
    if xba:
        diff_str = ""
        if xba_diff:
            diff_str = (" — hitting BELOW skill" if xba_diff > 0.020
                       else " — LUCKY, regression risk" if xba_diff < -0.020
                       else "")
        notes.append(f"xBA: {xba} | xwOBA: {xwoba} | xBA diff: {xba_diff:+.3f}{diff_str}")

    # L7 trend
    l7  = data.get("l7", {})
    reg = data.get("regression", {})
    if l7.get("avg"):
        trend_notes = reg.get("notes", [])
        for n in trend_notes:
            notes.append(n)

    # vs Team
    vs = data.get("vs_team", {})
    if vs.get("ab", 0) >= 5:
        notes.append(f"vs {data.get('opp_team','opp')}: "
                    f".{int(vs.get('avg',0)*1000):03d} "
                    f"({vs.get('hits',0)}-for-{vs.get('ab',0)}) "
                    f"OPS {vs.get('ops','.000')}")

    return notes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",         default=date.today().isoformat())
    parser.add_argument("--player",       default="")
    parser.add_argument("--opp-team",     default="")
    parser.add_argument("--update-cache", action="store_true")
    parser.add_argument("--test",         action="store_true")
    args = parser.parse_args()

    if args.test:
        print("Testing advanced stats for Ernie Clement...")
        result = enrich_player("Ernie Clement", "Tampa Bay Rays",
                              l14_avg=0.275, season=2026)
        print(f"\nResults:")
        print(f"  xBA:        {result.get('expected',{}).get('xba','N/A')}")
        print(f"  Hard Hit:   {result.get('expected',{}).get('hard_hit','N/A')}%")
        print(f"  L7 avg:     {result.get('l7',{}).get('avg','N/A')}")
        print(f"  vs TB:      {result.get('vs_team',{})}")
        print(f"  Regression: {result.get('regression',{}).get('score',0):+d} "
              f"— {result.get('regression',{}).get('direction','')}")
        for n in result.get("regression",{}).get("notes",[]):
            print(f"    {n}")

    elif args.player:
        result = enrich_player(args.player, args.opp_team,
                              season=2026)
        print(f"\n{'='*60}")
        print(f"ADVANCED SIGNALS: {args.player}")
        print(f"{'='*60}")
        exp = result.get("expected", {})
        print(f"xBA:         {exp.get('xba','N/A')}")
        print(f"Hard Hit:    {exp.get('hard_hit','N/A')}%")
        print(f"Exit Velo:   {exp.get('exit_velo','N/A')} mph")
        print(f"xSLG:        {exp.get('xslg','N/A')}")
        print(f"xwOBA:       {exp.get('xwoba','N/A')}")
        l7 = result.get("l7", {})
        print(f"L7 avg:      {l7.get('avg','N/A')} ({l7.get('hits','?')}-for-{l7.get('ab','?')})")
        vs = result.get("vs_team", {})
        if vs:
            print(f"vs {args.opp_team[:20]}:  .{int(vs.get('avg',0)*1000):03d} "
                 f"({vs.get('hits',0)}-for-{vs.get('ab',0)})")
        reg = result.get("regression", {})
        print(f"Regression:  {reg.get('score',0):+d} — {reg.get('direction','')}")
        for n in reg.get("notes", []):
            print(f"  → {n}")

    elif args.update_cache:
        update_cache(args.date)

    else:
        # Show cached signals summary
        if os.path.exists(SAVANT_CACHE):
            with open(SAVANT_CACHE) as f:
                cache = json.load(f)
            print(f"Savant cache: {len(cache)} players")
            print(f"\nREGRESSION SIGNALS:")
            print(f"{'─'*60}")
            players = []
            for name, d in cache.items():
                reg = d.get("regression", {})
                score = reg.get("score", 0)
                if score != 0:
                    players.append((name, score, reg.get("direction",""),
                                   reg.get("notes",[])))
            players.sort(key=lambda x: x[1], reverse=True)
            for name, score, direction, notes in players:
                print(f"  {name:28} {score:+d} {direction}")
                for n in notes[:1]:
                    print(f"    → {n}")
        else:
            print("No cache — run --update-cache first")
