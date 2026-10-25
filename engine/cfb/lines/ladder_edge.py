"""Shape edge vs full edge on every captured DK rung; the paper rung log (Phase 4 brief §5).

    python -m engine.cfb.lines.ladder_edge          # log new weeks' bet ladders, grade, report

For each captured rung and side (team perspective, rung L > 0 = getting points):
  shape edge = P_ours(team covers | centered at DK's own main line) - DK no-vig P
  full edge  = P_ours(team covers | centered at our projection)       - DK no-vig P
  EV at the posted price (per 1 unit staked), for both.
Ours = Phase 3 frozen distribution (normal, sigma = a + b|line| + c*total, key spikes, mean
preserved). Our projection = frozen margin model at DK's main line in the same snapshot:
  proj = L + k[bucket] * (ratings_margin - L) + b_qb * qb_delta   (targets file)

Paper log (append-only, committed): data/cfb/lines/paper_rungs_<season>.csv gets every
GETTING-points rung (Phase 3 operating rule) priced -500..-150 with shape or full edge >= 3 pp.
Laying rungs meeting the same test go in with kind=laying (diagnostic only).
Tim, 2026-10-25 (rung log stalled at week 7: this logger had only ever been run once, by hand, on a
Monday manual snapshot): each week is logged ONCE, from its bet-time ladder only, the same rule as
the forward test: per game, the first 'bet' ladder snapshot taken on the week's Tuesday before
18:00 ET, else the first ladder snapshot on or after that Tuesday. No later price is ever logged.
A week already in the log is never re-logged (week 7 keeps its original rows). Run automatically by
`forward weekly` and the Tuesday weekly task; safe to re-run.
Grades are written to paper_rungs_graded_<season>.csv (rebuilt each run from games.parquet).
"""
from __future__ import annotations
import glob

import numpy as np
import pandas as pd
from scipy import stats

from engine.cfb import config
from engine.cfb.lines.capture import LINES, SNAP, TARGETS
from engine.cfb.lines.ladder_fit import implied
from engine.cfb.lines.movement import md, write_block
from engine.cfb.model import distribution as dist, run as mrun

EDGE_PP = 3.0
PRICE_LO, PRICE_HI = -500, -150
BAR = {"min_games": 60, "lift_pp": 3.0}


def payout(price):
    price = np.asarray(price, float)
    return np.where(price < 0, 100 / -price, price / 100)


def ladders(season: int) -> pd.DataFrame:
    lf = sorted(glob.glob(str(SNAP / f"dk_ladders_{season}_wk*.csv")))
    mf = sorted(glob.glob(str(SNAP / f"dk_main_{season}_wk*.csv")))
    if not lf:
        return pd.DataFrame()
    L = pd.concat(pd.read_csv(f) for f in lf)
    M = pd.concat(pd.read_csv(f) for f in mf)
    sp = M[(M.market == "spreads") & (M.is_home == 1)][["game_id", "captured_at_utc", "point"]]
    tot = M[(M.market == "totals") & (M.team == "Over")][["game_id", "captured_at_utc", "point"]]
    main = sp.rename(columns={"point": "main_spread"}).merge(
        tot.rename(columns={"point": "total"}), on=["game_id", "captured_at_utc"], how="left")
    h = L[L.is_home == 1][["game_id", "captured_at_utc", "label", "week", "commence_time",
                           "home_team", "away_team", "rung", "price"]]
    a = L[L.is_home == 0][["game_id", "captured_at_utc", "rung", "price"]].assign(rung=lambda x: -x.rung)
    P = h.merge(a, on=["game_id", "captured_at_utc", "rung"], suffixes=("_home", "_away"))
    P = P.merge(main, on=["game_id", "captured_at_utc"], how="left").dropna(subset=["main_spread"])
    ih, ia = implied(P.price_home), implied(P.price_away)
    P["p_dk_home"] = ih / (ih + ia)
    return P


def projections(season: int, P: pd.DataFrame) -> pd.Series:
    rows = [pd.read_csv(f) for f in glob.glob(str(TARGETS / f"targets_{season}_wk*.csv"))]
    if not rows:
        return pd.Series(np.nan, index=P.index)
    t = pd.concat(rows).drop_duplicates("game_id", keep="last").set_index("game_id")
    L = -P.main_spread
    k = P.game_id.map(t.k)
    return L + k * (P.game_id.map(t.ratings_margin) - L) + P.game_id.map(t.b_qb) * P.game_id.map(t.qb_delta)


