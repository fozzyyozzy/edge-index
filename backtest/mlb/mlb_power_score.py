"""
Edge Index — Team Power Score
Composite team strength rating combining:
  1. Momentum      — L7/L14 record, run differential
  2. Lineup quality — aggregate wRC+ proxy from batting stats
  3. Pitcher quality — FIP-based starter rating
  4. Bullpen        — relief ERA/leverage index
  5. Park factor    — already in team_rl, used here for context

Power score feeds into mlb_team_rl.py to:
  - Validate whether a line is correctly priced
  - Find value when team signal diverges from book line
  - Flag when pitcher quality explains an elevated line

Usage:
  python mlb_power_score.py --date 2026-05-23
  python mlb_power_score.py --team "Cleveland Guardians"
"""
import os, sys, json, time, argparse, requests
from datetime import date, timedelta

BASE_API  = "https://statsapi.mlb.com/api/v1"
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept":     "application/json",
    "Origin":     "https://www.mlb.com",
    "Referer":    "https://www.mlb.com/",
}
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

POWER_CACHE = os.path.join(CACHE_DIR, "team_power_scores.json")

# ── PARK FACTORS ──────────────────────────────────────────────
PARK_FACTORS = {
    "Colorado Rockies":1.28,"Boston Red Sox":1.10,"Cincinnati Reds":1.09,
    "Philadelphia Phillies":1.06,"Texas Rangers":1.05,"Atlanta Braves":1.05,
    "St. Louis Cardinals":1.05,"San Diego Padres":1.05,"Toronto Blue Jays":1.04,
    "Chicago Cubs":1.04,"Arizona Diamondbacks":1.04,"Los Angeles Angels":1.04,
    "Milwaukee Brewers":1.02,"Baltimore Orioles":1.02,"Houston Astros":1.01,
    "New York Yankees":1.00,"Kansas City Royals":0.99,"Washington Nationals":0.99,
    "Detroit Tigers":0.98,"Pittsburgh Pirates":0.97,"Cleveland Guardians":0.97,
    "New York Mets":0.97,"Tampa Bay Rays":0.96,"Chicago White Sox":0.96,
    "Los Angeles Dodgers":0.95,"Minnesota Twins":0.94,"Miami Marlins":0.93,
    "Seattle Mariners":0.92,"San Francisco Giants":0.91,"Athletics":0.95,
}

# League average baselines
LEAGUE_ERA   = 4.10
LEAGUE_WHIP  = 1.28
LEAGUE_RS9   = 4.5   # runs scored per 9 innings
LEAGUE_WIN   = 0.500

def api_get(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_API}/{endpoint}",
            params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  API error: {e}")
    return None

def get_team_season_stats(team_id, season=2026):
    """Pull team batting + pitching season stats."""
    data = api_get(f"teams/{team_id}/stats", {
        "stats":    "season",
        "group":    "hitting,pitching",
        "season":   season,
        "sportId":  1,
    })
    if not data:
        return None, None

    hitting  = {}
    pitching = {}
    for stat in data.get("stats", []):
        group = stat.get("group", {}).get("displayName", "")
        splits = stat.get("splits", [{}])
        if splits:
            s = splits[0].get("stat", {})
            if group == "hitting":
                hitting = s
            elif group == "pitching":
                pitching = s

    return hitting, pitching

def get_team_record(team_id, season=2026):
    """Current season W/L record."""
    data = api_get("standings", {
        "leagueId": "103,104",
        "season":   season,
        "standingsTypes": "regularSeason",
        "hydrate":  "team",
    })
    if not data:
        return None

    for record in data.get("records", []):
        for team_record in record.get("teamRecords", []):
            if team_record.get("team", {}).get("id") == team_id:
                return {
                    "wins":   team_record.get("wins", 0),
                    "losses": team_record.get("losses", 0),
                    "pct":    float(team_record.get("winningPercentage", 0)),
                    "gb":     team_record.get("gamesBack", "-"),
                    "streak": team_record.get("streak", {}).get("streakCode", ""),
                    "run_diff": team_record.get("runDifferential", 0),
                    "rs":     team_record.get("runsScored", 0),
                    "ra":     team_record.get("runsAllowed", 0),
                }
    return None

