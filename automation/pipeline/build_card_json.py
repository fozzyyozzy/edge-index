"""
build_card_json.py — Wed/Fri/Mon job. Turns the floor scan + edge scan into a slate card with tickets
that obey the house rules, and writes it as JSON for the site and the newsletter draft.

Rules encoded here (do not relax without changing the newsletter copy too):
  LOCK  a card locks when its newsletter is sent. Before that, a rule fix may rebuild it from the same pulled prices
        (logged in MODEL_CHANGELOG.md); after that, never. Prices, results and injury flags may update; tickets don't.
  R1  3–4 legs per ticket, 2–3 tickets per slate (single-game slates: 2 legs allowed, always "Reduced payout")
  R2  no PLAYER appears on more than one ticket (any market), except a FLOOR STAR (L10 >= 9/10 and L15 >= 13/15),
      max 2 tickets, and a ticket may carry at most one repeated star — counted on every ticket the star is on, so no
      ticket shares more than one player with the rest of the card. Same player = same injury + same game script.
  R3  qualifying rung = any rung at or below the floor rung (the highest clearing L10 >= 80% and L15 >= 73%) that
      still clears those rates; each player/market offers its BEST-GRADED qualifying rung that passes R4/R9 and the
      price cap (ties: higher edge). Never stepped up for price.
  R4  every leg needs edge >= +2 pts: blended probability (common.leg_prob — lower of L10/L15 add-one clear rates,
      blended toward DK's no-vig price as 10 extra games, capped at 0.90) minus DK's implied probability at the price
  R5  attempt props excluded when the QB's team is favored by >= 7 (blowout flag)  [needs spreads.csv]
  R6  team-change and injury holds are hard holds. Injury (availability.py, the same snapshot grade_legs.py wrote): missed
      one of the team's last two games, Out/Doubtful/Questionable, DNP in practice, or held by hand in
      notes/holds_<season>_w<week>.csv. Limited practice with no game status yet is an "injury watch" flag on the leg.
  R7  single-game slates (TNF/MNF): one ticket, correlation noted, plus floors listed as singles; a 2-leg ticket
      is allowed there (thin menu) and is always labelled "Reduced payout"
  R8  Bloom target: each ticket aims for >= +200 (3.0x). Reach it by ADDING a 4th floor leg, never by stepping a rung up.
      The 4th leg comes from the best grade available; payout only chooses between legs of that grade.
      If 4 legs still fall short, publish as "reduced payout" — floors held, still recommended.
  R9  every leg is graded C or better on the Legs board (same cutoff as the Legs tab); anything below is held
      "grade below C". If that leaves no valid ticket (R7: a single-game slate needs 2 legs), the card has no ticket —
      never padded with a weaker leg.
  R10 selection is grade first (A+ > A > A- > B > C), then edge. A C leg is used only when no B-or-better leg can fill
      one of a ticket's first three spots — never as a 4th leg (3 legs already make a ticket; it runs reduced instead).
      A third ticket that would need a C leg is not built (two tickets beat a weaker third).
  R11 a player with an injury-watch flag goes on one ticket at most (no star repeat).

Inputs : lines/dk_<season>_w<week>_<slate>.csv   Player,Market,Line,Odds
         projections.csv (from make_projections.py), floors_<...>.csv (from floors.py)
         notes/notes_<season>_w<week>.md          your scheme/injury reads (optional, passed to the draft verbatim)
Output : cards/card_<season>_w<week>_<slate>.json
Usage  : python pipeline/build_card_json.py --season 2026 --week 3 --slate sun
"""
import argparse, glob, json, os, re, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, ".")
from altline_engine import evaluate, pick_win_rung, parlay, estimate_ladder
from common import norm_name, P, load_real_ladders, prices_pulled
import availability

FLOOR_STAR = lambda l10, l15: l10 >= 0.9 and l15 >= 13/15   # raw clear rates on purpose: consistency, not price
MAX_LEG_JUICE = -450
MIN_EDGE_PTS = 2.0          # R4
GRADE_OK = {"A+", "A", "A-", "B", "C"}   # R9
GRADE_RANK = {"A+": 5, "A": 4, "A-": 3, "B": 2, "C": 1}   # R10
TARGET_DEC = 3.0          # +200
def dec(o): return 1 + (100 / -o if o < 0 else o / 100)
SINGLE_GAME = {"tnf", "mnf", "snf"}

