"""DK's implied CFB alt-spread distribution (Phase 4 brief §4).

    python -m engine.cfb.lines.ladder_fit      # writes the LADDERFIT block of PHASE4_REPORT.md

De-vig: DK lists every alt rung with its complement (home at r <-> away at -r), so each
pair is normalized proportionally: p_home = imp_home / (imp_home + imp_away). Unpaired rungs
(none so far) fall back to removing the snapshot's main-spread hold proportionally.

Fit: DK's no-vig P(home covers at r) is modelled with the SAME machinery as our Phase 3
distribution (engine.cfb.model.distribution.pmf): integer margins, zero mass at 0, mean
preserved, centered at DK's own main line, sigma = a + c * total (DK main total), and key-number
multipliers at 3/7/10/14/17/21. Parameters minimize squared error in no-vig probability over
all captured rungs (one ladder per game: the latest snapshot unless --label is given).
Reproduction error: |fit - DK no-vig| in percentage points, and in American odds after
re-applying DK's average ladder hold.
"""
from __future__ import annotations
import argparse
import glob

import numpy as np
import pandas as pd
from scipy import optimize

from engine.cfb.lines.capture import SNAP
from engine.cfb.lines.movement import md, write_block
from engine.cfb.model import distribution as dist, run as mrun

KEYS = [3, 7, 10, 14, 17, 21]


