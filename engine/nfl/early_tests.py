"""Registered early-line tests (docs/nfl/PREREG_EARLY_LINES.md): A movement, B early-bought CLV/return, C cross-market
lag, plus cross-book price gaps (descriptive). Runs ONCE (marker data/nfl/verify/early_run.json).

    python -m engine.nfl.early_tests
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from engine.nfl import verify_replay as vr
from engine.nfl import verify_pull as vp

common = vr.common
OUT = vr.OUT
FIT, TEST = range(1, 10), range(10, 19)
FACTORS = {"F1_man_zone": ["mz"], "F2_game_script_early": ["implied_total_e", "team_spread_e"],
           "F3_pass_tendency": ["proe", "neutral_pass"], "F4_defense_weak_points": ["opp_allowed", "home", "home_split"],
           "F6_unders": ["hot", "hot_x_tough", "big_fav"]}
METHODS = ("hold", "anchor")
SNAPS = ("E72", "E24")
B_THRESH, B_SENS = 0.02, (0.01, 0.03)
C_TRIG, C_SENS = 1.5, (1.0, 2.5)
TEAM_ABBR = vp.TEAMS


def clustered_mean_ci(x, games):
    d = pd.DataFrame({"x": np.asarray(x, float), "g": np.asarray(games)}).dropna()
    if d.empty:
        return np.nan, [np.nan, np.nan]
    by = d.groupby("g").x.agg(["sum", "size"])
    s, n = by["sum"].to_numpy(), by["size"].to_numpy()
    rng = np.random.default_rng(vr.SEED)
    idx = rng.integers(0, len(by), size=(vr.BOOT, len(by)))
    m = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return float(d.x.mean()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def dk(props, snap=None):
    p = props[props.book == "draftkings"] if "book" in props else props
    if snap:
        p = p[p.snap == snap]
    return p.assign(game_type="REG")


# ---------- game lines ----------
def game_lines(sch):
    """DK spread/total per game at OPEN (its week's Sunday-night snapshot), E72, E24, CLOSE: each game is matched to the
    bulk snapshot requested for it (early_pull.game_line_times), i.e. the returned timestamp within 10 min before it"""
    from engine.nfl.early_pull import game_line_times
    from datetime import timedelta
    gl = pd.read_parquet(OUT / "game_lines_2025.parquet")
    gl = gl[gl.book == "draftkings"].copy()
    gl["snapshot_t"] = pd.to_datetime(gl.snapshot, utc=True)
    rows = []
    for (snap_t, home, away), d in gl.groupby(["snapshot_t", "home_team", "away_team"]):
        sp = d[d.market == "spreads"]
        to = d[(d.market == "totals") & (d.name == "Over")]
        hs = sp[sp.name.map(TEAM_ABBR) == home].point
        if hs.empty or to.empty:
            continue
        rows.append(dict(snapshot_t=snap_t, home_team=home, away_team=away, home_spread=float(hs.iloc[0]),
                         total=float(to.point.iloc[0])))
    gl = pd.DataFrame(rows)
    opens = {int(tag.split("_w")[1]): t for tag, t in game_line_times(sch) if tag.startswith("OPEN_w")}
    lead = {"E72": timedelta(hours=72), "E24": timedelta(hours=24), "CLOSE": timedelta(minutes=10)}
    out = []
    for g in sch.itertuples():
        d = gl[(gl.home_team == g.home_team) & (gl.away_team == g.away_team)]
        rec = dict(game_id=g.game_id, week=g.week, home_team=g.home_team, away_team=g.away_team)
        for snap in ("OPEN", "E72", "E24", "CLOSE"):
            req = pd.Timestamp(opens[g.week] if snap == "OPEN" else g.kickoff - lead[snap])
            x = d[(d.snapshot_t <= req) & (d.snapshot_t > req - pd.Timedelta(minutes=10))]
            rec[f"hs_{snap}"] = x.home_spread.iloc[0] if len(x) else np.nan
            rec[f"tot_{snap}"] = x.total.iloc[0] if len(x) else np.nan
        out.append(rec)
    return pd.DataFrame(out)


def team_view(gl):
    """per (game, team): implied team total and team spread at each snapshot"""
    rows = []
    for g in gl.itertuples():
        for side in ("home", "away"):
            team = g.home_team if side == "home" else g.away_team
            rec = dict(game_id=g.game_id, week=g.week, team=team)
            for s in ("OPEN", "E72", "E24", "CLOSE"):
                hs, tot = getattr(g, f"hs_{s}"), getattr(g, f"tot_{s}")
                sp = hs if side == "home" else -hs
                rec[f"spread_{s}"] = sp
                rec[f"itt_{s}"] = (tot - sp) / 2
            rows.append(rec)
    return pd.DataFrame(rows)


# ---------- features (from the factor study tables; per player-game-stat) ----------
def features():
    fa = pd.read_parquet(OUT / "factor_rows_A.parquet")
    fb = pd.read_parquet(OUT / "factor_rows_B.parquet")
    cols = ["game_id", "player", "stat", "team", "mz", "proe", "neutral_pass", "opp_allowed", "home", "home_split", "hot",
            "hot_x_tough", "big_fav"]
    f = pd.concat([fa[cols], fb[[c for c in cols if c in fb]]]).drop_duplicates(["game_id", "player", "stat"])
    return f


# ---------- Test A ----------
def zfit(df, feats, fit):
    X = df[feats].astype(float)
    mu, sd = X[fit].mean(), X[fit].std().replace(0, 1)
    return ((X - mu) / sd).fillna(0.0).to_numpy()


def ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X1, y, rcond=None)[0]


def ols_pred(X, b):
    return np.column_stack([np.ones(len(X)), X]) @ b


def test_A(rows, feats):
    """rows: one per (S, game, player, stat, rung) with dp_hold, dp_anchor, features"""
    res = {}
    preds = {}
    for S in SNAPS:
        r = rows[rows.S == S].reset_index(drop=True)
        fit, te = r.week.isin(FIT).to_numpy(), r.week.isin(TEST).to_numpy()
        X = zfit(r, feats, fit)
        out = {"rows_fit": int(fit.sum()), "rows_test": int(te.sum())}
        for m in METHODS:
            y = r[f"dp_{m}"].to_numpy()
            pred = np.full(len(r), np.nan)
            for s in r.stat.unique():
                sm = (r.stat == s).to_numpy()
                b = ols(X[fit & sm], y[fit & sm])
                pred[sm] = ols_pred(X[sm], b)
            base = np.full(len(r), np.nan)
            for s in r.stat.unique():
                sm = (r.stat == s).to_numpy()
                base[sm] = y[fit & sm].mean()
            mse_m, mse_b = np.mean((pred[te] - y[te]) ** 2), np.mean((base[te] - y[te]) ** 2)
            gain, ci = clustered_mean_ci((pred[te] - y[te]) ** 2 - (base[te] - y[te]) ** 2, r.game_id.to_numpy()[te])
            dirn, dci = clustered_mean_ci((np.sign(pred[te] - base[te]) == np.sign(y[te] - base[te])).astype(float),
                                          r.game_id.to_numpy()[te])
            out[m] = {"mse_model": float(mse_m), "mse_const": float(mse_b), "mse_diff": gain, "mse_diff_ci95": ci,
                      "beats_const": bool(mse_m < mse_b), "distinct": bool(ci[1] < 0),
                      "direction_acc": dirn, "direction_ci95": dci}
            preds[(S, m)] = pred
        out["passes_this_snapshot"] = all(out[m]["beats_const"] for m in METHODS)
        res[S] = out
    res["passes"] = any(res[S]["passes_this_snapshot"] for S in SNAPS)
    return res, preds


# ---------- Test B ----------
def legs_B(rows, preds, S, thresh):
    r = rows[rows.S == S].reset_index(drop=True)
    r = r.assign(pred=preds[(S, "hold")])
    te = r[r.week.isin(TEST) & r.imp_S.between(0.60, 0.95, inclusive="left") & (r.pred >= thresh)]
    return te.sort_values("pred", ascending=False).drop_duplicates(["game_id", "player", "stat"])


def metrics_B(legs):
    if legs.empty:
        return {"n": 0}
    out = {"n": int(len(legs)), "games": int(legs.game_id.nunique())}
    for m in METHODS:
        out[f"clv_{m}"], out[f"clv_{m}_ci95"] = clustered_mean_ci(legs[f"pc_{m}"] - legs[f"pS_{m}"], legs.game_id)
    out["hit_minus_close"], out["hit_minus_close_ci95"] = clustered_mean_ci(legs.y - legs.pc_hold, legs.game_id)
    ret = np.where(legs.y == 1, vr.dec(legs.price_S) - 1, -1.0)
    out["roi"], out["roi_ci95"] = clustered_mean_ci(ret, legs.game_id)
    out["hit"] = float(legs.y.mean())
    out["clv_confirmed"] = all(out[f"clv_{m}_ci95"][0] > 0 for m in METHODS)
    out["profitable"] = bool(out["roi_ci95"][0] > 0)
    return out


# ---------- Test C ----------
def test_C(mains_S, close_alt, close_main, tv, trig, kind="itt"):
    """mains_S: main lines at buy snapshots with team; returns metrics for triggered bets"""
    out = {}
    bets = []
    for S, prev in (("E72", "OPEN"), ("E24", "E72")):
        t = tv.assign(d_itt=tv[f"itt_{S}"] - tv[f"itt_{prev}"], d_spread=tv[f"spread_{S}"] - tv[f"spread_{prev}"])
        m = mains_S[mains_S.S == S].merge(t[["game_id", "team", "d_itt", "d_spread"]], on=["game_id", "team"])
        if kind == "itt":
            m = m[m.d_itt.abs() >= trig].assign(side=np.where(m.d_itt >= trig, "Over", "Under"))
        else:
            m = m[m.d_spread >= trig].assign(side="Over")
        bets.append(m.assign(S=S))
    b = pd.concat(bets) if bets else pd.DataFrame()
    if b.empty:
        return {"n": 0}, b
    b = attach_close(b, close_alt, close_main)
    b = b[b.pc_hold.notna() & b.pc_anchor.notna()]
    over = b.side == "Over"
    b["p_buy"] = np.where(over, b.q, 1 - b.q)
    b["price_buy"] = np.where(over, b.Over, b.Under)
    for m in METHODS:
        b[f"pc_side_{m}"] = np.where(over, b[f"pc_{m}"], 1 - b[f"pc_{m}"])
    b["win"] = np.where(over, b.y_over == 1, b.y_over == 0).astype(float)
    res = {"n": int(len(b)), "games": int(b.game_id.nunique()), "sides": b.side.value_counts().to_dict(),
           "by_snapshot": b.S.value_counts().to_dict()}
    for m in METHODS:
        res[f"clv_{m}"], res[f"clv_{m}_ci95"] = clustered_mean_ci(b[f"pc_side_{m}"] - b.p_buy, b.game_id)
    res["hit_minus_close"], res["hit_minus_close_ci95"] = clustered_mean_ci(b.win - b.pc_side_hold, b.game_id)
    ret = np.where(b.win == 1, vr.dec(b.price_buy) - 1, -1.0)
    res["roi"], res["roi_ci95"] = clustered_mean_ci(ret, b.game_id)
    res["clv_positive_both"] = all(res[f"clv_{m}_ci95"][0] > 0 for m in METHODS)
    res["exploitable"] = bool(res["roi_ci95"][0] > 0)
    return res, b


def attach_close(b, close_alt, close_main):
    """closing de-vigged P(Over) at the buy line: the alt rung at line+0.5 (both methods) else the same main line"""
    b = b.assign(rung=b.point + 0.5)
    ca = close_alt[["game_id", "player", "stat", "rung", "p_hold", "p_anchor"]].rename(
        columns={"p_hold": "pc_hold", "p_anchor": "pc_anchor"})
    b = b.merge(ca, on=["game_id", "player", "stat", "rung"], how="left")
    cm = close_main[["game_id", "player", "stat", "point", "q_close"]]
    b = b.merge(cm, on=["game_id", "player", "stat", "point"], how="left")
    for m in METHODS:
        b[f"pc_{m}"] = b[f"pc_{m}"].fillna(b.q_close)
    return b


def mains_table(props_snap):
    mn = props_snap[props_snap.market.isin(vr.MAIN)].pivot_table(
        index=["game_id", "week", "player", "market", "point", "home_team", "away_team"], columns="side", values="price",
        aggfunc="first").reset_index().dropna(subset=["Over", "Under"])
    io, iu = vr.implied(mn.Over), vr.implied(mn.Under)
    mn["q"] = io / (io + iu)
    mn["stat"] = mn.market.map(vr.MAIN)
    return mn


def lag_regression(mains_S, close_alt, close_main, tv):
    rows = []
    for S, prev in (("E72", "OPEN"), ("E24", "E72")):
        t = tv.assign(d_itt=tv[f"itt_{S}"] - tv[f"itt_{prev}"])
        m = mains_S[mains_S.S == S].merge(t[["game_id", "team", "d_itt"]], on=["game_id", "team"]).dropna(subset=["d_itt"])
        rows.append(m)
    m = attach_close(pd.concat(rows), close_alt, close_main).dropna(subset=["pc_hold"])
    m["dp"] = m.pc_hold - m.q
    x, y, g = m.d_itt.to_numpy(), m.dp.to_numpy(), m.game_id.to_numpy()
    def slope(ix):
        xx, yy = x[ix], y[ix]
        return float(np.polyfit(xx, yy, 1)[0]) if len(xx) > 2 else np.nan
    full = slope(np.arange(len(x)))
    games = pd.unique(g)
    gidx = {k: np.where(g == k)[0] for k in games}
    rng = np.random.default_rng(vr.SEED)
    bs = []
    for _ in range(2000):
        pick = rng.choice(games, size=len(games))
        bs.append(slope(np.concatenate([gidx[k] for k in pick])))
    return {"n": int(len(m)), "slope_dp_per_itt_point": full, "slope_ci95": [float(np.nanpercentile(bs, 2.5)),
                                                                              float(np.nanpercentile(bs, 97.5))],
            "positive_distinct": bool(np.nanpercentile(bs, 2.5) > 0)}


# ---------- cross-book ----------
def cross_book(allp, outcomes_settle):
    out = {}
    for snap in ("CLOSE_ALL", "E24", "E72"):
        p = allp[(allp.snap == snap) & allp.market.isin(vr.ALT) & (allp.side == "Over")].copy()
        p["key"] = p.player.map(common.norm_name)
        p["dec"] = vr.dec(p.price)
        d = p[p.book == "draftkings"]
        d = d[pd.Series(vr.implied(d.price), index=d.index).between(0.60, 0.95, inclusive="left")]
        others = p[p.book != "draftkings"]
        bb = others.loc[others.groupby(["game_id", "key", "market", "point"]).dec.idxmax()]
        bb = bb[["game_id", "key", "market", "point", "dec", "book"]].rename(columns={"dec": "best_dec", "book": "best_book"})
        m = d.merge(bb, on=["game_id", "key", "market", "point"], how="left")
        have = m.best_dec.notna()
        better = have & (m.best_dec > m.dec + 1e-9)
        imp_gain = (1 / m.dec - 1 / m.best_dec) * 100
        best_amer = np.where(m.best_dec >= 2, (m.best_dec - 1) * 100, -100 / (m.best_dec - 1))
        res = {"dk_floor_rungs": int(len(m)), "matched_elsewhere": int(have.sum()),
               "share_other_better": round(float(better[have].mean()) * 100, 2) if have.any() else None,
               "median_gain_implied_pts_when_better": round(float(imp_gain[better].median()), 2) if better.any() else None,
               "mean_gain_implied_pts_when_better": round(float(imp_gain[better].mean()), 2) if better.any() else None,
               "median_gain_cents_when_better": round(float(np.median(best_amer[better] - m.price[better])), 1) if better.any() else None,
               "best_book_counts": m[better].best_book.value_counts().to_dict(),
               "book_coverage_vs_dk_floor_rungs": {b: round(float(m.merge(others[others.book == b][["game_id", "key", "market", "point"]]
                                                                           .drop_duplicates(), how="inner").shape[0] / max(len(m), 1)) * 100, 1)
                                                   for b in sorted(others.book.unique())}}
        if snap == "CLOSE_ALL":
            s = outcomes_settle(m.assign(market=m.market.map(vr.ALT), rung=m.point + 0.5,
                                         teams=list(zip(m.home_team, m.away_team))))
            s = s[s.result.isin(["WIN", "LOSS"])]
            for label, dcol in (("dk_price", "dec"), ("best_available_price", "best_or_dk")):
                s = s.assign(best_or_dk=np.where(s.best_dec.notna(), np.maximum(s.best_dec, s.dec), s.dec))
                ret = np.where(s.result == "WIN", s[dcol] - 1, -1.0)
                mu, ci = clustered_mean_ci(ret, s.game_id)
                res[f"flat_roi_{label}"] = {"n": int(len(s)), "roi": mu, "ci95": ci}
        out[snap] = res
    return out


def main():
    marker = OUT / "early_run.json"
    if marker.exists():
        sys.exit(f"refusing: the registered early-line tests already ran ({marker})")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=vr.ROOT).stdout.strip()
    marker.write_text(json.dumps({"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "code_commit": commit}, indent=2))
    sch = vp.schedule()
    sch = sch[sch.game_type == "REG"]
    w, played, known = vr.outcomes(2025)

    def settle_alt(a):
        a = vr.settle(a.rename(columns={"stat": "market_"}).assign(market=lambda d: d.market_), w, played, known, 2025)
        return a.drop(columns=["market"]).rename(columns={"market_": "stat"})

    close_props = pd.read_parquet(OUT / "hist_props_2025.parquet")
    close_props = close_props[close_props.game_type == "REG"]
    close_alt, _ = vr.price_tables(close_props)
    close_alt = settle_alt(close_alt)
    cm = mains_table(close_props).rename(columns={"q": "q_close"})
    early = pd.read_parquet(OUT / "early_props_2025.parquet")
    feats = features()
    gl = game_lines(sch)
    tv = team_view(gl)
    # ---- rows for A/B: rungs priced by DK at S and at CLOSE ----
    rows = []
    mains = []
    for S in SNAPS:
        e = dk(early, S)
        if e.empty:
            continue
        ea, _ = vr.price_tables(e)
        m = ea[["game_id", "week", "player", "stat", "rung", "price", "p_hold", "p_anchor"]].rename(
            columns={"price": "price_S", "p_hold": "pS_hold", "p_anchor": "pS_anchor"}).merge(
            close_alt[["game_id", "player", "stat", "rung", "p_hold", "p_anchor", "result"]].rename(
                columns={"p_hold": "pc_hold", "p_anchor": "pc_anchor"}), on=["game_id", "player", "stat", "rung"])
        m = m[m.result.isin(["WIN", "LOSS"])].assign(S=S, y=lambda d: (d.result == "WIN").astype(float))
        m["dp_hold"], m["dp_anchor"] = m.pc_hold - m.pS_hold, m.pc_anchor - m.pS_anchor
        m["imp_S"] = vr.implied(m.price_S)
        rows.append(m)
        mn = mains_table(e).assign(S=S)
        mains.append(mn)
    rows = pd.concat(rows).dropna(subset=["dp_hold", "dp_anchor"])
    rows = rows.merge(feats, on=["game_id", "player", "stat"], how="left")
    # F2-early: DK's game lines at the same early snapshot (team implied total, team spread; + = underdog)
    tvl = pd.concat([tv[["game_id", "team", f"itt_{S}", f"spread_{S}"]]
                     .rename(columns={f"itt_{S}": "implied_total_e", f"spread_{S}": "team_spread_e"}).assign(S=S)
                     for S in SNAPS])
    rows = rows.merge(tvl, on=["game_id", "team", "S"], how="left")
    res = {"code_commit": commit, "rows_A": rows.groupby("S").size().to_dict(),
           "rows_A_by_week_half": rows.assign(h=np.where(rows.week <= 9, "fit", "test")).groupby(["S", "h"]).size()
           .rename(lambda x: f"{x[0]}:{x[1]}").to_dict(), "A": {}, "B": {}, "C": {}}
    passing = []
    model_preds = {}
    for f, fs in FACTORS.items():
        r, preds = test_A(rows, fs)
        res["A"][f] = r
        model_preds[f] = preds
        if r["passes"]:
            passing += fs
    res["A_passing_features"] = passing
    if passing:
        rc, pc = test_A(rows, passing)
        res["A"]["combined"] = rc
        model_preds["combined"] = pc
    # ---- B ----
    for f, preds in model_preds.items():
        res["B"][f] = {}
        for S in SNAPS:
            res["B"][f][S] = {f"t{t}": metrics_B(legs_B(rows, preds, S, t)) for t in (B_THRESH,) + B_SENS}
    res["B"]["model_free_all_floor_band"] = {}
    for S in SNAPS:
        r = rows[(rows.S == S) & rows.week.isin(TEST) & rows.imp_S.between(0.60, 0.95, inclusive="left")]
        res["B"]["model_free_all_floor_band"][S] = metrics_B(r)
        rall = rows[(rows.S == S) & rows.imp_S.between(0.60, 0.95, inclusive="left")]
        res["B"]["model_free_all_floor_band"][S + "_all_weeks"] = metrics_B(rall)
    # ---- C ----
    mains = pd.concat(mains)
    mains = mains.merge(feats[["game_id", "player", "stat", "team"]].drop_duplicates(["game_id", "player", "stat"]),
                        on=["game_id", "player", "stat"], how="inner")
    # settle main-line Over at buy line: Over wins iff stat >= point + 0.5
    st = vr.settle(mains.assign(market=mains.stat, rung=mains.point + 0.5,
                                teams=list(zip(mains.home_team, mains.away_team))), w, played, known, 2025)
    mains = st[st.result.isin(["WIN", "LOSS"])].assign(y_over=lambda d: (d.result == "WIN").astype(float))
    for kind in ("itt", "spread"):
        res["C"][kind] = {}
        for trig in (C_TRIG,) + C_SENS:
            allw, b = test_C(mains, close_alt, cm, tv, trig, kind)
            t10 = {"n": 0}
            if len(b):
                bt = b[b.week.isin(TEST)]
                t10 = {"n": int(len(bt))}
                for m in METHODS:
                    t10[f"clv_{m}"], t10[f"clv_{m}_ci95"] = clustered_mean_ci(bt[f"pc_side_{m}"] - bt.p_buy, bt.game_id)
                ret = np.where(bt.win == 1, vr.dec(bt.price_buy) - 1, -1.0)
                t10["roi"], t10["roi_ci95"] = clustered_mean_ci(ret, bt.game_id)
            res["C"][kind][f"trig{trig}"] = {"all_weeks": allw, "weeks_10_18": t10}
    res["C"]["lag_regression"] = lag_regression(mains, close_alt, cm, tv)
    res["C"]["game_line_coverage"] = {s: int(gl[f"tot_{s}"].notna().sum()) for s in ("OPEN", "E72", "E24", "CLOSE")}
    # ---- cross-book ----
    res["cross_book"] = cross_book(early, lambda a: vr.settle(a, w, played, known, 2025))
    res["coverage"] = {"early_props_outcomes": int(len(early)),
                       "books": early.book.value_counts().to_dict(),
                       "dk_games_by_snap": early[early.book == "draftkings"].groupby("snap").game_id.nunique().to_dict(),
                       "dk_rec_alt_players_per_game_by_snap": early[(early.book == "draftkings") &
                                                                    (early.market == "player_receptions_alternate")]
                       .groupby(["snap", "game_id"]).player.nunique().groupby("snap").median().to_dict()}
    (OUT / "early_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k in ("rows_A", "rows_A_by_week_half", "A_passing_features",
                                                            "coverage")}, indent=1, default=float))


if __name__ == "__main__":
    main()
