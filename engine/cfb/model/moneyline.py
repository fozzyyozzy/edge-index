"""Phase 5A: moneylines from the frozen Phase 3 distribution (no new parameters).

    python -m engine.cfb.model.moneyline      # -> ML block of docs/cfb/PHASE5_REPORT.md

Win probability = P(margin > 0) from the frozen pmf (no ties: CFB has overtime), centered on
the Phase 3 projected margin. Projections: LOSO for 2022-2024 (model + distribution refit
without the test season, as in Phase 3), frozen params for 2025 (holdout) and 2026 (to date).

Moneylines: CFBD has CLOSING moneylines only (no opener), so every comparison is vs the
close: conservative, since our projection is anchored at the open.
Provider: Bovada 2022-2025 (same book as the spread history), DraftKings 2026; DK 2023-25
is reported as a cross-check. De-vig: proportional within the two-way pair.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from engine.cfb import config
from engine.cfb.model import backtest as bt, distribution as dist, features, margin_model as mm, run as mrun

REPORT = config.ROOT / "docs" / "cfb" / "PHASE5_REPORT.md"
BINS = [(50, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95), (95, 100.01)]
RNG = np.random.default_rng(0)


def md(df, fmt="{:.2f}"):
    if df is None or len(df) == 0:
        return "_(none)_\n"
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in df.itertuples(index=False))


def write_block(name: str, text: str) -> None:
    doc = REPORT.read_text(encoding="utf-8") if REPORT.exists() else "# CFB Phase 5 Report\n"
    b, e = f"<!-- AUTO:{name}:BEGIN -->", f"<!-- AUTO:{name}:END -->"
    blk = f"{b}\n{text}\n{e}"
    doc = (doc[:doc.index(b)] + blk + doc[doc.index(e) + len(e):]) if b in doc and e in doc \
        else doc + f"\n{blk}\n"
    REPORT.write_text(doc, encoding="utf-8")


def implied(o):
    o = np.asarray(o, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(o < 0, -o / (-o + 100), 100 / (o + 100))


def payout(o):
    o = np.asarray(o, float)
    return np.where(o < 0, 100 / -o, o / 100)


# ------------------------------------------------------------------ frames
def projections() -> tuple[pd.DataFrame, np.ndarray]:
    """Rows = games with a projection; P = pmf matrix (rows aligned)."""
    params = mrun.load_params()
    dp = mrun.dist_params(params)
    d = mm.prep(features.load())
    d = d[d.margin_home.notna()]
    g1, P1 = bt.loso_frames(d, params["groups"], mrun.TUNE, dp["shape"], list(dp.get("spikes", {})))
    g1 = g1.assign(eval_set="2022-2024 LOSO")
    later = d[d.season.isin([mrun.HOLDOUT, mrun.LIVE])]
    g2, P2 = bt.project(later, {"groups": params["groups"], "coef": params["coef"]}, dp)
    g2 = g2.assign(eval_set=np.where(g2.season == mrun.HOLDOUT, "2025 holdout", "2026 to date"))
    return pd.concat([g1, g2], ignore_index=True), np.vstack([P1, P2])


def attach_ml(g: pd.DataFrame, provider_hist="Bovada", provider_live="DraftKings") -> pd.DataFrame:
    L = pd.read_parquet(config.CLEAN / "lines.parquet")
    L = L.dropna(subset=["home_ml", "away_ml"])
    out = g.copy()
    for tag, prov in (("ml", None), ("dk", "DraftKings")):
        if prov is None:
            pick = L[((L.provider == provider_hist) & (L.season < config.CURRENT_SEASON))
                     | ((L.provider == provider_live) & (L.season == config.CURRENT_SEASON))]
        else:
            pick = L[L.provider == prov]
        pick = pick.drop_duplicates("game_id")[["game_id", "provider", "home_ml", "away_ml", "spread"]]
        pick = pick.rename(columns={"provider": f"{tag}_provider", "home_ml": f"{tag}_home_ml",
                                    "away_ml": f"{tag}_away_ml", "spread": f"{tag}_close_spread"})
        out = out.merge(pick, on="game_id", how="left")
        ih, ia = implied(out[f"{tag}_home_ml"]), implied(out[f"{tag}_away_ml"])
        out[f"{tag}_nv_home"] = ih / (ih + ia)
        out[f"{tag}_hold"] = ih + ia - 1
    return out


# ------------------------------------------------------------------ evaluations
def side_pairs(g: pd.DataFrame, p_home: np.ndarray, tag="ml") -> pd.DataFrame:
    """Both sides per game: model p, no-vig p, posted price, outcome."""
    won_home = (g.margin_home > 0).astype(float).to_numpy()
    rows = []
    for side in ("home", "away"):
        h = side == "home"
        rows.append(pd.DataFrame({
            "game_id": g.game_id.to_numpy(), "eval_set": g.eval_set.to_numpy(), "side": side,
            "p": p_home if h else 1 - p_home,
            "nv": (g[f"{tag}_nv_home"] if h else 1 - g[f"{tag}_nv_home"]).to_numpy(),
            "price": g[f"{tag}_{side}_ml"].to_numpy(),
            "y": won_home if h else 1 - won_home}))
    return pd.concat(rows, ignore_index=True).dropna(subset=["p"])


def calibration(x: pd.DataFrame, col="p") -> pd.DataFrame:
    x = x[x[col] >= 0.5].copy()
    x["bin"] = pd.cut(100 * x[col], [b[0] for b in BINS] + [BINS[-1][1]], right=False,
                      labels=[f"{a}-{min(b, 100):.0f}" for a, b in BINS])
    rows = []
    for b, grp in x.groupby("bin", observed=False):
        if grp.empty:
            continue
        boots = [grp.y.to_numpy()[RNG.integers(0, len(grp), len(grp))].mean() for _ in range(1000)]
        rows.append({"bin": str(b), "n": len(grp), "pred_%": 100 * grp[col].mean(),
                     "actual_%": 100 * grp.y.mean(), "ci95_lo": 100 * np.percentile(boots, 2.5),
                     "ci95_hi": 100 * np.percentile(boots, 97.5),
                     "actual-pred": 100 * (grp.y.mean() - grp[col].mean())})
    return pd.DataFrame(rows)


def band_gap(x: pd.DataFrame, col="p", lo=0.65, hi=0.90) -> dict:
    b = x[(x[col] >= lo) & (x[col] < hi)]
    if b.empty:
        return {"n": 0}
    boots = []
    for _ in range(2000):
        i = RNG.integers(0, len(b), len(b))       # one favorite side per game in-band -> game-level
        boots.append(b.y.to_numpy()[i].mean() - b[col].to_numpy()[i].mean())
    return {"n": len(b), "pred_%": 100 * b[col].mean(), "actual_%": 100 * b.y.mean(),
            "gap_pts": 100 * (b.y.mean() - b[col].mean()),
            "ci95": f"{100 * np.percentile(boots, 2.5):+.1f} to {100 * np.percentile(boots, 97.5):+.1f}"}


def scores(x: pd.DataFrame) -> dict:
    h = x[x.side == "home"].dropna(subset=["nv"])
    def brier(p): return float(((p - h.y) ** 2).mean())
    def ll(p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return float(-(h.y * np.log(p) + (1 - h.y) * np.log(1 - p)).mean())
    return {"games": len(h), "brier_model": brier(h.p), "brier_novig": brier(h.nv),
            "logloss_model": ll(h.p), "logloss_novig": ll(h.nv)}


def strategy(x: pd.DataFrame, label: str) -> pd.DataFrame:
    x = x.dropna(subset=["nv", "price"]).copy()
    x["edge"] = x.p - x.nv
    x["ev"] = x.p * payout(x.price) - (1 - x.p)
    b = x[(x.edge >= 0.03) & (x.ev > 0)].copy()
    b["units"] = np.where(b.y == 1, payout(b.price), -1.0)
    b["band"] = pd.cut(b.price, [-100000, -300, -150, 150, 100000],
                       labels=["<= -300", "-300 to -150", "-150 to +150", "dogs > +150"], right=True)
    rows = []
    for band, grp in [("all", b)] + list(b.groupby("band", observed=False)):
        if grp.empty:
            rows.append({"set": label, "band": band, "bets": 0})
            continue
        boots = [grp.units.to_numpy()[RNG.integers(0, len(grp), len(grp))].mean() for _ in range(2000)]
        k = int(grp.y.sum())
        rows.append({"set": label, "band": str(band), "bets": len(grp), "wins": k,
                     "win_%": 100 * k / len(grp), "avg_price": grp.price.median(),
                     "breakeven_%": 100 * (1 / (1 + payout(grp.price))).mean(),
                     "roi_%": 100 * grp.units.mean(),
                     "roi_ci95": f"{100 * np.percentile(boots, 2.5):+.1f} to {100 * np.percentile(boots, 97.5):+.1f}"})
    return pd.DataFrame(rows)


def consistency(g: pd.DataFrame, dp: dict, tag="ml") -> tuple[dict, pd.DataFrame]:
    """Win prob implied by the book's own CLOSE spread (our distribution centered there)
    vs the book's no-vig moneyline. When they disagree by >= 3 pts, which was right?"""
    x = g.dropna(subset=[f"{tag}_close_spread", f"{tag}_nv_home", "total_bet"]).copy()
    mu = -x[f"{tag}_close_spread"]
    P = dist.pmf(mu, mu.abs(), x.total_bet, dp)
    x["p_spread"] = (P * (dist.M[None, :] > 0)).sum(axis=1)
    x["y"] = (x.margin_home > 0).astype(float)
    x["diff"] = x.p_spread - x[f"{tag}_nv_home"]
    dis = x[x["diff"].abs() >= 0.03]
    def brier(p, y): return float(((p - y) ** 2).mean())
    # the side each one prefers relative to the other: the spread says home is more (diff>0) or less likely
    right_spread = np.where(dis["diff"] > 0, dis.y == 1, dis.y == 0)
    out = {"games": len(x), "mean_|diff|_pts": 100 * x["diff"].abs().mean(),
           "disagree_ge3": len(dis),
           "brier_spread_implied (disagreements)": brier(dis.p_spread, dis.y) if len(dis) else np.nan,
           "brier_ml_novig (disagreements)": brier(dis[f"{tag}_nv_home"], dis.y) if len(dis) else np.nan,
           "spread-favored side won_%": 100 * right_spread.mean() if len(dis) else np.nan,
           "mean_pred_spread_side_%": 100 * np.where(dis["diff"] > 0, dis.p_spread, 1 - dis.p_spread).mean()
           if len(dis) else np.nan,
           "mean_pred_ml_side_%": 100 * np.where(dis["diff"] > 0, dis[f"{tag}_nv_home"],
                                                1 - dis[f"{tag}_nv_home"]).mean() if len(dis) else np.nan}
    # where do they disagree? by spread size
    x["abs_spread"] = x[f"{tag}_close_spread"].abs()
    by = (x.assign(b=pd.cut(x.abs_spread, [-0.1, 3, 7, 10, 14, 21, 60]))
            .groupby("b", observed=True).agg(games=("diff", "size"),
                                              spread_minus_ml_pts=("diff", lambda v: 100 * v.mean()),
                                              home_win_pct=("y", lambda v: 100 * v.mean()))
            .reset_index().rename(columns={"b": "|close spread|"}))
    return out, by


