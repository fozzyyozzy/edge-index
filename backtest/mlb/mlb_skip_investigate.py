"""
SKIP INVESTIGATION
==================
Why is SKIP outperforming AUTO? Two possibilities:
  1. SKIP plays have a real common characteristic the model is missing.
  2. 69% on 29 plays is just lucky variance (statistically not significant).

This script investigates by:
  - Dumping every SKIP play with full context (odds, prob, prop, edge, streak)
  - Comparing SKIP-WIN vs SKIP-LOSS characteristics
  - Comparing SKIP vs AUTO-MISS — what does SKIP have that failed AUTOs don't?
  - Looking for clusters: prop type, odds range, model_prob range

If we find a clear pattern (e.g., "SKIP wins cluster at odds -120 to +110 with
streak < 3"), that's a candidate tier definition. If not, SKIP's 69% is likely
variance and not actionable.

Usage:
    python mlb_skip_investigate.py
    python mlb_skip_investigate.py --cards-dir posted_cards
    python mlb_skip_investigate.py --csv skip_dump.csv   # raw data for spreadsheet
"""

import json
import os
import glob
import argparse
import csv
from collections import defaultdict


def load_cards(cards_dir):
    cards = []
    for fp in sorted(glob.glob(os.path.join(cards_dir, "posted_card_*.json"))):
        with open(fp, encoding="utf-8") as f:
            card = json.load(f)
        if not card.get("graded"):
            continue
        cards.append((card["date"], card.get("plays", [])))
    return cards


def extract_plays(cards, tier_filter=None, result_filter=None):
    """Extract plays matching tier/result filters with all context."""
    out = []
    for date, plays in cards:
        for p in plays:
            if tier_filter and p.get("tier") != tier_filter:
                continue
            if result_filter and p.get("result") != result_filter:
                continue
            out.append({
                "date":         date,
                "player":       p.get("player"),
                "prop":         p.get("prop"),
                "tier":         p.get("tier"),
                "odds":         p.get("odds"),
                "model_prob":   p.get("model_prob"),
                "book_implied": p.get("book_implied"),
                "edge":         p.get("edge"),
                "streak":       p.get("streak"),
                "l5":           p.get("l5"),
                "l10":          p.get("l10"),
                "result":       p.get("result"),
            })
    return out


def odds_bucket(odds):
    try:
        o = int(odds)
    except (TypeError, ValueError):
        return "?"
    if o >= 110:    return "+110 or higher"
    if o >= 0:      return "+100 to +109"
    if o > -120:    return "-101 to -119"
    if o > -150:    return "-120 to -149"
    if o > -200:    return "-150 to -199"
    if o > -250:    return "-200 to -249"
    return "-250 or worse"


def prob_bucket(p):
    if p is None:
        return "?"
    if p >= 0.90:  return "90%+"
    if p >= 0.80:  return "80-89%"
    if p >= 0.70:  return "70-79%"
    if p >= 0.60:  return "60-69%"
    if p >= 0.50:  return "50-59%"
    return "<50%"


def streak_bucket(s):
    if s is None:
        return "?"
    try:
        s = int(s)
    except:
        return "?"
    if s == 0:   return "0 (cold)"
    if s <= 2:   return "1-2"
    if s <= 4:   return "3-4"
    if s <= 7:   return "5-7"
    return "8+"


def crosstab(plays, key_fn, label):
    """Build crosstab of HITS vs MISSES across a categorical key."""
    buckets = defaultdict(lambda: {"hits": 0, "misses": 0})
    for p in plays:
        key = key_fn(p)
        if p["result"] == "hit":
            buckets[key]["hits"] += 1
        elif p["result"] == "miss":
            buckets[key]["misses"] += 1
    return buckets


def print_crosstab(buckets, label, sort_order=None):
    print(f"\n  {label}:")
    print(f"    {'Bucket':<22} {'Hits':>5} {'Miss':>5} {'Rate':>7} {'N':>5}")
    keys = sort_order if sort_order else sorted(buckets.keys())
    for key in keys:
        if key not in buckets:
            continue
        h = buckets[key]["hits"]
        m = buckets[key]["misses"]
        total = h + m
        if total == 0:
            continue
        rate = h / total * 100
        # Visual flag for high-edge buckets
        flag = ""
        if total >= 3:
            if rate >= 75:    flag = " ★ strong"
            elif rate >= 65:  flag = " ☆ promising"
            elif rate <= 40:  flag = " ⚠ weak"
        print(f"    {key:<22} {h:>5} {m:>5} {rate:>6.1f}% {total:>5}{flag}")


def odds_sort_key():
    return ["+110 or higher", "+100 to +109", "-101 to -119", "-120 to -149",
            "-150 to -199", "-200 to -249", "-250 or worse", "?"]


def prob_sort_key():
    return ["90%+", "80-89%", "70-79%", "60-69%", "50-59%", "<50%", "?"]


def streak_sort_key():
    return ["0 (cold)", "1-2", "3-4", "5-7", "8+", "?"]


