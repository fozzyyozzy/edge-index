# CFB Phase 3 Report: Game Model, Margin Distribution & Backtest

Brief: `docs/CFB_PHASE3_BRIEF.md`. Built 2026-10-10. The backtest makes 0 API calls;
`project_week` made 1 (ledger: 168).
Tuning seasons 2022-2024 are evaluated leave-one-season-out (LOSO): the margin model and
the distribution are both refit without the test season. The 2025 holdout has **not**
been run yet (section at the end).

## Top line (pre-holdout)

1. **k: the ratings add information beyond the opener, from week 4 on.**
   Weeks 1-3: k = −0.07 [−0.23, +0.08], i.e. nothing; lean on the line, as you expected.
   Weeks 4-8: **+0.25 [+0.06, +0.46]**. Weeks 9+: **+0.46 [+0.23, +0.67]**.
   (Game bootstrap, 1,000 draws, fit on 2022-2024.)
2. **CLV: the close moves toward the model.** LOSO 2022-2024, Bovada open vs close.
   When |proj − open| ≥ 1.5 / 3 / 5, the close moved toward the model in **64% / 68% / 73%**
   of games where it moved (CIs 60-67 / 62-73 / 61-82), by +0.8 / +1.2 / +2.1 points on
   average. corr(proj − open, close − open) = **+0.26**. Without the QB term the
   ratings gap alone still gets 61% / 65% (corr +0.21).
3. **Calibration, 75-90% band (where tickets live): getting-points rungs are good,
   laying-points rungs are overconfident.**
   Getting points: predicted 83.4%, actual 82.0% (gap −1.3 [−2.3, −0.3]).
   **Laying points: predicted 82.0%, actual 78.7% (gap −3.3 [−5.8, −0.8]).** At those
   prices, 82% vs 79% is roughly −455 vs −370 fair. The gap shrinks every season
   (2022 −6.3, 2023 −2.8, 2024 −0.8) and is concentrated where the model likes the
   favorite **more** than the opener (−5.3 when ≥1.5 points more bullish, −0.9 when
   ≥1.5 less). 2026 to date: laying-points +1.9 [−4.9, +7.2]; the sample is small.
   See "Hypotheses" for what I tested and why it is **not** in the frozen model.

## What's frozen (`engine/cfb/model/params.json`)

- **Margin model:** `margin − open = k[bucket]·(ratings_margin − open) + 0.358·qb_delta`
  (no intercept). Ratings HFA is 3.07, from Phase 2.
- **Features kept: QB only.** The drop-one LOSO table removed special teams, rest and
  travel: each made LOSO MAE worse and had wrong-signed coefficients.
- **Distribution:** normal, σ = 12.18 − 0.003·|line| + 0.058·total (≈15.3 at a 53 total;
  the line size doesn't matter). Mean-preserving, with key-number spikes at
  **3, 7, 10, 14, 17, 21** (×3.7, 3.3, 1.95, 1.8, 1.9, 2.2). Zero mass at 0; pushes only
  on whole numbers. Student-t (df 53) and KDE were no better.
- **Lines:** Bovada open/close for 2021-25 (DK fallback); DK first for 2026/live.

## Surprises and judgment calls

1. **Spike bug, fixed before freezing.** Multiplying key-number masses and renormalizing
   dragged every favorite's mean 1.5-2 points toward 0 (a 20-point projection became
   18.2). The pmf now re-solves its location so the mean equals the projected margin,
   and the spikes are refit under that rule. Ironically the bug had been masking the
   laying-points overconfidence above.
2. **Extended key numbers.** The brief named 3/7/10/14. 17 and 21 are just as lopsided
   (1.44× and 1.75× before spikes), and adding them improves LOSO log-likelihood
   (−4.031 vs −4.046 per game). Margins of 5, 9, 12, 16 and 19 are still under-hit
   (0.5-0.75×), but no spike was added for those.
3. **Special teams didn't survive selection.** Brief §1.1 asked for it. The ratings work:
   **Iowa is #2-3 in net starting field position** in 2024-25 (+10 yards/drive). But in
   the margin model its coefficient is −0.01 [−0.16, +0.14], and dropping it improves LOSO
   MAE. So **Iowa did not move**: the market already prices field position (Iowa's line
   reflects it). The feature code stays, but it's not used.
4. **QB term (+0.36 [+0.20, +0.51]) assumes the starter is known at the open.** It is
   built from THIS game's starter (most dropbacks). If the news broke after the opener,
   the vs-open numbers are flattered. The ratings-only robustness rows show what's left
   without it. Live, only `data/cfb/manual/qb_overrides.csv` sets it.
5. **The ratings are partly in-sample on 2022-2024.** Phase 2 tuned its hyperparameters
   and the to_points fit on these seasons, so k here is mildly optimistic. The 2025
   holdout is clean for both layers (Phase 3 params have never seen it).
6. **DraftKings' 2023 open equals its close in 47% of games** (Bovada: 17%), so Bovada is
   the historical opener. 2026 uses DK open → close, which may not be a true
   Monday-morning open.
7. **ATS vs open looks strong (57.4% at ≥1.5, 798 bets) but vs close is about 50%.**
   That is consistent with the CLV result: the edge is the line moving to us, not beating
   the close. These are diagnostics, not a betting record. The −110 ROI assumes we get
   the open.
8. **Pass/sack attribution.** Passer names are parsed from play text (98-99% of
   dropbacks) and keyed as first initial + last name. Rare collisions across teams are
   possible.

## Hypotheses (found after looking at tuning data; NOT in the frozen model)

