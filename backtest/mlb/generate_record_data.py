#!/usr/bin/env python3
"""
generate_record_data.py
=======================
Generates cfb-app/src/results_data.js from the graded posted_card_*.json files.

This KILLS manual entry of the RESULTS and FADE_RESULTS arrays in
RecordTracker.jsx. The posted cards are the single source of truth for what
was actually bet and how it graded.

WHAT THIS DOES
  - Reads every posted_cards/posted_card_YYYY-MM-DD.json
  - Emits RESULTS      (singles: pitchers + batters)
  - Emits FADE_RESULTS (cold-bat / K-under fades)
  - Emits PARLAY_RESULTS (currently always [] per card — parlays suspended)
  - RL_RESULTS is NOT generated here. Run lines can't be auto-graded from any
    existing file (no team final scores are stored). RL stays hand-maintained
    in rl_data.js — see note at bottom.

WHY pnl IS TRUSTED FOR FADES
  The posted card does not store the UNDER odds actually bet (odds_under is
  always null; the grader hardcodes +110 on a winning fade). So for fades we
  emit odds:110 on a win purely so RecordTracker's Number(f.odds) math
  reproduces the grader's pnl. A losing fade is a flat -100 regardless of odds.
  For SINGLES the real odds ARE stored, so those reconcile exactly.

USAGE
  python generate_record_data.py
  # optional flags:
  python generate_record_data.py --cards-dir "C:/Users/tyose/edge-index/backtest/mlb/posted_cards" \
                                 --out "C:/Users/tyose/edge-index/cfb-app/src/results_data.js"

  Add to morning_routine.py STEP 6 (after the card is graded) so the app data
  regenerates automatically every day.
"""

import argparse
import glob
import json
import os
import re
from datetime import datetime

# ---- result -> hit mapping -------------------------------------------------
# Card "result" field is one of: "hit", "miss", "void", or null (ungraded).
RESULT_TO_HIT = {
    "hit": "true",     # JS true
    "miss": "false",   # JS false
    "void": '"void"',  # JS "void"
    None: "null",      # JS null (pending / ungraded)
}

# prop name -> short display token
PROP_SHORT = {
    "strikeouts": "K",
    "hits": "H",
    "total_bases": "TB",
}


def js_str(s):
    """Safely render a Python string as a JS double-quoted string literal."""
    if s is None:
        return '""'
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def js_num_or_null(v):
    """Render a number (int/float/str-number) as a JS numeric literal, or null."""
    if v is None or v == "":
        return "null"
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)
    except (TypeError, ValueError):
        return "null"


def prop_display(prop, line, over_under):
    """Build a display string like 'K OVER 5.5' or 'H OVER 0.5' or 'TB OVER 1.5'."""
    short = PROP_SHORT.get(prop, (prop or "H").upper())
    if line is None:
        line = 0.5 if prop == "hits" else (1.5 if prop == "total_bases" else 0.5)
    # trim trailing .0 -> keep one decimal like the existing file (4.5, 0.5, 1.5)
    line_s = ("%g" % float(line))
    return f"{short} {over_under.upper()} {line_s}"


def hit_from_result(result):
    return RESULT_TO_HIT.get(result, "null")


def note_for_single(p):
    """Human-readable note WITHOUT a dollar figure (calcPnl owns the money)."""
    res = p.get("result")
    actual = p.get("actual")
    prop = p.get("prop")
    if res == "void":
        return "DNP / not in box scores \u2014 VOID"
    if res is None:
        return "Pending"
    unit = "Ks" if prop == "strikeouts" else ("TB" if prop == "total_bases" else "hits")
    verb = "WIN" if res == "hit" else "LOSS"
    return f"{actual} {unit} \u2014 {verb}"


def note_for_fade(f):
    res = f.get("result")
    actual = f.get("actual")
    if res == "void":
        return "No result found \u2014 VOID"
    if res is None:
        return "Pending"
    if res == "hit":
        return "0 hits \u2014 WIN"
    return (f"{actual} hit(s) \u2014 LOSS" if actual is not None else "Hit \u2014 LOSS")


def fade_odds_for_render(f):
    """
    RecordTracker computes fade P&L from f.odds. The card doesn't store the real
    under-odds. On a WIN, emit the odds that reproduce the grader's pnl
    (pnl/100*100 -> implied american). On a loss/void, +110 is a harmless
    placeholder since loss is flat -100 and void is excluded.
    """
    if f.get("result") == "hit":
        pnl = f.get("pnl")
        if pnl:
            # american odds from profit on a 100 stake
            return int(round(pnl))  # +110 profit -> +110 odds; +127 -> +127
    return 110


def build_single(p):
    over_under = p.get("type", "over")  # 'over' for singles
    prop = prop_display(p.get("prop"), p.get("line"), over_under)
    return {
        "player": js_str(p.get("player")),
        "prop": js_str(prop),
        "odds": js_num_or_null(p.get("odds")),
        "tier": js_str(p.get("tier")),
        "hit": hit_from_result(p.get("result")),
        "actual": js_num_or_null(p.get("actual")) if p.get("actual") is not None else "null",
        "note": js_str(note_for_single(p)),
        "hit_prob": js_num_or_null(p.get("model_prob")),
    }


