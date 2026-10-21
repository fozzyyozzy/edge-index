"""NFL factor study (docs/nfl/PREREG_FACTORS.md): do situational reads beat DK's de-vigged price?

    python -m engine.nfl.factor_study build    # features only -> data/nfl/verify/factor_rows_{A,B}.parquet (no fitting)
    python -m engine.nfl.factor_study run      # ONCE: fit weeks 1-9, test weeks 10-18 (marker: factor_run.json)

Every rolling feature comes from an as-of join on (season, week) that EXCLUDES the row's own game, over the entity's
last 16 regular-season games across 2024-2025 (the "last 16"). Game-level pregame facts (closing spread/total) and
game weather (actual; ~forecast, noted in the PREREG) attach to the row's own game.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from engine.nfl import verify_replay as vr

common = vr.common
OUT = vr.OUT
RAW = OUT / "raw" / "factor"
FIT_WEEKS, TEST_WEEKS = range(1, 10), range(10, 19)
N = 16
FACTORS = {"F1_man_zone": ["mz"], "F2_game_script": ["implied_total", "team_spread"],
           "F3_pass_tendency": ["proe", "neutral_pass"], "F4_defense_weak_points": ["opp_allowed", "home", "home_split"],
           "F5_weather": ["wind", "precip"]}
F6 = ["hot", "hot_x_tough", "big_fav"]
YCOL = {"receptions": "receptions", "rec_yds": "receiving_yards"}


def t_of(season, week):
    return np.asarray(season, int) * 100 + np.asarray(week, int)


def roll(df, key, cols, n=N):
    """per entity, sums over its last n games INCLUDING each game; looked up later strictly before the row's game"""
    df = df.sort_values([key, "t"]).copy()
    for c in cols:
        df[c] = df.groupby(key)[c].transform(lambda s: s.rolling(n, min_periods=1).sum())
    df["games"] = df.groupby(key).cumcount().clip(upper=n - 1) + 1
    return df[[key, "t"] + cols + ["games"]]


def asof(rows, rows_key, table, table_key, prefix):
    """attach the entity's latest rolled record from a game strictly before the row's game"""
    r = rows[[rows_key, "t"]].reset_index().rename(columns={rows_key: "_k"}).sort_values("t")
    tb = table.rename(columns={table_key: "_k"}).sort_values("t")
    m = pd.merge_asof(r, tb, on="t", by="_k", allow_exact_matches=False, direction="backward")
    m = m.set_index("index").drop(columns=["_k", "t"]).add_prefix(prefix)
    return rows.join(m)


def load_pbp():
    p = pd.concat([pd.read_parquet(RAW / f"play_by_play_{y}.parquet",
                                   columns=["game_id", "play_id", "season", "week", "season_type", "posteam", "defteam",
                                            "home_team", "away_team", "pass", "rush", "qb_dropback", "receiver_player_id",
                                            "complete_pass", "receiving_yards", "pass_oe", "wp", "qtr", "weather", "roof",
                                            "wind"]) for y in (2024, 2025)])
    p = p[p.season_type == "REG"].copy()
    p["t"] = t_of(p.season, p.week)
    part = pd.concat([pd.read_parquet(RAW / f"pbp_participation_{y}.parquet",
                                      columns=["nflverse_game_id", "play_id", "defense_man_zone_type", "offense_players"])
                      for y in (2024, 2025)]).rename(columns={"nflverse_game_id": "game_id"})
    p = p.merge(part, on=["game_id", "play_id"], how="left")
    return p


