import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)

print("=== PLAYERS TABLE (first 5) ===")
for r in conn.execute("SELECT id, name FROM players LIMIT 5").fetchall():
    print(f"  id={r[0]} name={r[1]}")

print("\n=== GAME LOGS player_ids (first 5) ===")
for r in conn.execute("SELECT DISTINCT player_id FROM game_logs LIMIT 5").fetchall():
    print(f"  player_id={r[0]}")

print("\n=== PROP LINES player_ids (first 5, actual only) ===")
for r in conn.execute("SELECT DISTINCT player_id FROM prop_lines WHERE source LIKE 'actual%' LIMIT 5").fetchall():
    print(f"  player_id={r[0]}")

print("\n=== NAME LOOKUP for prop line player_ids ===")
prop_ids = [r[0] for r in conn.execute(
    "SELECT DISTINCT player_id FROM prop_lines WHERE source LIKE 'actual%' LIMIT 10"
).fetchall()]
for pid in prop_ids:
    row = conn.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
    print(f"  prop player_id={pid} → name={row[0] if row else 'NOT FOUND'}")

print("\n=== NAME LOOKUP for game log player_ids ===")
log_ids = [r[0] for r in conn.execute(
    "SELECT DISTINCT player_id FROM game_logs LIMIT 10"
).fetchall()]
for pid in log_ids:
    row = conn.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
    print(f"  log  player_id={pid} → name={row[0] if row else 'NOT FOUND'}")

conn.close()
