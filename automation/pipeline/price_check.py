"""
price_check.py — do our legs beat their prices? Report only: nothing here changes a rule (R4 is revisited only once this
shows a pattern over at least 4 weeks).

  python pipeline/price_check.py --season 2026 --through 4 [--out receipts/price_check_2026.md]

1. Holds and carded legs (every pipeline card through --through): per hold reason (each reason a leg carries, plus "sole
   reason"), all held legs once, and carded legs — count, record, hit %, average implied % at the listed single price,
   our average probability (common.leg_prob, recomputed walk-forward: only games before that week, blended with DK's
   no-vig price at the listed odds), and flat 1u ROI at the listed single prices. Voids (no stat row) are excluded.
2. The Legs board, C-or-better rungs that settled: split at -500 (worse than -500 vs -500 or better), and the -500-or-
   better range split by edge (>= +2 vs < +2). Hit %, implied %, our %, flat ROI — counting every rung, and counting one
   rung per player/market (the row's best rung within that split: highest grade, then the higher rung — what the Legs
   tab headlines). Prices are the board's: the last pre-kickoff regrade (odds refresh), not the card's publish price.
"""
import argparse, glob, json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fetch_season, norm_name, COL, leg_prob, novig, load_holds, implied, P
from floors import INV
from grade import HOLD_CATS

GRADE_OK = ["A+", "A", "A-", "B", "C"]


def dec(o): return 1 + (100 / -o if o < 0 else o / 100)


def summarize(sub, label):
    s = sub[sub.result.isin(["hit", "miss"])]
    n = len(s); hits = int((s.result == "hit").sum())
    if not n: return dict(group=label, n=0, record="0-0", voids=int((sub.result == "void").sum()))
    pnl = sum(dec(o) - 1 if r == "hit" else -1.0 for r, o in zip(s.result, s.odds))
    return dict(group=label, n=n, record=f"{hits}-{n - hits}", voids=int((sub.result == "void").sum()),
                hit=round(100 * hits / n, 1), implied=round(100 * s.odds.map(implied).mean(), 1),
                ours=round(100 * s.prob.dropna().mean(), 1) if s.prob.notna().any() else None,
                beat_price=round(100 * (hits / n - s.odds.map(implied).mean()), 1),
                roi=round(100 * pnl / n, 1), units=round(pnl, 2))


def holds_and_carded(season, through):
    w = pd.concat([fetch_season(y) for y in (season - 2, season - 1, season)])
    cur = w[w.season == season]
    def actual(name, market, week):
        r = cur[(cur.key == norm_name(name)) & (cur.week == week)]
        return None if r.empty or pd.isna(r[COL[market]].iloc[0]) else float(r[COL[market]].iloc[0])
    def our_prob(name, market, rung, odds, week, holds):
        g = w[(w.key == norm_name(name)) & (w[INV[market]].fillna(0) > 0) & ((w.season < season) | (w.week < week))]
        v = g.sort_values(["season", "week"])[COL[market]].fillna(0).to_numpy()
        return leg_prob(v, rung, novig(odds, name, market, holds)[0]) if len(v) else None
    rows, sources = [], {}
    for f in sorted(glob.glob(P("cards", f"card_{season}_w*_*.json"))):
        c = json.load(open(f, encoding="utf-8")); wk = int(c["week"])
        if wk > through: continue
        holds = load_holds(season, wk)
        held = c.get("held_all") or c.get("held") or []
        sources[f"w{wk} {c['slate']}"] = "every hold" if c.get("held_all") else "top-15 holds only"
        for h in held:
            rung = float(str(h["Rung"]).rstrip("+")); odds = int(h["EstOdds"])
            cats = sorted({cat for pre, cat in HOLD_CATS for why in h.get("Reasons") or [] if why.startswith(pre)})
            rows.append(dict(kind="held", week=wk, slate=c["slate"], player=h["Player"], market=h["Market"], rung=rung,
                             odds=odds, cats=cats, sole=cats[0] if len(cats) == 1 else None,
                             actual=actual(h["Player"], h["Market"], wk), prob=our_prob(h["Player"], h["Market"], rung, odds, wk, holds)))
        seen = set()
        for t in c["tickets"]:
            for l in t["legs"]:
                k = (l["player"], l["market"], float(l["rung"]))
                if k in seen: continue
                seen.add(k)
                odds = int(l.get("published_odds") or l.get("odds_real") or l["odds_est"])
                rows.append(dict(kind="carded", week=wk, slate=c["slate"], player=l["player"], market=l["market"],
                                 rung=float(l["rung"]), odds=odds, cats=["carded"], sole="carded",
                                 actual=actual(l["player"], l["market"], wk), prob=our_prob(l["player"], l["market"], float(l["rung"]), odds, wk, holds)))
    df = pd.DataFrame(rows)
    if df.empty: return [], sources
    df["result"] = [("void" if pd.isna(a) else "hit" if a >= r else "miss") for a, r in zip(df.actual, df.rung)]
    out, ex = [], df.explode("cats")
    for _, cat in HOLD_CATS:
        s = ex[(ex.kind == "held") & (ex.cats == cat)]
        if not len(s): continue
        out.append(summarize(s, f"held: {cat}"))
        o = df[(df.kind == "held") & (df.sole == cat)]
        if len(o): out.append(summarize(o, f"held: {cat} (sole reason)"))
    out.append(summarize(df[df.kind == "held"].drop_duplicates(["week", "slate", "player", "market", "rung"]), "held: all, each leg once"))
    out.append(summarize(df[df.kind == "carded"], "carded legs"))
    return out, sources