def get_pitcher_fip(pitcher_id, season=2026, n_starts=5):
    """
    Calculate FIP for pitcher's last N starts.
    FIP = ((13*HR + 3*(BB+HBP) - 2*K) / IP) + FIP_constant
    FIP constant ≈ 3.10 for modern MLB
    """
    data = api_get(f"people/{pitcher_id}/stats", {
        "stats":    "gameLog",
        "group":    "pitching",
        "season":   season,
        "gameType": "R",
    })
    if not data:
        return None

    stats_list = data.get("stats", [])
    if not stats_list:
        return None
    splits = stats_list[0].get("splits", [])
    starts = [s for s in splits if s.get("stat",{}).get("gamesStarted",0) > 0]
    if not starts:
        return None

    recent = starts[-n_starts:]
    total_hr = total_bb = total_k = total_hbp = 0
    total_ip = 0.0

    for s in recent:
        st = s.get("stat", {})
        raw_ip = str(st.get("inningsPitched", "0"))
        try:
            parts = raw_ip.split(".")
            ip = int(parts[0]) + (int(parts[1])/3 if len(parts)>1 else 0)
        except:
            ip = 0
        total_ip  += ip
        total_hr  += st.get("homeRuns", 0) or 0
        total_bb  += st.get("baseOnBalls", 0) or 0
        total_k   += st.get("strikeOuts", 0) or 0
        total_hbp += st.get("hitByPitch", 0) or 0

    if total_ip <= 0 or len(recent) < 3:
        return None

    FIP_CONST = 3.10
    fip = ((13*total_hr + 3*(total_bb+total_hbp) - 2*total_k) / total_ip) + FIP_CONST
    era = sum(s.get("stat",{}).get("earnedRuns",0) or 0 for s in recent) / total_ip * 9
    whip = sum((s.get("stat",{}).get("baseOnBalls",0) or 0) + (s.get("stat",{}).get("hits",0) or 0) for s in recent) / total_ip

    return {
        "fip":    round(fip, 2),
        "era":    round(era, 2),
        "whip":   round(whip, 2),
        "ip":     round(total_ip, 1),
        "starts": len(recent),
        # FIP vs ERA delta — positive means ERA is worse than FIP (lucky/unlucky)
        "era_fip_delta": round(era - fip, 2),
    }

def score_pitcher(pitcher_stats):
    """
    Convert pitcher stats to a resistance score.
    Positive = pitcher is TOUGH (bad for offense)
    Negative = pitcher is WEAK (good for offense)
    Scale: roughly -3 to +3
    """
    if not pitcher_stats:
        return 0.0, "No data"

    fip  = pitcher_stats.get("fip",  LEAGUE_ERA)
    era  = pitcher_stats.get("era",  LEAGUE_ERA)
    whip = pitcher_stats.get("whip", LEAGUE_WHIP)

    # Use FIP as primary (ERA can be lucky/unlucky)
    fip_score  = (LEAGUE_ERA - fip) * 0.4    # elite FIP = positive resistance
    whip_score = (LEAGUE_WHIP - whip) * 1.0
    era_score  = (LEAGUE_ERA - era) * 0.2    # lesser weight

    total = fip_score + whip_score + era_score

    if total >= 1.5:
        label = "ELITE — significantly suppresses scoring"
    elif total >= 0.5:
        label = "ABOVE AVG — moderate suppression"
    elif total >= -0.5:
        label = "AVERAGE"
    elif total >= -1.5:
        label = "BELOW AVG — hitter-friendly"
    else:
        label = "WEAK — very hitter-friendly"

    return round(total, 2), label

