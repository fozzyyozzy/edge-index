"""CFB forward test (docs/cfb/FORWARD_TEST.md): line capture, logs, scoring.

    python -m engine.cfb.model.forward capture-close --season 2026 --week 7   # 1 API call
    python -m engine.cfb.model.forward score                                   # 0 calls

Logs (committed, append-only, the audit trail):
  data/cfb/forward/projections_log.csv  one row per game per project_week run
  data/cfb/forward/closes_log.csv       one row per game per close-capture run
PREGAME ONLY: no row is ever written for a game whose kickoff is at or before
the line's capture time.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.cfbd_client import CFBDClient

FORWARD = config.DATA / "forward"
PROJ_LOG = "projections_log.csv"
CLOSE_LOG = "closes_log.csv"
DOC = config.ROOT / "docs" / "cfb" / "FORWARD_TEST.md"

BARS = {"min_games": 150, "edge": 1.5, "toward_share_pct": 57.0, "avg_move_pts": 0.3,
        "first_week": 4}


# ------------------------------------------------------------------ lines
def fetch_lines(season: int, week: int, fetch: bool, tag: str) -> tuple[list, str]:
    """CFBD /lines for one week. Returns (raw, capture_ts_utc). One call when fetch=True;
    otherwise the cached response, stamped with the file's write time."""
    client = CFBDClient()
    name = f"{season}_wk{week:02d}{tag}"
    if fetch or not client.is_cached("lines_live", name):
        raw = client.get("lines_live", "/lines",
                         {"year": season, "week": week, "seasonType": "regular"}, name,
                         refresh=True)
        ts = datetime.now(timezone.utc)
    else:
        path = client.cache_path("lines_live", name)
        raw = json.loads(path.read_text(encoding="utf-8"))
        ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return raw, ts.isoformat(timespec="seconds")


def parse_lines(raw: list) -> pd.DataFrame:
    rows = []
    for g in raw:
        by = {ln["provider"]: ln for ln in g.get("lines") or [] if ln.get("spread") is not None}
        dk = by.get("DraftKings")
        rows.append({"game_id": g["id"], "home_team": g.get("homeTeam"),
                     "away_team": g.get("awayTeam"),
                     "kickoff_utc": g.get("startDate"),
                     "dk_spread": float(dk["spread"]) if dk else np.nan,
                     "dk_total": float(dk["overUnder"]) if dk and dk.get("overUnder") is not None else np.nan,
                     "providers": ",".join(sorted(by))})
    return pd.DataFrame(rows)


def append(log_dir: Path, name: str, df: pd.DataFrame) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / name
    df.to_csv(path, mode="a", header=not path.exists(), index=False)
    return path


def pregame(df: pd.DataFrame, capture_ts: str) -> pd.DataFrame:
    kick = pd.to_datetime(df.kickoff_utc, utc=True)
    return df[kick > pd.Timestamp(capture_ts)]


# ------------------------------------------------------------------ close capture
def capture_close(season: int, week: int, fetch: bool = True, log_dir: Path = FORWARD) -> int:
    raw, ts = fetch_lines(season, week, fetch, tag="_close")
    L = parse_lines(raw)
    L = L.dropna(subset=["dk_spread"])
    before = len(L)
    L = pregame(L, ts)
    L.insert(0, "capture_ts_utc", ts)
    L.insert(1, "season", season)
    L.insert(2, "week", week)
    path = append(log_dir, CLOSE_LOG, L)
    print(f"{season} wk {week}: {len(L)} DK lines logged as close candidates "
          f"({before - len(L)} skipped: already kicked off) -> {path}")
    return len(L)


# ------------------------------------------------------------------ scoring
def load_logs(log_dir: Path = FORWARD):
    p = pd.read_csv(log_dir / PROJ_LOG) if (log_dir / PROJ_LOG).exists() else pd.DataFrame()
    c = pd.read_csv(log_dir / CLOSE_LOG) if (log_dir / CLOSE_LOG).exists() else pd.DataFrame()
    return p, c