def board_rows(season, through):
    rows = []
    for f in sorted(glob.glob(P("cards", f"legs_{season}_w*_*.json"))):
        d = json.load(open(f, encoding="utf-8")); wk = int(d["meta"]["week"])
        if wk > through: continue
        for p in d["players"]:
            for r in p["rungs"]:
                if r.get("grade") in GRADE_OK and r.get("result") in ("hit", "miss", "void"):
                    rows.append(dict(week=wk, slate=d["meta"]["slate"], player=p["player"], market=p["market"], rung=float(r["rung"]),
                                     odds=int(r["est_odds"]), grade=r["grade"], edge=r.get("edge_pts"), prob=r.get("prob"), result=r["result"]))
    return pd.DataFrame(rows)


def board_split(b):
    if b.empty: return []
    b = b.copy(); b["gi"] = b.grade.map({g: i for i, g in enumerate(reversed(GRADE_OK))})
    def one_per_row(s):            # the row's best rung within the split: highest grade, then the higher rung
        return s.sort_values(["gi", "rung"], ascending=False).drop_duplicates(["week", "slate", "player", "market"])
    splits = [("worse than -500", b[b.odds < -500]),
              ("-500 or better", b[b.odds >= -500]),
              ("-500 or better, edge >= +2", b[(b.odds >= -500) & (b.edge >= 2)]),
              ("-500 or better, edge < +2", b[(b.odds >= -500) & (b.edge < 2)])]
    out = []
    for label, s in splits:
        out.append(dict(summarize(s, label), count="every rung"))
        out.append(dict(summarize(one_per_row(s), label), count="one rung per player/market"))
    return out


def table(rows, cols):
    head = "| " + " | ".join(cols) + " |\n|" + "|".join("---" for _ in cols) + "|\n"
    return head + "".join("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |\n" for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--through", type=int, required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    held, sources = holds_and_carded(a.season, a.through)
    b = board_rows(a.season, a.through)
    weeks = sorted(set(b.week)) if len(b) else []
    md = [f"# Price check, {a.season} through week {a.through}", "",
          "Report only: no rule changes from this (R4 is revisited once held legs beat their prices over at least 4 weeks).", "",
          "## Holds and carded legs (listed single prices)", "",
          "Hit vs implied at the listed price; our probability recomputed walk-forward. Voids excluded. Sources: "
          + ", ".join(f"{k} ({v})" for k, v in sorted(sources.items())) + ".", "",
          table(held, ["group", "n", "record", "voids", "hit", "implied", "ours", "beat_price", "roi", "units"]),
          f"## Legs board, C-or-better rungs (weeks {', '.join(map(str, weeks)) or 'none'})", "",
          "Board prices = last pre-kickoff regrade. One rung per player/market = the row's best rung within the split.", "",
          table(board_split(b), ["group", "count", "n", "record", "hit", "implied", "ours", "beat_price", "roi", "units"])]
    text = "\n".join(md)
    if a.out: open(a.out, "w", encoding="utf-8").write(text)
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