def load_floors(season, week, slate):
    name = f"floors_{season}_w{week}_{slate}.csv"
    for cand in (P("floors", name), name, os.path.join("automation", name)):
        if os.path.exists(cand):
            try: f = pd.read_csv(cand)
            except pd.errors.EmptyDataError: f = pd.DataFrame()        # floors.py found no floor legs on this slate
            break
    else:
        raise SystemExit(f"floor scan output not found: run floors.py first ({name})")
    if f.empty: return pd.DataFrame(columns=["Player", "Market", "Rung", "L10", "L15", "l10", "l15"])
    f["l10"] = f.L10.str.split("/").str[0].astype(int) / 10
    f["l15"] = f.L15.str.split("/").str[0].astype(int) / 15
    return f

def parse_last3(v):
    """floors CSV Last3 -> [126, 144, 68]; also reads old rows written as "[np.int64(126), ...]"."""
    return [int(float(x)) for x in re.findall(r"-?\d+(?:\.\d+)?", re.sub(r"np\.\w+\(", "", str(v)))]

def rank_or_none(r, col):
    """matchup rank from the floors CSV (1 = softest D / highest volume); older CSVs don't have the column"""
    v = getattr(r, col, None)
    return None if v is None or pd.isna(v) else int(v)

def frac(v):
    """'9/10' -> 0.9"""
    n, d = str(v).split("/"); return int(n) / int(d)

def player_market_holds(r, avail=None):
    """holds that apply to every rung of a player/market: injury, team change, blowout, matchup, volume"""
    why = []
    if avail is not None: why += availability.reasons(avail, r.Player, r.Market, r.Team)[0]   # R6 injury / by hand
    if getattr(r, "TeamChange", False) == True:
        why.append(f"team change ({r.PrevTeam}->{r.Team})" if isinstance(getattr(r, "PrevTeam", None), str) and r.PrevTeam else "team change")
    if r.Market in ("pass_att", "pass_cmps") and blowout_flag(r.Spread): why.append(f"blowout risk (fav by {-r.Spread:g})")
    if r.OppD == "TOUGH": why.append("opp D tough")
    if r.OwnVol == "TOUGH": why.append("own volume low")
    return why

def hold_reasons(r, avail=None):
    """Why a floor row's floor rung is not a card candidate (empty = candidate). Order: hard holds first."""
    why = []
    if avail is not None: why += availability.reasons(avail, r.Player, r.Market, r.Team)[0]   # R6 injury / by hand
    if getattr(r, "TeamChange", False) == True:
        why.append(f"team change ({r.PrevTeam}->{r.Team})" if isinstance(getattr(r, "PrevTeam", None), str) and r.PrevTeam else "team change")
    if r.Market in ("pass_att", "pass_cmps") and blowout_flag(r.Spread): why.append(f"blowout risk (fav by {-r.Spread:g})")
    if r.OppD == "TOUGH": why.append("opp D tough")
    if r.OwnVol == "TOUGH": why.append("own volume low")
    if r.EstOdds < MAX_LEG_JUICE: why.append(f"price worse than {MAX_LEG_JUICE}")
    edge = getattr(r, "EdgePts", None)
    if edge is not None and not pd.isna(edge) and edge < MIN_EDGE_PTS:
        why.append(f"edge {edge:+.1f} pts (< +{MIN_EDGE_PTS:g})")                 # R4
    return why

def hold_rank(h):
    """hard holds (team change, blowout) first, then matchup/volume, then price-only; floor-scan order within each"""
    first = h["Reasons"][0]
    return 0 if first.startswith(("team change", "blowout", "injury", "held by hand")) else 2 if first.startswith(("price", "edge")) else 1

