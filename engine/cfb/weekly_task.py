"""Unattended Tuesday run of engine.cfb.weekly (Tim, 2026-10-23). Scheduled Tue 10:20 AM ET by
agent/register_cfb_weekly_task.ps1 (runs whether signed in or not).

    python -m engine.cfb.weekly_task             # what the task runs
    python -m engine.cfb.weekly_task --no-push   # everything except the commit/push
    python -m engine.cfb.weekly_task --dry-run   # sync + week detection only (no weekly, no commit)

1. Sync: fetch origin and wait (up to --wait-min, default 40) until this Tuesday's tue10 bet snapshot
   is on origin (served_slots.txt has <date>:tue10), then pull it: stash, pull --rebase, stash pop,
   the same way it is done by hand. SAFETY: if any incoming file is one you have uncommitted changes in
   (or an untracked file it would add), the pull is skipped and logged, so the stash pop can never
   conflict with your work.
2. python -m engine.cfb.weekly --week <current>: update_week, project_week (forward log), DRAFT card.
   Current week = the earliest regular-season week of this season with a game not yet kicked off.
   Publishing stays manual (card --publish).
3. Commit ONLY targets_<season>_wk<NN>.csv, data/cfb/forward/projections_log.csv and the rung log
   data/cfb/lines/paper_rungs_<season>.csv, then push with
   the same stash / pull --rebase / pop (same safety check; on a skip the commit stays local).
Everything is appended to %USERPROFILE%\\.edge-index\\weekly.log.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from engine.cfb import config

ROOT = Path(__file__).resolve().parents[2]
LOG = Path(os.environ.get("USERPROFILE") or Path.home()) / ".edge-index" / "weekly.log"
ET = ZoneInfo("America/New_York")
SERVED = "data/cfb/lines/served_slots.txt"
FWD_LOG = "data/cfb/forward/projections_log.csv"
COAUTHOR = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for x in filter(None, self.streams):
            x.write(s)
            x.flush()

    def flush(self):
        for x in filter(None, self.streams):
            x.flush()


def say(msg: str) -> None:
    print(f"[{datetime.now(ET):%Y-%m-%d %H:%M:%S} ET] {msg}", flush=True)


def git(*args, check=True) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {out}")
    return out


def dirty_paths() -> set[str]:
    out = set()
    for ln in git("status", "--porcelain", "--untracked-files=all").splitlines():
        p = ln[3:].strip().strip('"')
        out.add(p.split(" -> ")[-1])
    return out


def sync(ignore: set[str] = frozenset(), allow_local: tuple = ()) -> bool:
    """stash / pull --rebase / pop, only if no incoming file collides with local uncommitted work
    (paths in `ignore` are ones this job just committed). True if in sync with origin afterwards."""
    git("fetch", "-q", "origin")
    local = [c for c in git("rev-list", "origin/main..HEAD").split() if c not in allow_local]
    if local:
        say(f"SYNC SKIPPED: local main has {len(local)} commit(s) not on origin (yours); "
            "not rebasing or pushing them")
        return False
    incoming = set(git("diff", "--name-only", "HEAD...origin/main").splitlines())
    clash = (incoming & dirty_paths()) - set(ignore)
    if clash:
        say(f"SYNC SKIPPED: incoming commits touch files with uncommitted local changes: {sorted(clash)[:8]}")
        return False
    if not incoming and not git("rev-list", "HEAD..origin/main"):
        return True
    stashed = "No local changes" not in git("stash", "push", "-q", "--include-untracked", "-m", "weekly_task", check=False)
    try:
        git("pull", "-q", "--rebase", "origin", "main")
    finally:
        if stashed:
            git("stash", "pop", "-q")
    return True


def wait_for_bet_snapshot(wait_min: float) -> bool:
    today = datetime.now(ET)
    tag = f"{today:%Y-%m-%d}:tue10"
    if today.weekday() != 1:
        say(f"not a Tuesday: not waiting for a bet snapshot")
        return True
    deadline = time.time() + wait_min * 60
    while True:
        git("fetch", "-q", "origin")
        if tag in git("show", f"origin/main:{SERVED}", check=False).split():
            say(f"{tag} is on origin")
            return True
        if time.time() > deadline:
            say(f"WARNING: {tag} not on origin after {wait_min:.0f} min; running anyway (card will fail without it)")
            return False
        time.sleep(120)


def current_week(season: int) -> int:
    g = pd.read_parquet(config.CLEAN / "games.parquet", columns=["season", "week", "season_type", "kickoff_utc"])
    g = g[(g.season == season) & (g.season_type == "regular")]
    ko = pd.to_datetime(g.kickoff_utc, utc=True)
    up = g[ko > pd.Timestamp.now(tz="UTC")]
    if up.empty:
        raise SystemExit(f"no upcoming regular-season {season} games")
    return int(up.week.min())


def commit_and_push(season: int, week: int) -> None:
    targets = f"data/cfb/lines/targets/targets_{season}_wk{week:02d}.csv"
    rungs = f"data/cfb/lines/paper_rungs_{season}.csv"
    paths = [p for p in (targets, FWD_LOG, rungs) if (ROOT / p).exists()]
    git("add", "--", *paths)
    if not git("diff", "--cached", "--name-only", "--", *paths):
        say("nothing new to commit (targets / forward log unchanged)")
        return
    git("commit", "-q", "-m", f"cfb week {week} targets + forward-log projections (weekly task)\n\n{COAUTHOR}",
        "--", *paths)
    say(f"committed {git('log', '--oneline', '-1')}")
    ours = (git("rev-parse", "HEAD"),)
    for attempt in range(3):
        if not sync(ignore=set(paths), allow_local=ours):
            say("PUSH SKIPPED: commit left local (see the sync line above)")
            return
        ours = (git("rev-parse", "HEAD"),)                    # the rebase rewrites our commit's sha
        r = subprocess.run(["git", "push", "-q", "origin", "main"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            say("pushed")
            return
        say(f"push attempt {attempt + 1} failed: {(r.stdout + r.stderr).strip()[:300]}")
        time.sleep(30)
    say("PUSH FAILED after 3 attempts: commit left local")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--week", type=int, help="default: current week")
    ap.add_argument("--wait-min", type=float, default=40)
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="sync + current week only; no weekly, no commit")
    a = ap.parse_args(argv)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        sys.stdout = sys.stderr = Tee(sys.__stdout__, f)
        say(f"===== weekly task start ({datetime.now(timezone.utc).isoformat(timespec='seconds')}) =====")
        rc = 1
        try:
            wait_for_bet_snapshot(a.wait_min)
            sync()
            week = a.week or current_week(a.season)
            say(f"running engine.cfb.weekly --season {a.season} --week {week}")
            if a.dry_run:
                say(f"DRY RUN: would commit targets_{a.season}_wk{week:02d}.csv + {FWD_LOG}; stopping")
                say("===== weekly task end =====")
                sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
                return 0
            from engine.cfb import weekly
            try:
                rc = weekly.main(["--season", str(a.season), "--week", str(week)])
            except SystemExit as e:                          # a step that exits (e.g. no bet snapshot)
                rc = e.code if isinstance(e.code, int) else 1
                say(f"weekly stopped: {e}")
            say(f"weekly exit {rc}")
            if not a.no_push:
                commit_and_push(a.season, week)              # targets / forward log, even if the card failed
        except Exception as e:                               # noqa: BLE001 - log everything, never crash silently
            say(f"ERROR: {type(e).__name__}: {e}")
            rc = 1
        say("===== weekly task end =====")
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
