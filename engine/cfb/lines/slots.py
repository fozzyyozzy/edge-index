"""CFB DK capture schedule (ET) and the slot guard used by .github/workflows/cfb_lines.yml.

    python -m engine.cfb.lines.slots --which              # "<tag> <lag_min> <capture args>" or nothing
    python -m engine.cfb.lines.slots --resolve tue10      # named slot (any lag); nothing if already served
    python -m engine.cfb.lines.slots --mark-served TAG

Cron is UTC and ET shifts with DST, so every slot has EDT and EST crons, plus a BACKUP cron 30
minutes later: GitHub delays or drops scheduled runs (the week-7 Tue 10 AM slot never fired, and
Monday's 9 AM fired ~8 h late). A scheduled run is tagged with its INTENDED slot if it starts within
GRACE_MIN (90) minutes after the slot time and that slot isn't served yet; the twin/backup cron then
skips. Every capture records the actual capture time and its lag behind the slot (snapshot columns
`slot`, `slot_lag_min`). A missed slot is recovered with the workflow_dispatch `slot` input, which
runs that slot's own capture args and tags it with the most recent occurrence of the slot.
A close slot with no kickoffs in its window makes no paid call (capture.py checks).
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SERVED = Path(__file__).resolve().parents[3] / "data" / "cfb" / "lines" / "served_slots.txt"
GRACE_MIN = 90
# Tim, 2026-10-19: CLOSE slots accept any late run (capped at 24 h): capture.py writes only games
# that haven't kicked off, so every row is still a valid pregame close after the bet snapshot.
CLOSE_GRACE_MIN = 24 * 60

# name: (weekday 0=Mon, hour ET, capture args)
SLOTS = {
    "sun18": (6, 18, "--label open_watch --ladders first_seen"),
    "sun22": (6, 22, "--label open_watch --ladders first_seen"),
    "mon09": (0, 9, "--label open_watch --ladders first_seen"),
    "tue10": (1, 10, "--label bet --ladders all"),          # forward-test bet-time default
    "wed10": (2, 10, "--label bet --ladders all"),
    "fri10": (4, 10, "--label late --ladders none"),
    "tue18": (1, 18, "--label close --ladders before_next --next-hours 8 --skip-if-idle"),
    "wed18": (2, 18, "--label close --ladders before_next --next-hours 8 --skip-if-idle"),
    "thu18": (3, 18, "--label close --ladders before_next --next-hours 8 --skip-if-idle"),
    "fri18": (4, 18, "--label close --ladders before_next --next-hours 8 --skip-if-idle"),
    "sat11": (5, 11, "--label close --ladders before_next --next-hours 4"),
    "sat15": (5, 15, "--label close --ladders before_next --next-hours 4"),
    "sat19": (5, 19, "--label close --ladders before_next --next-hours 14"),
}


def served() -> set[str]:
    return set(SERVED.read_text().split()) if SERVED.exists() else set()


def last_occurrence(name: str, now: datetime) -> datetime:
    wd, hr, _ = SLOTS[name]
    start = now.replace(hour=hr, minute=0, second=0, microsecond=0)
    start -= timedelta(days=(now.weekday() - wd) % 7)
    if start > now:
        start -= timedelta(days=7)
    return start


def which(now: datetime | None = None):
    """(tag, lag_min, args) for the most recent unserved slot within the grace window, else None."""
    now = (now or datetime.now(ET)).astimezone(ET)
    done = served()
    best = None
    for name, (_, _, args) in SLOTS.items():
        start = last_occurrence(name, now)
        lag = (now - start).total_seconds() / 60
        tag = f"{start:%Y-%m-%d}:{name}"
        grace = CLOSE_GRACE_MIN if "--label close" in args else GRACE_MIN
        if 0 <= lag <= grace and tag not in done and (best is None or lag < best[1]):
            best = (tag, round(lag), args)
    return best


def resolve(name: str, now: datetime | None = None):
    """Named slot (Windows trigger or manual recovery): tag with the most recent occurrence of `name`,
    any lag. None if that occurrence is already served, so a GitHub cron that got there first and the
    Windows trigger never both make a paid capture."""
    now = (now or datetime.now(ET)).astimezone(ET)
    start = last_occurrence(name, now)
    tag = f"{start:%Y-%m-%d}:{name}"
    if tag in served():
        return None
    return tag, round((now - start).total_seconds() / 60), SLOTS[name][2]


def mark(tag: str) -> None:
    SERVED.parent.mkdir(parents=True, exist_ok=True)
    with open(SERVED, "a") as f:
        f.write(tag + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", action="store_true")
    ap.add_argument("--resolve", choices=list(SLOTS))
    ap.add_argument("--mark-served")
    a = ap.parse_args()
    if a.which:
        w = which()
        print(f"{w[0]} {w[1]} {w[2]}" if w else "")
    elif a.resolve:
        t = resolve(a.resolve)
        print(f"{t[0]} {t[1]} {t[2]}" if t else "")
    elif a.mark_served:
        mark(a.mark_served)
