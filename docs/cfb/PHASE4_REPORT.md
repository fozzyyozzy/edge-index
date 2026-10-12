# CFB Phase 4 Report: DK Line Capture, Line Movement & Alt-Ladder Pricing

Brief: `docs/CFB_PHASE4_BRIEF.md`. Report dated 2026-10-12 (Monday of week 7). No Phase 2/3
parameters were retuned. All 7 model tests pass, plus 4 forward-scorer tests.

## 1. Is capture live?

**Yes.** `.github/workflows/cfb_lines.yml` was pushed on 2026-10-12 after you approved the
all-games plan (`docs/cfb/ODDS_BUDGET.md`). A manual Actions run verified the whole path:
it captured 59 games of DK main lines (spread, total, ML) and 59 alt-spread ladders (~42 rungs
per side), committed the snapshots plus `data/cfb/lines/odds_usage_cfb.csv`, and cost
**62 credits** (3 + 59).

- The NFL ledger `automation/lines/odds_usage.csv` is **untouched** (same hash before and
  after; its last commit is the NFL's own `3c7c21db`).
- **Snapshots so far:** one (manual, Mon 07:08 ET). The scheduled slots start with
  **Tue 10 AM ET** (bet window). Week 7's Sun/Mon open-watch slots had passed before the
  schedule was enabled, so week 7 has no open-watch snapshot; week 8's opens will.
- **Projected cost:** ~235 credits a week (≈1,000 a month) out of 5,000,000. The NFL reserve
  (100k) and the CFB cycle cap (3,000) are enforced in code.

## 2. Requested numbers, next to the DK-open result (edge ≥ 1.5 pts; frozen Phase 3 model, no refit)

CLV = share of line **moves** toward the model. Avg move = signed points toward the model,
averaged over all games including no-moves. ATS = record at the open, pushes excluded.

| Set | Line | QB | Games | CLV toward | Avg move | ATS bets | ATS win % | ATS 95% CI | ROI @ −110 |
|---|---|---|---|---|---|---|---|---|---|
| **2025 holdout** | Bovada open | on | 250 | 61.6% | +0.47 | 245 | 58.4% | 52.1-64.4 | +11.4% |
| **2025 holdout** | Bovada open | **off** | 192 | **57.4%** | +0.40 | 188 | **54.3%** | 47.1-61.2 | +3.6% |
| **2026 wks 4-6** (172 games, all of wk 6) | DK open (CFBD) | on | 63 | **84.9%** | +1.83 | 62 | **64.5%** | 52.1-75.3 | +23.2% |
| **2026 wks 4-6** | DK open (CFBD) | **off** | 51 | **84.4%** | +1.89 | 50 | **60.0%** | 46.2-72.4 | +14.6% |
| 2025 holdout, both books listed | **DK open** | on | 271 | **73.3%** | +1.61 | 269 | 58.0% | 52.0-63.7 | +10.7% |
| 2025 holdout, both books listed | **DK open** | off | 205 | **77.7%** | +1.99 | 203 | 54.7% | 47.8-61.4 | +4.4% |
| 2025 holdout, same games | Bovada open | on | 236 | 60.1% | +0.46 | 231 | 58.9% | 52.4-65.0 | +12.4% |
| 2025 holdout, same games | Bovada open | off | 178 | 57.1% | +0.44 | 174 | 56.3% | 48.9-63.5 | +7.5% |
| 2023-24 (tuning, in-sample k), both books | **DK open** | on | 574 | **73.2%** | +1.70 | 565 | 58.8% | 54.7-62.7 | +12.2% |
| 2023-24 (tuning), both books | **DK open** | off | 469 | 77.9% | +1.84 | 459 | 58.8% | 54.3-63.2 | +12.3% |
| 2023-24 (tuning), same games | Bovada open | on | 535 | 63.9% | +0.97 | 525 | 57.1% | 52.9-61.3 | +9.1% |
| **2023-25 full set**, both books | **DK open** | on | 845 | 73.2% | +1.67 | 834 | 58.5% | 55.1-61.8 | +11.7% |
| **2024-25 sensitivity (excl. 2023)** | **DK open** | on | 533 | **75.2%** | +2.15 | 529 | 59.4% | 55.1-63.5 | +13.3% |
| 2024-25 sensitivity (excl. 2023) | DK open | off | 433 | 77.8% | +2.32 | 429 | 57.3% | 52.6-61.9 | +9.5% |
| 2024-25 sensitivity, same games | Bovada open | on | 466 | 61.8% | +0.57 | 455 | 57.6% | 53.0-62.0 | +9.9% |

Notes on the table:
- **The 2025 QB-on row is recomputed** from today's rebuilt features: 61.6% on 250 games.
  The frozen Phase 3 holdout record (60.5% on 248) stands as the official number; the rebuild
  finds one fewer QB change. The QB-off rows match Phase 3 exactly.
- **2026 now covers all of week 6** (172 games), so it supersedes the midweek-only figures in
  the Phase 3 report.

## 3. The DK-open result (2023-25): the edge does NOT disappear against DK's open

Anchored on **DK's** open, the frozen model's CLV is **higher** than against Bovada's open:
73% vs 60-64% of moves, with a larger average move (+1.6-2.0 vs +0.5-1.0 points). ATS at the
open is about the same (~58%). So the edge isn't Bovada-specific. Caveats:

- **DK's CFBD "open" moves more:** |open − close| averages 1.96-2.29 points in 2024-25, vs
  1.34-1.40 for Bovada. DK's open equals its close only 15-20% of the time (Bovada: 14-16%).
  DK appears to open earlier or softer, which leaves more room for CLV. **But the open's
  timestamp is unknown in CFBD.** The 2026 snapshots will show when DK actually opens.
- **2023 DK data is odd:** its open equals its close 44% of the time, which looks like a
  late-captured "open" for part of that season. Per Tim (2026-10-12), it's kept. The 2024-25
  sensitivity rows without it show the same picture: 75.2% of moves toward the model on DK's
  open vs 73.2% for the full set.
- **2026 weeks 4-6 are still implausibly strong** (~85% CLV, corr ≈ 0.5) on 50-63 games.
  The forward test, on our own timestamps, is the real check.
- **Without QB, ATS is borderline everywhere** (CIs touch 50% in 2025); CLV holds at 57-78%.

## 4. DK's implied CFB ladder vs ours (59 ladders, one snapshot)

| | DK implied | Ours (Phase 3) |
|---|---|---|
| σ at the median total (49.5) | **15.8** | 15.0 |
| σ per 10 points of total | 0.43 | 0.58 |
| Key spikes 3 / 7 / 10 / 14 / 17 / 21 | 2.5 / 2.5 / 1.2 / 1.5 / 0.9 / 1.8 | 3.7 / 3.3 / 2.0 / 1.8 / 1.9 / 2.2 |

- **Reproduction error:** the fit misses DK's no-vig probabilities by **1.35 pp** on average
  (2,472 rungs). On price (rungs −1000..+1000) the median miss is **18¢**, p90 119¢ (long
  tails). DK's average ladder hold is **7.0%** per pair (main line ~4.5%).
- **DK widens σ with the size of the spread** (per-game σ corr +0.49 with |line|); ours has
  no line-size term. Centered at DK's own line, our probabilities run **above** DK's on rungs
  well above the line (+1.9 pp at 14+ points) and below on rungs well below it. In other
  words, we think big alt cushions cover more often than DK prices them. That's the
  hypothesis the shape bar tests.
- **One snapshot only.** The fit gets refit as the Tue/Wed/close ladders arrive.

## 5. Snapshot-to-snapshot movement

Only one snapshot so far, so there are no movement findings yet. The first scheduled bet,
close and open-watch snapshots run this week; week 8 gives the first full open → Tue → Wed
→ close series.

## Forward-test changes (pre-registered in `docs/cfb/FORWARD_TEST.md`, before anything was scored)

- **Forward test** started Mon 10/12 with week 7: 59 games logged on fresh ratings.
  **Amendment 1:** bet-time = DK Tue 10 AM snapshot (first-seen reported alongside), close =
  last pre-kickoff DK snapshot, CFBD lines as the fallback.
- **Ladder-shape bar:** 60 games, one rung per game per side (largest shape edge,
  getting-points rungs, −500..−150), lift ≥ +3 pp with a game-clustered CI excluding 0.
  $0 until passed.
- **Paper rung log** (`data/cfb/lines/paper_rungs_2026.csv`): 326 rows, 46 games so far
  (286 getting, 40 laying). Ungraded, so not a result yet.
- **EV at the posted price** (Tim, 2026-10-12) is now reported next to the no-vig lift, in
  the grading, this report and the weekly entries. **Early read (ungraded, our probabilities):**
  shape-qualified getting rungs average **+4.6 pp** over DK's no-vig probability, but **−0.004
  units** EV at DK's posted price. The ~7% ladder hold absorbs almost all of it, and only 27% of
  those rungs are +EV. A shape edge has to beat the hold, not just the no-vig line.
- **Weekly log:** `python -m engine.cfb.model.forward weekly --week N` appends a dated entry to
  `FORWARD_TEST.md` with games scored, CLV toward the model, ATS vs the bet-time line, and the
  rung log's lift and EV to date. Bars unchanged.

## Splits research (`docs/cfb/SPLITS_RESEARCH.md`)

**None viable for automation today.**
- **Action Network's terms forbid robots and commercial use.**
- **VSiN's DK splits** (5-minute updates) are a paid Pro feature with DraftKings-licensed data,
  and VSiN publishes no terms permitting automation.
- **Recommendation:** ask VSiN in writing about a licensed feed. Until then, manual reading only.

## Other changes this phase

- **`update_week` now rebuilds the model-play table** the ratings read. Before, ratings could
  silently miss the newly pulled week.
- **`project_week` guards on the plays the ratings actually use**, prefers DK snapshot lines
  (< 24 h old) over CFBD, and exports capture targets.

## Open questions for Tim

1. **The 2023 DK "open"** looks partly late-captured (44% equal to close). Exclude 2023 DK from
   the historical comparison?
2. **Ladder σ term:** DK scales σ with |line|; our Phase 3 fit found no |line| effect on
   outcomes. That disagreement *is* the shape bet. OK to leave our distribution frozen while
   the shape bar runs?
3. **VSiN:** do you want me to draft the licensing inquiry?

## Results (generated)

<!-- AUTO:REQUESTED:BEGIN -->
_2026 weeks 4-6 now include all of week 6 (172 completed FBS-vs-FBS games; the Phase 3 report had week 6 midweek games only)._

| set | edge >= | games | clv_toward_%_of_moves | avg_move_toward | ats_bets | ats_win_% | ats_ci95 | roi_%_-110 | corr |
|---|---|---|---|---|---|---|---|---|---|
| 2025 holdout (Bovada open) · QB on | 1.50 | 250 | 61.57 | 0.47 | 245 | 58.37 | 52.1-64.4 | 11.43 | 0.15 |
| 2025 holdout (Bovada open) · QB on | 3.00 | 90 | 60.26 | 0.53 | 90 | 62.22 | 51.9-71.5 | 18.79 | 0.15 |
| 2025 holdout (Bovada open) · QB on | 5.00 | 18 | 66.67 | 0.89 | 18 | 55.56 | 33.7-75.4 | 6.06 | 0.15 |
| 2025 holdout (Bovada open) · QB off | 1.50 | 192 | 57.40 | 0.40 | 188 | 54.26 | 47.1-61.2 | 3.58 | 0.12 |
| 2025 holdout (Bovada open) · QB off | 3.00 | 42 | 63.16 | 0.73 | 42 | 54.76 | 39.9-68.8 | 4.55 | 0.12 |
| 2025 holdout (Bovada open) · QB off | 5.00 | 2 | 100.00 | 1.75 | 2 | 0.00 | 0.0-65.8 | -100.00 | 0.12 |
| 2026 wks 4-6 (DK open) · QB on | 1.50 | 63 | 84.91 | 1.83 | 62 | 64.52 | 52.1-75.3 | 23.17 | 0.49 |
| 2026 wks 4-6 (DK open) · QB on | 3.00 | 19 | 86.67 | 1.97 | 19 | 73.68 | 51.2-88.2 | 40.67 | 0.49 |
| 2026 wks 4-6 (DK open) · QB on | 5.00 | 3 | 66.67 | 1.33 | 3 | 66.67 | 20.8-93.9 | 27.27 | 0.49 |
| 2026 wks 4-6 (DK open) · QB off | 1.50 | 51 | 84.44 | 1.89 | 50 | 60.00 | 46.2-72.4 | 14.55 | 0.51 |
| 2026 wks 4-6 (DK open) · QB off | 3.00 | 6 | 100.00 | 3.83 | 6 | 83.33 | 43.6-97.0 | 59.09 | 0.51 |
| 2026 wks 4-6 (DK open) · QB off | 5.00 | 1 | 100.00 | 3.00 | 1 | 100.00 | 20.7-100.0 | 90.91 | 0.51 |

<!-- AUTO:REQUESTED:END -->

<!-- AUTO:DKOPEN:BEGIN -->
_Generated by `python -m engine.cfb.lines.movement`. Frozen Phase 3 primary, no refit. 2023-2024 are tuning seasons (in-sample for k); 2025 is the held-out season; 2026 weeks 4-6 = all completed games to date._

### DK vs Bovada: open, close, movement (CFBD, FBS vs FBS)

| season | dk_games | dk_|open-close| | dk_open==close_% | both_books | bov_|open-close| | bov_open==close_% | dk_open==bov_close_% | dk_open==bov_open_% | |dk_open-bov_open| |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 705 | 1.00 | 44.40 | 703 | 1.74 | 10.53 | 14.94 | 26.32 | 1.03 |
| 2024 | 690 | 2.29 | 15.22 | 690 | 1.34 | 15.51 | 11.16 | 18.12 | 1.69 |
| 2025 | 661 | 1.96 | 20.42 | 661 | 1.40 | 13.92 | 11.20 | 17.70 | 1.43 |
| 2026 | 322 | 1.88 | 17.39 | 322 | 1.25 | 17.08 | 9.63 | 24.53 | 1.25 |


### The DK-open test: frozen model anchored on each book's open (same games: both books listed)

| set | games | clv_toward_%_of_moves | avg_move_toward | ats_bets | ats_win_% | ats_ci95 | roi_%_-110 | corr |
|---|---|---|---|---|---|---|---|---|
| 2023 · DK open · QB on | 312 | 68.11 | 0.85 | 305 | 57.05 | 51.4-62.5 | 8.91 | 0.32 |
| 2023 · DK open · QB off | 241 | 77.94 | 1.11 | 233 | 57.94 | 51.5-64.1 | 10.61 | 0.38 |
| 2023 · Bovada open · QB on | 305 | 64.00 | 1.18 | 301 | 57.81 | 52.2-63.3 | 10.36 | 0.45 |
| 2023 · Bovada open · QB off | 220 | 62.31 | 1.35 | 217 | 58.06 | 51.4-64.4 | 10.85 | 0.53 |
| 2024 · DK open · QB on | 262 | 77.05 | 2.70 | 260 | 60.77 | 54.7-66.5 | 16.01 | 0.64 |
| 2024 · DK open · QB off | 228 | 77.83 | 2.62 | 226 | 59.73 | 53.2-65.9 | 14.04 | 0.61 |
| 2024 · Bovada open · QB on | 230 | 63.68 | 0.68 | 224 | 56.25 | 49.7-62.6 | 7.39 | 0.28 |
| 2024 · Bovada open · QB off | 198 | 59.28 | 0.36 | 192 | 54.69 | 47.6-61.6 | 4.40 | 0.15 |
| 2023-2024 (tuning) · DK open · QB on | 574 | 73.19 | 1.70 | 565 | 58.76 | 54.7-62.7 | 12.18 | 0.51 |
| 2023-2024 (tuning) · DK open · QB off | 469 | 77.87 | 1.84 | 459 | 58.82 | 54.3-63.2 | 12.30 | 0.52 |
| 2023-2024 (tuning) · Bovada open · QB on | 535 | 63.87 | 0.97 | 525 | 57.14 | 52.9-61.3 | 9.09 | 0.39 |
| 2023-2024 (tuning) · Bovada open · QB off | 418 | 60.93 | 0.88 | 409 | 56.48 | 51.6-61.2 | 7.82 | 0.41 |
| 2025 (holdout) · DK open · QB on | 271 | 73.33 | 1.61 | 269 | 57.99 | 52.0-63.7 | 10.71 | 0.45 |
| 2025 (holdout) · DK open · QB off | 205 | 77.65 | 1.99 | 203 | 54.68 | 47.8-61.4 | 4.39 | 0.49 |
| 2025 (holdout) · Bovada open · QB on | 236 | 60.10 | 0.46 | 231 | 58.87 | 52.4-65.0 | 12.40 | 0.15 |
| 2025 (holdout) · Bovada open · QB off | 178 | 57.05 | 0.44 | 174 | 56.32 | 48.9-63.5 | 7.52 | 0.14 |
| 2023-2025 (full set) · DK open · QB on | 845 | 73.24 | 1.67 | 834 | 58.51 | 55.1-61.8 | 11.71 | 0.49 |
| 2023-2025 (full set) · DK open · QB off | 674 | 77.80 | 1.89 | 662 | 57.55 | 53.8-61.3 | 9.87 | 0.51 |
| 2023-2025 (full set) · Bovada open · QB on | 771 | 62.72 | 0.81 | 756 | 57.67 | 54.1-61.1 | 10.10 | 0.33 |
| 2023-2025 (full set) · Bovada open · QB off | 596 | 59.77 | 0.75 | 583 | 56.43 | 52.4-60.4 | 7.73 | 0.35 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB on | 533 | 75.21 | 2.15 | 529 | 59.36 | 55.1-63.5 | 13.32 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB off | 433 | 77.75 | 2.32 | 429 | 57.34 | 52.6-61.9 | 9.47 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB on | 466 | 61.83 | 0.57 | 455 | 57.58 | 53.0-62.0 | 9.93 | 0.21 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB off | 376 | 58.20 | 0.39 | 366 | 55.46 | 50.3-60.5 | 5.89 | 0.15 |


<details><summary>All thresholds (1.5 / 3 / 5)</summary>


| set | edge >= | games | clv_toward_%_of_moves | avg_move_toward | ats_bets | ats_win_% | ats_ci95 | roi_%_-110 | corr |
|---|---|---|---|---|---|---|---|---|---|
| 2023 · DK open · QB on | 1.50 | 312 | 68.11 | 0.85 | 305 | 57.05 | 51.4-62.5 | 8.91 | 0.32 |
| 2023 · DK open · QB on | 3.00 | 133 | 71.25 | 1.22 | 131 | 63.36 | 54.8-71.1 | 20.96 | 0.32 |
| 2023 · DK open · QB on | 5.00 | 28 | 82.35 | 2.04 | 28 | 82.14 | 64.4-92.1 | 56.82 | 0.32 |
| 2023 · DK open · QB off | 1.50 | 241 | 77.94 | 1.11 | 233 | 57.94 | 51.5-64.1 | 10.61 | 0.38 |
| 2023 · DK open · QB off | 3.00 | 72 | 88.10 | 1.95 | 72 | 69.44 | 58.0-78.9 | 32.58 | 0.38 |
| 2023 · DK open · QB off | 5.00 | 8 | 100.00 | 3.44 | 8 | 87.50 | 52.9-97.8 | 67.05 | 0.38 |
| 2023 · Bovada open · QB on | 1.50 | 305 | 64.00 | 1.18 | 301 | 57.81 | 52.2-63.3 | 10.36 | 0.45 |
| 2023 · Bovada open · QB on | 3.00 | 126 | 64.35 | 2.12 | 125 | 64.00 | 55.3-71.9 | 22.18 | 0.45 |
| 2023 · Bovada open · QB on | 5.00 | 31 | 66.67 | 4.94 | 31 | 80.65 | 63.7-90.8 | 53.96 | 0.45 |
| 2023 · Bovada open · QB off | 1.50 | 220 | 62.31 | 1.35 | 217 | 58.06 | 51.4-64.4 | 10.85 | 0.53 |
| 2023 · Bovada open · QB off | 3.00 | 67 | 70.31 | 3.28 | 67 | 73.13 | 61.5-82.3 | 39.62 | 0.53 |
| 2023 · Bovada open · QB off | 5.00 | 10 | 88.89 | 12.00 | 10 | 90.00 | 59.6-98.2 | 71.82 | 0.53 |
| 2024 · DK open · QB on | 1.50 | 262 | 77.05 | 2.70 | 260 | 60.77 | 54.7-66.5 | 16.01 | 0.64 |
| 2024 · DK open · QB on | 3.00 | 101 | 83.33 | 4.37 | 101 | 55.45 | 45.7-64.8 | 5.85 | 0.64 |
| 2024 · DK open · QB on | 5.00 | 27 | 85.19 | 8.33 | 27 | 66.67 | 47.8-81.4 | 27.27 | 0.64 |
| 2024 · DK open · QB off | 1.50 | 228 | 77.83 | 2.62 | 226 | 59.73 | 53.2-65.9 | 14.04 | 0.61 |
| 2024 · DK open · QB off | 3.00 | 62 | 88.33 | 5.96 | 62 | 61.29 | 48.8-72.4 | 17.01 | 0.61 |
| 2024 · DK open · QB off | 5.00 | 14 | 92.86 | 13.29 | 14 | 71.43 | 45.4-88.3 | 36.36 | 0.61 |
| 2024 · Bovada open · QB on | 1.50 | 230 | 63.68 | 0.68 | 224 | 56.25 | 49.7-62.6 | 7.39 | 0.28 |
| 2024 · Bovada open · QB on | 3.00 | 75 | 73.85 | 1.40 | 74 | 50.00 | 38.9-61.1 | -4.55 | 0.28 |
| 2024 · Bovada open · QB on | 5.00 | 13 | 72.73 | 1.50 | 13 | 76.92 | 49.7-91.8 | 46.85 | 0.28 |
| 2024 · Bovada open · QB off | 1.50 | 198 | 59.28 | 0.36 | 192 | 54.69 | 47.6-61.6 | 4.40 | 0.15 |
| 2024 · Bovada open · QB off | 3.00 | 36 | 65.52 | 0.99 | 36 | 47.22 | 32.0-63.0 | -9.85 | 0.15 |
| 2024 · Bovada open · QB off | 5.00 | 2 | 0.00 | -0.75 | 2 | 100.00 | 34.2-100.0 | 90.91 | 0.15 |
| 2023-2024 (tuning) · DK open · QB on | 1.50 | 574 | 73.19 | 1.70 | 565 | 58.76 | 54.7-62.7 | 12.18 | 0.51 |
| 2023-2024 (tuning) · DK open · QB on | 3.00 | 234 | 77.84 | 2.58 | 232 | 59.91 | 53.5-66.0 | 14.38 | 0.51 |
| 2023-2024 (tuning) · DK open · QB on | 5.00 | 55 | 84.09 | 5.13 | 55 | 74.55 | 61.7-84.2 | 42.31 | 0.51 |
| 2023-2024 (tuning) · DK open · QB off | 1.50 | 469 | 77.87 | 1.84 | 459 | 58.82 | 54.3-63.2 | 12.30 | 0.52 |
| 2023-2024 (tuning) · DK open · QB off | 3.00 | 134 | 88.24 | 3.81 | 134 | 65.67 | 57.3-73.2 | 25.37 | 0.52 |
| 2023-2024 (tuning) · DK open · QB off | 5.00 | 22 | 94.74 | 9.70 | 22 | 77.27 | 56.6-89.9 | 47.52 | 0.52 |
| 2023-2024 (tuning) · Bovada open · QB on | 1.50 | 535 | 63.87 | 0.97 | 525 | 57.14 | 52.9-61.3 | 9.09 | 0.39 |
| 2023-2024 (tuning) · Bovada open · QB on | 3.00 | 201 | 67.78 | 1.85 | 199 | 58.79 | 51.9-65.4 | 12.24 | 0.39 |
| 2023-2024 (tuning) · Bovada open · QB on | 5.00 | 44 | 68.29 | 3.92 | 44 | 79.55 | 65.5-88.8 | 51.86 | 0.39 |
| 2023-2024 (tuning) · Bovada open · QB off | 1.50 | 418 | 60.93 | 0.88 | 409 | 56.48 | 51.6-61.2 | 7.82 | 0.41 |
| 2023-2024 (tuning) · Bovada open · QB off | 3.00 | 103 | 68.82 | 2.48 | 103 | 64.08 | 54.5-72.7 | 22.33 | 0.41 |
| 2023-2024 (tuning) · Bovada open · QB off | 5.00 | 12 | 80.00 | 9.88 | 12 | 91.67 | 64.6-98.5 | 75.00 | 0.41 |
| 2025 (holdout) · DK open · QB on | 1.50 | 271 | 73.33 | 1.61 | 269 | 57.99 | 52.0-63.7 | 10.71 | 0.45 |
| 2025 (holdout) · DK open · QB on | 3.00 | 95 | 78.16 | 2.42 | 94 | 64.89 | 54.8-73.8 | 23.89 | 0.45 |
| 2025 (holdout) · DK open · QB on | 5.00 | 25 | 86.96 | 4.10 | 25 | 52.00 | 33.5-70.0 | -0.73 | 0.45 |
| 2025 (holdout) · DK open · QB off | 1.50 | 205 | 77.65 | 1.99 | 203 | 54.68 | 47.8-61.4 | 4.39 | 0.49 |
| 2025 (holdout) · DK open · QB off | 3.00 | 49 | 80.43 | 3.43 | 48 | 62.50 | 48.4-74.8 | 19.32 | 0.49 |
| 2025 (holdout) · DK open · QB off | 5.00 | 9 | 100.00 | 8.94 | 8 | 50.00 | 21.5-78.5 | -4.55 | 0.49 |
| 2025 (holdout) · Bovada open · QB on | 1.50 | 236 | 60.10 | 0.46 | 231 | 58.87 | 52.4-65.0 | 12.40 | 0.15 |
| 2025 (holdout) · Bovada open · QB on | 3.00 | 85 | 58.90 | 0.52 | 85 | 62.35 | 51.7-71.9 | 19.04 | 0.15 |
| 2025 (holdout) · Bovada open · QB on | 5.00 | 17 | 64.29 | 0.91 | 17 | 58.82 | 36.0-78.4 | 12.30 | 0.15 |
| 2025 (holdout) · Bovada open · QB off | 1.50 | 178 | 57.05 | 0.44 | 174 | 56.32 | 48.9-63.5 | 7.52 | 0.14 |
| 2025 (holdout) · Bovada open · QB off | 3.00 | 39 | 60.00 | 0.71 | 39 | 56.41 | 41.0-70.7 | 7.69 | 0.14 |
| 2025 (holdout) · Bovada open · QB off | 5.00 | 2 | 100.00 | 1.75 | 2 | 0.00 | 0.0-65.8 | -100.00 | 0.14 |
| 2023-2025 (full set) · DK open · QB on | 1.50 | 845 | 73.24 | 1.67 | 834 | 58.51 | 55.1-61.8 | 11.71 | 0.49 |
| 2023-2025 (full set) · DK open · QB on | 3.00 | 329 | 77.95 | 2.53 | 326 | 61.35 | 56.0-66.5 | 17.12 | 0.49 |
| 2023-2025 (full set) · DK open · QB on | 5.00 | 80 | 85.07 | 4.81 | 80 | 67.50 | 56.6-76.8 | 28.86 | 0.49 |
| 2023-2025 (full set) · DK open · QB off | 1.50 | 674 | 77.80 | 1.89 | 662 | 57.55 | 53.8-61.3 | 9.87 | 0.51 |
| 2023-2025 (full set) · DK open · QB off | 3.00 | 183 | 85.81 | 3.70 | 182 | 64.84 | 57.7-71.4 | 23.78 | 0.51 |
| 2023-2025 (full set) · DK open · QB off | 5.00 | 31 | 96.43 | 9.48 | 30 | 70.00 | 52.1-83.3 | 33.64 | 0.51 |
| 2023-2025 (full set) · Bovada open · QB on | 1.50 | 771 | 62.72 | 0.81 | 756 | 57.67 | 54.1-61.1 | 10.10 | 0.33 |
| 2023-2025 (full set) · Bovada open · QB on | 3.00 | 286 | 65.22 | 1.45 | 284 | 59.86 | 54.1-65.4 | 14.28 | 0.33 |
| 2023-2025 (full set) · Bovada open · QB on | 5.00 | 61 | 67.27 | 3.08 | 61 | 73.77 | 61.6-83.2 | 40.83 | 0.33 |
| 2023-2025 (full set) · Bovada open · QB off | 1.50 | 596 | 59.77 | 0.75 | 583 | 56.43 | 52.4-60.4 | 7.73 | 0.35 |
| 2023-2025 (full set) · Bovada open · QB off | 3.00 | 142 | 66.41 | 1.99 | 142 | 61.97 | 53.8-69.5 | 18.31 | 0.35 |
| 2023-2025 (full set) · Bovada open · QB off | 5.00 | 14 | 83.33 | 8.71 | 14 | 78.57 | 52.4-92.4 | 50.00 | 0.35 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB on | 1.50 | 533 | 75.21 | 2.15 | 529 | 59.36 | 55.1-63.5 | 13.32 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB on | 3.00 | 196 | 80.87 | 3.43 | 195 | 60.00 | 53.0-66.6 | 14.55 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB on | 5.00 | 52 | 86.00 | 6.30 | 52 | 59.62 | 46.1-71.8 | 13.81 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB off | 1.50 | 433 | 77.75 | 2.32 | 429 | 57.34 | 52.6-61.9 | 9.47 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB off | 3.00 | 111 | 84.91 | 4.84 | 110 | 61.82 | 52.5-70.4 | 18.02 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · DK open · QB off | 5.00 | 23 | 95.65 | 11.59 | 22 | 63.64 | 43.0-80.3 | 21.49 | 0.56 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB on | 1.50 | 466 | 61.83 | 0.57 | 455 | 57.58 | 53.0-62.0 | 9.93 | 0.21 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB on | 3.00 | 160 | 65.94 | 0.93 | 159 | 56.60 | 48.8-64.1 | 8.06 | 0.21 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB on | 5.00 | 30 | 68.00 | 1.17 | 30 | 66.67 | 48.8-80.8 | 27.27 | 0.21 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB off | 1.50 | 376 | 58.20 | 0.39 | 366 | 55.46 | 50.3-60.5 | 5.89 | 0.15 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB off | 3.00 | 75 | 62.50 | 0.84 | 75 | 52.00 | 40.9-62.9 | -0.73 | 0.15 |
| 2024-2025 (sensitivity: excl. 2023) · Bovada open · QB off | 5.00 | 4 | 66.67 | 0.50 | 4 | 50.00 | 15.0-85.0 | -4.55 | 0.15 |


</details>

<!-- AUTO:DKOPEN:END -->

<!-- AUTO:MOVEMENT:BEGIN -->
**Snapshots so far**

| captured_at_utc | label | games |
|---|---|---|
| 2026-10-12 11:08:35+00:00 | manual | 59 |


**First seen (by our capture; the open-watch slots start Sun 6 PM ET)**

| first_seen_et | games |
|---|---|
| Mon 07:08 | 59 |


Only one snapshot label so far: movement needs the scheduled slots.

<!-- AUTO:MOVEMENT:END -->

<!-- AUTO:LADDERFIT:BEGIN -->
_Generated by `python -m engine.cfb.lines.ladder_fit` from 1 snapshot time(s): 2026-10-12T11:08:35+00:00 (59 games). All rungs are x.5 and paired; de-vig = proportional within each pair._

**DK's implied ladder vs ours**

|  | DK implied (fit) | ours (Phase 3) |
|---|---|---|
| sigma at median total (49.5) | 15.812 | 15.041 |
| sigma per 10 pts of total | 0.430 | 0.582 |
| spike x at |margin|=3 | 2.493 | 3.740 |
| spike x at |margin|=7 | 2.495 | 3.263 |
| spike x at |margin|=10 | 1.227 | 1.950 |
| spike x at |margin|=14 | 1.465 | 1.832 |
| spike x at |margin|=17 | 0.888 | 1.870 |
| spike x at |margin|=21 | 1.809 | 2.210 |


Per-game sigma (no spikes): median 15.11, IQR 14.49-16.01; corr with total +0.21, with |line| +0.49.


**Reproduction error** (fit vs DK's actual rung prices; the CFB 'estimated vs real' check)

| rungs | games | MAE_pp_fit | MAE_pp_ours_at_dk_line | median_cents_fit (-1000..+1000) | p90_cents_fit | avg_pair_hold_% |
|---|---|---|---|---|---|---|
| 2472 | 59 | 1.35 | 1.88 | 17.71 | 118.57 | 7.01 |


**Ours (centered at DK's line) minus DK no-vig, by rung distance from the main line** (home perspective, both sides pooled via pairing)

| rung - line (pts) | rungs | ours_minus_dk_pp |
|---|---|---|
| (-45, -14] | 771 | -0.83 |
| (-14, -7] | 251 | -0.30 |
| (-7, -3] | 149 | -0.64 |
| (-3, 0] | 125 | -0.35 |
| (0, 3] | 120 | +0.31 |
| (3, 7] | 151 | +0.39 |
| (7, 14] | 240 | +0.56 |
| (14, 45] | 529 | +1.87 |

<!-- AUTO:LADDERFIT:END -->

<!-- AUTO:SHAPE:BEGIN -->
_Generated by `python -m engine.cfb.lines.ladder_edge`. 0 new paper rows this run -> `data\cfb\lines\paper_rungs_2026.csv`._

**Shape-edge bar status: IN PROGRESS: 0/60 graded games; $0** (pre-registered in docs/cfb/FORWARD_TEST.md)


**All captured rungs: mean edges by kind and price band (pp)**

| kind | price band | rungs | mean_shape_pp | share_shape_ge3 | mean_full_pp | mean_ev_shape | share_ev_shape_pos |
|---|---|---|---|---|---|---|---|
| getting | (-100000, -500] | 1196 | 1.80 | 22.99 | 1.74 | -0.05 | 1.92 |
| getting | (-500, -150] | 761 | 1.24 | 14.59 | 1.21 | -0.05 | 3.81 |
| getting | (-150, 100000] | 515 | -0.07 | 2.72 | 0.00 | -0.08 | 1.55 |
| laying | (-100000, -500] | 44 | 2.84 | 40.91 | 2.84 | -0.03 | 0.00 |
| laying | (-500, -150] | 269 | 0.24 | 1.49 | 0.08 | -0.06 | 0.00 |
| laying | (-150, 100000] | 2159 | -1.51 | 1.67 | -1.46 | -0.16 | 4.82 |


**Paper log so far:** 326 rows, 46 games; getting-points rows 286, of which shape-qualified 113, full-qualified 247. Not a result until the bar's sample is graded.

Shape-qualified getting rows: mean shape edge +4.61 pp vs DK no-vig; mean EV at the posted price -0.004 units; 27% of them are +EV after DK's hold.

<!-- AUTO:SHAPE:END -->