def implied(o):
    o = np.asarray(o, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(o < 0, -o / (-o + 100), 100 / (o + 100))


def american(p):
    p = np.asarray(p, float)
    return np.where(p >= 0.5, -100 * p / (1 - p), 100 * (1 - p) / p)


def cents(a, b):
    """distance between two American prices, continuous across +-100"""
    f = lambda x: np.where(x < 0, x + 100, x - 100)  # noqa: E731
    return np.abs(f(np.asarray(a, float)) - f(np.asarray(b, float)))


def load(label: str | None = None, season: int = 2026) -> pd.DataFrame:
    """One ladder per game (latest snapshot, or the latest with `label`), with DK main line/total."""
    lf = sorted(glob.glob(str(SNAP / f"dk_ladders_{season}_wk*.csv")))
    mf = sorted(glob.glob(str(SNAP / f"dk_main_{season}_wk*.csv")))
    if not lf:
        return pd.DataFrame()
    L = pd.concat(pd.read_csv(f) for f in lf)
    M = pd.concat(pd.read_csv(f) for f in mf)
    if label:
        L = L[L.label == label]
    last = L.groupby("game_id").captured_at_utc.max().rename("snap")
    L = L.merge(last, on="game_id")
    L = L[L.captured_at_utc == L.snap]
    h = L[L.is_home == 1][["game_id", "captured_at_utc", "week", "rung", "price"]]
    a = L[L.is_home == 0][["game_id", "rung", "price"]].assign(rung=lambda x: -x.rung)
    P = h.merge(a, on=["game_id", "rung"], how="outer", suffixes=("_home", "_away"))
    sp = M[(M.market == "spreads") & (M.is_home == 1)][["game_id", "captured_at_utc", "point", "price"]]
    sa = M[(M.market == "spreads") & (M.is_home == 0)][["game_id", "captured_at_utc", "price"]]
    tot = M[(M.market == "totals") & (M.team == "Over")][["game_id", "captured_at_utc", "point"]]
    main = (sp.merge(sa, on=["game_id", "captured_at_utc"], suffixes=("", "_away"))
              .merge(tot.rename(columns={"point": "total"}), on=["game_id", "captured_at_utc"], how="left")
              .rename(columns={"point": "main_spread", "price": "main_home_price",
                               "price_away": "main_away_price"}))
    P = P.merge(main, on=["game_id", "captured_at_utc"], how="left")
    ih, ia = implied(P.price_home), implied(P.price_away)
    paired = P.price_home.notna() & P.price_away.notna()
    main_hold = implied(P.main_home_price) + implied(P.main_away_price) - 1
    P["p_dk"] = np.where(paired, ih / (ih + ia), ih / (1 + main_hold))
    P["pair_hold"] = np.where(paired, ih + ia - 1, np.nan)
    P["paired"] = paired
    P["mu_dk"] = -P.main_spread
    return P.dropna(subset=["p_dk", "mu_dk", "total"])


def model_cover(P: pd.DataFrame, params: dict, mu_col: str = "mu_dk") -> np.ndarray:
    """P(home covers at rung) for each row, our pmf machinery with `params`."""
    out = np.empty(len(P))
    for gid, idx in P.groupby("game_id").indices.items():
        r = P.iloc[idx]
        pm = dist.pmf([r[mu_col].iloc[0]], [abs(r.main_spread.iloc[0])], [r.total.iloc[0]], params)
        out[idx] = dist.cover(np.repeat(pm, len(r), axis=0), r.rung.to_numpy(), "home")[0]
    return out


def fit(P: pd.DataFrame) -> dict:
    def unpack(th):
        return {"shape": "normal", "a": th[0], "b": 0.0, "c": th[1],
                "spikes": {k: float(np.exp(v)) for k, v in zip(KEYS, th[2:])}}

    def loss(th):
        return float(((model_cover(P, unpack(th)) - P.p_dk) ** 2).mean())
    x0 = [12.0, 0.06] + [0.0] * len(KEYS)
    res = optimize.minimize(loss, x0, method="Nelder-Mead",
                            options={"maxiter": 3000, "xatol": 1e-4, "fatol": 1e-9})
    out = unpack(res.x)
    out["rmse_pp"] = float(np.sqrt(res.fun) * 100)
    return out


def per_game_sigma(P: pd.DataFrame) -> pd.DataFrame:
    """sigma per game with no spikes (diagnostic dispersion)."""
    rows = []
    for gid, r in P.groupby("game_id"):
        def loss(s):
            return float(((model_cover(r, {"shape": "normal", "a": s[0], "b": 0, "c": 0, "spikes": {}})
                           - r.p_dk) ** 2).mean())
        s = optimize.minimize(loss, [15.0], method="Nelder-Mead").x[0]
        rows.append({"game_id": gid, "sigma": s, "line": r.main_spread.iloc[0], "total": r.total.iloc[0]})
    return pd.DataFrame(rows)


def report(label: str | None = None) -> dict:
    P = load(label)
    if P.empty:
        write_block("LADDERFIT", "_No ladders captured yet._")
        return {}
    ours = mrun.dist_params(mrun.load_params())
    f = fit(P)
    P["p_fit"] = model_cover(P, f)
    P["p_ours_at_dk"] = model_cover(P, ours)
    hold = P.pair_hold.mean()
    P["price_fit"] = american(np.clip(P.p_fit * (1 + hold), 0.005, 0.995))
    band = P[(P.price_home > -1000) & (P.price_home < 1000)]
    err = {"rungs": len(P), "games": P.game_id.nunique(),
           "MAE_pp_fit": 100 * (P.p_fit - P.p_dk).abs().mean(),
           "MAE_pp_ours_at_dk_line": 100 * (P.p_ours_at_dk - P.p_dk).abs().mean(),
           "median_cents_fit (-1000..+1000)": float(np.median(cents(band.price_fit, band.price_home))),
           "p90_cents_fit": float(np.percentile(cents(band.price_fit, band.price_home), 90)),
           "avg_pair_hold_%": 100 * hold}
    sig = per_game_sigma(P)
    tot = P.groupby("game_id").total.first()
    med_total = float(tot.median())
    our_sig = ours["a"] + ours["b"] * 7 + ours["c"] * med_total
    dk_sig = f["a"] + f["c"] * med_total
    comp = pd.DataFrame({
        "": ["sigma at median total (%.1f)" % med_total, "sigma per 10 pts of total"]
        + [f"spike x at |margin|={k}" for k in KEYS],
        "DK implied (fit)": [dk_sig, 10 * f["c"]] + [f["spikes"][k] for k in KEYS],
        "ours (Phase 3)": [our_sig, 10 * ours["c"]] + [ours["spikes"].get(k, 1.0) for k in KEYS]})
    # where DK and ours differ by rung distance from the line (getting vs laying side)
    P["dist_from_line"] = P.rung + P.main_spread          # >0: home getting more than the main line
    P["diff_pp"] = 100 * (P.p_ours_at_dk - P.p_dk)
    by = (P.assign(b=pd.cut(P.dist_from_line, [-45, -14, -7, -3, 0, 3, 7, 14, 45]))
            .groupby("b", observed=True).agg(rungs=("diff_pp", "size"), ours_minus_dk_pp=("diff_pp", "mean")))
    snaps = P.groupby("captured_at_utc").game_id.nunique()
    T = [f"_Generated by `python -m engine.cfb.lines.ladder_fit` from {len(snaps)} snapshot time(s): "
         f"{', '.join(f'{s} ({n} games)' for s, n in snaps.items())}. All rungs are x.5 and paired; "
         f"de-vig = proportional within each pair._\n",
         "**DK's implied ladder vs ours**\n", md(comp, "{:.3f}"),
         f"\nPer-game sigma (no spikes): median {sig.sigma.median():.2f}, IQR "
         f"{sig.sigma.quantile(.25):.2f}-{sig.sigma.quantile(.75):.2f}; corr with total "
         f"{np.corrcoef(sig.sigma, sig.total)[0, 1]:+.2f}, with |line| "
         f"{np.corrcoef(sig.sigma, sig.line.abs())[0, 1]:+.2f}.\n",
         "\n**Reproduction error** (fit vs DK's actual rung prices; the CFB 'estimated vs real' check)\n",
         md(pd.DataFrame([err]), "{:.2f}"),
         "\n**Ours (centered at DK's line) minus DK no-vig, by rung distance from the main line** "
         "(home perspective, both sides pooled via pairing)\n",
         md(by.reset_index().rename(columns={"b": "rung - line (pts)"}), "{:+.2f}")]
    write_block("LADDERFIT", "\n".join(T))
    print("\n".join(T))
    return {"fit": f, "err": err}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default=None)
    a = ap.parse_args()
    report(a.label)
