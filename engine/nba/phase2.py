"""Phase 2: model development (train/validation only) and the single registered holdout run.

    python -m engine.nba.phase2 dev        # 2023-24 fit -> 2024-25 validation; writes data/nba/model/frozen_config.json
    python -m engine.nba.phase2 holdout    # ONCE, after the frozen config is committed (PREREG §1, §8)

dev never loads a 2025-26 row (model.guard). holdout refuses to run twice: it writes
data/nba/model/holdout_run.json and stops if that file already exists.
"""
from __future__ import annotations
import argparse
import itertools
import json
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from engine.nba import model as M
from engine.nba.eligibility import eligible
from engine.nba.espn import ROOT

DATA = ROOT / "data" / "nba"
OUTDIR = DATA / "model"
TRAIN, VALID = "2023-24", "2024-25"
H_M = [5.0, 10.0, 15.0]
H_R = [10.0, 20.0, 40.0]
KAPPA = [100.0, 300.0, 900.0]
GAMMA = [0.0, 0.5, 1.0]
FAMILIES = ["poisson", "nbinom", "dnorm", "dgamma", "dresid"]   # dgamma, dresid added during validation (dev log)
BAND = (0.60, 0.95)
SLOPE_SET = (0.50, 0.97)
SLOPE_DIAG = (0.60, 0.90)
GATE_BINS = [(0.70, 0.75), (0.75, 0.80), (0.80, 0.85), (0.85, 0.90)]
HOT_BINS = [(0.75, 0.80), (0.80, 0.85), (0.85, 0.90), (0.90, 0.95)]
N_MIN = 300
CARD = ["pts", "reb", "ast", "fg3m", "pr", "pa", "pra"]          # card-eligible if passed (R+A calibration-only)
SHADOW = ["stl", "blk"]


def load(holdout: bool) -> pd.DataFrame:
    pg = pd.read_parquet(DATA / "player_games.parquet")
    if not holdout:
        pg = pg[pg.season.isin([TRAIN, VALID])]
    M.guard(pg, holdout)
    pg = pg.assign(eligible=eligible(pg))
    return pg


