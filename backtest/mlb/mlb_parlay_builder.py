"""
Edge Index — MLB Parlay Builder v2
New logic (May 13, 2026):
  SINGLES:  Only plays at -150 or better odds
  PARLAYS:  Pair by juice — best odds with best odds
            Odd number = last 3 become a 3-leg
            Max 1 appearance per player per parlay
            No player appears in more than 2 parlays total

Usage:
  python mlb_parlay_builder.py --date 2026-05-13
"""
import os, sys, json, argparse, itertools
from datetime import date

def to_dec(odds):
    o = int(odds)
    return 1 + (100/abs(o)) if o < 0 else 1 + (o/100)

def to_am(dec):
    if dec >= 2.0:
        return f"+{round((dec-1)*100)}"
    return f"{round(-100/(dec-1))}"

def implied(odds):
    return 1 / to_dec(int(odds))

def calc_ev(model_prob, odds):
    dec = to_dec(int(odds))
    return round(model_prob * (dec-1) - (1-model_prob), 3)

def parlay_ev(legs):
    hit_prob = 1.0
    dec      = 1.0
    for l in legs:
        hit_prob *= l["model_prob"]
        dec      *= to_dec(l["odds"])
    ev = round(hit_prob * (dec-1) - (1-hit_prob), 3)
    return ev, round(hit_prob, 3), round(dec, 3)

def build_singles(plays):
    """
    Singles: WIN PROBABILITY first.
    Only plays at -150 or better odds, EV >= 0.10 as gate.
    Sorted by model_prob descending — we want to WIN, not maximize EV.
    EV and edge are filters, not ranking signals.
    """
    singles = []
    for p in plays:
        if p.get("tier") not in ("AUTO","T1"):
            continue
        odds = int(p.get("odds", -999))
        if odds < -150:
            continue
        if p.get("model_prob", 0) < 0.65:
            continue

        single_ev = calc_ev(p["model_prob"], odds)
        if single_ev < 0.10:
            continue

        # Book edge filter — must have real edge
        bi   = implied(odds)
        edge = round(p["model_prob"] - bi, 4)
        if edge < 0.05:
            continue

        singles.append({**p, "single_ev": single_ev, "edge": edge,
                        "book_implied": bi})

    # ── Sort by WIN PROBABILITY, not EV ───────────────────────
    # EV is a long-run concept — we have 7 plays today.
    # Rank by model_prob: take the plays most likely to win.
    singles.sort(key=lambda x: x["model_prob"], reverse=True)
    return singles

def build_high_edge(plays, singles):
    """
    High Edge tab — outlier value plays.
    These clear ALL thresholds but are too juicy for singles (-150 cutoff).
    Separate category: high risk, transparent, not core picks.

    Thresholds (all must pass):
      - Tier: AUTO or T1
      - model_prob >= 0.70  (higher bar since odds are worse)
      - EV >= 0.25          (meaningful value only)
      - edge >= 0.08        (8%+ over book — real mispricing)
      - streak >= 3         (momentum signal required)
      - Max 3 plays         (discipline — this is bonus, not core)
    """
    # Exclude players already in singles
    singles_names = {s["player"].lower() for s in singles}

    candidates = []
    for p in plays:
        if p.get("tier") not in ("AUTO","T1"):
            continue
        if p["player"].lower() in singles_names:
            continue
        if p.get("model_prob", 0) < 0.70:
            continue
        if p.get("streak", 0) < 3:
            continue

        odds      = int(p.get("odds", -999))
        single_ev = calc_ev(p["model_prob"], odds)
        bi        = implied(odds)
        edge      = round(p["model_prob"] - bi, 4)

        if single_ev < 0.25:
            continue
        if edge < 0.08:
            continue

        candidates.append({**p, "single_ev": single_ev, "edge": edge,
                           "book_implied": bi})

    # High edge plays ranked by edge over book — value IS the point here
    candidates.sort(key=lambda x: x["edge"], reverse=True)
    return candidates[:3]  # max 3

def build_parlays(plays, max_player_appearances=2):
    """
    Parlay logic:
      1. Use all AUTO/T1 plays (regardless of odds) as parlay candidates
      2. Sort by odds (most juiced first — they need parlaying)
      3. Pair sequentially: #1+#2, #3+#4, #5+#6...
      4. If odd count: last 3 form a 3-leg
      5. Max 1 player per parlay, max 2 parlays per player
    """
    candidates = [p for p in plays
                  if p.get("tier") in ("AUTO","T1")
                  and p.get("model_prob", 0) >= 0.70]

    # Sort by odds (most negative = most juiced = needs parlaying most)
    candidates.sort(key=lambda x: int(x["odds"]))

    # Deduplicate players — keep highest model_prob per player
    seen_players = {}
    deduped = []
    for p in candidates:
        name = p["player"]
        if name not in seen_players:
            seen_players[name] = p
            deduped.append(p)
        else:
            if p["model_prob"] > seen_players[name]["model_prob"]:
                idx = deduped.index(seen_players[name])
                deduped[idx] = p
                seen_players[name] = p

    # Build pairs
    parlays      = []
    player_count = {}
    i            = 0

    while i < len(deduped):
        remaining = len(deduped) - i

        # If 3 left and odd — make a 3-leg
        if remaining == 3:
            legs = deduped[i:i+3]
        elif remaining >= 2:
            legs = deduped[i:i+2]
        else:
            break

        # Check player appearance limit
        players = [l["player"] for l in legs]
        if all(player_count.get(pl, 0) < max_player_appearances
               for pl in players):
            ev, hit_prob, dec = parlay_ev(legs)
            am = (dec-1)*100 if dec >= 2.0 else -100/(dec-1)
            parlays.append({
                "legs":     legs,
                "odds":     to_am(dec),
                "decimal":  dec,
                "hit_prob": hit_prob,
                "ev":       ev,
                "n_legs":   len(legs),
                "am_odds":  am,
            })
            for pl in players:
                player_count[pl] = player_count.get(pl, 0) + 1

        i += len(legs)

    return parlays