def compute_power_score(team_id, team_name, season=2026):
    """
    Full composite power score for a team.
    Returns dict with score breakdown.
    """
    # Season stats
    hitting, pitching = get_team_season_stats(team_id, season)
    time.sleep(0.1)

    # Season record
    record = get_team_record(team_id, season)
    time.sleep(0.1)

    score = 0.0
    components = {}

    # ── OFFENSE ───────────────────────────────────────────────
    # Runs scored per game vs league avg
    if hitting:
        games = hitting.get("gamesPlayed", 1) or 1
        rs_pg = (hitting.get("runs", 0) or 0) / games
        avg   = float(hitting.get("avg", 0) or 0)
        obp   = float(hitting.get("obp", 0) or 0)
        slg   = float(hitting.get("slg", 0) or 0)
        ops   = obp + slg

        offense_score = (
            (rs_pg - LEAGUE_RS9) * 0.5 +   # runs above avg
            (ops - 0.720) * 3.0 +           # OPS above avg
            (avg - 0.250) * 5.0             # BA above avg
        )
        score += offense_score
        components["offense"] = round(offense_score, 2)
        components["rs_pg"]   = round(rs_pg, 2)
        components["ops"]     = round(ops, 3)
        components["avg"]     = round(avg, 3)

    # ── DEFENSE/PITCHING ──────────────────────────────────────
    if pitching:
        games = pitching.get("gamesPlayed", 1) or 1
        era   = float(pitching.get("era", LEAGUE_ERA) or LEAGUE_ERA)
        whip  = float(pitching.get("whip", LEAGUE_WHIP) or LEAGUE_WHIP)

        def ip_to_float(ip):
            try:
                parts = str(ip).split(".")
                return int(parts[0]) + (int(parts[1])/3 if len(parts)>1 else 0)
            except:
                return 0

        ip_total = ip_to_float(pitching.get("inningsPitched", 0))
        ks       = pitching.get("strikeOuts", 0) or 0
        k9       = ks / ip_total * 9 if ip_total > 0 else 0

        pitch_score = (
            (LEAGUE_ERA - era) * 0.4 +
            (LEAGUE_WHIP - whip) * 1.2 +
            (k9 - 8.4) * 0.05
        )
        score += pitch_score
        components["pitching"] = round(pitch_score, 2)
        components["team_era"] = round(era, 2)
        components["team_whip"]= round(whip, 2)

    # ── SEASON RECORD ─────────────────────────────────────────
    if record:
        win_pct = record["pct"]
        rd_pg   = record["run_diff"] / max(record["wins"]+record["losses"],1)
        rec_score = (
            (win_pct - LEAGUE_WIN) * 3.0 +
            rd_pg * 0.3
        )
        score += rec_score
        components["record"]   = round(rec_score, 2)
        components["win_pct"]  = win_pct
        components["run_diff_pg"] = round(rd_pg, 2)
        components["streak"]   = record.get("streak","")

    # ── PARK FACTOR ───────────────────────────────────────────
    park = PARK_FACTORS.get(team_name, 1.0)
    components["park"] = park

    # ── FINAL RATING ──────────────────────────────────────────
    if score >= 2.0:
        tier = "ELITE"
    elif score >= 1.0:
        tier = "STRONG"
    elif score >= 0.0:
        tier = "AVERAGE"
    elif score >= -1.0:
        tier = "BELOW AVG"
    else:
        tier = "WEAK"

    return {
        "team":       team_name,
        "team_id":    team_id,
        "power_score":round(score, 2),
        "tier":       tier,
        "components": components,
        "season":     season,
        "updated":    date.today().isoformat(),
    }

