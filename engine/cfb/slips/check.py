"""CFB slip checker: price, sanity-check and grade a multi-leg slip (Tim, 2026-10-19).

    python -m engine.cfb.slips.check data/cfb/slips/2026_wk07_ml_flier.json

Slip file (JSON): {"id", "season", "week", "boost_pct" (profit boost, e.g. 50), "stake" (optional),
"slip_price" (optional posted price; else the product of the leg prices), "price_source" note,
"legs": [{"type": "ml", "team": "Texas"} | {"type": "spread", "team", "line"} |
         {"type": "total", "game": "<team in the game>", "side": "Over"|"Under", "line"}],
each leg may carry its own "price"}.

Per leg: model probability, the market's no-vig probability, the price, leg EV.
  ml      P(team wins) from the frozen Phase 3 distribution at the Phase 3 projection; |DK spread| > 14
          -> shaded halfway to the no-vig ML (5E rule).            label ML-SHADED
  spread  cover probability from the same distribution (pushes on whole lines).  label SPREAD
  total   market-anchored totals (centered on DK's main total, frozen sigma + key totals);
          PAPER-UNPROVEN (totals never beat the market in testing)
Prices default to the week's Tue bet-time DK snapshot (main lines; alt totals/spreads from the ladder
snapshot), labeled as such; a leg's own "price" overrides.
Slip: joint probability (legs independent; same-game legs are flagged), payout with the boost applied
to the PROFIT, EV vs our model and vs the market's no-vig, and the boost each needs to break even.
Grading uses games.parquet final scores only.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.cards import card as C
from engine.cfb.model import distribution as dist, run as mrun
from engine.cfb.totals import anchored, model as tm


def norm(s):
    return str(s).strip().lower()


def find_game(games: pd.DataFrame, team: str) -> pd.Series:
    t = norm(team)
    x = games[(games.home_team.str.lower() == t) | (games.away_team.str.lower() == t)]
    if len(x) != 1:
        raise SystemExit(f"leg team '{team}': {len(x)} games found in this week")
    return x.iloc[0]


def check(slip: dict) -> dict:
    season, week = slip["season"], slip["week"]
    games = pd.read_parquet(config.CLEAN / "games.parquet")
    games = games[(games.season == season) & (games.week == week)]
    ts, main, lad, alt = C.load_snapshot(season, week, slip.get("snapshot", "tue10"))
    gt = C.game_table(main, season, week).set_index("game_id")
    dp = mrun.dist_params(mrun.load_params())
    tp = json.loads(anchored.PARAMS.read_text())
    kt = {int(k): v for k, v in tp["key_totals"].items()}
    out = []
    for leg in slip["legs"]:
        g = find_game(games, leg.get("team") or leg.get("game"))
        gid = int(g.game_id)
        r = gt.loc[gid] if gid in gt.index else None
        home = norm(leg.get("team", "")) == norm(g.home_team)
        row = {"leg": None, "game": f"{g.away_team} @ {g.home_team}", "game_id": gid, "type": leg["type"]}
        if r is None:
            row.update({"note": "no DK snapshot/projection for this game"})
            out.append(row)
            continue
        absl, tot = abs(r.home_spread), r.total if pd.notna(r.total) else 52.0
        P = dist.pmf([r.proj], [absl], [tot], dp)
        if leg["type"] == "ml":
            ph = float((P * (dist.M[None, :] > 0)).sum())
            ih, ia = C.implied(r.home_ml), C.implied(r.away_ml)
            nv_h = float(ih / (ih + ia))
            pm, nv = (ph, nv_h) if home else (1 - ph, 1 - nv_h)
            shaded = absl > 14
            p = (pm + nv) / 2 if shaded else pm
            price = leg.get("price", r.home_ml if home else r.away_ml)
            row.update({"leg": f"{leg['team']} ML", "label": "ML-SHADED", "p_model_raw": pm, "shaded": shaded,
                        "dk_spread_team": float(r.home_spread if home else -r.home_spread)})
        elif leg["type"] == "spread":
            side = "home" if home else "away"
            c, push = dist.cover(P, float(leg["line"]), side)
            p = float(c[0] / max(1 - push[0], 1e-9)) if float(leg["line"]) % 1 == 0 else float(c[0])
            nv, price = np.nan, leg.get("price")
            if price is None:
                if float(leg["line"]) == float(r.home_spread if home else -r.home_spread):
                    price = r.home_spread_price if home else r.away_spread_price
                else:
                    z = lad[(lad.game_id == gid) & (lad.rung == float(leg["line"]))
                            & (lad.is_home == (1 if home else 0))] if len(lad) else lad
                    price = float(z.price.iloc[0]) if len(z) else None
            row.update({"leg": f"{leg['team']} {float(leg['line']):+g}", "label": "SPREAD"})
        elif leg["type"] == "total":
            L, side = float(leg["line"]), leg["side"].capitalize()
            st = tm.sigma_t([tp["sigma_t"]["a"], tp["sigma_t"]["c"]], np.array([tot]))
            PT = anchored.pmf_anchored(np.array([tot]), st, kt)
            ov, push = tm.over(PT, L)
            p_over = float(ov[0] / max(1 - push[0], 1e-9))
            p = p_over if side == "Over" else 1 - p_over
            price, nv = leg.get("price"), np.nan
            if L == float(r.total):
                po, pu = r.over_price, r.under_price
            else:
                z = alt[(alt.game_id == gid) & (alt.market == "alternate_totals") & (alt.point == L)] if len(alt) else alt
                po = float(z[z.side == "Over"].price.iloc[0]) if len(z[z.side == "Over"]) else None
                pu = float(z[z.side == "Under"].price.iloc[0]) if len(z[z.side == "Under"]) else None
            if po is not None and pu is not None:
                io, iu = C.implied(po), C.implied(pu)
                nv = float((io if side == "Over" else iu) / (io + iu))
            if price is None:
                price = po if side == "Over" else pu
            row.update({"leg": f"{side} {L:g} ({g.away_team} @ {g.home_team})", "label": "PAPER-UNPROVEN",
                        "dk_main_total": float(r.total)})
        else:
            raise SystemExit(f"unknown leg type {leg['type']}")
        dec = 1 + float(C.payout(price)) if price is not None else np.nan
        row.update({"price": price, "p_model": p, "p_novig": nv, "decimal": dec,
                    "leg_ev_model": p * dec - 1 if price is not None else np.nan})
        # grade from final scores
        if pd.notna(g.home_points) and bool(g.completed):
            hp, ap = float(g.home_points), float(g.away_points)
            tm_ = (hp - ap) if home else (ap - hp)
            if leg["type"] == "ml":
                res = 1.0 if tm_ > 0 else 0.0
            elif leg["type"] == "spread":
                v = tm_ + float(leg["line"])
                res = None if v == 0 else float(v > 0)
            else:
                v = (hp + ap - L) * (1 if side == "Over" else -1)
                res = None if v == 0 else float(v > 0)
            row.update({"result": res, "final": f"{g.away_team} {int(ap)} - {g.home_team} {int(hp)}"})
        out.append(row)
    legs = pd.DataFrame(out)
    games_seen = legs.game_id.value_counts()
    same_game = sorted(set(legs.game_id[legs.game_id.isin(games_seen[games_seen > 1].index)]))
    dec = float(np.prod(legs.decimal)) if slip.get("slip_price") is None else 1 + float(C.payout(slip["slip_price"]))
    boost = slip.get("boost_pct", 0) / 100
    dec_b = 1 + (dec - 1) * (1 + boost)
    pj = float(np.prod(legs.p_model))
    pj_nv = float(np.prod(legs.p_novig)) if legs.p_novig.notna().all() else np.nan
    res = legs.result if "result" in legs else pd.Series([None] * len(legs))
    graded = res.notna().all()
    summary = {"legs": len(legs), "price_unboosted": float(C.american(np.array(dec))),
               "price_boosted": float(C.american(np.array(dec_b))), "boost_pct": slip.get("boost_pct", 0),
               "p_joint_model": pj, "p_joint_market_novig": pj_nv,
               "fair_price_model": float(C.american(np.array(1 / pj))),
               "ev_model_boosted": pj * dec_b - 1, "ev_model_unboosted": pj * dec - 1,
               "ev_market_boosted": pj_nv * dec_b - 1 if pj_nv == pj_nv else np.nan,
               "breakeven_boost_model_pct": 100 * ((1 / pj - 1) / (dec - 1) - 1),
               "breakeven_boost_market_pct": 100 * ((1 / pj_nv - 1) / (dec - 1) - 1) if pj_nv == pj_nv else np.nan,
               "same_game_legs": same_game,
               "result": ("WIN" if (res == 1).all() else "LOSS") if graded and (res == 0).any() or (graded and (res == 1).all()) else "PENDING",
               "legs_won": int((res == 1).sum()), "legs_lost": int((res == 0).sum())}
    stake = slip.get("stake")
    if stake and summary["result"] != "PENDING":
        summary["net_units"] = stake * (dec_b - 1) if summary["result"] == "WIN" else -stake
    return {"slip": slip, "snapshot_utc": ts.isoformat(), "legs": legs, "summary": summary}


def readout(r: dict) -> str:
    s, L = r["summary"], r["legs"]
    lines = [f"# Slip check: {r['slip']['id']} ({r['slip']['season']} week {r['slip']['week']})",
             f"Prices: {r['slip'].get('price_source', 'DK Tue bet snapshot ' + r['snapshot_utc'])}. "
             f"Boost: +{s['boost_pct']}% on profit. Legs treated as independent"
             + (f"; SAME-GAME legs: {s['same_game_legs']}" if s["same_game_legs"] else "") + ".", "",
             "| # | leg | label | price | model p | market no-vig p | leg EV | result |",
             "|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(L.itertuples(), 1):
        nv = f"{100 * x.p_novig:.1f}%" if pd.notna(x.p_novig) else "n/a"
        sh = getattr(x, "shaded", False)
        flag = " (shaded, |spread| > 14)" if (sh == sh and bool(sh)) else ""   # numpy-bool safe
        res = {1.0: "W", 0.0: "L"}.get(getattr(x, "result", None), "push/pending")
        lines.append(f"| {i} | {x.leg} | {x.label}{flag} | {x.price:+.0f} | {100 * x.p_model:.1f}% | {nv} | "
                     f"{100 * x.leg_ev_model:+.1f}% | {res} |")
    lines += ["",
              f"**Slip:** {s['legs']} legs, {s['price_unboosted']:+.0f} -> **{s['price_boosted']:+.0f} boosted**. "
              f"Joint probability: model **{100 * s['p_joint_model']:.2f}%** (fair {s['fair_price_model']:+.0f}), "
              f"market no-vig {100 * s['p_joint_market_novig']:.2f}%.",
              f"**EV (boosted):** model {100 * s['ev_model_boosted']:+.1f}%, market {100 * s['ev_market_boosted']:+.1f}% "
              f"(unboosted, model: {100 * s['ev_model_unboosted']:+.1f}%). Break-even boost: model "
              f"{s['breakeven_boost_model_pct']:+.0f}%, market {s['breakeven_boost_market_pct']:+.0f}%.",
              f"**Result:** {s['result']} ({s['legs_won']} won, {s['legs_lost']} lost)."]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slip")
    a = ap.parse_args(argv)
    slip = json.loads(Path(a.slip).read_text(encoding="utf-8"))
    r = check(slip)
    md = readout(r)
    out = Path(a.slip).with_suffix(".check.md")
    out.write_text(md, encoding="utf-8")
    print(md)
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
