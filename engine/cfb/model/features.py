"""Game-level features as of each game's week cutoff (Phase 3 brief §2-3).

    python -m engine.cfb.model.features        # builds data/cfb/derived/model_games.parquet

One row per FBS-vs-FBS game (non-CFP bowls excluded), 2021-2026. Every
feature uses only plays/results from games that kicked off before the game's
as-of cutoff (the earliest kickoff of its week slot, as in Phase 2), except:
  * qb_change uses THIS game's starter (most dropbacks). That assumes injury /
    depth-chart news is known at bet time (brief §3); live, the manual
    override file replaces it.
  * schedule facts (rest days, venues, distances) are known in advance.

Lines (brief §2): one provider per game for both open and close.
  2021-2025: Bovada, else DraftKings;  2026: DraftKings, else Bovada.
  (DK's 2023 "open" equals its close in 47% of games vs Bovada's 17%, so
  Bovada is the more trustworthy historical opener.)
  The provider needs a non-null open AND close; consensus close is kept
  separately for "vs close" evaluations only.

Special teams (opponent-adjusted, ridge-to-prior as in Phase 2):
  st_fp   net average starting field position (yards from own goal) of a
          team's drives minus its opponents' drives, ridge per drive with
          prior = ST_PRIOR_FACTOR x previous season's final, FCS -> 0.
  st_fg   field-goal points over expected per game: 3 x (made - p(make|dist)),
          p from a logistic fit on strictly earlier seasons (2021 uses itself;
          it's burn-in), shrunk toward ST_PRIOR_FACTOR x last season with
          FG_N0 pseudo-games.
QB: dropbacks = passes + sacks (+ CFBD-tagged scrambles); the passer is parsed
  from play text and keyed as first initial + last name ("c.boley").
"""
from __future__ import annotations
import re

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from engine.cfb import config
from engine.cfb.ratings import adjust
from engine.cfb.ratings.plays_prep import DERIVED

MODEL_GAMES = DERIVED / "model_games.parquet"
SEASONS = list(range(2021, config.CURRENT_SEASON + 1))

ST_PRIOR_FACTOR = 0.5
FP_LAMBDA = 20.0          # drives
FG_N0 = 4.0               # pseudo-games
QB_MIN_STARTS = 3
QB_N0_BACKUP = 300.0      # dropbacks of shrinkage toward replacement level
QB_N0_STARTER = 50.0      # toward league mean
REST_CAP = 7
BYE_DAYS = 13
WEST_TZ = {"America/Los_Angeles", "America/Denver", "America/Phoenix", "America/Boise"}
EAST_TZ = {"America/New_York", "America/Detroit", "America/Indiana/Indianapolis",
           "America/Kentucky/Louisville"}

DROPBACK_TYPES = {"Pass Reception", "Pass Incompletion", "Pass Completion",
                  "Passing Touchdown", "Pass", "Sack", "Interception",
                  "Pass Interception Return", "Interception Return Touchdown"}
NON_DRIVE_START = {"Kickoff", "Kickoff Return (Offense)", "Kickoff Return Touchdown",
                   "Timeout", "End Period", "End of Half", "End of Game",
                   "End of Regulation", "Uncategorized", "placeholder"}
FG_TYPES = {"Field Goal Good": 1, "Field Goal Missed": 0, "Blocked Field Goal": 0,
            "Missed Field Goal Return": 0, "Blocked Field Goal Touchdown": 0,
            "Missed Field Goal Return Touchdown": 0}


def bucket_of(week_asof: pd.Series, season_type: pd.Series) -> pd.Series:
    b = np.select([week_asof <= 3, week_asof <= 8], ["1-3", "4-8"], default="9+")
    return pd.Series(b, index=week_asof.index)   # CFP games fall in 9+


