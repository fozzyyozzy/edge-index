"""
TIER HIT-RATE AUDIT
===================
Analyzes posted_card_*.json files to evaluate whether AUTO/T1/T2 tier
classifications are actually performing at the rates the model expects.

Usage:
    python mlb_tier_audit.py
    python mlb_tier_audit.py --cards-dir posted_cards
    python mlb_tier_audit.py --window 7    # rolling 7-day window analysis
    python mlb_tier_audit.py --by-prop     # break down by prop type

Outputs:
    1. Overall hit rate per tier (all-time)
    2. Hit rate per tier per week (degradation check)
    3. EV per play per tier (is the edge real?)
    4. Miss analysis — what do AUTO misses have in common?
    5. Recommendations — should any tier be relabeled?

The "AUTO threshold" question: if AUTO hits 80%+, the label is honest.
Below that, the model is overconfident and AUTO should be retiered or
the assignment criteria tightened.
"""

import json
import os
import glob
import argparse
from collections import defaultdict
from datetime import datetime


def load_cards(cards_dir):
    """Load all graded posted cards, return list of (date, plays, fades) tuples."""
    cards = []
    for fp in sorted(glob.glob(os.path.join(cards_dir, "posted_card_*.json"))):
        with open(fp, encoding="utf-8") as f:
            card = json.load(f)
        if not card.get("graded"):
            continue
        cards.append((card["date"], card.get("plays", []), card.get("fades", [])))
    return cards


def odds_to_payout(odds, stake=100):
    """Convert American odds to payout on $stake win."""
    try:
        o = int(odds)
    except (TypeError, ValueError):
        return 0
    if o > 0:
        return stake * o / 100
    else:
        return stake * 100 / abs(o)


def audit_overall(cards):
    """Tier-by-tier overall stats."""
    stats = defaultdict(lambda: {"plays": 0, "hits": 0, "misses": 0, "voids": 0, "pnl": 0.0})
    for date, plays, _ in cards:
        for p in plays:
            tier = p.get("tier", "?")
            s = stats[tier]
            s["plays"] += 1
            result = p.get("result")
            if result == "hit":
                s["hits"] += 1
                s["pnl"] += odds_to_payout(p.get("odds", 0))
            elif result == "miss":
                s["misses"] += 1
                s["pnl"] -= 100  # $100 unit stake
            elif result == "void":
                s["voids"] += 1
    return stats


def audit_rolling(cards, window=7):
    """Rolling hit rates per tier — detects degradation over time."""
    # Group by date, then walk forward computing rolling stats
    by_date = defaultdict(lambda: defaultdict(lambda: {"hits": 0, "decided": 0}))
    for date, plays, _ in cards:
        for p in plays:
            tier = p.get("tier", "?")
            result = p.get("result")
            if result in ("hit", "miss"):
                by_date[date][tier]["decided"] += 1
                if result == "hit":
                    by_date[date][tier]["hits"] += 1

    dates = sorted(by_date.keys())
    rolling = []
    for i in range(len(dates)):
        window_dates = dates[max(0, i - window + 1):i + 1]
        window_stats = defaultdict(lambda: {"hits": 0, "decided": 0})
        for d in window_dates:
            for tier, ts in by_date[d].items():
                window_stats[tier]["hits"] += ts["hits"]
                window_stats[tier]["decided"] += ts["decided"]
        rolling.append((dates[i], dict(window_stats)))
    return rolling


def audit_misses(cards, tier="AUTO"):
    """What do AUTO misses have in common? Look at odds, model_prob, prop type, edge."""
    misses = []
    for date, plays, _ in cards:
        for p in plays:
            if p.get("tier") != tier:
                continue
            if p.get("result") != "miss":
                continue
            misses.append({
                "date": date,
                "player": p.get("player"),
                "prop": p.get("prop"),
                "odds": p.get("odds"),
                "model_prob": p.get("model_prob"),
                "book_implied": p.get("book_implied"),
                "edge": p.get("edge"),
                "streak": p.get("streak"),
            })
    return misses