def main() -> int:
    params = mrun.load_params()
    dp = mrun.dist_params(params)
    g, P = projections()
    g = attach_ml(g)
    p_home = (P * (dist.M[None, :] > 0)).sum(axis=1)
    g["p_home_win"] = p_home
    T = ["_Generated by `python -m engine.cfb.model.moneyline`. No new parameters. **Moneylines are "
         "CLOSING lines** (CFBD has no ML open), so all results are vs the close: conservative. "
         "Provider: Bovada 2022-25, DK 2026; DK 2023-25 cross-check. De-vig: proportional._\n"]
    cov = g.groupby("eval_set").agg(games=("game_id", "size"),
                                    with_ml=("ml_home_ml", lambda v: v.notna().sum()),
                                    with_dk_ml=("dk_home_ml", lambda v: v.notna().sum()),
                                    mean_hold_pct=("ml_hold", lambda v: 100 * v.mean())).reset_index()
    T += ["### Coverage\n", md(cov)]

    band_rows, score_rows, strat, cal_tables = [], [], [], []
    for es in ["2022-2024 LOSO", "2025 holdout", "2026 to date"]:
        sub = g[g.eval_set == es]
        x = side_pairs(sub, sub.p_home_win.to_numpy())
        x_nv = x.dropna(subset=["nv"])
        band_rows.append({"set": es, "who": "model", **band_gap(x_nv, "p")})
        band_rows.append({"set": es, "who": "book no-vig", **band_gap(x_nv, "nv")})
        score_rows.append({"set": es, **scores(x)})
        strat.append(strategy(x, es))
        cal_tables.append((es, calibration(x_nv, "p")))
        if es != "2026 to date":
            xd = side_pairs(sub, sub.p_home_win.to_numpy(), tag="dk").dropna(subset=["nv"])
            if len(xd):
                score_rows.append({"set": es + " (vs DK)", **scores(xd)})
                strat.append(strategy(xd, es + " (vs DK)"))
    T += ["\n### 65-90% band calibration (favorite side; the focus band ~ -185 to -900)\n",
          md(pd.DataFrame(band_rows)),
          "\n### Model vs book no-vig: Brier and log loss (home side, one row per game)\n",
          md(pd.DataFrame(score_rows), "{:.4f}"),
          "\n### Paper strategy: model - no-vig >= 3 pts AND EV > 0 at the posted (close) price\n",
          md(pd.concat(strat, ignore_index=True), "{:.1f}")]
    for es, ct in cal_tables:
        T += [f"\n**Calibration, {es}** (model win %, favorite side, game-level bootstrap CI)\n", md(ct, "{:.1f}")]

    cons_rows, cons_by = [], []
    for es in ["2022-2024 LOSO", "2025 holdout", "2026 to date"]:
        o, by = consistency(g[g.eval_set == es], dp)
        cons_rows.append({"set": es, **o})
        cons_by.append(by.assign(set=es))
    T += ["\n### ML/spread consistency (book's own close spread through our distribution vs its no-vig ML)\n",
          md(pd.DataFrame(cons_rows), "{:.4f}"),
          "\nBy spread size (spread-implied minus ML no-vig, home perspective):\n",
          md(pd.concat(cons_by, ignore_index=True))]
    write_block("ML", "\n".join(T))
    print("\n".join(T))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