- **Favorite-direction shrink.** A term for the part of the ratings gap pointing toward
  the opening favorite fits at −0.25 [−0.53, +0.01]. It improves LOSO MAE by 0.014 and
  trims the laying-band miss from −3.3 to −2.7. Read: the ratings' signal toward the
  favorite is weaker than toward the dog.
- **Favorite-oriented KDE** (a shape that can learn big favorites' fatter downside:
  P(z<−1) is 18.3% vs 15.9% normal for projections ≥ 10) changed log-likelihood by
  only 0.0003 and didn't fix the band. It's in the code but not a tuning candidate.
- Per your data rule #5 these are hypotheses. Testing one properly means freezing it
  *before* a holdout, which would spend 2025 on it.

## Open questions for Tim

1. **The laying-points miscalibration** (−3.3 in the 75-90 band, worst in 2022): options are
   (a) freeze as is and let 2025 tell us whether it persists; it shrank to −0.8 in 2024.
   (b) Adopt the favorite-direction term or a calibration haircut on laying rungs *now*,
   before the holdout. (c) Restrict tickets to getting-points rungs until Phase 4.
   I'd lean (a); your call, since it changes what 2025 tests.
2. **Weeks 1-3:** k ≈ 0. Skip publishing CFB plays in weeks 1-3?
3. **QB news timing:** OK to keep the QB term (it's live only via the override file)?
4. **Key numbers 17/21:** OK with the extension beyond the brief's four?

## Leakage tests

`python -m pytest engine/cfb/model/tests engine/cfb/ratings/tests -q`: **7 passed**
(3 new and 4 from Phase 2). The new ones:
1. Every play's EPA, field position and FG result, and every game score at or after the
   2023 week-6 cutoff are scrambled. All features for every game in or before that week
   are bit-identical: ratings, special teams, QB delta, rest, travel, open line and total.
   Later special-teams features do move.
2. The FG make-probability model for season s is unchanged when FG results in season s
   and later are flipped.
3. Projections are unchanged when results and closes are overwritten.
Documented exception: `qb_change` uses the game's own starter (brief §3).

## Live: `project_week`

`python -m engine.cfb.model.project_week --season 2026 --week 7` (1 API call) projected
the 18 week-7 games that have a DK line so far (41 FBS games had no line yet on
Saturday). Each game gets the full ladder (−35.5..+35.5 in half points, both sides,
cover/push/fair odds) in `data/cfb/derived/projections_2026_wk07.{parquet,json}`. Ratings
warn that 12 week-6 midweek games' plays aren't pulled yet; run `update_week` Sunday,
then re-project.

## Results (generated)

<!-- AUTO:TUNING:BEGIN -->
_Generated by `python -m engine.cfb.model.run` at 2026-10-10 12:11._

## 1. k by week bucket (2022-2024 fit; game bootstrap 95% CI)

k = weight on (ratings margin - open). 0 = the ratings add nothing beyond the opener.

| bucket | k | ci95_lo | ci95_hi | boot_se |
|---|---|---|---|---|
| weeks 1-3 | -0.073 | -0.230 | +0.082 | +0.079 |
| weeks 4-8 | +0.252 | +0.059 | +0.461 | +0.102 |
| weeks 9+ | +0.459 | +0.231 | +0.666 | +0.114 |


## 2. CLV (LOSO out of sample, 2022-2024)

**CLV, 2022-2024 LOSO** (corr(proj - open, close - open) = +0.255)

| games | |proj-open| >= | n | moved_toward_pct | moved_away_pct | no_move_pct | toward_share_of_moves_pct | ci95 | avg_move_toward_model_pts |
|---|---|---|---|---|---|---|---|---|
| 2022-2024 LOSO | 1.5 | 817 | 54.8 | 31.2 | 14.0 | 63.7 | 60-67 | 0.8 |
| 2022-2024 LOSO | 3.0 | 299 | 59.5 | 28.1 | 12.4 | 67.9 | 62-73 | 1.2 |
| 2022-2024 LOSO | 5.0 | 69 | 69.6 | 26.1 | 4.3 | 72.7 | 61-82 | 2.1 |


**Calibration, 75-90% band, 2022-2024 LOSO** (game-bootstrap CI on actual - predicted)

| rungs | pairs | games | pred_pct | actual_pct | gap_pts | gap_ci95 |
|---|---|---|---|---|---|---|
| all | 36532 | 2243 | 83.1 | 81.5 | -1.7 | -2.7 to -0.8 |
| dog (getting) | 30607 | 2058 | 83.4 | 82.0 | -1.3 | -2.3 to -0.3 |
| fav (laying) | 5925 | 1048 | 82.0 | 78.7 | -3.3 | -5.8 to -0.8 |


**2026 to date (informational; frozen params; DK open/close)**

**CLV, 2026 to date** (corr(proj - open, close - open) = +0.250)

| games | |proj-open| >= | n | moved_toward_pct | moved_away_pct | no_move_pct | toward_share_of_moves_pct | ci95 | avg_move_toward_model_pts |
|---|---|---|---|---|---|---|---|---|
| 2026 to date | 1.5 | 44 | 72.7 | 11.4 | 15.9 | 86.5 | 72-94 | 2.0 |
| 2026 to date | 3.0 | 11 | 81.8 | 0.0 | 18.2 | 100.0 | 70-100 | 2.9 |
| 2026 to date | 5.0 | 1 | 100.0 | 0.0 | 0.0 | 100.0 | 21-100 | 3.0 |


**Calibration, 75-90% band, 2026 to date** (game-bootstrap CI on actual - predicted)

| rungs | pairs | games | pred_pct | actual_pct | gap_pts | gap_ci95 |
|---|---|---|---|---|---|---|
| all | 4425 | 283 | 83.1 | 82.6 | -0.5 | -3.4 to +1.8 |
| dog (getting) | 3492 | 240 | 83.3 | 82.2 | -1.1 | -4.3 to +1.8 |
| fav (laying) | 933 | 152 | 82.3 | 84.1 | 1.9 | -4.9 to +7.2 |


**Robustness: ratings gap only (no QB feature).** The QB feature assumes the starter is known at the open; these rows remove it.

corr(proj - open, close - open) = +0.207

| games | |proj-open| >= | n | moved_toward_pct | moved_away_pct | no_move_pct | toward_share_of_moves_pct | ci95 | avg_move_toward_model_pts |
|---|---|---|---|---|---|---|---|---|
| k only, 2022-2024 LOSO | 1.5 | 491 | 52.5 | 33.4 | 14.1 | 61.1 | 56-66 | 0.8 |
| k only, 2022-2024 LOSO | 3.0 | 103 | 57.3 | 31.1 | 11.7 | 64.8 | 55-74 | 1.4 |
| k only, 2022-2024 LOSO | 5.0 | 10 | 60.0 | 40.0 | 0.0 | 60.0 | 31-83 | 7.3 |

| games | vs | |edge| >= | bets | wins | win_pct | ci95 | roi_pct_at_-110 | pushes |
|---|---|---|---|---|---|---|---|---|
| k only, 2022-2024 LOSO | open | 1.5 | 477 | 256 | 53.7 | 49.2-58.1 | 2.5 | 14 |
| k only, 2022-2024 LOSO | open | 3.0 | 100 | 54 | 54.0 | 44.3-63.4 | 3.1 | 3 |
| k only, 2022-2024 LOSO | open | 5.0 | 9 | 4 | 44.4 | 18.9-73.3 | -15.2 | 1 |


## 3. Calibration, all rungs (LOSO, 2022-2024)


**2022-2024 LOSO**

| rungs | pairs | brier | log_loss | 75-90 pairs | 75-90 games | 75-90 pred_pct | 75-90 actual_pct | 75-90 gap_pts | 75-90 gap_ci95 |
|---|---|---|---|---|---|---|---|---|---|
| all | 161496 | 0.1114 | 0.3521 | 36532 | 2243 | 83.14 | 81.48 | -1.665 | -2.7 to -0.8 |
| dog (getting) | 137350 | 0.09621 | 0.3129 | 30607 | 2058 | 83.36 | 82.01 | -1.349 | -2.3 to -0.3 |
| fav (laying) | 24146 | 0.198 | 0.5752 | 5925 | 1048 | 82.03 | 78.73 | -3.296 | -5.8 to -0.8 |


Reliability, dog (getting):

| bin | n | games | pred_pct | actual_pct | ci95_lo | ci95_hi | actual_minus_pred |
|---|---|---|---|---|---|---|---|
| 50-60 | 8714 | 2194 | 55.2 | 55.9 | 54.2 | 57.7 | 0.7 |
| 60-70 | 11151 | 2161 | 65.2 | 65.6 | 64.3 | 67.1 | 0.4 |
| 70-75 | 6934 | 2108 | 72.5 | 73.3 | 71.9 | 74.7 | 0.7 |
| 75-80 | 8089 | 2058 | 77.6 | 76.7 | 75.5 | 78.1 | -0.8 |
| 80-85 | 9791 | 1984 | 82.6 | 81.2 | 79.8 | 82.5 | -1.4 |
| 85-90 | 12727 | 1881 | 87.6 | 86.0 | 84.9 | 87.0 | -1.6 |
| 90-95 | 18780 | 2044 | 92.7 | 91.6 | 90.8 | 92.5 | -1.1 |
| 95-100 | 61164 | 2243 | 98.5 | 97.8 | 97.4 | 98.2 | -0.7 |


Reliability, fav (laying):

| bin | n | games | pred_pct | actual_pct | ci95_lo | ci95_hi | actual_minus_pred |
|---|---|---|---|---|---|---|---|
| 50-60 | 7148 | 2218 | 54.8 | 52.4 | 50.4 | 54.6 | -2.4 |
| 60-70 | 5838 | 1767 | 64.8 | 62.8 | 60.5 | 65.0 | -2.0 |
| 70-75 | 2460 | 1191 | 72.5 | 70.6 | 67.9 | 73.1 | -1.9 |
| 75-80 | 2222 | 1020 | 77.5 | 73.2 | 70.0 | 75.8 | -4.3 |
| 80-85 | 1977 | 809 | 82.5 | 79.1 | 76.1 | 81.7 | -3.4 |
| 85-90 | 1726 | 604 | 87.4 | 85.5 | 82.6 | 88.0 | -2.0 |
| 90-95 | 1537 | 398 | 92.4 | 91.1 | 88.5 | 93.5 | -1.3 |
| 95-100 | 1238 | 199 | 97.4 | 98.0 | 95.8 | 99.4 | 0.6 |


**Diagnostic: laying rungs, 75-90% band, by season and by model-vs-open direction (how much more the model likes the laying team than the opener does)**

| season | pairs | games | pred_pct | actual_pct | gap_pts |
|---|---|---|---|---|---|
| 2022 | 1975.0 | 346.0 | 82.1 | 75.8 | -6.3 |
| 2023 | 1979.0 | 356.0 | 81.9 | 79.1 | -2.8 |
| 2024 | 1971.0 | 346.0 | 82.1 | 81.3 | -0.8 |

| direction | pairs | games | pred_pct | actual_pct | gap_pts |
|---|---|---|---|---|---|
| model <= -1.5 | 765.0 | 130.0 | 82.0 | 81.0 | -0.9 |
| -1.5 to 0 | 1543.0 | 284.0 | 82.0 | 79.6 | -2.4 |
| 0 to +1.5 | 2172.0 | 372.0 | 82.1 | 78.7 | -3.4 |
| model >= +1.5 | 1445.0 | 262.0 | 81.9 | 76.6 | -5.3 |


## Feature selection: drop-one (LOSO MAE, 2022-2024)

A group is kept if dropping it raises LOSO MAE and its coefficient signs make sense.

| model | loso_mae | delta_vs_all | group_helps | signs_ok | coefs |
|---|---|---|---|---|---|
| all groups | 12.1738 | 0.0000 | nan | nan | nan |
| drop st | 12.1614 | -0.0124 | False | False | st_fp_diff -0.012, st_fg_diff -0.438 |
| drop qb | 12.2244 | 0.0506 | True | True | qb_delta +0.357 |
| drop rest | 12.1723 | -0.0015 | False | False | rest_diff -0.362, bye_diff +3.810 |
| drop travel | 12.1458 | -0.0280 | False | False | travel_k +0.961, tz_diff -0.777, w2e_diff -3.560 |
| ratings gap only (k) | 12.1925 |  | nan | nan | nan |
| selected: qb | 12.1357 | -0.0381 | nan | nan | nan |


## Coefficients

Frozen model (groups: ['qb']):

| term | coef | ci95_lo | ci95_hi | boot_se |
|---|---|---|---|---|
| k_1-3 | -0.073 | -0.230 | +0.082 | +0.079 |
| k_4-8 | +0.252 | +0.059 | +0.461 | +0.102 |
| k_9+ | +0.459 | +0.231 | +0.666 | +0.114 |
| qb_delta | +0.358 | +0.195 | +0.511 | +0.081 |


For reference, all candidate features (not used):

| term | coef | ci95_lo | ci95_hi | boot_se |
|---|---|---|---|---|
| k_1-3 | -0.078 | -0.242 | +0.088 | +0.082 |
| k_4-8 | +0.253 | +0.062 | +0.460 | +0.104 |
| k_9+ | +0.449 | +0.214 | +0.655 | +0.116 |
| st_fp_diff | -0.012 | -0.164 | +0.136 | +0.079 |
| st_fg_diff | -0.438 | -1.544 | +0.647 | +0.560 |
| qb_delta | +0.357 | +0.194 | +0.512 | +0.082 |
| rest_diff | -0.362 | -1.034 | +0.306 | +0.357 |
| bye_diff | +3.810 | -1.138 | +8.606 | +2.580 |
| travel_k | +0.961 | -0.753 | +2.617 | +0.859 |
| tz_diff | -0.777 | -2.217 | +0.673 | +0.720 |
| w2e_diff | -3.560 | -18.201 | +7.230 | +6.417 |


## Distribution

| shape | spikes | loso_loglik_per_game |
|---|---|---|
| normal | 3,7,10,14,17,21 | -4.0308 |
| t | 3,7,10,14,17,21 | -4.0312 |
| kde | 3,7,10,14,17,21 | -4.0326 |
| normal | 3,7,10,14 | -4.0456 |
| t | 3,7,10,14 | -4.0460 |
| kde | 3,7,10,14 | -4.0476 |
| t | none | -4.1278 |
| normal | none | -4.1279 |
| kde | none | -4.1313 |


Chosen: **normal**, sigma = 12.18 + -0.0031·|line| + 0.0582·total; spikes {3: 3.739531609804069, 7: 3.2633091047121168, 10: 1.9504355891449954, 14: 1.8316453873338174, 17: 1.869834335566078, 21: 2.20993201557316}.


Key numbers, LOSO 2022-2024 (observed vs implied by the chosen distribution):

| |margin| | observed_pct | implied_pct | ratio |
|---|---|---|---|
| 1 | 3.25 | 2.85 | 1.14 |
| 2 | 3.39 | 2.84 | 1.19 |
| 3 | 10.70 | 10.59 | 1.01 |
| 4 | 3.79 | 2.80 | 1.35 |
| 5 | 2.05 | 2.78 | 0.74 |
| 6 | 3.30 | 2.75 | 1.20 |
| 7 | 8.96 | 8.85 | 1.01 |
| 8 | 3.25 | 2.67 | 1.22 |
| 9 | 1.20 | 2.62 | 0.46 |
| 10 | 5.08 | 5.01 | 1.01 |
| 11 | 2.27 | 2.52 | 0.90 |
| 12 | 1.60 | 2.46 | 0.65 |
| 13 | 2.14 | 2.40 | 0.89 |
| 14 | 4.32 | 4.27 | 1.01 |
| 15 | 1.83 | 2.26 | 0.81 |
| 16 | 1.07 | 2.19 | 0.49 |
| 17 | 4.01 | 3.97 | 1.01 |
| 18 | 2.23 | 2.05 | 1.09 |
| 19 | 1.25 | 1.97 | 0.63 |
| 20 | 1.87 | 1.89 | 0.99 |
| 21 | 4.06 | 4.00 | 1.01 |


## Margin accuracy (LOSO 2022-2024; same games in every column)

| games | model_MAE | open_MAE | close_MAE |
|---|---|---|---|
| 2243.00 | 12.14 | 12.19 | 12.02 |


By season:

| season | games | model_MAE | open_MAE | close_MAE |
|---|---|---|---|---|
| 2022 | 730.00 | 12.08 | 12.12 | 12.02 |
| 2023 | 753.00 | 12.06 | 12.19 | 11.94 |
| 2024 | 760.00 | 12.27 | 12.27 | 12.11 |


By bucket:

| bucket | games | model_MAE | open_MAE | close_MAE |
|---|---|---|---|---|
| 1-3 | 443.00 | 12.30 | 12.28 | 12.15 |
| 4-8 | 817.00 | 11.75 | 11.81 | 11.73 |
| 9+ | 983.00 | 12.38 | 12.47 | 12.21 |


2026 to date:

| bucket | games | model_MAE | open_MAE | close_MAE |
|---|---|---|---|---|
| 1-3 | 157.00 | 11.23 | 11.17 | 10.93 |
| 4-8 | 126.00 | 12.31 | 12.65 | 12.12 |


## ATS (diagnostic; -110 pricing)

| games | vs | |edge| >= | bets | wins | win_pct | ci95 | roi_pct_at_-110 | pushes |
|---|---|---|---|---|---|---|---|---|
| 2022-2024 LOSO | open | 1.5 | 798 | 458 | 57.4 | 53.9-60.8 | 9.6 | 19 |
| 2022-2024 LOSO | open | 3.0 | 291 | 164 | 56.4 | 50.6-61.9 | 7.6 | 8 |
| 2022-2024 LOSO | open | 5.0 | 68 | 45 | 66.2 | 54.3-76.3 | 26.3 | 1 |
| 2022-2024 LOSO | close | 1.5 | 1123 | 571 | 50.8 | 47.9-53.8 | -2.9 | 23 |
| 2022-2024 LOSO | close | 3.0 | 466 | 244 | 52.4 | 47.8-56.9 | -0.0 | 9 |
| 2022-2024 LOSO | close | 5.0 | 122 | 66 | 54.1 | 45.3-62.7 | 3.3 | 3 |
| 2026 | open | 1.5 | 44 | 30 | 68.2 | 53.4-80.0 | 30.2 | 0 |
| 2026 | open | 3.0 | 11 | 9 | 81.8 | 52.3-94.9 | 56.2 | 0 |
| 2026 | open | 5.0 | 1 | 1 | 100.0 | 20.7-100.0 | 90.9 | 0 |
| 2026 | close | 1.5 | 150 | 71 | 47.3 | 39.5-55.3 | -9.6 | 2 |
| 2026 | close | 3.0 | 61 | 27 | 44.3 | 32.5-56.7 | -15.5 | 1 |
| 2026 | close | 5.0 | 15 | 7 | 46.7 | 24.8-69.9 | -10.9 | 0 |


## Fair-ladder samples (10 random 2024 games, LOSO; favorite side, x.5 rungs)


**Maryland @ Indiana** (2024 wk 5): open -6.5 (Bovada), projected home margin +5.9, sigma 15.2, final +14. Ladder for **Indiana**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 6.5 | +1430 |
| -26.5 | 7.4 | +1260 |
| -25.5 | 8.2 | +1113 |
| -24.5 | 9.2 | +986 |
| -23.5 | 10.3 | +875 |
| -22.5 | 11.4 | +779 |
| -21.5 | 12.6 | +695 |
| -20.5 | 15.1 | +560 |
| -19.5 | 16.5 | +506 |
| -18.5 | 17.9 | +458 |
| -17.5 | 19.4 | +414 |
| -16.5 | 22.6 | +343 |
| -15.5 | 24.2 | +313 |
| -14.5 | 25.9 | +286 |
| -13.5 | 29.2 | +242 |
| -12.5 | 31.0 | +222 |
| -11.5 | 32.9 | +204 |
| -10.5 | 34.8 | +187 |
| -9.5 | 38.2 | +162 |
| -8.5 | 40.1 | +149 |
| -7.5 | 42.1 | +138 |
| -6.5 | 48.8 | +105 |
| -5.5 | 50.8 | -103 |
| -4.5 | 52.7 | -112 |
| -3.5 | 54.7 | -121 |
| -2.5 | 62.6 | -167 |
| -1.5 | 64.4 | -181 |
| -0.5 | 66.2 | -196 |
| +0.5 | 66.2 | -196 |
| +1.5 | 68.0 | -212 |
| +2.5 | 69.6 | -229 |
| +3.5 | 76.2 | -320 |
| +4.5 | 77.7 | -348 |
| +5.5 | 79.1 | -379 |
| +6.5 | 80.5 | -413 |
| +7.5 | 84.9 | -563 |
| +8.5 | 86.1 | -621 |
| +9.5 | 87.3 | -685 |


**Stanford @ Notre Dame** (2024 wk 7): open -23.0 (Bovada), projected home margin +23.7, sigma 14.7, final +42. Ladder for **Notre Dame**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 39.4 | +154 |
| -26.5 | 41.8 | +139 |
| -25.5 | 44.1 | +127 |
| -24.5 | 46.5 | +115 |
| -23.5 | 48.8 | +105 |
| -22.5 | 51.2 | -105 |
| -21.5 | 53.4 | -115 |
| -20.5 | 58.0 | -138 |
| -19.5 | 60.1 | -151 |
| -18.5 | 62.3 | -165 |
| -17.5 | 64.3 | -180 |
| -16.5 | 68.2 | -215 |
| -15.5 | 70.1 | -235 |
| -14.5 | 72.0 | -257 |
| -13.5 | 75.2 | -303 |
| -12.5 | 76.8 | -331 |
| -11.5 | 78.3 | -362 |
| -10.5 | 79.8 | -395 |
| -9.5 | 82.1 | -459 |
| -8.5 | 83.4 | -501 |
| -7.5 | 84.5 | -545 |
| -6.5 | 88.1 | -742 |
| -5.5 | 89.1 | -816 |
| -4.5 | 90.0 | -896 |
| -3.5 | 90.8 | -981 |
| -2.5 | 93.7 | -1495 |
| -1.5 | 94.4 | -1678 |
| -0.5 | 95.0 | -1881 |
| +0.5 | 95.0 | -1881 |
| +1.5 | 95.4 | -2077 |
| +2.5 | 95.8 | -2285 |
| +3.5 | 97.3 | -3560 |
| +4.5 | 97.6 | -4024 |
| +5.5 | 97.8 | -4535 |
| +6.5 | 98.1 | -5091 |


**Louisville @ Boston College** (2024 wk 9): open +7.5 (Bovada), projected home margin -5.1, sigma 15.1, final -4. Ladder for **Louisville**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 5.8 | +1634 |
| -26.5 | 6.5 | +1434 |
| -25.5 | 7.3 | +1263 |
| -24.5 | 8.2 | +1115 |
| -23.5 | 9.2 | +987 |
| -22.5 | 10.2 | +876 |
| -21.5 | 11.4 | +780 |
| -20.5 | 13.8 | +625 |
| -19.5 | 15.1 | +564 |
| -18.5 | 16.4 | +509 |
| -17.5 | 17.9 | +460 |
| -16.5 | 20.8 | +380 |
| -15.5 | 22.4 | +346 |
| -14.5 | 24.1 | +315 |
| -13.5 | 27.3 | +266 |
| -12.5 | 29.1 | +244 |
| -11.5 | 30.9 | +224 |
| -10.5 | 32.7 | +205 |
| -9.5 | 36.1 | +177 |
| -8.5 | 38.0 | +163 |
| -7.5 | 39.9 | +150 |
| -6.5 | 46.7 | +114 |
| -5.5 | 48.6 | +106 |
| -4.5 | 50.6 | -102 |
| -3.5 | 52.6 | -111 |
| -2.5 | 60.5 | -153 |
| -1.5 | 62.4 | -166 |
| -0.5 | 64.3 | -180 |
| +0.5 | 64.3 | -180 |
| +1.5 | 66.1 | -195 |
| +2.5 | 67.8 | -210 |
| +3.5 | 74.6 | -293 |
| +4.5 | 76.2 | -319 |
| +5.5 | 77.7 | -348 |
| +6.5 | 79.1 | -378 |
| +7.5 | 83.7 | -515 |
| +8.5 | 85.0 | -567 |
| +9.5 | 86.2 | -625 |


**Kansas @ West Virginia** (2024 wk 4): open -2.5 (Bovada), projected home margin +0.3, sigma 15.3, final +4. Ladder for **West Virginia**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -26.5 | 3.2 | +3016 |
| -25.5 | 3.7 | +2618 |
| -24.5 | 4.2 | +2279 |
| -23.5 | 4.8 | +1990 |
| -22.5 | 5.4 | +1743 |
| -21.5 | 6.1 | +1531 |
| -20.5 | 7.7 | +1202 |
| -19.5 | 8.5 | +1074 |
| -18.5 | 9.4 | +960 |
| -17.5 | 10.4 | +860 |
| -16.5 | 12.5 | +699 |
| -15.5 | 13.7 | +632 |
| -14.5 | 14.9 | +573 |
| -13.5 | 17.3 | +478 |
| -12.5 | 18.7 | +436 |
| -11.5 | 20.1 | +398 |
| -10.5 | 21.6 | +363 |
| -9.5 | 24.4 | +311 |
| -8.5 | 26.0 | +285 |
| -7.5 | 27.7 | +261 |
| -6.5 | 33.7 | +197 |
| -5.5 | 35.5 | +182 |
| -4.5 | 37.3 | +168 |
| -3.5 | 39.2 | +155 |
| -2.5 | 47.0 | +113 |
| -1.5 | 48.9 | +104 |
| -0.5 | 50.9 | -103 |
| +0.5 | 50.9 | -103 |
| +1.5 | 52.8 | -112 |
| +2.5 | 54.7 | -121 |
| +3.5 | 62.4 | -166 |
| +4.5 | 64.3 | -180 |
| +5.5 | 66.1 | -195 |
| +6.5 | 67.9 | -211 |
| +7.5 | 73.7 | -281 |
| +8.5 | 75.4 | -306 |
| +9.5 | 77.0 | -334 |


**Houston @ Arizona** (2024 wk 12): open -2.0 (Bovada), projected home margin +3.0, sigma 14.2, final +24. Ladder for **Arizona**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 3.4 | +2866 |
| -26.5 | 3.9 | +2465 |
| -25.5 | 4.5 | +2128 |
| -24.5 | 5.1 | +1843 |
| -23.5 | 5.9 | +1602 |
| -22.5 | 6.7 | +1397 |
| -21.5 | 7.6 | +1222 |
| -20.5 | 9.5 | +952 |
| -19.5 | 10.6 | +848 |
| -18.5 | 11.7 | +756 |
| -17.5 | 12.9 | +675 |
| -16.5 | 15.5 | +545 |
| -15.5 | 16.9 | +492 |
| -14.5 | 18.4 | +444 |
| -13.5 | 21.3 | +369 |
| -12.5 | 23.0 | +336 |
| -11.5 | 24.7 | +305 |
| -10.5 | 26.5 | +278 |
| -9.5 | 29.7 | +237 |
| -8.5 | 31.6 | +216 |
| -7.5 | 33.6 | +198 |
| -6.5 | 40.4 | +148 |
| -5.5 | 42.4 | +136 |
| -4.5 | 44.4 | +125 |
| -3.5 | 46.5 | +115 |
| -2.5 | 55.0 | -122 |
| -1.5 | 57.0 | -133 |
| -0.5 | 59.0 | -144 |
| +0.5 | 59.0 | -144 |
| +1.5 | 61.0 | -156 |
| +2.5 | 62.9 | -169 |
| +3.5 | 70.5 | -239 |
| +4.5 | 72.3 | -261 |
| +5.5 | 74.0 | -285 |
| +6.5 | 75.7 | -311 |
| +7.5 | 81.0 | -426 |
| +8.5 | 82.5 | -471 |
| +9.5 | 83.9 | -520 |


**Toledo @ Northern Illinois** (2024 wk 8): open -2.5 (Bovada), projected home margin +5.2, sigma 14.3, final -7. Ladder for **Northern Illinois**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 5.0 | +1915 |
| -26.5 | 5.7 | +1663 |
| -25.5 | 6.5 | +1449 |
| -24.5 | 7.3 | +1267 |
| -23.5 | 8.3 | +1111 |
| -22.5 | 9.3 | +977 |
| -21.5 | 10.4 | +862 |
| -20.5 | 12.8 | +681 |
| -19.5 | 14.1 | +610 |
| -18.5 | 15.5 | +547 |
| -17.5 | 16.9 | +491 |
| -16.5 | 20.0 | +401 |
| -15.5 | 21.6 | +363 |
| -14.5 | 23.3 | +329 |
| -13.5 | 26.6 | +276 |
| -12.5 | 28.4 | +252 |
| -11.5 | 30.3 | +230 |
| -10.5 | 32.3 | +210 |
| -9.5 | 35.8 | +180 |
| -8.5 | 37.8 | +165 |
| -7.5 | 39.8 | +151 |
| -6.5 | 46.9 | +113 |
| -5.5 | 49.0 | +104 |
| -4.5 | 51.0 | -104 |
| -3.5 | 53.0 | -113 |
| -2.5 | 61.4 | -159 |
| -1.5 | 63.4 | -173 |
| -0.5 | 65.3 | -188 |
| +0.5 | 65.3 | -188 |
| +1.5 | 67.1 | -204 |
| +2.5 | 68.9 | -221 |
| +3.5 | 75.9 | -314 |
| +4.5 | 77.5 | -344 |
| +5.5 | 79.0 | -376 |
| +6.5 | 80.4 | -411 |
| +7.5 | 85.1 | -570 |
| +8.5 | 86.3 | -632 |
| +9.5 | 87.5 | -701 |


**Nebraska @ Indiana** (2024 wk 8): open -6.0 (Bovada), projected home margin +6.8, sigma 14.9, final +49. Ladder for **Indiana**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 7.1 | +1304 |
| -26.5 | 8.0 | +1148 |
| -25.5 | 9.0 | +1013 |
| -24.5 | 10.0 | +897 |
| -23.5 | 11.2 | +796 |
| -22.5 | 12.4 | +708 |
| -21.5 | 13.7 | +632 |
| -20.5 | 16.4 | +509 |
| -19.5 | 17.9 | +459 |
| -18.5 | 19.4 | +415 |
| -17.5 | 21.0 | +376 |
| -16.5 | 24.3 | +311 |
| -15.5 | 26.1 | +284 |
| -14.5 | 27.9 | +259 |
| -13.5 | 31.4 | +219 |
| -12.5 | 33.3 | +201 |
| -11.5 | 35.2 | +184 |
| -10.5 | 37.2 | +169 |
| -9.5 | 40.7 | +146 |
| -8.5 | 42.7 | +134 |
| -7.5 | 44.7 | +124 |
| -6.5 | 51.6 | -107 |
| -5.5 | 53.6 | -115 |
| -4.5 | 55.5 | -125 |
| -3.5 | 57.5 | -135 |
| -2.5 | 65.4 | -189 |
| -1.5 | 67.2 | -205 |
| -0.5 | 69.0 | -223 |
| +0.5 | 69.0 | -223 |
| +1.5 | 70.7 | -241 |
| +2.5 | 72.3 | -261 |
| +3.5 | 78.6 | -368 |
| +4.5 | 80.1 | -402 |
| +5.5 | 81.4 | -439 |
| +6.5 | 82.7 | -479 |
| +7.5 | 86.9 | -661 |
| +8.5 | 88.0 | -732 |
| +9.5 | 89.0 | -811 |


**Kennesaw State @ Louisiana Tech** (2024 wk 14): open -11.0 (Bovada), projected home margin +14.4, sigma 14.2, final +33. Ladder for **Louisiana Tech**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 17.3 | +479 |
| -26.5 | 19.0 | +427 |
| -25.5 | 20.7 | +382 |
| -24.5 | 22.6 | +343 |
| -23.5 | 24.5 | +308 |
| -22.5 | 26.5 | +277 |
| -21.5 | 28.6 | +250 |
| -20.5 | 32.8 | +205 |
| -19.5 | 35.0 | +186 |
| -18.5 | 37.2 | +169 |
| -17.5 | 39.4 | +154 |
| -16.5 | 43.8 | +128 |
| -15.5 | 46.0 | +117 |
| -14.5 | 48.2 | +107 |
| -13.5 | 52.4 | -110 |
| -12.5 | 54.5 | -120 |
| -11.5 | 56.7 | -131 |
| -10.5 | 58.8 | -142 |
| -9.5 | 62.3 | -165 |
| -8.5 | 64.2 | -180 |
| -7.5 | 66.1 | -195 |
| -6.5 | 72.3 | -261 |
| -5.5 | 74.0 | -285 |
| -4.5 | 75.6 | -310 |
| -3.5 | 77.1 | -338 |
| -2.5 | 83.1 | -492 |
| -1.5 | 84.4 | -543 |
| -0.5 | 85.7 | -599 |
| +0.5 | 85.7 | -599 |
| +1.5 | 86.8 | -655 |
| +2.5 | 87.7 | -714 |
| +3.5 | 91.4 | -1062 |
| +4.5 | 92.2 | -1181 |
| +5.5 | 92.9 | -1312 |
| +6.5 | 93.6 | -1454 |
| +7.5 | 95.6 | -2151 |
| +8.5 | 96.1 | -2447 |
| +9.5 | 96.5 | -2782 |


**Army @ Temple** (2024 wk 5): open +13.0 (Bovada), projected home margin -10.0, sigma 14.6, final -28. Ladder for **Army**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 10.6 | +846 |
| -26.5 | 11.8 | +749 |
| -25.5 | 13.1 | +665 |
| -24.5 | 14.4 | +592 |
| -23.5 | 15.9 | +529 |
| -22.5 | 17.5 | +473 |
| -21.5 | 19.1 | +424 |
| -20.5 | 22.5 | +344 |
| -19.5 | 24.3 | +312 |
| -18.5 | 26.1 | +283 |
| -17.5 | 28.0 | +257 |
| -16.5 | 31.9 | +214 |
| -15.5 | 33.9 | +195 |
| -14.5 | 35.9 | +178 |
| -13.5 | 39.8 | +151 |
| -12.5 | 41.9 | +139 |
| -11.5 | 44.0 | +127 |
| -10.5 | 46.1 | +117 |
| -9.5 | 49.8 | +101 |
| -8.5 | 51.8 | -108 |
| -7.5 | 53.8 | -117 |
| -6.5 | 60.7 | -154 |
| -5.5 | 62.6 | -168 |
| -4.5 | 64.5 | -182 |
| -3.5 | 66.3 | -197 |
| -2.5 | 73.6 | -279 |
| -1.5 | 75.3 | -305 |
| -0.5 | 76.9 | -333 |
| +0.5 | 76.9 | -333 |
| +1.5 | 78.4 | -362 |
| +2.5 | 79.7 | -393 |
| +3.5 | 85.0 | -565 |
| +4.5 | 86.1 | -621 |
| +5.5 | 87.2 | -683 |
| +6.5 | 88.2 | -749 |
| +7.5 | 91.4 | -1063 |
| +8.5 | 92.2 | -1189 |
| +9.5 | 93.0 | -1330 |


**Maryland @ Oregon** (2024 wk 11): open -25.0 (Bovada), projected home margin +22.9, sigma 15.7, final +21. Ladder for **Oregon**:

| rung | cover_pct | fair_odds |
|---|---|---|
| -27.5 | 37.9 | +164 |
| -26.5 | 40.1 | +149 |
| -25.5 | 42.3 | +136 |
| -24.5 | 44.5 | +125 |
| -23.5 | 46.7 | +114 |
| -22.5 | 48.8 | +105 |
| -21.5 | 51.0 | -104 |
| -20.5 | 55.3 | -123 |
| -19.5 | 57.3 | -134 |
| -18.5 | 59.4 | -146 |
| -17.5 | 61.3 | -159 |
| -16.5 | 65.1 | -187 |
| -15.5 | 67.0 | -203 |
| -14.5 | 68.8 | -220 |
| -13.5 | 72.0 | -257 |
| -12.5 | 73.6 | -279 |
| -11.5 | 75.2 | -303 |
| -10.5 | 76.6 | -328 |
| -9.5 | 79.1 | -377 |
| -8.5 | 80.4 | -409 |
| -7.5 | 81.6 | -442 |
| -6.5 | 85.4 | -587 |
| -5.5 | 86.5 | -640 |
| -4.5 | 87.5 | -698 |
| -3.5 | 88.4 | -758 |
| -2.5 | 91.7 | -1111 |
| -1.5 | 92.5 | -1231 |
| -0.5 | 93.2 | -1362 |
| +0.5 | 93.2 | -1362 |
| +1.5 | 93.7 | -1491 |
| +2.5 | 94.2 | -1627 |
| +3.5 | 96.1 | -2434 |
| +4.5 | 96.4 | -2715 |
| +5.5 | 96.8 | -3023 |
| +6.5 | 97.1 | -3358 |
| +7.5 | 98.0 | -5011 |
| +8.5 | 98.3 | -5721 |
| +9.5 | 98.5 | -6525 |


## Iowa check (special-teams ratings, end of season / as of now)

| season | as_of_week | teams | net_start_fp_yds | fp_rank | fg_poe_per_game | fg_rank |
|---|---|---|---|---|---|---|
| 2024 | 17 | 134 | +10.29 | 3 | +0.58 | 17 |
| 2025 | 17 | 136 | +10.85 | 2 | +0.39 | 26 |
| 2026 | 15 | 138 | +8.00 | 11 | +0.26 | 25 |

<!-- AUTO:TUNING:END -->
