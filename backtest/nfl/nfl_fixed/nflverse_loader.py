import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Edge Index — nflverse Data Loader
Downloads real NFL stats from nflverse GitHub releases.
Run this on YOUR machine (not sandboxed environment).

Step 1: pip install requests pandas
Step 2: python nflverse_loader.py
Step 3: python run_backtest.py --quick

This replaces the manual seeder entirely.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, pandas as pd, numpy as np, sqlite3, io, gzip
from db_setup import get_conn, init_db

# ── Usage thresholds for player selection ─────────────────────────────────────
USAGE_THRESHOLDS = {
    "WR": {"target_share": 0.12, "snap_pct": 0.55},
    "TE": {"target_share": 0.10, "snap_pct": 0.50},
    "QB": {"attempts_per_game": 25,  "snap_pct": 0.85},
    "RB": {"carries_per_game": 8,    "rec_targets_per_game": 3},  # either/or
}

SEASONS = [2023, 2024, 2025]

# ── nflverse URLs ─────────────────────────────────────────────────────────────
BASE = "https://github.com/nflverse/nflverse-data/releases/download"

URLS = {
    "player_stats": f"{BASE}/player_stats/player_stats.csv",
    "snap_counts":  f"{BASE}/snap_counts/snap_counts_{{season}}.csv",
    "ngs_recv":     f"{BASE}/nextgen_stats/ngs_receiving_{{season}}.csv",
    "ngs_rush":     f"{BASE}/nextgen_stats/ngs_rushing_{{season}}.csv",
    "ngs_pass":     f"{BASE}/nextgen_stats/ngs_passing_{{season}}.csv",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Edge Index research project)"}

def fetch(url, label=""):
    print(f"  Downloading {label or url[:60]}...")
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), low_memory=False)

def fetch_gz(url, label=""):
    print(f"  Downloading {label or url[:60]}...")
    r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
    r.raise_for_status()
    with gzip.GzipFile(fileobj=io.BytesIO(r.content)) as f:
        return pd.read_csv(f, low_memory=False)

def select_players_by_usage(stats_df, season):
    """
    Auto-select players based on usage thresholds.
    Returns dict: {player_name: {pos, team, avg_metrics}}
    """
    df = stats_df[stats_df['season'] == season].copy()
    
    selected = {}
    
    # ── WR ──
    wr = df[df['position'] == 'WR'].copy()
    wr_agg = wr.groupby(['player_name','recent_team']).agg(
        games=('week','count'),
        avg_targets=('targets','mean'),
        avg_receptions=('receptions','mean'),
        avg_rec_yds=('receiving_yards','mean'),
        total_targets=('targets','sum'),
    ).reset_index()
    wr_agg['target_share_proxy'] = wr_agg['avg_targets'] / 8.5  # ~8.5 team targets/skill player
    
    # Top 50 by targets
    top_wr = wr_agg[wr_agg['games'] >= 8].nlargest(50, 'total_targets')
    for _, r in top_wr.iterrows():
        selected[r['player_name']] = {
            'pos': 'WR', 'team': r['recent_team'],
            'avg_rec_yds': round(r['avg_rec_yds'], 1),
            'avg_targets': round(r['avg_targets'], 1),
        }
    
    # ── TE ──
    te = df[df['position'] == 'TE'].copy()
    te_agg = te.groupby(['player_name','recent_team']).agg(
        games=('week','count'),
        avg_targets=('targets','mean'),
        avg_rec_yds=('receiving_yards','mean'),
        total_targets=('targets','sum'),
    ).reset_index()
    top_te = te_agg[te_agg['games'] >= 8].nlargest(15, 'total_targets')
    for _, r in top_te.iterrows():
        selected[r['player_name']] = {
            'pos': 'TE', 'team': r['recent_team'],
            'avg_rec_yds': round(r['avg_rec_yds'], 1),
            'avg_targets': round(r['avg_targets'], 1),
        }
    
    # ── QB ──
    qb = df[df['position'] == 'QB'].copy()
    qb_agg = qb.groupby(['player_name','recent_team']).agg(
        games=('week','count'),
        avg_attempts=('attempts','mean'),
        avg_pass_yds=('passing_yards','mean'),
        total_att=('attempts','sum'),
    ).reset_index()
    top_qb = qb_agg[
        (qb_agg['games'] >= 8) & (qb_agg['avg_attempts'] >= 25)
    ].nlargest(20, 'total_att')
    for _, r in top_qb.iterrows():
        selected[r['player_name']] = {
            'pos': 'QB', 'team': r['recent_team'],
            'avg_pass_yds': round(r['avg_pass_yds'], 1),
            'avg_attempts': round(r['avg_attempts'], 1),
        }
    
    # ── RB ──
    rb = df[df['position'] == 'RB'].copy()
    rb_agg = rb.groupby(['player_name','recent_team']).agg(
        games=('week','count'),
        avg_carries=('carries','mean'),
        avg_rush_yds=('rushing_yards','mean'),
        avg_targets=('targets','mean'),
        avg_rec_yds=('receiving_yards','mean'),
        total_touches=('carries','sum'),
    ).reset_index()
    # RB: either workhorse OR receiving back
    top_rb = rb_agg[
        (rb_agg['games'] >= 8) &
        ((rb_agg['avg_carries'] >= 8) | (rb_agg['avg_targets'] >= 3))
    ].nlargest(30, 'total_touches')
    for _, r in top_rb.iterrows():
        selected[r['player_name']] = {
            'pos': 'RB', 'team': r['recent_team'],
            'avg_rush_yds': round(r['avg_rush_yds'], 1),
            'avg_rec_yds':  round(r['avg_rec_yds'], 1),
            'avg_carries':  round(r['avg_carries'], 1),
            'avg_targets':  round(r['avg_targets'], 1),
        }
    
    return selected

