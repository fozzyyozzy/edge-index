import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'shared'))
"""
Build realistic alt-line anchors from historical DK/FD/BetMGM data.
Instead of scanning arbitrary thresholds, use what books actually posted.

Output: alt_line_anchors.json
  {
    "player_name": {
      "prop_type": {
        "lines": [3.5, 4.5, 5.5, 6.5],
        "avg_line": 4.7,
        "low_line": 3.5,
        "high_line": 6.5,
        "n_samples": 120
      }
    }
  }
"""
import sys, os, sqlite3, json
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_setup import get_conn

def build_anchors(season=2025, min_samples=5):
    """
    Pull all posted alt-lines from historical data.
    Use the distribution of posted lines as realistic thresholds.
    """
    conn = get_conn()

    # Pull all real lines with player names
    lines = pd.read_sql(f"""
        SELECT p.name, p.position,
               pl.prop_type, pl.line, pl.direction,
               pl.season, pl.week, pl.source
        FROM prop_lines pl
        JOIN players p ON pl.player_id = p.id
        WHERE pl.source LIKE 'actual%'
        AND pl.season = {season}
        AND pl.direction = 'OVER'
        ORDER BY p.name, pl.prop_type, pl.line
    """, conn)
    conn.close()

    print(f"Loaded {len(lines):,} prop lines from {season} season")
    print(f"Players: {lines['name'].nunique()}")
    print(f"Prop types: {lines['prop_type'].unique()}")

    anchors = {}

    for (name, pos, prop), group in lines.groupby(['name','position','prop_type']):
        posted_lines = sorted(group['line'].unique().tolist())
        n = len(group)

        if n < min_samples:
            continue

        # Get the distribution of posted lines
        # Round to nearest 0.5 to normalize across books
        rounded = [round(l * 2) / 2 for l in posted_lines]
        unique_rounded = sorted(set(rounded))

        # Find the most commonly posted line (the "main" line)
        line_counts = group['line'].value_counts()
        main_line   = round(line_counts.index[0] * 2) / 2

        # Define realistic alt-line set:
        # Start 2 steps below main line, go 3 steps above
        step = 0.5
        if prop in ('pass_yds', 'rec_yds', 'rush_yds'):
            step = 5.0 if prop == 'pass_yds' else 2.5

        alt_set = sorted(set(
            [round((main_line + i * step) * 2) / 2
             for i in range(-3, 5)]
        ))

        # Only include lines that make sense for the prop
        min_floor = {
            'pass_yds': 150, 'rush_yds': 15, 'rec_yds': 15,
            'receptions': 2, 'targets': 2, 'pass_att': 15,
        }.get(prop, 0)

        alt_set = [l for l in alt_set if l >= min_floor]

        if name not in anchors:
            anchors[name] = {"position": pos, "props": {}}

        anchors[name]["props"][prop] = {
            "lines":      alt_set,
            "main_line":  main_line,
            "low_line":   min(posted_lines),
            "high_line":  max(posted_lines),
            "avg_line":   round(float(group['line'].mean()), 2),
            "n_samples":  n,
            "posted_unique": unique_rounded,
        }

    print(f"\nBuilt anchors for {len(anchors)} players")
    return anchors

def print_sample(anchors, n=5):
    """Show sample anchors for key players."""
    sample_players = [
        "Travis Kelce", "Saquon Barkley", "Ja'Marr Chase",
        "Lamar Jackson", "Patrick Mahomes"
    ]
    print(f"\n{'='*65}")
    print("SAMPLE ALT-LINE ANCHORS")
    print(f"{'='*65}")

    for player in sample_players:
        if player not in anchors:
            continue
        data = anchors[player]
        print(f"\n{player} ({data['position']}):")
        for prop, pdata in data["props"].items():
            print(f"  {prop}:")
            print(f"    Main line:    {pdata['main_line']}")
            print(f"    Alt range:    {pdata['lines']}")
            print(f"    Books posted: {pdata['posted_unique']}")
            print(f"    Avg posted:   {pdata['avg_line']}")

if __name__ == "__main__":
    print("Building alt-line anchors from 2024-2025 historical data...")

    # Build from 2025 first, fall back to 2024
    anchors_2025 = build_anchors(season=2025)
    anchors_2024 = build_anchors(season=2024)

    # Merge — 2025 takes priority, fill gaps with 2024
    merged = {}
    all_players = set(anchors_2025.keys()) | set(anchors_2024.keys())

    for player in all_players:
        if player in anchors_2025:
            merged[player] = anchors_2025[player]
            # Fill missing props from 2024
            if player in anchors_2024:
                for prop, data in anchors_2024[player]["props"].items():
                    if prop not in merged[player]["props"]:
                        merged[player]["props"][prop] = data
        else:
            merged[player] = anchors_2024[player]

    print(f"\nFinal anchor set: {len(merged)} players")

    # Save
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "alt_line_anchors.json")
    with open(out_path, 'w') as f:
        json.dump(merged, f, indent=2)
    print(f"Saved to alt_line_anchors.json")

    print_sample(merged)
