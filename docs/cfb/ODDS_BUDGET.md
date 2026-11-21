# Odds API credit plan: CFB DraftKings capture (Phase 4 §7)

Prepared 2026-10-12, **before** the CFB schedule is enabled. No CFB credits spent so far.

## Plan and current use (verified from live response headers, 2026-10-12 11:00 UTC)

| Item | Value | Source |
|---|---|---|
| Monthly plan | **5,000,000 credits** (used + remaining) | `x-requests-used` 1,258 + `x-requests-remaining` 4,998,742 |
| Used this cycle | **1,258** (all NFL) | header; matches `automation/lines/odds_usage.csv` |
| Cycle start | about Oct 2 (the upgrade from the 20K plan, seen in the NFL ledger) | ledger: 19,429 → 4,999,804 on 10/02 |
| Next reset | about Nov 2 (monthly on the subscription date; verify in the account) | assumption |

## Verified costs (v4 docs + headers)

| Call | Cost |
|---|---|
| `/sports`, `/events` | free |
| Bulk `/sports/americanfootball_ncaaf/odds`, `bookmakers=draftkings`, markets spreads+totals+h2h | **3 per snapshot** (1 per market; ≤10 bookmakers count as 1 region). Covers every listed game. |
| Per-event `/events/{id}/odds`, `alternate_spreads`, DK | **1 per game**, only when DK returns the market (empty responses are free) |

## NFL projected weekly use

