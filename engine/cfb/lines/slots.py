"""CFB DK capture schedule (ET) and the slot guard used by .github/workflows/cfb_lines.yml.

    python -m engine.cfb.lines.slots --which        # prints "<slot> <capture args>" or nothing
    python -m engine.cfb.lines.slots --mark-served SLOT

Cron is UTC and ET shifts with DST, so every slot has an EDT and an EST cron. The guard
serves a slot only when the current ET time is within WINDOW_MIN after its start and it
isn't recorded in data/cfb/lines/served_slots.txt yet; the twin cron then finds it served.
A close slot with no kickoffs in its window makes no paid call (capture.py checks).
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SERVED = Path(__file__).resolve().parents[3] / "data" / "cfb" / "lines" / "served_slots.txt"
WINDOW_MIN = 150

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


def which(now: datetime | None = None) -> tuple[str, str] | None:
    now = (now or datetime.now(ET)).astimezone(ET)
    done = served()
    for name, (wd, hr, args) in SLOTS.items():
        start = now.replace(hour=hr, minute=0, second=0, microsecond=0)
        start -= timedelta(days=(now.weekday() - wd) % 7)
        tag = f"{start:%Y-%m-%d}:{name}"
        if start <= now <= start + timedelta(minutes=WINDOW_MIN) and tag not in done:
            return tag, args
    return None


def mark(tag: str) -> None:
    SERVED.parent.mkdir(parents=True, exist_ok=True)
    with open(SERVED, "a") as f:
        f.write(tag + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", action="store_true")
    ap.add_argument("--mark-served")
    a = ap.parse_args()
    if a.which:
        w = which()
        print(f"{w[0]} {w[1]}" if w else "")
    elif a.mark_served:
        mark(a.mark_served)
