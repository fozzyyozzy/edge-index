# NBA Floor Lines — Phase 2 Pre-Registration

> **Status: approved by Tim 2026-10-21 and registered by the commit that adds this file to `nba-phase1`.**
> - The commit hash is recorded in `PHASE2_RESULTS.md`.
> - The holdout runs **once**, after this commit.
> - No 2025-26 outcome or price has been used for any modelling choice before this commit.
>   - Phase 1 data-quality checks (league means, ESPN cross-check) and the coverage sample (market *availability* only, §6.6) are not modelling choices.

## 1. Data and split

- **Source:** `data/nba/player_games.parquet` (ESPN box scores, Phase 1), with pregame DK spread/total from `data/nba/lines/pregame_spreads_totals.parquet`.
- **Train:** 2023-24 and 2024-25 regular seasons.
  - Model structure, distribution family per market, shrinkage, recency weights and any matchup terms are chosen here.
  - Selection method: fit on 2023-24, validate on 2024-25, then refit on both.
- **Holdout:** the 2025-26 regular season, entirely.
- **Walk-forward (rule 4):** every projection for a game uses only games strictly before that game's date. During the holdout, parameters are frozen and only the data inputs roll forward.

## 2. What gets scored

- **Unit:** one (player-game, market, rung k) row, with k an integer threshold (DK alt ladders are "k+" at whole numbers).
  - **Prediction:** `p = P(stat ≥ k)` from the frozen model.
  - **Outcome:** `stat ≥ k` from the ESPN box.
- **Eligible player-games** (implemented in `engine/nba/eligibility.py`, tested in `automation/tests/nba/test_nba_eligibility.py`):
  - The player **played** (DK voids props for non-participants; availability is handled by Phase 3 holds).
  - He has **≥ 8 games played this season (any team) strictly before the game date**.
  - His **mean minutes over his last ≤ 10 games played this season, strictly before the game date, is ≥ 20**.
  - **No leakage:** both filters compare dates explicitly (`date < game date`), so the scored game and anything after it never enter. The tests check that:
    - changing the scored game's or any later game's minutes doesn't change eligibility
    - a malformed same-date row is not counted as "before"
    - on real 2024-25 data, the prior-game count equals the strict-before count
- **Evaluation band:** rungs with model p in **[0.60, 0.95)**.
- **Calibration-slope set (gating):** rungs with p in **[0.50, 0.97]**.
- **Slope diagnostic (non-gating):** the same slope on rungs with p in **[0.60, 0.90]**. Reported only.
- **Bins:** 5-point bins, 60–65 … 90–95.
  - Each bin reports n (rungs) and n_pg (distinct player-games). Rungs within a player-game are nested and correlated, so n overstates the evidence.
  - The gate uses n.
- **Naive baseline:** last-10 played games' clear rate at the same rung (strictly prior games, ≥ 5 required).
  - Rows without it are dropped from **both** model and baseline Brier.

## 3. Calibration bars (applied to each market separately)

| ID | Bar | Pass if |
|---|---|---|
| B0 | Sample: at least 2 of the four 70–90 bins have n ≥ 300 | otherwise **INSUFFICIENT**, which counts as not passed |
| B1 | Calibration slope: logistic recalibration `logit P(y) = a + b·logit(p)` on the slope set | **0.90 ≤ b ≤ 1.10** |
| B2 | Bin accuracy in 70–75, 75–80, 80–85, 85–90, for each bin with n ≥ 300 | **\|mean p − hit rate\| ≤ 3.0 pts** |
| B3 | Brier score on the evaluation band, same rows as the naive baseline | **model Brier < naive Brier** |
| B4 | Not hot: for each bin from 75 up (75–80 … 90–95) with n ≥ 300 | **hit rate ≥ mean p − 5.0 pts** |

- **A market passes only if B0–B4 all pass.**
- **A market that fails is dropped from v1, not tuned on the holdout.** Any later fix gets a new pre-registration and is judged on 2026-27 forward data.
- **What gets reported:** every market's numbers, plus reliability tables over the full 5–95 range and the 0.60–0.90 slope diagnostic.

## 4. Markets

| Market | Stat | DK keys (main / alt) | Card role if it passes |
|---|---|---|---|
| Points | `pts` | `player_points` / `player_points_alternate` | card-eligible |
| Rebounds | `reb` | `player_rebounds` / `player_rebounds_alternate` | card-eligible |
| Assists | `ast` | `player_assists` / `player_assists_alternate` | card-eligible |
| Threes | `fg3m` | `player_threes` / `player_threes_alternate` | **card-eligible** (Tim, 2026-10-21) |
| P+R | `pr` | `player_points_rebounds` / `_alternate` | card-eligible |
| P+A | `pa` | `player_points_assists` / `_alternate` | card-eligible |
| R+A | `ra` | `player_rebounds_assists` / `_alternate` | card-eligible |
| PRA | `pra` | `player_points_rebounds_assists` / `_alternate` | card-eligible |
| Steals | `stl` | `player_steals` / `player_steals_alternate` | **shadow-only for the first forward month**; then card-eligible only by Tim's decision |
| Blocks | `blk` | `player_blocks` / `player_blocks_alternate` | **shadow-only for the first forward month**; then card-eligible only by Tim's decision |

