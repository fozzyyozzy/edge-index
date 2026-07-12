#!/usr/bin/env python3
"""
extract_legacy.py  (RUN ONCE)
=============================
Pulls the hand-entered history that PREDATES the posted-card JSON files out of
the original RecordTracker.jsx and freezes it into legacy_data.js.

Why: the generator (generate_record_data.py) can only reproduce days that have a
posted_card_*.json. Everything before the first posted card (here: before
2026-05-23) exists ONLY as hand-typed data in the original JSX. We snapshot it
once, verbatim, so it's preserved forever and never regenerated.

The cutoff is the earliest date for which a posted card exists. Days on/after the
cutoff are owned by the generator; days before it are owned by legacy_data.js.

After running once, you typically never run this again.
"""
import argparse
import re


def extract_array(src, name):
    """Return the text of `const NAME = [ ... ];` (without the const/closing)."""
    start = src.index(f"const {name} = [")
    body_start = src.index("[", start)
    # walk brackets to find the matching close
    depth = 0
    i = body_start
    while i < len(src):
        c = src[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return src[body_start + 1:i]  # inside the outer [ ]
        i += 1
    raise ValueError(f"Unbalanced array for {name}")


def split_day_objects(arr_text):
    """Split a top-level array of {..} day objects into individual object strings."""
    objs = []
    depth = 0
    cur = []
    in_obj = False
    for ch in arr_text:
        if ch == "{":
            if depth == 0:
                in_obj = True
                cur = []
            depth += 1
        if in_obj:
            cur.append(ch)
        if ch == "}":
            depth -= 1
            if depth == 0 and in_obj:
                objs.append("".join(cur))
                in_obj = False
    return objs


def date_of(obj_text):
    m = re.search(r'date:\s*"([\d-]+)"', obj_text)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True,
                    help="original RecordTracker.jsx containing hand-entered history")
    ap.add_argument("--cutoff", default="2026-05-23",
                    help="first date owned by the generator; days BEFORE this are legacy")
    ap.add_argument("--out", default="legacy_data.js")
    args = ap.parse_args()

    src = open(args.src, "r", encoding="utf-8").read()

    results = split_day_objects(extract_array(src, "RESULTS"))
    fades = split_day_objects(extract_array(src, "FADE_RESULTS"))

    legacy_results = [o for o in results if date_of(o) and date_of(o) < args.cutoff]
    legacy_fades = [o for o in fades if date_of(o) and date_of(o) < args.cutoff]

    # newest-first ordering (same as the live arrays)
    legacy_results.sort(key=date_of, reverse=True)
    legacy_fades.sort(key=date_of, reverse=True)

    out = []
    out.append("// FROZEN LEGACY DATA — hand-entered history predating posted-card JSON.")
    out.append(f"// Cutoff: days strictly before {args.cutoff}. Extracted once from the")
    out.append("// original RecordTracker.jsx. Safe to edit by hand if you ever correct a")
    out.append("// historical box score; the generator never touches this file.")
    out.append("")
    out.append("export const LEGACY_RESULTS = [")
    for o in legacy_results:
        out.append("  " + o.strip().rstrip(",") + ",")
    out.append("];")
    out.append("")
    out.append("export const LEGACY_FADE_RESULTS = [")
    for o in legacy_fades:
        out.append("  " + o.strip().rstrip(",") + ",")
    out.append("];")
    out.append("")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))

    print(f"Wrote {args.out}")
    print(f"  legacy singles days: {len(legacy_results)} "
          f"({date_of(legacy_results[-1])} .. {date_of(legacy_results[0])})")
    print(f"  legacy fade days:    {len(legacy_fades)} "
          f"({date_of(legacy_fades[-1])} .. {date_of(legacy_fades[0])})")


if __name__ == "__main__":
    main()
