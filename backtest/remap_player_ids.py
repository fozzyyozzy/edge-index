"""
Fix: remap prop_lines player_ids using the saved CSV as the name→id bridge.
The CSV has player_name + player_id from when the odds loader ran.
We use that to build old_id → name → current_id mapping.
"""
import sys, os, sqlite3
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_results.csv")

# Try expanded CSV first, fall back to original
if not os.path.exists(CSV_PATH):
    CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "backtest_results_expanded.csv")

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ── Step 1: Load CSV to get old_id → name mapping ────────────────────────────
print(f"Loading CSV: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)
print(f"  {len(df):,} rows, columns: {list(df.columns)}")

if 'player_id' not in df.columns or 'player_name' not in df.columns:
    print("ERROR: CSV missing player_id or player_name column")
    sys.exit(1)

# Build old_id → name from CSV
csv_map = {}
for _, row in df.drop_duplicates('player_id').iterrows():
    csv_map[int(row['player_id'])] = str(row['player_name'])

print(f"  Old IDs in CSV: {len(csv_map)}")

# ── Step 2: Get current player IDs from DB ────────────────────────────────────
current = {}
for pid, name in conn.execute("SELECT id, name FROM players").fetchall():
    current[name.lower().strip()] = pid
    current[name.split()[-1].lower()] = pid
    clean = name.lower()
    for s in [" jr.", " sr.", " ii", " iii", " iv"]:
        clean = clean.replace(s, "")
    current[clean.strip()] = pid

print(f"  Current players in DB: {len(set(current.values()))}")

# ── Step 3: Check prop_lines IDs ─────────────────────────────────────────────
prop_ids = [r[0] for r in conn.execute(
    "SELECT DISTINCT player_id FROM prop_lines WHERE source LIKE 'actual%'"
).fetchall()]
print(f"\nDistinct player_ids in prop_lines: {len(prop_ids)}")
print(f"Prop IDs sample: {sorted(prop_ids)[:10]}")
print(f"CSV IDs sample:  {sorted(csv_map.keys())[:10]}")
print(f"DB IDs sample:   {sorted(set(current.values()))[:10]}")

# ── Step 4: Build remap table ─────────────────────────────────────────────────
remap = {}  # old_prop_id → new_db_id
no_match = []

for prop_id in prop_ids:
    # Does this prop_id exist in the CSV?
    name = csv_map.get(prop_id)
    if name:
        new_id = (current.get(name.lower().strip()) or
                  current.get(name.split()[-1].lower()))
        if new_id:
            remap[prop_id] = new_id
        else:
            no_match.append((prop_id, name, "not in current players"))
    else:
        # Prop ID not in CSV — check if it's already a current DB id
        row = conn.execute("SELECT name FROM players WHERE id=?", (prop_id,)).fetchone()
        if row:
            remap[prop_id] = prop_id  # already correct
        else:
            no_match.append((prop_id, "?", "not in CSV or DB"))

print(f"\nCan remap: {len(remap)}")
print(f"No match:  {len(no_match)}")
if no_match[:5]:
    print("  Sample no-match:", no_match[:5])

# ── Step 5: Apply remap ───────────────────────────────────────────────────────
if not remap:
    print("\nNo remapping possible.")
    print("The prop_lines were stored with IDs that exist in neither")
    print("the current DB nor the CSV. A fresh pull is needed:")
    print("  python odds_api_loader.py --seasons 2024 2025")
    conn.close()
    sys.exit(0)

print(f"\nApplying {len(remap)} ID remappings...")
total_updated = 0
for old_id, new_id in remap.items():
    if old_id == new_id:
        continue
    cursor.execute(
        "UPDATE prop_lines SET player_id=? WHERE player_id=?",
        (new_id, old_id)
    )
    total_updated += cursor.rowcount

conn.commit()
print(f"Updated {total_updated:,} prop line rows")

# ── Step 6: Verify ────────────────────────────────────────────────────────────
matched = conn.execute("""
    SELECT COUNT(*) FROM prop_lines pl
    JOIN players p ON pl.player_id = p.id
    WHERE pl.source LIKE 'actual%'
""").fetchone()[0]
total = conn.execute(
    "SELECT COUNT(*) FROM prop_lines WHERE source LIKE 'actual%'"
).fetchone()[0]

print(f"\nVerification:")
print(f"  Total real lines:   {total:,}")
print(f"  Lines with match:   {matched:,}")
print(f"  Match rate:         {matched/total*100:.1f}%" if total > 0 else "  N/A")

if matched > 0:
    print("\n✓ Remap successful! Now run:")
    print("  python run_backtest.py --quick")
else:
    print("\n✗ Still no matches.")
    print("CSV player_ids and prop_lines player_ids don't overlap.")
    print("Fresh pull required: python odds_api_loader.py --seasons 2024 2025")

conn.close()