def fmt_pct(n, d):
    if d == 0:
        return "  --  "
    return f"{n/d*100:>5.1f}%"


def fmt_currency(n):
    sign = "+" if n >= 0 else "-"
    return f"{sign}${abs(n):>6.0f}"


def print_overall(stats):
    print()
    print("=" * 78)
    print("OVERALL TIER PERFORMANCE (all graded cards)")
    print("=" * 78)
    print(f"{'Tier':<8} {'Plays':>6} {'Hits':>6} {'Miss':>6} {'Void':>6} "
          f"{'HitRate':>9} {'P&L':>10} {'EV/Bet':>10}")
    print("-" * 78)

    tier_order = ["AUTO", "T1", "T2", "SKIP", "JUICE", "?"]
    seen = []
    for tier in tier_order:
        if tier not in stats:
            continue
        seen.append(tier)
        s = stats[tier]
        decided = s["hits"] + s["misses"]
        hit_rate = fmt_pct(s["hits"], decided) if decided else "  --  "
        ev = (s["pnl"] / s["plays"]) if s["plays"] else 0
        print(f"{tier:<8} {s['plays']:>6} {s['hits']:>6} {s['misses']:>6} "
              f"{s['voids']:>6} {hit_rate:>9} {fmt_currency(s['pnl']):>10} "
              f"{fmt_currency(ev):>10}")

    # Also any tiers not in expected list
    for tier in stats:
        if tier not in seen:
            tier_label = str(tier) if tier is not None else "(none)"
            s = stats[tier]
            decided = s["hits"] + s["misses"]
            hit_rate = fmt_pct(s["hits"], decided) if decided else "  --  "
            ev = (s["pnl"] / s["plays"]) if s["plays"] else 0
            print(f"{tier_label:<8} {s['plays']:>6} {s['hits']:>6} {s['misses']:>6} "
                  f"{s['voids']:>6} {hit_rate:>9} {fmt_currency(s['pnl']):>10} "
                  f"{fmt_currency(ev):>10}")


def print_rolling(rolling, window):
    print()
    print("=" * 78)
    print(f"ROLLING {window}-DAY HIT RATES (degradation check)")
    print("=" * 78)
    print(f"{'Date':<12} {'AUTO':>9} {'T1':>9} {'T2':>9} {'SKIP':>9}")
    print("-" * 78)

    for date, window_stats in rolling:
        row = [date]
        for tier in ["AUTO", "T1", "T2", "SKIP"]:
            ts = window_stats.get(tier, {"hits": 0, "decided": 0})
            if ts["decided"] == 0:
                row.append("    --  ")
            else:
                pct = ts["hits"] / ts["decided"] * 100
                row.append(f"{pct:>5.1f}% ({ts['decided']:>2})")
        print(f"{row[0]:<12} {row[1]:>9} {row[2]:>9} {row[3]:>9} {row[4]:>9}")


def print_miss_analysis(misses, tier):
    if not misses:
        print(f"\nNo {tier} misses to analyze.")
        return

    print()
    print("=" * 78)
    print(f"{tier} MISS ANALYSIS — what do failed {tier} plays have in common?")
    print("=" * 78)

    # Group by odds bucket
    buckets = defaultdict(int)
    for m in misses:
        o = m.get("odds", 0)
        try:
            o = int(o)
        except (TypeError, ValueError):
            continue
        if o >= 0:
            buckets["+money"] += 1
        elif o > -150:
            buckets["-100 to -149"] += 1
        elif o > -200:
            buckets["-150 to -199"] += 1
        elif o > -250:
            buckets["-200 to -249"] += 1
        else:
            buckets["-250 or worse"] += 1

    print(f"\n  Odds distribution of {tier} misses ({len(misses)} total):")
    for bucket in ["+money", "-100 to -149", "-150 to -199", "-200 to -249", "-250 or worse"]:
        n = buckets[bucket]
        bar = "█" * n
        print(f"    {bucket:<20}  {n:>3}  {bar}")

    # Model prob distribution
    probs = [m.get("model_prob", 0) for m in misses if m.get("model_prob")]
    if probs:
        avg = sum(probs) / len(probs)
        lowest = min(probs)
        highest = max(probs)
        print(f"\n  Model probability on {tier} misses:")
        print(f"    Average: {avg:.1%}")
        print(f"    Range: {lowest:.1%} to {highest:.1%}")
        print(f"    (If avg is high — e.g. 85%+ — model is overconfident on these")
        print(f"    If avg is borderline — e.g. 65-70% — these are edge-of-AUTO)")

    # Prop distribution
    props = defaultdict(int)
    for m in misses:
        props[m.get("prop", "?")] += 1
    print(f"\n  Prop type distribution of {tier} misses:")
    for prop, n in sorted(props.items(), key=lambda x: -x[1]):
        print(f"    {prop:<15}  {n}")