# ---------- dev ----------
def dev():
    pg = load(holdout=False)
    cfg = M.Config()
    log = {"minutes": [], "markets": {}}
    # 1. minutes halflife: fit on train, MAE on validation
    best = None
    for h in H_M:
        cfg.h_m = h
        p = M.features(pg, cfg)
        e = p.reset_index(drop=True)
        e = e[e.eligible]
        tr, va = e[e.season == TRAIN], e[e.season == VALID]
        cfg.minutes_coef = M.fit_minutes(tr)
        mae = float(np.abs(M._min_design(va) @ np.asarray(cfg.minutes_coef) - va.minutes).mean())
        log["minutes"].append({"h_m": h, "valid_mae": round(mae, 3)})
        print(f"minutes h_m={h}: valid MAE {mae:.3f}", flush=True)
        if best is None or mae < best[0]:
            best = (mae, h)
    cfg.h_m = best[1]
    # 2. per market: (h_r, kappa, gamma, family) by validation RPS, params fit on train
    chosen = {}
    for hr in H_R:
        for s in M.STATS:
            cfg.h_r[s] = hr
        for kap in KAPPA:
            for s in M.STATS:
                cfg.kappa[s] = kap
            p = M.features(pg, cfg)
            e = p.reset_index(drop=True)
            e = e[e.eligible]
            tr, va = e[e.season == TRAIN], e[e.season == VALID]
            cfg.minutes_coef = M.fit_minutes(tr)
            for g in GAMMA:
                for s in M.STATS:
                    cfg.gamma[s] = g
                mtr, mva = M.mu(tr, cfg), M.mu(va, cfg)
                for s in M.STATS:
                    for fam in FAMILIES:
                        par = M.fit_family(fam, mtr[f"mu_{s}"].to_numpy(), tr[s].to_numpy())
                        score = M.rps(fam, par, mva[f"mu_{s}"].to_numpy(), va[s].to_numpy(), M.KMAX[s])
                        rec = {"h_r": hr, "kappa": kap, "gamma": g, "family": fam, "valid_rps": round(score, 5)}
                        log["markets"].setdefault(s, []).append(rec)
                        if s not in chosen or score < chosen[s]["valid_rps"]:
                            chosen[s] = rec
            print(f"h_r={hr} kappa={kap}: done", flush=True)
    for s, c in chosen.items():
        cfg.h_r[s], cfg.kappa[s], cfg.gamma[s] = c["h_r"], c["kappa"], c["gamma"]
    # 3. validation diagnostics with train-fitted parameters (2024-25 is validation, not holdout)
    p = M.features(pg, cfg)
    e = p[p.eligible].reset_index(drop=True)
    tr = e[e.season == TRAIN].reset_index(drop=True)
    va = e[e.season == VALID].reset_index(drop=True)
    cfg.minutes_coef = M.fit_minutes(tr)
    mtr, mva = M.mu(tr, cfg), M.mu(va, cfg)
    for s in M.STATS:
        fam = chosen[s]["family"]
        cfg.dist[s] = {"family": fam, **M.fit_family(fam, mtr[f"mu_{s}"].to_numpy(), tr[s].to_numpy())}
    valid_report = {s: score_market(va, mva, cfg, s, pg) for s in M.STATS}
    # 4. freeze: refit minutes + distribution params on train + validation with the chosen settings
    cfg.minutes_coef = M.fit_minutes(e)
    me = M.mu(e, cfg)
    for s in M.STATS:
        fam = chosen[s]["family"]
        cfg.dist[s] = {"family": fam, **M.fit_family(fam, me[f"mu_{s}"].to_numpy(), e[s].to_numpy())}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    frozen = {"frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "fit_seasons": [TRAIN, VALID], "config": cfg.to_dict(), "minutes_features": M.MIN_X}
    (OUTDIR / "frozen_config.json").write_text(json.dumps(frozen, indent=2))
    (OUTDIR / "dev_log.json").write_text(json.dumps({"search": log, "chosen": chosen,
                                                      "validation_2024_25": valid_report}, indent=2, default=float))
    print(json.dumps({s: {k: v for k, v in r.items() if k in ("passes", "slope", "brier_model", "brier_naive")}
                      for s, r in valid_report.items()}, indent=1, default=float))


# ---------- scoring ----------
def naive_rates(e: pd.DataFrame, pg: pd.DataFrame, stat: str, kmax: int) -> np.ndarray:
    """last-10 played games' clear rate at each rung k (strictly prior, same season); NaN if < 5 prior games"""
    p = pg[pg.played].sort_values(["espn_id", "season", "date"])
    lags = pd.concat({i: p.groupby(["espn_id", "season"])[stat].shift(i) for i in range(1, 11)}, axis=1)
    lags = pd.concat([p[["game_id", "espn_id"]], lags], axis=1)
    v = e[["game_id", "espn_id"]].merge(lags, on=["game_id", "espn_id"], how="left").iloc[:, 2:].to_numpy(float)
    n = (~np.isnan(v)).sum(axis=1)
    k = np.arange(1, kmax + 1)
    hits = (v[:, :, None] >= k[None, None, :]).sum(axis=1)
    rate = hits / np.maximum(n, 1)[:, None]
    rate[n < 5] = np.nan
    return rate.ravel()


def logistic_slope(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """IRLS fit of logit P(y) = a + b*logit(p)"""
    p = np.clip(p, 1e-4, 1 - 1e-4)
    x = np.log(p / (1 - p))
    X = np.column_stack([np.ones_like(x), x])
    beta = np.array([0.0, 1.0])
    for _ in range(50):
        eta = X @ beta
        mu_ = 1 / (1 + np.exp(-eta))
        w = mu_ * (1 - mu_)
        z = eta + (y - mu_) / np.maximum(w, 1e-9)
        new = np.linalg.solve(X.T @ (w[:, None] * X), X.T @ (w * z))
        if np.max(np.abs(new - beta)) < 1e-8:
            beta = new
            break
        beta = new
    return float(beta[0]), float(beta[1])


def bins_table(t: pd.DataFrame, edges=np.round(np.arange(0.05, 1.0001, 0.05), 2)) -> list[dict]:
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        b = t[(t.p >= lo) & (t.p < hi)]
        if len(b):
            out.append({"bin": f"{int(lo * 100)}-{int(hi * 100)}", "n": int(len(b)), "n_pg": int(b.row.nunique()),
                        "mean_p": round(float(b.p.mean()) * 100, 2), "hit": round(float(b.y.mean()) * 100, 2)})
    return out


def score_market(e: pd.DataFrame, m: pd.DataFrame, cfg: M.Config, stat: str, pg: pd.DataFrame | None = None) -> dict:
    t = M.prob_table(e, m, cfg, stat)
    t["row"] = np.repeat(np.arange(len(e)), M.KMAX[stat])
    res = {"market": stat, "player_games": int(len(e))}
    ss = t[(t.p >= SLOPE_SET[0]) & (t.p <= SLOPE_SET[1])]
    res["slope_n"] = int(len(ss))
    res["intercept"], res["slope"] = logistic_slope(ss.p.to_numpy(), ss.y.to_numpy())
    sd = t[(t.p >= SLOPE_DIAG[0]) & (t.p <= SLOPE_DIAG[1])]
    res["slope_diag_60_90"] = logistic_slope(sd.p.to_numpy(), sd.y.to_numpy())[1]
    band = t[(t.p >= BAND[0]) & (t.p < BAND[1])].copy()
    if pg is not None:
        naive = naive_rates(e, pg, stat, M.KMAX[stat])
        band["naive"] = naive[band.index.to_numpy()]
        bb = band.dropna(subset=["naive"])
        res["brier_n"] = int(len(bb))
        res["brier_model"] = float(((bb.p - bb.y) ** 2).mean())
        res["brier_naive"] = float(((bb.naive - bb.y) ** 2).mean())
    bins = {b["bin"]: b for b in bins_table(t)}
    res["reliability"] = list(bins.values())
    gate = [bins.get(f"{int(lo * 100)}-{int(hi * 100)}") for lo, hi in GATE_BINS]
    big = [b for b in gate if b and b["n"] >= N_MIN]
    res["B0"] = len(big) >= 2
    res["B1"] = 0.90 <= res["slope"] <= 1.10
    res["B2"] = all(abs(b["mean_p"] - b["hit"]) <= 3.0 for b in big)
    res["B3"] = res.get("brier_model", np.inf) < res.get("brier_naive", -np.inf)
    hot = [bins.get(f"{int(lo * 100)}-{int(hi * 100)}") for lo, hi in HOT_BINS]
    res["B4"] = all(b["hit"] >= b["mean_p"] - 5.0 for b in hot if b and b["n"] >= N_MIN)
    res["passes"] = all(res[k] for k in ("B0", "B1", "B2", "B3", "B4"))
    return res


# ---------- holdout ----------
def holdout():
    marker = OUTDIR / "holdout_run.json"
    if marker.exists():
        sys.exit(f"refusing: the registered holdout already ran ({marker})")
    frozen = json.loads((OUTDIR / "frozen_config.json").read_text())
    cfg = M.Config(**frozen["config"])
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    marker.write_text(json.dumps({"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "code_commit": commit}, indent=2))
    pg = load(holdout=True)
    p = M.features(pg, cfg, holdout=True)
    e = p.reset_index(drop=True)
    e = e[e.eligible & (e.season == M.HOLDOUT)].reset_index(drop=True)
    m = M.mu(e, cfg)
    results = {s: score_market(e, m, cfg, s, pg) for s in M.STATS}
    probs = {s: M.prob_table(e, m, cfg, s) for s in M.STATS}
    blend = blend_analysis(e, probs)
    out = {"code_commit": commit, "frozen_config": frozen, "markets": results, "blend": blend}
    (OUTDIR / "holdout_results.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({s: {k: r[k] for k in ("passes", "B0", "B1", "B2", "B3", "B4", "slope")}
                      for s, r in results.items()}, indent=1, default=float))
    print(json.dumps({k: v for k, v in blend.items() if k != "reliability"}, indent=1, default=float))


# ---------- blend (PREREG §6 + amendment §9) ----------
ODDS_STAT = {"points": "pts", "rebounds": "reb", "assists": "ast", "threes": "fg3m", "points_rebounds": "pr",
             "points_assists": "pa", "rebounds_assists": "ra", "points_rebounds_assists": "pra", "steals": "stl",
             "blocks": "blk"}
W = [0.1, 0.2, 0.4, 0.6]


def implied(o):
    o = np.asarray(o, float)
    with np.errstate(divide="ignore", invalid="ignore"):          # np.where evaluates both branches
        return np.where(o < 0, -o / (-o + 100), 100 / (o + 100))


def market_probs() -> pd.DataFrame:
    """alt rungs with p_hold (§6.2) and p_anchor (§9.1), keyed to espn_id"""
    from engine.nba.crosswalk import match_odds_name, load_overrides, name_key
    props = pd.read_parquet(DATA / "lines" / f"hist_props_{M.HOLDOUT}.parquet")
    games = pd.read_parquet(DATA / "games.parquet")[["game_id", "home", "away"]]
    pg = pd.read_parquet(DATA / "player_games.parquet")
    idx = pg[pg.season == M.HOLDOUT][["espn_id", "player", "team"]].drop_duplicates(["espn_id", "team"])
    idx = idx.rename(columns={"player": "name"}).assign(key=lambda d: d.name.map(name_key))
    ov = load_overrides()
    props = props.merge(games, on="game_id")
    names = props[["game_id", "player", "home", "away"]].drop_duplicates(["game_id", "player"])
    names["espn_id"] = [match_odds_name(n, (h, a), idx, ov) for n, h, a in zip(names.player, names.home, names.away)]
    props = props.merge(names[["game_id", "player", "espn_id"]], on=["game_id", "player"])
    props["alt"] = props.market.str.endswith("_alternate")
    props["stat"] = props.market.str.replace("player_", "").str.replace("_alternate", "").map(ODDS_STAT)
    main = props[~props.alt].pivot_table(index=["game_id", "espn_id", "stat", "point"], columns="side",
                                         values="price", aggfunc="first").reset_index()
    main = main.dropna(subset=["Over", "Under"])
    main["io"], main["iu"] = implied(main.Over), implied(main.Under)
    main["hold"] = main.io + main.iu - 1
    main = main[(main.hold > -0.01) & (main.hold < 0.25)]
    main["q"] = main.io / (main.io + main.iu)
    main = main.sort_values("hold").drop_duplicates(["game_id", "espn_id", "stat"])     # one main line per player
    alt = props[props.alt & (props.side == "Over")].copy()
    alt["k"] = (alt.point + 0.5).round().astype(int)
    alt["ia"] = implied(alt.price)
    alt = alt.merge(main[["game_id", "espn_id", "stat", "point", "hold", "q"]].rename(columns={"point": "main_point"}),
                    on=["game_id", "espn_id", "stat"], how="left")
    # §6.2 hold-based: player's own hold, else the market's median hold in that game, else the game's median hold
    gm = main.groupby(["game_id", "stat"]).hold.median().rename("hold_gm")
    g_all = main.groupby("game_id").hold.median().rename("hold_g")
    alt = alt.join(gm, on=["game_id", "stat"]).join(g_all, on="game_id")
    alt["hold_src"] = np.where(alt.hold.notna(), "two-way", np.where(alt.hold_gm.notna(), "market median", "game median"))
    h = alt.hold.fillna(alt.hold_gm).fillna(alt.hold_g)
    alt["p_hold"] = alt.ia / (1 + h)
    # §9.1 ladder-anchored: markup r at the rung matching the main line
    anchor = alt[alt.main_point.notna() & np.isclose(alt.point, alt.main_point)]
    r = anchor.assign(r=anchor.ia / anchor.q)[["game_id", "espn_id", "stat", "r"]]
    r = r[(r.r > 0.5) & (r.r < 2.0)].drop_duplicates(["game_id", "espn_id", "stat"])
    alt = alt.merge(r, on=["game_id", "espn_id", "stat"], how="left")
    rg = r.groupby(["game_id", "stat"]).r.median().rename("r_gm")
    rs = r.groupby("stat").r.median().rename("r_season")
    alt = alt.join(rg, on=["game_id", "stat"]).join(rs, on="stat")
    alt["anchor_src"] = np.where(alt.r.notna(), "anchored", np.where(alt.r_gm.notna(), "game median",
                                                                    np.where(alt.r_season.notna(), "season median", None)))
    rr = alt.r.fillna(alt.r_gm).fillna(alt.r_season)
    alt["p_anchor"] = np.minimum(alt.ia / rr, 0.999)
    keep = ["game_id", "espn_id", "stat", "k", "price", "snapshot", "p_hold", "hold_src", "p_anchor", "anchor_src"]
    return alt[keep], {"outcomes": int(len(props)), "players_unmatched": int(names.espn_id.isna().sum()),
                       "players": int(len(names))}


def brier(p, y):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def blend_analysis(e: pd.DataFrame, probs: dict) -> dict:
    path = DATA / "lines" / f"hist_props_{M.HOLDOUT}.parquet"
    if not path.exists():
        return {"status": "no historical prices: blend evaluated forward-only (PREREG §6.1)"}
    alt, info = market_probs()
    model = []
    for s, t in probs.items():
        t = t.assign(game_id=np.repeat(e.game_id.to_numpy(), M.KMAX[s]),
                     espn_id=np.repeat(e.espn_id.to_numpy(), M.KMAX[s]), stat=s)
        model.append(t[["game_id", "espn_id", "stat", "k", "p", "y"]])
    model = pd.concat(model).rename(columns={"p": "p_model"})
    rows = alt.merge(model, on=["game_id", "espn_id", "stat", "k"])      # eligible player-games only
    rows = rows[rows.p_hold.notna() & rows.p_anchor.notna() & rows.p_hold.between(*SLOPE_SET)]
    out = {"price_info": info, "rows_total": int(len(rows)),
           "rows_by_market": rows.groupby("stat").size().to_dict(),
           "hold_src": rows.hold_src.value_counts().to_dict(), "anchor_src": rows.anchor_src.value_counts().to_dict()}
    pooled = rows[rows.stat.isin(CARD)]
    table = {}
    for meth in ("hold", "anchor"):
        pm = pooled[f"p_{meth}"]
        table[meth] = {"market_only": brier(pm, pooled.y), "model_only": brier(pooled.p_model, pooled.y)}
        for w in W:
            table[meth][f"w{w}"] = brier(w * pooled.p_model + (1 - w) * pm, pooled.y)
    out["pooled_brier"] = table
    qual = [w for w in W if all(table[m][f"w{w}"] < table[m]["market_only"] for m in ("hold", "anchor"))]
    chosen = min(qual, key=lambda w: (table["hold"][f"w{w}"], w)) if qual else 0.1
    out["qualifying_w"], out["pooled_w"] = qual, chosen
    per = {}
    for s in sorted(rows.stat.unique()):
        r = rows[rows.stat == s]
        d = {"n": int(len(r))}
        for meth in ("hold", "anchor"):
            pm = r[f"p_{meth}"]
            d[meth] = {"market_only": brier(pm, r.y), "model_only": brier(r.p_model, r.y),
                       **{f"w{w}": brier(w * r.p_model + (1 - w) * pm, r.y) for w in W}}
        if s in CARD:
            worse = any(d[m][f"w{chosen}"] > d[m]["market_only"] for m in ("hold", "anchor"))
            d["card_w"] = 0.1 if worse else chosen
            d["valve_triggered"] = bool(worse and chosen != 0.1)
        else:
            d["card_w"] = None                     # R+A calibration-only; steals/blocks model-only shadow
        per[s] = d
    out["per_market"] = per
    rel = {}
    for meth in ("hold", "anchor"):
        f = rows[rows[f"p_{meth}"].between(*BAND, inclusive="left")]
        rel[meth] = {"pooled_card": bins_table(f[f.stat.isin(CARD)].assign(p=lambda d: d[f"p_{meth}"], row=0),
                                               np.round(np.arange(0.60, 0.9501, 0.05), 2)),
                     **{s: bins_table(g.assign(p=g[f"p_{meth}"], row=0), np.round(np.arange(0.60, 0.9501, 0.05), 2))
                        for s, g in f.groupby("stat")}}
    out["market_only_reliability"] = rel
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["dev", "holdout"])
    a = ap.parse_args()
    dev() if a.mode == "dev" else holdout()


if __name__ == "__main__":
    main()
