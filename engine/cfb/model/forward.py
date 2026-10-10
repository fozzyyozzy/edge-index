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


def score(log_dir: Path = FORWARD, write_doc: bool = True) -> dict:
    g = scored_games(log_dir)
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
                    "primary": prim, "ratings_only": ronly})
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
    sc = sub.add_parser("score", help="score the forward test against the pre-registered bars")
    sc.add_argument("--log-dir", type=Path, default=FORWARD)
    a = ap.parse_args(argv)
    if a.cmd == "capture-close":
        capture_close(a.season, a.week, fetch=not a.no_fetch, log_dir=a.log_dir)
    else:
        out = score(a.log_dir, write_doc=a.log_dir == FORWARD)
        print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
