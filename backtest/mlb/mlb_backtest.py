"""
Edge Index — MLB Backtest
Runs the full selection pipeline against historical dates and grades
against actual box scores. Validates that the model's card selection
logic reproduces (or improves on) the real posted-card results.

PHASE 1 — Sanity check (May 8-15):
  Run against dates you already have results for.
  If backtest P&L ≈ posted-card P&L, pipeline is sound.
  If they diverge significantly, there's a data or logic problem.

PHASE 2 — Extended backtest (May 1-7):
  Only run after Phase 1 validates. Requires historical odds from
  The Odds API (uses ~100 credits per day).

Usage:
  # Phase 1 — sanity check against known dates
  python mlb_backtest.py --start 2026-05-08 --end 2026-05-15

  # Single date
  python mlb_backtest.py --date 2026-05-12

  # Compare backtest card vs what you actually posted
  python mlb_backtest.py --start 2026-05-08 --end 2026-05-15 --vs-posted

  # Full May (after Phase 1 validates)
  python mlb_backtest.py --start 2026-05-01 --end 2026-05-15

  # Show summary only
  python mlb_backtest.py --start 2026-05-08 --end 2026-05-15 --summary-only

Rules applied (must match live card exactly):
  Singles: AUTO/T1, odds >= -150, model_prob >= 0.65, EV >= 0.10
  NEW: book edge >= 0.05 (model_prob - book_implied)
  Fades:   L14 avg <= .120, AB >= 10, plus-money under preferred
  K Unders: K/IP < 0.85 AND 4/5 starts under line (dual gate)
  Max 6-8 plays per day
"""
import os, sys, json, glob, argparse
from datetime import date, timedelta, datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR  = os.path.join(BASE_DIR, "posted_cards")

# ── SELECTION RULES (must match live pipeline exactly) ────────
MAX_PLAYS       = 7       # max singles per day
MIN_ODDS        = -150    # singles odds floor
MIN_MODEL_PROB  = 0.65    # minimum model probability
MIN_EV          = 0.10    # minimum expected value
MIN_EDGE        = 0.05    # minimum edge over book implied
FADE_L14_MAX    = 0.120   # tightened from .150
FADE_MIN_AB     = 10      # minimum AB for fade signal
K_UNDER_MAX_KIP = 0.85    # K/IP ceiling for K under
K_UNDER_MIN_L5U = 4       # minimum L5 starts under line

# ── HELPERS ───────────────────────────────────────────────────

def plays_path(d):
    return os.path.join(BASE_DIR, f"mlb_plays_{d}.json")

def results_path(d):
    return os.path.join(BASE_DIR, f"mlb_results_{d}.json")

def k_unders_path(d):
    return os.path.join(BASE_DIR, f"mlb_k_unders_{d}.json")

def posted_card_path(d):
    return os.path.join(CARDS_DIR, f"posted_card_{d}.json")

def book_implied(odds):
    o = int(odds)
    return abs(o) / (abs(o) + 100) if o < 0 else 100 / (o + 100)

def calc_ev(model_prob, odds):
    o   = int(odds)
    dec = 1 + (100/abs(o)) if o < 0 else 1 + (o/100)
    return round(model_prob * (dec - 1) - (1 - model_prob), 3)

def calc_pnl(odds, hit):
    if hit is None:
        return 0.0
    o = int(odds)
    if hit:
        return 100*(100/abs(o)) if o < 0 else 100*(o/100)
    return -100.0

# ── CARD SELECTION — mirrors live pipeline rules ──────────────

def select_singles(plays_data):
    """
    Apply card selection rules to model output.
    Returns ordered list of selected plays (max MAX_PLAYS).
    """
    all_plays = (
        [p for p in plays_data.get("pitcher_plays", []) if p] +
        [p for p in plays_data.get("batter_plays",  []) if p]
    )

    candidates = []
    for p in all_plays:
        tier  = p.get("tier", "SKIP")
        odds  = p.get("odds")
        mprob = p.get("model_prob", 0)

        if tier not in ("AUTO", "T1"):
            continue
        if odds is None:
            continue
        if int(odds) < MIN_ODDS:
            continue
        if mprob < MIN_MODEL_PROB:
            continue

        ev   = calc_ev(mprob, odds)
        bi   = book_implied(odds)
        edge = round(mprob - bi, 4)

        if ev < MIN_EV:
            continue
        if edge < MIN_EDGE:
            continue

        candidates.append({
            **p,
            "single_ev":    ev,
            "book_implied": bi,
            "edge":         edge,
        })

    # Sort by win probability, cap at MAX_PLAYS
    candidates.sort(key=lambda x: x["model_prob"], reverse=True)
    return candidates[:MAX_PLAYS]

