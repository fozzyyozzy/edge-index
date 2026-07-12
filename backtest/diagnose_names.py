import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)

# What names do the prop lines actually have?
print("=== PROP LINE PLAYER NAMES (all unique, sample 30) ===")
prop_names = [r[0] for r in conn.execute("""
    SELECT DISTINCT p.name FROM prop_lines pl
    JOIN players p ON pl.player_id = p.id
    WHERE pl.source LIKE 'actual%'
    ORDER BY p.name
""").fetchall()]
print(f"Total unique names in prop lines: {len(prop_names)}")
for n in prop_names[:30]:
    print(f"  '{n}'")

print("\n=== GAME LOG PLAYER NAMES (all, sample 30) ===")
log_names = [r[0] for r in conn.execute("""
    SELECT DISTINCT p.name FROM game_logs gl
    JOIN players p ON gl.player_id = p.id
    ORDER BY p.name
""").fetchall()]
print(f"Total unique names in game logs: {len(log_names)}")
for n in log_names[:30]:
    print(f"  '{n}'")

# Find prop line names that AREN'T in game logs
prop_set = set(n.lower().strip() for n in prop_names)
log_set  = set(n.lower().strip() for n in log_names)

in_props_not_logs = sorted(prop_set - log_set)
in_logs_not_props = sorted(log_set - prop_set)

print(f"\n=== IN PROP LINES BUT NOT GAME LOGS ({len(in_props_not_logs)}) ===")
for n in in_props_not_logs[:20]:
    print(f"  '{n}'")

print(f"\n=== IN GAME LOGS BUT NOT PROP LINES ({len(in_logs_not_props)}) ===")
for n in in_logs_not_props[:20]:
    print(f"  '{n}'")

conn.close()