# ------------------------------------------------------------------ inputs
def load_inputs():
    games = pd.read_parquet(config.CLEAN / "games.parquet")
    plays = pd.read_parquet(config.CLEAN / "plays.parquet", columns=[
        "game_id", "season", "drive_id", "drive_number", "play_number", "offense",
        "offense_id", "defense_id", "period", "yards_to_goal", "play_type",
        "play_text", "ppa", "is_duplicate"])
    plays = plays[plays.game_id.isin(games.game_id[games.fbs_involved])]
    plays = plays.merge(games[["game_id", "kickoff_utc"]], on="game_id")
    return games, plays


def slots(games: pd.DataFrame) -> pd.DataFrame:
    """game_id -> season, week_asof, cutoff (Phase 2 slot convention)."""
    out = []
    for s in SEASONS:
        ctx = adjust.season_ctx(games, s)
        sl = adjust.slot_for_game(ctx, games).rename("week_asof").reset_index()
        sl = sl.merge(ctx.slots[["week_asof", "cutoff"]], on="week_asof", how="left")
        sl["season"] = s
        out.append(sl)
    return pd.concat(out, ignore_index=True)


# ------------------------------------------------------------------ lines
def pick_lines(games: pd.DataFrame) -> pd.DataFrame:
    L = pd.read_parquet(config.CLEAN / "lines.parquet")
    L = L.dropna(subset=["spread", "spread_open"])
    rows = []
    for gid, grp in L.groupby("game_id"):
        season = grp.season.iloc[0]
        pref = (["DraftKings", "Bovada"] if season >= config.CURRENT_SEASON
                else ["Bovada", "DraftKings"])
        by = grp.set_index("provider")
        for p in pref:
            if p in by.index:
                r = by.loc[p]
                rows.append({"game_id": gid, "provider": p, "spread_open": r.spread_open,
                             "spread_close": r.spread,
                             "total_open": r.total_open, "total_close": r.total})
                break
    out = pd.DataFrame(rows)
    med_total = (pd.read_parquet(config.CLEAN / "lines.parquet")
                 .groupby("game_id").total.median().rename("total_median"))
    out = out.merge(med_total, on="game_id", how="left")
    # bet-time total for the spread-scale model: provider open, else provider close, else median
    out["total_bet"] = out.total_open.fillna(out.total_close).fillna(out.total_median)
    return out


# ------------------------------------------------------------------ special teams
def drive_starts(plays: pd.DataFrame) -> pd.DataFrame:
    p = plays[(plays.period <= 4) & ~plays.play_type.isin(NON_DRIVE_START)
              & ~plays.is_duplicate.fillna(False) & plays.yards_to_goal.between(1, 99)]
    p = p.sort_values(["game_id", "drive_number", "play_number"])
    d = p.drop_duplicates("drive_id")
    d = d.dropna(subset=["offense_id", "defense_id"])
    return pd.DataFrame({"game_id": d.game_id.values, "season": d.season.values,
                         "kickoff_utc": pd.to_datetime(d.kickoff_utc.values, utc=True),
                         "offense_id": d.offense_id.astype("int64").values,
                         "defense_id": d.defense_id.astype("int64").values,
                         "start": (100 - d.yards_to_goal).astype(float).values})


def fg_attempts(plays: pd.DataFrame) -> pd.DataFrame:
    f = plays[plays.play_type.isin(FG_TYPES) & ~plays.is_duplicate.fillna(False)].copy()
    f["dist"] = f.yards_to_goal.astype(float) + 17
    f["made"] = f.play_type.map(FG_TYPES)
    f = f.dropna(subset=["offense_id"])
    f["team_id"] = f.offense_id.astype("int64")
    return f[["game_id", "season", "kickoff_utc", "team_id", "dist", "made"]]


def fg_make_models(fg: pd.DataFrame) -> dict:
    """season -> logistic p(make | dist), fit on strictly earlier seasons (2021: itself)."""
    models = {}
    for s in SEASONS:
        tr = fg[fg.season < s] if s > SEASONS[0] else fg[fg.season == s]
        X = np.column_stack([tr.dist, tr.dist ** 2])
        models[s] = LogisticRegression(C=1e6, max_iter=1000).fit(X, tr.made)
    return models