def seed_from_nflverse(seasons=SEASONS):
    """Main function — downloads data and seeds the DB."""
    
    init_db()
    conn = get_conn()
    cursor = conn.cursor()
    
    print("\n[1/3] Downloading nflverse player stats (all seasons)...")
    try:
        stats = fetch(URLS['player_stats'], "player_stats.csv")
        print(f"  Loaded {len(stats):,} weekly records")
        print(f"  Seasons available: {sorted(stats['season'].unique())}")
        print(f"  Columns: {list(stats.columns[:15])}")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  → Check internet connection and try again")
        return

    total_players = 0
    total_logs = 0
    
    for season in seasons:
        print(f"\n[Season {season}]")
        season_df = stats[stats['season'] == season]
        
        if season_df.empty:
            print(f"  No data for {season}")
            continue
        
        # Auto-select players by usage
        players = select_players_by_usage(stats, season)
        print(f"  Selected {len(players)} players by usage thresholds")
        print(f"  WR: {sum(1 for p in players.values() if p['pos']=='WR')}")
        print(f"  QB: {sum(1 for p in players.values() if p['pos']=='QB')}")
        print(f"  RB: {sum(1 for p in players.values() if p['pos']=='RB')}")
        print(f"  TE: {sum(1 for p in players.values() if p['pos']=='TE')}")
        
        # Seed each player's game logs
        for player_name, meta in players.items():
            pos  = meta['pos']
            team = meta['team']
            
            # Get player's weekly logs for this season
            player_logs = season_df[
                (season_df['player_name'] == player_name) |
                (season_df['player_display_name'] == player_name)
            ].sort_values('week')
            
            if player_logs.empty:
                continue
            
            # Get or create player
            cursor.execute(
                "INSERT OR IGNORE INTO players (name, team, position) VALUES (?,?,?)",
                (player_name, team, pos)
            )
            cursor.execute("SELECT id FROM players WHERE name=?", (player_name,))
            row = cursor.fetchone()
            if not row: continue
            pid = row[0]
            
            # Clear existing logs for this player+season
            cursor.execute(
                "DELETE FROM game_logs WHERE player_id=? AND season=?",
                (pid, season)
            )
            
            for _, log in player_logs.iterrows():
                week = int(log.get('week', 0))
                if week == 0 or week > 22: continue
                
                opp = str(log.get('opponent_team', '')).replace('@','').strip()
                
                if pos == 'QB':
                    cursor.execute("""
                        INSERT INTO game_logs
                        (player_id,season,week,team,opponent,result,
                         pass_yds,pass_att,pass_cmp,pass_tds,interceptions,rush_yds)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (pid, season, week, team, opp,
                          'W' if log.get('result','')=='W' else 'L',
                          int(log.get('passing_yards',0) or 0),
                          int(log.get('attempts',0) or 0),
                          int(log.get('completions',0) or 0),
                          int(log.get('passing_tds',0) or 0),
                          int(log.get('interceptions',0) or 0),
                          int(log.get('rushing_yards',0) or 0)))
                
                elif pos == 'RB':
                    cursor.execute("""
                        INSERT INTO game_logs
                        (player_id,season,week,team,opponent,result,
                         rush_yds,rush_att,receptions,rec_yds,targets)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (pid, season, week, team, opp,
                          'W' if log.get('result','')=='W' else 'L',
                          int(log.get('rushing_yards',0) or 0),
                          int(log.get('carries',0) or 0),
                          int(log.get('receptions',0) or 0),
                          int(log.get('receiving_yards',0) or 0),
                          int(log.get('targets',0) or 0)))
                
                else:  # WR, TE
                    cursor.execute("""
                        INSERT INTO game_logs
                        (player_id,season,week,team,opponent,result,
                         receptions,rec_yds,targets)
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (pid, season, week, team, opp,
                          'W' if log.get('result','')=='W' else 'L',
                          int(log.get('receptions',0) or 0),
                          int(log.get('receiving_yards',0) or 0),
                          int(log.get('targets',0) or 0)))
                
                total_logs += 1
            
            total_players += 1
        
        conn.commit()
        print(f"  Seeded {total_players} players, {total_logs} game logs")
    
    conn.close()
    print(f"\nDone. Total: {total_players} player-seasons, {total_logs} game logs")
    print("Now run: python run_backtest.py --quick")

if __name__ == "__main__":
    seed_from_nflverse()