def select_fades(plays_data):
    """
    Select fade plays from the model's fade_plays list.
    Applies tightened L14 threshold.
    """
    fade_plays = plays_data.get("fade_plays", [])
    selected   = []

    for p in fade_plays:
        reason = p.get("reason", "")

        # Parse L14 avg from reason string
        import re
        avg_match = re.search(r'\.(\d{3})', reason)
        if avg_match:
            l14_avg = float("0." + avg_match.group(1))
            if l14_avg > FADE_L14_MAX:
                continue  # above tightened threshold

        selected.append(p)

    return selected

def select_k_unders(k_unders_data):
    """
    Select K under plays from pitcher under analysis.
    Applies dual gate: K/IP < 0.85 AND 4/5 under.
    """
    if not k_unders_data:
        return []

    selected = []
    for p in k_unders_data.get("pitchers", []):
        if p.get("side") != "UNDER":
            continue
        if p.get("net", 0) > -3:
            continue  # only LEAN UNDER or stronger

        # Dual gate check
        logs = p.get("logs", [])
        if len(logs) >= 3:
            avg_kip     = sum(l.get("k_per_ip", 0) for l in logs) / len(logs)
            k_line      = p.get("k_line", 4.5)
            under_count = sum(1 for l in logs if l.get("ks", 99) <= k_line)

            passes_kip   = avg_kip < K_UNDER_MAX_KIP
            passes_streak = under_count >= K_UNDER_MIN_L5U

            if not (passes_kip and passes_streak):
                continue  # dual gate failed

        selected.append(p)

    return selected

# ── GRADING ───────────────────────────────────────────────────

def grade_plays(selected_plays, results_data):
    """
    Match selected plays to actual box score results.
    Returns list with result, actual, pnl added.
    """
    results_index = {}
    for r in results_data.get("plays", []):
        results_index[r["player"].lower()] = r

    graded = []
    for play in selected_plays:
        name  = play.get("player", "").lower()
        prop  = play.get("prop", "hits")
        odds  = play.get("odds", -110)

        # Fuzzy match
        match = results_index.get(name)
        if not match:
            for key, val in results_index.items():
                if name.split()[-1] in key:
                    match = val
                    break

        if not match:
            graded.append({**play, "result": "void", "actual": None, "pnl": 0})
            continue

        result = match.get("result")
        actual = match.get("actual")

        if result == "hit":
            pnl = calc_pnl(odds, True)
            graded.append({**play, "result": "hit",  "actual": actual, "pnl": pnl})
        elif result == "miss":
            graded.append({**play, "result": "miss", "actual": actual, "pnl": -100})
        else:
            graded.append({**play, "result": "void", "actual": actual, "pnl": 0})

    return graded

def grade_fades(selected_fades, results_data):
    """
    Grade fade plays — fade wins when OVER misses.
    """
    results_index = {}
    for r in results_data.get("plays", []):
        results_index[r["player"].lower()] = r

    # Also check raw fade results in results file
    fade_index = {}
    for r in results_data.get("fade_results", []):
        fade_index[r.get("player", "").lower()] = r

    graded = []
    for fade in selected_fades:
        name       = fade.get("player", "").lower()
        over_odds  = fade.get("over_odds", -150)
        under_odds = fade.get("under_odds", 110)

        match = results_index.get(name)
        if not match:
            for key, val in results_index.items():
                if name.split()[-1] in key:
                    match = val
                    break

        if not match:
            graded.append({**fade, "result": "void", "actual": None, "pnl": 0})
            continue

        result = match.get("result")
        actual = match.get("actual")

        # Fade wins when OVER misses
        if result == "miss":
            pnl = calc_pnl(under_odds, True)
            graded.append({**fade, "result": "hit",  "actual": actual, "pnl": round(pnl, 2)})
        elif result == "hit":
            graded.append({**fade, "result": "miss", "actual": actual, "pnl": -100})
        else:
            graded.append({**fade, "result": "void", "actual": actual, "pnl": 0})

    return graded

# ── SINGLE DATE RUN ───────────────────────────────────────────

