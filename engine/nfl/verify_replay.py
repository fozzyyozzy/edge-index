"""NFL floor verification (docs/nfl/PREREG_NFL.md): the registered 2025 analysis, and the 2026 forward check.

    python -m engine.nfl.verify_replay registered     # ONCE: Q1-Q4 on 2025 (marker: data/nfl/verify/analysis_run.json)
    python -m engine.nfl.verify_replay forward        # 2026 weeks 3-6 from the pipeline's own pregame ladders and cards

Q3 replays the LIVE scripts (automation/pipeline floors.py -> grade_legs.py -> build_card_json.py) for every 2025 week and
slate in a scratch automation root (EDGE_ROOT), with every nflverse weekly-stats load patched to return only weeks
BEFORE the replayed week (walk-forward), twice: WITH injury reconstruction (availability.build as live) and WITHOUT
(empty availability snapshot).
"""
from __future__ import annotations
import contextlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "nfl" / "verify"
REPLAY = OUT / "replay"
CACHE = OUT / "raw" / "nflverse"
os.environ["EDGE_ROOT"] = str(REPLAY / "with_injuries")          # before the pipeline imports read it
sys.path.insert(0, str(ROOT / "automation" / "pipeline"))
import common                                                     # noqa: E402
import floors                                                     # noqa: E402
import grade_legs                                                 # noqa: E402
import build_card_json                                            # noqa: E402
import availability                                               # noqa: E402

SEASON = 2025
ALT = {"player_receptions_alternate": "receptions", "player_reception_yds_alternate": "rec_yds"}
MAIN = {"player_receptions": "receptions", "player_reception_yds": "rec_yds"}
STAT = {"receptions": "receptions", "rec_yds": "receiving_yards"}
BAND, SLOPE_SET = (0.60, 0.95), (0.50, 0.97)
W = [0.1, 0.2, 0.4, 0.6]
SEED, BOOT = 20261021, 10_000
SLATES = ["tnf", "sun", "mnf"]

# ---------- data access: cached, and walk-forward for the replayed scripts ----------
_orig_read = common.read_csv_source
_mem = {}


def cached_read(source, **fmt):
    key = (source, tuple(sorted(fmt.items())))
    if key not in _mem:
        CACHE.mkdir(parents=True, exist_ok=True)
        f = CACHE / (source.replace(" ", "_") + "_" + "_".join(f"{k}{v}" for k, v in sorted(fmt.items())) + ".pkl")
        if f.exists():
            _mem[key] = pd.read_pickle(f)
        else:
            _mem[key] = _orig_read(source, **fmt)
            _mem[key].to_pickle(f)
    return _mem[key].copy()


common.read_csv_source = cached_read
availability.read_csv_source = cached_read
_orig_fetch = common.fetch_season
NOW = {"season": None, "week": None}


def wf_fetch_season(yr):
    """the live fetch_season, cut to weeks strictly before the replayed week (walk-forward)"""
    w = _orig_fetch(yr)
    s, wk = NOW["season"], NOW["week"]
    if s is None:
        return w
    if yr > s:
        return w.iloc[0:0]
    if yr == s:
        w = w[w.week < wk]
        assert w.week.max() < wk if len(w) else True
    return w


for _m in (common, floors, grade_legs, availability):
    _m.fetch_season = wf_fetch_season
_orig_build = availability.build


def empty_availability(season, week, stats=None):
    return dict(season=season, week=week, fetched_at=None, sources={"replay": "WITHOUT: no injury information"},
                team_games={}, qb_change={}, players={})


