"""
Fix remaining abbreviated and mismatched player names.
Run after nflverse_loader.py to align all names with odds API format.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Step 1: Additional name mappings for still-missing players
EXTRA_MAP = {
    "B.Cooks":       "Brandin Cooks",
    "C.Brown":       "Chase Brown",
    "C.Hubbard":     "Chuba Hubbard",
    "C.Kupp":        "Cooper Kupp",
    "D.Douglas":     "Darius Douglas",
    "D.Hopkins":     "DeAndre Hopkins",
    "D.Mooney":      "Darnell Mooney",
    "D.Singletary":  "Devin Singletary",
    "E.Moore":       "Elijah Moore",
    "G.Conner":      "James Conner",
    "J.Conner":      "James Conner",
    "J.Smith-Njigba":"Jaxon Smith-Njigba",
    "J.Meyers":      "Jakobi Meyers",
    "J.Dotson":      "Jahan Dotson",
    "J.Palmer":      "Joshua Palmer",
    "K.Johnson":     "Kalif Raymond",
    "M.Jones":       "Mac Jones",
    "M.Williams":    "Mike Williams",
    "N.Agholor":     "Nelson Agholor",
    "P.Campbell":    "Parris Campbell",
    "R.White":       "Rachaad White",
    "S.Moore":       "Skyy Moore",
    "T.Boyd":        "Tyler Boyd",
    "T.Hill":        "Taysom Hill",
    "T.Patrick":     "Tim Patrick",
    "Z.Ertz":        "Zach Ertz",
    "D.London":      "Drake London",
    "C.Kirk":        "Christian Kirk",
    "G.Everett":     "Gerald Everett",
    "H.Henry":       "Hunter Henry",
    "J.Smith":       "Jonnu Smith",
    "D.Schultz":     "Dalton Schultz",
    "I.Thomas":      "Isaiah Thomas",
    "A.Shaheen":     "Adam Shaheen",
    "C.Tremble":     "Tommy Tremble",
    "J.Whitle":      "Jordan Whitle",
    "D.Waller":      "Darren Waller",
    "T.Hockenson":   "T.J. Hockenson",
    "C.Otton":       "Cade Otton",
    "D.Kincaid":     "Dalton Kincaid",
    "B.Skowronek":   "Ben Skowronek",
    "C.Clayton":     "Chase Claypool",
    "T.Johnson":     "Tre'Quan Smith",
    "M.Hardman":     "Mecole Hardman",
    "J.Reagor":      "Jalen Reagor",
    "D.Njoku":       "David Njoku",
    "G.Dulcich":     "Greg Dulcich",
    "S.LaPorta":     "Sam LaPorta",
    "T.McBride":     "Trey McBride",
    "T.Kelce":       "Travis Kelce",
    "P.Freiermuth":  "Pat Freiermuth",
    "K.Pitts":       "Kyle Pitts",
    "J.Ferguson":    "Jake Ferguson",
    "E.Engram":      "Evan Engram",
    "M.Andrews":     "Mark Andrews",
    "T.Warren":      "Tyler Warren",
    "B.Bowers":      "Brock Bowers",
    "C.Kmet":        "Cole Kmet",
}

# Apply extra mappings
updated = 0
for abbrev, full in EXTRA_MAP.items():
    rows = conn.execute(
        "SELECT id FROM players WHERE name=?", (abbrev,)
    ).fetchall()
    for row in rows:
        pid = row[0]
        # Check if full name already exists
        existing = conn.execute(
            "SELECT id FROM players WHERE name=?", (full,)
        ).fetchone()
        if existing and existing[0] != pid:
            cursor.execute("UPDATE game_logs SET player_id=? WHERE player_id=?",
                          (existing[0], pid))
            cursor.execute("DELETE FROM players WHERE id=?", (pid,))
        else:
            cursor.execute("UPDATE players SET name=? WHERE id=?", (full, pid))
        updated += 1

conn.commit()
print(f"Step 1 — Fixed {updated} additional abbreviated names")

# Step 2: Fix known mismatches between nflverse and odds API
RENAME_MAP = {
    "Brian Thomas":     "Brian Thomas Jr.",
    "C.J. Stroud":      "CJ Stroud",
    "A.J. Brown":       "AJ Brown",
    "D.K. Metcalf":     "DK Metcalf",
    "D.J. Moore":       "DJ Moore",
    "D.J. Chark":       "DJ Chark",
    "T.J. Hockenson":   "TJ Hockenson",
    "K.J. Osborn":      "KJ Osborn",
    "Marvin Harrison":  "Marvin Harrison Jr.",
    "Michael Pittman":  "Michael Pittman Jr.",
    "Brian Thomas Jr.": "Brian Thomas Jr.",
}

fixed2 = 0
for wrong, correct in RENAME_MAP.items():
    rows = conn.execute(
        "SELECT id FROM players WHERE name=?", (wrong,)
    ).fetchall()
    for row in rows:
        pid = row[0]
        existing = conn.execute(
            "SELECT id FROM players WHERE name=?", (correct,)
        ).fetchone()
        if existing and existing[0] != pid:
            cursor.execute("UPDATE game_logs SET player_id=? WHERE player_id=?",
                          (existing[0], pid))
            cursor.execute("DELETE FROM players WHERE id=?", (pid,))
        else:
            cursor.execute("UPDATE players SET name=? WHERE id=?", (correct, pid))
        fixed2 += 1

conn.commit()
print(f"Step 2 — Fixed {fixed2} name format mismatches")

# Step 3: Check overlap now
overlap = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT lower(trim(p.name)) FROM game_logs gl
        JOIN players p ON gl.player_id = p.id
        INTERSECT
        SELECT lower(trim(p.name)) FROM prop_lines pl
        JOIN players p ON pl.player_id = p.id
        WHERE pl.source LIKE 'actual%'
    )
""").fetchone()[0]

total_log_players = conn.execute(
    "SELECT COUNT(DISTINCT player_id) FROM game_logs"
).fetchone()[0]

print(f"\nResult: {overlap} of {total_log_players} game log players now match prop lines")

# Show still-missing
still_missing = conn.execute("""
    SELECT DISTINCT p.name FROM game_logs gl
    JOIN players p ON gl.player_id = p.id
    WHERE lower(trim(p.name)) NOT IN (
        SELECT lower(trim(p2.name)) FROM prop_lines pl
        JOIN players p2 ON pl.player_id = p2.id
        WHERE pl.source LIKE 'actual%'
    )
    ORDER BY p.name LIMIT 20
""").fetchall()

if still_missing:
    print(f"\nStill unmatched (first 20):")
    for r in still_missing:
        print(f"  '{r[0]}'")

conn.close()
print("\nRun: python run_backtest.py --quick")