def get_todays_matchup_analysis(game_date, season=2026):
    """
    For each game today, compute power scores and pitcher resistance.
    Returns analysis with line value assessment.
    """
    # Get schedule
    data = api_get("schedule", {
        "sportId":  1,
        "date":     game_date,
        "hydrate":  "probablePitcher,team",
        "gameType": "R",
    })
    if not data:
        return []

    games = data.get("dates",[{}])[0].get("games",[]) if data.get("dates") else []

    # Load run lines
    lines_path = os.path.join(BASE_DIR, f"mlb_lines_{game_date}.json")
    run_lines  = {}
    if os.path.exists(lines_path):
        with open(lines_path) as f:
            raw = json.load(f)
        for rl in raw.get("run_lines", []):
            team = rl.get("team","").lower()
            line = rl.get("line", 0)
            odds = rl.get("odds", 0)
            if team not in run_lines:
                run_lines[team] = {}
            run_lines[team][line] = odds

    results = []
    print(f"\nMATCHUP POWER ANALYSIS — {game_date}")
    print("="*75)

    for game in games:
        home_data  = game.get("teams",{}).get("home",{})
        away_data  = game.get("teams",{}).get("away",{})
        home_name  = home_data.get("team",{}).get("name","?")
        away_name  = away_data.get("team",{}).get("name","?")
        home_id    = home_data.get("team",{}).get("id")
        away_id    = away_data.get("team",{}).get("id")
        home_prob  = home_data.get("probablePitcher",{})
        away_prob  = away_data.get("probablePitcher",{})

        print(f"\n  {away_name} @ {home_name}")

        # Power scores
        h_power = compute_power_score(home_id, home_name, season)
        time.sleep(0.15)
        a_power = compute_power_score(away_id, away_name, season)
        time.sleep(0.15)

        # Pitcher FIP
        h_fip = get_pitcher_fip(home_prob.get("id"), season) if home_prob.get("id") else None
        time.sleep(0.1)
        a_fip = get_pitcher_fip(away_prob.get("id"), season) if away_prob.get("id") else None
        time.sleep(0.1)

        h_pitch_score, h_pitch_label = score_pitcher(h_fip)
        a_pitch_score, a_pitch_label = score_pitcher(a_fip)

        # Composite game score
        # Away team faces home pitcher (h_pitch), home faces away pitcher (a_pitch)
        away_offense_vs_pitcher = a_power["power_score"] - h_pitch_score
        home_offense_vs_pitcher = h_power["power_score"] - a_pitch_score

        print(f"    {away_name:30} Power:{a_power['power_score']:+.2f} ({a_power['tier']})")
        print(f"      vs {home_prob.get('fullName','TBD'):20} FIP:{a_fip['fip'] if a_fip else 'N/A'}  Resistance:{h_pitch_score:+.2f} [{h_pitch_label[:20]}]")
        print(f"    {home_name:30} Power:{h_power['power_score']:+.2f} ({h_power['tier']})")
        print(f"      vs {away_prob.get('fullName','TBD'):20} FIP:{h_fip['fip'] if h_fip else 'N/A'}  Resistance:{a_pitch_score:+.2f} [{a_pitch_label[:20]}]")

        # Line value check — team power score gates prevent false positives
        for team_name, eff_score, team_power_score, opp_pitch_label in [
            (away_name, away_offense_vs_pitcher, a_power["power_score"], h_pitch_label),
            (home_name, home_offense_vs_pitcher, h_power["power_score"], a_pitch_label),
        ]:
            team_lower = team_name.lower()
            minus_odds = run_lines.get(team_lower, {}).get(-1.5)
            plus_odds  = run_lines.get(team_lower, {}).get(1.5)

            if minus_odds is not None:
                # Gate: team must be genuinely strong (power >= +0.5)
                if team_power_score >= 0.5 and eff_score >= 0.5 and minus_odds <= -130:
                    print(f"    ✅ VALUE: {team_name} -1.5 ({minus_odds}) — power:{team_power_score:+.2f} eff:{eff_score:+.2f}")
                elif team_power_score >= 0.5 and eff_score >= 0.5 and minus_odds > 100:
                    print(f"    🎯 PLUS VALUE: {team_name} -1.5 (+{minus_odds}) — strong team (+{team_power_score:.2f}) getting plus odds!")
                elif team_power_score <= -0.5 and minus_odds <= -180:
                    print(f"    ⚠️  TRAP: {team_name} -1.5 ({minus_odds}) — weak team ({team_power_score:+.2f}) heavily juiced")

            if plus_odds is not None and plus_odds >= 130:
                # Cold fade: team must be genuinely weak
                if team_power_score <= -0.5 and eff_score <= -0.3:
                    print(f"    ✅ COLD FADE: {team_name} +1.5 (+{plus_odds}) — weak team ({team_power_score:+.2f}) getting plus money")
                # Hot underdog: strong team priced as underdog
                elif team_power_score >= 0.5 and plus_odds >= 150:
                    print(f"    🎯 HOT UNDERDOG: {team_name} +1.5 (+{plus_odds}) — strong team ({team_power_score:+.2f}) as underdog, real value")

        results.append({
            "home":        home_name,
            "away":        away_name,
            "home_power":  h_power,
            "away_power":  a_power,
            "home_pitcher_fip":   h_fip,
            "away_pitcher_fip":   a_fip,
            "home_pitch_resistance": h_pitch_score,
            "away_pitch_resistance": a_pitch_score,
            "away_eff_score": round(away_offense_vs_pitcher, 2),
            "home_eff_score": round(home_offense_vs_pitcher, 2),
        })

    # Save
    out_path = os.path.join(BASE_DIR, f"mlb_power_{game_date}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Saved to {os.path.basename(out_path)}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",   default=date.today().isoformat())
    parser.add_argument("--team",   default=None)
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()

    if args.team:
        # Look up team ID
        data = api_get("teams", {"sportId":1,"season":args.season})
        teams = data.get("teams",[]) if data else []
        team  = next((t for t in teams if args.team.lower() in t.get("name","").lower()), None)
        if team:
            result = compute_power_score(team["id"], team["name"], args.season)
            print(f"\nPOWER SCORE: {result['team']}")
            print(f"  Score: {result['power_score']:+.2f} ({result['tier']})")
            for k, v in result["components"].items():
                print(f"  {k:20} {v}")
        else:
            print(f"Team '{args.team}' not found")
    else:
        get_todays_matchup_analysis(args.date, args.season)
