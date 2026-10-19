"""
blend_study.py — research, report only: how would the board look under other market weights in the probability blend?
IN-SAMPLE: the weights are compared on the same weeks used to choose among them; treat any winner as a hypothesis.

  python pipeline/blend_study.py --season 2026 --weeks 3-6 [--out receipts/blend_study_2026.md]

Each settled Legs board (weeks given) is re-graded under each config in common.BLEND_VARIANTS with grade_legs.reblend()
(the rung's stored L10/L15 counts and DK no-vig probability; same grade modifiers), then:
  - calibration (one rung per player/market: Brier, mean |gap|, buckets) - price_check.calibration
  - grade x edge on the board (one rung per player/market) - price_check.grade_edge
  - how many C-or-better rungs pass R4 (edge >= +2) and the price cap: the pool a card could draw from
"""
import argparse, glob, json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, BLEND_VARIANTS
from grade_legs import reblend
from price_check import calibration, grade_edge, table, GRADE_OK

MAX_LEG_JUICE, MIN_EDGE = -450, 2.0


def board_frame(docs):
    rows = []
    for d in docs:
        wk, sl = int(d["meta"]["week"]), d["meta"]["slate"]
        for p in d["players"]:
            for r in p["rungs"]:
                if r.get("grade") in GRADE_OK and r.get("result") in ("hit", "miss", "void"):
                    rows.append(dict(week=wk, slate=sl, player=p["player"], market=p["market"], rung=float(r["rung"]),
                                     odds=int(r["est_odds"]), grade=r["grade"], edge=r.get("edge_pts"), prob=r.get("prob"),
                                     result=r["result"]))
    return pd.DataFrame(rows)


def study(season, weeks):
    docs = []
    for wk in weeks:
        for f in sorted(glob.glob(P("cards", f"legs_{season}_w{wk}_*.json"))):
            docs.append(json.load(open(f, encoding="utf-8")))
    out = {}
    for name, cfg in BLEND_VARIANTS.values():
        b = board_frame([reblend(d, cfg) for d in docs])
        cal, cal_sum = calibration(b)
        pool = b[(b.edge >= MIN_EDGE) & (b.odds >= MAX_LEG_JUICE)]
        out[name] = dict(cfg=cfg, cal=cal, cal_sum=cal_sum, ge=grade_edge(b, pd.DataFrame()),
                         pool=dict(rungs=len(pool), rows=len(pool.drop_duplicates(["week", "slate", "player", "market"]))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--weeks", default="3-6")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.weeks.split("-"))
    res = study(a.season, range(lo, hi + 1))
    md = [f"# Blend weight study, {a.season} weeks {a.weeks} (IN-SAMPLE: hypothesis only)", "",
          "Each board re-graded under each blend from its stored L10/L15 counts and DK no-vig probability. One rung per "
          "player/market. 'Pool' = C-or-better rungs that pass R4 (edge >= +2) and the -450 cap: what a card could use.", "",
          table([dict(blend=n, **{k: v for k, v in r["cfg"].items()}, brier=next(s["brier"] for s in r["cal_sum"] if s["source"] == "ours"),
                      mean_abs_gap=next(s["mean_abs_gap"] for s in r["cal_sum"] if s["source"] == "ours"),
                      dk_brier=next(s["brier"] for s in r["cal_sum"] if s["source"] == "DK implied"),
                      dk_gap=next(s["mean_abs_gap"] for s in r["cal_sum"] if s["source"] == "DK implied"),
                      card_pool_rungs=r["pool"]["rungs"], card_pool_rows=r["pool"]["rows"]) for n, r in res.items()],
                ["blend", "market_games", "history_weight", "cap", "brier", "mean_abs_gap", "dk_brier", "dk_gap",
                 "card_pool_rungs", "card_pool_rows"])]
    for n, r in res.items():
        md += [f"## {n}", "", "Calibration (ours):", "",
               table([c for c in r["cal"] if c["source"] == "ours"], ["bucket", "n", "predicted", "hit", "gap"]),
               "Grade x edge, board one rung per row:", "",
               table(r["ge"], ["grade", "split", "share", "n", "record", "hit", "implied", "ours", "beat_price", "roi"])]
    text = "\n".join(md)
    if a.out: open(a.out, "w", encoding="utf-8").write(text)
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
