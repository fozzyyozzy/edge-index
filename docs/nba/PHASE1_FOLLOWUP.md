# NBA Floor Lines — Phase 1 Follow-up (before Phase 2)

**Date:** 2026-10-21. These are Tim's six follow-up items. **No paid Odds API calls were made for this follow-up**; the usage log's last row is unchanged at 12,513 used. No NFL changes.

## 1. Steals and blocks, and combo columns

- **New columns:** `stl` and `blk` are now in `data/nba/player_games.parquet`, parsed from the same ESPN box as the other stats.
- **Cross-check:** both were checked against nba_api the same way as the other stats. Matched rows: 79,336.

| Stat | Exact | Within ±1 | Mismatches | Direction |
|---|---|---|---|---|
| stl | 99.986% | 100% | 11 | 6 low / 5 high: no bias |
| blk | 99.995% | 100% | 4 | 2 / 2: no bias |
| (for reference) pts / fg3m | 100% | 100% | 0 | |
| reb / ast | 99.99% / 99.995% | 100% | 8 / 4 | no bias |
| minutes | 99.78% | 100% | 174 | ESPN +1 (rounding) |

- **By season, stl / blk:**
  - 2023-24: 99.96 / 99.996
  - 2024-25: 99.996 / 99.99
  - 2025-26: 100 / 99.996
- **Combos:** `pr`, `pa`, `ra` and `pra` were already there.
- **New data-gate test,** `test_combo_columns_equal_component_sums`: every row satisfies P+R, P+A, R+A and PRA equal to their parts.
- **New test,** `test_steals_blocks_present_and_sane`: no nulls, plausible per-game and per-team ranges. The parser fixture now also pins stl/blk (Desmond Bane: 4 stl, 3 blk, the same as nba_api).
- **Tests:** 28 NBA tests pass.

## 2. Spend rule

Any Odds API pull over **2,000 credits** needs your approval first, with a dry-run estimate.

- **In code:** `engine/nba/hist_lines.py` now refuses any run planned over 2,000 credits unless it's given `--approved-credits N` (N ≥ the planned cost). `--dry-run` prints the plan.
- **Props pull:** the new `engine/nba/hist_props.py` has **no pull path at all**, only the estimate.
- **Memory:** the rule is saved in my memory for future sessions. I'll treat "DRY RUN ONLY" as zero paid calls, not even small coverage probes.

## 3. Dry run: historical DK player-prop prices, 2025-26

**Plan:**
- One historical event-odds call per game, 10 minutes before tip, DK only (1 region).
- 20 market keys: main + alternate for points, rebounds, assists, threes, P+R, P+A, R+A, PRA, steals and blocks.
- Event ids for all 1,230 games come from the snapshots already cached in Phase 1, so **no paid id lookups** are needed.

**Pricing** (Odds API docs, read today):
- Historical event odds cost **10 × unique markets *returned* × regions**.
- Empty responses are free.
- Prop/additional-market history exists from 2023-05-03, at 5-minute snapshots.

| Scenario | Per game | 2025-26 total (1,230 games) |
|---|---|---|
| All 20 keys return data | 200 | **246,000** |
| Only the 9 keys DK returned for every game in Phase 0 | 90 | **110,700** |
| Event-id lookups | — | 0 |

So the real cost is between **~111k and 246k credits**: about 2–5% of the ~4.99M remaining. That's a one-off.

| Month | Games |
|---|---|
| Oct | 80 |
| Nov | 219 |
| Dec | 197 |
| Jan | 233 |
| Feb | 166 |
| Mar | 239 |
| Apr | 96 |

**Coverage: not measurable without paying.**
- **Dates/games:** all 1,230 games over 164 dates have an event id and a DK pregame line in the snapshots. Every game existed at DK.
- **Markets confirmed live** (Phase 0, 13 of 13 games, current season): points, rebounds, assists, PRA (main + alt) and threes (alt).
- **Never checked:**
  - `player_threes`
  - P+R, P+A and R+A (main and alt)
  - steals and blocks (main and alt)
- **Unknowable without paying:** whether DK posted the never-checked markets in 2025-26, and how deep the historical alt ladders go.

**Options:**
- **Coverage probe:** sample 1 game per month (7 games). That's at most 7 × 200 = **1,400 credits**. It's under 2,000, but you said "do not pull", so it needs your go-ahead. It would tell us which of the 20 keys DK carried and how many rungs, and pin the full-season cost to within about ±10%.
- **Full pull:** 111k–246k credits. Over 2,000, so it needs your explicit approval after the probe.
  - If you approve it, the market-blend bar has to be added to PREREG **before** any price is read.

## 4. Grading rule: UNGRADEABLE

**Rule:** a leg whose player can't be matched to a box score is graded **UNGRADEABLE**, never WIN/LOSS, and logged with the reason.
- **Causes:** no crosswalk match, ESPN row without an athlete id (like Olbrich), or a missing box.
- **Counting:** it's excluded from hit-rate and calibration counts, but its count is always reported.
- **VOID** stays separate: the player matched but didn't play.

Where it's recorded:
- `PREREG.md` §7, so it's registered with the bars
- the project memory notes

The grader is Phase 3 code, so it's not implemented yet.

## 5. Commit on `nba-phase1`

See the closing note: gitleaks result, then commit status. The commit holds:
- Phase 0 and 1 code (`engine/nba/`)
- tests and fixtures
- `data/nba/`, except the gitignored `raw/`
- `docs/nba/`: brief, Phase 0 report, Phase 1 report, this file, and the shared-code TODO
- the one-line `tests.yml` change

It's built in a separate worktree, so your main checkout and its uncommitted MLB/CFB files are untouched. It does **not** include `PREREG.md`.

## 6. PREREG.md drafted (uncommitted)

`docs/nba/PREREG.md` is written and **not committed**. No holdout has been scored.
- **Bars** come from the brief and apply to each market: slope 0.90–1.10; 70–90 bins within ±3 pts at n ≥ 300; Brier beats last-10 clear rate; nothing more than 5 pts hot from 75% up. A failed market is dropped, not tuned.
- **Markets:** all 10 are listed. Steals and blocks are shadow-only for the first forward month.

These are my choices for you to confirm or change. They're marked **[TIM]** in the file:
1. **Eligibility:** ≥ 8 prior games, plus trailing-10 minutes ≥ 20 as a "DK would post him" proxy.
2. **Slope set:** calibration slope measured on p 0.50–0.97 rather than only the floor band (stability).
3. **B0 sample bar:** a market needs at least 2 of the four 70–90 bins at n ≥ 300, or it's INSUFFICIENT, which counts as not passed.
4. **Threes role:** the brief's default was shadow-only, but your list didn't mark it. It's drafted as a v1 candidate. Confirm which.

**Stopping here for Tim.**
