"""
Edge Index — Team Run Line Backtest
Tests viability of -1.5 RL bets on hot teams vs weak pitching/parks
and +1.5 RL fades on cold teams vs strong pitching/parks.

Signals used:
  - Team offensive streak (W/L last 7, runs scored avg)
  - Opposing pitcher ERA, K/9, WHIP last 3 starts
  - Park factor
  - Team L14 batting avg (aggregate of our cold bat signal)
  - Home/away split

Usage:
  python mlb_team_backtest.py --season 2026
  python mlb_team_backtest.py --season 2026 --from 2026-04-01 --to 2026-05-22
  python mlb_team_backtest.py --season 2026 --show-all
"""
import os, sys, json, time, argparse, requests
from datetime import date, datetime, timedelta
from collections import defaultdict

BASE_API = "https://statsapi.mlb.com/api/v1"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json, text/plain, */*",
    "Origin":     "https://www.mlb.com",
    "Referer":    "https://www.mlb.com/",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── PARK FACTORS (runs scored, 1.0 = neutral) ──────────────
PARK_FACTORS = {
    "Colorado Rockies":       1.28,
    "Boston Red Sox":         1.10,
    "Cincinnati Reds":        1.09,
    "Philadelphia Phillies":  1.06,
    "Texas Rangers":          1.05,
    "Atlanta Braves":         1.05,
    "St. Louis Cardinals":    1.05,
    "San Diego Padres":       1.05,
    "Toronto Blue Jays":      1.04,
    "Chicago Cubs":           1.04,
    "Arizona Diamondbacks":   1.04,
    "Los Angeles Angels":     1.04,
    "Milwaukee Brewers":      1.02,
    "Baltimore Orioles":      1.02,
    "Houston Astros":         1.01,
    "New York Yankees":       1.00,
    "Kansas City Royals":     0.99,
    "Washington Nationals":   0.99,
    "Detroit Tigers":         0.98,
    "Pittsburgh Pirates":     0.97,
    "Cleveland Guardians":    0.97,
    "New York Mets":          0.97,
    "Tampa Bay Rays":         0.96,
    "Chicago White Sox":      0.96,
    "Los Angeles Dodgers":    0.95,
    "Minnesota Twins":        0.94,
    "Miami Marlins":          0.93,
    "Seattle Mariners":       0.92,
    "San Francisco Giants":   0.91,
    "Athletics":              0.95,
}

def api_get(endpoint, params=None, retries=2):
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE_API}/{endpoint}",
                params=params, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json()
            time.sleep(0.5)
        except Exception as e:
            if attempt == retries - 1:
                print(f"  API error: {e}")
    return None

def get_schedule(start_date, end_date, season):
    """Get all regular season games in date range."""
    data = api_get("schedule", {
        "sportId": 1,
        "startDate": start_date,
        "endDate": end_date,
        "season": season,
        "gameType": "R",
        "hydrate": "linescore,decisions,probablePitcher",
    })
    if not data:
        return []
    games = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            if g.get("status", {}).get("abstractGameState") == "Final":
                games.append(g)
    return games

def get_team_recent_record(team_id, before_date, season, n_games=7):
    """Get team W/L record and run totals for last N games before date."""
    data = api_get("schedule", {
        "sportId": 1,
        "teamId": team_id,
        "startDate": f"{season}-03-01",
        "endDate": before_date,
        "season": season,
        "gameType": "R",
        "hydrate": "linescore",
    })
    if not data:
        return None

    games = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            if g.get("status", {}).get("abstractGameState") == "Final":
                games.append(g)

    if not games:
        return None

    recent = games[-n_games:]
    wins = 0
    runs_scored = []
    runs_allowed = []

    for g in recent:
        home_id = g.get("teams",{}).get("home",{}).get("team",{}).get("id")
        away_id = g.get("teams",{}).get("away",{}).get("team",{}).get("id")
        home_score = g.get("teams",{}).get("home",{}).get("score", 0)
        away_score = g.get("teams",{}).get("away",{}).get("score", 0)

        is_home = (home_id == team_id)
        scored   = home_score if is_home else away_score
        allowed  = away_score if is_home else home_score
        won      = scored > allowed

        wins += int(won)
        runs_scored.append(scored)
        runs_allowed.append(allowed)

    return {
        "wins":         wins,
        "losses":       len(recent) - wins,
        "win_pct":      wins / len(recent),
        "avg_scored":   round(sum(runs_scored) / len(runs_scored), 2),
        "avg_allowed":  round(sum(runs_allowed) / len(runs_allowed), 2),
        "run_diff":     round((sum(runs_scored) - sum(runs_allowed)) / len(recent), 2),
        "games":        len(recent),
    }

def get_pitcher_recent(pitcher_id, before_date, season, n_starts=3):
    """Get pitcher stats for last N starts."""
    data = api_get(f"people/{pitcher_id}/stats", {
        "stats": "gameLog",
        "group": "pitching",
        "season": season,
        "gameType": "R",
    })
    if not data:
        return None

    logs = data.get("stats", [{}])[0].get("splits", [])
    # Filter to starts before date
    starts = [s for s in logs
              if s.get("stat",{}).get("gamesStarted", 0) > 0
              and s.get("date","") < before_date]

    if not starts:
        return None

    recent = starts[-n_starts:]
    era_list = []
    whip_list = []
    k9_list = []

    for s in recent:
        st = s.get("stat", {})
        ip = float(str(st.get("inningsPitched","0")).replace(".1",".33").replace(".2",".67") or 0)
        er = st.get("earnedRuns", 0)
        bb = st.get("baseOnBalls", 0)
        h  = st.get("hits", 0)
        k  = st.get("strikeOuts", 0)

        if ip > 0:
            era_list.append(er / ip * 9)
            whip_list.append((bb + h) / ip)
            k9_list.append(k / ip * 9)

    if not era_list:
        return None

    return {
        "era":   round(sum(era_list) / len(era_list), 2),
        "whip":  round(sum(whip_list) / len(whip_list), 2),
        "k_per9": round(sum(k9_list) / len(k9_list), 2),
        "starts": len(recent),
    }

def score_game(home_record, away_record, home_park, away_pitcher, home_pitcher):
    """
    Score each team's advantage.
    Returns (home_score, away_score) — higher = stronger bet candidate.
    """
    def team_score(record, park, opp_pitcher, is_home):
        if not record:
            return 0
        score = 0
        # Offensive streak
        score += (record["win_pct"] - 0.5) * 4      # +2 for 7-0, -2 for 0-7
        score += (record["avg_scored"] - 4.5) * 0.3  # runs above avg
        score += record["run_diff"] * 0.2

        # Park factor
        score += (park - 1.0) * 3  # 1.28 COL = +0.84 bonus

        # Opposing pitcher
        if opp_pitcher:
            score -= (opp_pitcher["era"] - 4.0) * 0.15   # good pitcher hurts
            score -= (opp_pitcher["whip"] - 1.3) * 0.5
            score += (opp_pitcher["k_per9"] - 8.0) * 0.05

        # Home advantage
        if is_home:
            score += 0.2

        return score

    hs = team_score(home_record, home_park, away_pitcher, True)
    as_ = team_score(away_record, home_park * 0.95, home_pitcher, False)
    return hs, as_

def run_backtest(season, start_date, end_date, score_threshold=1.5, show_all=False):
    """Run full backtest over date range."""
    print(f"\nBACKTEST: {start_date} to {end_date} (season {season})")
    print(f"Score threshold: {score_threshold}")
    print("="*70)

    games = get_schedule(start_date, end_date, season)
    print(f"Found {len(games)} completed games\n")

    results = {
        "hot_rl":   {"w":0,"l":0,"pnl":0.0},   # bet -1.5 on hot team
        "cold_rl":  {"w":0,"l":0,"pnl":0.0},   # bet +1.5 on cold team (fade)
        "all_games": [],
    }

    team_cache  = {}
    pitch_cache = {}

    for i, game in enumerate(games):
        home  = game.get("teams",{}).get("home",{})
        away  = game.get("teams",{}).get("away",{})
        h_id  = home.get("team",{}).get("id")
        a_id  = away.get("team",{}).get("id")
        h_name= home.get("team",{}).get("name","?")
        a_name= away.get("team",{}).get("name","?")
        h_score= home.get("score",0)
        a_score= away.get("score",0)
        g_date = game.get("officialDate", game.get("gameDate","")[:10])

        if i % 20 == 0:
            print(f"  Processing game {i+1}/{len(games)}...")

        # Get team records (cached)
        h_key = f"{h_id}_{g_date}"
        a_key = f"{a_id}_{g_date}"

        if h_key not in team_cache:
            team_cache[h_key] = get_team_recent_record(h_id, g_date, season)
            time.sleep(0.05)
        if a_key not in team_cache:
            team_cache[a_key] = get_team_recent_record(a_id, g_date, season)
            time.sleep(0.05)

        h_rec = team_cache[h_key]
        a_rec = team_cache[a_key]

        # Get probable pitchers
        h_prob = home.get("probablePitcher",{})
        a_prob = away.get("probablePitcher",{})
        h_pid  = h_prob.get("id")
        a_pid  = a_prob.get("id")

        h_pitch_key = f"{h_pid}_{g_date}"
        a_pitch_key = f"{a_pid}_{g_date}"

        if h_pid and h_pitch_key not in pitch_cache:
            pitch_cache[h_pitch_key] = get_pitcher_recent(h_pid, g_date, season)
            time.sleep(0.05)
        if a_pid and a_pitch_key not in pitch_cache:
            pitch_cache[a_pitch_key] = get_pitcher_recent(a_pid, g_date, season)
            time.sleep(0.05)

        h_pitch = pitch_cache.get(h_pitch_key)
        a_pitch = pitch_cache.get(a_pitch_key)

        h_park = PARK_FACTORS.get(h_name, 1.0)

        h_score_val, a_score_val = score_game(h_rec, a_rec, h_park, a_pitch, h_pitch)
        margin = h_score - a_score

        game_rec = {
            "date":    g_date,
            "home":    h_name,
            "away":    a_name,
            "h_score": h_score,
            "a_score": a_score,
            "margin":  margin,
            "h_signal": round(h_score_val, 2),
            "a_signal": round(a_score_val, 2),
            "h_rec":   h_rec,
            "a_rec":   a_rec,
        }
        results["all_games"].append(game_rec)

        # ── HOT TEAM -1.5 RL BET ──────────────────────────────
        # Bet the stronger team to win by 2+
        if h_score_val >= score_threshold and h_score_val - a_score_val >= 1.0:
            # Home team is hot — bet home -1.5
            if margin >= 2:
                results["hot_rl"]["w"]   += 1
                results["hot_rl"]["pnl"] += 58.82  # -170 payout
            else:
                results["hot_rl"]["l"]   += 1
                results["hot_rl"]["pnl"] -= 100

        elif a_score_val >= score_threshold and a_score_val - h_score_val >= 1.0:
            # Away team is hot — bet away -1.5
            if (a_score - h_score) >= 2:
                results["hot_rl"]["w"]   += 1
                results["hot_rl"]["pnl"] += 58.82
            else:
                results["hot_rl"]["l"]   += 1
                results["hot_rl"]["pnl"] -= 100

        # ── COLD TEAM +1.5 RL FADE ────────────────────────────
        # Fade the weaker team — bet them +1.5 (just need to not lose by 2+)
        if h_score_val <= -score_threshold and a_score_val - h_score_val >= 1.0:
            # Home team is cold — take cold team +1.5
            # +1.5 pays around +150 to +230 (use +180 avg)
            if margin > -2:  # lost by 0 or 1 = win on +1.5
                results["cold_rl"]["w"]   += 1
                results["cold_rl"]["pnl"] += 180
            else:
                results["cold_rl"]["l"]   += 1
                results["cold_rl"]["pnl"] -= 100

        elif a_score_val <= -score_threshold and h_score_val - a_score_val >= 1.0:
            # Away team is cold — take cold team +1.5
            if (h_score - a_score) < 2:
                results["cold_rl"]["w"]   += 1
                results["cold_rl"]["pnl"] += 180
            else:
                results["cold_rl"]["l"]   += 1
                results["cold_rl"]["pnl"] -= 100

    # ── PRINT RESULTS ─────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"BACKTEST RESULTS — Season {season}")
    print(f"{'='*70}\n")

    for label, key in [("HOT TEAM -1.5 RL", "hot_rl"), ("COLD TEAM +1.5 RL", "cold_rl")]:
        r = results[key]
        total = r["w"] + r["l"]
        rate  = r["w"] / total if total else 0
        units = r["pnl"] / 100
        print(f"  {label}")
        print(f"  Record:   {r['w']}-{r['l']} ({rate*100:.1f}%)")
        print(f"  P&L:      ${r['pnl']:+.2f} ({units:+.2f}u)  [at assumed odds]")
        print(f"  Bets:     {total}")
        if total:
            print(f"  Per bet:  ${r['pnl']/total:+.2f}")

        # Odds sensitivity — what does this hit rate mean at different odds?
        if total > 0:
            print(f"\n  Odds sensitivity at {rate*100:.1f}% hit rate:")
            if key == "cold_rl":
                for odds in [130, 150, 170, 180, 200, 220]:
                    ev = (rate * odds) - ((1-rate) * 100)
                    be = 100 / (100 + odds) * 100
                    marker = " <-- current assumption" if odds == 180 else ""
                    print(f"    +{odds}: EV ${ev:+.2f}/bet  (break-even: {be:.1f}%){marker}")
            else:
                for odds in [140, 150, 160, 170, 180, 200]:
                    payout = 100 / (odds/100)
                    ev = (rate * payout) - ((1-rate) * 100)
                    be = odds / (100 + odds) * 100
                    marker = " <-- current assumption" if odds == 170 else ""
                    print(f"    -{odds}: EV ${ev:+.2f}/bet  (break-even: {be:.1f}%){marker}")
        print()

    if show_all:
        print(f"\n{'TOP SIGNALS':}")
        print(f"  {'DATE':12} {'AWAY':25} {'HOME':25} {'SCORE':8} {'H_SIG':7} {'A_SIG':7}")
        print(f"  {'-'*85}")
        sorted_games = sorted(results["all_games"],
            key=lambda g: max(abs(g["h_signal"]), abs(g["a_signal"])),
            reverse=True)
        for g in sorted_games[:20]:
            print(f"  {g['date']:12} {g['away']:25} {g['home']:25} "
                  f"{g['a_score']}-{g['h_score']:3} "
                  f"{g['h_signal']:+.2f}  {g['a_signal']:+.2f}")

    # Save results
    out_path = os.path.join(BASE_DIR, f"team_rl_backtest_{season}.json")
    with open(out_path, "w") as f:
        json.dump({
            "season":    season,
            "from":      start_date,
            "to":        end_date,
            "threshold": score_threshold,
            "hot_rl":    results["hot_rl"],
            "cold_rl":   results["cold_rl"],
            "games":     len(results["all_games"]),
        }, f, indent=2)
    print(f"  Saved to {out_path}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season",    type=int, default=2026)
    parser.add_argument("--from",      dest="from_date", default=f"2026-03-27")
    parser.add_argument("--to",        dest="to_date",
                        default=date.today().isoformat())
    parser.add_argument("--threshold", type=float, default=1.5,
                        help="Signal score threshold to place bet")
    parser.add_argument("--show-all",  action="store_true")
    args = parser.parse_args()

    run_backtest(
        season=args.season,
        start_date=args.from_date,
        end_date=args.to_date,
        score_threshold=args.threshold,
        show_all=args.show_all,
    )