def st_ratings(games, drives, fg, sl) -> pd.DataFrame:
    """(season, week_asof, team_id) -> st_fp, st_fg. Uses data < slot cutoff."""
    models = fg_make_models(fg)
    fg = fg.copy()
    fg["poe"] = 0.0
    for s, m in models.items():
        idx = fg.season == s
        p = m.predict_proba(np.column_stack([fg.dist[idx], fg.dist[idx] ** 2]))[:, 1]
        fg.loc[idx, "poe"] = 3 * (fg.made[idx] - p)

    rows, prev_final = [], None
    for s in SEASONS:
        ctx = adjust.season_ctx(games, s)
        teams = ctx.teams.team_id.values
        if prev_final is None:
            prior_o = pd.Series(0.0, index=teams)
            prior_d = pd.Series(0.0, index=teams)
            prior_fg = pd.Series(0.0, index=teams)
        else:
            prior_o = (ST_PRIOR_FACTOR * prev_final.o_fp).reindex(teams).fillna(0.0)
            prior_d = (ST_PRIOR_FACTOR * prev_final.d_fp).reindex(teams).fillna(0.0)
            prior_fg = (ST_PRIOR_FACTOR * prev_final.st_fg).reindex(teams).fillna(0.0)
        fcs = ctx.teams.set_index("team_id").is_fcs.reindex(teams).values
        prior_o[fcs], prior_d[fcs], prior_fg[fcs] = 0.0, 0.0, 0.0
        ds, fs, tg = drives[drives.season == s], fg[fg.season == s], ctx.team_games

        def at(cut):
            d = ds if cut is None else ds[ds.kickoff_utc < cut]
            f = fs if cut is None else fs[fs.kickoff_utc < cut]
            d = d.assign(offense_home=0)
            O, D, _, _ = adjust.fit_metric(d, teams, prior_o, prior_d, d.start.values,
                                           np.ones(len(d)), FP_LAMBDA)
            ngames = (tg if cut is None else tg[tg.kickoff_utc < cut]).groupby("team_id").size()
            ng = ngames.reindex(teams).fillna(0).values
            poe = f.groupby("team_id").poe.sum().reindex(teams).fillna(0).values
            st_fg = (poe + FG_N0 * prior_fg.values) / (ng + FG_N0)
            return pd.DataFrame({"team_id": teams, "o_fp": O, "d_fp": D, "st_fg": st_fg})

        for w, cut in ctx.slots[["week_asof", "cutoff"]].itertuples(index=False):
            r = at(cut)
            r["st_fp"] = r.o_fp + r.d_fp
            r["season"], r["week_asof"] = s, w
            rows.append(r)
        prev_final = at(None).set_index("team_id")
    return pd.concat(rows, ignore_index=True)


# ------------------------------------------------------------------ QB
_STRIP = re.compile(r"^\(\d+:\d+\)\s*|No Huddle-Shotgun|No Huddle|Shotgun", re.I)
_SUFFIX = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}


def passer_key(text: str) -> str | None:
    t = _STRIP.sub("", str(text or "")).strip()
    # TD format: "Receiver 21 Yd pass from Passer (Kicker Kick)"
    m = re.search(r"\bpass from (#\d+\s*)?([A-Za-z][\w'.\- ]+?)(?:\s*\(|,|$)", t)
    if m:
        name = m.group(2)
    else:
        m = re.match(r"^(#\d+\s*)?(.+?)\s+(pass|sacked|scrambles?)\b", t)
        if not m:
            return None
        name = m.group(2)
    name = re.sub(r"#\d+", "", name).strip()
    if not name or name.upper() == "TEAM":
        return None
    if "." in name and " " not in name:                 # "C.Boley"
        first, last = name.split(".", 1)
    else:
        toks = [x for x in name.split() if x.lower() not in _SUFFIX]
        if len(toks) < 2:
            return None
        first, last = toks[0], toks[-1]
    key = f"{first[:1]}.{last}".lower()
    return re.sub(r"[^a-z.\-']", "", key)


