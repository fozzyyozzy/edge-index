"""One weekly command: refresh data, project the week, draft the card (Tim, 2026-10-23).

    python -m engine.cfb.weekly --week 8 [--season 2026] [--snapshot tue10] [--publish-at ISO]

Runs, stopping at the first failure:
  1. engine.cfb.update_week         CFBD refresh (games, lines, stats, new PBP; <= 10 calls)
  2. engine.cfb.model.project_week  as-of week-N ratings -> projections, capture targets, forward log
  3. engine.cfb.lines.ladder_edge   rung log: this week's bet-time ladder (once per week)
  4. engine.cfb.cards.card          DRAFT card from the Tue bet snapshot (publishing stays a separate,
                                    explicit `card --publish` after Tim's OK)
"""
from __future__ import annotations
import argparse

from engine.cfb import config, update_week
from engine.cfb.cards import card
from engine.cfb.lines import ladder_edge
from engine.cfb.model import project_week


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--snapshot", default="tue10")
    ap.add_argument("--publish-at")
    a = ap.parse_args(argv)
    sw = ["--season", str(a.season), "--week", str(a.week)]
    steps = [("update_week", update_week.main, ["--season", str(a.season)]),
             ("project_week", project_week.main, sw),
             ("rung log (ladder_edge)", lambda _: ladder_edge.main(a.season), []),
             ("card (draft)", card.main, sw + ["--snapshot", a.snapshot]
              + (["--publish-at", a.publish_at] if a.publish_at else []))]
    for name, fn, args in steps:
        print(f"\n=== {name} ===", flush=True)
        rc = fn(args)
        if rc:
            print(f"{name} failed (exit {rc}); stopping")
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