def implied(o):
    o = np.asarray(o, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(o < 0, -o / (-o + 100), 100 / (o + 100))


def dec(o):
    o = np.asarray(o, float)
    return np.where(o < 0, 1 + 100 / -o, 1 + o / 100)


# ---------- outcomes ----------
def outcomes(season: int):
    """weekly stat rows (REG + POST) and who played, for settling legs"""
    w = cached_read("nflverse weekly player stats", season=season)
    w = w[w.player_display_name.notna()].copy()
    w["key"] = w.player_display_name.map(common.norm_name)
    try:
        s = cached_read("nflverse snap counts", season=season)
        s = s[s.offense_snaps.fillna(0) > 0]
        played = set(zip(s.player.map(common.norm_name), s.team, s.week))
    except Exception:
        played = set()
    played |= set(zip(w.key, w.team, w.week))
    known = set(w.key) | {k for k, _, _ in played}
    return w, played, known


def settle(rows: pd.DataFrame, w, played, known, season) -> pd.DataFrame:
    """adds value, result in {WIN, LOSS, VOID, UNGRADEABLE}. rows: player, market, rung, week, teams (tuple)"""
    idx = {(k, wk): r for k, wk, r in zip(w.key, w.week, w.to_dict("records"))}
    vals, res = [], []
    for p, m, t, wk, teams in zip(rows.player, rows.market, rows.rung, rows.week, rows.teams):
        k = common.norm_name(p)
        r = idx.get((k, wk))
        if r is not None and r["team"] in teams:
            v = float(r[STAT.get(m, common.COL.get(m))] or 0)
        elif any((k, tm, wk) in played for tm in teams):
            v = 0.0
        else:
            vals.append(np.nan); res.append("VOID" if k in known else "UNGRADEABLE"); continue
        vals.append(v); res.append("WIN" if v >= t else "LOSS")
    return rows.assign(value=vals, result=res)


def boot_ci(ret: pd.Series, games: pd.Series) -> tuple[float, float]:
    """game-clustered percentile bootstrap of mean return"""
    df = pd.DataFrame({"r": ret.to_numpy(float), "g": games.to_numpy()})
    by = df.groupby("g").r.agg(["sum", "size"])
    s, n = by["sum"].to_numpy(), by["size"].to_numpy()
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(by), size=(BOOT, len(by)))
    means = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def roi_summary(d: pd.DataFrame, price_col="price") -> dict:
    d = d[d.result.isin(["WIN", "LOSS"])]
    if d.empty:
        return {"n": 0}
    ret = np.where(d.result == "WIN", dec(d[price_col]) - 1, -1.0)
    lo, hi = boot_ci(pd.Series(ret), d.game_id)
    return {"n": int(len(d)), "games": int(d.game_id.nunique()), "hit": round(float((d.result == "WIN").mean()) * 100, 2),
            "avg_implied": round(float(implied(d[price_col]).mean()) * 100, 2), "roi_pct": round(float(ret.mean()) * 100, 2),
            "ci95_pct": [round(lo * 100, 2), round(hi * 100, 2)]}


def verdict(ci) -> str:
    return "CONFIRMED" if ci[0] > 0 else "REFUTED" if ci[1] < 0 else "INCONCLUSIVE"


# ---------- price tables ----------
def price_tables(props: pd.DataFrame):
    """alt Over rungs with p_hold / p_anchor (NBA §6.2/§9.1 definitions) and the two-way mains"""
    props = props.copy()
    props["stat"] = props.market.map({**ALT, **MAIN})
    main = props[props.market.isin(MAIN)].pivot_table(index=["game_id", "player", "stat", "point"], columns="side",
                                                       values="price", aggfunc="first").reset_index()
    main = main.dropna(subset=["Over", "Under"])
    main["io"], main["iu"] = implied(main.Over), implied(main.Under)
    main["hold"] = main.io + main.iu - 1
    main = main[(main.hold > -0.01) & (main.hold < 0.25)]
    main["q"] = main.io / (main.io + main.iu)
    main = main.sort_values("hold").drop_duplicates(["game_id", "player", "stat"])
    alt = props[props.market.isin(ALT) & (props.side == "Over")].copy()
    alt["rung"] = alt.point + 0.5
    alt["ia"] = implied(alt.price)
    alt = alt.merge(main[["game_id", "player", "stat", "point", "hold", "q"]].rename(columns={"point": "main_point"}),
                    on=["game_id", "player", "stat"], how="left")
    gm = main.groupby(["game_id", "stat"]).hold.median().rename("hold_gm")
    gg = main.groupby("game_id").hold.median().rename("hold_g")
    alt = alt.join(gm, on=["game_id", "stat"]).join(gg, on="game_id")
    h = alt.hold.fillna(alt.hold_gm).fillna(alt.hold_g)
    alt["hold_src"] = np.where(alt.hold.notna(), "two-way", np.where(alt.hold_gm.notna(), "market median", "game median"))
    alt["p_hold"] = alt.ia / (1 + h)
    anc = alt[alt.main_point.notna() & np.isclose(alt.point, alt.main_point)]
    r = anc.assign(r=anc.ia / anc.q)[["game_id", "player", "stat", "r"]]
    r = r[(r.r > 0.5) & (r.r < 2.0)].drop_duplicates(["game_id", "player", "stat"])
    alt = alt.merge(r, on=["game_id", "player", "stat"], how="left")
    alt = alt.join(r.groupby(["game_id", "stat"]).r.median().rename("r_gm"), on=["game_id", "stat"])
    alt = alt.join(r.groupby("stat").r.median().rename("r_season"), on="stat")
    rr = alt.r.fillna(alt.r_gm).fillna(alt.r_season)
    alt["anchor_src"] = np.where(alt.r.notna(), "anchored", np.where(alt.r_gm.notna(), "game median", "season median"))
    alt["p_anchor"] = np.minimum(alt.ia / rr, 0.999)
    alt["teams"] = list(zip(alt.home_team, alt.away_team))
    return alt, main


