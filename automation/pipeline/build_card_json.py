"""
build_card_json.py — Wed/Fri/Mon job. Turns the floor scan + edge scan into a slate card with tickets
that obey the house rules, and writes it as JSON for the site and the newsletter draft.

Rules encoded here (do not relax without changing the newsletter copy too):
  R1  3–4 legs per ticket, 2–3 tickets per slate
  R2  no PLAYER appears on more than one ticket (any market), except a FLOOR STAR (L10 >= 9/10 and L15 >= 13/15),
      max 2 tickets, and a ticket may carry at most one repeated star. Same player = same injury + same game script.
  R3  floor rung = highest rung clearing L10 >= 80% and L15 >= 73%; never stepped up for price
  R4  every leg model% >= implied% - 2pts (winnable first; never a leg we know is overpriced)
  R5  attempt props excluded when the QB's team is favored by >= 7 (blowout flag)  [needs spreads.csv]
  R6  team-change and injury holds are hard holds
  R7  single-game slates (TNF/MNF): one ticket, correlation noted, plus floors listed as singles
  R8  Bloom target: each ticket aims for >= +200 (3.0x). Reach it by ADDING a 4th floor leg, never by stepping a rung up.
      If 4 legs still fall short, publish as "reduced payout" — floors held, still recommended.

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
from common import norm_name, P

FLOOR_STAR = lambda l10, l15: l10 >= 0.9 and l15 >= 13/15
MAX_LEG_JUICE = -450
TARGET_DEC = 3.0          # +200
def dec(o): return 1 + (100 / -o if o < 0 else o / 100)
SINGLE_GAME = {"tnf", "mnf", "snf"}

def load_floors(season, week, slate):
    f = pd.read_csv(P("floors", f"floors_{season}_w{week}_{slate}.csv"))
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
    # star cap: a floor star may anchor two tickets, but never two tickets in the same slate that would otherwise share nothing
    for i in range(n_tickets):
        legs, games, reused = [], set(), 0
        def can_take(c):
            k = c["player"]                                   # player-level uniqueness across tickets
            if used.get(k, 0) >= (2 if c["star"] else 1): return False
            if used.get(k, 0) == 1 and reused >= 1: return False
            g = frozenset([c["team"], c["opp"]])
            if a.slate not in SINGLE_GAME and g in games: return False
            if any(l["player"] == c["player"] for l in legs): return False
            return True
        # pass 1: three strongest floors
        for c in cands:
            if len(legs) == 3: break
            if can_take(c):
                if used.get(c["player"], 0) == 1: reused += 1
                legs.append(c); games.add(frozenset([c["team"], c["opp"]]))
        if len(legs) < 3: break
        payout = 1.0
        for l in legs: payout *= dec(l["odds_est"])
        # pass 2 (R8): under target -> add the 4th leg that gets closest to / past 3.0x, floors only
        if payout < TARGET_DEC:
            best = None
            for c in cands:
                if can_take(c) and c["odds_est"] <= -130 and min(c["l10"], c["l15"]) >= 0.73:   # 4th leg is a floor, not a flyer
                    p2 = payout * dec(c["odds_est"])
                    if best is None or abs(p2 - TARGET_DEC) < abs(best[1] - TARGET_DEC) or (p2 >= TARGET_DEC and best[1] < TARGET_DEC):
                        best = (c, p2)
            if best:
                c, payout = best
                if used.get(c["player"], 0) == 1: reused += 1
                legs.append(c); games.add(frozenset([c["team"], c["opp"]]))
        for l in legs: used[l["player"]] = used.get(l["player"], 0) + 1
        p = 1.0
        for l in legs: p *= l["model_pct"] / 100
        tickets.append(dict(name=f"{a.slate.upper()}-{i+1}", legs=legs, model_hit=round(p, 3), est_payout=round(payout, 2),
                            est_american=int(round((payout - 1) * 100)) if payout >= 2 else int(round(-100 / (payout - 1))),
                            reduced=payout < TARGET_DEC, correlated=a.slate in SINGLE_GAME,
                            label="Reduced payout: floors held, not stretched — still recommended" if payout < TARGET_DEC else "Bloom: +200 target met"))

    notes_path = P("notes", f"notes_{a.season}_w{a.week}.md")
    notes = open(notes_path).read() if os.path.exists(notes_path) else ""
    card = dict(season=a.season, week=a.week, slate=a.slate, rules="R1-R7 (see build_card_json.py)",
                tickets=tickets, floors_singles=cands[:12], held=fl[(fl.OppD == "TOUGH") | (fl.OwnVol == "TOUGH") | (fl.get("TeamChange", False) == True)]
                [["Player", "Market", "Rung", "EstOdds", "L10", "L15", "OppD", "OwnVol", "TeamChange"]].to_dict("records")[:15], notes=notes)
    out = P("cards", f"card_{a.season}_w{a.week}_{a.slate}.json")
    json.dump(card, open(out, "w"), indent=1, default=str)
    print(f"wrote {out}: {len(tickets)} tickets, {len(cands)} candidate floors")
    for t in tickets:
        flag = "  [REDUCED]" if t["reduced"] else ""
        print(f"  {t['name']} est {t['est_american']:+d} model {t['model_hit']*100:.0f}%{flag} :: " + " · ".join(f"{l['player']} {l['rung']:g}+ {l['market']} ({l['odds_est']:+d})" for l in t["legs"]))

if __name__ == "__main__":
    main()