| | Credits |
|---|---|
| Actual, 2026 weeks 3 / 4 / 5 | 462 / 714 / 810 |
| Hard cap (NFL's own weekly guard, `ODDS_WEEKLY_BUDGET`) | 3,000 / week |
| Projected rest of season (cap-bound worst case) | ≤ 3,000 / week ≈ 13,000 / month |

## CFB projected weekly use (about 60 FBS games a week)

| Snapshot | Slots/week | Main | Ladders (recommended: all FBS games) | Ladders (brief minimum: targets only, cap 30) |
|---|---|---|---|---|
| Open watch: Sun 6pm, Sun 10pm, Mon 9am | 3 | 9 | first sighting of each **target** game: ~15-25 | ~15-25 |
| Bet window: Tue 10am, Wed 10am | 2 | 6 | all FBS: ~120 | targets ≤ 60 |
| Late: Fri 10am | 1 | 3 | none | none |
| Close: Sat 11am, 3pm, 7pm | 3 | 9 | last before each game, all FBS: ~55 | targets: ~20 |
| Close: Tue-Fri 6pm (only if games kick off; otherwise 0 credits) | ~2 | 6 | midweek games: ~5 | ~3 |
| **Total / week** | | **33** | **~200** | **~100** |
| **CFB total** | | | **~235 / week ≈ 1,000 / month** | **~135 / week ≈ 600 / month** |

## Headroom

| | Per month |
|---|---|
| Plan | 5,000,000 |
| NFL worst case (cap-bound) | ~13,000 |
| CFB recommended | ~1,000 (hard cap 3,000 per cycle in the workflow) |
| **Total worst case** | **~16,000 = 0.3% of plan** |
| 85% stop line | 4,250,000 |

**Verdict: fits with roughly 99.7% headroom.** The 85% stop rule isn't close.

## Guards (built in)

- **Separate ledger:** `data/cfb/lines/odds_usage_cfb.csv`. NFL's weekly budget sums
  `automation/lines/odds_usage.csv`, so CFB rows never count against the NFL weekly guard.
- **NFL reserve:** CFB refuses any paid call that would leave < **100,000** credits.
- **CFB cycle cap:** **3,000** credits per quota cycle (about 3× the plan); over that, CFB stops.
- **Ladder cap:** 70 games per snapshot.
- **Idle close slots** (Tue-Fri 6pm) make no paid call when nothing kicks off in the next 8 hours.
- **Own GitHub concurrency group** (`cfb-lines`), so a queued CFB run can never displace a
  pending NFL run in `data-main`. Pushes retry with a rebase.

## Recommendation

Approve the **all-FBS-games ladders** variant (~1,000 credits a month). Section 5's
shape-edge test doesn't depend on our projection. Laddering only the games where we
disagree with the line (the targets) would give a biased sample, and the extra cost is
about 0.01% of the plan. The cheaper targets-only variant (~600 a month) is one flag away:
`--ladders targets` on the Tue/Wed slots.

## Phase 5C extension: alternate totals + alternate team totals (APPROVED 2026-10-12: option A)

**Verified with one test call** (Georgia Southern @ Old Dominion, 2026-10-12 13:03 UTC):
`markets=alternate_totals,team_totals,alternate_team_totals`, DK, per-event endpoint →
`x-requests-last: 2`.

- DK offers **`alternate_totals`** (84 outcomes, 27.5-69.5) and **`alternate_team_totals`**
  (84 outcomes, 11.5-34.5 per team).
- DK has **no separate `team_totals`** market for NCAAF, so it isn't charged; the alt team
  ladder contains the main team total.

Asked for in the same per-game call as `alternate_spreads`, the extras add **+2 credits per
laddered game** and no extra requests. The code is in place but off: `CFB_EXTRA_MARKETS` is
unset in `cfb_lines.yml`.

| Option | Which ladder calls carry the extras | Extra / week | CFB total / week | CFB / month |
|---|---|---|---|---|
| **A (recommended): all ladder calls** | open-watch first sighting, Tue, Wed, last-before-close | ~+400 | ~635 | ~2,750 |
| B: bet-time + close only | Tue 10 AM + last-before-close | ~+230 | ~465 | ~2,000 |
| Current (spreads only) | n/a | 0 | ~235 | ~1,000 |

Option A means the **CFB cycle cap rises from 3,000 to 6,000** (it would bind at ~2,750).
Worst case total with NFL (~13,000 a month) stays **< 0.4% of the 5,000,000 plan**. The
100,000-credit NFL reserve and the separate CFB ledger are unchanged.

**Approved by Tim, 2026-10-12: option A.** `cfb_lines.yml` sets
`CFB_EXTRA_MARKETS=alternate_totals,alternate_team_totals` and `CFB_ODDS_CYCLE_CAP=6000`.
New rows go to `data/cfb/lines/snapshots/dk_alt_totals_<season>_wk<NN>.csv`.

## Free tier (Tim, 2026-11-21)

The paid key was deactivated about 2026-11-01. The new free key has about 500 credits/month, shared by NFL and CFB.
Switches live in `engine/core/odds_budget.json`; `engine/core/odds_budget.py` enforces them.

- **Hard cap:** 450 credits per month across every caller of the key: NFL `fetch_lines.py`, `engine/collector.py` and CFB `capture.py`. Every paid call is checked first against the key's own `x-requests-used` counter, using the previous response's headers. A call that would pass 450, or overdraw what remains, stops before it is made. A run with no quota headers yet makes no paid call.
- **CFB:** DK main lines only (spreads, totals, h2h; 3 credits a snapshot), in four slots:
  - `tue10`, the bet line
  - `sat11`, `sat15` and `sat19`, the closes

  Ladders, alt totals, the open-watch slots, `wed10`, `fri10` and the weekday closes are off. A dispatch of an off slot spends nothing. Weekday games fall back to CFBD's DK close. Expected spend is about 12 credits a week, roughly 50 a month.
- **NFL:** automatic pulls are paused. The `refresh-odds` and `sun-snapshot` schedules are commented out. `fetch_lines.py` and the collector refuse to pull unless `NFL_ODDS_MANUAL=1` is set, and that path is still capped. `card.yml` builds from pastes in `automation/lines/raw/w<N>/`.
- **Forward test:** the ladder (rung log / shape bar) and floor-card tracks are paused, and each weekly entry says so. The spread CLV/ATS forward test continues on main lines.
