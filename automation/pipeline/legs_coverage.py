"""
legs_coverage.py — every rung DraftKings offers on a slate must either be on the Legs board or be listed in the legs
file's `omitted` record with the reason grade_legs.py left it off. Anything else is a silently dropped rung.

  python pipeline/legs_coverage.py --season 2026 --week 4 --slate sun          exit 1 if any rung is unexplained

Inputs: lines/ladders_<season>_w<week>.csv (every DK rung, with kickoff), cards/legs_<season>_w<week>_<slate>.json.
"""
import argparse, json, os, sys
from collections import defaultdict
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import norm_name, P
from fetch_lines import slate_of


def check(ladder, legs, slate):
    """[{player, market, rung, odds, reason}] for every DK rung on this slate that isn't on the board.
    reason = the omitted record's reason, or None when nothing explains it (a silent drop)."""
    lad = ladder[ladder.Commence.map(slate_of) == slate] if "Commence" in ladder else ladder
    shown = defaultdict(set)
    for p in legs["players"]:
        shown[(norm_name(p["player"]), p["market"])].update(float(r["rung"]) for r in p["rungs"])
    why = {}
    for o in legs.get("omitted", []):
        for t in o["rungs"]:
            why[(norm_name(o["player"]), o["market"], float(t))] = o["reason"]
    out = []
    for r in lad.drop_duplicates(["Player", "Market", "Rung"]).itertuples():
        k = (norm_name(r.Player), r.Market)
        if float(r.Rung) in shown[k]: continue
        out.append(dict(player=r.Player, market=r.Market, rung=float(r.Rung), odds=int(r.Odds),
                        reason=why.get((*k, float(r.Rung)))))
    return sorted(out, key=lambda g: (g["player"], g["market"], g["rung"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", required=True)
    ap.add_argument("--md", action="store_true", help="one checklist line for card.yml's QA issue")
    a = ap.parse_args()
    ladder = pd.read_csv(P("lines", f"ladders_{a.season}_w{a.week}.csv"))
    legs = json.load(open(P("cards", f"legs_{a.season}_w{a.week}_{a.slate}.json"), encoding="utf-8"))
    gaps = check(ladder, legs, a.slate)
    bad = [g for g in gaps if g["reason"] is None]
    by = defaultdict(int)
    for g in gaps:
        r = g["reason"] or "UNEXPLAINED"
        by["held: only the 3 rungs nearest the DK line shown" if r.startswith("held (") else r] += 1
    if a.md:
        print(f"- [{' ' if bad else 'x'}] {'⚠ **WARNING** ' if bad else ''}Legs board shows every DK rung or records why "
              f"(warning only, doesn't block the card) — {len(gaps) - len(bad)} rungs left off with a reason"
              + (f"; {len(bad)} UNEXPLAINED: " + ", ".join(f"{g['player']} {g['rung']:g}+ {g['market']}" for g in bad[:15]) if bad else ""))
        sys.exit(1 if bad else 0)
    print(f"week {a.week} {a.slate}: {len(gaps)} DK rungs not on the board — " + ", ".join(f"{k}: {v}" for k, v in sorted(by.items())))
    for g in bad: print(f"  UNEXPLAINED {g['player']} {g['market']} {g['rung']:g}+ ({g['odds']:+d})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
