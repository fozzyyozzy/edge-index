"""
Run this from: C:\Users\tyose\edge-index\backtest\
It fixes all import paths in the nfl\ subfolder.
"""
import os, sys

NFL_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nfl")
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared")
DB_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")

REPLACEMENTS = [
    # db_setup import → point to shared folder
    (
        'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom db_setup import get_conn',
        'sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared"))\nfrom db_setup import get_conn'
    ),
    (
        "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom db_setup import get_conn",
        "sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))\nfrom db_setup import get_conn"
    ),
    # DB path references
    (
        'DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")',
        'DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "edge_index.db")'
    ),
    (
        "DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edge_index.db')",
        "DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'edge_index.db')"
    ),
    # backtester imports within nfl folder
    (
        'from backtester import calc_streak, calc_hit_rate, calc_model_prob',
        'from backtester import calc_streak, calc_hit_rate, calc_model_prob'
    ),
    # live_schedule import in weekly_pipeline
    (
        'from live_schedule import demo_games',
        'from live_schedule import demo_games'
    ),
]

fixed = []
skipped = []

for fname in os.listdir(NFL_DIR):
    if not fname.endswith('.py'):
        continue

    path = os.path.join(NFL_DIR, fname)
    with open(path, encoding='utf-8') as f:
        original = f.read()

    updated = original
    for old, new in REPLACEMENTS:
        if old in updated:
            updated = updated.replace(old, new)

    if updated != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated)
        fixed.append(fname)
    else:
        skipped.append(fname)

print(f"Fixed imports in {len(fixed)} files:")
for f in fixed:
    print(f"  ✓ {f}")

print(f"\nNo changes needed in {len(skipped)} files:")
for f in skipped:
    print(f"  - {f}")

# Also fix db_setup.py to point DB path one level up
db_setup_path = os.path.join(SHARED_DIR, "db_setup.py")
if os.path.exists(db_setup_path):
    with open(db_setup_path, encoding='utf-8') as f:
        c = f.read()
    
    c_new = c.replace(
        'os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_index.db")',
        'os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "edge_index.db")'
    ).replace(
        "os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edge_index.db')",
        "os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'edge_index.db')"
    )
    
    if c_new != c:
        with open(db_setup_path, 'w', encoding='utf-8') as f:
            f.write(c_new)
        print(f"\n✓ Fixed db_setup.py DB path")
    else:
        print(f"\n- db_setup.py DB path already correct or uses different format")
        print(f"  Check manually: {db_setup_path}")

print("\nDone. Test with:")
print("  cd nfl")
print("  python run_backtest.py --quick")