# ---------- live-format inputs for the replay ----------
def write_inputs(props_wk: pd.DataFrame, season: int, week: int):
    P = common.P
    game = props_wk.away_team + " @ " + props_wk.home_team
    alt = props_wk[props_wk.market.isin(ALT) & (props_wk.side == "Over")]
    lad = pd.DataFrame({"Player": alt.player, "Market": alt.market.map(ALT), "Rung": alt.point + 0.5,
                        "Odds": alt.price.astype(int), "Game": game[alt.index], "Commence": alt.kickoff,
                        "PulledAt": alt.snapshot}).drop_duplicates(["Player", "Market", "Rung"])
    lad.to_csv(P("lines", f"ladders_{season}_w{week}.csv"), index=False)
    mn = props_wk[props_wk.market.isin(MAIN)]
    tw = mn.pivot_table(index=["player", "market", "point", "away_team", "home_team", "kickoff", "snapshot"],
                        columns="side", values="price", aggfunc="first").reset_index()
    tw = pd.DataFrame({"Player": tw.player, "Market": tw.market.map(MAIN), "Line": tw.point, "Over": tw.get("Over"),
                       "Under": tw.get("Under"), "Game": tw.away_team + " @ " + tw.home_team, "Commence": tw.kickoff,
                       "PulledAt": tw.snapshot})
    tw.to_csv(P("lines", f"twoway_{season}_w{week}.csv"), index=False)
    lad2 = lad.copy()                                                   # fetch_lines.py's main-line rule
    lad2["dist"] = (lad2.Odds.abs() - 110).abs() + (lad2.Odds > 0) * 5
    dk = lad2.sort_values("dist").groupby(["Player", "Market"], as_index=False).first()[["Player", "Market", "Rung", "Odds"]]
    dk = dk.rename(columns={"Rung": "Line"})
    for s in ["all"] + SLATES:
        dk.to_csv(P("lines", f"dk_{season}_w{week}_{s}.csv"), index=False)
    snap = pd.to_datetime(props_wk.snapshot, utc=True).max().isoformat(timespec="minutes")
    for s in SLATES + [None]:
        open(P("lines", f"pulled_{season}_w{week}" + (f"_{s}" if s else "") + ".txt"), "w").write(snap)


def run_script(mod, argv, log):
    old = sys.argv
    sys.argv = [mod.__file__] + argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            mod.main()
    finally:
        sys.argv = old
        log.write(f"$ {mod.__name__} {' '.join(argv)}\n{buf.getvalue()}\n")