def scored_games(log_dir: Path = FORWARD) -> pd.DataFrame:
    """One row per game: FIRST pre-kickoff projection with a DK line (bet time) and the
    LAST pre-kickoff DK close capture taken after it."""
    p, c = load_logs(log_dir)
    if p.empty:
        return pd.DataFrame()
    for df in (p, c):
        if len(df):
            df["capture_ts_utc"] = pd.to_datetime(df.capture_ts_utc, utc=True)
            df["kickoff_utc"] = pd.to_datetime(df.kickoff_utc, utc=True)
    p = p.dropna(subset=["dk_spread"])
    p = p[(p.capture_ts_utc < p.kickoff_utc) & (p.week >= BARS["first_week"])]
    bet = p.sort_values("capture_ts_utc").drop_duplicates("game_id", keep="first")
    if c.empty:
        bet["close_spread"] = np.nan
        return bet
    c = c[c.capture_ts_utc < c.kickoff_utc]
    c = c.merge(bet[["game_id", "capture_ts_utc"]].rename(columns={"capture_ts_utc": "bet_ts"}),
                on="game_id")
    c = c[c.capture_ts_utc > c.bet_ts]
    close = (c.sort_values("capture_ts_utc").drop_duplicates("game_id", keep="last")
             [["game_id", "dk_spread", "capture_ts_utc"]]
             .rename(columns={"dk_spread": "close_spread", "capture_ts_utc": "close_ts_utc"}))
    return bet.merge(close, on="game_id", how="left")


def clv_stats(g: pd.DataFrame, proj_col: str) -> dict:
    x = g.dropna(subset=["close_spread"])
    line_m = -x.dk_spread
    edge = x[proj_col] - line_m
    move = (-x.close_spread) - line_m              # + = toward home
    q = x[edge.abs() >= BARS["edge"]].index
    e, mv = edge[q], move[q]
    moved = mv != 0
    toward = (np.sign(mv) == np.sign(e)) & moved
    return {"games_edge": int(len(q)),
            "moves": int(moved.sum()),
            "toward_share_pct": float(100 * toward.sum() / moved.sum()) if moved.any() else np.nan,
            "avg_move_toward_model": float((mv * np.sign(e)).mean()) if len(q) else np.nan,
            "corr": float(np.corrcoef(edge, move)[0, 1]) if len(x) > 2 else np.nan}


# ------------------------------------------------------------------ DK snapshot path (Phase 4)
SNAP = config.DATA / "lines" / "snapshots"


def _bucket_k(week: pd.Series, coef: dict) -> pd.Series:
    b = np.where(week <= 3, "1-3", np.where(week <= 8, "4-8", "9+"))
    return pd.Series([coef[f"k_{x}"] for x in b], index=week.index)