def build_fade(f):
    # Build the prop display the renderer expects. For an h_under fade the
    # renderer only checks .includes("K"); give it a real string so it never
    # crashes on null.
    ftype = f.get("fade_type", "h_under")
    if (f.get("prop") == "strikeouts"):
        prop = prop_display("strikeouts", f.get("line"), "under")
    else:
        prop = "H UNDER 0.5"
    team = f.get("home") or ""
    return {
        "player": js_str(f.get("player")),
        "team": js_str(team),
        "prop": js_str(prop),
        "odds": js_num_or_null(fade_odds_for_render(f)),
        "l14": js_str(""),  # not stored in card; cosmetic
        "hit": hit_from_result(f.get("result")),
        "actual": js_num_or_null(f.get("actual")) if f.get("actual") is not None else "null",
        "note": js_str(note_for_fade(f)),
    }


def render_obj(obj, indent):
    pad = " " * indent
    parts = [f"{k}:{v}" for k, v in obj.items()]
    return pad + "{" + ", ".join(parts) + "}"


# Markers used in --inject mode. The generator replaces everything BETWEEN
# these two lines inside RecordTracker.jsx, leaving the rest of the file alone.
INJECT_BEGIN = "// >>> AUTO-GENERATED DATA BEGIN — do not edit between markers"
INJECT_END = "// <<< AUTO-GENERATED DATA END"


def build_arrays_text(results_days, fade_days, exported, prefix=""):
    """Render the RESULTS + FADE_RESULTS arrays as JS.
    exported=True -> 'export const' (module mode).
    exported=False -> 'const'        (inline/inject mode).
    prefix -> name prefix, e.g. 'GENERATED_' for merge-mode inject."""
    kw = "export const" if exported else "const"
    rname = f"{prefix}RESULTS"
    fname = f"{prefix}FADE_RESULTS"
    lines = []
    lines.append(f"{kw} {rname} = [")
    for date, plays in results_days:
        lines.append("  {")
        lines.append(f'    date: "{date}",')
        lines.append('    sport: "MLB",')
        lines.append("    plays: [")
        for p in plays:
            lines.append(render_obj(p, 6) + ",")
        lines.append("    ],")
        lines.append("    parlays: [],")
        lines.append("  },")
    lines.append("];")
    lines.append("")
    lines.append(f"{kw} {fname} = [")
    for date, fades in fade_days:
        lines.append("  {")
        lines.append(f'    date: "{date}",')
        lines.append('    sport: "MLB",')
        lines.append("    fades: [")
        for f in fades:
            lines.append(render_obj(f, 6) + ",")
        lines.append("    ],")
        lines.append("  },")
    lines.append("];")
    return "\n".join(lines)


def inject_into_jsx(jsx_path, arrays_text):
    with open(jsx_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    if INJECT_BEGIN not in src or INJECT_END not in src:
        raise SystemExit(
            "Markers not found in JSX. Add these two lines where the data should live:\n"
            f"  {INJECT_BEGIN}\n  {INJECT_END}"
        )
    pre, rest = src.split(INJECT_BEGIN, 1)
    _, post = rest.split(INJECT_END, 1)
    stamp = f"// Generated: {datetime.now().isoformat(timespec='seconds')}  (source: posted_cards/)"
    new = (pre + INJECT_BEGIN + "\n" + stamp + "\n" + arrays_text + "\n"
           + INJECT_END + post)
    with open(jsx_path, "w", encoding="utf-8") as fh:
        fh.write(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards-dir", default="posted_cards",
                    help="directory containing posted_card_*.json")
    ap.add_argument("--out", default="results_data.js",
                    help="output JS module path (module mode)")
    ap.add_argument("--inject", default=None,
                    help="path to RecordTracker.jsx to inject data into "
                         "(single-file mode). Overrides --out when set.")
    args = ap.parse_args()

    pattern = os.path.join(args.cards_dir, "posted_card_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"No posted cards found at {pattern}")

    # newest first to match the existing arrays' ordering
    cards = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as fh:
            cards.append(json.load(fh))
    cards.sort(key=lambda c: c.get("date", ""), reverse=True)

    results_days = []
    fade_days = []
    for c in cards:
        date = c.get("date")
        plays = c.get("plays", []) or []
        fades = c.get("fades", []) or []

        play_objs = [build_single(p) for p in plays]
        results_days.append((date, play_objs))

        fade_objs = [build_fade(f) for f in fades]
        fade_days.append((date, fade_objs))

    if args.inject:
        arrays_text = build_arrays_text(results_days, fade_days,
                                        exported=False, prefix="")
        inject_into_jsx(args.inject, arrays_text)
        n_play = sum(len(p) for _, p in results_days)
        n_fade = sum(len(f) for _, f in fade_days)
        print(f"Injected into {args.inject}")
        print(f"  {len(results_days)} days  |  {n_play} singles  |  {n_fade} fades")
        return

    arrays_text = build_arrays_text(results_days, fade_days, exported=True)
    header = (
        "// AUTO-GENERATED by generate_record_data.py \u2014 DO NOT EDIT BY HAND.\n"
        f"// Generated: {datetime.now().isoformat(timespec='seconds')}\n"
        "// Source of truth: posted_cards/posted_card_*.json\n\n"
    )
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(header + arrays_text + "\n")

    n_play = sum(len(p) for _, p in results_days)
    n_fade = sum(len(f) for _, f in fade_days)
    print(f"Wrote {args.out}")
    print(f"  {len(results_days)} days  |  {n_play} singles  |  {n_fade} fades")


if __name__ == "__main__":
    main()
