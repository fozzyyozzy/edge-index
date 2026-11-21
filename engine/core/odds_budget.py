"""Shared Odds API credit cap for NFL + CFB (Tim, 2026-11-21: free key, ~500 credits/month).

Every PAID call (NFL automation/pipeline/fetch_lines.py, CFB engine/cfb/lines/capture.py) calls
check() first with the quota headers from the previous response on the same key. The free /events
call made at the start of each run supplies the first headers. x-requests-used is the key's own
monthly counter, so it covers NFL and CFB together, and every caller of the key.

    used + planned  > monthly_cap (odds_budget.json, 450)  -> stop
    remaining - planned < 0                                 -> stop
    no quota headers seen yet                               -> stop (never call blind)

A stop raises BudgetStop (a SystemExit with the reason), so the run ends before the call is made.
"""
from __future__ import annotations
import json
from pathlib import Path

CONFIG = Path(__file__).with_name("odds_budget.json")


class BudgetStop(SystemExit):
    pass


def cfg() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def check(used, remaining, planned: int, who: str) -> None:
    """Raise BudgetStop unless a paid call costing up to `planned` credits fits under the monthly cap."""
    cap = int(cfg()["monthly_cap"])
    used, remaining = _int(used), _int(remaining)
    if used is None:
        raise BudgetStop(f"STOP ({who}): no x-requests-used header seen yet; refusing a blind paid call")
    if used + planned > cap:
        raise BudgetStop(f"STOP ({who}): {used} credits used this month + {planned} planned would pass the "
                         f"{cap}-credit monthly cap (engine/core/odds_budget.json)")
    if remaining is not None and remaining - planned < 0:
        raise BudgetStop(f"STOP ({who}): {remaining} credits remaining < {planned} planned")
