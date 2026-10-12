"""Grade published CFB floor cards (Phase 5E). Used by `forward weekly`.

Only data/cfb/cards/card_<season>_wk<NN>.json (published, paper) are graded, from games.parquet
final scores. A leg pushes (void) when the result lands exactly on a whole-number line.
Units are at the posted price, 1 unit per leg. Floor legs feed the pre-registered bar
(docs/cfb/FORWARD_TEST.md): >= 100 graded floor legs, ROI > 0 with a game-clustered 95% CI
lower bound > -2%, and realized hit rate >= the mean implied break-even. Second legs and tickets
are reported, not barred.
"""
from __future__ import annotations
import glob
import json

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.cards.card import CARDS, implied, payout

BAR = {"min_legs": 100, "roi_ci_lo": -0.02}


def outcome(leg: dict, g: pd.Series) -> float | None:
    """1 win, 0 loss, None for push/ungraded."""
    if pd.isna(g.home_points) or pd.isna(g.away_points) or not bool(g.completed):   # numpy bool safe
        return None
    hp, ap = float(g.home_points), float(g.away_points)
    m = leg["market"]
    home = leg.get("side") == "home"
    if m in ("SPREAD-CLV", "ALT-SHAPE"):
        v = (hp - ap if home else ap - hp) + leg["line"]
    elif m == "ML-SHADED":
        v = (hp - ap) if home else (ap - hp)
    elif m == "PAPER-UNPROVEN":
        v = (hp + ap - leg["line"]) * (1 if leg["side"] == "Over" else -1)
    elif m == "TEAM-TOTAL":
        team_pts = hp if leg["pick"].startswith(leg["game"].split(" @ ")[1]) else ap
        v = (team_pts - leg["line"]) * (1 if leg["side"] == "Over" else -1)
    else:
        return None
    return None if v == 0 else float(v > 0)


def legs(season: int) -> pd.DataFrame:
    g = pd.read_parquet(config.CLEAN / "games.parquet").set_index("game_id")
    rows = []
    for f in sorted(glob.glob(str(CARDS / f"card_{season}_wk*.json"))):
        c = json.loads(open(f, encoding="utf-8").read())
        for x in c["floor_legs"]:
            y = outcome(x, g.loc[x["game_id"]]) if x["game_id"] in g.index else None
            rows.append({"week": c["week"], "snapshot_utc": c["snapshot_utc"], **{k: x.get(k) for k in
                         ("game_id", "game", "pick", "market", "role", "price", "p_used", "ev",
                          "dk_home_spread")}, "result": y})
    d = pd.DataFrame(rows)
    if len(d):
        d["units"] = np.where(d.result == 1, payout(d.price), np.where(d.result == 0, -1.0, np.nan))
        d["breakeven"] = implied(d.price)
    return d


def edge_legs(season: int) -> pd.DataFrame:
    """Track 2: the card's main-spread edge list (|edge| >= 1.5 vs the Tuesday line), graded at the
    posted Tuesday line and price, 1 unit each. Separate from the floor card."""
    g = pd.read_parquet(config.CLEAN / "games.parquet").set_index("game_id")
    rows = []
    for f in sorted(glob.glob(str(CARDS / f"card_{season}_wk*.json"))):
        c = json.loads(open(f, encoding="utf-8").read())
        for x in c.get("spread_edges", []):
            leg = {**x, "market": "SPREAD-CLV"}
            y = outcome(leg, g.loc[x["game_id"]]) if x.get("game_id") in g.index else None
            rows.append({"week": c["week"], "game_id": x.get("game_id"), "game": x["game"], "pick": x["pick"],
                         "market": "SPREAD-CLV", "role": "edge", "price": x["price"], "edge_pts": x["edge_pts"],
                         "p_used": x["p_model"], "ev": x["ev"], "result": y})
    d = pd.DataFrame(rows)
    if len(d):
        d["units"] = np.where(d.result == 1, payout(d.price), np.where(d.result == 0, -1.0, np.nan))
        d["breakeven"] = implied(d.price)
    return d


def alt_shape_split(d: pd.DataFrame) -> dict:
    """DIAGNOSTIC (not a bar): ALT-SHAPE floor legs split by game spread |DK main line| <= 14 vs > 14."""
    x = d[(d.role == "floor") & (d.market == "ALT-SHAPE")].dropna(subset=["result"]) if len(d) else d
    if x is None or x.empty:
        return {}
    big = x.dk_home_spread.abs() > 14
    out = {}
    for name, grp in (("|spread| <= 14", x[~big]), ("|spread| > 14", x[big])):
        if len(grp):
            out[name] = {"legs": len(grp), "hit_%": round(100 * grp.result.mean(), 1),
                         "breakeven_%": round(100 * grp.breakeven.mean(), 1),
                         "roi_%": round(100 * grp.units.mean(), 1)}
    return out


def summary(d: pd.DataFrame, role="floor", n_boot=2000, seed=0) -> dict:
    x = d[(d.role == role)].dropna(subset=["result"]) if len(d) else d
    if x is None or x.empty:
        return {"graded_legs": 0}
    games = x.game_id.unique()
    idx = x.groupby("game_id").indices
    rng = np.random.default_rng(seed)
    b = [x.units.to_numpy()[np.concatenate([idx[gg] for gg in rng.choice(games, len(games))])].mean()
         for _ in range(n_boot)]
    out = {"graded_legs": len(x), "games": len(games), "hit_%": 100 * x.result.mean(),
           "mean_breakeven_%": 100 * x.breakeven.mean(), "roi_%": 100 * x.units.mean(),
           "roi_ci95": f"{100 * np.percentile(b, 2.5):+.1f} to {100 * np.percentile(b, 97.5):+.1f}",
           "by_market": x.groupby("market").agg(legs=("units", "size"), hit=("result", "mean"),
                                                roi=("units", "mean")).round(3).to_dict("index")}
    if role == "floor":
        if len(x) >= BAR["min_legs"]:
            ok = (x.units.mean() > 0 and np.percentile(b, 2.5) > BAR["roi_ci_lo"]
                  and x.result.mean() >= x.breakeven.mean())
            out["bar"] = ("PASSED" if ok else "FAILED") + f" at {len(x)} legs"
        else:
            out["bar"] = f"IN PROGRESS: {len(x)}/{BAR['min_legs']} graded floor legs; $0"
    return out