def main():
    parser = argparse.ArgumentParser(description="Investigate SKIP tier performance")
    parser.add_argument("--cards-dir", default="posted_cards")
    parser.add_argument("--csv", default=None, help="Dump SKIP plays to CSV")
    args = parser.parse_args()

    cards = load_cards(args.cards_dir)
    if not cards:
        print(f"✗ No graded cards in {args.cards_dir}")
        return

    skip_plays  = extract_plays(cards, tier_filter="SKIP")
    auto_plays  = extract_plays(cards, tier_filter="AUTO")
    auto_misses = extract_plays(cards, tier_filter="AUTO", result_filter="miss")
    skip_wins   = [p for p in skip_plays if p["result"] == "hit"]
    skip_losses = [p for p in skip_plays if p["result"] == "miss"]

    print(f"\n📊 SKIP INVESTIGATION — {len(cards)} graded cards")
    print(f"   SKIP plays: {len(skip_plays)} total ({len(skip_wins)} wins, {len(skip_losses)} losses)")
    print(f"   AUTO plays: {len(auto_plays)} total ({len(auto_misses)} misses)")

    # ───────────────────────────────────────────────────────────
    # 1. RAW DUMP — show every SKIP play
    # ───────────────────────────────────────────────────────────
    print()
    print("=" * 100)
    print("EVERY SKIP PLAY — sorted by date")
    print("=" * 100)
    print(f"{'Date':<12} {'Player':<22} {'Prop':<12} {'Odds':>6} {'Prob':>6} "
          f"{'Edge':>6} {'Strk':>4} {'Result':<6}")
    print("-" * 100)
    for p in sorted(skip_plays, key=lambda x: x["date"]):
        odds = f"{p['odds']:+d}" if isinstance(p["odds"], (int, float)) else str(p["odds"])
        prob = f"{p['model_prob']*100:.0f}%" if p["model_prob"] else "?"
        edge = f"{p['edge']*100:+.0f}%" if p["edge"] else "?"
        streak = str(p["streak"]) if p["streak"] is not None else "?"
        result = p["result"] or "?"
        flag = " ✓" if result == "hit" else " ✗" if result == "miss" else "  "
        print(f"{p['date']:<12} {p['player']:<22} {p['prop']:<12} {odds:>6} "
              f"{prob:>6} {edge:>6} {streak:>4} {result:<6}{flag}")

    # ───────────────────────────────────────────────────────────
    # 2. SKIP-WIN vs SKIP-LOSS — look for differentiators
    # ───────────────────────────────────────────────────────────
    print()
    print("=" * 100)
    print("SKIP WIN/LOSS PATTERNS — what's different about winners vs losers?")
    print("=" * 100)

    print_crosstab(crosstab(skip_plays, lambda p: odds_bucket(p["odds"]), "odds"),
                   "By odds range", sort_order=odds_sort_key())
    print_crosstab(crosstab(skip_plays, lambda p: prob_bucket(p["model_prob"]), "prob"),
                   "By model_prob range", sort_order=prob_sort_key())
    print_crosstab(crosstab(skip_plays, lambda p: streak_bucket(p["streak"]), "streak"),
                   "By streak length", sort_order=streak_sort_key())
    print_crosstab(crosstab(skip_plays, lambda p: p["prop"] or "?", "prop"),
                   "By prop type")

    # ───────────────────────────────────────────────────────────
    # 3. SKIP vs AUTO-MISS — what does SKIP have that failed AUTOs don't?
    # ───────────────────────────────────────────────────────────
    print()
    print("=" * 100)
    print("SKIP-WINS vs AUTO-MISSES — what separates winning SKIP from failed AUTO?")
    print("=" * 100)

    def compare(skip_wins, auto_misses, key_fn, label):
        print(f"\n  {label}:")
        skip_buckets  = defaultdict(int)
        auto_buckets  = defaultdict(int)
        for p in skip_wins:  skip_buckets[key_fn(p)] += 1
        for p in auto_misses: auto_buckets[key_fn(p)] += 1
        all_keys = sorted(set(list(skip_buckets.keys()) + list(auto_buckets.keys())))
        print(f"    {'Bucket':<22} {'SKIP-W%':>10} {'AUTO-M%':>10}")
        for key in all_keys:
            sw_pct = skip_buckets[key] / len(skip_wins) * 100 if skip_wins else 0
            am_pct = auto_buckets[key] / len(auto_misses) * 100 if auto_misses else 0
            flag = ""
            if abs(sw_pct - am_pct) >= 15:
                flag = " ← divergent"
            print(f"    {key:<22} {sw_pct:>9.1f}% {am_pct:>9.1f}%{flag}")

    compare(skip_wins, auto_misses, lambda p: odds_bucket(p["odds"]), "Odds distribution")
    compare(skip_wins, auto_misses, lambda p: prob_bucket(p["model_prob"]), "Model prob distribution")
    compare(skip_wins, auto_misses, lambda p: streak_bucket(p["streak"]), "Streak distribution")
    compare(skip_wins, auto_misses, lambda p: p["prop"] or "?", "Prop type")

    # ───────────────────────────────────────────────────────────
    # 4. CSV export if requested
    # ───────────────────────────────────────────────────────────
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=skip_plays[0].keys())
            writer.writeheader()
            writer.writerows(skip_plays)
        print(f"\n✓ SKIP plays dumped to {args.csv}")

    # ───────────────────────────────────────────────────────────
    # 5. CONCLUSION SCAFFOLD
    # ───────────────────────────────────────────────────────────
    print()
    print("=" * 100)
    print("READING THE RESULTS")
    print("=" * 100)
    print(f"""
  Look for these patterns:

  STRONG SIGNAL — actionable:
    - One bucket has 75%+ hit rate AND 5+ plays (e.g. "SKIP at -101 to -119 hits 80% on 8 plays")
    - SKIP-W and AUTO-M differ by 15+ percentage points in a specific bucket
    - A clear odds range OR prop OR prob band stands out across multiple cuts

  NOISE WARNING — likely variance:
    - Hits are scattered across all buckets evenly
    - Strong-looking buckets all have only 1-3 plays
    - SKIP-W and AUTO-M look similar in every dimension

  If you find a strong signal: use those criteria as a new tier definition.
  If you find noise: SKIP's 69% rate is probably variance — don't build on it.
    """)


if __name__ == "__main__":
    main()
