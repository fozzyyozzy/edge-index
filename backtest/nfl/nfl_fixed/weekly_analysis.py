"""
Week-by-week hit rate analysis.
Shows how model performance evolves across the season.
"""
import sys, os, sqlite3
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)

df = pd.read_sql("""
    SELECT season, week, tier, hit, pnl
    FROM backtest_results
    ORDER BY season, week
""", conn)
conn.close()

print("=" * 65)
print("WEEK-BY-WEEK HIT RATE ANALYSIS")
print("=" * 65)

for season in [2024, 2025]:
    s = df[df['season'] == season]
    print(f"\n{'─'*65}")
    print(f"SEASON {season}")
    print(f"{'─'*65}")
    print(f"{'Week':<6} {'Plays':>6} {'Hit%':>7} {'AUTO%':>8} {'P&L':>10}  Verdict")
    print(f"{'─'*65}")

    for week in sorted(s['week'].unique()):
        w = s[s['week'] == week]
        auto = w[w['tier'] == 'AUTO']
        plays = len(w)
        hits  = w['hit'].sum()
        rate  = hits/plays*100 if plays > 0 else 0
        auto_rate = auto['hit'].sum()/len(auto)*100 if len(auto) > 0 else 0
        pnl   = w['pnl'].sum()
        verdict = "🔥" if rate >= 65 else "✓" if rate >= 55 else "⚠" if rate >= 52.4 else "✗"
        print(f"Wk {week:<3} {plays:>6} {rate:>6.1f}% {auto_rate:>7.1f}% ${pnl:>8,.0f}  {verdict}")

    # Summary
    auto_all = s[s['tier']=='AUTO']
    print(f"{'─'*65}")
    print(f"{'TOTAL':<6} {len(s):>6} {s['hit'].sum()/len(s)*100:>6.1f}% "
          f"{auto_all['hit'].sum()/len(auto_all)*100 if len(auto_all)>0 else 0:>7.1f}% "
          f"${s['pnl'].sum():>8,.0f}")

# Early vs late season split
print(f"\n{'='*65}")
print("EARLY vs LATE SEASON — 2024")
print(f"{'='*65}")
s24 = df[df['season']==2024]
early = s24[s24['week'] <= 9]
late  = s24[s24['week'] >= 10]
print(f"Weeks 1-9:   {early['hit'].sum()/len(early)*100:.1f}% hit rate on {len(early):,} plays  ${early['pnl'].sum():,.0f}")
print(f"Weeks 10-18: {late['hit'].sum()/len(late)*100:.1f}% hit rate on {len(late):,} plays  ${late['pnl'].sum():,.0f}")

# AUTO plays by week group
print(f"\n{'='*65}")
print("AUTO PLAYS — WEEK GROUPS")
print(f"{'='*65}")
auto = df[df['tier']=='AUTO']
for season in [2024, 2025]:
    sa = auto[auto['season']==season]
    early_a = sa[sa['week']<=9]
    late_a  = sa[sa['week']>=10]
    print(f"\n{season}:")
    if len(early_a) > 0:
        print(f"  Wks 1-9:   {early_a['hit'].sum()/len(early_a)*100:.1f}% on {len(early_a):,} AUTO plays")
    if len(late_a) > 0:
        print(f"  Wks 10-18: {late_a['hit'].sum()/len(late_a)*100:.1f}% on {len(late_a):,} AUTO plays")
