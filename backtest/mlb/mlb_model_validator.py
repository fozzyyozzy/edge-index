"""
Edge Index — MLB Model Validator
Calculates R² for each signal against actual hit/no-hit outcomes.
Implements colleague's methodology: scale features 0-1, weight by R².

Usage:
  python mlb_model_validator.py                    # analyze all results
  python mlb_model_validator.py --signal l5        # single signal deep dive
  python mlb_model_validator.py --rebuild-weights  # output new model weights
  python mlb_model_validator.py --backtest         # walk-forward backtest

Output:
  - R² for each signal vs actual outcome
  - Recommended weights (R²-scaled, per colleague's method)
  - Calibration chart: predicted prob vs actual hit rate
  - New model formula to paste into mlb_run_today.py
"""
import os, sys, json, glob, argparse
import numpy as np
from datetime import date, datetime

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = BASE_DIR  # mlb_results_YYYY-MM-DD.json live here
PLAYS_DIR   = BASE_DIR  # mlb_plays_YYYY-MM-DD.json live here

# ── SIGNAL NAMES → plays JSON key ────────────────────────────
# Maps what we call the signal to its key in mlb_plays output
SIGNAL_MAP = {
    "l5":           "l5",          # L5 hit rate (0.0-1.0)
    "l10":          "l10",         # L10 hit rate (0.0-1.0)
    "streak":       "streak",      # consecutive games over line (int)
    "model_prob":   "model_prob",  # composite model output (0.0-1.0)
    "park_factor":  None,          # derived from home team
    "xba_diff":     None,          # from savant signals (optional)
    "platoon_adj":  None,          # derived from platoon cache (optional)
}

PARK_FACTORS = {
    "Cincinnati Reds":1.08,"Philadelphia Phillies":1.06,"Boston Red Sox":1.05,
    "Houston Astros":1.04,"New York Yankees":1.03,"Milwaukee Brewers":1.02,
    "Texas Rangers":1.02,"Atlanta Braves":1.01,"Los Angeles Dodgers":1.00,
    "Chicago Cubs":1.00,"St. Louis Cardinals":0.99,"Minnesota Twins":0.98,
    "Detroit Tigers":0.98,"Toronto Blue Jays":0.97,"Cleveland Guardians":0.97,
    "Pittsburgh Pirates":0.96,"Miami Marlins":0.95,"Athletics":0.95,
    "San Francisco Giants":0.94,"San Diego Padres":0.94,"Seattle Mariners":0.93,
    "Tampa Bay Rays":0.98,"Baltimore Orioles":0.99,"Kansas City Royals":0.98,
    "Los Angeles Angels":0.99,"Arizona Diamondbacks":1.02,"Colorado Rockies":1.18,
    "Washington Nationals":0.99,"New York Mets":0.97,"Chicago White Sox":1.01,
}

# ── DATA LOADING ──────────────────────────────────────────────

def load_all_results():
    """
    Load all mlb_results_YYYY-MM-DD.json files.
    Returns list of {date, player, prop, result, actual, odds, tier}.
    """
    pattern = os.path.join(RESULTS_DIR, "mlb_results_*.json")
    files   = sorted(glob.glob(pattern))

    if not files:
        print(f"No results files found in {RESULTS_DIR}")
        print("Run: python mlb_results_checker.py --date YYYY-MM-DD for each past date")
        return []

    all_results = []
    for fp in files:
        try:
            with open(fp) as f:
                data = json.load(f)
            game_date = data.get("date", os.path.basename(fp)[12:22])
            for play in data.get("plays", []):
                if play.get("result") in ("hit", "miss"):
                    all_results.append({
                        "date":   game_date,
                        "player": play.get("player"),
                        "prop":   play.get("prop"),
                        "line":   play.get("line"),
                        "odds":   play.get("odds"),
                        "tier":   play.get("tier"),
                        "result": play.get("result"),
                        "actual": play.get("actual"),
                        "hit":    1 if play.get("result") == "hit" else 0,
                    })
        except Exception as e:
            print(f"  Error loading {fp}: {e}")

    print(f"Loaded {len(all_results)} settled plays from {len(files)} days")
    return all_results

def load_plays_for_date(game_date):
    """Load mlb_plays_YYYY-MM-DD.json — has all signal values."""
    path = os.path.join(PLAYS_DIR, f"mlb_plays_{game_date}.json")
    if not os.path.exists(path):
        return []

    with open(path) as f:
        data = json.load(f)

    plays = []
    for p in data.get("batter_plays", []) + data.get("pitcher_plays", []):
        if p:
            p["date"] = game_date
            plays.append(p)
    return plays