def dk_snapshot_games(log_dir: Path = FORWARD) -> pd.DataFrame:
    """Per game from Odds API DK snapshots (pregame only by construction):
    bet line = earliest 'bet' snapshot (Tue 10 AM ET), else the first-seen snapshot;
    close = last snapshot before kickoff (taken after the bet snapshot).
    Projection recomputed at each line with the frozen model from the latest projection-log
    row captured at or before the bet snapshot (else the earliest row)."""
    import glob
    files = sorted(glob.glob(str(SNAP / "dk_main_*_wk*.csv")))
    p, _ = load_logs(log_dir)
    if not files or p.empty:
        return pd.DataFrame()
    m = pd.concat(pd.read_csv(x) for x in files)
    m = m[(m.market == "spreads") & (m.is_home == 1)].dropna(subset=["game_id"])
    m["game_id"] = m.game_id.astype(int)
    m["captured_at_utc"] = pd.to_datetime(m.captured_at_utc, utc=True)
    m["kick"] = pd.to_datetime(m.commence_time, utc=True)
    m = m[m.captured_at_utc < m.kick].sort_values("captured_at_utc")
    first = m.drop_duplicates("game_id", keep="first").set_index("game_id")
    bet = m[m.label == "bet"].drop_duplicates("game_id", keep="first").set_index("game_id")
    bet = bet.reindex(first.index)
    bet_src = np.where(bet.point.notna(), "dk_tue_bet", "dk_first_seen")
    bet = bet.combine_first(first)
    rows = []
    p = p.copy()
    p["capture_ts_utc"] = pd.to_datetime(p.capture_ts_utc, utc=True)
    import json as _json
    from engine.cfb.model.run import PARAMS
    coef = _json.loads(PARAMS.read_text())["coef"]
    for i, gid in enumerate(first.index):
        later = m[(m.game_id == gid) & (m.captured_at_utc > bet.loc[gid, "captured_at_utc"])]
        pr = p[p.game_id == gid]
        if pr.empty:
            continue
        before = pr[pr.capture_ts_utc <= bet.loc[gid, "captured_at_utc"]]
        row = (before if len(before) else pr).sort_values("capture_ts_utc").iloc[-1 if len(before) else 0]
        rows.append({"game_id": gid, "season": row.season, "week": row.week,
                     "kickoff_utc": first.loc[gid, "kick"], "source": bet_src[i],
                     "bet_ts_utc": bet.loc[gid, "captured_at_utc"], "dk_spread": bet.loc[gid, "point"],
                     "first_seen_spread": first.loc[gid, "point"],
                     "close_spread": later.point.iloc[-1] if len(later) else np.nan,
                     "close_ts_utc": later.captured_at_utc.iloc[-1] if len(later) else pd.NaT,
                     "ratings_margin": row.ratings_margin, "qb_delta": row.qb_delta})
    g = pd.DataFrame(rows)
    if g.empty:
        return g
    g = g[g.week >= BARS["first_week"]]
    k = _bucket_k(g.week, coef)
    bq = coef.get("qb_delta", 0.0)
    for col, spread in (("", "dk_spread"), ("_first_seen", "first_seen_spread")):
        L = -g[spread]
        g[f"proj_primary{col}"] = L + k * (g.ratings_margin - L) + bq * g.qb_delta.fillna(0)
        g[f"proj_ratings_only{col}"] = L + k * (g.ratings_margin - L)
    return g


