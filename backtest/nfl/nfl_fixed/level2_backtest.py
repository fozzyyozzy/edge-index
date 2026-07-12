import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Level 2 Backtest — True Out-of-Sample Validation
Train: 2023 game logs (streak warm-up only)
Test:  2024 season with real DK/FD/BetMGM lines
Result: No hand-seeded data, no lookahead bias
"""
import sys, os, sqlite3
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_setup import get_conn
from backtester import calc_streak, calc_hit_rate, calc_model_prob

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")

def run_level2():
    conn = get_conn()

    # Load only nflverse game logs (2023 + 2024) — no hand-seeded 2025
    logs_df = pd.read_sql("""
        SELECT gl.player_id, gl.season, gl.week,
               gl.pass_yds, gl.pass_att, gl.rush_yds, gl.rush_att,
               gl.receptions, gl.rec_yds, gl.targets,
               p.name, p.position
        FROM game_logs gl
        JOIN players p ON gl.player_id = p.id
        WHERE gl.season IN (2023, 2024)
        ORDER BY p.name, gl.season, gl.week
    """, conn)

    # Load only 2024 real prop lines
    raw_lines = pd.read_sql("""
        SELECT p.name as prop_name,
               pl.season, pl.week, pl.prop_type, pl.direction,
               CAST(pl.line AS REAL) as line,
               CAST(pl.odds AS INTEGER) as odds,
               pl.source
        FROM prop_lines pl
        JOIN players p ON pl.player_id = p.id
        WHERE pl.source LIKE 'actual%'
        AND pl.season = 2024
    """, conn)
    conn.close()

    # Name-match lines to game log players
    log_players = logs_df[['player_id','name','position']].drop_duplicates('player_id')
    raw_lines['key'] = raw_lines['prop_name'].str.lower().str.strip()
    log_players = log_players.copy()
    log_players['key'] = log_players['name'].str.lower().str.strip()
    lines_df = raw_lines.merge(log_players, on='key', how='inner')
    
    # Deduplicate — each player/week/prop should have ONE direction
    # Keep OVER only (model evaluates against OVER line)
    lines_df = lines_df[lines_df['direction']=='OVER'].copy()
    lines_df = lines_df.drop_duplicates(
        subset=['player_id','season','week','prop_type']
    ).reset_index(drop=True)

    print(f"Level 2 Backtest — 2024 season only, 2023 warm-up")
    print(f"Game logs: {len(logs_df):,} ({logs_df['season'].value_counts().to_dict()})")
    print(f"Prop lines: {len(lines_df):,} across {lines_df['player_id'].nunique()} players")
    print(f"Running...\n")

    STAT_MAP = {
        'pass_yds':'pass_yds', 'pass_att':'pass_att',
        'rush_yds':'rush_yds', 'rush_att':'rush_att',
        'receptions':'receptions', 'rec_yds':'rec_yds',
    }

    results = []
    players_df = log_players.copy()

    for player in players_df.itertuples():
        pid   = player.player_id
        pname = player.name
        pos   = player.position

        player_logs  = logs_df[logs_df['player_id']==pid].sort_values(['season','week']).reset_index(drop=True)
        player_lines = lines_df[lines_df['player_id']==pid]

        if len(player_logs) < 4 or player_lines.empty:
            continue

        for _, line_row in player_lines.iterrows():
            season    = int(line_row['season'])
            week      = int(line_row['week'])
            prop_type = line_row['prop_type']
            direction = line_row['direction']
            line      = float(line_row['line'])
            odds      = int(line_row['odds']) if pd.notna(line_row['odds']) else -110

            # Only use PRIOR data (2023 + prior 2024 weeks)
            prior_mask = (
                (player_logs['season'] < season) |
                ((player_logs['season'] == season) & (player_logs['week'] < week))
            )
            prior_logs = player_logs[prior_mask]
            if len(prior_logs) < 3:
                continue

            stat_col = STAT_MAP.get(prop_type)
            if not stat_col or stat_col not in prior_logs.columns:
                continue

            prior_values = prior_logs[stat_col].dropna().tolist()
            if len(prior_values) < 3:
                continue

            # Get actual result from 2024 game logs
            actual_row = player_logs[
                (player_logs['season']==season) &
                (player_logs['week']==week)
            ]
            if actual_row.empty or pd.isna(actual_row.iloc[0][stat_col]):
                continue
            actual_value = float(actual_row.iloc[0][stat_col])

            streak    = calc_streak(prior_values, line, direction)
            l6_rate   = calc_hit_rate(prior_values, line, direction, 6)
            l10_rate  = calc_hit_rate(prior_values, line, direction, 10)
            prior_avg = np.mean(prior_values[-6:]) if prior_values else 0
            floor_gap = prior_avg - line if direction=='OVER' else line - prior_avg

            model_prob = calc_model_prob(l6_rate, l10_rate, streak, floor_gap, odds, direction, prop_type)

            if model_prob >= 0.85 and streak >= 8:
                tier = 'AUTO'
            elif model_prob >= 0.65:
                tier = 'T1'
            elif model_prob >= 0.55:
                tier = 'T2'
            else:
                tier = 'T3'

            hit = (actual_value >= line) if direction=='OVER' else (actual_value <= line)

            if odds < 0:
                wager = 100
                pnl   = (100/abs(odds)*100) if hit else -100
            else:
                wager = 100
                pnl   = odds if hit else -100

            results.append({
                'player': pname, 'position': pos,
                'season': season, 'week': week,
                'prop_type': prop_type, 'direction': direction,
                'line': line, 'odds': odds,
                'actual': actual_value, 'hit': int(hit),
                'streak': streak, 'l6_rate': l6_rate,
                'model_prob': round(model_prob,3),
                'tier': tier, 'pnl': round(pnl,2),
            })

    df = pd.DataFrame(results)
    if df.empty:
        print("No results generated.")
        return

    total = len(df)
    wins  = df['hit'].sum()
    rate  = wins/total

    print("="*65)
    print("LEVEL 2 BACKTEST — 2024 REAL DATA ONLY")
    print("Train: 2023 nflverse | Test: 2024 DK/FD/BetMGM lines")
    print("="*65)
    print(f"\nTotal plays: {total:,}")
    print(f"Hit rate:    {rate*100:.1f}% ({wins}/{total})")
    print(f"P&L:         ${df['pnl'].sum():,.0f}")
    print(f"Edge:        +{(rate-0.524)*100:.1f}% above break-even\n")

    print(f"{'─'*65}")
    print(f"BY TIER")
    print(f"{'─'*65}")
    for tier in ['AUTO','T1','T2','T3']:
        t = df[df['tier']==tier]
        if t.empty: continue
        tr = t['hit'].sum()/len(t)
        print(f"{tier:<6} {len(t):>6} plays  {tr*100:>6.1f}%  ${t['pnl'].sum():>10,.0f}")

    print(f"\n{'─'*65}")
    print(f"AUTO + T1 COMBINED")
    print(f"{'─'*65}")
    act = df[df['tier'].isin(['AUTO','T1'])]
    ar  = act['hit'].sum()/len(act)
    print(f"Plays: {len(act):,}  Hit rate: {ar*100:.1f}%  P&L: ${act['pnl'].sum():,.0f}")

    print(f"\n{'─'*65}")
    print(f"BY STREAK")
    print(f"{'─'*65}")
    for label, mask in [
        ('0-2',  df['streak']<=2),
        ('3-5',  (df['streak']>=3)&(df['streak']<=5)),
        ('6-9',  (df['streak']>=6)&(df['streak']<=9)),
        ('10+',  df['streak']>=10),
    ]:
        s = df[mask]
        if s.empty: continue
        sr = s['hit'].sum()/len(s)
        print(f"Streak {label:<4} {len(s):>6} plays  {sr*100:>6.1f}%  ${s['pnl'].sum():>10,.0f}")

    print(f"\n{'─'*65}")
    print(f"BY WEEK (2024)")
    print(f"{'─'*65}")
    for week in sorted(df['week'].unique()):
        w = df[df['week']==week]
        wr = w['hit'].sum()/len(w)
        flag = "🔥" if wr>=0.65 else "✓" if wr>=0.55 else "⚠" if wr>=0.524 else "✗"
        print(f"Wk {week:<3} {len(w):>5} plays  {wr*100:>5.1f}%  ${w['pnl'].sum():>9,.0f}  {flag}")

    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
              'level2_results.csv'), index=False)
    print(f"\nSaved to level2_results.csv")

if __name__ == "__main__":
    run_level2()
