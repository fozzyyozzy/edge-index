"""docs/nfl/PREREG_UNDERS.md: main-line Unders at the best Maryland-book price.

    python -m engine.nfl.unders_test     # registered 2024 test ONCE (marker data/nfl/verify/unders_run.json) + descriptives

Descriptive (non-gating): 2025 closing (same bet), 2026 weeks 3-6 DK-only from the live pipeline's two-way pulls, and
2-leg cross-game Under parlays priced at a single listed book (2024, 2025).
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from engine.nfl import verify_replay as vr
from engine.nfl.early_tests import clean, clustered_mean_ci

OUT = vr.OUT
BOOKS = ["draftkings", "fanduel", "betmgm", "williamhill_us", "fanatics", "betrivers"]
MAIN = {"player_receptions": "receptions", "player_reception_yds": "rec_yds"}
PK = ["game_id", "week", "player", "stat", "home_team", "away_team"]


def offers(props, books):
    c = props[props.market.isin(MAIN) & (props.side == "Under") & props.book.isin(books)].copy()
    c["stat"] = c.market.map(MAIN)
    c["dec"] = vr.dec(c.price)
    return c


def reference_lines(u):
    """DK's line when DK posts one, else the most common listed line (ties -> lower)"""
    dkl = u[u.book == "draftkings"].groupby(PK).point.first().rename("dk_line")
    mode = u.groupby(PK).point.agg(lambda s: s.value_counts().sort_index().idxmax()).rename("mode_line")
    ref = pd.concat([dkl, mode], axis=1).reset_index()
    ref["line"] = ref.dk_line.fillna(ref.mode_line)
    return ref[PK + ["line"]]


def bets(props, season, books=BOOKS, dk_only=False):
    u = offers(props, ["draftkings"] if dk_only else books)
    at = u.merge(reference_lines(u), on=PK)
    at = at[at.point == at.line]
    by_book = at.pivot_table(index=PK + ["point"], columns="book", values="dec", aggfunc="max")
    best = at.loc[at.groupby(PK + ["point"]).dec.idxmax()][PK + ["point", "dec", "book"]] \
        .rename(columns={"dec": "best_dec", "book": "best_book"})
    b = best.merge(at.groupby(PK + ["point"]).book.nunique().rename("n_books").reset_index(), on=PK + ["point"])
    w, played, known = vr.outcomes(season)
    s = vr.settle(b.assign(market=b.stat, rung=b.point, teams=list(zip(b.home_team, b.away_team))), w, played, known, season)
    counts = s.result.value_counts().to_dict()
    s = s[s.result.isin(["WIN", "LOSS"])].copy()                     # VOID / UNGRADEABLE excluded (counted)
    s["res"] = np.where(s.value < s.point, "WIN", np.where(s.value == s.point, "PUSH", "LOSS"))
    s["ret"] = np.where(s.res == "WIN", s.best_dec - 1, np.where(s.res == "PUSH", 0.0, -1.0))
    return s, counts, by_book


def summary(s, col="ret"):
    if s.empty:
        return {"n": 0}
    mu, ci = clustered_mean_ci(s[col], s.game_id)
    return {"n": int(len(s)), "games": int(s.game_id.nunique()), "hit_pct": round(float((s.res == "WIN").mean()) * 100, 2),
            "push": int((s.res == "PUSH").sum()), "avg_price_dec": round(float(s.best_dec.mean()), 4),
            "avg_implied_pct": round(float((1 / s.best_dec).mean()) * 100, 2),
            "roi_pct": round(mu * 100, 2), "ci95_pct": [round(c * 100, 2) for c in ci]}


def report(s):
    out = {"pooled": summary(s), "by_market": {st: summary(x) for st, x in s.groupby("stat")},
           "halves": {h: summary(x) for h, x in s.assign(h=np.where(s.week <= 9, "wk1-9", "wk10-18")).groupby("h")},
           "best_book_counts": s.best_book.value_counts().to_dict(), "books_at_line_median": float(s.n_books.median())}
    return out