def print_report(singles, high_edge, parlays, all_plays, game_date):
    print(f"\n{'='*65}")
    print(f"EDGE INDEX MLB — {game_date}")
    print(f"{'='*65}")

    # ── SINGLES — ranked by WIN PROBABILITY ───────────────────
    print(f"\n✅ SINGLE PLAYS — ranked by win probability (-150 or better)")
    print(f"{'─'*65}")
    if singles:
        for p in singles:
            odds    = int(p["odds"])
            mkt     = implied(odds)
            edge    = p.get("edge", p["model_prob"] - mkt)
            prop    = "K" if p["prop"]=="strikeouts" else "H"
            print(f"  {p['player']:26} {prop} OVER {p['line']} "
                  f"({odds:+})  Win:{p['model_prob']*100:.0f}%  "
                  f"Edge:{edge*100:+.1f}%  EV:{p['single_ev']:+.3f}")
    else:
        print("  No plays qualify today")

    # ── HIGH EDGE — value plays, posted transparently ─────────
    if high_edge:
        print(f"\n🎯 HIGH EDGE PLAYS — value/EV focused (higher risk, real edge)")
        print(f"   These clear all thresholds but are too juiced for singles")
        print(f"{'─'*65}")
        for p in high_edge:
            odds  = int(p["odds"])
            prop  = "K" if p["prop"]=="strikeouts" else "H"
            edge  = p.get("edge", 0)
            print(f"  {p['player']:26} {prop} OVER {p['line']} "
                  f"({odds:+})  Win:{p['model_prob']*100:.0f}%  "
                  f"Edge:{edge*100:+.1f}%  EV:{p['single_ev']:+.3f}  "
                  f"Streak:{p.get('streak',0)}g")

    # ── PARLAY ONLY ───────────────────────────────────────────
    parlay_only = [p for p in all_plays
                   if p.get("tier") in ("AUTO","T1")
                   and p.get("model_prob",0) >= 0.70
                   and int(p.get("odds",-999)) < -150]
    parlay_only.sort(key=lambda x: x["model_prob"], reverse=True)

    if parlay_only:
        print(f"\n🔒 PARLAY-ONLY (too juiced for singles)")
        print(f"{'─'*65}")
        for p in parlay_only:
            prop = "K" if p["prop"]=="strikeouts" else "H"
            print(f"  {p['player']:26} {prop} OVER {p['line']} "
                  f"({int(p['odds']):+})  Win:{p['model_prob']*100:.0f}%")

    # ── SUMMARY ───────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"Singles:    {len(singles)} plays  (ranked by win probability)")
    print(f"High Edge:  {len(high_edge)} plays  (ranked by edge over book)")
    if parlays:
        pos_ev = [p for p in parlays if p["ev"] > 0]
        print(f"Parlays:    {len(parlays)} generated | {len(pos_ev)} positive EV")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",       default=date.today().isoformat())
    parser.add_argument("--no-parlays", action="store_true",
                        help="Skip parlays — singles only")
    parser.add_argument("--max-plays",  type=int, default=7,
                        help="Max singles to show (default 7)")
    args = parser.parse_args()

    plays_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_plays_{args.date}.json"
    )

    if not os.path.exists(plays_path):
        print(f"No plays file for {args.date}")
        print(f"Run: python mlb_run_today.py --date {args.date}")
        sys.exit(1)

    with open(plays_path) as f:
        data = json.load(f)

    all_plays = (data.get("pitcher_plays",[]) +
                 data.get("batter_plays", []))
    all_plays = [p for p in all_plays if p]

    print(f"Loaded {len(all_plays)} plays for {args.date}")

    singles    = build_singles(all_plays)
    singles    = singles[:args.max_plays]
    high_edge  = build_high_edge(all_plays, singles)

    if args.no_parlays:
        parlays = []
        print(f"Parlay mode: DISABLED (--no-parlays)")
    else:
        parlays = build_parlays(all_plays)

    print_report(singles, high_edge, parlays, all_plays, args.date)

    # Save to JSON for app use
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_parlays_{args.date}.json"
    )
    with open(out_path, "w") as f:
        json.dump({
            "date":       args.date,
            "singles":    singles,
            "high_edge":  high_edge,
            "parlays":    [{
                "legs":     [{k:v for k,v in l.items()
                              if k != "notes"} for l in p["legs"]],
                "odds":     p["odds"],
                "hit_prob": p["hit_prob"],
                "ev":       p["ev"],
                "n_legs":   p["n_legs"],
            } for p in parlays],
        }, f, indent=2)
    print(f"\nSaved to mlb_parlays_{args.date}.json")
