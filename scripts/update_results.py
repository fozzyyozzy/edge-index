"""
EDGE INDEX — Results Tracker
==============================
Run every Monday by GitHub Actions to update the public results CSV.
You manually enter the actual outcomes — this script calculates ROI,
ATS record, and formats the public-facing results table.

Usage:
    python scripts/update_results.py --results-file results/results_tracker.csv

The CSV format (add rows manually each Monday):
    week, season, player_or_game, stat, direction, line, projection,
    actual, result (W/L/P), edge_pct, tier, notes
"""

import argparse
import csv
import json
from pathlib import Path
from datetime import date


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

RESULTS_TEMPLATE = [
    "week", "season", "date", "type", "player_or_game", "stat_or_side",
    "direction", "line", "projection", "edge_pct", "tier",
    "actual", "result", "units", "notes"
]


def initialize_results_file(path: Path) -> None:
    """Create results CSV with headers if it doesn't exist."""
    if not path.exists():
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=RESULTS_TEMPLATE)
            writer.writeheader()
        print(f"[init] Created results file: {path}")


def calculate_summary(path: Path) -> dict:
    """Calculate running performance stats from results CSV."""
    if not path.exists():
        return {}

    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("result") in ("W", "L", "P")]

    if not rows:
        return {"message": "No completed results yet"}

    wins   = sum(1 for r in rows if r["result"] == "W")
    losses = sum(1 for r in rows if r["result"] == "L")
    pushes = sum(1 for r in rows if r["result"] == "P")
    total  = wins + losses

    win_pct = (wins / total * 100) if total > 0 else 0

    # By tier
    t1_rows = [r for r in rows if r.get("tier") == "1" and r["result"] != "P"]
    t2_rows = [r for r in rows if r.get("tier") == "2" and r["result"] != "P"]

    t1_wins = sum(1 for r in t1_rows if r["result"] == "W")
    t2_wins = sum(1 for r in t2_rows if r["result"] == "W")

    # Units (assume -110 standard vig, 1 unit per play)
    try:
        net_units = sum(
            0.909 if r["result"] == "W" else
            -1.0  if r["result"] == "L" else
            0.0
            for r in rows
        )
    except Exception:
        net_units = 0

    # By week
    weeks = {}
    for r in rows:
        w = r.get("week", "?")
        if w not in weeks:
            weeks[w] = {"W": 0, "L": 0, "P": 0}
        weeks[w][r["result"]] += 1

    summary = {
        "overall":    f"{wins}-{losses}-{pushes}",
        "win_pct":    round(win_pct, 1),
        "net_units":  round(net_units, 2),
        "roi_pct":    round(net_units / max(total, 1) * 100, 1),
        "tier1":      f"{t1_wins}-{len(t1_rows)-t1_wins}" if t1_rows else "0-0",
        "tier2":      f"{t2_wins}-{len(t2_rows)-t2_wins}" if t2_rows else "0-0",
        "by_week":    weeks,
        "last_updated": date.today().isoformat(),
    }
    return summary


def generate_public_markdown(summary: dict, path: Path) -> str:
    """Generate public-facing results markdown for posting."""
    if not summary or "message" in summary:
        return "No results to display yet."

    lines = [
        "## Edge Index — Season Record",
        "",
        f"**Overall:** {summary['overall']} · Win%: {summary['win_pct']}% · "
        f"Net units: {summary['net_units']:+.1f} · ROI: {summary['roi_pct']:+.1f}%",
        "",
        f"**Tier 1 (★★★):** {summary['tier1']}",
        f"**Tier 2 (★★):** {summary['tier2']}",
        "",
        "| Week | W | L | P |",
        "|------|---|---|---|",
    ]

    for week, rec in sorted(summary.get("by_week", {}).items(),
                             key=lambda x: int(x[0]) if str(x[0]).isdigit() else 99):
        lines.append(f"| {week} | {rec['W']} | {rec['L']} | {rec['P']} |")

    lines += [
        "",
        f"*Last updated: {summary['last_updated']}*",
        "*All results posted publicly — no cherry-picking.*"
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-file", default="results/results_tracker.csv")
    args = parser.parse_args()

    results_path = Path(args.results_file)
    initialize_results_file(results_path)

    summary = calculate_summary(results_path)
    print(f"\nResults summary:\n{json.dumps(summary, indent=2)}")

    if summary and "message" not in summary:
        md = generate_public_markdown(summary, results_path)
        md_path = RESULTS_DIR / "public_record.md"
        md_path.write_text(md)
        print(f"\n[output] Public record → {md_path}")
        print(f"\n{md}")

        # Also save JSON for future dashboard
        json_path = RESULTS_DIR / "summary.json"
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