def print_recommendation(stats):
    print()
    print("=" * 78)
    print("RECOMMENDATIONS")
    print("=" * 78)

    auto = stats.get("AUTO", {})
    auto_decided = auto.get("hits", 0) + auto.get("misses", 0)
    auto_rate = auto["hits"] / auto_decided if auto_decided else 0

    t1 = stats.get("T1", {})
    t1_decided = t1.get("hits", 0) + t1.get("misses", 0)
    t1_rate = t1["hits"] / t1_decided if t1_decided else 0

    print(f"\n  AUTO actual: {auto_rate:.1%} on {auto_decided} decided plays")
    print(f"  T1 actual:   {t1_rate:.1%} on {t1_decided} decided plays")

    if auto_decided < 20:
        print(f"\n  ⚠ Only {auto_decided} AUTO plays graded — too small a sample for")
        print(f"    confident conclusions. Need 50+ for stable rate.")
    elif auto_rate >= 0.80:
        print(f"\n  ✓ AUTO performing at expected level (80%+). Tier classification is honest.")
    elif auto_rate >= 0.70:
        print(f"\n  ⚠ AUTO underperforming target. Real rate {auto_rate:.0%} vs expected 80%+.")
        print(f"    Either: (a) tighten AUTO criteria, (b) rename to T1, (c) variance — wait for more data.")
    else:
        print(f"\n  ✗ AUTO significantly underperforming. Real rate {auto_rate:.0%}.")
        print(f"    The tier label is misleading — these are not 'automatic' plays.")
        print(f"    Recommend: retune model_prob calculation OR raise AUTO threshold.")

    # Compare AUTO vs T1 — if T1 > AUTO, the tiering logic is broken
    if t1_decided >= 20 and auto_decided >= 20:
        if t1_rate > auto_rate:
            print(f"\n  ⚠ ANOMALY: T1 ({t1_rate:.1%}) outperforming AUTO ({auto_rate:.1%}).")
            print(f"    Tiering logic likely has a bug — AUTO should be the strongest plays.")
            print(f"    Possible cause: AUTO juice cap is too high, picking overpriced favorites.")


def main():
    parser = argparse.ArgumentParser(description="Audit tier hit rates from posted cards")
    parser.add_argument("--cards-dir", default="posted_cards",
                        help="Directory of posted_card_*.json files")
    parser.add_argument("--window", type=int, default=7,
                        help="Rolling window size in days (default 7)")
    parser.add_argument("--miss-tier", default="AUTO",
                        help="Tier to analyze misses for (default AUTO)")
    args = parser.parse_args()

    if not os.path.isdir(args.cards_dir):
        print(f"✗ Cards directory not found: {args.cards_dir}")
        return

    cards = load_cards(args.cards_dir)
    if not cards:
        print(f"✗ No graded cards found in {args.cards_dir}")
        return

    print(f"\n📊 TIER AUDIT — {len(cards)} graded cards from {cards[0][0]} to {cards[-1][0]}")

    stats = audit_overall(cards)
    print_overall(stats)

    rolling = audit_rolling(cards, args.window)
    print_rolling(rolling, args.window)

    misses = audit_misses(cards, args.miss_tier)
    print_miss_analysis(misses, args.miss_tier)

    print_recommendation(stats)
    print()


if __name__ == "__main__":
    main()
