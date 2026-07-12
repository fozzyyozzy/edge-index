"""
Check which nflverse players are missing prop lines.
Then pull ONLY those players from the odds API.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)

# Players with game logs
log_players = conn.execute("""
    SELECT DISTINCT p.id, p.name, p.position, p.team
    FROM game_logs gl
    JOIN players p ON gl.player_id = p.id
    ORDER BY p.position, p.name
""").fetchall()

# Players with real prop lines
line_players = set(r[0] for r in conn.execute("""
    SELECT DISTINCT pl.player_id
    FROM prop_lines pl
    JOIN players p ON pl.player_id = p.id
    WHERE pl.source LIKE 'actual%'
""").fetchall())

# Also check by name match
line_names = set(r[0].lower() for r in conn.execute("""
    SELECT DISTINCT p.name
    FROM prop_lines pl
    JOIN players p ON pl.player_id = p.id
    WHERE pl.source LIKE 'actual%'
""").fetchall())

print(f"Players with game logs: {len(log_players)}")
print(f"Players with prop lines (by ID): {len(line_players)}")
print(f"Players with prop lines (by name): {len(line_names)}")

missing = [(pid, name, pos, team) for pid, name, pos, team in log_players
           if name.lower() not in line_names]

print(f"\nMissing prop lines: {len(missing)}")
print(f"\nBy position:")
for pos in ['QB','RB','WR','TE']:
    pos_missing = [p for p in missing if p[2]==pos]
    print(f"  {pos}: {len(pos_missing)} missing")
    for pid, name, p, team in pos_missing[:5]:
        print(f"    {name} ({team})")
    if len(pos_missing) > 5:
        print(f"    ... and {len(pos_missing)-5} more")

conn.close()
print("\nTo pull lines for just these players, the odds loader")
print("needs to run again — it will add lines for new players")
print("while keeping existing lines intact (INSERT OR REPLACE).")
print("\nEstimated additional credits: ~158 players x 285 games / 32 teams")
print("= ~1,400 additional game-player pairs x 160 credits = ~224,000 credits")