def edges(season: int = config.CURRENT_SEASON) -> pd.DataFrame:
    P = ladders(season)
    if P.empty:
        return P
    ours = mrun.dist_params(mrun.load_params())
    P["proj"] = projections(season, P)
    P["p_shape_home"] = np.nan
    P["p_full_home"] = np.nan
    for (gid, ts), idx in P.groupby(["game_id", "captured_at_utc"]).indices.items():
        r = P.iloc[idx]
        absl, tot = [abs(r.main_spread.iloc[0])], [r.total.iloc[0] if pd.notna(r.total.iloc[0]) else 50.0]
        rung = r.rung.to_numpy()
        pm = dist.pmf([-r.main_spread.iloc[0]], absl, tot, ours)
        P.iloc[idx, P.columns.get_loc("p_shape_home")] = dist.cover(np.repeat(pm, len(r), 0), rung, "home")[0]
        if pd.notna(r.proj.iloc[0]):
            pf = dist.pmf([r.proj.iloc[0]], absl, tot, ours)
            P.iloc[idx, P.columns.get_loc("p_full_home")] = dist.cover(np.repeat(pf, len(r), 0), rung, "home")[0]
    # long format: one row per side (team perspective)
    home = pd.DataFrame({"side": "home", "team": P.home_team, "rung": P.rung, "price": P.price_home,
                         "p_dk": P.p_dk_home, "p_shape": P.p_shape_home, "p_full": P.p_full_home})
    away = pd.DataFrame({"side": "away", "team": P.away_team, "rung": -P.rung, "price": P.price_away,
                         "p_dk": 1 - P.p_dk_home, "p_shape": 1 - P.p_shape_home,
                         "p_full": 1 - P.p_full_home})
    keep = ["game_id", "captured_at_utc", "label", "week", "commence_time", "home_team",
            "away_team", "main_spread", "total", "proj"]
    out = pd.concat([pd.concat([P[keep], home], axis=1), pd.concat([P[keep], away], axis=1)],
                    ignore_index=True)
    out["shape_edge_pp"] = 100 * (out.p_shape - out.p_dk)
    out["full_edge_pp"] = 100 * (out.p_full - out.p_dk)
    pay = payout(out.price)
    out["ev_shape"] = out.p_shape * pay - (1 - out.p_shape)
    out["ev_full"] = out.p_full * pay - (1 - out.p_full)
    out["kind"] = np.where(out.rung > 0, "getting", "laying")
    return out


BET_CUTOFF_HOUR = 18


def bet_snapshot(e: pd.DataFrame) -> pd.DataFrame:
    """Rows of each game's bet-time ladder snapshot (Tue 'bet' before 18:00 ET, else first on/after Tue)."""
    if e.empty:
        return e
    ts = pd.to_datetime(e.captured_at_utc, utc=True)
    kick = pd.to_datetime(e.commence_time, utc=True).dt.tz_convert("America/New_York")
    tue0 = (kick.dt.normalize() - pd.to_timedelta((kick.dt.weekday - 1) % 7, unit="D")).dt.tz_convert("UTC")
    pre = ts < pd.to_datetime(e.commence_time, utc=True)
    on_tue = pre & (e.label == "bet") & (ts >= tue0) & (ts < tue0 + pd.Timedelta(hours=BET_CUTOFF_HOUR))
    late = pre & (ts >= tue0)
    pick = ts[on_tue].groupby(e.game_id[on_tue]).min()
    pick = pick.combine_first(ts[late].groupby(e.game_id[late]).min())
    return e[ts == e.game_id.map(pick)]


def update_paper_log(e: pd.DataFrame, season: int) -> tuple[int, str]:
    """Append the bet-time rows of weeks not yet in the log (see module docstring)."""
    path = LINES / f"paper_rungs_{season}.csv"
    if path.exists():
        e = e[~e.week.isin(pd.read_csv(path, usecols=["week"]).week.unique())]
    e = bet_snapshot(e)
    q = e[e.price.between(PRICE_LO, PRICE_HI)
          & ((e.shape_edge_pp >= EDGE_PP) | (e.full_edge_pp >= EDGE_PP))]
    key = ["captured_at_utc", "game_id", "side", "rung"]
    if path.exists():
        old = pd.read_csv(path)[key]
        q = q.merge(old.assign(_seen=1), on=key, how="left")
        q = q[q._seen.isna()].drop(columns="_seen")
    cols = ["captured_at_utc", "label", "game_id", "week", "commence_time", "home_team", "away_team",
            "side", "team", "kind", "rung", "price", "main_spread", "proj", "p_shape", "p_full",
            "p_dk", "shape_edge_pp", "full_edge_pp", "ev_shape", "ev_full"]
    q[cols].to_csv(path, mode="a", header=not path.exists(), index=False)
    return len(q), str(path)


