"""
Edge Index — Team Run Line Signal
Scores today's games for hot team -1.5 and cold team +1.5 plays.
Uses team recent record, park factors, opposing pitcher, and umpire data.

Gates:
  Hot  -1.5: only post if odds <= -150
  Cold +1.5: only post if odds >= +140

Usage:
  python mlb_team_rl.py --date 2026-05-23
  python mlb_team_rl.py --date 2026-05-23 --min-score 1.2
"""
import os, sys, json, time, argparse, requests
from datetime import date, datetime, timedelta

BASE_API  = "https://statsapi.mlb.com/api/v1"
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json, text/plain, */*",
    "Origin":     "https://www.mlb.com",
    "Referer":    "https://www.mlb.com/",
}
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

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

# Run line odds gates
HOT_MAX_ODDS  = -150   # only post hot -1.5 if odds <= -150 (less juice)
COLD_MIN_ODDS = 140    # only post cold +1.5 if odds >= +140 (plus money)

def api_get(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_API}/{endpoint}",
            params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  API error: {e}")
    return None

def load_lines(game_date):
    """Load today's odds from lines file."""
    path = os.path.join(BASE_DIR, f"mlb_lines_{game_date}.json")
    if not os.path.exists(path):
        print(f"  No lines file for {game_date} — run mlb_odds_puller.py first")
        return {}
    with open(path) as f:
        data = json.load(f)

    # Build game-level run line odds index
    # Keys: (home_team_abbr, away_team_abbr)
    rl_index = {}
    for prop in data.get("props", []):
        if prop.get("prop_type") not in ("run_line", "runline", "spread"):
            continue
        team  = prop.get("team", "")
        odds  = prop.get("odds")
        line  = prop.get("line", -1.5)
        game  = prop.get("game_id", "")
        if team and odds is not None:
            key = (game, team)
            rl_index[key] = {"odds": odds, "line": line}
    return rl_index

def get_team_record(team_id, before_date, season, n=7):
    """Last N games record for a team."""
    data = api_get("schedule", {
        "sportId": 1,
        "teamId":  team_id,
        "startDate": f"{season}-03-01",
        "endDate":  before_date,
        "season":   season,
        "gameType": "R",
        "hydrate":  "linescore",
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

    recent = games[-n:]
    wins, scored_list, allowed_list = 0, [], []

    for g in recent:
        h_id    = g["teams"]["home"]["team"]["id"]
        h_score = g["teams"]["home"].get("score", 0) or 0
        a_score = g["teams"]["away"].get("score", 0) or 0
        is_home = (h_id == team_id)
        sc      = h_score if is_home else a_score
        al      = a_score if is_home else h_score
        wins   += int(sc > al)
        scored_list.append(sc)
        allowed_list.append(al)

    g_count = len(recent)
    return {
        "wins":        wins,
        "losses":      g_count - wins,
        "win_pct":     round(wins / g_count, 3),
        "avg_scored":  round(sum(scored_list) / g_count, 2),
        "avg_allowed": round(sum(allowed_list) / g_count, 2),
        "run_diff":    round((sum(scored_list) - sum(allowed_list)) / g_count, 2),
        "streak":      _calc_streak(recent, team_id),
        "games":       g_count,
    }

def _calc_streak(games, team_id):
    """Current W/L streak."""
    streak = 0
    last   = None
    for g in reversed(games):
        h_id    = g["teams"]["home"]["team"]["id"]
        h_score = g["teams"]["home"].get("score", 0) or 0
        a_score = g["teams"]["away"].get("score", 0) or 0
        is_home = (h_id == team_id)
        won     = (h_score > a_score) if is_home else (a_score > h_score)
        if last is None:
            last   = won
            streak = 1
        elif won == last:
            streak += 1
        else:
            break
    return streak if last else -streak

def get_pitcher_stats(pitcher_id, before_date, season, n=3):
    """Last N starts ERA/WHIP/K9."""
    data = api_get(f"people/{pitcher_id}/stats", {
        "stats":     "gameLog",
        "group":     "pitching",
        "season":    season,
        "gameType":  "R",
    })
    if not data:
        return None

    stats_list = data.get("stats", [])
    if not stats_list:
        return None
    splits = stats_list[0].get("splits", [])
    starts = [s for s in splits
              if s.get("stat", {}).get("gamesStarted", 0) > 0
              and s.get("date", "") < before_date]
    if not starts:
        return None

    recent = starts[-n:]
    era_l, whip_l, k9_l = [], [], []

    for s in recent:
        st = s.get("stat", {})
        raw_ip = str(st.get("inningsPitched", "0"))
        try:
            parts  = raw_ip.split(".")
            ip     = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
        except:
            ip = 0
        if ip <= 0:
            continue
        er = st.get("earnedRuns", 0) or 0
        bb = st.get("baseOnBalls", 0) or 0
        h  = st.get("hits", 0) or 0
        k  = st.get("strikeOuts", 0) or 0
        era_l.append(er / ip * 9)
        whip_l.append((bb + h) / ip)
        k9_l.append(k / ip * 9)

    if not era_l:
        return None

    return {
        "era":     round(sum(era_l) / len(era_l), 2),
        "whip":    round(sum(whip_l) / len(whip_l), 2),
        "k_per9":  round(sum(k9_l) / len(k9_l), 2),
        "name":    data.get("people", [{}])[0].get("fullName", "Unknown") if False else "",
        "starts":  len(recent),
    }

def score_team(record, park_factor, opp_pitcher, is_home):
    """
    Composite score for a team's run-scoring outlook.
    Positive = hot/favorable, negative = cold/unfavorable.
    """
    if not record:
        return 0.0

    score = 0.0
    score += (record["win_pct"] - 0.500) * 5.0    # +2.5 for 7-0, -2.5 for 0-7
    score += (record["avg_scored"] - 4.5) * 0.4   # runs above league avg
    score += record["run_diff"] * 0.25
    score += (park_factor - 1.0) * 4.0            # park boost/penalty
    if is_home:
        score += 0.25                              # home field

    if opp_pitcher:
        score -= (opp_pitcher["era"] - 4.0) * 0.20    # good pitcher = penalty
        score -= (opp_pitcher["whip"] - 1.30) * 0.60
        score += (opp_pitcher["k_per9"] - 8.0) * 0.06

    return round(score, 2)

def load_ump_cache():
    path = os.path.join(CACHE_DIR, "umpire_stats.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def run_today(game_date, min_score=1.2, season=2026):
    print(f"\nTEAM RUN LINE SIGNALS — {game_date}")
    print("="*70)

    # Load umpire cache
    ump_cache = load_ump_cache()

    # Get today's schedule with probable pitchers
    data = api_get("schedule", {
        "sportId":  1,
        "date":     game_date,
        "hydrate":  "probablePitcher,team,officials",
        "gameType": "R",
    })
    if not data:
        print("  No schedule data")
        return []

    games = data.get("dates", [{}])[0].get("games", []) if data.get("dates") else []
    if not games:
        print("  No games today")
        return []

    print(f"  {len(games)} games today")

    # Load run line odds
    lines_path = os.path.join(BASE_DIR, f"mlb_lines_{game_date}.json")
    rl_odds = {}  # team_name_lower -> {odds, line}
    if os.path.exists(lines_path):
        with open(lines_path) as f:
            raw = json.load(f)
        # run_lines is a list of {team, opp, home, away, line, odds}
        for rl in raw.get("run_lines", []):
            team = rl.get("team", "").lower()
            if team:
                existing = rl_odds.get(team)
                # Keep best odds — for -1.5 (lower abs), for +1.5 (higher)
                if not existing:
                    rl_odds[team] = {"odds": rl.get("odds"), "line": rl.get("line", 0)}
                else:
                    # If same line, keep better odds
                    new_odds = rl.get("odds", 0)
                    old_odds = existing.get("odds", 0)
                    if rl.get("line", 0) < 0 and new_odds > old_odds:  # -1.5: want less juice
                        rl_odds[team] = {"odds": new_odds, "line": rl.get("line")}
                    elif rl.get("line", 0) > 0 and new_odds > old_odds:  # +1.5: want more plus
                        rl_odds[team] = {"odds": new_odds, "line": rl.get("line")}
        if rl_odds:
            print(f"  Loaded run line odds for {len(rl_odds)} teams")

    # Also pull moneyline odds to determine favorites
    ml_odds = {}  # team_name_lower -> ml_odds
    if os.path.exists(lines_path):
        with open(lines_path) as f:
            raw_data = json.load(f)
        for rl in raw_data.get("run_lines", []):
            # Infer ML favorite from -1.5 odds
            # If team has line=-1.5 and odds < -110, they're likely favorite
            team  = rl.get("team","").lower()
            line  = rl.get("line", 0)
            odds  = rl.get("odds", 0)
            if line == -1.5:
                ml_odds[team] = odds  # negative odds on -1.5 = strong favorite

    results = []

    for game in games:
        home_data  = game.get("teams", {}).get("home", {})
        away_data  = game.get("teams", {}).get("away", {})
        home_team  = home_data.get("team", {})
        away_team  = away_data.get("team", {})
        home_name  = home_team.get("name", "?")
        away_name  = away_team.get("name", "?")
        home_id    = home_team.get("id")
        away_id    = away_team.get("id")
        home_prob  = home_data.get("probablePitcher", {})
        away_prob  = away_data.get("probablePitcher", {})
        game_pk    = game.get("gamePk")

        # Get HP ump
        ump_name = None
        for o in game.get("officials", []):
            if o.get("officialType") == "Home Plate":
                ump_name = o.get("official", {}).get("fullName")
                break

        ump_adj = 0.0
        ump_tendency = "UNKNOWN"
        if ump_name and ump_name in ump_cache:
            u = ump_cache[ump_name]
            ump_adj = u.get("vs_league_avg", 0) * 0.05  # smaller adj for team totals
            ump_tendency = u.get("tendency", "NEUTRAL")

        print(f"\n  {away_name} @ {home_name}")
        print(f"    HP Ump: {ump_name or 'TBD'} {('HIGH_K' if ump_tendency=='HIGH_K' else 'LOW_K' if ump_tendency=='LOW_K' else '')}")

        # Pull team records
        h_rec = get_team_record(home_id, game_date, season)
        time.sleep(0.1)
        a_rec = get_team_record(away_id, game_date, season)
        time.sleep(0.1)

        # Pull pitcher stats
        h_pitch_stats = None
        a_pitch_stats = None
        if away_prob.get("id"):
            a_pitch_stats = get_pitcher_stats(away_prob["id"], game_date, season)
            if a_pitch_stats:
                a_pitch_stats["name"] = away_prob.get("fullName", "?")
            time.sleep(0.1)
        if home_prob.get("id"):
            h_pitch_stats = get_pitcher_stats(home_prob["id"], game_date, season)
            if h_pitch_stats:
                h_pitch_stats["name"] = home_prob.get("fullName", "?")
            time.sleep(0.1)

        home_park = PARK_FACTORS.get(home_name, 1.0)

        # Score each team
        h_score = score_team(h_rec, home_park, a_pitch_stats, True)
        a_score = score_team(a_rec, home_park * 0.95, h_pitch_stats, False)

        # Print scores
        for label, rec, pitcher, sc in [
            (home_name, h_rec, a_pitch_stats, h_score),
            (away_name, a_rec, h_pitch_stats, a_score),
        ]:
            if rec:
                streak = rec.get("streak", 0)
                streak_str = f"W{streak}" if streak > 0 else f"L{abs(streak)}"
                print(f"    {label:28} {rec['wins']}-{rec['losses']} L7  "
                      f"RS:{rec['avg_scored']:.1f}  RA:{rec['avg_allowed']:.1f}  "
                      f"{streak_str:4}  Score:{sc:+.2f}")
                if pitcher:
                    print(f"      vs {pitcher.get('name','?'):20} ERA:{pitcher['era']:.2f}  "
                          f"WHIP:{pitcher['whip']:.2f}  K/9:{pitcher['k_per9']:.1f}")

        diff = abs(h_score - a_score)

        # ── SIGNAL GATES ─────────────────────────────────────
        for team_name, team_score, opp_score, is_home, rec, opp_pitcher, park in [
            (home_name, h_score, a_score, True,  h_rec, a_pitch_stats, home_park),
            (away_name, a_score, h_score, False, a_rec, h_pitch_stats, home_park*0.95),
        ]:
            if not rec:
                continue

            signal_diff = team_score - opp_score

            # HOT TEAM -1.5 — only valid if team is ML favorite
            is_favorite = ml_odds.get(team_name.lower(), 0) < -110
            is_underdog = not is_favorite

            if team_score >= min_score and signal_diff >= 0.8 and is_favorite:
                # Look up odds — try full name then last word
                team_lower = team_name.lower()
                odds_data = rl_odds.get(team_lower)
                if not odds_data:
                    last_word = team_lower.split()[-1]
                    for k, v in rl_odds.items():
                        if last_word in k and v.get("line", 0) < 0:
                            odds_data = v
                            break

                odds_val   = odds_data.get("odds") if odds_data else None
                qualifies  = odds_val is not None and odds_val >= HOT_MAX_ODDS

                tier = ("⚡ AUTO" if team_score >= 2.0
                        else "★ T1"  if team_score >= 1.5
                        else "◆ T2")

                results.append({
                    "type":        "hot",
                    "team":        team_name,
                    "opp":         away_name if is_home else home_name,
                    "home":        home_name,
                    "is_home":     is_home,
                    "score":       team_score,
                    "diff":        round(signal_diff, 2),
                    "tier":        tier,
                    "record":      rec,
                    "opp_pitcher": opp_pitcher,
                    "park":        park,
                    "ump":         ump_name,
                    "ump_tendency":ump_tendency,
                    "ump_adj":     ump_adj,
                    "odds":        odds_val,
                    "line":        -1.5,
                    "qualifies":   qualifies,
                    "bet":         f"{team_name} -1.5",
                    "reason":      _hot_reason(rec, opp_pitcher, park, ump_tendency),
                })
                gate_str = f"QUALIFIES OK ({odds_val})" if qualifies else f"SKIP — juice too high ({odds_val})"
                print(f"    HOT HOT {team_name} -1.5: Score {team_score:+.2f}  {gate_str}")

            # COLD TEAM — bet OPPONENT -1.5 (cold team is weak, fade them)
            elif team_score <= -min_score and signal_diff <= -0.8 and is_underdog:
                opp_name  = home_name if not is_home else away_name
                opp_lower = opp_name.lower()
                odds_data = rl_odds.get(opp_lower)
                if not odds_data:
                    last_word = opp_lower.split()[-1]
                    for k, v in rl_odds.items():
                        if last_word in k and v.get("line", 0) < 0:
                            odds_data = v
                            break
                odds_val  = odds_data.get("odds") if odds_data else None
                qualifies = odds_val is not None and odds_val >= HOT_MAX_ODDS

                tier = ("⚡ AUTO" if team_score <= -2.0
                        else "★ T1"  if team_score <= -1.5
                        else "◆ T2")

                results.append({
                    "type":        "cold_fade",
                    "cold_team":   team_name,
                    "team":        opp_name,
                    "opp":         team_name,
                    "home":        home_name,
                    "is_home":     not is_home,
                    "score":       team_score,
                    "diff":        round(signal_diff, 2),
                    "tier":        tier,
                    "record":      rec,
                    "opp_pitcher": opp_pitcher,
                    "park":        park,
                    "ump":         ump_name,
                    "ump_tendency":ump_tendency,
                    "ump_adj":     ump_adj,
                    "odds":        odds_val,
                    "line":        -1.5,
                    "qualifies":   qualifies,
                    "bet":         opp_name + " -1.5 (fade " + team_name + ")",
                    "reason":      _cold_reason(rec, opp_pitcher, park, ump_tendency),
                })
                gate_str = f"QUALIFIES OK (" + str(odds_val) + ")" if qualifies else "SKIP — juice too high (" + str(odds_val) + ")"
                print(f"    COLD  FADE {team_name} → bet {opp_name} -1.5: Score {team_score:+.2f}  {gate_str}")

    # ── SUMMARY ──────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"QUALIFYING PLAYS — {game_date}")
    print(f"{'='*70}")

    hot_plays  = [r for r in results if r["type"]=="hot"  and r["qualifies"]]
    cold_plays = [r for r in results if r["type"]=="cold" and r["qualifies"]]

    if hot_plays:
        print(f"\nHOT HOT TEAM -1.5 (need <= -150):")
        for p in sorted(hot_plays, key=lambda x: x["score"], reverse=True):
            rec = p["record"]
            print(f"  {p['tier']:8} {p['team']:28} -1.5  {p['odds']}  Score:{p['score']:+.2f}")
            print(f"           {rec['wins']}-{rec['losses']} L7 · RS:{rec['avg_scored']:.1f} · RA:{rec['avg_allowed']:.1f}")
            print(f"           {p['reason']}")

    if cold_plays:
        print(f"\nCOLD  FADE COLD TEAM — bet OPPONENT -1.5 (need <= -150):")
        for p in sorted(cold_plays, key=lambda x: x["score"]):
            rec = p["record"]
            print(f"  {p['tier']:8} {p['team']:28} +1.5  +{p['odds']}  Score:{p['score']:+.2f}")
            print(f"           {rec['wins']}-{rec['losses']} L7 · RS:{rec['avg_scored']:.1f} · RA:{rec['avg_allowed']:.1f}")
            print(f"           {p['reason']}")

    if not hot_plays and not cold_plays:
        print("  No qualifying plays today — thresholds not met")

    # Save output
    out = {
        "date":       game_date,
        "hot_plays":  hot_plays,
        "cold_plays": cold_plays,
        "all_signals": results,
    }
    out_path = os.path.join(BASE_DIR, f"mlb_team_rl_{game_date}.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n  Saved to {os.path.basename(out_path)}")
    return out

def _hot_reason(rec, pitcher, park, ump):
    parts = []
    if rec["win_pct"] >= 0.714:
        parts.append(f"{rec['wins']}-{rec['losses']} L7 hot streak")
    if rec["avg_scored"] >= 5.5:
        parts.append(f"{rec['avg_scored']:.1f} RS/g")
    if rec["run_diff"] >= 1.5:
        parts.append(f"+{rec['run_diff']:.1f} run diff")
    if park >= 1.04:
        parts.append(f"hitter park {park:.2f}x")
    if pitcher and pitcher["era"] >= 5.0:
        parts.append(f"weak SP ERA {pitcher['era']:.2f}")
    if ump == "HIGH_K":
        parts.append("HIGH_K ump")
    return " · ".join(parts) if parts else "Composite signal"

def _cold_reason(rec, pitcher, park, ump):
    parts = []
    if rec["win_pct"] <= 0.286:
        parts.append(f"{rec['wins']}-{rec['losses']} L7 cold streak")
    if rec["avg_scored"] <= 3.5:
        parts.append(f"{rec['avg_scored']:.1f} RS/g anemic offense")
    if rec["run_diff"] <= -1.5:
        parts.append(f"{rec['run_diff']:.1f} run diff")
    if park <= 0.95:
        parts.append(f"pitcher park {park:.2f}x")
    if pitcher and pitcher["era"] <= 3.0:
        parts.append(f"elite SP ERA {pitcher['era']:.2f}")
    if ump == "LOW_K":
        parts.append("LOW_K ump — suppressed scoring")
    return " · ".join(parts) if parts else "Composite signal"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",      default=date.today().isoformat())
    parser.add_argument("--min-score", type=float, default=1.2)
    parser.add_argument("--season",    type=int, default=2026)
    args = parser.parse_args()
    run_today(args.date, args.min_score, args.season)