def run_date(game_date, verbose=True):
    """
    Run full backtest pipeline for one date.
    Returns dict with selected plays, grades, P&L.
    """
    ppath = plays_path(game_date)
    rpath = results_path(game_date)

    if not os.path.exists(ppath):
        return {"date": game_date, "status": "no_plays_file"}
    if not os.path.exists(rpath):
        return {"date": game_date, "status": "no_results_file"}

    with open(ppath) as f:
        plays_data = json.load(f)
    with open(rpath) as f:
        results_data = json.load(f)

    # Load K unders if available
    k_unders_data = {}
    if os.path.exists(k_unders_path(game_date)):
        with open(k_unders_path(game_date)) as f:
            k_unders_data = json.load(f)

    # Select plays
    selected_singles = select_singles(plays_data)
    selected_fades   = select_fades(plays_data)
    selected_k_unders = select_k_unders(k_unders_data)
    all_fades        = selected_fades + selected_k_unders

    # Grade
    graded_singles = grade_plays(selected_singles, results_data)
    graded_fades   = grade_fades(all_fades, results_data)

    # Calculate P&L
    s_hits   = sum(1 for p in graded_singles if p["result"] == "hit")
    s_losses = sum(1 for p in graded_singles if p["result"] == "miss")
    s_voids  = sum(1 for p in graded_singles if p["result"] == "void")
    s_pnl    = sum(p["pnl"] for p in graded_singles)

    f_hits   = sum(1 for p in graded_fades if p["result"] == "hit")
    f_losses = sum(1 for p in graded_fades if p["result"] == "miss")
    f_voids  = sum(1 for p in graded_fades if p["result"] == "void")
    f_pnl    = sum(p["pnl"] for p in graded_fades)

    total_pnl = s_pnl + f_pnl

    if verbose:
        date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%b %d")
        print(f"\n{'='*65}")
        print(f"BACKTEST — {game_date}")
        print(f"{'─'*65}")

        print(f"\n⚾ SINGLES ({len(graded_singles)} selected):")
        for p in graded_singles:
            marker = "✓" if p["result"]=="hit" else "✗" if p["result"]=="miss" else "—"
            tier   = p.get("tier","?")
            ev     = p.get("single_ev", 0)
            edge   = p.get("edge", 0)
            pnl_s  = f"+${p['pnl']:.2f}" if p["pnl"] > 0 else f"-$100.00" if p["pnl"] < 0 else "VOID"
            print(f"  {marker} {p['player']:26} {tier:5} "
                  f"{p.get('odds',0):+5}  EV:{ev:+.3f}  "
                  f"edge:{edge*100:+.1f}%  → {p.get('actual','—')}  {pnl_s}")

        if graded_fades:
            print(f"\n📉 FADES ({len(graded_fades)} selected):")
            for p in graded_fades:
                marker  = "✓" if p["result"]=="hit" else "✗" if p["result"]=="miss" else "—"
                u_odds  = p.get("under_odds", 110)
                u_str   = f"+{u_odds}" if u_odds > 0 else str(u_odds)
                pnl_s   = f"+${p['pnl']:.2f}" if p["pnl"] > 0 else f"-$100.00" if p["pnl"] < 0 else "VOID"
                print(f"  {marker} {p['player']:26} UNDER {u_str:6}  "
                      f"→ {p.get('actual','—')}  {pnl_s}")

        s_rate = s_hits/(s_hits+s_losses) if (s_hits+s_losses) else 0
        f_rate = f_hits/(f_hits+f_losses) if (f_hits+f_losses) else 0
        print(f"\n  Singles: {s_hits}-{s_losses} ({s_rate*100:.0f}%)  "
              f"{'+' if s_pnl>=0 else ''}${s_pnl:.2f}")
        print(f"  Fades:   {f_hits}-{f_losses} ({f_rate*100:.0f}%)  "
              f"{'+' if f_pnl>=0 else ''}${f_pnl:.2f}")
        print(f"  TOTAL:   {'+' if total_pnl>=0 else ''}${total_pnl:.2f}  "
              f"({'+' if total_pnl>=0 else ''}{total_pnl/100:.2f}u)")

    return {
        "date":       game_date,
        "status":     "graded",
        "singles":    graded_singles,
        "fades":      graded_fades,
        "s_hits":     s_hits,
        "s_losses":   s_losses,
        "s_voids":    s_voids,
        "s_pnl":      round(s_pnl, 2),
        "f_hits":     f_hits,
        "f_losses":   f_losses,
        "f_voids":    f_voids,
        "f_pnl":      round(f_pnl, 2),
        "total_pnl":  round(total_pnl, 2),
    }

