"""
Edge Index v2 — CFB spreads backtest vs REAL CFBD lines (open + close).

Grades the same model against the OPENING line and the CLOSING line.
Beating closers is near-impossible; beating openers (bet early week)
is the realistic edge — and CLV (close moving toward our side) is the
proof it would persist.

Optional: preseason SP+ prior (needs CFBD_API_KEY; cached after).
Runs fully offline once data/cfbd_cache is populated.

Usage: python engine/cfb/spreads_backtest.py [--seasons 2022 2023 2024 2025]
"""
from __future__ import annotations
import argparse, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
API = "https://api.collegefootballdata.com"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", "data", "cfbd_cache")
K, MARGIN_CAP, HFA, CARRY = 0.06, 28, 2.6, 0.65
CLOSE_PREF = ["consensus", "DraftKings", "ESPN Bet",
              "William Hill (New Jersey)", "Bovada"]
OPEN_PREF = ["DraftKings", "Bovada", "ESPN Bet"]


def _fetch(endpoint: str, params: dict, key: str = "") -> list:
    fname = os.path.join(CACHE, endpoint.strip("/").replace("/", "_") + "_" +
                         "_".join(f"{k}{v}" for k, v in sorted(params.items())) + ".json")
    if os.path.exists(fname):
        return json.load(open(fname))
    if not key:
        raise FileNotFoundError(f"{fname} not cached and no CFBD_API_KEY set")
    import requests
    r = requests.get(API + endpoint, params=params,
                     headers={"Authorization": f"Bearer {key}"}, timeout=30)
    r.raise_for_status()
    os.makedirs(CACHE, exist_ok=True)
    json.dump(r.json(), open(fname, "w"))
    return json.load(open(fname))


def _pick(lines: list, pref: list, field: str):
    by = {ln["provider"]: ln.get(field) for ln in lines}
    for p in pref:
        if by.get(p) is not None:
            return float(by[p])
    return None


def load_season(season: int, key: str):
    games = pd.DataFrame(_fetch("/games", {"year": season,
                                           "seasonType": "regular"}, key))
    lmap = {}
    for g in _fetch("/lines", {"year": season, "seasonType": "regular"}, key):
        close = _pick(g.get("lines", []), CLOSE_PREF, "spread")
        opn = _pick(g.get("lines", []), OPEN_PREF, "spreadOpen")
        if close is not None:
            lmap[g["id"]] = (opn, close)
    return games, lmap


def sp_prior(season: int, key: str) -> dict:
    """Prior season's final SP+ ratings as preseason priors (leak-free)."""
    try:
        data = _fetch("/ratings/sp", {"year": season - 1}, key)
        return {d["team"]: float(d["rating"]) for d in data
                if d.get("team") and d.get("rating") is not None}
    except Exception:
        return {}


def run(seasons, key, thresholds=(1.5, 2.5, 3.5, 5.0)):
    ratings, bets = {}, []
    for season in seasons:
        games, lmap = load_season(season, key)
        games = games.dropna(subset=["homePoints", "awayPoints"])
        sp = sp_prior(season, key)
        if sp:  # SP+ prior (points-scaled). Full SP+ when no Elo history —
                # half-weighting a full-scale rating creates phantom dogs.
            teams = set(ratings) | set(sp)
            ratings = {t: (0.5 * ratings[t] * CARRY + 0.5 * sp[t])
                       if (t in ratings and t in sp)
                       else sp.get(t, ratings.get(t, 0.0) * CARRY)
                       for t in teams}
        else:
            ratings = {t: r * CARRY for t, r in ratings.items()}
        for week in sorted(games.week.unique()):
            wk = games[games.week == week]
            for _, g in wk.iterrows():
                h, a = g.homeTeam, g.awayTeam
                if h not in ratings or a not in ratings or g.id not in lmap:
                    continue
                model = -(ratings[h] - ratings[a] + HFA)
                opn, close = lmap[g.id]
                margin = g.homePoints - g.awayPoints
                for mkt, tag in ((opn, "open"), (close, "close")):
                    if mkt is None:
                        continue
                    edge = mkt - model
                    cover = margin + mkt
                    if cover == 0 or edge == 0:
                        continue
                    side = "HOME" if edge > 0 else "AWAY"
                    won = (cover > 0) if side == "HOME" else (cover < 0)
                    clv = (close - opn) * (1 if side == "HOME" else -1) \
                        if (tag == "open" and opn is not None) else None
                    bets.append(dict(season=season, week=week, home=h, away=a,
                                     vs=tag, market=mkt, model=round(model, 1),
                                     edge=round(abs(edge), 1), side=side,
                                     won=int(won), clv=clv,
                                     pnl=0.909 if won else -1.0))
            for _, g in wk.iterrows():
                h, a = g.homeTeam, g.awayTeam
                ratings.setdefault(h, 0.0); ratings.setdefault(a, 0.0)
                err = np.clip(g.homePoints - g.awayPoints, -MARGIN_CAP,
                              MARGIN_CAP) - (ratings[h] - ratings[a] + HFA)
                ratings[h] += K * err; ratings[a] -= K * err
    df = pd.DataFrame(bets)
    for tag in ("close", "open"):
        s = df[df.vs == tag]
        print(f"\n=== vs {tag.upper()}ING line — {len(s)} bets ===")
        print(f"{'thr':>5} {'n':>6} {'cover%':>8} {'roi':>8} {'clv(pts)':>9} {'clv+%':>7}")
        for thr in thresholds:
            b = s[s.edge >= thr]
            if not len(b):
                continue
            clv = b.clv.dropna()
            print(f"{thr:>5} {len(b):>6} {b.won.mean():>8.1%} "
                  f"{b.pnl.sum()/len(b):>8.2%}"
                  + (f" {clv.mean():>9.2f} {(clv>0).mean():>7.1%}" if len(clv) else ""))
        b = s[(s.edge >= 3.5) & (s.season == max(seasons))]
        if len(b):
            print(f"  holdout {max(seasons)} thr=3.5: {len(b)} bets, "
                  f"{b.won.mean():.1%} cover, ROI {b.pnl.sum()/len(b):+.2%}")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int,
                    default=[2022, 2023, 2024, 2025])
    ap.add_argument("--out", default="cfb_backtest_v2.csv")
    args = ap.parse_args()
    df = run(args.seasons, os.environ.get("CFBD_API_KEY", ""))
    df.to_csv(args.out, index=False)
    print(f"\nsaved -> {args.out}")
