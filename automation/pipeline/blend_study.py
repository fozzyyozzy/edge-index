"""
blend_study.py — research, report only: how would the board look under other market weights in the probability blend?
IN-SAMPLE: the weights are compared on the same weeks used to choose among them; treat any winner as a hypothesis.

  python pipeline/blend_study.py --season 2026 --weeks 3-6 [--out receipts/blend_study_2026.md]

Each settled Legs board (weeks given) is re-graded under each config in common.BLEND_VARIANTS with grade_legs.reblend()
(the rung's stored L10/L15 counts and DK no-vig probability; same grade modifiers), then:
  - calibration (one rung per player/market: Brier, mean |gap|, buckets) - price_check.calibration
  - grade x edge on the board (one rung per player/market) - price_check.grade_edge
  - how many C-or-better rungs pass R4 (that variant's edge floor) and the price cap: the pool a card could draw from
  - card study: every slate's card rebuilt under each variant (build_card_json.py --shadow, the slate's committed
    inputs, latest pre-kickoff prices): candidate pool, tickets per slate, ticket results, and the pool's legs by grade x
    edge vs implied (results from the settled Legs board)
"""
import argparse, glob, json, os, shutil, subprocess, sys, tempfile
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, BLEND_VARIANTS as ALL_VARIANTS, SHADOW_RULES, PROB_FIRST, fetch_week, COL, norm_name
BLEND_VARIANTS = {k: v for k, v in ALL_VARIANTS.items() if k not in PROB_FIRST}   # pfirst/calib: calib_study.py
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
    for slug, (name, cfg) in BLEND_VARIANTS.items():
        b = board_frame([reblend(d, cfg) for d in docs])
        cal, cal_sum = calibration(b)
        pool = b[(b.edge >= SHADOW_RULES.get(slug, {}).get("min_edge", MIN_EDGE)) & (b.odds >= MAX_LEG_JUICE)]
        out[name] = dict(cfg=cfg, cal=cal, cal_sum=cal_sum, ge=grade_edge(b, pd.DataFrame()),
                         pool=dict(rungs=len(pool), rows=len(pool.drop_duplicates(["week", "slate", "player", "market"]))))
    return out


INPUTS = ["floors/floors_{s}_w{w}_{sl}.csv", "cards/legs_{s}_w{w}_{sl}.json", "cards/availability_{s}_w{w}_{sl}.json",
          "lines/ladders_{s}_w{w}.csv", "lines/dk_{s}_w{w}_{sl}.csv", "lines/pulled_{s}_w{w}_{sl}.txt",
          "lines/pulled_{s}_w{w}.txt", "notes/notes_{s}_w{w}.md"]