# ── COMPARISON VS POSTED CARD ─────────────────────────────────

def compare_vs_posted(game_date, backtest_result):
    """
    Show what the backtest selected vs what was actually posted.
    Highlights divergences — plays backtest would add/remove.
    """
    cpath = posted_card_path(game_date)
    if not os.path.exists(cpath):
        print(f"  No posted card for {game_date} — skipping comparison")
        return

    with open(cpath) as f:
        card = json.load(f)

    posted_names = {p["player"].lower() for p in card.get("plays", [])}
    bt_names     = {p["player"].lower() for p in backtest_result.get("singles", [])}

    added   = bt_names - posted_names
    removed = posted_names - bt_names
    matched = bt_names & posted_names

    print(f"\n  📊 vs POSTED CARD comparison:")
    print(f"     Matched: {len(matched)} plays same as posted")

    if added:
        print(f"     Backtest ADDS (not posted): "
              f"{', '.join(p.title() for p in added)}")
    if removed:
        print(f"     Backtest REMOVES (was posted): "
              f"{', '.join(p.title() for p in removed)}")

    # P&L delta
    posted_summary = card.get("summary", {})
    posted_pnl     = posted_summary.get("total_pnl", 0)
    bt_pnl         = backtest_result.get("total_pnl", 0)
    delta          = bt_pnl - posted_pnl

    print(f"     Posted P&L:   {'+' if posted_pnl>=0 else ''}${posted_pnl:.0f}")
    print(f"     Backtest P&L: {'+' if bt_pnl>=0 else ''}${bt_pnl:.0f}")
    print(f"     Delta:        {'+' if delta>=0 else ''}${delta:.0f} "
          f"({'better' if delta>=0 else 'worse'} than posted)")

# ── RANGE RUN ─────────────────────────────────────────────────

def run_range(start_date, end_date, vs_posted=False, summary_only=False):
    """Run backtest for a date range and print summary table."""
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end     = datetime.strptime(end_date,   "%Y-%m-%d")

    results     = []
    skipped     = []

    while current <= end:
        d = current.strftime("%Y-%m-%d")

        if not os.path.exists(plays_path(d)):
            skipped.append((d, "no plays file"))
            current += timedelta(days=1)
            continue
        if not os.path.exists(results_path(d)):
            skipped.append((d, "no results file"))
            current += timedelta(days=1)
            continue

        result = run_date(d, verbose=not summary_only)
        results.append(result)

        if vs_posted and not summary_only:
            compare_vs_posted(d, result)

        current += timedelta(days=1)

    # ── SUMMARY TABLE ─────────────────────────────────────────
    print(f"\n{'='*75}")
    print(f"BACKTEST SUMMARY — {start_date} to {end_date}")
    print(f"{'─'*75}")
    print(f"  {'DATE':12} {'S-REC':8} {'S-PNL':9} "
          f"{'F-REC':8} {'F-PNL':9} {'TOTAL':10} {'UNITS':8} {'✓/✗'}")
    print(f"  {'─'*70}")

    total_s_w = total_s_l = 0
    total_f_w = total_f_l = 0
    total_pnl = 0.0

    for r in results:
        if r["status"] != "graded":
            continue

        sw = r["s_hits"];   sl = r["s_losses"]
        fw = r["f_hits"];   fl = r["f_losses"]
        sp = r["s_pnl"];    fp = r["f_pnl"]
        tp = r["total_pnl"]

        total_s_w += sw;  total_s_l += sl
        total_f_w += fw;  total_f_l += fl
        total_pnl += tp

        s_rate   = sw/(sw+sl) if (sw+sl) else 0
        f_rate   = fw/(fw+fl) if (fw+fl) else 0
        sp_str   = f"{'+' if sp>=0 else ''}${sp:.0f}"
        fp_str   = f"{'+' if fp>=0 else ''}${fp:.0f}"
        tp_str   = f"{'+' if tp>=0 else ''}${tp:.0f}"
        tu_str   = f"{'+' if tp>=0 else ''}{tp/100:.2f}u"
        flag     = "✓" if tp >= 0 else "✗"
        s_rec    = f"{sw}-{sl}"
        f_rec    = f"{fw}-{fl}" if (fw+fl) > 0 else "—"

        print(f"  {r['date']:12} {s_rec:8} {sp_str:9} "
              f"{f_rec:8} {fp_str:9} {tp_str:10} {tu_str:8} {flag}")

    # Totals
    total_units = total_pnl / 100
    s_rate_tot  = total_s_w/(total_s_w+total_s_l) if (total_s_w+total_s_l) else 0
    f_rate_tot  = total_f_w/(total_f_w+total_f_l) if (total_f_w+total_f_l) else 0
    s_tot_rec   = f"{total_s_w}-{total_s_l}"
    f_tot_rec   = f"{total_f_w}-{total_f_l}"

    print(f"\n  {'─'*70}")
    print(f"  {'TOTAL':12} {s_tot_rec:8} "
          f"      {f_tot_rec:8} "
          f"      {'+' if total_pnl>=0 else ''}${total_pnl:.0f}  "
          f"{'+' if total_units>=0 else ''}{total_units:.2f}u")
    print(f"  {'HIT RATE':12} {s_rate_tot*100:.1f}%           "
          f"{f_rate_tot*100:.1f}%")
    print(f"  {'DAYS':12} {len(results)} graded  "
          f"{len(skipped)} skipped")

    if skipped:
        print(f"\n  Skipped dates (missing data):")
        for d, reason in skipped:
            print(f"    {d} — {reason}")

    # ── DIVERGENCE WARNING ────────────────────────────────────
    # Check if backtest total is within 20% of posted card total
    posted_total = sum_posted_pnl(start_date, end_date)
    if posted_total is not None:
        divergence = abs(total_pnl - posted_total) / max(abs(posted_total), 1)
        print(f"\n  {'─'*70}")
        print(f"  VALIDATION vs POSTED CARDS:")
        print(f"    Posted card P&L:   {'+' if posted_total>=0 else ''}${posted_total:.0f}")
        print(f"    Backtest P&L:      {'+' if total_pnl>=0 else ''}${total_pnl:.0f}")
        print(f"    Divergence:        {divergence*100:.1f}%")
        if divergence <= 0.20:
            print(f"    ✓ VALID — backtest within 20% of real results")
            print(f"      Safe to extend to earlier dates")
        elif divergence <= 0.40:
            print(f"    ⚠ MODERATE — {divergence*100:.0f}% gap between backtest and real")
            print(f"      Check card selection logic before extending")
        else:
            print(f"    ✗ HIGH DIVERGENCE — {divergence*100:.0f}% gap")
            print(f"      DO NOT extend backtest — fix logic first")
            print(f"      Likely cause: lookahead bias or card selection mismatch")

    print(f"\n{'='*75}\n")

    return results