def merge_signals_and_outcomes(results):
    """
    Join results (outcomes) with plays (signals) by date+player+prop.
    Returns list of dicts with both signal values and hit outcome.
    """
    merged = []

    # Group results by date
    by_date = {}
    for r in results:
        by_date.setdefault(r["date"], []).append(r)

    for game_date, day_results in by_date.items():
        plays = load_plays_for_date(game_date)
        plays_idx = {
            (p.get("player","").lower(), p.get("prop","")): p
            for p in plays
        }

        for r in day_results:
            key = (r["player"].lower(), r["prop"])
            play = plays_idx.get(key, {})

            # Park factor from home team
            home = play.get("home", "")
            pf   = PARK_FACTORS.get(home, 1.0)

            merged.append({
                "date":       game_date,
                "player":     r["player"],
                "prop":       r["prop"],
                "hit":        r["hit"],
                "tier":       r.get("tier"),
                "odds":       int(r.get("odds", -110)),
                # Signals
                "l5":         play.get("l5", None),
                "l10":        play.get("l10", None),
                "streak":     play.get("streak", None),
                "model_prob": play.get("model_prob", None),
                "park_factor":pf,
                "l5_avg":     play.get("l5_avg", None),
            })

    return merged

# ── STATISTICS ────────────────────────────────────────────────

def pearson_r2(x_vals, y_vals):
    """
    Calculate R² (coefficient of determination) between signal and outcome.
    y_vals is binary (0/1 hit). x_vals is the signal value.
    Uses Pearson r then squares it — colleague's method.
    """
    x = np.array(x_vals, dtype=float)
    y = np.array(y_vals, dtype=float)

    # Remove NaN pairs
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]

    if len(x) < 10:
        return None, len(x)

    x_mean = np.mean(x)
    y_mean = np.mean(y)
    num    = np.sum((x - x_mean) * (y - y_mean))
    den    = np.sqrt(np.sum((x - x_mean)**2) * np.sum((y - y_mean)**2))

    if den == 0:
        return 0.0, len(x)

    r  = num / den
    r2 = r ** 2
    return round(r2, 4), len(x)