def score(log_dir: Path = FORWARD, write_doc: bool = True) -> dict:
    # DK snapshot lines first (Phase 4 amendment); CFBD-captured lines only where no snapshot exists
    g_dk = dk_snapshot_games(log_dir)
    g_cf = scored_games(log_dir)
    if len(g_cf):
        g_cf = g_cf.assign(source="cfbd_fallback")
        if len(g_dk):
            g_cf = g_cf[~g_cf.game_id.isin(g_dk.game_id)]
    g = pd.concat([x for x in (g_dk, g_cf) if len(x)], ignore_index=True) if (len(g_dk) or len(g_cf)) \
        else pd.DataFrame()
    out = {"scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if g.empty:
        out["status"] = "no projections logged yet"
    else:
        g = g.sort_values("kickoff_utc")
        # evaluation sample: the FIRST 150 qualifying games by kickoff (no optional stopping)
        with_close = g.dropna(subset=["close_spread"])
        edge = with_close.proj_primary - (-with_close.dk_spread)
        qual = with_close[edge.abs() >= BARS["edge"]]
        sample_ids = set(qual.game_id.head(BARS["min_games"]))
        ev = with_close[~((edge.abs() >= BARS["edge"]) & ~with_close.game_id.isin(sample_ids))]
        prim, ronly = clv_stats(ev, "proj_primary"), clv_stats(ev, "proj_ratings_only")
        out.update({"games_logged": int(len(g)), "games_with_close": int(len(with_close)),
                    "line_source": g.source.value_counts().to_dict() if "source" in g else {},
                    "primary": prim, "ratings_only": ronly})
        fs = with_close.dropna(subset=["first_seen_spread"]) if "first_seen_spread" in with_close else None
        if fs is not None and len(fs):
            out["first_seen_line_primary"] = clv_stats(
                fs.assign(dk_spread=fs.first_seen_spread, proj_primary=fs.proj_primary_first_seen),
                "proj_primary")
        n = prim["games_edge"]
        if n < BARS["min_games"]:
            out["status"] = f"IN PROGRESS: {n}/{BARS['min_games']} qualifying games; $0"
        else:
            ok = (prim["toward_share_pct"] >= BARS["toward_share_pct"]
                  and prim["avg_move_toward_model"] > BARS["avg_move_pts"])
            out["status"] = ("PASSED" if ok else "FAILED") + f" at {n} games"
        # results (informational): ATS vs bet-time DK line once games are final
        games = pd.read_parquet(config.CLEAN / "games.parquet")[["game_id", "margin_home"]]
        r = with_close.merge(games, on="game_id").dropna(subset=["margin_home"])
        if len(r):
            e = r.proj_primary + r.dk_spread
            res = r.margin_home + r.dk_spread
            b = r[(e.abs() >= BARS["edge"]) & (res != 0)]
            win = (np.sign(res[b.index]) == np.sign(e[b.index]))
            out["ats_vs_bet_line"] = {"bets": int(len(b)), "wins": int(win.sum())}
    if write_doc:
        write_doc_block(out)
    return out


# ------------------------------------------------------------------ weekly log entry (Tim, 2026-10-12)
def scored_all(log_dir: Path = FORWARD) -> pd.DataFrame:
    """Same game set the score uses: DK snapshot lines first, CFBD fallback otherwise."""
    g_dk = dk_snapshot_games(log_dir)
    g_cf = scored_games(log_dir)
    if len(g_cf):
        g_cf = g_cf.assign(source="cfbd_fallback")
        if len(g_dk):
            g_cf = g_cf[~g_cf.game_id.isin(g_dk.game_id)]
    parts = [x for x in (g_dk, g_cf) if len(x)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _ats(x: pd.DataFrame, proj_col: str) -> tuple[int, int, int]:
    """(wins, losses, pushes) betting the model side at the bet-time DK spread, |edge| >= 1.5."""
    e = x[proj_col] + x.dk_spread
    q = x[e.abs() >= BARS["edge"]]
    res = q.margin_home + q.dk_spread
    push = int((res == 0).sum())
    win = int(((np.sign(res) == np.sign(e[q.index])) & (res != 0)).sum())
    return win, len(q) - win - push, push


def _fmt_rec(w, l, p):
    n = w + l
    return f"{w}-{l}" + (f"-{p}" if p else "") + (f" ({100 * w / n:.1f}%)" if n else "")


def weekly_entry(season: int, week: int, log_dir: Path = FORWARD) -> str:
    g = scored_all(log_dir)
    games = pd.read_parquet(config.CLEAN / "games.parquet")[["game_id", "margin_home"]]
    if len(g):
        g = g.merge(games, on="game_id", how="left")
    wk = g[(g.week == week)] if len(g) else g
    todate = g[(g.week >= BARS["first_week"]) & (g.week <= week)] if len(g) else g
    lines = [f"### Week {week} ({season}), graded {datetime.now(timezone.utc):%Y-%m-%d}"]
    for label, x in (("This week", wk), ("To date (weeks 4+)", todate)):
        if x is None or x.empty:
            lines.append(f"- **{label}:** no logged games.")
            continue
        wc = x.dropna(subset=["close_spread"])
        prim, ronly = clv_stats(wc, "proj_primary"), clv_stats(wc, "proj_ratings_only")
        gr = wc.dropna(subset=["margin_home"])
        lines.append(
            f"- **{label}:** {len(x)} games logged, {len(wc)} with a DK close, "
            f"{prim['games_edge']} at |edge| >= 1.5"
            + (f" ({prim['games_edge']}/{BARS['min_games']} toward the bar)" if label.startswith("To") else "")
            + f". CLV toward model: **{prim['toward_share_pct']:.1f}%** of {prim['moves']} moves, "
            f"avg move {prim['avg_move_toward_model']:+.2f} pts (ratings-only {ronly['toward_share_pct']:.1f}%, "
            f"{ronly['avg_move_toward_model']:+.2f}). ATS vs bet-time line (|edge| >= 1.5): "
            f"**{_fmt_rec(*_ats(gr, 'proj_primary'))}**, ratings-only {_fmt_rec(*_ats(gr, 'proj_ratings_only'))}."
            .replace("nan%", "n/a").replace("+nan", "n/a"))
    # rung log (shape bar sample), to date
    from engine.cfb.lines import ladder_edge as le
    p = le.grade(season)
    s = le.bar_sample(p) if len(p) else p
    lift = le.clustered_lift(s) if len(s) else None
    if lift:
        lines.append(
            f"- **Rung log (shape-bar sample, to date):** {lift['games']} graded games / {lift['rungs']} rungs; "
            f"hit {lift['hit_%']:.1f}% vs DK no-vig {lift['dk_novig_%']:.1f}% "
            f"(**lift {lift['lift_pp']:+.1f} pp**, 95% CI {lift['ci95_lo']:+.1f} to {lift['ci95_hi']:+.1f}); "
            f"break-even at posted prices {lift['breakeven_at_price_%']:.1f}%; "
            f"**EV at posted price: predicted {lift['pred_ev_shape_per_unit']:+.3f}, realized "
            f"{lift['realized_units_per_rung']:+.3f} units/rung** "
            f"(CI {lift['units_ci95_lo']:+.3f} to {lift['units_ci95_hi']:+.3f}). "
            f"{lift['games']}/{le.BAR['min_games']} toward the bar.")
    else:
        lines.append("- **Rung log:** no graded bar-sample rungs yet.")
    return "\n".join(lines) + "\n"


def append_weekly(season: int, week: int, dry_run: bool = False, force: bool = False) -> str:
    entry = weekly_entry(season, week)
    if dry_run or not DOC.exists():
        return entry
    doc = DOC.read_text(encoding="utf-8")
    tag = f"### Week {week} ({season}),"
    if tag in doc and not force:
        return f"(week {week} already logged; use --force to add another entry)\n"
    head, anchor = "## Weekly log", "## Current score"
    if head not in doc:
        doc = doc.replace(anchor, f"{head}\n\nAppended after each week grades by "
                                  f"`python -m engine.cfb.model.forward weekly --week N`. "
                                  f"Informational; the bars above decide.\n\n{anchor}")
    doc = doc.replace(anchor, entry + "\n" + anchor)
    DOC.write_text(doc, encoding="utf-8")
    return entry


def write_doc_block(out: dict) -> None:
    if not DOC.exists():
        return
    doc = DOC.read_text(encoding="utf-8")
    b, e = "<!-- AUTO:SCORE:BEGIN -->", "<!-- AUTO:SCORE:END -->"
    body = (f"_Scored {out['scored_at']} by `python -m engine.cfb.model.forward score`._\n\n"
            f"**Status: {out['status']}**\n\n```json\n{json.dumps(out, indent=2, default=str)}\n```")
    if b in doc and e in doc:
        doc = doc[:doc.index(b)] + f"{b}\n{body}\n{e}" + doc[doc.index(e) + len(e):]
        DOC.write_text(doc, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    cc = sub.add_parser("capture-close", help="log current DK lines for games not yet started")
    cc.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    cc.add_argument("--week", type=int, required=True)
    cc.add_argument("--no-fetch", action="store_true", help="use the cached response (testing)")
    cc.add_argument("--log-dir", type=Path, default=FORWARD)
    wk = sub.add_parser("weekly", help="append a dated weekly entry to FORWARD_TEST.md")
    wk.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    wk.add_argument("--week", type=int, required=True)
    wk.add_argument("--dry-run", action="store_true")
    wk.add_argument("--force", action="store_true")
    sc = sub.add_parser("score", help="score the forward test against the pre-registered bars")
    sc.add_argument("--log-dir", type=Path, default=FORWARD)
    a = ap.parse_args(argv)
    if a.cmd == "weekly":
        print(append_weekly(a.season, a.week, dry_run=a.dry_run, force=a.force))
        return 0
    if a.cmd == "capture-close":
        capture_close(a.season, a.week, fetch=not a.no_fetch, log_dir=a.log_dir)
    else:
        out = score(a.log_dir, write_doc=a.log_dir == FORWARD)
        print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
