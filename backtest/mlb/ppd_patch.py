"""
Edge Index — PPD/Postponement Detection Patch
Adds postponement awareness to mlb_results_checker.py and mlb_grade_patch.py.

Add this function to mlb_results_checker.py to detect PPD games before
pulling box scores. Call get_game_statuses(game_date) at the top of the
daily run to build a PPD index.

Also handles doubleheader detection — flags game 1 vs game 2.
"""

PPD_STATUS_CODES = {"PPD", "PW", "CR", "DI"}  # postponed, weather, canceled, darkness
PPD_DETAILED     = {"Postponed", "Cancelled", "Suspended", "Suspended: Rain"}

def get_game_statuses(game_date, season=2026):
    """
    Returns dict of game statuses for the date.
    Keys: (home_team, away_team) tuples
    Values: dict with status, is_ppd, is_doubleheader, game_num
    """
    import requests
    BASE_API = "https://statsapi.mlb.com/api/v1"
    HEADERS  = {
        "User-Agent": "Mozilla/5.0",
        "Accept":     "application/json",
        "Referer":    "https://www.mlb.com/",
    }
    data = requests.get(f"{BASE_API}/schedule", params={
        "sportId":  1,
        "date":     game_date,
        "hydrate":  "team",
        "gameType": "R",
        "season":   season,
    }, headers=HEADERS, timeout=15).json()

    statuses   = {}
    team_games = {}  # track doubleheaders

    for day in data.get("dates", []):
        for g in day.get("games", []):
            home     = g.get("teams",{}).get("home",{}).get("team",{}).get("name","?")
            away     = g.get("teams",{}).get("away",{}).get("team",{}).get("name","?")
            status   = g.get("status",{})
            code     = status.get("statusCode","")
            detailed = status.get("detailedState","")
            abstract = status.get("abstractGameState","")
            game_pk  = g.get("gamePk")
            dh_num   = g.get("gameNumber", 1)

            is_ppd   = code in PPD_STATUS_CODES or detailed in PPD_DETAILED
            is_final = abstract == "Final"

            # Track doubleheaders
            pair_key = tuple(sorted([home, away]))
            if pair_key not in team_games:
                team_games[pair_key] = []
            team_games[pair_key].append(game_pk)
            is_dh = len(team_games[pair_key]) > 1

            key = (home, away, dh_num)
            statuses[key] = {
                "home":         home,
                "away":         away,
                "game_pk":      game_pk,
                "game_num":     dh_num,
                "is_ppd":       is_ppd,
                "is_final":     is_final,
                "is_dh":        is_dh,
                "status_code":  code,
                "detailed":     detailed,
            }

    # Report
    ppd_games = [v for v in statuses.values() if v["is_ppd"]]
    dh_games  = [v for v in statuses.values() if v["is_dh"]]

    if ppd_games:
        print(f"  ⚠️  POSTPONED GAMES ({len(ppd_games)}):")
        for g in ppd_games:
            print(f"    PPD: {g['away']} @ {g['home']} — {g['detailed']}")

    if dh_games:
        dh_pairs = set(tuple(sorted([g['home'],g['away']])) for g in dh_games)
        print(f"  📋 DOUBLEHEADERS ({len(dh_pairs)} pairs):")
        for pair in dh_pairs:
            print(f"    DH: {pair[0]} vs {pair[1]}")

    return statuses

def get_ppd_players(game_date, roster_cache_path=None):
    """
    Returns set of player names whose games were postponed today.
    Used to auto-void plays in grade_patch.
    """
    import json, os

    statuses = get_game_statuses(game_date)
    ppd_teams = set()

    for key, g in statuses.items():
        if g["is_ppd"]:
            ppd_teams.add(g["home"].lower())
            ppd_teams.add(g["away"].lower())

    if not ppd_teams:
        return set(), set()

    print(f"  PPD teams: {ppd_teams}")

    # Load roster cache to find players on PPD teams
    ppd_players = set()
    if roster_cache_path and os.path.exists(roster_cache_path):
        with open(roster_cache_path) as f:
            roster = json.load(f)
        for player, team in roster.items():
            if isinstance(team, str) and team.lower() in ppd_teams:
                ppd_players.add(player.lower())

    return ppd_teams, ppd_players

# ── INTEGRATION NOTES ─────────────────────────────────────────
# In mlb_results_checker.py, add at the top of the daily run:
#
#   from ppd_patch import get_game_statuses, get_ppd_players
#   statuses = get_game_statuses(game_date)
#   ppd_teams, ppd_players = get_ppd_players(game_date, roster_cache)
#
# Then when a player is "not found in box scores", check:
#   if player.lower() in ppd_players:
#       result = "void"
#       note   = "PPD — game postponed"
#   else:
#       result = "void"
#       note   = "Player not found in box scores"
#
# ── DOUBLEHEADER NOTES ────────────────────────────────────────
# mlb_odds_puller.py already pulls both DH games separately.
# mlb_run_today.py deduplicates by player/prop — so a player
# appearing in both DH games gets their best odds, not doubled.
# The grade patch handles DH correctly since it looks at total
# hits/Ks across the day's box score, not per-game.
# Main risk: a player in game 1 of a DH might not appear in
# game 2 — the grader should count whichever game they played.