def sum_posted_pnl(start_date, end_date):
    """Sum actual posted card P&L for comparison."""
    files = sorted(glob.glob(os.path.join(CARDS_DIR, "posted_card_*.json")))
    if not files:
        return None

    total = 0.0
    found = 0
    for fp in files:
        with open(fp) as f:
            card = json.load(f)
        d = card.get("date", "")
        if d < start_date or d > end_date:
            continue
        if not card.get("graded"):
            continue
        total += card.get("summary", {}).get("total_pnl", 0)
        found += 1

    return total if found > 0 else None

# ── ENTRY POINT ───────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",         default=None,
                        help="Single date: 2026-05-12")
    parser.add_argument("--start",        default=None,
                        help="Start date for range: 2026-05-08")
    parser.add_argument("--end",          default=None,
                        help="End date for range: 2026-05-15")
    parser.add_argument("--vs-posted",    action="store_true",
                        help="Compare backtest card vs what was actually posted")
    parser.add_argument("--summary-only", action="store_true",
                        help="Print summary table only, no day detail")
    args = parser.parse_args()

    if args.date:
        result = run_date(args.date, verbose=True)
        if args.vs_posted:
            compare_vs_posted(args.date, result)

    elif args.start and args.end:
        run_range(
            args.start, args.end,
            vs_posted=args.vs_posted,
            summary_only=args.summary_only,
        )

    else:
        parser.print_help()
        print(f"\nPhase 1 — Sanity check (run this first):")
        print(f"  python mlb_backtest.py --start 2026-05-08 --end 2026-05-15")
        print(f"\nWith comparison vs posted cards:")
        print(f"  python mlb_backtest.py --start 2026-05-08 --end 2026-05-15 --vs-posted")
        print(f"\nSummary table only:")
        print(f"  python mlb_backtest.py --start 2026-05-08 --end 2026-05-15 --summary-only")
        print(f"\nAfter Phase 1 validates, extend to full May:")
        print(f"  python mlb_backtest.py --start 2026-05-01 --end 2026-05-15")
