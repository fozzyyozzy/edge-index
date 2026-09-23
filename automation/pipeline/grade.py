"""
grade.py — Tuesday job. Grades every leg on last week's card(s) against nflverse actuals.
Reads : cards/card_<season>_w<week>_<slate>.json   (from build_card_json.py)
Writes: receipts/receipts_<season>_w<week>.json  +  receipts/season_ledger.csv (append)
Usage : python pipeline/grade.py --season 2026 --week 2
"""
import argparse, glob, json, os
import pandas as pd
from common import norm_name, COL, fetch_week, pay, P

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    w = fetch_week(a.season, a.week)
    act = {(k, m): v for m, c in COL.items() for k, v in zip(w.key, w[c])}

    legs, tickets = [], []
    for path in sorted(glob.glob(P("cards", f"card_{a.season}_w{a.week}_*.json"))):
        card = json.load(open(path))
        for t in card["tickets"]:
            t_hits = []
            for l in t["legs"]:
                actual = act.get((norm_name(l["player"]), l["market"]))
                hit = None if actual is None or pd.isna(actual) else bool(actual >= l["rung"])
                odds = l.get("odds_real") or l["odds_est"]
                legs.append({**l, "slate": card["slate"], "ticket": t["name"],
                             "actual": None if actual is None or pd.isna(actual) else float(actual), "hit": hit,
                             "pnl_1u": None if hit is None else (pay(odds) if hit else -1.0),
                             "miss_by": None if hit is None or hit else round(l["rung"] - float(actual), 1)})
                t_hits.append(hit)
            tickets.append({"slate": card["slate"], "name": t["name"], "legs": len(t["legs"]),
                            "result": "VOID" if any(h is None for h in t_hits) else ("WIN" if all(t_hits) else "LOSS"),
                            "misses": [l["player"] for l, h in zip(t["legs"], t_hits) if h is False]})

    df = pd.DataFrame(legs); g = df[df.hit.notna()].copy()
    g["bucket"] = pd.cut(g.model_pct, [0, 75, 85, 101], labels=["<75", "75-85", "85+"])
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
        "est_vs_real": g[g.odds_real.notna()][["player", "market", "rung", "odds_est", "odds_real"]].to_dict("records"),
        "tickets": tickets,
        "ticket_record": {r: sum(1 for t in tickets if t["result"] == r) for r in ("WIN", "LOSS", "VOID")},
    }
    out = P("receipts", f"receipts_{a.season}_w{a.week}.json")
    json.dump(summary, open(out, "w"), indent=1)
    ledger = P("receipts", "season_ledger.csv")
    df.assign(season=a.season, week=a.week).to_csv(ledger, mode="a", index=False, header=not os.path.exists(ledger))
    print(f"wrote {out}"); print(json.dumps({k: summary[k] for k in ("legs_graded", "legs_hit", "hit_rate", "avg_model_pct", "flat_pnl_1u", "ticket_record")}, indent=1))

if __name__ == "__main__":
    main()
