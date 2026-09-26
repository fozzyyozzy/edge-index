"""
grade.py — Tuesday job. Grades every leg on last week's card(s) against nflverse actuals.
Reads : cards/card_<season>_w<week>_<slate>.json   (from build_card_json.py)
        cards/handbuilt_<season>_w<week>_<slate>.json   (card tickets published by hand, outside the pipeline — each
                                                         carries a "flag"; they count in the ticket W-L but have no
                                                         pipeline grade, so they never enter by_grade)
Writes: receipts/receipts_<season>_w<week>.json  +  receipts/season_ledger.csv (this week's rows replaced, so a
        regrade — a late cron plus a manual run — never double-counts)
Usage : python pipeline/grade.py --season 2026 --week 2
"""
import argparse, glob, json, os
import pandas as pd
from common import norm_name, COL, fetch_week, pay, P

GRADES = ["A+", "A", "A-", "B"]
LEDGER_COLS = ["season", "week", "slate", "ticket", "hand_built", "player", "team", "opp", "market", "rung", "grade",
               "clear_pct", "model_pct", "prob", "fair_odds", "edge_pts", "published", "closing", "clv_pts", "actual", "hit", "hit_standard", "early_exit",
               "pnl_1u", "miss_by"]

def dec(o): return 1 + (100 / -o if o < 0 else o / 100)

def closing_odds(leg, kick):
    """Closing price = the last price_history point pulled before the leg's kickoff (refresh_odds.py records history;
    the first point is the published price). None when the leg has no history (e.g. a hand-built ticket)."""
    ko = leg.get("kickoff") or kick.get(leg.get("team"))
    hist = [h for h in leg.get("price_history") or [] if h.get("at") and h.get("odds") is not None]
    if ko: hist = [h for h in hist if pd.Timestamp(h["at"]) < pd.Timestamp(ko)]
    return max(hist, key=lambda h: pd.Timestamp(h["at"]))["odds"] if hist else None

def settle(hits, decs, est_american=None):
    """(result, units at 1u flat) for one parlay. hits: True/False/None (None = void/no data -> VOID ticket).
    Payout = product of the legs' decimal prices, or the ticket's own published price when every leg stands."""
    if not hits or any(h is None for h in hits): return "VOID", 0.0
    if not all(hits): return "LOSS", -1.0
    d = 1.0
    for x in decs: d *= x
    return "WIN", round(d - 1, 2)

def by_grade_table(pg):
    """Per letter (A+, A, A-, B): legs, hits, average blended probability (common.leg_prob, as published on the card),
    average DK implied probability at the published price. `expected` = blended when known, else the old clear %."""
    def mean_pct(x):
        x = pd.to_numeric(x, errors="coerce")
        return round(float(x.mean()), 1) if x.notna().any() else None
    out = []
    for gr in GRADES:
        s = pg[pg.grade == gr]
        avg_prob = mean_pct(100 * pd.to_numeric(s["prob"], errors="coerce")) if "prob" in s else None
        out.append(dict(grade=gr, n=int(len(s)), hits=int(s.hit.sum()), avg_prob=avg_prob,
                        avg_implied=mean_pct(100 / s.published.map(dec)) if len(s) else None,
                        expected=avg_prob if avg_prob is not None else mean_pct(s.clear_pct)))
    return out

def am_dec(am): return 1 + (am / 100 if am > 0 else 100 / -am)

def official(t, hits, ee, prices):
    """As DraftKings settled: early-exit legs drop out; the rest decide it. If no leg was voided and the ticket has its own
    published price, a win pays that; otherwise the product of the standing legs' prices."""
    stand = [(h, dec(o)) for h, e, (o, _) in zip(hits, ee, prices) if not e]
    if not stand: return "VOID", 0.0
    res, units = settle([h for h, _ in stand], [d for _, d in stand])
    if res == "WIN" and not any(ee) and t.get("est_american"): units = round(am_dec(t["est_american"]) - 1, 2)
    return res, units