def grade(season: int) -> pd.DataFrame:
    path = LINES / f"paper_rungs_{season}.csv"
    if not path.exists():
        return pd.DataFrame()
    p = pd.read_csv(path)
    g = pd.read_parquet(config.CLEAN / "games.parquet")[["game_id", "margin_home", "completed"]]
    p = p.merge(g, on="game_id", how="left")
    tm = np.where(p.side == "home", p.margin_home, -p.margin_home)
    p["result"] = np.where(p.margin_home.notna() & (p.completed == True),  # noqa: E712
                           (tm + p.rung > 0).astype(float), np.nan)
    p["units"] = np.where(p.result == 1, payout(p.price), np.where(p.result == 0, -1.0, np.nan))
    p.drop(columns=["completed"]).to_csv(LINES / f"paper_rungs_graded_{season}.csv", index=False)
    return p


def bar_sample(p: pd.DataFrame) -> pd.DataFrame:
    """Pre-registered unit: per game and side, the bet-time ladder (first 'bet' snapshot, else
    the game's first ladder), getting-points rungs that qualified on SHAPE edge, the one with the
    largest shape edge. First BAR['min_games'] games by kickoff WITH A GRADED UNIT (as registered:
    an ungraded game, e.g. postponed, is skipped, not held in the sample)."""
    x = p[(p.kind == "getting") & (p.shape_edge_pp >= EDGE_PP)].copy()
    if x.empty:
        return x
    x["is_bet"] = (x.label == "bet").astype(int)
    first_bet = x[x.is_bet == 1].groupby("game_id").captured_at_utc.min()
    first_any = x.groupby("game_id").captured_at_utc.min()
    snap = first_bet.reindex(first_any.index).fillna(first_any)
    x = x[x.captured_at_utc == x.game_id.map(snap)]
    x = x.sort_values("shape_edge_pp", ascending=False).drop_duplicates(["game_id", "side"])
    graded = x[x.result.notna()] if "result" in x else x
    order = graded.groupby("game_id").commence_time.first().sort_values().index[:BAR["min_games"]]
    return x[x.game_id.isin(order)]


VERDICT_HEAD = "## Ladder-shape bar: verdict"


def record_verdict(season: int, doc: Path) -> str | None:
    """Tim, 2026-10-25: when the registered sample reaches BAR['min_games'] graded games, evaluate the
    bar EXACTLY as registered (lift >= +3.0 pp and the 95% game-clustered bootstrap CI, 2,000 draws,
    excluding 0) and write the verdict to FORWARD_TEST.md ONCE. Never re-evaluated, extended or
    re-defined; any further shape study is a new, separately declared test."""
    if not doc.exists():
        return None
    text = doc.read_text(encoding="utf-8")
    if VERDICT_HEAD in text:
        return None
    s_ = bar_sample(grade(season))
    lift = clustered_lift(s_) if len(s_) else None
    if not lift or lift["games"] < BAR["min_games"]:
        return None
    ok = lift["lift_pp"] >= BAR["lift_pp"] and (lift["ci95_lo"] > 0 or lift["ci95_hi"] < 0)
    verdict = "PASSED" if ok else "FAILED"
    first, last = s_.commence_time.min(), s_.commence_time.max()
    from datetime import datetime, timezone
    block = (f"{VERDICT_HEAD} (recorded {datetime.now(timezone.utc):%Y-%m-%d}, evaluated once, as registered)\n\n"
             f"**{verdict}.** Sample: the first {lift['games']} games by kickoff with a graded unit "
             f"({lift['rungs']} rungs; kickoffs {first[:10]} to {last[:10]}). Hit rate {lift['hit_%']:.1f}% vs "
             f"mean DK no-vig {lift['dk_novig_%']:.1f}%: **lift {lift['lift_pp']:+.1f} pp** (bar: >= +3.0), "
             f"95% game-clustered bootstrap CI {lift['ci95_lo']:+.1f} to {lift['ci95_hi']:+.1f} "
             f"(bar: excludes 0). Informational: break-even at posted prices {lift['breakeven_at_price_%']:.1f}%, "
             f"realized {lift['realized_units_per_rung']:+.3f} units/rung (CI {lift['units_ci95_lo']:+.3f} to "
             f"{lift['units_ci95_hi']:+.3f}).\n\nThis bar is closed: not extended, re-run or re-defined. Any further "
             f"shape study is declared below as a new, separate test before its data is graded.\n\n")
    anchor = "## Floor-card bar"
    text = text.replace(anchor, block + anchor, 1) if anchor in text else text + "\n" + block
    doc.write_text(text, encoding="utf-8")
    return verdict