def thursday_prices(season, week, slate, before):
    """Sunday slate only: the latest Thursday snapshot (sun-snapshot.yml) pulled before this card's prices.
    Returns ({(name, market, rung): odds}, pulled_at) or ({}, None)."""
    if slate != "sun" or not before: return {}, None
    best = None
    for f in sorted(glob.glob(P("lines", "snapshots", f"ladders_{season}_w{week}_sun_*.csv"))):
        d = pd.read_csv(f)
        if len(d) and str(d.PulledAt.iloc[0]) < before: best = d      # ISO UTC strings compare in time order
    if best is None: return {}, None
    return ({(norm_name(r.Player), r.Market, float(r.Rung)): int(r.Odds) for r in best.itertuples()},
            str(best.PulledAt.iloc[0]))

def blowout_flag(spread):
    return spread is not None and not pd.isna(spread) and spread <= -7

def build_tickets(cands, slate, n_tickets):
    """Assemble tickets from candidates already sorted grade-first (R10). Pure: no files, no network — the rule
    tests call it directly. Enforces R1/R2/R7/R8/R10/R11 and one leg per game (multi-game slates)."""
    tickets, used = [], {}
    owner, shared = {}, []      # R2: player -> the ticket he first went on; per ticket, players it shares with another ticket
    # star cap: a floor star may anchor two tickets, and each ticket shares at most ONE player with all the other tickets
    # combined — checked on both sides, so an earlier ticket can't end up sharing one star with SUN-2 and another with SUN-3
    for i in range(n_tickets):
        legs, games, reused = [], set(), 0
        def can_take(c):
            k = c["player"]                                   # player-level uniqueness across tickets
            if used.get(k, 0) >= (2 if c["star"] and not c["injury_watch"] else 1): return False     # R2, R11
            if used.get(k, 0) == 1 and (reused >= 1 or shared[owner[k]] >= 1): return False
            g = frozenset([c["team"], c["opp"]])
            if slate not in SINGLE_GAME and g in games: return False
            if any(l["player"] == c["player"] for l in legs): return False
            return True
        # pass 1: three best legs, grade first then edge (R10: a C only when nothing B-or-better fits)
        for c in cands:
            if len(legs) == 3: break
            if can_take(c):
                if used.get(c["player"], 0) == 1: reused += 1
                legs.append(c); games.add(frozenset([c["team"], c["opp"]]))
        if len(legs) < (2 if slate in SINGLE_GAME else 3): break          # R1/R7
        payout = 1.0
        for l in legs: payout *= dec(l["odds_est"])
        # pass 2 (R8): under target -> add the 4th leg that gets closest to / past 3.0x, floors only
        if i >= 2 and any(l["grade"] == "C" for l in legs): break     # R10: no third ticket that needs a C leg
        if payout < TARGET_DEC:
            best = None
            # 4th leg is a floor, not a flyer; R8/R10: from the best grade available, payout decides within that grade
            elig = [c for c in cands if can_take(c) and c["odds_est"] <= -130 and min(c["l10"], c["l15"]) >= 0.73]
            top = max((GRADE_RANK[c["grade"]] for c in elig), default=0)
            if top < GRADE_RANK["B"]: elig = []          # R10: 3 legs already make a ticket, so a C is never needed here
            for c in elig:
                if GRADE_RANK[c["grade"]] == top:
                    p2 = payout * dec(c["odds_est"])
                    if best is None or abs(p2 - TARGET_DEC) < abs(best[1] - TARGET_DEC) or (p2 >= TARGET_DEC and best[1] < TARGET_DEC):
                        best = (c, p2)
            if best:
                c, payout = best
                if used.get(c["player"], 0) == 1: reused += 1
                legs.append(c); games.add(frozenset([c["team"], c["opp"]]))
        shared.append(0)
        for l in legs:
            k = l["player"]
            if used.get(k, 0) == 1: shared[owner[k]] += 1; shared[i] += 1      # a repeat counts on both tickets
            else: owner[k] = i
            used[k] = used.get(k, 0) + 1
        p = 1.0
        for l in legs: p *= l["model_pct"] / 100
        reduced = payout < TARGET_DEC or len(legs) == 2                     # a 2-leg ticket is always reduced
        tickets.append(dict(name=f"{slate.upper()}-{i+1}", legs=legs, model_hit=round(p, 3), est_payout=round(payout, 2),
                            est_american=int(round((payout - 1) * 100)) if payout >= 2 else int(round(-100 / (payout - 1))),
                            reduced=reduced, correlated=slate in SINGLE_GAME,
                            label="Reduced payout: floors held, not stretched — still recommended" if reduced else "Bloom: +200 target met"))
    return tickets

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", required=True, help="tnf | sun | mnf"); ap.add_argument("--tickets", type=int, default=3)
    a = ap.parse_args()
    fl = load_floors(a.season, a.week, a.slate)
    ladders_path = P("lines", f"ladders_{a.season}_w{a.week}.csv")
    REAL = load_real_ladders(ladders_path)                       # {(name, market): [(rung, odds)]} — real DK prices
    pulled = prices_pulled(a.season, a.week, a.slate)
    THU, THU_AT = thursday_prices(a.season, a.week, a.slate, pulled)
    AVAIL = availability.load(a.season, a.week, a.slate)          # grade_legs.py's snapshot (built here if missing)
    lines_path = P("lines", f"dk_{a.season}_w{a.week}_{a.slate}.csv")
    # every player/market DK had posted when this card was built; refresh_odds.py flags anything newer "posted_after_card"
    try:
        at_publish = sorted({f"{norm_name(r.Player)}|{r.Market}" for r in pd.read_csv(lines_path).itertuples()})
    except (FileNotFoundError, pd.errors.EmptyDataError):
        at_publish = []
    # grade letter + clear % per rung from grade_legs.py (runs first in card.yml) — the Record tab grades by letter
    legs_path = P("cards", f"legs_{a.season}_w{a.week}_{a.slate}.json")
    GRADED, RUNGS = {}, {}
    if os.path.exists(legs_path):
        for p in json.load(open(legs_path, encoding="utf-8"))["players"]:
            for r in p["rungs"]:
                GRADED[(norm_name(p["player"]), p["market"], float(r["rung"]))] = (r["grade"], r.get("clear_pct"))
            RUNGS[(norm_name(p["player"]), p["market"])] = p["rungs"]

    # candidate legs: floors that are winnable AND not over-priced, sorted by strength
    cands, held = [], []
    for r in fl.itertuples():
        floor = float(r.Rung.rstrip("+"))
        why = player_market_holds(r, AVAIL)
        opts = []
        if not why:                                                   # R3: best-graded qualifying rung at or below the floor
            for x in RUNGS.get((norm_name(r.Player), r.Market), []):
                if x["rung"] > floor or x.get("grade") not in GRADE_OK or "l10" not in x: continue
                if frac(x["l10"]) < 0.8 or frac(x["l15"]) < 0.73: continue
                if x["est_odds"] < MAX_LEG_JUICE or x.get("edge_pts") is None or x["edge_pts"] < MIN_EDGE_PTS: continue
                opts.append(x)
        if not opts:                                                  # held: the floor rung's reasons, as before
            why = hold_reasons(r, AVAIL)
            # R9: the leg's Legs-board grade must be C or better (the Legs tab's cutoff). No grade = trimmed below C.
            g = GRADED.get((norm_name(r.Player), r.Market, floor), (None, None))[0]
            if g not in GRADE_OK: why.append("grade below C")
            held.append(dict(Player=r.Player, Market=r.Market, Rung=r.Rung, EstOdds=int(r.EstOdds), L10=r.L10, L15=r.L15,
                             OppD=r.OppD, OwnVol=r.OwnVol, TeamChange=bool(getattr(r, "TeamChange", False) == True),
                             Last3=parse_last3(r.Last3), Reasons=why or ["no qualifying rung"]))
            continue
        x = max(opts, key=lambda x: (GRADE_RANK[x["grade"]], x["edge_pts"], x["rung"]))
        rung = float(x["rung"]); last3 = parse_last3(r.Last3); l10, l15 = frac(x["l10"]), frac(x["l15"])
        real = dict(REAL.get((norm_name(r.Player), r.Market), [])).get(rung)
        # what the estimator would have priced this rung from the main line alone — the Record tab's est-vs-real table
        model_est = dict(estimate_ladder(r.Market, float(r.Main), int(r.MainOdds))[0]).get(rung)
        cands.append(dict(player=r.Player, team=r.Team, opp=r.Opp, market=r.Market, rung=rung, floor_rung=floor,
                          odds_est=int(x["est_odds"]), odds_real=int(real) if real is not None else None,
                          odds_model_est=int(model_est) if model_est is not None else None, l10=l10, l15=l15,
                          last3=last3, opp_d=r.OppD, own_vol=r.OwnVol, star=FLOOR_STAR(l10, l15),
                          opp_d_rank=rank_or_none(r, "OppDRank"), own_vol_rank=rank_or_none(r, "OwnVolRank"),
                          # blended probability from grade_legs.py (common.leg_prob) for the chosen rung
                          model_pct=round(100 * float(x["prob"]), 1), prob=float(x["prob"]), fair_odds=x.get("fair_odds"),
                          edge_pts=float(x["edge_pts"]), novig_pct=x.get("novig_pct"),
                          grade=x["grade"], clear_pct=x.get("clear_pct"),
                          injury_watch=availability.reasons(AVAIL, r.Player, r.Market, r.Team)[1] or None,
                          note=f"L10 {x['l10']}, L15 {x['l15']}; last 3 {last3}; opp D {r.OppD}"
                               + (f"; floor rung {floor:g}+ graded lower" if rung < floor else "")))
        # locked at publish, never changed: the price the card was built on and when. refresh_odds.py appends to
        # price_history (only before the game's kickoff) and moves current_odds; grade.py reads closing from the history.
        c = cands[-1]; pub = c["odds_real"] if c["odds_real"] is not None else c["odds_est"]
        hist = [dict(at=pulled, odds=pub)]
        thu = THU.get((norm_name(r.Player), r.Market, rung))
        if thu is not None:                                            # Sunday card: Thursday -> published -> close
            hist.insert(0, dict(at=THU_AT, odds=thu, source="thursday snapshot"))
        c.update(published_odds=pub, published_at=pulled, current_odds=pub, current_at=pulled,
                 thursday_odds=thu, price_history=hist)
    cands.sort(key=lambda c: (-GRADE_RANK[c["grade"]], -c["edge_pts"], c["odds_est"]))      # R10: grade, then edge

    tickets = build_tickets(cands, a.slate, 1 if a.slate in SINGLE_GAME else a.tickets)

    notes_path = P("notes", f"notes_{a.season}_w{a.week}.md")
    notes = open(notes_path).read() if os.path.exists(notes_path) else ""
    card = dict(season=a.season, week=a.week, slate=a.slate, rules="R1-R11 (see build_card_json.py)", prices_pulled=pulled,
                published_at=pulled, thursday_pulled=THU_AT, markets_at_publish=at_publish,
                availability=dict(fetched_at=AVAIL.get("fetched_at"), sources=AVAIL.get("sources")),
                tickets=tickets, floors_singles=cands[:12], candidates=cands, held=sorted(held, key=hold_rank)[:15],
                held_all=sorted(held, key=hold_rank),        # every hold, for grading holds by reason (held = top 15, for display)
                notes=notes)
    out = P("cards", f"card_{a.season}_w{a.week}_{a.slate}.json")
    json.dump(card, open(out, "w"), indent=1, allow_nan=False)   # no default=str: it hid numpy values as repr strings
    print(f"wrote {out}: {len(tickets)} tickets, {len(cands)} candidate floors")
    for t in tickets:
        flag = "  [REDUCED]" if t["reduced"] else ""
        print(f"  {t['name']} est {t['est_american']:+d} model {t['model_hit']*100:.0f}%{flag} :: " + " · ".join(f"{l['player']} {l['rung']:g}+ {l['market']} ({l['odds_est']:+d})" for l in t["legs"]))

if __name__ == "__main__":
    main()