def clv_pts(pub, close):
    """Implied-probability points the price moved toward us: positive = it shortened after we published."""
    if pub is None or close is None: return None
    return round(100 * (1 / dec(close) - 1 / dec(pub)), 2)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    w = fetch_week(a.season, a.week)
    from floors import kickoffs
    kick = kickoffs(a.season, a.week)
    act = {(k, m): v for m, c in COL.items() for k, v in zip(w.key, w[c])}

    legs, tickets = [], []
    paths = sorted(glob.glob(P("cards", f"card_{a.season}_w{a.week}_*.json"))) +             sorted(glob.glob(P("cards", f"handbuilt_{a.season}_w{a.week}_*.json")))
    for path in paths:
        card = json.load(open(path))
        hand = bool(card.get("hand_built"))
        for t in card["tickets"]:
            t_hits, t_prices, t_std, t_ee = [], [], [], []
            for l in t["legs"]:
                actual = act.get((norm_name(l["player"]), l["market"]))
                hit_std = None if actual is None or pd.isna(actual) else bool(actual >= l["rung"])
                # DraftKings Early Exit protection: a leg whose player left the game early is voided and the parlay
                # settles on the rest. Official record = as DK settled; hit_standard keeps the stat-only grade.
                hit = None if l.get("early_exit") else hit_std
                odds = l.get("published_odds") or l.get("odds_real") or l["odds_est"]     # the price the card published
                close = None if hand else closing_odds(l, kick)   # hand-built legs stay out of every grade stat, CLV included
                legs.append({**l, "slate": card["slate"], "ticket": t["name"], "hand_built": hand,
                             "actual": None if actual is None or pd.isna(actual) else float(actual), "hit": hit,
                             "hit_standard": hit_std, "early_exit": bool(l.get("early_exit")),
                             "published": odds, "closing": close, "clv_pts": clv_pts(odds, close),
                             "pnl_1u": None if hit is None else (pay(odds) if hit else -1.0),
                             "miss_by": None if hit is None or hit else round(l["rung"] - float(actual), 1)})
                t_hits.append(hit); t_prices.append((odds, close)); t_std.append(hit_std); t_ee.append(bool(l.get("early_exit")))
            tickets.append({"slate": card["slate"], "name": t["name"], "legs": len(t["legs"]),
                            "flag": t.get("flag") if hand else None, "est_american": t.get("est_american"),
                            # ticket CLV: implied-probability points between the parlay at published vs closing prices
                            "clv_pts": round(100 * (1 / pd.Series([dec(c) for _, c in t_prices]).prod()
                                                    - 1 / pd.Series([dec(o) for o, _ in t_prices]).prod()), 2)
                                       if t_prices and all(c is not None for _, c in t_prices) else None,
                            "leg_text": [f"{l['player']} {l['rung']:g}+ {l['market']} ({'~' if l.get('price_estimated') else ''}"
                                         f"{(l.get('odds_real') or l['odds_est']):+d}){' · early exit' if l.get('early_exit') else ''}"
                                         for l in t["legs"]],
                            "early_exit": [l["player"] for l, e in zip(t["legs"], t_ee) if e],
                            **dict(zip(("result", "units"), official(t, t_hits, t_ee, t_prices))),
                            **dict(zip(("result_standard", "units_standard"),
                                       settle(t_std, [dec(o) for o, _ in t_prices]) if not t.get("est_american") or None in t_std or not all(t_std)
                                       else ("WIN", round(am_dec(t["est_american"]) - 1, 2)))),
                            "misses": [l["player"] for l, h in zip(t["legs"], t_hits) if h is False]})

    df = pd.DataFrame(legs)
    for col in ("model_pct", "clear_pct", "clv_pts"):                  # all-None for hand-built weeks -> numeric NaN
        if col in df: df[col] = pd.to_numeric(df[col], errors="coerce")
    g = df[df.hit.notna()].copy()
    g["bucket"] = pd.cut(g.model_pct, [0, 75, 85, 101], labels=["<75", "75-85", "85+"])
    pg = g[g.hand_built != True] if "hand_built" in g else g        # pipeline legs only: hand-built legs have no grade
    pipe_clv = (df.hand_built != True) & df.clv_pts.notna() if len(df) else []
    summary = {
        "season": a.season, "week": a.week,
        "legs_graded": int(len(g)), "legs_hit": int(g.hit.sum()),
        "hit_rate": round(float(g.hit.mean()), 3) if len(g) else None,
        "avg_model_pct": round(float(g.model_pct.mean()), 1) if len(g) else None,
        "flat_pnl_1u": round(float(g.pnl_1u.sum()), 2) if len(g) else None,
        "by_market": g.groupby("market").agg(n=("hit", "size"), hit=("hit", "mean")).round(2).reset_index().to_dict("records"),
        "by_bucket": g.groupby("bucket", observed=True).agg(n=("hit", "size"), hit=("hit", "mean")).round(2).reset_index().to_dict("records"),
        "near_misses": g[(g.hit == False) & (g.miss_by <= 3)][["player", "market", "rung", "actual", "miss_by"]].to_dict("records"),
        "misses": g[g.hit == False][["player", "market", "rung", "actual", "note", "opp_d", "own_vol", "ticket"]].to_dict("records"),
        # estimator's price (from the main line alone) vs the real DK rung price; older cards lack odds_model_est
        "est_vs_real": (g[g.odds_real.notna() & g.odds_model_est.notna()]
                        [["player", "market", "rung", "odds_model_est", "odds_real", "hit"]]
                        .rename(columns={"odds_model_est": "est", "odds_real": "real"}).to_dict("records")
                        if "odds_model_est" in g else []),
        # leg hit rate by the Legs-tab letter vs what the letter expected (mean clear %); older cards have no grade
        "by_grade": by_grade_table(pg) if "grade" in pg else [],
        # "clear %" = the card's legs predate the blend (no prob), so AVG PROB for this week is the published clear %
        "grade_basis": ("blended" if "prob" in pg and pd.to_numeric(pg["prob"], errors="coerce").notna().any()
                        else "clear %") if "grade" in pg and pg.grade.notna().any() else None,
        "tickets": tickets,
        # pipeline legs only (hand-built legs have no price history); every leg counts, graded or void
        "clv": dict(n=int(df[pipe_clv].shape[0]), avg_leg_pts=round(float(df[pipe_clv].clv_pts.mean()), 2)
                    if df[pipe_clv].shape[0] else None),
        "ticket_record": {r: sum(1 for t in tickets if t["result"] == r) for r in ("WIN", "LOSS", "VOID")},
        "ticket_record_standard": {r: sum(1 for t in tickets if t["result_standard"] == r) for r in ("WIN", "LOSS", "VOID")},
        "units": round(sum(t["units"] for t in tickets), 2),
        "units_standard": round(sum(t["units_standard"] for t in tickets), 2),
    }
    out = P("receipts", f"receipts_{a.season}_w{a.week}.json")
    json.dump(summary, open(out, "w"), indent=1)
    ledger = P("receipts", "season_ledger.csv")
    rows = df.assign(season=a.season, week=a.week).reindex(columns=LEDGER_COLS)
    if os.path.exists(ledger):                                          # idempotent: replace this week, keep the rest
        old = pd.read_csv(ledger)
        rows = pd.concat([old[~((old.season == a.season) & (old.week == a.week))].reindex(columns=LEDGER_COLS), rows],
                         ignore_index=True).sort_values(["season", "week"], kind="stable")
    rows.to_csv(ledger, index=False)
    write_season_record(a.season)
    print(f"wrote {out}"); print(json.dumps({k: summary[k] for k in ("legs_graded", "legs_hit", "hit_rate", "avg_model_pct", "flat_pnl_1u", "ticket_record")}, indent=1))