All ten are held to the same bars (§3). Combos are scored on their own outcome column, which the data gate checks equals the sum of its parts. Correlation between components is the model's job and is not assumed independent.

## 5. Frozen before the holdout runs

Each of these is recorded in `PHASE2_RESULTS.md` with this file's commit hash:
- distribution family per market
- minutes model
- recency weights and shrinkage
- eligibility thresholds
- band edges
- baseline definition
- de-vig method (§6.2)
- random seeds, if any

Matchup terms are included only if they improved **2024-25 validation** calibration.

## 6. Market blend

### 6.1 When it runs
This section applies **only if historical DK prop prices for 2025-26 are pulled**. That needs Tim's separate approval: the full pull is ~111k–246k credits.
- Without them, the blend is evaluated forward-only in Phase 4, and the card starts at the default in §6.5.
- It is scored on the same holdout, after the calibration bars, in the same single run.

### 6.2 Market-only probability (de-vig)
- **Price snapshot:** for each priced alt rung, the latest pregame snapshot (tip − 10 min).
- **Formula:** `p_market = implied(alt Over price) / (1 + h)`. This is the same method as NFL `common.novig`.
  - `h` is the hold on that player's two-way main line for the same market in the same snapshot: `implied(Over) + implied(Under) − 1`. Quotes with h outside [−0.01, 0.25] are discarded.
  - If the player has no usable main line, `h` is that market's median hold in that snapshot.
  - If the market has none, `h` is the median hold across all markets in that snapshot.
  - Which source was used is recorded on every row.

### 6.3 Variants compared
- **Model-only:** `p_model` (w = 1).
- **Market-only:** `p_market` (w = 0).
- **Blends:** `p_w = w · p_model + (1 − w) · p_market` for **w ∈ {0.1, 0.2, 0.4, 0.6}**, with w the model's weight.

### 6.4 Rows
The same rows for every variant:
- eligible player-games (§2)
- priced alt rungs whose **`p_market` is in [0.50, 0.97]**

Selection is by market price, not by model, so no variant chooses its own rows. Rows are pooled across the **card-eligible markets** that have prices. Steals and blocks are reported separately and never set the card's weight.

### 6.5 The weight rule (written now, applied mechanically)
1. Compute the Brier score of market-only and of each blend w ∈ {0.1, 0.2, 0.4, 0.6} on the §6.4 rows.
2. A blend **qualifies** only if its Brier is **strictly lower than market-only's**.
3. **If one or more blends qualify:** the card uses the qualifying w with the lowest Brier. On an exact tie, use the smaller w (more market-dominant).
4. **If none qualify:** the card uses **w = 0.1** (market-dominant).
5. Model-only (w = 1) is reported but can never be selected.
6. Per-market Brier for every variant is reported as a diagnostic. It does **not** change the pooled weight. A market-specific weight would need a new pre-registration judged on forward data.
7. Whatever w this rule picks is the starting live weight for Phase 4. Shadow cards keep logging every other w, and any change to the live w is judged on forward data under the Phase 4 bars, not on the holdout.

### 6.6 Coverage sample (already approved, not a modelling input)
The 7-game coverage sample (one game per month of 2025-26) is used only to see **which markets DK carried**. Its prices are not used for any modelling choice and are not part of the §6.4 scoring rows.

## 7. Grading definitions (for Phase 3 and 4 forward grading)

| Grade | When |
|---|---|
| **UNGRADEABLE** | The leg's player can't be matched to a box score: no crosswalk match, an ESPN row without an id (see `espn_issues.csv`), or a missing box score. **Never WIN or LOSS.** Logged with the reason. Excluded from hit-rate and calibration counts, but its count is reported. |
| **VOID** | The player didn't play (DK voids the prop). |
| **WIN / LOSS** | The stat from the matched ESPN box compared with the rung. |

## 8. Integrity

- **One holdout run.** If code is fixed after it, both runs are reported and the first one stands for pass/fail and for the §6.5 weight.
- **Slices found after looking** are reported as hypotheses only (CLAUDE.md rule 5).
- **Real data only:** every scored row traces to an ESPN `game_id` + `espn_id`, and every price to a stored Odds API snapshot.
