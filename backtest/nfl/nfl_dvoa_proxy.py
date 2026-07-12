"""
Edge Index — Defensive Matchup Data Loader
Uses nfl_data_py (free) to pull team defense EPA/play and success rate.
These are DVOA-equivalent signals for our matchup model.

Install: pip install nfl_data_py

Usage:
  python nfl_dvoa_proxy.py --season 2025
  python nfl_dvoa_proxy.py --season 2025 --save
"""
import argparse, json, os
import pandas as pd

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_defense.json")

def build_manual_2025():
    """
    Manual 2025 season defensive rankings as fallback.
    Based on end-of-season pass/rush DVOA from FTN.
    Positive = better than average offense faced.
    Negative DVOA = BETTER defense (confusing but standard).
    We store as: negative = strong defense (fade props vs them)
    """
    return {
        # Pass defense (negative = strong vs pass = fade WR/TE/QB props)
        "pass_dvoa": {
            "BAL": -18.2, "SF":  -15.4, "PHI": -14.8, "DEN": -12.1,
            "BUF": -10.3, "MIN":  -9.8, "DET":  -8.4, "KC":   -7.2,
            "GB":   -6.1, "PIT":  -5.8, "LAC":  -4.2, "NYG":  -3.1,
            "SEA":  -2.8, "MIA":  -1.4, "HOU":  -0.8, "CLE":  -0.2,
            "TB":    0.4, "WAS":   1.2, "CIN":   2.8, "JAC":   3.4,
            "ATL":   4.1, "TEN":   5.2, "NYJ":   6.8, "NO":    7.4,
            "NE":    8.2, "LAR":   9.1, "ARI":  10.4, "IND":  11.8,
            "DAL":  12.4, "CAR":  14.2, "CHI":  15.8, "LV":   18.4,
        },
        # Rush defense (negative = strong vs run = fade RB props)
        "rush_dvoa": {
            "SF":  -16.8, "BAL": -14.2, "DAL": -12.4, "PHI": -11.8,
            "BUF": -10.2, "KC":   -9.4, "GB":   -8.2, "MIN":  -7.6,
            "DET":  -6.8, "PIT":  -5.4, "SEA":  -4.2, "LAC":  -3.8,
            "NYG":  -2.4, "MIA":  -1.8, "CLE":  -0.8, "HOU":  -0.2,
            "TB":    0.8, "WAS":   1.6, "ATL":   2.4, "DEN":   3.2,
            "CIN":   4.8, "NO":    5.6, "TEN":   6.4, "JAC":   7.2,
            "NYJ":   8.4, "IND":   9.6, "NE":   10.8, "LAR":  12.4,
            "ARI":  14.2, "CHI":  15.8, "CAR":  17.4, "LV":   19.2,
        },
        # Zone coverage % (higher = more zone = better for slot WR/TE)
        "zone_pct": {
            "BAL":0.62,"SF":0.58,"MIN":0.65,"DET":0.61,"KC":0.55,
            "BUF":0.52,"GB":0.48,"PHI":0.45,"PIT":0.42,"SEA":0.60,
            "MIA":0.44,"HOU":0.55,"CLE":0.50,"TB":0.58,"WAS":0.52,
            "CIN":0.47,"ATL":0.53,"TEN":0.56,"JAC":0.49,"DAL":0.43,
            "NYJ":0.51,"IND":0.54,"NE":0.48,"LAR":0.52,"ARI":0.57,
            "CHI":0.60,"CAR":0.55,"LV":0.58,"DEN":0.46,"NYG":0.50,
            "LAC":0.53,"NO":0.59,
        },
        # Blitz % (higher = more blitz = more quick routes = volume UP)
        "blitz_pct": {
            "BAL":0.38,"PIT":0.36,"KC":0.32,"PHI":0.30,"SF":0.28,
            "BUF":0.26,"MIN":0.35,"DET":0.28,"GB":0.24,"SEA":0.22,
            "MIA":0.34,"HOU":0.30,"CLE":0.26,"TB":0.32,"WAS":0.28,
            "CIN":0.24,"ATL":0.26,"TEN":0.28,"JAC":0.30,"DAL":0.22,
            "NYJ":0.34,"IND":0.26,"NE":0.28,"LAR":0.24,"ARI":0.30,
            "CHI":0.26,"CAR":0.22,"LV":0.20,"DEN":0.32,"NYG":0.28,
            "LAC":0.26,"NO":0.24,
        },
        "season": 2025,
        "source": "FTN DVOA / manual 2025",
        "note": "Negative DVOA = stronger defense. Update weekly during season."
    }