def clustered_lift(x: pd.DataFrame, n_boot=2000, seed=0):
    d = x.dropna(subset=["result"])
    if d.empty:
        return None
    games = d.game_id.unique()
    idx = d.groupby("game_id").indices
    rng = np.random.default_rng(seed)
    b, u = [], []
    res, pdk, units = d.result.to_numpy(), d.p_dk.to_numpy(), d.units.to_numpy()
    for _ in range(n_boot):
        pick = rng.choice(games, len(games))
        ix = np.concatenate([idx[g] for g in pick])
        b.append(res[ix].mean() - pdk[ix].mean())
        u.append(units[ix].mean())
    # EV at the POSTED price (DK's ~7% ladder hold included), per 1 unit staked
    be = 1 / (1 + payout(d.price))               # break-even probability at the posted price
    return {"games": len(games), "rungs": len(d), "hit_%": 100 * d.result.mean(),
            "dk_novig_%": 100 * d.p_dk.mean(), "breakeven_at_price_%": 100 * be.mean(),
            "lift_pp": 100 * (d.result.mean() - d.p_dk.mean()),
            "ci95_lo": 100 * np.percentile(b, 2.5), "ci95_hi": 100 * np.percentile(b, 97.5),
            "pred_ev_shape_per_unit": float(d.ev_shape.mean()),
            "realized_units_per_rung": float(units.mean()),
            "units_ci95_lo": float(np.percentile(u, 2.5)), "units_ci95_hi": float(np.percentile(u, 97.5))}


def main(season: int = config.CURRENT_SEASON) -> int:
    e = edges(season)
    if e.empty:
        write_block("SHAPE", "_No ladders yet._")
        return 0
    n, path = update_paper_log(e, season)
    p = grade(season)
    s = bar_sample(p)
    graded = s.dropna(subset=["result"]) if len(s) else s
    lift = clustered_lift(s) if len(s) else None
    status = ("IN PROGRESS: %d/%d graded games; $0" % (graded.game_id.nunique() if len(graded) else 0,
                                                        BAR["min_games"]))
    if lift and lift["games"] >= BAR["min_games"]:
        ok = lift["lift_pp"] >= BAR["lift_pp"] and lift["ci95_lo"] > 0
        status = ("PASSED" if ok else "FAILED") + f" at {lift['games']} games"
    summ = (e.assign(abs_shape=e.shape_edge_pp)
              .groupby(["kind", pd.cut(e.price, [-100000, -500, -150, 100000])], observed=True)
              .agg(rungs=("shape_edge_pp", "size"), mean_shape_pp=("shape_edge_pp", "mean"),
                   share_shape_ge3=("shape_edge_pp", lambda v: 100 * (v >= EDGE_PP).mean()),
                   mean_full_pp=("full_edge_pp", "mean"),
                   mean_ev_shape=("ev_shape", "mean"),
                   share_ev_shape_pos=("ev_shape", lambda v: 100 * (v > 0).mean()))
            ).reset_index().rename(columns={"price": "price band"})
    pl = pd.read_csv(LINES / f"paper_rungs_{season}.csv")
    T = [f"_Generated by `python -m engine.cfb.lines.ladder_edge`. {n} new paper rows this run -> "
         f"`{path.split('edge-index')[-1].lstrip(chr(92)).lstrip('/')}`._\n",
         f"**Shape-edge bar status: {status}** (pre-registered in docs/cfb/FORWARD_TEST.md)\n",
         "\n**All captured rungs: mean edges by kind and price band (pp)**\n", md(summ, "{:.2f}"),
         f"\n**Paper log so far:** {len(pl)} rows, {pl.game_id.nunique()} games; getting-points rows "
         f"{(pl.kind == 'getting').sum()}, of which shape-qualified {((pl.kind == 'getting') & (pl.shape_edge_pp >= EDGE_PP)).sum()}, "
         f"full-qualified {((pl.kind == 'getting') & (pl.full_edge_pp >= EDGE_PP)).sum()}. Not a result "
         f"until the bar's sample is graded.\n"]
    gq = pl[(pl.kind == "getting") & (pl.shape_edge_pp >= EDGE_PP)]
    T.append(f"Shape-qualified getting rows: mean shape edge {gq.shape_edge_pp.mean():+.2f} pp vs DK no-vig; "
             f"mean EV at the posted price {gq.ev_shape.mean():+.3f} units; "
             f"{(gq.ev_shape > 0).mean() * 100:.0f}% of them are +EV after DK's hold.\n"
             if len(gq) else "")
    if lift:
        T += ["\n**Bar sample (graded so far): no-vig lift and EV at the posted price**\n",
              md(pd.DataFrame([lift]), "{:.3f}")]
    write_block("SHAPE", "\n".join(T))
    print("\n".join(T))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
