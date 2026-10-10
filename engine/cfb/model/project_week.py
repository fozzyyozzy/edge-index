"""Live projections + fair alt ladders for one week (Phase 3 brief §7).

    python -m engine.cfb.model.project_week --season 2026 --week 7 [--no-fetch]

* Ratings: Phase 2 as-of ratings for (season, week) (warns if plays are missing).
* Lines: ONE CFBD /lines call for the week (DraftKings, else Bovada, else the
  median across providers); --no-fetch uses the last cached response.
  The current spread stands in for the backtest's open (params.lines).
* QB: data/cfb/manual/qb_overrides.csv (game_id or team, week, qb_out,
  replacement_qb, note). Live, nothing else sets qb_delta.
Outputs data/cfb/derived/projections_<season>_wk<NN>.parquet and .json.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.cfbd_client import CFBDClient
from engine.cfb.model import distribution as dist, features, forward, margin_model as mm, run as mrun
from engine.cfb.ratings import evaluate as reval, run as rrun

OVERRIDES = config.DATA / "manual" / "qb_overrides.csv"


def name_key(name: str) -> str | None:
    return features.passer_key(f"{name} pass")


def live_lines(season: int, week: int, fetch: bool) -> tuple[pd.DataFrame, str]:
    """(lines, capture_ts_utc). Projection line: DraftKings, else Bovada, else median."""
    raw, ts = forward.fetch_lines(season, week, fetch, tag="")
    rows = []
    for g in raw:
        by = {ln["provider"]: ln for ln in g.get("lines") or [] if ln.get("spread") is not None}
        pick = next((p for p in ("DraftKings", "Bovada") if p in by), None)
        if pick:
            spread, total = by[pick]["spread"], by[pick].get("overUnder")
        elif by:
            pick = "median"
            spread = float(np.median([v["spread"] for v in by.values()]))
            tots = [v.get("overUnder") for v in by.values() if v.get("overUnder") is not None]
            total = float(np.median(tots)) if tots else None
        else:
            continue
        tots = [v.get("overUnder") for v in by.values() if v.get("overUnder") is not None]
        rows.append({"game_id": g["id"], "provider": pick, "spread": float(spread),
                     "total": total if total is not None else (np.median(tots) if tots else np.nan)})
    lines = pd.DataFrame(rows)
    dk = forward.parse_lines(raw)[["game_id", "dk_spread", "dk_total"]]
    return (lines.merge(dk, on="game_id", how="left") if len(lines) else lines), ts


def qb_overrides(mg: pd.DataFrame, week: int, plays) -> pd.DataFrame:
    """qb_delta per (game, side) from the manual file; same formula as the backtest."""
    if not OVERRIDES.exists():
        return pd.DataFrame(columns=["game_id", "side", "qb_delta", "note"])
    ov = pd.read_csv(OVERRIDES, dtype=str).fillna("")
    ov = ov[(ov.week == "") | (ov.week == str(week))]
    if ov.empty:
        return pd.DataFrame(columns=["game_id", "side", "qb_delta", "note"])
    db = features.dropbacks(plays)
    per_game = (db.groupby(["game_id", "team_id", "qb"])
                .agg(n=("ppa", "size"), epa=("ppa", "sum"), kick=("kickoff_utc", "first"),
                     season=("season", "first")).reset_index())
    s21 = per_game[per_game.season == 2021]
    league = s21.epa.sum() / s21.n.sum()
    starters = per_game.sort_values("n", ascending=False).drop_duplicates(["game_id", "team_id"])
    ns = per_game.merge(starters[["game_id", "team_id", "qb"]].assign(st=1),
                        on=["game_id", "team_id", "qb"], how="left")
    ns21 = ns[(ns.st != 1) & (ns.season == 2021)]
    repl = ns21.epa.sum() / ns21.n.sum()
    out = []
    for o in ov.itertuples():
        for r in mg.itertuples():
            for side in ("home", "away"):
                team = getattr(r, f"{side}_team")
                if not ((o.game_id and str(r.game_id) == o.game_id) or
                        (not o.game_id and o.team.strip().lower() == team.lower())):
                    continue
                if o.game_id and o.team and o.team.strip().lower() != team.lower():
                    continue
                hist = per_game[per_game.kick < r.cutoff]
                tid = getattr(r, f"{side}_id")
                b = hist[hist.qb == name_key(o.replacement_qb)]
                s = hist[hist.qb == name_key(o.qb_out)]
                b_rate = (b.epa.sum() + features.QB_N0_BACKUP * repl) / (b.n.sum() + features.QB_N0_BACKUP)
                s_rate = (s.epa.sum() + features.QB_N0_STARTER * league) / (s.n.sum() + features.QB_N0_STARTER)
                tdb = hist[(hist.team_id == tid) & (hist.season == r.season)] \
                    .groupby("game_id").n.sum().mean()
                out.append({"game_id": r.game_id, "side": side,
                            "qb_delta": float((b_rate - s_rate) * (tdb if pd.notna(tdb) else 30)),
                            "note": f"{team}: {o.qb_out} out, {o.replacement_qb} in "
                                    f"({b.n.sum()} career dropbacks). {o.note}".strip()})
    return pd.DataFrame(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--no-fetch", action="store_true", help="use the cached live lines")
    ap.add_argument("--no-log", action="store_true",
                    help="don't append to the forward-test log (testing)")
    ap.add_argument("--log-dir", type=Path, default=forward.FORWARD)
    ap.add_argument("--log-anyway", action="store_true",
                    help="log even if completed games before the cutoff lack plays")
    a = ap.parse_args(argv)
    params = mrun.load_params()
    dp = mrun.dist_params(params)

    # ratings as of this week (Phase 2 chain), injected into the feature build
    rd = rrun.Data()
    slate = reval.asof_slate(rd, rrun.load_params(), a.season, a.week)
    ratings = pd.read_parquet(features.DERIVED / "ratings_asof.parquet")
    ratings = pd.concat([ratings[~((ratings.season == a.season) & (ratings.week_asof == a.week))],
                         slate[ratings.columns]], ignore_index=True)
    games, plays = features.load_inputs()
    mg = features.build(write=False, games=games, plays=plays, ratings=ratings)
    mg = mg[(mg.season == a.season) & (mg.week_asof == a.week)
            & (mg.season_type == "regular")].copy()

    # live lines replace the historical open
    ll, capture_ts = live_lines(a.season, a.week, fetch=not a.no_fetch)
    mg = mg.drop(columns=["provider", "spread_open", "total_bet", "open_margin"]).merge(
        ll.rename(columns={"spread": "spread_open", "total": "total_bet"}), on="game_id", how="left")
    mg["open_margin"] = -mg.spread_open
    mg["total_bet"] = mg.total_bet.fillna(mg.total_bet.median())
    no_line = mg[mg.open_margin.isna()]

    # QB: live, only the override file sets qb_delta
    mg["qb_delta"] = 0.0
    mg["qb_note"] = ""
    qo = qb_overrides(mg, a.week, plays)
    for q in qo.itertuples():
        sign = 1 if q.side == "home" else -1
        mg.loc[mg.game_id == q.game_id, "qb_delta"] += sign * q.qb_delta
        mg.loc[mg.game_id == q.game_id, "qb_note"] += q.note + " "

    d = mm.prep(mg.dropna(subset=["open_margin"]))
    d["proj"] = mm.predict(d, {"groups": params["groups"], "coef": params["coef"]})
    # ratings only (QB term off): reported alongside in the forward test
    d["proj_ratings_only"] = mm.predict(d.assign(qb_delta=0.0),
                                        {"groups": params["groups"], "coef": params["coef"]})
    d["absline"] = d.open_margin.abs()
    P = dist.pmf(d.proj, d.absline, d.total_bet, dp)
    d["sigma"] = dist.sigma([dp["a"], dp["b"], dp["c"]], d.absline, d.total_bet)
    d["edge"] = d.proj - d.open_margin
    d["home_cover_at_line"] = dist.cover(P, d.spread_open.to_numpy(), "home")[0]

    records = []
    for i, r in enumerate(d.reset_index(drop=True).itertuples()):
        lad = dist.ladder(P[i])
        records.append({
            "game_id": int(r.game_id), "kickoff_utc": str(r.kickoff_utc),
            "away_team": r.away_team, "home_team": r.home_team, "neutral_site": bool(r.neutral_site),
            "line_provider": r.provider, "home_spread": r.spread_open, "total": r.total_bet,
            "ratings_margin": r.ratings_margin, "projected_home_margin": r.proj,
            "sigma": r.sigma, "edge_home_pts": r.edge, "qb_note": r.qb_note.strip(),
            "ladder": lad.to_dict(orient="records")})
    stem = features.DERIVED / f"projections_{a.season}_wk{a.week:02d}"
    flat = d[["game_id", "kickoff_utc", "away_team", "home_team", "provider", "spread_open",
              "total_bet", "ratings_margin", "proj", "sigma", "edge", "home_cover_at_line",
              "qb_note"]].rename(columns={"spread_open": "home_spread", "total_bet": "total",
                                          "proj": "projected_home_margin"})
    flat["ladder_json"] = [json.dumps(rec["ladder"]) for rec in records]
    flat.to_parquet(stem.with_suffix(".parquet"), index=False)
    stem.with_suffix(".json").write_text(json.dumps(
        {"season": a.season, "week": a.week, "params_frozen_at": params["frozen_at"],
         "games": records}, indent=1, default=float))

    # forward-test guard: the scored capture is the FIRST one per game, so never log a
    # projection whose ratings are missing completed games (run update_week first)
    cut = slate.cutoff.iloc[0]
    done = games[(games.season == a.season) & games.fbs_involved & (games.completed == True)  # noqa: E712
                 & (games.kickoff_utc < cut) & ~(games.is_bowl & ~games.is_cfp)]
    missing = int((~done.game_id.isin(plays.game_id)).sum())
    if not a.no_log and missing and not a.log_anyway:
        print(f"forward log: NOT logged: {missing} completed games before the week-{a.week} "
              f"cutoff have no plays (run python -m engine.cfb.update_week, then re-run)")
    elif not a.no_log:
        log = d[["game_id", "season", "week", "home_team", "away_team", "kickoff_utc",
                 "dk_spread", "dk_total", "provider", "spread_open", "ratings_margin",
                 "qb_delta", "qb_note", "proj", "proj_ratings_only", "sigma"]].rename(
            columns={"spread_open": "line_used", "proj": "proj_primary"})
        log.insert(0, "capture_ts_utc", capture_ts)
        log["kickoff_utc"] = pd.to_datetime(log.kickoff_utc, utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        log["params_sha256"] = hashlib.sha256(mrun.PARAMS.read_bytes()).hexdigest()[:12]
        n0 = len(log)
        log = forward.pregame(log, capture_ts)
        path = forward.append(a.log_dir, forward.PROJ_LOG, log)
        print(f"forward log: {len(log)} rows appended ({n0 - len(log)} skipped: already kicked "
              f"off), lines captured {capture_ts} -> {path}")

    k = params["coef"]
    print(f"{a.season} week {a.week}: {len(d)} games projected "
          f"(k weeks 4-8 = {k['k_4-8']:+.2f}, 9+ = {k['k_9+']:+.2f}); "
          f"{len(no_line)} without a line: {', '.join((no_line.away_team + ' @ ' + no_line.home_team).head(6))}")
    show = d.reindex(d.edge.abs().sort_values(ascending=False).index).head(25)
    show = show.assign(matchup=show.away_team + " @ " + show.home_team,
                       line=show.spread_open.map(lambda v: f"{v:+.1f}"),
                       model=(-show.proj).map(lambda v: f"{v:+.1f}"),
                       edge=show.edge.map(lambda v: f"{v:+.1f}"),
                       home_cover=(100 * show.home_cover_at_line).map(lambda v: f"{v:.1f}%"))
    print(show[["matchup", "provider", "line", "model", "edge", "home_cover", "qb_note"]]
          .to_string(index=False))
    print("(line/model = home spread; edge = model minus line in home points; + favors home)")
    print(f"-> {stem.with_suffix('.parquet')}  and .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
