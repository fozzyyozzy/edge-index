# -*- coding: utf-8 -*-
import os; os.environ["PYTHONIOENCODING"] = "utf-8"
"""
Edge Index [VOID] Morning Results Checker
Pulls yesterday's box scores from MLB Stats API and grades plays.
Run each morning BEFORE the daily pipeline.

Usage:
  python mlb_results_checker.py --date 2026-05-14
  python mlb_results_checker.py  (defaults to yesterday)
"""
import os, sys, json, argparse, requests
from datetime import date, timedelta

BASE    = "https://statsapi.mlb.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))

PPD_STATUS_CODES = {"PPD", "PW", "CR", "DI", "UR"}
PPD_DETAILED     = {"Postponed", "Cancelled", "Suspended", "Suspended: Rain",
                    "Postponed: Rain", "Postponed: Weather"}

def get_box_scores(game_date):
    """Pull all box scores for a given date. Detects PPDs and doubleheaders."""
    try:
        resp = requests.get(
            f"{BASE}/schedule",
            params={
                "sportId":  1,
                "date":     game_date,
                "hydrate":  "boxscore,linescore",
                "gameType": "R",
            },
            headers=HEADERS, timeout=15
        )
        if resp.status_code != 200:
            print(f"Schedule error: {resp.status_code}")
            return {}, set(), set()

        dates = resp.json().get("dates", [])
        if not dates:
            return {}, set(), set()

        games    = dates[0].get("games", [])
        box_data = {}
        ppd_teams    = set()  # team names with postponed games
        dh_matchups  = {}     # track doubleheaders

        for game in games:
            status   = game.get("status", {})
            abstract = status.get("abstractGameState", "")
            code     = status.get("statusCode", "")
            detailed = status.get("detailedState", "")
            home     = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "")
            away     = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "")
            game_pk  = game.get("gamePk")
            game_num = game.get("gameNumber", 1)

            # Detect PPD
            is_ppd = code in PPD_STATUS_CODES or detailed in PPD_DETAILED
            if is_ppd:
                ppd_teams.add(home)
                ppd_teams.add(away)
                print(f"  PPD: {away} @ {home} [VOID] {detailed}")
                continue

            # Track doubleheaders
            pair = tuple(sorted([home, away]))
            if pair in dh_matchups:
                dh_matchups[pair].append(game_pk)
                print(f"  DH Game {game_num}: {away} @ {home}")
            else:
                dh_matchups[pair] = [game_pk]

            if abstract != "Final":
                continue

            home_score = game.get("teams", {}).get("home", {}).get("score", 0)
            away_score = game.get("teams", {}).get("away", {}).get("score", 0)

            box = get_game_box_score(game_pk)
            box_data[game_pk] = {
                "home":       home,
                "away":       away,
                "home_score": home_score,
                "away_score": away_score,
                "total_runs": home_score + away_score,
                "game_num":   game_num,
                "players":    box,
            }
            dh_label = f" (Game {game_num})" if dh_matchups.get(pair,[]) and len(dh_matchups.get(pair,[])) > 1 else ""
            print(f"  {away} {away_score} @ {home} {home_score}{dh_label} [VOID] {len(box)} players")

        return box_data, ppd_teams, dh_matchups

    except Exception as e:
        print(f"Error: {e}")
        return {}, set(), set()

def get_game_box_score(game_pk):
    """Get player stats from a specific game."""
    try:
        resp = requests.get(
            f"{BASE}/game/{game_pk}/boxscore",
            headers=HEADERS, timeout=15
        )
        if resp.status_code != 200:
            return {}

        data    = resp.json()
        players = {}

        for side in ["home", "away"]:
            team_players = data.get("teams", {}).get(side, {}).get("players", {})
            for pid, pdata in team_players.items():
                name   = pdata.get("person", {}).get("fullName", "")
                stats  = pdata.get("stats", {})

                # Batting stats
                batting = stats.get("batting", {})
                hits    = batting.get("hits", None)
                ab      = batting.get("atBats", None)
                hr      = batting.get("homeRuns", 0)
                tb      = batting.get("totalBases", None)

                # Pitching stats
                pitching = stats.get("pitching", {})
                ks       = pitching.get("strikeOuts", None)
                ip_str   = pitching.get("inningsPitched", None)

                if name:
                    players[name.lower()] = {
                        "name":   name,
                        "hits":   hits,
                        "ab":     ab,
                        "hr":     hr,
                        "tb":     tb,
                        "ks":     ks,
                        "ip":     ip_str,
                        "side":   side,
                    }

        return players

    except Exception as e:
        return {}

