"""
Full diagnostic and fix in one script.
Shows exact ID ranges and fixes the mismatch directly.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Show exact ID ranges
print("=== ID RANGES ===")
gl_ids = [r[0] for r in conn.execute("SELECT DISTINCT player_id FROM game_logs").fetchall()]
pl_ids = [r[0] for r in conn.execute("SELECT DISTINCT player_id FROM prop_lines WHERE source LIKE 'actual%'").fetchall()]
p_ids  = [r[0] for r in conn.execute("SELECT id FROM players").fetchall()]

print(f"Game log IDs:  min={min(gl_ids)} max={max(gl_ids)} count={len(gl_ids)}")
print(f"Prop line IDs: min={min(pl_ids)} max={max(pl_ids)} count={len(pl_ids)}")
print(f"Players IDs:   min={min(p_ids)}  max={max(p_ids)}  count={len(p_ids)}")
print(f"Overlap game_logs ∩ prop_lines: {len(set(gl_ids) & set(pl_ids))}")

# Show sample names for each
print("\n=== SAMPLE GAME LOG PLAYER NAMES ===")
for pid in sorted(gl_ids)[:5]:
    r = conn.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
    print(f"  id={pid} name={r[0] if r else 'NOT FOUND'}")

print("\n=== SAMPLE PROP LINE PLAYER NAMES ===")
for pid in sorted(pl_ids)[:5]:
    r = conn.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
    print(f"  id={pid} name={r[0] if r else 'NOT FOUND'}")

# THE FIX: update game_logs to use prop_line player IDs via name matching
print("\n=== APPLYING FIX: Align game_log IDs to prop_line IDs via name ===")

# Build name -> prop_line_player_id map
prop_name_map = {}
for pid in pl_ids:
    r = conn.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
    if r:
        prop_name_map[r[0].lower().strip()] = pid

print(f"Prop line name map built: {len(prop_name_map)} entries")
print(f"Sample: {list(prop_name_map.items())[:3]}")

# Update game_logs player_ids to match prop_lines
updated = 0
not_found = []
for gl_pid in gl_ids:
    r = conn.execute("SELECT name FROM players WHERE id=?", (gl_pid,)).fetchone()
    if not r:
        continue
    name = r[0].lower().strip()
    new_pid = prop_name_map.get(name)
    if not new_pid:
        # try last name
        last = name.split()[-1]
        new_pid = prop_name_map.get(last)
    if new_pid and new_pid != gl_pid:
        cursor.execute(
            "UPDATE game_logs SET player_id=? WHERE player_id=?",
            (new_pid, gl_pid)
        )
        updated += cursor.rowcount
    elif not new_pid:
        not_found.append(r[0])

conn.commit()
print(f"Updated {updated} game log rows")
if not_found:
    print(f"Not matched: {not_found[:10]}")

# Verify
overlap = conn.execute("""
    SELECT COUNT(DISTINCT gl.player_id)
    FROM game_logs gl
    WHERE gl.player_id IN (
        SELECT DISTINCT player_id FROM prop_lines WHERE source LIKE 'actual%'
    )
""").fetchone()[0]
print(f"\nOverlap after fix: {overlap} players")
if overlap > 0:
    print("✓ Run: python run_backtest.py --quick")
else:
    print("✗ Still no overlap — prop lines may not have player names in DB")
    print("Sample prop line player IDs and their DB names:")
    for pid in sorted(pl_ids)[:10]:
        r = conn.execute("SELECT name FROM players WHERE id=?", (pid,)).fetchone()
        print(f"  id={pid} → {r[0] if r else 'NO NAME IN DB'}")

conn.close()
