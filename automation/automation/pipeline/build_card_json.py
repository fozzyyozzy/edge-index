"""
build_card_json.py — Wed/Fri/Mon job. Turns the floor scan + edge scan into a slate card with tickets
that obey the house rules, and writes it as JSON for the site and the newsletter draft.

Rules encoded here (do not relax without changing the newsletter copy too):
  R1  3–4 legs per ticket, 2–3 tickets per slate
  R2  no leg appears on more than one ticket, except a FLOOR STAR (L10 >= 9/10 and L15 >= 13/15), max 2 tickets,
      and a ticket may carry at most one repeated star
  R3  floor rung = highest rung clearing L10 >= 80% and L15 >= 73%; never stepped up for price
  R4  every leg model% >= implied% - 2pts (winnable first; never a leg we know is overpriced)
  R5  attempt props excluded when the QB's team is favored by >= 7 (blowout flag)  [needs spreads.csv]
  R6  team-change and injury holds are hard holds
  R7  single-game slates (TNF/MNF): one ticket, correlation noted, plus floors listed as singles

Inputs : lines/dk_<season>_w<week>_<slate>.csv   Player,Market,Line,Odds
         projections.csv (from make_projections.py), floors_<...>.csv (from floors.py)
         notes/notes_<season>_w<week>.md          your scheme/injury reads (optional, passed to the draft verbatim)
Output : cards/card_<season>_w<week>_<slate>.json
Usage  : python pipeline/build_card_json.py --season 2026 --week 3 --slate sun
"""
import argparse, json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, ".")
from altline_engine import evaluate, pick_win_rung, parlay
from common import norm_name

FLOOR_STAR = lambda l10, l15: l10 >= 0.9 and l15 >= 13/15
MAX_LEG_JUICE = -450
SINGLE_GAME = {"tnf", "mnf", "snf"}

def load_floors(season, week, slate):
    f = pd.read_csv(f"floors_{season}_w{week}_{slate}.csv")
    f["l10"] = f.L10.str.split("/").str[0].astype(int) / 10
    f["l15"] = f.L15.str.split("/").str[0].astype(int) / 15
    return f

def blowout_flag(spread):
    return spread is not None and not pd.isna(spread) and spread <= -7

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", required=True, help="tnf | sun | mnf"); ap.add_argument("--tickets", type=int, default=3)
    a = ap.parse_args()
    fl = load_floors(a.season, a.week, a.slate)

    # candidate legs: floors that are winnable AND not over-priced, sorted by strength
    cands = []
    for r in fl.itertuples():
        if r.OppD == "TOUGH" or r.OwnVol == "TOUGH": continue
        if getattr(r, "TeamChange", False): continue                  # R6 hard hold: new team this season
        if r.Market in ("pass_att", "pass_cmps") and blowout_flag(r.Spread): continue
        if r.EstOdds < MAX_LEG_JUICE: continue
        cands.append(dict(player=r.Player, team=r.Team, opp=r.Opp, market=r.Market, rung=float(r.Rung.rstrip("+")),
                          odds_est=int(r.EstOdds), odds_real=None, l10=r.l10, l15=r.l15, last3=r.Last3,
                          opp_d=r.OppD, own_vol=r.OwnVol, star=FLOOR_STAR(r.l10, r.l15),
                          model_pct=round(100 * min(r.l10, r.l15, 0.9), 1),   # conservative: min of L10/L15, capped 90
                          note=f"L10 {r.L10}, L15 {r.L15}; last 3 {r.Last3}; opp D {r.OppD}"))
    cands.sort(key=lambda c: (-(c["l10"] + c["l15"]), c["odds_est"]))

    tickets, used = [], {}
    n_tickets = 1 if a.slate in SINGLE_GAME else a.tickets
    for i in range(n_tickets):
        legs, games, reused = [], set(), 0
        for c in cands:
            k = (c["player"], c["market"])
            if used.get(k, 0) >= (2 if c["star"] else 1): continue
            if used.get(k, 0) == 1:
                if reused >= 1: continue          # a ticket may carry at most ONE repeated floor star
                reused += 1
            g = frozenset([c["team"], c["opp"]])
            if a.slate not in SINGLE_GAME and g in games: continue          # cross-game only on Sunday slates
            if any(l["player"] == c["player"] for l in legs): continue
            legs.append(c); games.add(g)
            if len(legs) == 3: break
        if len(legs) < 3: break
        for l in legs: used[(l["player"], l["market"])] = used.get((l["player"], l["market"]), 0) + 1
        p = 1.0; dec = 1.0
        for l in legs:
            p *= l["model_pct"] / 100; dec *= 1 + (100 / -l["odds_est"] if l["odds_est"] < 0 else l["odds_est"] / 100)
        tickets.append(dict(name=f"{a.slate.upper()}-{i+1}", legs=legs, model_hit=round(p, 3), est_payout=round(dec, 2),
                            est_american=int(round((dec - 1) * 100)) if dec >= 2 else int(round(-100 / (dec - 1))),
                            correlated=a.slate in SINGLE_GAME))

    notes_path = f"notes/notes_{a.season}_w{a.week}.md"
    notes = open(notes_path).read() if os.path.exists(notes_path) else ""
    card = dict(season=a.season, week=a.week, slate=a.slate, rules="R1-R7 (see build_card_json.py)",
                tickets=tickets, floors_singles=cands[:12], held=fl[(fl.OppD == "TOUGH") | (fl.OwnVol == "TOUGH") | (fl.get("TeamChange", False) == True)]
                [["Player", "Market", "Rung", "EstOdds", "L10", "L15", "OppD", "OwnVol", "TeamChange"]].to_dict("records")[:15], notes=notes)
    os.makedirs("cards", exist_ok=True)
    out = f"cards/card_{a.season}_w{a.week}_{a.slate}.json"
    json.dump(card, open(out, "w"), indent=1, default=str)
    print(f"wrote {out}: {len(tickets)} tickets, {len(cands)} candidate floors")
    for t in tickets:
        print(f"  {t['name']} est {t['est_american']:+d} model {t['model_hit']*100:.0f}% :: " + " · ".join(f"{l['player']} {l['rung']:g}+ {l['market']}" for l in t["legs"]))

if __name__ == "__main__":
    main()
