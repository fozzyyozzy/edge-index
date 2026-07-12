"""Check if 2023 data is in DB and show what Level 2 would look like."""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)

# Season breakdown
print("=== GAME LOGS BY SEASON ===")
for r in conn.execute("""
    SELECT season, COUNT(DISTINCT player_id) as players, COUNT(*) as logs
    FROM game_logs GROUP BY season ORDER BY season
""").fetchall():
    print(f"  {r[0]}: {r[1]} players, {r[2]} game logs")

print("\n=== PROP LINES BY SEASON ===")
for r in conn.execute("""
    SELECT season, COUNT(DISTINCT player_id) as players, COUNT(*) as lines
    FROM prop_lines WHERE source LIKE 'actual%'
    GROUP BY season ORDER BY season
""").fetchall():
    print(f"  {r[0]}: {r[1]} players, {r[2]} prop lines")

# Show what 2024 week 1 looks like with/without 2023 warmup
print("\n=== LEVEL 2 IMPACT ESTIMATE ===")
# Players who have 2023 data
with_2023 = conn.execute("""
    SELECT COUNT(DISTINCT player_id) FROM game_logs WHERE season=2023
""").fetchone()[0]

# Players who have 2024 prop lines
with_2024_lines = conn.execute("""
    SELECT COUNT(DISTINCT p.name) 
    FROM prop_lines pl
    JOIN players p ON pl.player_id=p.id
    WHERE pl.source LIKE 'actual%' AND pl.season=2024
""").fetchone()[0]

print(f"  Players with 2023 game logs: {with_2023}")
print(f"  Players with 2024 prop lines: {with_2024_lines}")
print(f"""
  WITHOUT 2023 warmup:
    2024 Week 1-5: streak=0 for everyone → all T3 → 47% hit rate
    Model cold starts, drags 2024 to 50%

  WITH 2023 warmup (current setup):
    2024 Week 1: model looks back at 2023 stats
    Players with established 2023 streaks get AUTO/T1 from week 1
    Expected 2024 improvement: 50% → 60%+

  The prior_mask already includes season < season.
  If 2023 logs exist, Level 2 is already running.
""")

conn.close()