def grade_play(play, all_players, ppd_teams=None):
    """
    Grade a single play against box score data.
    Returns (result, actual_value, note)
    """
    player_name = play.get("player", "").lower()
    prop        = play.get("prop", "")
    line        = float(play.get("line", 0.5))
    team        = play.get("team", "")

    # Check if player's team had a PPD game
    if ppd_teams:
        for ppd_team in ppd_teams:
            if team and team.lower() in ppd_team.lower():
                return "void", None, f"PPD [VOID] {ppd_team} game postponed"

    # Find player in box scores
    player_data = None
    for game_pk, game in all_players.items():
        for pname, pdata in game.get("players", {}).items():
            if player_name in pname or pname in player_name:
                player_data = pdata
                player_data["game"] = f"{game['away']} @ {game['home']}"
                player_data["total_runs"] = game["total_runs"]
                break
        if player_data:
            break

    if not player_data:
        return "void", None, "Player not found in box scores"

    # Grade by prop type
    if "hits" in prop.lower() or prop == "hits":
        actual = player_data.get("hits")
        if actual is None:
            return "void", None, "Did not bat"
        ab = player_data.get("ab", 0)
        if ab == 0:
            return "void", 0, "0 AB [VOID] did not bat"
        result = "hit" if actual > line else "miss"
        return result, actual, f"{actual} hits in {ab} AB"

    elif "total_bases" in prop.lower() or "tb" in prop.lower():
        actual = player_data.get("tb")
        if actual is None:
            return "void", None, "Did not bat"
        result = "hit" if actual > line else "miss"
        return result, actual, f"{actual} total bases"

    elif "strikeout" in prop.lower() or prop == "strikeouts":
        actual = player_data.get("ks")
        if actual is None:
            return "void", None, "Did not pitch"
        result = "hit" if actual > line else "miss"
        ip = player_data.get("ip", "?")
        return result, actual, f"{actual} Ks in {ip} IP"

    return "void", None, f"Unknown prop: {prop}"

