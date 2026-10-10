"""Backtest, CLV and calibration (Phase 3 brief §6).

Everything is out of sample: leave-one-season-out (LOSO) within 2022-2024
for tuning (margin model AND distribution refit without the test season),
frozen params for the 2025 holdout and 2026 to date.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from engine.cfb.model import distribution as dist, margin_model as mm

RUNGS = np.arange(-35.5, 36.0, 1.0)            # every half-point (x.5) rung
BINS = [(50, 60), (60, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95), (95, 100.01)]
EDGE_THRESH = (1.5, 3, 5)


def bet_inputs(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["absline"] = d.open_margin.abs()
    return d


# ------------------------------------------------------------------ projections
def project(d: pd.DataFrame, model: dict, dparams: dict) -> tuple[pd.DataFrame, np.ndarray]:
    d = bet_inputs(d)
    d["proj"] = mm.predict(d, model)
    d = d.dropna(subset=["proj", "total_bet"])
    P = dist.pmf(d.proj, d.absline, d.total_bet, dparams)
    sig = dist.sigma([dparams["a"], dparams["b"], dparams["c"]], d.absline, d.total_bet)
    d["sigma"] = sig
    return d, P


def fit_dist(d: pd.DataFrame, model: dict, shape: str, keys) -> dict:
    d = bet_inputs(d)
    d["proj"] = mm.predict(d, model)
    e = d.dropna(subset=["proj", "margin_home", "total_bet"])
    f = dist.fit(e.margin_home - e.proj, e.absline, e.total_bet, shape, orient=np.sign(e.proj))
    if keys:
        f["spikes"] = dist.fit_spikes(e.margin_home, e.proj, e.absline, e.total_bet, f, keys)
    return f


def loso_frames(d: pd.DataFrame, groups, seasons, shape, keys):
    """Concatenated LOSO projections + pmfs for the tuning seasons."""
    frames, Ps = [], []
    for s in seasons:
        tr = d[d.season.isin(seasons) & (d.season != s)]
        m = mm.fit(tr, groups)
        f = fit_dist(tr, m, shape, keys)
        te, P = project(d[(d.season == s)].dropna(subset=["margin_home"]), m, f)
        frames.append(te)
        Ps.append(P)
    return pd.concat(frames), np.vstack(Ps)


def choose_distribution(d, groups, seasons) -> tuple[str, list, pd.DataFrame]:
    rows, best = [], None
    for shape in dist.SHAPES:
        for kname, keys in (("none", []), ("3,7,10,14", [3, 7, 10, 14]),
                            ("3,7,10,14,17,21", [3, 7, 10, 14, 17, 21])):
            g, P = loso_frames(d, groups, seasons, shape, keys)
            ll = dist.loglik(g.margin_home, P).mean()
            rows.append({"shape": shape, "spikes": kname, "loso_loglik_per_game": ll})
            if best is None or ll > best[0]:
                best = (ll, shape, keys)
    return best[1], best[2], pd.DataFrame(rows).sort_values("loso_loglik_per_game", ascending=False)


# ------------------------------------------------------------------ evaluations
def accuracy(g: pd.DataFrame, by=None) -> pd.DataFrame:
    def f(x):
        x = x.dropna(subset=["close_margin"])
        return pd.Series({"games": len(x),
                          "model_MAE": (x.margin_home - x.proj).abs().mean(),
                          "open_MAE": (x.margin_home - x.open_margin).abs().mean(),
                          "close_MAE": (x.margin_home - x.close_margin).abs().mean()})
    return f(g).to_frame().T if by is None else g.groupby(by).apply(f).reset_index()


def clv(g: pd.DataFrame, label: str) -> pd.DataFrame:
    x = g.dropna(subset=["close_margin"])
    edge = x.proj - x.open_margin
    move = x.close_margin - x.open_margin           # + = market moved toward home
    rows = []
    for t in EDGE_THRESH:
        s = edge.abs() >= t
        e, mv = edge[s], move[s]
        toward = (np.sign(mv) == np.sign(e)) & (mv != 0)
        away = (np.sign(mv) == -np.sign(e)) & (mv != 0)
        signed = (mv * np.sign(e))
        n = int(s.sum())
        ci = binomtest(int(toward.sum()), int((mv != 0).sum())).proportion_ci(method="wilson") if (mv != 0).any() else None
        rows.append({"games": label, "|proj-open| >=": t, "n": n,
                     "moved_toward_pct": 100 * toward.mean() if n else np.nan,
                     "moved_away_pct": 100 * away.mean() if n else np.nan,
                     "no_move_pct": 100 * (mv == 0).mean() if n else np.nan,
                     "toward_share_of_moves_pct": 100 * toward.sum() / max((mv != 0).sum(), 1),
                     "ci95": f"{100 * ci.low:.0f}-{100 * ci.high:.0f}" if ci else "",
                     "avg_move_toward_model_pts": signed.mean() if n else np.nan})
    out = pd.DataFrame(rows)
    out.attrs["corr"] = float(np.corrcoef(edge, move)[0, 1]) if len(x) > 2 else np.nan
    return out


def ats(g: pd.DataFrame, label: str, vs: str) -> pd.DataFrame:
    """Bet the model side at the open (or close) spread when |edge| >= t. -110 pricing."""
    if vs == "open":
        x = g.dropna(subset=["open_margin"]).assign(line_m=lambda z: z.open_margin)
    else:
        lm = g.close_margin.fillna(g.consensus_close_margin)
        x = g.assign(line_m=lm).dropna(subset=["line_m"])
    rows = []
    for t in EDGE_THRESH:
        edge = x.proj - x.line_m
        y = x[edge.abs() >= t]
        e = edge[edge.abs() >= t]
        res = y.margin_home - y.line_m                 # >0 home covers
        push = res == 0
        win = (np.sign(res) == np.sign(e))[~push]
        n, k = len(win), int(win.sum())
        ci = binomtest(k, n).proportion_ci(method="wilson") if n else None
        rows.append({"games": label, "vs": vs, "|edge| >=": t, "bets": n, "wins": k,
                     "win_pct": 100 * k / n if n else np.nan,
                     "ci95": f"{100 * ci.low:.1f}-{100 * ci.high:.1f}" if ci else "",
                     "roi_pct_at_-110": 100 * (k * (100 / 110) - (n - k)) / n if n else np.nan,
                     "pushes": int(push.sum())})
    return pd.DataFrame(rows)


def rung_pairs(g: pd.DataFrame, P: np.ndarray) -> pd.DataFrame:
    """(game, side, rung, p, outcome) for every x.5 rung, both sides, p >= 0.5."""
    out = []
    m = g.margin_home.to_numpy()
    gid = g.game_id.to_numpy()
    for side in ("home", "away"):
        tm = m if side == "home" else -m
        for L in RUNGS:
            c, _ = dist.cover(P, L, side)
            out.append(pd.DataFrame({"game_id": gid, "side": side, "rung": L, "p": c,
                                     "y": (tm + L > 0).astype(float)}))
    r = pd.concat(out, ignore_index=True)
    r = r[r.p >= 0.5]
    r["kind"] = np.where(r.rung < 0, "fav (laying)", "dog (getting)")
    return r


def reliability(r: pd.DataFrame, n_boot: int = 500, seed: int = 0) -> pd.DataFrame:
    """Binned predicted vs actual with game-level bootstrap CIs."""
    r = r.copy()
    r["bin"] = pd.cut(100 * r.p, [b[0] for b in BINS] + [BINS[-1][1]], right=False,
                      labels=[f"{a}-{min(b, 100):.0f}" for a, b in BINS])
    games = r.game_id.unique()
    rng = np.random.default_rng(seed)
    grp = r.groupby("game_id")
    idx = {g: ix for g, ix in grp.indices.items()}
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(games, len(games))
        ix = np.concatenate([idx[g] for g in pick])
        boots.append(r.iloc[ix].groupby("bin", observed=False).y.mean())
    boots = pd.concat(boots, axis=1)
    t = r.groupby("bin", observed=False).agg(n=("y", "size"), games=("game_id", "nunique"),
                                             pred_pct=("p", "mean"), actual_pct=("y", "mean"))
    t["pred_pct"] *= 100
    t["actual_pct"] *= 100
    t["ci95_lo"] = 100 * boots.quantile(0.025, axis=1)
    t["ci95_hi"] = 100 * boots.quantile(0.975, axis=1)
    t["actual_minus_pred"] = t.actual_pct - t.pred_pct
    return t.reset_index()


def scores(r: pd.DataFrame) -> dict:
    p = r.p.clip(1e-6, 1 - 1e-6)
    return {"pairs": len(r), "brier": float(((r.p - r.y) ** 2).mean()),
            "log_loss": float(-(r.y * np.log(p) + (1 - r.y) * np.log(1 - p)).mean())}


def band(r: pd.DataFrame, lo=0.75, hi=0.90, n_boot: int = 500, seed: int = 1) -> dict:
    x = r[(r.p >= lo) & (r.p < hi)]
    games = x.game_id.unique()
    rng = np.random.default_rng(seed)
    idx = x.groupby("game_id").indices
    b = []
    for _ in range(n_boot):
        pick = rng.choice(games, len(games))
        ix = np.concatenate([idx[g] for g in pick])
        b.append(x.y.to_numpy()[ix].mean() - x.p.to_numpy()[ix].mean())
    return {"pairs": len(x), "games": len(games), "pred_pct": 100 * x.p.mean(),
            "actual_pct": 100 * x.y.mean(),
            "gap_pts": 100 * (x.y.mean() - x.p.mean()),
            "gap_ci95": f"{100 * np.percentile(b, 2.5):+.1f} to {100 * np.percentile(b, 97.5):+.1f}"}