def replay(props: pd.DataFrame, season: int, weeks, variant: str, log) -> list[dict]:
    """live cards for every week/slate; returns [{week, slate, card}]"""
    common.ROOT = str(REPLAY / variant)
    availability.build = _orig_build if variant == "with_injuries" else empty_availability
    sch = floors.schedule_all(season)
    cards = []
    for wk in weeks:
        NOW.update(season=season, week=wk)
        pw = props[props.week == wk]
        if pw.empty:
            continue
        write_inputs(pw, season, wk)
        days = set(sch[sch.week == wk].weekday)
        for slate in SLATES:
            if not days & floors.SLATE_DAYS[slate]:
                continue
            lines = common.P("lines", f"dk_{season}_w{wk}_{slate}.csv")
            lad = common.P("lines", f"ladders_{season}_w{wk}.csv")
            args = ["--season", str(season), "--week", str(wk), "--slate", slate]
            run_script(floors, args + ["--lines", lines, "--ladders", lad], log)
            run_script(grade_legs, args + ["--lines", lines, "--ladders", lad], log)
            run_script(build_card_json, args, log)
            card = json.load(open(common.P("cards", f"card_{season}_w{wk}_{slate}.json")))
            cards.append(dict(week=wk, slate=slate, card=card))
    NOW.update(season=None, week=None)
    return cards


# ---------- model probabilities for every priced rung (Q2 / calibration) ----------
def model_rows(alt: pd.DataFrame, season: int, weeks) -> pd.DataFrame:
    out = []
    for wk in weeks:
        NOW.update(season=season, week=wk)
        a = alt[alt.week == wk]
        if a.empty:
            continue
        w = pd.concat([wf_fetch_season(y) for y in (season - 2, season - 1, season)])
        cur, prev = w[w.season == season], w[w.season == season - 1]
        team_now = cur.groupby("key")["team"].last() if len(cur) else prev.groupby("key")["team"].last()
        team_prev = prev.groupby("key")["team"].last()
        holds = common.load_holds(season, wk) if os.path.exists(common.P("lines", f"twoway_{season}_w{wk}.csv")) else {}
        for (player, stat), g0 in a.groupby(["player", "stat"]):
            key = common.norm_name(player)
            g = w[(w.key == key) & (w.targets.fillna(0) > 0)].sort_values(["season", "week"])
            tm = team_now.get(key)
            teams = g0.teams.iloc[0]
            if tm not in teams:
                continue
            g, _, min_games = common.grading_history(g, season, tm, team_prev.get(key), w[w.key == key])
            v = g[common.COL[stat]].fillna(0).to_numpy()
            if len(v) < min_games:
                continue
            for r in g0.itertuples():
                mo = common.leg_prob(v, r.rung, None)
                lb = common.leg_prob(v, r.rung, common.novig(int(r.price), player, stat, holds)[0])
                out.append({"idx": r.Index, "MO": mo, "LB": lb})
    NOW.update(season=None, week=None)
    m = pd.DataFrame(out).set_index("idx")
    return alt.join(m, how="inner")


def brier(p, y):
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def logistic_slope(p, y):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    y = np.asarray(y, float)
    X = np.column_stack([np.ones_like(p), np.log(p / (1 - p))])
    b = np.array([0.0, 1.0])
    for _ in range(50):
        mu = 1 / (1 + np.exp(-(X @ b)))
        wt = mu * (1 - mu)
        nb = np.linalg.solve(X.T @ (wt[:, None] * X), X.T @ (wt * (X @ b) + (y - mu)))
        if np.max(np.abs(nb - b)) < 1e-9:
            b = nb
            break
        b = nb
    return float(b[1])


def rel_table(p, y, lo=0.05, hi=1.0001, step=0.05):
    out = []
    p, y = np.asarray(p, float), np.asarray(y, float)
    for a in np.arange(lo, hi - 1e-9, step):
        m = (p >= a) & (p < a + step)
        if m.sum():
            out.append({"bin": f"{a * 100:.0f}-{(a + step) * 100:.0f}", "n": int(m.sum()),
                        "mean_p": round(float(p[m].mean()) * 100, 2), "hit": round(float(y[m].mean()) * 100, 2)})
    return out