def write_season_record(season):
    """All of this season's receipts -> receipts/record_<season>.json, the site's NFL Record tab
    (tuesday.yml copies it to cfb-app/public/data/nfl_record.json). Rebuilt from the per-week files each run,
    so re-grading a week replaces it rather than double-counting."""
    weeks = []
    for path in sorted(glob.glob(P("receipts", f"receipts_{season}_w*.json")), key=lambda f: int(f.rsplit("_w", 1)[1][:-5])):
        weeks.append(json.load(open(path)))
    by_grade = []
    for gr in GRADES:
        rows = [b for wk in weeks for b in wk.get("by_grade", []) if b["grade"] == gr and b["n"]]
        n = sum(b["n"] for b in rows)
        def wavg(k):                                                    # leg-weighted across weeks, skipping unknowns
            rs = [b for b in rows if b.get(k) is not None]; m = sum(b["n"] for b in rs)
            return round(sum(b[k] * b["n"] for b in rs) / m, 1) if m else None
        by_grade.append(dict(grade=gr, n=n, hits=sum(b["hits"] for b in rows), avg_prob=wavg("avg_prob"),
                             avg_implied=wavg("avg_implied"), expected=wavg("expected")))
    record = dict(meta=dict(season=season, generated=pd.Timestamp.now(tz="UTC").isoformat(timespec="minutes"), weeks=len(weeks)),
                  weeks=[dict(week=wk["week"], ticket_record=wk["ticket_record"], legs_graded=wk["legs_graded"],
                              ticket_record_standard=wk.get("ticket_record_standard"), units=wk.get("units"),
                              units_standard=wk.get("units_standard"),
                              legs_hit=wk["legs_hit"], tickets=wk["tickets"], clv=wk.get("clv")) for wk in weeks],
                  by_grade=by_grade,
                  clear_basis_weeks=[wk["week"] for wk in weeks if wk.get("grade_basis") == "clear %"
                                     or (wk.get("grade_basis") is None and any(b.get("n") and b.get("avg_prob") is None
                                                                               for b in wk.get("by_grade", [])))],
                  est_vs_real=[dict(week=wk["week"], **r) for wk in weeks for r in wk.get("est_vs_real", [])])
    json.dump(record, open(P("receipts", f"record_{season}.json"), "w"), indent=1, allow_nan=False)

if __name__ == "__main__":
    main()