def card_study(season, weeks):
    """{slug: {"slates": [...], "pool": DataFrame}} - each slate's card rebuilt under every variant from the slate's
    committed files (offline: no odds pull, no stats fetch except box scores for ticket results)."""
    pipe = os.path.dirname(os.path.abspath(__file__))
    out = {slug: dict(label=lab, slates=[], pool=[]) for slug, (lab, _) in BLEND_VARIANTS.items()}
    for wk in weeks:
        w = fetch_week(season, wk); act = {(k, m): v for m, c in COL.items() for k, v in zip(w.key, w[c])}
        for sl in ("tnf", "sun", "mnf"):
            fmt = dict(s=season, w=wk, sl=sl)
            if not all(os.path.exists(P(x.format(**fmt))) for x in INPUTS[:2]): continue
            res = {(norm_name(p["player"]), p["market"], float(r["rung"])): r.get("result")
                   for p in json.load(open(P(f"cards/legs_{season}_w{wk}_{sl}.json"), encoding="utf-8"))["players"] for r in p["rungs"]}
            tmp = tempfile.mkdtemp(prefix="blend_card_")
            for x in INPUTS:
                src = P(x.format(**fmt))
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(os.path.join(tmp, x.format(**fmt))), exist_ok=True)
                    shutil.copy(src, os.path.join(tmp, x.format(**fmt)))
            env = dict(os.environ, EDGE_ROOT=tmp, PYTHONIOENCODING="utf-8")
            for slug in BLEND_VARIANTS:
                args = [sys.executable, os.path.join(pipe, "build_card_json.py"), "--season", str(season), "--week", str(wk), "--slate", sl]
                if slug != "live": args += ["--shadow", slug]
                r = subprocess.run(args, env=env, capture_output=True, text=True)
                if r.returncode: continue
                f = os.path.join(tmp, "cards", f"card_{season}_w{wk}_{sl}.json") if slug == "live" else \
                    os.path.join(tmp, "cards", "shadow", f"card_{season}_w{wk}_{sl}_{slug}.json")
                c = json.load(open(f, encoding="utf-8"))
                tix = []
                for t in c["tickets"]:
                    hits = [None if pd.isna(act.get((norm_name(l["player"]), l["market"]), float("nan"))) else
                            act[(norm_name(l["player"]), l["market"])] >= l["rung"] for l in t["legs"]]
                    win = all(h is True for h in hits); loss = any(h is False for h in hits)
                    tix.append("WIN" if win else "LOSS" if loss else "VOID")
                    u = round(t["est_payout"] - 1, 2) if win else -1.0 if loss else 0.0
                    tix[-1] = (tix[-1], u)
                out[slug]["slates"].append(dict(week=wk, slate=sl, candidates=len(c.get("candidates", [])), tickets=len(tix),
                                                 W=sum(r == "WIN" for r, _ in tix), L=sum(r == "LOSS" for r, _ in tix),
                                                 units=round(sum(u for _, u in tix), 2)))
                for x in c.get("candidates", []):
                    out[slug]["pool"].append(dict(week=wk, slate=sl, player=x["player"], market=x["market"], rung=float(x["rung"]),
                                                  odds=int(x["odds_est"]), grade=x.get("grade"), edge=x.get("edge_pts"),
                                                  prob=x.get("prob"), result=res.get((norm_name(x["player"]), x["market"], float(x["rung"])))))
            shutil.rmtree(tmp, ignore_errors=True)
    for v in out.values(): v["pool"] = pd.DataFrame(v["pool"])
    return out


def card_md(cs):
    md = ["## Card study: every week's slates rebuilt under each variant (IN-SAMPLE)", "",
          "Each slate's committed inputs (latest pre-kickoff prices), built offline with build_card_json.py --shadow. "
          "Every rule except the variant's blend / R4 floor applies: -450 cap, C or better, every hold. 'Pool' = candidate "
          "legs the card could choose from; tickets scored on box scores (every leg clears; paid at the card's estimate).", ""]
    rows = []
    for slug, v in cs.items():
        sl = pd.DataFrame(v["slates"])
        if sl.empty: continue
        rows.append(dict(variant=v["label"], slates=len(sl), pool=int(sl.candidates.sum()), pool_per_slate=round(sl.candidates.mean(), 1),
                         tickets=int(sl.tickets.sum()), tickets_per_slate=round(sl.tickets.mean(), 2),
                         slates_with_no_ticket=int((sl.tickets == 0).sum()), record=f"{int(sl.W.sum())}-{int(sl.L.sum())}",
                         units=round(float(sl.units.sum()), 2)))
    md += [table(rows, ["variant", "slates", "pool", "pool_per_slate", "tickets", "tickets_per_slate", "slates_with_no_ticket",
                        "record", "units"])]
    md += ["Tickets per slate, by variant:", "",
           table([dict(slate=f"w{r['week']} {r['slate']}", **{v["label"]: next((x["tickets"] for x in v["slates"]
                 if x["week"] == r["week"] and x["slate"] == r["slate"]), "-") for v in cs.values()}) for r in cs["live"]["slates"]],
                 ["slate"] + [v["label"] for v in cs.values()])]
    for slug, v in cs.items():
        p = v["pool"]
        if p.empty: md += [f"### Pool, {v['label']}: empty", ""]; continue
        p = p[p.result.isin(["hit", "miss", "void"])]
        md += [f"### Pool legs by grade x edge, {v['label']}", "", table(grade_edge(p, pd.DataFrame()),
               ["grade", "split", "share", "n", "record", "hit", "implied", "ours", "beat_price", "roi"])]
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--weeks", default="3-6")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cards", action="store_true", help="also rebuild every slate's card under each variant (slower)")
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
    if a.cards:
        md += card_md(card_study(a.season, range(lo, hi + 1)))
    text = "\n".join(md)
    if a.out: open(a.out, "w", encoding="utf-8").write(text)
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main()