def q2(rows: pd.DataFrame) -> dict:
    d = rows[rows.result.isin(["WIN", "LOSS"]) & rows.p_hold.between(*SLOPE_SET) & rows.p_anchor.notna()].copy()
    d["y"] = (d.result == "WIN").astype(float)
    out = {"rows": int(len(d)), "by_market": d.stat.value_counts().to_dict(),
           "hold_src": d.hold_src.value_counts().to_dict(), "anchor_src": d.anchor_src.value_counts().to_dict()}
    def table(x):
        t = {}
        for m in ("hold", "anchor"):
            pm = x[f"p_{m}"]
            t[m] = {"market_only": brier(pm, x.y), "MO": brier(x.MO, x.y), "LB": brier(x.LB, x.y),
                    **{f"w{w}": brier(w * x.MO + (1 - w) * pm, x.y) for w in W}}
        return t
    pooled = table(d)
    out["pooled"] = pooled
    qual = [w for w in W if all(pooled[m][f"w{w}"] < pooled[m]["market_only"] for m in ("hold", "anchor"))]
    chosen = min(qual, key=lambda w: (pooled["hold"][f"w{w}"], w)) if qual else 0.1
    out["qualifying_w"], out["pooled_w"] = qual, chosen
    out["LB_beats_market_both"] = all(pooled[m]["LB"] < pooled[m]["market_only"] for m in ("hold", "anchor"))
    per = {}
    for s, x in d.groupby("stat"):
        t = table(x)
        worse = any(t[m][f"w{chosen}"] > t[m]["market_only"] for m in ("hold", "anchor"))
        per[s] = {"n": int(len(x)), **t, "card_w": 0.1 if worse else chosen,
                  "LB_beats_market_both": all(t[m]["LB"] < t[m]["market_only"] for m in ("hold", "anchor"))}
    out["per_market"] = per
    cal = {}
    for s, x in d.groupby("stat"):
        cal[s] = {mdl: {"slope": logistic_slope(x[mdl], x.y), "reliability": rel_table(x[mdl], x.y, 0.5)}
                  for mdl in ("MO", "LB")}
        cal[s]["market_hold"] = {"reliability_floor_band": rel_table(x.p_hold, x.y, 0.60, 0.9501)}
    out["calibration_not_gating"] = cal
    return out


def q1(rows: pd.DataFrame) -> dict:
    d = rows[pd.Series(implied(rows.price), index=rows.index).between(BAND[0], BAND[1], inclusive="left")].copy()
    d["imp"] = implied(d.price)
    res = {"all": roi_summary(d)}
    for s, x in d.groupby("stat"):
        res[s] = roi_summary(x)
        res[s]["by_bin"] = []
        for a in np.arange(0.60, 0.95 - 1e-9, 0.05):
            b = x[(x.imp >= a) & (x.imp < a + 0.05)]
            r = roi_summary(b)
            g = b[b.result.isin(["WIN", "LOSS"])]
            r.update(bin=f"{a * 100:.0f}-{a * 100 + 5:.0f}", devig_mean=round(float(g.p_hold.mean()) * 100, 2) if len(g) else None)
            res[s]["by_bin"].append(r)
    res["result_counts"] = d.result.value_counts().to_dict()
    return res


def fs_mu(season: int):
    """engine/nfl/floor_study.py's expectation: DECAY 0.85 over <= 16 prior games (>= 7), all game rows incl. playoffs"""
    rows = []
    for y in (season - 2, season - 1, season):
        w = cached_read("nflverse weekly player stats", season=y)
        rows.append(w[w.player_display_name.notna()])
    w = pd.concat(rows)
    w["key"] = w.player_display_name.map(common.norm_name)
    w = w.sort_values(["season", "week"])
    mu = {}
    for key, g in w.groupby("key"):
        for stat, col in STAT.items():
            v = g[col].fillna(0).to_numpy()
            for i, (s, wk) in enumerate(zip(g.season, g.week)):
                if s != season:
                    continue
                hist = v[max(0, i - 16):i]
                if len(hist) < 7 or hist.mean() <= 0:
                    continue
                wt = 0.85 ** np.arange(len(hist) - 1, -1, -1)
                mu[(key, int(wk), stat)] = float(wt @ hist / wt.sum())
    return mu