def team_tables(p):
    """per team-game: man rate faced/played (defense), PROE and neutral pass rate (offense), weather"""
    tag = p[p.defense_man_zone_type.isin(["MAN_COVERAGE", "ZONE_COVERAGE"])]
    d = tag.assign(man=(tag.defense_man_zone_type == "MAN_COVERAGE").astype(float), n=1.0) \
        .groupby(["defteam", "game_id", "t"])[["man", "n"]].sum().reset_index()
    def_man = roll(d, "defteam", ["man", "n"])
    league_man = float(d[d.t < 202501].man.sum() / d[d.t < 202501].n.sum())       # 2024: before every row
    plays = p[(p["pass"] == 1) | (p.rush == 1)]
    o = plays.groupby(["posteam", "game_id", "t"]).agg(proe_sum=("pass_oe", "sum"), proe_n=("pass_oe", "count")).reset_index()
    neu = plays[(plays.wp.between(0.2, 0.8)) & (plays.qtr <= 3)]
    o = o.merge(neu.groupby(["posteam", "game_id"]).agg(neu_pass=("pass", "sum"), neu_n=("pass", "size")).reset_index(),
                on=["posteam", "game_id"], how="left").fillna({"neu_pass": 0, "neu_n": 0})
    off = roll(o, "posteam", ["proe_sum", "proe_n", "neu_pass", "neu_n"])
    g = p.groupby("game_id").agg(roof=("roof", "first"), wind=("wind", "max"), weather=("weather", "first")).reset_index()
    outdoor = g.roof.isin(["outdoors", "open"])
    g["wind_f"] = np.where(outdoor, g.wind.fillna(0), 0.0)
    g["precip_f"] = np.where(outdoor & g.weather.fillna("").str.lower().str.contains("rain|snow|shower|sleet|drizzle"), 1.0, 0.0)
    return def_man, league_man, off, g[["game_id", "wind_f", "precip_f"]]


def receiver_mz(p):
    """per player-game: on-field tagged dropbacks and targets / receiving yards, split man vs zone"""
    tag = p[p.defense_man_zone_type.isin(["MAN_COVERAGE", "ZONE_COVERAGE"]) & (p.qb_dropback == 1)].copy()
    tag["man"] = tag.defense_man_zone_type == "MAN_COVERAGE"
    on = tag[["game_id", "t", "man", "offense_players"]].assign(pid=tag.offense_players.fillna("").str.split(";")) \
        .explode("pid")
    on = on[on.pid.str.len() > 0]
    on_n = on.groupby(["pid", "game_id", "t", "man"]).size().unstack("man", fill_value=0)
    on_n.columns = ["on_zone" if not c else "on_man" for c in on_n.columns]
    tg = tag[tag.receiver_player_id.notna()]
    tt = tg.groupby(["receiver_player_id", "game_id", "t", "man"]).agg(tgt=("play_id", "size"),
                                                                       yds=("receiving_yards", "sum")).unstack("man", fill_value=0)
    tt.columns = [f"{a}_{'man' if b else 'zone'}" for a, b in tt.columns]
    tt.index = tt.index.set_names(["pid", "game_id", "t"])
    m = on_n.join(tt, how="left").fillna(0).reset_index()
    for c in ("tgt_man", "tgt_zone", "yds_man", "yds_zone", "on_man", "on_zone"):
        if c not in m:
            m[c] = 0.0
    return roll(m, "pid", ["on_man", "on_zone", "tgt_man", "tgt_zone", "yds_man", "yds_zone"])


def player_tables(stats):
    """weekly stats (2024-2025 REG) -> player rolled stat sums, home/away splits, roles, defense allowed by role group"""
    s = stats.copy()
    s["t"] = t_of(s.season, s.week)
    s = s.reset_index(drop=True)
    s["group"] = s.position.map({"TE": "TE", "RB": "RB", "FB": "RB"})
    wr = s.position == "WR"                                                    # role in that past game: target rank
    rk = s[wr].groupby(["team", "t"]).targets.rank(method="first", ascending=False)
    s.loc[wr, "group"] = np.where(rk == 1, "WR1", np.where(rk == 2, "WR2", "WR3"))
    allowed = s[s.group.notna()].groupby(["opponent_team", "t", "group"])[["receptions", "receiving_yards"]].sum() \
        .unstack("group", fill_value=0)
    allowed.columns = [f"{a}_{b}" for a, b in allowed.columns]
    allowed = allowed.reset_index()
    cols = [c for c in allowed.columns if c not in ("opponent_team", "t")]
    league = allowed[allowed.t < 202501][cols].mean()                          # 2024 per-game average by group
    allowed_r = roll(allowed, "opponent_team", cols)
    return s, allowed_r, league


