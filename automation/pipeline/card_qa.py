"""
card_qa.py — checks a built card against every house rule (build_card_json.py R1–R11, the price cap, one leg per game)
and the availability snapshot, independently of the code that built it. card.yml runs it after the card is built:
pass -> the checklist goes into the newsletter draft issue; fail -> nothing publishes and a "CARD FAILED QA" issue opens.

  python pipeline/card_qa.py --season 2026 --week 4 --slate sun [--out qa.md]     exit 0 = pass, 1 = fail

Inputs: cards/card_*.json, cards/legs_*.json (grades, spreads, hold reasons), cards/availability_*.json.
"""
import argparse, json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import norm_name, P
import availability

SINGLE_GAME = {"tnf", "mnf", "snf"}
GRADE_OK = {"A+", "A", "A-", "B", "C"}
GRADE_RANK = {"A+": 5, "A": 4, "A-": 3, "B": 2, "C": 1}
MAX_LEG_JUICE, MIN_EDGE_PTS, TARGET_DEC = -450, 2.0, 3.0
FLOOR_STAR = lambda l10, l15: l10 >= 0.9 and l15 >= 13 / 15

def dec(o): return 1 + (100 / -o if o < 0 else o / 100)

def check(card, legs=None, avail=None):
    """[(rule, ok, detail)] — one row per rule; detail lists every offending leg/ticket (or a short pass note)."""
    T = card.get("tickets", []); single = card["slate"] in SINGLE_GAME
    rows = []
    def add(rule, bad, ok_note=""):
        rows.append((rule, not bad, "; ".join(bad) if bad else ok_note))
    allegs = [(t, l) for t in T for l in t["legs"]]
    tag = lambda t, l: f"{t['name']} {l['player']} {l['rung']:g}+ {l['market']}"
    board = {}
    if legs:
        for p in legs["players"]:
            board[(norm_name(p["player"]), p["market"])] = p

    # R1 ticket and leg counts
    bad = []
    if len(T) > (1 if single else 3): bad.append(f"{len(T)} tickets")
    for t in T:
        lo = 2 if single else 3
        if not lo <= len(t["legs"]) <= 4: bad.append(f"{t['name']} has {len(t['legs'])} legs")
    add("R1 3–4 legs per ticket, 2–3 tickets (single game: 1 ticket, 2 legs allowed)", bad, f"{len(T)} tickets")

    # R2 player repeats: floor stars only, max 2 tickets, each ticket shares at most one player
    bad = []
    on = Counter(l["player"] for t in T for l in {x["player"]: x for x in t["legs"]}.values())
    star = {l["player"]: FLOOR_STAR(l["l10"], l["l15"]) for _, l in allegs}
    for p, n in on.items():
        if n > 2 or (n == 2 and not star[p]): bad.append(f"{p} on {n} tickets" + ("" if star[p] else " (not a floor star)"))
    for t in T:
        names = [l["player"] for l in t["legs"]]
        if len(names) != len(set(names)): bad.append(f"{t['name']} repeats a player")
        sh = [n for n in set(names) if on[n] > 1]
        if len(sh) > 1: bad.append(f"{t['name']} shares {len(sh)} players ({', '.join(sorted(sh))})")
    add("R2 repeats are floor stars only, max 2 tickets, one shared player per ticket", bad)

    # R3 qualifying rung
    bad = [tag(t, l) + f" (L10 {l['l10']:.2f} L15 {l['l15']:.2f}" + (f", floor {l['floor_rung']:g}+" if l.get("floor_rung") is not None else "") + ")"
           for t, l in allegs if l["l10"] < 0.8 or l["l15"] < 0.73 or (l.get("floor_rung") is not None and l["rung"] > l["floor_rung"])]
    add("R3 every leg is a qualifying rung (L10 ≥ 80%, L15 ≥ 73%, at or below the floor rung)", bad)

    # R4 edge
    bad = [tag(t, l) + f" edge {l.get('edge_pts')}" for t, l in allegs if l.get("edge_pts") is None or l["edge_pts"] < MIN_EDGE_PTS]
    add("R4 every leg has edge ≥ +2 pts", bad)

    # R5 blowout
    bad = []
    for t, l in allegs:
        sp = (board.get((norm_name(l["player"]), l["market"])) or {}).get("spread")
        if l["market"] in ("pass_att", "pass_cmps") and sp is not None and sp <= -7: bad.append(tag(t, l) + f" (fav by {-sp:g})")
    add("R5 no attempt props for a team favored by 7+", bad, "" if legs else "no legs file: spreads not checked")

    # R6 injury and team-change holds (recomputed from the availability snapshot, not taken from the card)
    bad = []
    for t, l in allegs:
        if avail is not None:
            h = availability.reasons(avail, l["player"], l["market"], l.get("team"))[0]
            if h: bad.append(tag(t, l) + ": " + "; ".join(h))
        row = board.get((norm_name(l["player"]), l["market"]))
        if row and any("team change" in x for r in row["rungs"] for x in r.get("reasons", [])):
            bad.append(tag(t, l) + ": team change")
    note = "" if avail is not None else "no availability snapshot"
    add("R6 no injury, held-by-hand or team-change holds on a ticket", bad, note)

    # R7 single-game slates
    bad = []
    if single:
        for t in T:
            if not t.get("correlated"): bad.append(f"{t['name']} not marked correlated")
            if len(t["legs"]) == 2 and not t.get("reduced"): bad.append(f"{t['name']} has 2 legs but isn't labelled reduced")
    add("R7 single-game slate: one ticket, correlated, a 2-leg ticket is labelled reduced", bad, "" if single else "multi-game slate")

    # R8 payout and label
    bad = []
    for t in T:
        d = 1.0
        for l in t["legs"]: d *= dec(l["odds_est"])
        if abs(d - t["est_payout"]) > 0.011: bad.append(f"{t['name']} payout {t['est_payout']} but legs multiply to {d:.2f}")
        if bool(t.get("reduced")) != (d < TARGET_DEC or len(t["legs"]) == 2): bad.append(f"{t['name']} reduced label wrong")
        if len(t["legs"]) == 4:
            d3 = 1.0
            for l in t["legs"][:3]: d3 *= dec(l["odds_est"])
            if d3 >= TARGET_DEC: bad.append(f"{t['name']} has a 4th leg but 3 legs already paid {d3:.2f}x")
    add("R8 payout matches the legs; 4th leg only to reach +200; reduced label right", bad)

    # R9 grades
    bad = []
    for t, l in allegs:
        if l.get("grade") not in GRADE_OK: bad.append(tag(t, l) + f" grade {l.get('grade')}")
        row = board.get((norm_name(l["player"]), l["market"]))
        if row:
            g = next((r.get("grade") for r in row["rungs"] if float(r["rung"]) == float(l["rung"])), None)
            if g != l.get("grade"): bad.append(tag(t, l) + f" card grade {l.get('grade')} vs Legs board {g}")
    add("R9 every leg graded C or better (and matches the Legs board)", bad)

    # R10 grade first: a C leg only when no B-or-better leg could fill the spot; no third ticket with a C
    bad = []
    used = {l["player"] for _, l in allegs}
    for i, t in enumerate(T):
        cs = [l for l in t["legs"] if l.get("grade") == "C"]
        if cs and i >= 2: bad.append(f"{t['name']} is a third ticket with a C leg")
        if len(t["legs"]) == 4 and t["legs"][3].get("grade") == "C": bad.append(f"{t['name']} has a C 4th leg")
        games = {frozenset([l["team"], l["opp"]]) for l in t["legs"] if l.get("grade") != "C"}
        for l in cs:
            fourth = t["legs"].index(l) == 3                     # a 4th leg must also be a floor price (<= -130)
            alt = [c for c in card.get("candidates", []) if GRADE_RANK.get(c.get("grade"), 0) >= GRADE_RANK["B"]
                   and c["player"] not in used and (single or frozenset([c["team"], c["opp"]]) not in games)
                   and (not fourth or c["odds_est"] <= -130)]
            if alt: bad.append(f"{tag(t, l)} is C while {alt[0]['player']} {alt[0]['rung']:g}+ {alt[0]['market']} ({alt[0]['grade']}) sat unused")
    add("R10 grade first: no C leg while a B-or-better leg fits, never a C 4th leg, no third ticket with a C", bad,
        "" if "candidates" in card else "card has no candidate list: unused-leg check skipped")

    # R11 injury watch: one ticket at most (flags recomputed from the snapshot, plus any on the card)
    bad = []
    for p, n in on.items():
        watch = any(l.get("injury_watch") for _, l in allegs if l["player"] == p)
        if avail is not None:
            l0 = next(l for _, l in allegs if l["player"] == p)
            watch = watch or bool(availability.reasons(avail, p, l0["market"], l0.get("team"))[1])
        if watch and n > 1: bad.append(f"{p} has an injury-watch flag and is on {n} tickets")
    add("R11 injury-watch players on one ticket at most", bad)

    # price cap, one leg per game, published price
    bad = [tag(t, l) + f" {l.get('published_odds')}" for t, l in allegs if (l.get("published_odds") or l["odds_est"]) < MAX_LEG_JUICE]
    add(f"Price cap: no leg worse than {MAX_LEG_JUICE}", bad)
    bad = []
    if not single:
        for t in T:
            g = Counter(frozenset([l["team"], l["opp"]]) for l in t["legs"])
            bad += [f"{t['name']} has {n} legs from {'/'.join(sorted(k))}" for k, n in g.items() if n > 1]
    add("One leg per game per ticket (multi-game slates)", bad, "" if not single else "single-game slate")
    bad = [tag(t, l) for t, l in allegs if l.get("published_odds") != (l["odds_real"] if l.get("odds_real") is not None else l["odds_est"])]
    add("Published price is the real DK price when there is one", bad)

    # data
    bad = []
    if legs is not None and not legs.get("players"):
        bad.append("no DK lines for this slate's games (props not posted yet?): re-run card.yml by hand once they are")
    if not card.get("prices_pulled"): bad.append("card has no prices_pulled")
    if avail is None: bad.append("no availability snapshot")
    else:
        bad += [f"{k}: {v}" for k, v in (avail.get("sources") or {}).items() if str(v).startswith("unavailable")]
    add("Data: slate has DK lines; price pull time recorded; availability sources loaded", bad,
        f"{len(legs['players']) if legs else '?'} player/markets graded, prices {card.get('prices_pulled')}, "
        f"availability {avail.get('fetched_at') if avail else None}")
    return rows

def markdown(card, rows):
    ok = all(r[1] for r in rows)
    out = [f"### Card QA: {'PASS' if ok else 'FAIL'} — week {card['week']} {card['slate']} ({len(card.get('tickets', []))} tickets, prices {card.get('prices_pulled')})", ""]
    for rule, good, detail in rows:
        out.append(f"- [{'x' if good else ' '}] {'' if good else '**FAIL** '}{rule}" + (f" — {detail}" if detail else ""))
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", required=True); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    card = json.load(open(P("cards", f"card_{a.season}_w{a.week}_{a.slate}.json"), encoding="utf-8"))
    lp, vp = P("cards", f"legs_{a.season}_w{a.week}_{a.slate}.json"), availability.path(a.season, a.week, a.slate)
    legs = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else None
    avail = json.load(open(vp, encoding="utf-8")) if os.path.exists(vp) else None
    rows = check(card, legs, avail); md = markdown(card, rows)
    if a.out: open(a.out, "w", encoding="utf-8").write(md)
    sys.stdout.buffer.write(md.encode("utf-8"))
    sys.exit(0 if all(r[1] for r in rows) else 1)

if __name__ == "__main__":
    main()