def q4(rows: pd.DataFrame, mu: dict) -> dict:
    out = {}
    for stat, floor_min in (("receptions", 3.0), ("rec_yds", 25.0)):
        x = rows[rows.stat == stat].copy()
        x["mu"] = [mu.get((common.norm_name(p), int(wk), stat)) for p, wk in zip(x.player, x.week)]
        x = x[x.mu.notna() & (x.mu >= floor_min)]
        line = np.maximum(np.floor(0.6 * x.mu) - 0.5, 0.5) if stat == "receptions" else np.floor(0.6 * x.mu * 2) / 2 + 0.5
        x["target"] = line
        x["dist"] = (x.point - x.target).abs()
        pick = x.sort_values(["dist", "point"]).drop_duplicates(["game_id", "player"])
        r = roi_summary(pick)
        g = pick[pick.result.isin(["WIN", "LOSS"])]
        r.update(median_price=float(g.price.median()) if len(g) else None,
                 price_iqr=[float(g.price.quantile(0.25)), float(g.price.quantile(0.75))] if len(g) else None,
                 exact_rung_share=round(float((pick.dist < 1e-9).mean()), 3))
        if stat == "receptions" and len(g):
            r["claim_supported"] = bool(r["median_price"] > -400 and r["ci95_pct"][0] > 0)
        out[stat] = r
    return out


def q3(cards: list, w, played, known, mo_lookup) -> dict:
    cand, tickets = [], []
    gid = {}
    for c in cards:
        wk, card = c["week"], c["card"]
        for x in card["candidates"]:
            cand.append(dict(week=wk, slate=c["slate"], player=x["player"], market=x["market"], rung=x["rung"],
                             price=x["odds_real"] if x["odds_real"] is not None else x["odds_est"], team=x["team"],
                             opp=x["opp"], teams=(x["team"], x["opp"]), LB=x["prob"], novig=(x.get("novig_pct") or 0) / 100,
                             grade=x["grade"], injury_watch=bool(x.get("injury_watch"))))
        for t in card["tickets"]:
            tickets.append(dict(week=wk, slate=c["slate"], name=t["name"],
                                legs=[(l["player"], l["market"], l["rung"]) for l in t["legs"]]))
    cd = pd.DataFrame(cand)
    if cd.empty:
        return {"legs": {"n": 0}}
    cd = settle(cd, w, played, known, None)
    cd["game_id"] = [f"{wk}:{'-'.join(sorted(tt))}" for wk, tt in zip(cd.week, cd.teams)]
    cd["MO"] = [mo_lookup.get((common.norm_name(p), m, float(r), int(wk))) for p, m, r, wk in
                zip(cd.player, cd.market, cd.rung, cd.week)]
    legs = roi_summary(cd)
    legs["verdict"] = verdict(legs["ci95_pct"]) if legs.get("n") else None
    legs["by_market"] = {m: roi_summary(x) for m, x in cd.groupby("market")}
    legs["by_grade"] = {g: roi_summary(x) for g, x in cd.groupby("grade")}
    legs["mean_LB"] = round(float(cd[cd.result.isin(['WIN', 'LOSS'])].LB.mean()) * 100, 2)
    legs["result_counts"] = cd.result.value_counts().to_dict()
    # tickets: settled from the legs; a VOID leg drops out (DK parlay rule), UNGRADEABLE makes the ticket ungradeable
    key = {(r.week, r.player, r.market, r.rung): r for r in cd.itertuples()}
    trows = []
    for t in tickets:
        ls = [key.get((t["week"], p, m, r)) for p, m, r in t["legs"]]
        if any(l is None or l.result == "UNGRADEABLE" for l in ls):
            trows.append(dict(result="UNGRADEABLE")); continue
        live = [l for l in ls if l.result != "VOID"]
        pay = float(np.prod([dec(l.price) for l in live])) if live else 1.0
        won = all(l.result == "WIN" for l in live)
        imp = float(np.prod([implied(l.price) for l in live])) if live else 1.0
        fair = float(np.prod([l.novig for l in live])) if live else 1.0
        lb = float(np.prod([l.LB for l in live])) if live else 1.0
        mo = np.prod([l.MO for l in live]) if live and all(l.MO is not None for l in live) else np.nan
        trows.append(dict(result="WIN" if won else "LOSS", legs=len(live), ret=pay - 1 if won else -1.0, payout=pay,
                          implied=imp, fair=fair, LB=lb, MO=mo, game_id=f"{t['week']}:{t['slate']}"))
    td = pd.DataFrame(trows)
    g = td[td.result.isin(["WIN", "LOSS"])]
    tick = {"n": int(len(g)), "ungradeable": int((td.result == "UNGRADEABLE").sum())}
    if len(g):
        lo, hi = boot_ci(g.ret, g.game_id)
        tick.update(hit=round(float((g.result == "WIN").mean()) * 100, 2), roi_pct=round(float(g.ret.mean()) * 100, 2),
                    ci95_pct=[round(lo * 100, 2), round(hi * 100, 2)], avg_payout=round(float(g.payout.mean()), 3),
                    mean_LB_product=round(float(g.LB.mean()) * 100, 2),
                    mean_MO_product=round(float(np.nanmean(g.MO)) * 100, 2),
                    mean_implied_product=round(float(g.implied.mean()) * 100, 2),
                    compounded_vig=round(float((g.implied / g.fair).mean()), 4))
    return {"legs": legs, "tickets": tick, "candidates": cd.drop(columns=["teams"]).to_dict("records")}


