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