def dropbacks(plays: pd.DataFrame) -> pd.DataFrame:
    t = plays.play_text.fillna("")
    db = plays[plays.play_type.isin(DROPBACK_TYPES)
               | (plays.play_type.isin(["Rush", "Rushing Touchdown"])
                  & t.str.contains("scramble", case=False))]
    db = db[~db.is_duplicate.fillna(False)].dropna(subset=["offense_id"]).copy()
    db["qb"] = db.play_text.map(passer_key)
    db["team_id"] = db.offense_id.astype("int64")
    return db.dropna(subset=["qb"])[["game_id", "season", "kickoff_utc", "team_id",
                                     "qb", "ppa"]]


def qb_features(db: pd.DataFrame, model_games: pd.DataFrame) -> pd.DataFrame:
    """Per (game, side): qb_change and qb_delta (points), using dropbacks < cutoff."""
    per_game = (db.groupby(["game_id", "team_id", "qb"])
                .agg(n=("ppa", "size"), epa=("ppa", "sum"), kick=("kickoff_utc", "first"),
                     season=("season", "first")).reset_index())
    starters = (per_game.sort_values("n", ascending=False)
                .drop_duplicates(["game_id", "team_id"])[["game_id", "team_id", "qb", "kick", "season"]])
    team_db = per_game.groupby(["game_id", "team_id"]).agg(n=("n", "sum"), kick=("kick", "first"),
                                                           season=("season", "first")).reset_index()
    # replacement level: EPA/dropback of non-starters in 2021 (burn-in season)
    ns = per_game.merge(starters[["game_id", "team_id", "qb"]].assign(st=1),
                        on=["game_id", "team_id", "qb"], how="left")
    ns21 = ns[(ns.st != 1) & (ns.season == 2021)]
    repl = ns21.epa.sum() / ns21.n.sum()
    league = per_game[per_game.season == 2021].epa.sum() / per_game[per_game.season == 2021].n.sum()

    out = []
    for r in model_games.itertuples():
        for side in ("home", "away"):
            tid = getattr(r, f"{side}_id")
            row = {"game_id": r.game_id, "side": side, "qb_change": 0, "qb_delta": 0.0,
                   "starter": None, "primary": None}
            st = starters[(starters.game_id == r.game_id) & (starters.team_id == tid)]
            if len(st):
                row["starter"] = st.qb.iloc[0]
            prior = per_game[(per_game.team_id == tid) & (per_game.season == r.season)
                             & (per_game.kick < r.cutoff)]
            if len(prior) and row["starter"]:
                tot = prior.groupby("qb").n.sum()
                primary = tot.idxmax()
                starts = (starters[(starters.team_id == tid) & (starters.season == r.season)
                                   & (starters.kick < r.cutoff)].qb == primary).sum()
                row["primary"] = primary
                if primary != row["starter"] and starts >= QB_MIN_STARTS:
                    hist = per_game[per_game.kick < r.cutoff]
                    b = hist[hist.qb == row["starter"]]
                    s_ = hist[hist.qb == primary]
                    b_rate = (b.epa.sum() + QB_N0_BACKUP * repl) / (b.n.sum() + QB_N0_BACKUP)
                    s_rate = (s_.epa.sum() + QB_N0_STARTER * league) / (s_.n.sum() + QB_N0_STARTER)
                    tdb = team_db[(team_db.team_id == tid) & (team_db.season == r.season)
                                  & (team_db.kick < r.cutoff)].n.mean()
                    row["qb_change"] = 1
                    row["qb_delta"] = (b_rate - s_rate) * tdb
            out.append(row)
    q = pd.DataFrame(out)
    w = q.pivot(index="game_id", columns="side", values=["qb_change", "qb_delta",
                                                          "starter", "primary"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    for c in ("qb_change_home", "qb_change_away"):
        w[c] = w[c].astype(int)
    for c in ("qb_delta_home", "qb_delta_away"):
        w[c] = w[c].astype(float)
    w.attrs["repl"], w.attrs["league"] = repl, league
    return w


# ------------------------------------------------------------------ rest / travel
def haversine_mi(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))


def utc_offset_h(tz: str | None, when: pd.Timestamp) -> float:
    if not isinstance(tz, str):
        return np.nan
    return when.tz_convert(tz).utcoffset().total_seconds() / 3600


def rest_travel(games: pd.DataFrame, mg: pd.DataFrame) -> pd.DataFrame:
    venues = pd.read_parquet(config.CLEAN / "venues.parquet").set_index("venue_id")
    # rest: all games (incl. FCS opponents) per team-season
    long = pd.concat([
        games[["game_id", "season", "kickoff_utc", "home_id"]].rename(columns={"home_id": "team_id"}),
        games[["game_id", "season", "kickoff_utc", "away_id"]].rename(columns={"away_id": "team_id"}),
    ]).dropna(subset=["team_id"]).sort_values(["team_id", "kickoff_utc"])
    long["prev"] = long.groupby(["team_id", "season"]).kickoff_utc.shift(1)
    long["rest"] = (long.kickoff_utc - long.prev).dt.total_seconds() / 86400
    rest = long.set_index(["game_id", "team_id"]).rest

    # home venue: most frequent non-neutral home venue across the data
    hv = (games[~games.neutral_site.astype(bool)].groupby(["home_id", "venue_id"]).size()
          .reset_index(name="n").sort_values("n", ascending=False)
          .drop_duplicates("home_id").set_index("home_id").venue_id)

    def loc(vid):
        if pd.isna(vid) or vid not in venues.index:
            return np.nan, np.nan, None
        v = venues.loc[vid]
        return v.latitude, v.longitude, v.timezone

    rows = []
    for r in mg.itertuples():
        glat, glon, gtz = loc(r.venue_id)
        out = {"game_id": r.game_id}
        for side in ("home", "away"):
            tid = getattr(r, f"{side}_id")
            rd = rest.get((r.game_id, tid), np.nan)
            out[f"rest_{side}"] = rd
            out[f"bye_{side}"] = int(pd.notna(rd) and rd >= BYE_DAYS)
            hlat, hlon, htz = loc(hv.get(tid, np.nan))
            if side == "home" and not r.neutral_site:
                dist, tzx = 0.0, 0.0
            else:
                dist = haversine_mi(hlat, hlon, glat, glon) if pd.notna(hlat) and pd.notna(glat) else np.nan
                tzx = abs(utc_offset_h(htz, r.kickoff_utc) - utc_offset_h(gtz, r.kickoff_utc))
            out[f"dist_{side}"], out[f"tz_{side}"] = dist, tzx
            et_hour = r.kickoff_utc.tz_convert("America/New_York").hour
            out[f"w2e_{side}"] = int(htz in WEST_TZ and gtz in EAST_TZ and et_hour < 13
                                     and not getattr(r, "start_time_tbd", False))
        rows.append(out)
    t = pd.DataFrame(rows)
    rh, ra = t.rest_home, t.rest_away
    t["rest_diff"] = np.where(rh.notna() & ra.notna(), (rh - ra).clip(-REST_CAP, REST_CAP), 0.0)
    t["bye_diff"] = t.bye_home - t.bye_away
    # home perspective: positive = away team travelled more (good for home)
    t["travel_k"] = ((t.dist_away.fillna(0) - t.dist_home.fillna(0)) / 1000.0)
    t["tz_diff"] = t.tz_away.fillna(0) - t.tz_home.fillna(0)
    t["w2e_diff"] = t.w2e_away - t.w2e_home
    return t


# ------------------------------------------------------------------ assemble
def build(write: bool = True, games=None, plays=None, ratings=None) -> pd.DataFrame:
    """Inputs can be injected (leakage tests); default reads the clean/derived tables."""
    if games is None or plays is None:
        games, plays = load_inputs()
    sl = slots(games)
    mg = games[games.both_fbs & ~(games.is_bowl & ~games.is_cfp) & games.season.isin(SEASONS)]
    mg = mg.merge(sl[["game_id", "week_asof", "cutoff"]], on="game_id", how="inner")
    mg["bucket"] = bucket_of(mg.week_asof, mg.season_type)

    if ratings is None:
        ratings = pd.read_parquet(DERIVED / "ratings_asof.parquet")
    pw = ratings[["season", "week_asof", "team_id", "power_pts"]]
    for side in ("home", "away"):
        mg = mg.merge(pw.rename(columns={"team_id": f"{side}_id", "power_pts": f"power_{side}"}),
                      on=["season", "week_asof", f"{side}_id"], how="left")

    st = st_ratings(games, drive_starts(plays), fg_attempts(plays), sl)
    for side in ("home", "away"):
        mg = mg.merge(st[["season", "week_asof", "team_id", "st_fp", "st_fg"]].rename(
            columns={"team_id": f"{side}_id", "st_fp": f"st_fp_{side}", "st_fg": f"st_fg_{side}"}),
            on=["season", "week_asof", f"{side}_id"], how="left")
    mg["st_fp_diff"] = mg.st_fp_home - mg.st_fp_away
    mg["st_fg_diff"] = mg.st_fg_home - mg.st_fg_away

    q = qb_features(dropbacks(plays), mg)
    mg = mg.merge(q, on="game_id", how="left")
    mg["qb_delta"] = mg.qb_delta_home.fillna(0) - mg.qb_delta_away.fillna(0)

    mg = mg.merge(rest_travel(games, mg), on="game_id", how="left")
    mg = mg.merge(pick_lines(games), on="game_id", how="left")
    mg["open_margin"] = -mg.spread_open
    mg["close_margin"] = -mg.spread_close
    mg["consensus_close_margin"] = -mg.consensus_close_spread
    keep = ["game_id", "season", "week", "season_type", "week_asof", "cutoff", "bucket",
            "kickoff_utc", "completed", "neutral_site", "home_id", "home_team", "away_id",
            "away_team", "margin_home", "power_home", "power_away",
            "st_fp_diff", "st_fg_diff", "qb_change_home", "qb_change_away",
            "qb_delta_home", "qb_delta_away", "qb_delta", "starter_home", "primary_home",
            "starter_away", "primary_away", "rest_home", "rest_away", "rest_diff",
            "bye_home", "bye_away", "bye_diff", "dist_home", "dist_away", "travel_k",
            "tz_diff", "w2e_diff", "provider", "spread_open", "spread_close",
            "total_open", "total_close", "total_bet", "open_margin", "close_margin",
            "consensus_close_margin"]
    out = mg[keep].sort_values(["season", "kickoff_utc"]).reset_index(drop=True)
    if write:
        out.to_parquet(MODEL_GAMES, index=False)
    return out


def load() -> pd.DataFrame:
    if not MODEL_GAMES.exists():
        build()
    return pd.read_parquet(MODEL_GAMES)


if __name__ == "__main__":
    df = build()
    print(f"{len(df):,} games -> {MODEL_GAMES}")
    print(df.groupby("season").agg(games=("game_id", "size"),
                                   with_open=("open_margin", lambda s: s.notna().sum()),
                                   bovada=("provider", lambda s: (s == "Bovada").sum()),
                                   dk=("provider", lambda s: (s == "DraftKings").sum()),
                                   qb_changes=("qb_change_home", lambda s: s.sum()),
                                   ).to_string())
