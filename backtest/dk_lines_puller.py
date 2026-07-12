"""
Edge Index — DraftKings Live Lines Puller
Pulls current-week player prop lines from DraftKings public API.
No API key required. Run Thursday morning each week.

Usage:
  python dk_lines_puller.py             # pulls all props
  python dk_lines_puller.py --week 10   # tag lines as week 10
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, json, sqlite3, argparse
from db_setup import get_conn

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# DraftKings NFL prop subcategory IDs
DK_PROP_IDS = {
    "rec_yds":    "13.5.55",
    "receptions": "13.5.56",
    "rush_yds":   "13.5.57",
    "pass_yds":   "13.5.58",
    "pass_att":   "13.5.59",
    "pass_tds":   "13.5.60",
    "rush_att":   "13.5.61",
}

DK_BASE = ("https://sportsbook.draftkings.com/sites/US-SB/api/v5/"
           "eventgroups/88808/categories/743/subcategories/{sub_id}")

def parse_american_odds(odds_str):
    """Convert DK odds string to integer American odds."""
    try:
        s = str(odds_str).replace('+','').strip()
        return int(s)
    except:
        return -115

def pull_dk_props(season=2025, week=None):
    """Pull all NFL player prop lines from DraftKings."""
    if week is None:
        week = int(input("Enter current NFL week number: "))
    
    conn = get_conn()
    cursor = conn.cursor()
    inserted = 0
    
    for prop_type, sub_id in DK_PROP_IDS.items():
        url = DK_BASE.format(sub_id=sub_id)
        print(f"  Fetching {prop_type} ({sub_id})...")
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"    HTTP {r.status_code} — skipping")
                continue
            
            data = r.json()
            events = (data.get('eventGroup', {})
                         .get('offerCategories', [{}])[0]
                         .get('offerSubcategoryDescriptors', [{}])[0]
                         .get('offerSubcategory', {})
                         .get('offers', []))
            
            for offer in events:
                for outcome in offer.get('outcomes', []):
                    player_name = outcome.get('participant', '')
                    if not player_name:
                        continue
                    
                    label     = outcome.get('label', '')   # 'Over' or 'Under'
                    line      = outcome.get('line', None)
                    odds_dec  = outcome.get('oddsDecimal', None)
                    odds_am   = outcome.get('oddsAmerican', None)
                    
                    if line is None:
                        continue
                    
                    direction = 'OVER' if 'ver' in label else 'UNDER'
                    odds_int  = parse_american_odds(odds_am) if odds_am else -115
                    
                    # Match to player in DB
                    cursor.execute(
                        "SELECT id FROM players WHERE name LIKE ?",
                        (f"%{player_name.split()[-1]}%",)
                    )
                    player_row = cursor.fetchone()
                    if not player_row:
                        continue
                    pid = player_row[0]
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO prop_lines
                        (player_id, season, week, prop_type, direction, line, odds, source)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (pid, season, week, prop_type, direction,
                          float(line), odds_int, 'actual_dk'))
                    inserted += 1
        
        except Exception as e:
            print(f"    Error: {e}")
            continue
    
    conn.commit()
    conn.close()
    print(f"\nInserted {inserted} live DK prop lines for Week {week}")
    print("These are tagged 'actual_dk' — real lines, not estimates")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--week', type=int, default=None)
    parser.add_argument('--season', type=int, default=2025)
    args = parser.parse_args()
    pull_dk_props(season=args.season, week=args.week)