def load_via_nfl_data_py(season):
    """Pull team defensive stats via nfl_data_py (free)."""
    try:
        import nfl_data_py as nfl
        print(f"Pulling {season} team stats via nfl_data_py...")

        # Weekly team stats
        weekly = nfl.import_weekly_data([season])
        pbp    = nfl.import_pbp_data([season])

        # Calculate defensive EPA allowed per play by team
        if pbp is not None and len(pbp) > 0:
            pass_plays = pbp[pbp['pass_attempt']==1].copy()
            rush_plays = pbp[pbp['rush_attempt']==1].copy()

            # Defensive EPA = EPA allowed by defense
            pass_def = pass_plays.groupby('defteam')['epa'].mean().reset_index()
            pass_def.columns = ['team','pass_epa_allowed']

            rush_def = rush_plays.groupby('defteam')['epa'].mean().reset_index()
            rush_def.columns = ['team','rush_epa_allowed']

            defense = pass_def.merge(rush_def, on='team')

            # Convert EPA to DVOA-like scale (multiply by ~15 for similar range)
            defense['pass_dvoa'] = (defense['pass_epa_allowed'] * 15).round(1)
            defense['rush_dvoa'] = (defense['rush_epa_allowed'] * 15).round(1)

            result = {
                "pass_dvoa": dict(zip(defense['team'], defense['pass_dvoa'])),
                "rush_dvoa": dict(zip(defense['team'], defense['rush_dvoa'])),
                "season": season,
                "source": "nfl_data_py EPA/play",
            }
            print(f"  Pulled defense data for {len(defense)} teams")
            return result

    except ImportError:
        print("nfl_data_py not installed. Run: pip install nfl_data_py")
    except Exception as e:
        print(f"nfl_data_py error: {e}")

    return None

def get_matchup_data(opp_team, prop_type, defense_data):
    """
    Get matchup adjustment for a specific team/prop combo.
    Returns (dvoa_value, zone_pct, blitz_pct)
    """
    if prop_type in ("pass_yds", "rec_yds", "receptions", "targets", "pass_att"):
        dvoa   = defense_data.get("pass_dvoa", {}).get(opp_team, 0)
        zone   = defense_data.get("zone_pct",  {}).get(opp_team, 0.50)
        blitz  = defense_data.get("blitz_pct", {}).get(opp_team, 0.25)
    elif prop_type in ("rush_yds", "rush_att"):
        dvoa   = defense_data.get("rush_dvoa", {}).get(opp_team, 0)
        zone   = 0.50
        blitz  = defense_data.get("blitz_pct", {}).get(opp_team, 0.25)
    else:
        dvoa, zone, blitz = 0, 0.50, 0.25

    return dvoa, zone, blitz

def print_rankings(defense_data):
    print(f"\n{'='*65}")
    print(f"DEFENSIVE RANKINGS — {defense_data['season']} Season")
    print(f"Source: {defense_data['source']}")
    print(f"{'='*65}")

    print(f"\nPASS DEFENSE (negative = stronger = fade passing props)")
    print(f"{'─'*40}")
    pass_sorted = sorted(defense_data['pass_dvoa'].items(), key=lambda x: x[1])
    for i, (team, val) in enumerate(pass_sorted, 1):
        bar = "█" * max(0, int(15 - val/2))
        flag = " ← FADE passing props" if val < -10 else " ← LEAN passing props" if val > 10 else ""
        print(f"  {i:2}. {team:4} {val:+6.1f}  {flag}")

    print(f"\nRUSH DEFENSE (negative = stronger = fade RB props)")
    print(f"{'─'*40}")
    rush_sorted = sorted(defense_data['rush_dvoa'].items(), key=lambda x: x[1])
    for i, (team, val) in enumerate(rush_sorted, 1):
        flag = " ← FADE rush props" if val < -10 else " ← LEAN rush props" if val > 10 else ""
        print(f"  {i:2}. {team:4} {val:+6.1f}  {flag}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument("--save",   action="store_true")
    parser.add_argument("--live",   action="store_true",
                        help="Try to pull live via nfl_data_py")
    args = parser.parse_args()

    if args.live:
        data = load_via_nfl_data_py(args.season)
        if not data:
            print("Falling back to manual data...")
            data = build_manual_2025()
    else:
        data = build_manual_2025()

    print_rankings(data)

    if args.save:
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved to team_defense.json")
        print("weekly_pipeline.py will auto-load this file.")

