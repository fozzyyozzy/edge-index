"""Market-anchored totals distribution (Phase 5B outcome, Tim's rule of 2026-10-12).

    python -m engine.cfb.totals.anchored        # LOSO checks on 2022-24 -> engine/cfb/totals/params.json

No totals model beat the opening total (k_t weeks 4+ pooled +0.12 [-0.11, +0.33] even with
observed kickoff weather), so totals are MARKET-ANCHORED: center = the market total
(history: the provider's open; live: DK's current total), sigma_t = a + c * total fit by MLE
on 2022-24 residuals (actual - open), NO recency weighting. Key-total spikes are chosen inside
each LOSO fold (the N most over-represented totals in the training seasons) and kept only if
held-out log-likelihood improves. The 2025 totals holdout is NOT run. Totals legs are
PAPER-UNPROVEN.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb.totals import features as tf, model as tm

PARAMS = Path(__file__).resolve().parent / "params.json"
TUNE = [2022, 2023, 2024]
N_KEYS = (0, 4, 6)


def pmf_anchored(center, sig, spikes: dict | None = None, iters: int = 4) -> np.ndarray:
    """Integer-total pmf, mean preserved at `center` after spikes (like the Phase 3 spread pmf)."""
    target = np.asarray(center, float)[:, None]
    s = np.asarray(sig, float)[:, None]
    loc = target.copy()

    def binned(loc):
        from scipy import stats
        p = stats.norm.cdf((tm.TSUP[None, :] + 0.5 - loc) / s) - stats.norm.cdf((tm.TSUP[None, :] - 0.5 - loc) / s)
        for k, f in (spikes or {}).items():
            p[:, tm.TSUP == int(k)] *= f
        return p / p.sum(1, keepdims=True)
    for _ in range(iters):
        p = binned(loc)
        loc = loc + (target - (p * tm.TSUP[None, :]).sum(1, keepdims=True))
    return binned(loc)


def fit_keys(actual, P, n) -> dict:
    if n == 0:
        return {}
    a = np.asarray(actual, int)
    obs = pd.Series(a).value_counts().reindex(range(len(tm.TSUP))).fillna(0).to_numpy()
    imp = P.sum(0)
    ratio = np.where(imp > 0.004 * len(a), obs / np.maximum(imp, 1e-9), 0)
    keys = np.argsort(-ratio)[:n]
    return {int(k): float(obs[k] / imp[k]) for k in keys}


def loglik(actual, P):
    idx = np.clip(np.asarray(actual, int), 0, len(tm.TSUP) - 1)
    return np.log(np.clip(P[np.arange(len(P)), idx], 1e-12, None))


def main() -> int:
    d = tf.load()
    d = d[d.season.isin(TUNE)].dropna(subset=["total_open", "actual_total"])
    rows = []
    for n in N_KEYS:
        ll = []
        for s in TUNE:
            tr, te = d[d.season != s], d[d.season == s]
            p = tm.fit_sigma(tr.actual_total - tr.total_open, tr.total_open)
            Ptr = pmf_anchored(tr.total_open, tm.sigma_t(p, tr.total_open))
            keys = fit_keys(tr.actual_total, Ptr, n)
            P = pmf_anchored(te.total_open, tm.sigma_t(p, te.total_open), keys)
            ll.append(loglik(te.actual_total, P))
        rows.append({"key_totals": n, "loso_loglik_per_game": float(np.concatenate(ll).mean())})
    t = pd.DataFrame(rows).sort_values("loso_loglik_per_game", ascending=False)
    best_n = int(t.key_totals.iloc[0])
    p = tm.fit_sigma(d.actual_total - d.total_open, d.total_open)
    keys = fit_keys(d.actual_total, pmf_anchored(d.total_open, tm.sigma_t(p, d.total_open)), best_n)
    params = {"status": "market_anchored", "label": "PAPER-UNPROVEN",
              "center": "market total (history: provider open; live: DK current total)",
              "sigma_t": {"a": float(p[0]), "c": float(p[1])}, "key_totals": keys,
              "rho_margin_total_resid": 0.075,
              "decision": "k_t weeks 4+ pooled +0.12 [-0.11, +0.33] with observed weather (2022-24): "
                          "CI spans 0 -> per Tim's rule, no 2025 totals holdout",
              "tuned_on": TUNE, "recency_weighting": False,
              "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "loso_key_total_choice": t.to_dict(orient="records")}
    PARAMS.write_text(json.dumps(params, indent=2) + "\n")
    print(t.to_string(index=False))
    print(json.dumps({k: v for k, v in params.items() if k != "loso_key_total_choice"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