def calibration_bins(signal_vals, hit_vals, n_bins=5):
    """
    Bucket signal into n_bins, show actual hit rate per bucket.
    Tells us: when model says 80%, do we actually hit 80%?
    """
    pairs = [(s, h) for s, h in zip(signal_vals, hit_vals)
             if s is not None]
    if len(pairs) < 10:
        return []

    pairs.sort(key=lambda x: x[0])
    bin_size = max(1, len(pairs) // n_bins)
    bins     = []

    for i in range(0, len(pairs), bin_size):
        chunk = pairs[i:i+bin_size]
        if not chunk:
            continue
        sig_vals  = [c[0] for c in chunk]
        hit_rate  = sum(c[1] for c in chunk) / len(chunk)
        bins.append({
            "signal_range": (round(min(sig_vals), 3), round(max(sig_vals), 3)),
            "n":            len(chunk),
            "actual_rate":  round(hit_rate, 3),
            "signal_avg":   round(np.mean(sig_vals), 3),
        })

    return bins

# ── WEIGHT CALCULATION — colleague's method ───────────────────

def calc_weights(r2_scores):
    """
    Scale weights by R² value so highest-R² signal gets most weight.
    Signals with R² < 0.05 are dropped (too weak).
    Returns dict of signal → weight (sum to 1.0).

    Per colleague:
    - Don't apply multipliers to base number
    - Scale: 0 = min, 0.5 = league avg, 1 = max
    - Weight each feature by its R² / sum(R²s)
    """
    qualified = {k: v for k, v in r2_scores.items()
                 if v is not None and v >= 0.05}

    if not qualified:
        print("WARNING: No signals cleared R² >= 0.05 threshold")
        return {}

    total_r2 = sum(qualified.values())
    weights  = {k: round(v / total_r2, 4) for k, v in qualified.items()}
    return weights

def scale_signal(value, all_values, signal_name):
    """
    Scale a signal to [0, 1] where 0.5 = league average.
    Per colleague: average = 0.5, max = 1, min = 0.
    """
    vals = [v for v in all_values if v is not None]
    if not vals:
        return 0.5

    min_v = min(vals)
    max_v = max(vals)

    if max_v == min_v:
        return 0.5

    return round((value - min_v) / (max_v - min_v), 4)

# ── MAIN ANALYSIS ─────────────────────────────────────────────

def analyze_signals(records, prop_filter=None):
    """
    Run R² analysis on all signals.
    prop_filter: 'hits', 'strikeouts', None (all)
    """
    if prop_filter:
        records = [r for r in records if r.get("prop") == prop_filter]

    if len(records) < 15:
        print(f"  Only {len(records)} records — need more data for reliable R²")
        print("  Keep running daily. R² stabilizes around 50+ observations.")
        return {}

    signals = ["l5", "l10", "streak", "model_prob", "park_factor"]
    outcomes = [r["hit"] for r in records]

    print(f"\n{'='*65}")
    label = prop_filter.upper() if prop_filter else "ALL PROPS"
    print(f"SIGNAL R² ANALYSIS — {label} | n={len(records)}")
    print(f"{'='*65}")
    print(f"  {'SIGNAL':18} {'R²':8} {'n':6} {'DIRECTION':12} {'KEEP?':6}")
    print(f"  {'─'*55}")

    r2_scores = {}

    for sig in signals:
        sig_vals = [r.get(sig) for r in records]
        r2, n    = pearson_r2(sig_vals, outcomes)

        if r2 is None:
            print(f"  {sig:18} {'N/A':8} {n:6} {'insufficient data':12}")
            continue

        # Direction: is higher signal = more hits?
        sig_clean = [s for s, o in zip(sig_vals, outcomes) if s is not None]
        out_clean = [o for s, o in zip(sig_vals, outcomes) if s is not None]
        pos_corr  = np.corrcoef(sig_clean, out_clean)[0,1] > 0
        direction = "positive" if pos_corr else "negative"
        keep      = "✓ YES" if r2 >= 0.05 else "✗ WEAK"

        print(f"  {sig:18} {r2:8.4f} {n:6} {direction:12} {keep}")
        r2_scores[sig] = r2

    return r2_scores

def print_calibration(records, signal="model_prob"):
    """Show predicted vs actual hit rate by bucket."""
    sig_vals = [r.get(signal) for r in records]
    hit_vals = [r["hit"] for r in records]
    bins     = calibration_bins(sig_vals, hit_vals)

    if not bins:
        return

    overall_rate = round(sum(hit_vals) / len(hit_vals), 3)

    print(f"\n{'='*65}")
    print(f"CALIBRATION — {signal.upper()} vs ACTUAL HIT RATE")
    print(f"League average hit rate in sample: {overall_rate*100:.1f}%")
    print(f"{'─'*65}")
    print(f"  {'SIGNAL RANGE':20} {'N':5} {'PREDICTED':12} {'ACTUAL':10} {'DIFF':8}")
    print(f"  {'─'*55}")

    for b in bins:
        lo, hi   = b["signal_range"]
        pred     = b["signal_avg"]
        actual   = b["actual_rate"]
        diff     = actual - pred
        bar_len  = int(actual * 20)
        bar      = "█" * bar_len + "░" * (20 - bar_len)
        flag     = " ← OVERFIT" if abs(diff) > 0.15 else ""

        print(f"  {lo:.2f}–{hi:.2f}              "
              f"{b['n']:5} {pred*100:8.1f}%    "
              f"{actual*100:6.1f}%    "
              f"{diff:+.3f}{flag}")

    print(f"\n  Ideal calibration: diff column near 0.000 across all rows")
    print(f"  Large positive diff = model UNDERESTIMATES (conservative)")
    print(f"  Large negative diff = model OVERESTIMATES (overconfident)")

def print_new_weights(r2_scores, records):
    """
    Output the new R²-weighted model formula.
    Implements colleague's scaling method exactly.
    """
    weights = calc_weights(r2_scores)

    if not weights:
        return

    print(f"\n{'='*65}")
    print(f"RECOMMENDED MODEL WEIGHTS (R²-scaled)")
    print(f"Per colleague methodology — no multipliers, scaled features")
    print(f"{'─'*65}")

    for sig, w in sorted(weights.items(), key=lambda x: -x[1]):
        r2 = r2_scores.get(sig, 0)
        print(f"  {sig:18} R²={r2:.4f}  →  weight {w:.4f} ({w*100:.1f}%)")

    print(f"\n{'─'*65}")
    print(f"NEW MODEL FORMULA — paste into mlb_run_today.py:")
    print(f"{'─'*65}")

    # Build scaling context from records
    sig_ranges = {}
    for sig in weights:
        vals = [r.get(sig) for r in records if r.get(sig) is not None]
        if vals:
            sig_ranges[sig] = (min(vals), max(vals))

    print(f"\ndef evaluate_batter_v2(row, prior_values, prop_type):")
    print(f"    line   = row['line']")
    print(f"    l5     = calc_rate(prior_values, line, 5)")
    print(f"    l10    = calc_rate(prior_values, line, 10)")
    print(f"    streak = calc_streak(prior_values, line)")
    print(f"    pf     = PARK_FACTORS.get(row['home'], 1.0)")
    print(f"")
    print(f"    # Scale each signal to [0,1] where 0.5 = league average")

    for sig in weights:
        if sig in sig_ranges:
            lo, hi = sig_ranges[sig]
            print(f"    {sig}_s = ({sig} - {lo:.3f}) / {(hi-lo):.3f}  "
                  f"# range [{lo:.3f}, {hi:.3f}]")

    print(f"")
    print(f"    # R²-weighted probability — no multipliers")
    terms = " + ".join(
        f"{w:.4f}*{sig}_s" for sig, w in sorted(weights.items(), key=lambda x: -x[1])
    )
    print(f"    model_prob = min(0.95, max(0.05, {terms}))")
    print(f"")
    print(f"    # Note: result is already in [0,1] space")
    print(f"    # Tier thresholds apply AFTER this calculation")

def walk_forward_backtest(records):
    """
    Walk-forward: train on first N days, test on remaining.
    Shows whether the model generalizes or overfits.
    """
    by_date  = {}
    for r in records:
        by_date.setdefault(r["date"], []).append(r)

    dates = sorted(by_date.keys())

    if len(dates) < 4:
        print("Need at least 4 days of data for walk-forward backtest")
        return

    print(f"\n{'='*65}")
    print(f"WALK-FORWARD BACKTEST — {len(dates)} days")
    print(f"{'─'*65}")
    print(f"  {'DATE':12} {'TRAIN N':8} {'TEST N':7} {'MODEL ACC':10} "
          f"{'BASELINE':10} {'EDGE':8}")
    print(f"  {'─'*55}")

    # Start training after first 5 days minimum
    for split in range(min(5, len(dates)-1), len(dates)):
        train_dates = dates[:split]
        test_dates  = [dates[split]]

        train = [r for r in records if r["date"] in set(train_dates)]
        test  = [r for r in records if r["date"] in set(test_dates)]

        if len(train) < 10 or not test:
            continue

        # Calculate weights on train set
        train_r2 = {}
        for sig in ["l5", "l10", "streak", "model_prob"]:
            sig_vals = [r.get(sig) for r in train]
            r2, _    = pearson_r2(sig_vals, [r["hit"] for r in train])
            if r2 is not None:
                train_r2[sig] = r2

        weights = calc_weights(train_r2)

        if not weights:
            continue

        # Score test set
        correct   = 0
        total     = 0
        baseline  = sum(r["hit"] for r in test) / len(test)

        for r in test:
            # Build scaled score
            score = 0.0
            for sig, w in weights.items():
                val = r.get(sig)
                if val is not None:
                    train_vals = [tr.get(sig) for tr in train
                                  if tr.get(sig) is not None]
                    lo = min(train_vals) if train_vals else 0
                    hi = max(train_vals) if train_vals else 1
                    scaled = (val - lo) / (hi - lo) if hi > lo else 0.5
                    score += w * scaled

            predict_hit = score >= 0.50
            actual_hit  = r["hit"] == 1
            if predict_hit == actual_hit:
                correct += 1
            total += 1

        acc  = correct / total if total else 0
        edge = acc - baseline

        flag = " ← EDGE" if edge > 0.05 else ""
        print(f"  {dates[split]:12} {len(train):8} {total:7} "
              f"{acc*100:8.1f}%   {baseline*100:8.1f}%   "
              f"{edge:+.3f}{flag}")

def tier_breakdown(records):
    """Show hit rate by tier — validates tier thresholds."""
    print(f"\n{'='*65}")
    print(f"HIT RATE BY TIER")
    print(f"{'─'*65}")
    print(f"  {'TIER':8} {'W-L':8} {'HIT RATE':10} {'P&L @$100':12} {'TARGET':8}")
    print(f"  {'─'*50}")

    targets = {"AUTO": 0.88, "T1": 0.75, "T2": 0.65}

    for tier in ["AUTO", "T1", "T2"]:
        subset = [r for r in records if r.get("tier") == tier]
        if not subset:
            continue

        hits   = sum(r["hit"] for r in subset)
        total  = len(subset)
        rate   = hits / total

        pnl = 0.0
        for r in subset:
            odds = r.get("odds", -110)
            if r["hit"]:
                pnl += 100*(100/abs(odds)) if odds < 0 else 100*(odds/100)
            else:
                pnl -= 100

        target  = targets.get(tier, 0.65)
        vs_tgt  = rate - target
        flag    = " ✓" if vs_tgt >= 0 else " ← BELOW TARGET"

        print(f"  {tier:8} {hits}-{total-hits:3}    "
              f"{rate*100:6.1f}%    "
              f"{'+' if pnl>=0 else ''}${pnl:8.0f}    "
              f"{target*100:.0f}%{flag}")

    print(f"\n  Tier targets: AUTO≥88%, T1≥75%, T2≥65%")
    print(f"  If AUTO is below 75%, threshold needs tightening")

# ── ENTRY POINT ───────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal",          default=None,
                        help="Deep dive a single signal: l5, l10, streak, model_prob")
    parser.add_argument("--prop",            default=None,
                        choices=["hits","strikeouts","total_bases"],
                        help="Filter to specific prop type")
    parser.add_argument("--rebuild-weights", action="store_true",
                        help="Output new R²-weighted model formula")
    parser.add_argument("--backtest",        action="store_true",
                        help="Run walk-forward backtest")
    parser.add_argument("--tiers",           action="store_true",
                        help="Show hit rate breakdown by tier")
    parser.add_argument("--calibrate",       action="store_true",
                        help="Show model calibration (predicted vs actual)")
    args = parser.parse_args()

    print(f"\nEdge Index Model Validator — {date.today()}")
    print(f"Looking for results in: {RESULTS_DIR}")

    # Load outcomes
    results = load_all_results()
    if not results:
        sys.exit(1)

    # Merge with signal values from plays files
    print("Merging with signal data from plays files...")
    records = merge_signals_and_outcomes(results)
    settled = [r for r in records if r["hit"] is not None]

    print(f"  {len(settled)} records with signal data available")

    overall_rate = sum(r["hit"] for r in settled) / max(len(settled), 1)
    print(f"  Overall hit rate in sample: {overall_rate*100:.1f}%")
    print(f"  Date range: {min(r['date'] for r in settled)} "
          f"to {max(r['date'] for r in settled)}")

    if args.tiers:
        tier_breakdown(settled)

    if args.calibrate:
        print_calibration(settled, signal=args.signal or "model_prob")

    if args.signal:
        # Deep dive one signal
        sig_vals = [r.get(args.signal) for r in settled]
        hit_vals = [r["hit"] for r in settled]
        r2, n    = pearson_r2(sig_vals, hit_vals)
        print(f"\nDeep dive: {args.signal}")
        print(f"  R² = {r2:.4f} | n = {n}")
        bins = calibration_bins(sig_vals, hit_vals, n_bins=8)
        print(f"\n  {'RANGE':15} {'N':5} {'AVG SIGNAL':12} {'ACTUAL HIT%':12}")
        for b in bins:
            lo, hi = b["signal_range"]
            bar = "█" * int(b["actual_rate"] * 30)
            print(f"  {lo:.3f}–{hi:.3f}      "
                  f"{b['n']:5}  {b['signal_avg']:8.3f}     "
                  f"{b['actual_rate']*100:6.1f}%  {bar}")
    else:
        # Full R² analysis
        r2_scores = analyze_signals(settled, prop_filter=args.prop)

        if r2_scores:
            if args.rebuild_weights:
                print_new_weights(r2_scores, settled)
            else:
                weights = calc_weights(r2_scores)
                if weights:
                    print(f"\n{'─'*65}")
                    print(f"PRELIMINARY WEIGHTS (run --rebuild-weights for full formula):")
                    for sig, w in sorted(weights.items(), key=lambda x: -x[1]):
                        print(f"  {sig:18} {w*100:.1f}%")

    if args.backtest:
        walk_forward_backtest(settled)

    # Always print tier breakdown as baseline
    if not any([args.tiers, args.calibrate, args.signal]):
        tier_breakdown(settled)

    print(f"\n{'='*65}")
    print(f"NEXT STEPS:")
    print(f"  1. Run daily — R² stabilizes after ~50+ observations per signal")
    print(f"  2. Once R² > 0.7 confirmed: python mlb_model_validator.py --rebuild-weights")
    print(f"  3. Paste new formula into mlb_run_today.py evaluate_batter()")
    print(f"  4. Backtest first: python mlb_model_validator.py --backtest")
    print(f"  5. Run parallel for 1 week before switching live model")
    print(f"{'='*65}\n")