def parlays(s, by_book):
    """every cross-game pair within a week; both legs at the single listed book with the best combined price"""
    s = s.reset_index(drop=True)
    key = PK + ["point"]
    D = by_book.reindex(pd.MultiIndex.from_frame(s[key])).to_numpy(dtype=float)        # legs x books (NaN = not offered)
    rows = []
    for wk, idx in s.groupby("week").groups.items():
        idx = np.asarray(list(idx))
        d = D[idx]                                                                        # n x B
        prod = d[:, None, :] * d[None, :, :]                                              # n x n x B
        with np.errstate(invalid="ignore"):
            best = np.nanmax(np.where(np.isnan(prod), -np.inf, prod), axis=2)
        g = s.game_id.to_numpy()[idx]
        iu, ju = np.triu_indices(len(idx), k=1)
        ok = (g[iu] != g[ju]) & np.isfinite(best[iu, ju])
        iu, ju = iu[ok], ju[ok]
        bi = best[iu, ju]
        ri, rj = s.res.to_numpy()[idx][iu], s.res.to_numpy()[idx][ju]
        # same book: price each leg at that book for push handling (a push leg -> single at the other leg's price)
        bidx = np.nanargmax(np.where(np.isnan(prod[iu, ju]), -np.inf, prod[iu, ju]), axis=1)
        di, dj = d[iu, bidx], d[ju, bidx]
        win_i, win_j = ri == "WIN", rj == "WIN"
        push_i, push_j = ri == "PUSH", rj == "PUSH"
        ret = np.where(win_i & win_j, bi - 1, -1.0)
        ret = np.where(push_i & win_j, dj - 1, ret)
        ret = np.where(push_j & win_i, di - 1, ret)
        ret = np.where(push_i & push_j, 0.0, ret)
        straight = (s.ret.to_numpy()[idx][iu] + s.ret.to_numpy()[idx][ju]) / 2           # same legs as straights, 0.5u each
        rows.append(pd.DataFrame({"week": wk, "ret": ret, "both": win_i & win_j, "straight": straight,
                                  "dec": bi}))
    p = pd.concat(rows)
    legs_hit = float((s.res == "WIN").mean())
    def wk_ci(x):
        by = p.groupby("week")[x].agg(["sum", "size"])
        rng = np.random.default_rng(vr.SEED)
        ix = rng.integers(0, len(by), size=(2000, len(by)))
        m = by["sum"].to_numpy()[ix].sum(axis=1) / by["size"].to_numpy()[ix].sum(axis=1)
        return [round(float(np.percentile(m, 2.5)) * 100, 2), round(float(np.percentile(m, 97.5)) * 100, 2)]
    return {"pairs": int(len(p)), "weeks": int(p.week.nunique()), "avg_parlay_dec": round(float(p.dec.mean()), 3),
            "both_win_pct": round(float(p.both.mean()) * 100, 2), "leg_hit_squared_pct": round(legs_hit ** 2 * 100, 2),
            "parlay_roi_pct": round(float(p.ret.mean()) * 100, 2), "parlay_roi_ci95_week_bootstrap": wk_ci("ret"),
            "same_legs_straight_roi_pct": round(float(p.straight.mean()) * 100, 2),
            "same_legs_straight_ci95_week_bootstrap": wk_ci("straight")}


def dk_2026_wk3_6():
    """live pipeline's committed DK two-way pulls (last pregame pull per game), DK price at DK line"""
    from engine.nfl.verify_pull import TEAMS
    frames = []
    for wk in range(3, 7):
        t = pd.read_csv(vr.ROOT / "automation" / "lines" / f"twoway_2026_w{wk}.csv")
        t = t[t.Market.isin(["receptions", "rec_yds"])].dropna(subset=["Over", "Under"])
        t = t[pd.to_datetime(t.PulledAt, utc=True) < pd.to_datetime(t.Commence, utc=True)]
        t[["away_n", "home_n"]] = t.Game.str.split(" @ ", expand=True)
        frames.append(t.assign(file_week=wk))
    t = pd.concat(frames)
    sch = vr.cached_read("nflverse schedule")
    sch = sch[(sch.season == 2026) & (sch.game_type == "REG")]
    t["home_team"], t["away_team"] = t.home_n.map(TEAMS), t.away_n.map(TEAMS)
    t = t.merge(sch[["game_id", "week", "home_team", "away_team"]], on=["home_team", "away_team"])
    t = t.sort_values("PulledAt").drop_duplicates(["game_id", "Player", "Market"], keep="last")
    props = pd.DataFrame({"game_id": t.game_id, "week": t.week, "player": t.Player,
                          "market": t.Market.map({v: k for k, v in MAIN.items()}), "side": "Under", "point": t.Line,
                          "price": t.Under, "book": "draftkings", "home_team": t.home_team, "away_team": t.away_team})
    s, counts, _ = bets(props, 2026, dk_only=True)
    return {"result_counts": counts, **report(s), "weeks": sorted(s.week.unique().tolist())}


def main():
    marker = OUT / "unders_run.json"
    if marker.exists():
        sys.exit(f"refusing: the registered Unders test already ran ({marker})")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=vr.ROOT).stdout.strip()
    marker.write_text(json.dumps({"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "code_commit": commit}, indent=2))
    p24 = pd.read_parquet(OUT / "close_mains_2024.parquet")
    s24, c24, bb24 = bets(p24, 2024)
    d24, dc24, _ = bets(p24, 2024, dk_only=True)
    reg = report(s24)
    n = reg["pooled"]["n"]
    verdict = "INSUFFICIENT" if n < 2000 else ("PASS" if reg["pooled"]["ci95_pct"][0] > 0 else "FAIL")
    res = {"code_commit": commit, "registered_2024": {"verdict": verdict, "result_counts": c24, **reg,
                                                      "dk_only": {"result_counts": dc24, **report(d24)}}}
    (OUT / "unders_results.json").write_text(json.dumps(clean(res), indent=1))        # registered result saved first
    e = pd.read_parquet(OUT / "early_props_2025.parquet")
    p25 = e[e.snap == "CLOSE_ALL"]
    s25, c25, bb25 = bets(p25, 2025)
    d25, _, _ = bets(p25, 2025, dk_only=True)
    res["descriptive_2025"] = {"result_counts": c25, **report(s25), "dk_only": report(d25)}
    res["descriptive_2026_wk3_6_dk_only"] = dk_2026_wk3_6()
    res["parlays_2leg_same_book"] = {"2024": parlays(s24, bb24), "2025": parlays(s25, bb25)}
    (OUT / "unders_results.json").write_text(json.dumps(clean(res), indent=1))
    print("saved data/nfl/verify/unders_results.json; verdict", verdict)


if __name__ == "__main__":
    main()