def build():
    props = pd.read_parquet(OUT / "hist_props_2025.parquet")
    props["kickoff"] = pd.to_datetime(props.kickoff, utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    props = props[props.game_type == "REG"]
    alt, _ = vr.price_tables(props)
    w, played, known = vr.outcomes(2025)
    alt = vr.settle(alt.rename(columns={"stat": "market_"}).assign(market=lambda d: d.market_), w, played, known, 2025) \
        .drop(columns=["market"]).rename(columns={"market_": "stat"})
    rowsA = alt[alt.result.isin(["WIN", "LOSS"]) & alt.p_hold.between(0.50, 0.97) & alt.p_anchor.notna()].copy()
    rowsA["y"] = (rowsA.result == "WIN").astype(float)
    # rows B: two-way main lines (proportional de-vig), outcome Over = stat > line
    mn = props[props.market.isin(vr.MAIN)].pivot_table(index=["game_id", "week", "player", "market", "point", "home_team",
                                                               "away_team"], columns="side", values="price",
                                                        aggfunc="first").reset_index().dropna(subset=["Over", "Under"])
    io, iu = vr.implied(mn.Over), vr.implied(mn.Under)
    mn["p_main"] = io / (io + iu)
    mn["stat"] = mn.market.map(vr.MAIN)
    mn["teams"] = list(zip(mn.home_team, mn.away_team))
    mn = mn.assign(rung=mn.point + 0.5)          # Over clears iff stat >= point + 0.5 (point is x.5)
    mn = vr.settle(mn.rename(columns={"market": "odds_market"}).assign(market=mn.stat), w, played, known, 2025)
    rowsB = mn[mn.result.isin(["WIN", "LOSS"])].copy()
    rowsB["y"] = (rowsB.result == "WIN").astype(float)
    # ids, teams, opponents
    stats = pd.concat([vr.cached_read("nflverse weekly player stats", season=y) for y in (2024, 2025)])
    stats = stats[(stats.season_type == "REG") & stats.player_display_name.notna()].copy()
    stats["key"] = stats.player_display_name.map(common.norm_name)
    ident = stats[stats.season == 2025][["key", "team", "player_id", "position"]].drop_duplicates(["key", "team"])
    p = load_pbp()
    def_man, league_man, off, wx = team_tables(p)
    rmz = receiver_mz(p)
    s, allowed_r, league = player_tables(stats)
    sch = vr.cached_read("nflverse schedule")
    sch = sch[sch.season == 2025][["game_id", "home_team", "away_team", "spread_line", "total_line"]]
    out = {}
    for name, rows in (("A", rowsA), ("B", rowsB)):
        r = rows.copy()
        r["key"] = r.player.map(common.norm_name)
        r = r.merge(ident.rename(columns={"team": "team_"}), on="key", how="left")
        r = r[[tm in tt for tm, tt in zip(r.team_, r.teams)]].copy()           # player's team must be in this game
        r["team"] = r.team_
        r["home"] = np.where(r.team == r.home_team, 1.0, -1.0)
        r["opp"] = np.where(r.home > 0, r.away_team, r.home_team)
        r["t"] = t_of(2025, r.week)
        r = r.merge(sch[["game_id", "spread_line", "total_line"]], on="game_id", how="left")
        # F2: spread_line > 0 = home favored
        r["implied_total"] = np.where(r.home > 0, (r.total_line + r.spread_line) / 2, (r.total_line - r.spread_line) / 2)
        r["team_spread"] = np.where(r.home > 0, -r.spread_line, r.spread_line)
        r = r.merge(wx, on="game_id", how="left").rename(columns={"wind_f": "wind", "precip_f": "precip"})
        # F1
        r = asof(r, "opp", def_man, "defteam", "dm_")
        r = asof(r, "player_id", rmz, "pid", "rz_")
        opp_rate = r.dm_man / r.dm_n
        if name == "A":
            num_man = np.where(r.stat == "receptions", r.rz_tgt_man, r.rz_yds_man)
            num_zone = np.where(r.stat == "receptions", r.rz_tgt_zone, r.rz_yds_zone)
            split = num_man / (r.rz_on_man + 40) - num_zone / (r.rz_on_zone + 40)
            r["mz"] = (opp_rate - league_man) * split
        # F3
        r = asof(r, "team", off, "posteam", "of_")
        r["proe"] = r.of_proe_sum / r.of_proe_n
        r["neutral_pass"] = r.of_neu_pass / r.of_neu_n
        # player history (last 16 / last 3 / home split / role) from weekly stats strictly before
        ps = s[["player_id", "t", "team", "receptions", "receiving_yards", "targets", "position"]].copy()
        hist = []
        for row in r[["player_id", "t", "stat", "team"]].drop_duplicates().itertuples():
            h = ps[(ps.player_id == row.player_id) & (ps.t < row.t)].sort_values("t")
            v16 = h[YCOL[row.stat]].fillna(0).to_numpy()[-N:]
            hist.append(dict(player_id=row.player_id, t=row.t, stat=row.stat,
                             last16_mean=v16.mean() if len(v16) else np.nan, last16_sd=v16.std() if len(v16) > 1 else np.nan,
                             last3_mean=v16[-3:].mean() if len(v16) else np.nan, n16=len(v16)))
        hist = pd.DataFrame(hist)
        r = r.merge(hist, on=["player_id", "t", "stat"], how="left")
        # home split: needs where each past game was played -> from schedule of both seasons
        allsch = vr.cached_read("nflverse schedule")
        allsch = allsch[allsch.season.isin([2024, 2025]) & (allsch.game_type == "REG")]
        hm = pd.concat([allsch[["season", "week", "home_team"]].rename(columns={"home_team": "team"}).assign(h=1),
                        allsch[["season", "week", "away_team"]].rename(columns={"away_team": "team"}).assign(h=0)])
        hm["t"] = t_of(hm.season, hm.week)
        ps2 = ps.merge(hm[["team", "t", "h"]], on=["team", "t"], how="left")
        hs = []
        for row in r[["player_id", "t", "stat"]].drop_duplicates().itertuples():
            h = ps2[(ps2.player_id == row.player_id) & (ps2.t < row.t)].sort_values("t").tail(N)
            v = h[YCOL[row.stat]].fillna(0)
            a, b = v[h.h == 1], v[h.h == 0]
            n = len(h)
            hs.append(dict(player_id=row.player_id, t=row.t, stat=row.stat,
                           home_split=((a.mean() - b.mean()) * n / (n + 8)) if len(a) and len(b) else np.nan))
        r = r.merge(pd.DataFrame(hs), on=["player_id", "t", "stat"], how="left")
        # F4 role from the player's last 4 games with his current team (target rank among team WRs)
        role = []
        for row in r[["player_id", "t", "team", "position"]].drop_duplicates().itertuples():
            if row.position in ("TE",):
                role.append((row.player_id, row.t, "TE")); continue
            if row.position in ("RB", "FB"):
                role.append((row.player_id, row.t, "RB")); continue
            tg = ps[(ps.team == row.team) & (ps.position == "WR") & (ps.t < row.t)]
            last4 = sorted(tg.t.unique())[-4:]
            rank = tg[tg.t.isin(last4)].groupby("player_id").targets.sum().sort_values(ascending=False)
            pos = list(rank.index).index(row.player_id) if row.player_id in rank.index else 2
            role.append((row.player_id, row.t, ["WR1", "WR2"][pos] if pos < 2 else "WR3"))
        r = r.merge(pd.DataFrame(role, columns=["player_id", "t", "group"]), on=["player_id", "t"], how="left")
        r = asof(r, "opp", allowed_r, "opponent_team", "al_")
        col = [f"al_{YCOL[s_]}_{g}" for s_, g in zip(r.stat, r.group)]
        num = np.array([r.at[i, c] if c in r.columns else np.nan for i, c in zip(r.index, col)], dtype=float)
        lg = np.array([league.get(c[3:], np.nan) for c in col], dtype=float)
        r["opp_allowed"] = num / r.al_games / lg - 1
        # F6
        r["hot"] = (r.last3_mean - r.last16_mean) / np.maximum(r.last16_sd.fillna(1), 1)
        r["hot_x_tough"] = r.hot * (-r.opp_allowed)
        r["big_fav"] = (r.team_spread <= -10).astype(float)
        keep = [c for c in r.columns if not c.startswith(("dm_", "rz_", "of_", "al_"))]
        out[name] = r[keep]
        out[name].drop(columns=["teams"]).to_parquet(OUT / f"factor_rows_{name}.parquet", index=False)
        feats = sorted({f for fs in FACTORS.values() for f in fs} | set(F6))
        print(name, len(rows), "->", len(r), "rows matched;", r.groupby("week").size().pipe(lambda x: f"weeks {x.index.min()}-{x.index.max()}"))
        print(r[[f for f in feats if f in r]].describe().round(3).loc[["count", "mean", "std", "min", "max"]].to_string())


# ---------- fitting and testing ----------
def logit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_offset(X, y, off, ridge=1e-6):
    """max-likelihood logistic with offset and no intercept"""
    b = np.zeros(X.shape[1])
    for _ in range(100):
        eta = off + X @ b
        mu = 1 / (1 + np.exp(-eta))
        w = mu * (1 - mu)
        g = X.T @ (y - mu) - ridge * b
        H = X.T @ (w[:, None] * X) + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(H, g)
        b += step
        if np.max(np.abs(step)) < 1e-10:
            break
    return b


def predict(X, off, b):
    return 1 / (1 + np.exp(-(off + X @ b)))


def standardize(df, feats, fit_mask):
    X = df[feats].astype(float).copy()
    mu, sd = X[fit_mask].mean(), X[fit_mask].std().replace(0, 1)
    return ((X - mu) / sd).fillna(0.0).to_numpy(), {f: [float(mu[f]), float(sd[f])] for f in feats}


def evaluate(r, feats, methods):
    """per market fit on weeks 1-9, test 10-18; returns test predictions per method and coefficients"""
    fit = r.week.isin(FIT_WEEKS).to_numpy()
    X, scale = standardize(r, feats, fit)
    preds, coefs = {}, {}
    for m, pcol in methods.items():
        p = np.full(len(r), np.nan)
        for s in r.stat.unique():
            sm = (r.stat == s).to_numpy()
            b = fit_offset(X[fit & sm], r.y.to_numpy()[fit & sm], logit(r[pcol].to_numpy()[fit & sm]))
            coefs[f"{m}:{s}"] = dict(zip(feats, map(float, b)))
            p[sm] = predict(X[sm], logit(r[pcol].to_numpy()[sm]), b)
        preds[m] = p
    return preds, coefs, scale


def delta_ci(y, p_new, p_old, games):
    d = pd.DataFrame({"d": (p_new - y) ** 2 - (p_old - y) ** 2, "g": games})
    by = d.groupby("g").d.agg(["sum", "size"])
    s, n = by["sum"].to_numpy(), by["size"].to_numpy()
    rng = np.random.default_rng(vr.SEED)
    idx = rng.integers(0, len(by), size=(vr.BOOT, len(by)))
    means = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return float(d.d.mean()), [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def test_factor(r, feats, methods):
    preds, coefs, scale = evaluate(r, feats, methods)
    te = r.week.isin(TEST_WEEKS).to_numpy()
    res = {"features": feats, "coefficients_fit_weeks_1_9": coefs, "test_rows": int(te.sum()), "methods": {}}
    for m, pcol in methods.items():
        y, pn, po = r.y.to_numpy()[te], preds[m][te], r[pcol].to_numpy()[te]
        d, ci = delta_ci(y, pn, po, r.game_id.to_numpy()[te])
        res["methods"][m] = {"brier_dk": vr.brier(po, y), "brier_factor": vr.brier(pn, y), "delta": d, "delta_ci95": ci,
                             "by_market": {s: {"brier_dk": vr.brier(po[(r.stat.to_numpy()[te] == s)], y[(r.stat.to_numpy()[te] == s)]),
                                               "brier_factor": vr.brier(pn[(r.stat.to_numpy()[te] == s)], y[(r.stat.to_numpy()[te] == s)])}
                                           for s in r.stat.unique()}}
    res["passes"] = all(v["brier_factor"] < v["brier_dk"] for v in res["methods"].values())
    res["distinguishable_from_noise"] = all(v["delta_ci95"][1] < 0 for v in res["methods"].values())
    return res, preds


def card(r, p_model, side_main=False):
    """flat 1u singles on weeks 10-18: one leg per player-game-market, floor band (raw implied 60-95%), EV > 0 at DK's price"""
    te = r.week.isin(TEST_WEEKS).to_numpy()
    d = r[te].copy()
    d["p"] = p_model[te]
    if side_main:
        o = d.assign(side="Over", price=d.Over, ps=d.p, win=d.y == 1)
        u = d.assign(side="Under", price=d.Under, ps=1 - d.p, win=d.y == 0)
        d = pd.concat([o, u])
    else:
        d["ps"], d["win"] = d.p, d.y == 1
    d["imp"] = vr.implied(d.price)
    d["ev"] = d.ps * vr.dec(d.price) - 1
    d = d[(d.ev > 0) & d.imp.between(0.60, 0.95, inclusive="left")] if not side_main else d[d.ev > 0]
    d = d.sort_values("ev", ascending=False).drop_duplicates(["game_id", "player", "stat"])
    if d.empty:
        return {"n": 0}
    ret = np.where(d.win, vr.dec(d.price) - 1, -1.0)
    lo, hi = vr.boot_ci(pd.Series(ret), d.game_id)
    out = {"n": int(len(d)), "games": int(d.game_id.nunique()), "hit": round(float(d.win.mean()) * 100, 2),
           "avg_implied": round(float(d.imp.mean()) * 100, 2), "mean_model_p": round(float(d.ps.mean()) * 100, 2),
           "roi_pct": round(float(ret.mean()) * 100, 2), "ci95_pct": [round(lo * 100, 2), round(hi * 100, 2)]}
    if side_main:
        out["sides"] = d.side.value_counts().to_dict()
    return out


def run():
    marker = OUT / "factor_run.json"
    if marker.exists():
        sys.exit(f"refusing: the registered factor study already ran ({marker})")
    import subprocess
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=vr.ROOT).stdout.strip()
    marker.write_text(json.dumps({"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "code_commit": commit}, indent=2))
    A = pd.read_parquet(OUT / "factor_rows_A.parquet")
    B = pd.read_parquet(OUT / "factor_rows_B.parquet")
    mA = {"hold": "p_hold", "anchor": "p_anchor"}
    mB = {"main": "p_main"}
    res = {"code_commit": commit, "rows": {"A": int(len(A)), "B": int(len(B))}, "factors": {}, "cards_descriptive": {}}
    passing = []
    for f, feats in FACTORS.items():
        r, preds = test_factor(A, feats, mA)
        res["factors"][f] = r
        res["cards_descriptive"][f] = card(A, preds["hold"])
        if r["passes"]:
            passing += feats
    r6, p6 = test_factor(B, F6, mB)
    res["factors"]["F6_unders"] = r6
    res["cards_descriptive"]["F6_unders"] = card(B, p6["main"], side_main=True)
    res["passing_features_A"] = passing
    if passing:
        rc, pc = test_factor(A, passing, mA)
        res["combined"] = rc
        res["card_registered"] = card(A, pc["hold"]) if rc["passes"] else {"n": 0, "note": "combined model failed the test"}
    else:
        res["combined"] = None
        res["card_registered"] = {"n": 0, "note": "no factor passed: no registered card"}
    res["unders_card_registered"] = res["cards_descriptive"]["F6_unders"] if r6["passes"] else {"n": 0, "note": "F6 failed"}
    (OUT / "factor_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "factors"}, indent=1, default=float))
    for f, r in res["factors"].items():
        print(f, "PASS" if r["passes"] else "fail", "noise-distinct" if r["distinguishable_from_noise"] else "",
              {m: (round(v["brier_dk"], 5), round(v["brier_factor"], 5), [round(x, 5) for x in v["delta_ci95"]])
               for m, v in r["methods"].items()})


if __name__ == "__main__":
    {"build": build, "run": run}[sys.argv[1]]()