# ---------- runs ----------
def registered():
    marker = OUT / "analysis_run.json"
    if marker.exists():
        sys.exit(f"refusing: the registered analysis already ran ({marker})")
    import subprocess
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    marker.write_text(json.dumps({"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "code_commit": commit}, indent=2))
    props = pd.read_parquet(OUT / f"hist_props_{SEASON}.parquet")
    props["kickoff"] = pd.to_datetime(props.kickoff, utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert (pd.to_datetime(props.snapshot, utc=True) < pd.to_datetime(props.kickoff, utc=True)).all()
    alt, _ = price_tables(props)
    w, played, known = outcomes(SEASON)
    alt = settle(alt.rename(columns={"stat": "market_"}).assign(market=lambda d: d.market_), w, played, known, SEASON)
    alt = alt.drop(columns=["market"]).rename(columns={"market_": "stat"})
    reg = alt[alt.game_type == "REG"]
    post = alt[alt.game_type != "REG"]
    log = open(OUT / "replay_log.txt", "w", encoding="utf-8")
    weeks = range(1, 19)
    # Q3 first so the replay roots hold each week's inputs for Q2's live novig holds
    cards = {v: replay(props[props.game_type == "REG"], SEASON, weeks, v, log) for v in ("with_injuries", "without_injuries")}
    common.ROOT = str(REPLAY / "with_injuries")
    mrows = model_rows(reg, SEASON, weeks)
    mo_lookup = {(common.norm_name(p), s, float(r), int(wk)): mo for p, s, r, wk, mo in
                 zip(mrows.player, mrows.stat, mrows.rung, mrows.week, mrows.MO)}
    res = {"code_commit": commit, "prices": {"outcomes": int(len(props)), "games": int(props.game_id.nunique()),
                                            "alt_rungs": int(len(alt))},
           "Q1_regular": q1(reg), "Q1_playoffs": q1(post), "Q2_regular": q2(mrows),
           "Q4_regular": q4(reg, fs_mu(SEASON)),
           "Q3": {v: q3(c, w, played, known, mo_lookup) for v, c in cards.items()}}
    res["Q3_cards_built"] = {v: {"cards": len(c), "tickets": sum(len(x["card"]["tickets"]) for x in c),
                                 "candidates": sum(len(x["card"]["candidates"]) for x in c)} for v, c in cards.items()}
    (OUT / "results_2025.json").write_text(json.dumps(res, indent=1, default=float))
    log.close()
    brief = {k: v for k, v in res.items() if k != "Q3"}
    brief["Q3"] = {v: {"legs": {k: x for k, x in r["legs"].items() if k != "by_grade"}, "tickets": r["tickets"]}
                   for v, r in res["Q3"].items()}
    print(json.dumps(brief, indent=1, default=float)[:20000])


def forward():
    """2026 weeks 3-6: the pipeline's own pregame DK ladders/two-way files and its published cards; no credits"""
    lines = ROOT / "automation" / "lines"
    sch = floors.schedule_all(2026)
    sch = sch[sch.week.between(3, 6)].copy()
    from zoneinfo import ZoneInfo
    sch["kickoff"] = [datetime.fromisoformat(f"{d}T{t}").replace(tzinfo=ZoneInfo("America/New_York"))
                      .astimezone(timezone.utc) for d, t in zip(sch.gameday, sch.gametime)]
    from engine.nfl.verify_pull import TEAMS
    frames = []
    for wk in range(3, 7):
        lad = pd.read_csv(lines / f"ladders_2026_w{wk}.csv")
        tw = pd.read_csv(lines / f"twoway_2026_w{wk}.csv")
        for df, kind in ((lad, "alt"), (tw, "main")):
            df = df[df.Market.isin(["receptions", "rec_yds"])].copy()
            df[["away_n", "home_n"]] = df.Game.str.split(" @ ", expand=True)
            df["away_team"], df["home_team"] = df.away_n.map(TEAMS), df.home_n.map(TEAMS)
            df = df[pd.to_datetime(df.PulledAt, utc=True) < pd.to_datetime(df.Commence, utc=True)]   # pregame only
            frames.append((kind, df))
    rows = []
    for kind, df in frames:
        for r in df.itertuples():
            g = sch[(sch.home_team == r.home_team) & (sch.away_team == r.away_team)]
            if g.empty:
                continue
            g = g.iloc[0]
            base = dict(game_id=g.game_id, week=int(g.week), game_type="REG", kickoff=r.Commence, snapshot=r.PulledAt,
                        player=r.Player, home_team=r.home_team, away_team=r.away_team)
            if kind == "alt":
                rows.append({**base, "market": {v: k for k, v in ALT.items()}[r.Market], "side": "Over",
                             "point": r.Rung - 0.5, "price": r.Odds})
            else:
                m = {v: k for k, v in MAIN.items()}[r.Market]
                rows.append({**base, "market": m, "side": "Over", "point": r.Line, "price": r.Over})
                rows.append({**base, "market": m, "side": "Under", "point": r.Line, "price": r.Under})
    props = pd.DataFrame(rows).drop_duplicates(["game_id", "market", "player", "side", "point"], keep="last")
    alt, _ = price_tables(props)
    w, played, known = outcomes(2026)
    alt = settle(alt.rename(columns={"stat": "market_"}).assign(market=lambda d: d.market_), w, played, known, 2026)
    alt = alt.drop(columns=["market"]).rename(columns={"market_": "stat"})
    common.ROOT = str(REPLAY / "forward_2026")
    for wk in range(3, 7):
        write_inputs(props[props.week == wk], 2026, wk)
    mrows = model_rows(alt, 2026, range(3, 7))
    # Q3 forward: the cards the pipeline actually published (all markets), settled from nflverse
    cards = []
    for wk in range(3, 7):
        for s in SLATES:
            f = ROOT / "automation" / "cards" / f"card_2026_w{wk}_{s}.json"
            if f.exists():
                cards.append(dict(week=wk, slate=s, card=json.load(open(f))))
    mo_lookup = {(common.norm_name(p), s, float(r), int(wk)): mo for p, s, r, wk, mo in
                 zip(mrows.player, mrows.stat, mrows.rung, mrows.week, mrows.MO)}
    q3f = q3(cards, w, played, known, mo_lookup)
    rec = [c for c in q3f.get("candidates", []) if c["market"] in ("receptions", "rec_yds")]
    res = {"weeks": [3, 4, 5, 6], "Q1": q1(alt), "Q2": q2(mrows), "Q4": q4(alt, fs_mu(2026)),
           "Q3_published_cards": {"legs": q3f["legs"], "tickets": q3f["tickets"]},
           "Q3_receptions_recyds_only": roi_summary(pd.DataFrame(rec)) if rec else {"n": 0}}
    (OUT / "results_forward_2026.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float)[:15000])


if __name__ == "__main__":
    {"registered": registered, "forward": forward}[sys.argv[1]]()