def check_results(game_date):
    """Main function [VOID] grade all plays from yesterday."""
    plays_path = os.path.join(BASE_DIR, f"mlb_plays_{game_date}.json")

    if not os.path.exists(plays_path):
        print(f"No plays file for {game_date}")
        print(f"Run pipeline first for that date")
        return

    with open(plays_path) as f:
        plays_data = json.load(f)

    print(f"\nPulling box scores for {game_date}...")
    box_scores, ppd_teams, dh_matchups = get_box_scores(game_date)

    if ppd_teams:
        print(f"  POSTPONED teams: {', '.join(sorted(ppd_teams))}")
    if dh_matchups:
        dh_pairs = [k for k,v in dh_matchups.items() if len(v) > 1]
        if dh_pairs:
            print(f"  DOUBLEHEADERs: {len(dh_pairs)} pair(s)")

    if not box_scores and not ppd_teams:
        print("No completed games found")
        return

    all_plays = (
        [p for p in plays_data.get("pitcher_plays", []) if p] +
        [p for p in plays_data.get("batter_plays", []) if p]
    )

    print(f"\n{'='*65}")
    print(f"EDGE INDEX RESULTS [VOID] {game_date}")
    print(f"{'='*65}")

    hits   = []
    misses = []
    voids  = []
    pnl    = 0.0

    for play in all_plays:
        tier = play.get("tier", "")
        if tier not in ("AUTO", "T1", "T2"):
            continue

        result, actual, note = grade_play(play, box_scores, ppd_teams)

        odds    = int(play.get("odds", -110))
        player  = play.get("player", "")
        prop    = play.get("prop", "")
        line    = play.get("line", 0.5)
        model   = play.get("model_prob", 0)

        if result == "hit":
            win = 100*(100/abs(odds)) if odds < 0 else 100*(odds/100)
            pnl += win
            hits.append(play)
            marker = "[HIT]"
            color_note = f"+${win:.2f}"
        elif result == "miss":
            pnl -= 100
            misses.append(play)
            marker = "[MISS]"
            color_note = "-$100.00"
        else:
            voids.append(play)
            marker = "[VOID]"
            color_note = "VOID"

        odds_str = f"{odds:+d}"
        print(f"  {marker} {tier:4} {player:28} {prop[:12]:12} {odds_str:6} "
              f"actual:{actual if actual is not None else '[VOID]':4} "
              f"{color_note:10} {note}")

    # Check fade plays
    fade_plays = [p for p in plays_data.get("fade_plays", []) if p]
    if fade_plays:
        print(f"\n{'─'*65}")
        print(f"FADE FADE PLAYS (UNDER):")
        for play in fade_plays:
            # For fades, we check UNDER [VOID] hit if actual hits = 0
            player  = play.get("player", "")
            prop    = play.get("prop", "hits")
            line    = float(play.get("line", 0.5))
            under_odds = int(play.get("under_odds", 110))

            # Find player
            fade_play = {"player": player, "prop": prop, "line": line, "odds": -110}
            result, actual, note = grade_play(fade_play, box_scores, ppd_teams)

            # Fade is HIT if actual <= line (UNDER hits)
            if result == "hit":
                fade_result = "miss"  # OVER hit = fade missed
            elif result == "miss":
                fade_result = "hit"   # OVER missed = fade hit
            else:
                fade_result = "void"

            if fade_result == "hit":
                win = 100*(under_odds/100) if under_odds > 0 else 100*(100/abs(under_odds))
                marker = "[HIT]"
                color_note = f"+${win:.2f}"
                pnl += win
            elif fade_result == "miss":
                marker = "[MISS]"
                color_note = "-$100.00"
                pnl -= 100
            else:
                marker = "[VOID]"
                color_note = "VOID"

            odds_str = f"{under_odds:+d}"
            print(f"  {marker} FADE {player:28} UNDER {line} {odds_str:6} "
                  f"actual:{actual if actual is not None else '[VOID]':4} "
                  f"{color_note}")

    # Summary
    total    = len(hits) + len(misses)
    rate     = hits.__len__() / max(total, 1)
    print(f"\n{'='*65}")
    print(f"RESULTS: {len(hits)}-{len(misses)} ({rate*100:.1f}%)"
          f"  |  {len(voids)} voids"
          f"  |  P&L: {'+' if pnl>=0 else ''}${pnl:.2f}"
          f"  ({'+' if pnl>=0 else ''}{pnl/100:.2f}u)")
    print(f"{'='*65}")

    # Save results
    out = {
        "date":    game_date,
        "hits":    len(hits),
        "misses":  len(misses),
        "voids":   len(voids),
        "pnl":     round(pnl, 2),
        "units":   round(pnl/100, 2),
        "rate":    round(rate, 3),
        "plays":   [
            {
                "player": p.get("player"),
                "prop":   p.get("prop"),
                "line":   p.get("line"),
                "odds":   p.get("odds"),
                "tier":   p.get("tier"),
                "result": grade_play(p, box_scores, ppd_teams)[0],
                "actual": grade_play(p, box_scores, ppd_teams)[1],
            }
            for p in all_plays if p.get("tier") in ("AUTO","T1","T2")
        ],
        # Full box score data [VOID] used by mlb_grade_patch for fade grading
        # Keys are player name lowercase, values include hits, ab, ks, ip
        "box_scores": {
            name: {
                "hits": pdata.get("hits"),
                "ab":   pdata.get("ab"),
                "ks":   pdata.get("ks"),
                "ip":   pdata.get("ip"),
            }
            for game_data in box_scores.values()
            if isinstance(game_data, dict)
            for name, pdata in game_data.get("players", {}).items()
            if isinstance(pdata, dict)
        }
    }

    out_path = os.path.join(BASE_DIR, f"mlb_results_{game_date}.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n[HIT] Results saved to mlb_results_{game_date}.json")
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=(date.today()-timedelta(days=1)).isoformat())
    args = parser.parse_args()
    check_results(args.date)
