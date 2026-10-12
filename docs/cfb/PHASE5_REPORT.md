# CFB Phase 5 Report: More Markets & the CFB Floor Card

Brief: `docs/CFB_PHASE5_BRIEF.md`. Started 2026-10-12. Per Tim: any new σ is fit **without**
recency weighting (diagnostics show no variance trend), and plays start at **week 4**.
The frozen Phase 2/3 parameters are untouched.

## 1. Moneylines (5A): checkpoint 1

**Data:** CFBD has **closing** moneylines only, with no opener in any provider: Bovada 2021-26
(708-763 FBS games a season) and DK 2023-26. So everything is **vs the close, which is
conservative**: our projection is anchored at the open, while the close has seen the week's
information. Win probability = P(margin > 0) from the frozen Phase 3 distribution
(no ties), centered on the Phase 3 projection. 2022-24 projections are LOSO, as in Phase 3.
**No new parameters.**

- **65-90% band calibration:** the model is within 2 pts in both eras. 2022-24 LOSO:
  predicted 77.2%, actual 76.2% (**−1.0**, CI −3.6 to +1.6, 1,088 games). 2025 holdout: 76.2%
  vs 76.0% (**−0.3**, CI −4.4 to +3.8, 387 games). The 2 pt rule isn't triggered, so **no
  recalibration parameter**.
- **Model vs the book's closing no-vig:** in 2022-24 the close is slightly better (log loss
  0.5516 vs 0.5464). In the **2025 holdout the model beats the close**: 0.5372 vs 0.5408 vs
  Bovada, and 0.5315 vs 0.5370 vs DK. Brier scores are about equal (0.1816 vs 0.1820).
- **Paper strategy** (model − no-vig ≥ 3 pts and EV > 0 at the posted closing price): **no
  reliable edge vs the close.** 2022-24: 915 bets, ROI −0.7% (CI −8.0 to +7.4). 2025: −2.4%
  vs Bovada, +4.3% vs DK, with CIs spanning ±10-15%. The ≤ −300 band lost 9.2% in 2022-24 but
  won in 2025. Unstable, so don't trade it. Against the **open** it may differ, but there is
  no opening ML in history; the 2026 DK snapshots will provide one.
- **ML/spread consistency** (the book's own close spread through our distribution vs its
  no-vig ML): they differ by 2.8 pts on average (2025: 3.3), and by ≥ 3 pts in 735 of 2,117
  games (2022-24). **When they disagree, the moneyline is slightly better** (Brier 0.1772 vs
  0.1786 in 2022-24; 0.1804 vs 0.1827 in 2025). The disagreement is systematic by spread size:
  for |spread| > 14 the spread-implied win probability is **+0.7 to +2.1 pts higher** for the
  home side than the ML says, and it's ~0 under 10. Read: on big spreads the market's ML
  carries more upset risk than our spread distribution does. Shading toward the ML there is
  safer, which matters for any moneyline leg in 5E.

**5E rule (Tim, 2026-10-12): big-favorite moneyline shading.** For any moneyline leg in a game
whose DK spread is **larger than 14 points**, the model win probability used for eligibility
and EV is **shaded toward DK's no-vig moneyline probability**. This follows from the finding
above: on spreads over 14, the market's ML carries more upset risk than our spread
distribution, and the ML was right more often when they disagreed. Implementation:
`p_used = (p_model + p_novig) / 2` for spreads > 14 (an equal-weight blend; no parameter
fit, so 2025 isn't spent). Unchanged for spreads ≤ 14. The card JSON records both
probabilities.

## 2. Totals (5B): interim, before the weather decision and the freeze

**Non-weather build, tuning seasons 2022-24, LOSO.** Team-game stats come from
`games.parquet` (points), CFBD advanced game stats (drives: PBP drive/offense labels proved
unreliable, e.g. punts credited to the receiving team) and Phase 2 model plays (plays per
game and explosiveness, garbage time excluded), plus clock-based seconds per play. Each gets
an opponent-adjusted as-of ridge with a 0.5 × last-season prior and fixed λ.

| LOSO MAE, 2022-24 (2,237 games) | |
|---|---|
| **Open total, no model** | **12.67** |
| T_pts (points per game) + k_t | 12.71 |
| T_ppd (points per drive × drives) + k_t | 12.72 |
| T_epa (Phase 2 EPA × expected plays) + k_t | 12.72 |
| T_pts + tempo clash + explosive matchup | 12.72 |

- **No totals model beats the opening total.** k_t (best spec, T_pts): weeks 1-3 +0.08
  [−0.31, +0.44], weeks 4-8 +0.06 [−0.23, +0.36], weeks 9+ +0.11 [−0.19, +0.38]. Every CI
  spans 0. The raw signal is near zero: corr(model − open, actual − open) is −0.01 to +0.04
  in every bucket.
- **Both style interactions fail** drop-one (dropping either lowers LOSO MAE; the explosive
  matchup also has the wrong sign).
- **σ_t** = 11.06 + 0.093 × total (≈ 16.0 at 53.5). Adding pace doesn't help LOSO (−4.1915 vs
  −4.1918), so it's line only, with **no recency weighting** per Tim.
- **Key totals are weak but present:** 41, 51, 55 and 37 land 1.5-1.8× as often as implied
  (~3% vs ~2%). Spikes will be tested LOSO at the freeze.
- **Margin/total residual correlation:** +0.075 (+0.080 favorite-oriented). Small, and it
  feeds 5C team totals.
- **Disclosure:** one early sanity printout pooled correlations across 2021-2026, which
  includes the 2025 totals holdout (three summary numbers, no fitting). Every tuning step
  since uses 2022-24 only.

**Weather options (no weather data pulled)**

| | Open-Meteo | NOAA (NCEI ISD + NWS) |
|---|---|---|
| Commercial use | **Free tier is non-commercial only**; sites with paid subscriptions count as commercial | U.S. federal data: NCEI restricts only **non-U.S.** ISD data (WMO Res. 40, per its readme); NWS API: "open data, free to use for any purpose" |
| History | Historical API needs **Professional, ~$99/mo** (Standard $29/mo has no history) | ISD-Lite hourly (temp, wind, 1h/6h precip), about 150 MB for all venues 2021-26, free |
| Live | Included in paid plans | NWS `points` → `forecastHourly`, free; a User-Agent with contact info is required |
| License | CC BY 4.0 (attribution) | Public-domain U.S. government work (inferred from federal-work status; no explicit "commercial OK" sentence found for ISD) |
| Coverage | Gridded, every venue | **98.6% of 3,647 outdoor FBS games have an active U.S. station ≤ 25 km** (median 6.5 km, p90 14 km). Only Dublin/London (6 games) lack one; those are left as missing |

**Recommendation: NOAA.** It's free, the terms fit commercial use for U.S. stations, and
coverage is near-complete. One caveat to verify on the first pull: the station list
(`isd-history.csv`) was last updated August 2025, so 2025-26 file availability per station
gets confirmed then. **Expectation is modest:** the non-weather features carry no signal over
the open, and the market already prices forecast wind and rain. Weather is worth one honest
test, not a lot of build.

### 5B outcome: weather test and decision (Tim's rule)

- **Weather source: NOAA.** NCEI ISD-Lite for 2021 to 2025-08-25, when ISD stopped updating;
  its successor **GHCNh** (by-year parquet) for 2025-26, with about a 1-week lag. U.S. stations
  only: 147 nearest stations, 724 + 286 station-year files (~306 MB raw, gitignored).
  **Observed kickoff weather covers 94-96% of outdoor games 2021-25** (77% of 2026 so far,
  limited by the lag). Domes have no weather. Live games use NWS `forecastHourly`
  (`python -m engine.cfb.weather.noaa forecast`), stamped at capture; the User-Agent contact
  is `edge-index.com` (override with `NWS_CONTACT`).
- **The historical weather test uses OBSERVED kickoff weather, which wasn't known at the
  open, so it flatters the backtest.** Live uses forecasts captured at bet time.
- **Result (2022-24 LOSO, 2,141 games with observed or indoor weather):** adding wind > 10 mph,
  cold < 45 °F and rain makes LOSO MAE slightly *worse* (12.726 vs 12.716; the open total is
  12.672). Coefficients have the expected signs but every CI spans 0: wind −0.20/mph
  [−0.44, +0.09], cold −0.09/°F [−0.30, +0.12], rain −2.0 [−5.3, +1.5].
- **Decision rule:** k_t for weeks 4+ pooled, with weather = **+0.12 [−0.11, +0.33]**, so
  the CI includes 0. **The 2025 totals holdout is NOT run.** Totals are **market-anchored**:
  centered on the market total, with σ_t = 10.90 + 0.094 × total (no recency weighting) and
  six key-total spikes (23, 41, 37, 51, 38, 55; ×1.5-1.9). The spikes were chosen inside each
  LOSO fold and improved held-out log-likelihood (−4.1835 vs −4.1881 with none). Frozen in
  `engine/cfb/totals/params.json`. **Totals legs are `PAPER-UNPROVEN` in 5E.**

## 4. Team totals (5C): calibration on 2022-24 team scores

Tim's spec: home = (market total + projected margin) / 2, away = (market total − projected
margin) / 2; bivariate normal with ρ = +0.075 (re-measured around the market total: also
+0.075). σ_M is the frozen spread σ and σ_T the frozen totals σ. **No new parameters.**

- **The 75-90% band is calibrated on both sides:** overs predicted 83.2%, actual 82.9%
  (**−0.3**, CI −1.4 to +0.6); unders 83.2% vs 83.0% (**−0.2**, CI −1.3 to +0.8). Every band
  is within ±1.0 pt.
- **Centers are unbiased** (mean residual +0.04 home, +0.23 away). The SD matches the model
  (11.46 vs 11.45 home, 10.63 vs 10.62 away).
- **Caveat:** exact team scores cluster on football numbers (7, 3, 10, 14 at 2.4-2.9× implied;
  24, 17, 31, 38 at 1.8-2.0×). Band calibration holds, but single rungs next to those numbers
  (e.g. 23.5 / 24.5) will be mispriced by a smooth distribution. A LOSO-fitted team-score
  spike set is the obvious fix if team-total legs reach a card. It's not done here.
- **DK capture extension (alt totals + alt team totals):** verified at **+2 credits per game**.
  Built, **off**, and pending approval (`docs/cfb/ODDS_BUDGET.md`). DK's implied totals and
  team-total ladder fits (σ, hold, reproduction error) need captured ladders first.

Detailed tables follow under "Results (generated)".

## Results (generated)

<!-- AUTO:ML:BEGIN -->
_Generated by `python -m engine.cfb.model.moneyline`. No new parameters. **Moneylines are CLOSING lines** (CFBD has no ML open), so all results are vs the close: conservative. Provider: Bovada 2022-25, DK 2026; DK 2023-25 cross-check. De-vig: proportional._

### Coverage

| eval_set | games | with_ml | with_dk_ml | mean_hold_pct |
|---|---|---|---|---|
| 2022-2024 LOSO | 2243 | 2117 | 1404 | 4.41 |
| 2025 holdout | 773 | 720 | 704 | 4.56 |
| 2026 to date | 329 | 313 | 313 | 4.11 |


### 65-90% band calibration (favorite side; the focus band ~ -185 to -900)

| set | who | n | pred_% | actual_% | gap_pts | ci95 |
|---|---|---|---|---|---|---|
| 2022-2024 LOSO | model | 1088 | 77.17 | 76.19 | -0.98 | -3.6 to +1.6 |
| 2022-2024 LOSO | book no-vig | 1236 | 77.05 | 77.35 | 0.29 | -2.0 to +2.7 |
| 2025 holdout | model | 387 | 76.24 | 75.97 | -0.27 | -4.4 to +3.8 |
| 2025 holdout | book no-vig | 428 | 75.68 | 76.40 | 0.72 | -3.0 to +4.6 |
| 2026 to date | model | 149 | 77.14 | 77.85 | 0.71 | -5.7 to +7.1 |
| 2026 to date | book no-vig | 159 | 77.41 | 81.76 | 4.35 | -1.8 to +10.1 |


### Model vs book no-vig: Brier and log loss (home side, one row per game)

| set | games | brier_model | brier_novig | logloss_model | logloss_novig |
|---|---|---|---|---|---|
| 2022-2024 LOSO | 2117 | 0.1857 | 0.1841 | 0.5516 | 0.5464 |
| 2022-2024 LOSO (vs DK) | 1404 | 0.1790 | 0.1776 | 0.5349 | 0.5291 |
| 2025 holdout | 720 | 0.1816 | 0.1820 | 0.5372 | 0.5408 |
| 2025 holdout (vs DK) | 704 | 0.1796 | 0.1811 | 0.5315 | 0.5370 |
| 2026 to date | 313 | 0.1562 | 0.1535 | 0.4750 | 0.4704 |


### Paper strategy: model - no-vig >= 3 pts AND EV > 0 at the posted (close) price

| set | band | bets | wins | win_% | avg_price | breakeven_% | roi_% | roi_ci95 |
|---|---|---|---|---|---|---|---|---|
| 2022-2024 LOSO | all | 915 | 474 | 51.8 | -110.0 | 52.9 | -0.7 | -8.0 to +7.4 |
| 2022-2024 LOSO | <= -300 | 182 | 141 | 77.5 | -550.0 | 85.0 | -9.2 | -16.7 to -2.0 |
| 2022-2024 LOSO | -300 to -150 | 157 | 101 | 64.3 | -200.0 | 67.0 | -3.8 | -15.2 to +7.1 |
| 2022-2024 LOSO | -150 to +150 | 270 | 142 | 52.6 | 100.0 | 50.0 | 6.8 | -5.6 to +18.6 |
| 2022-2024 LOSO | dogs > +150 | 306 | 90 | 29.4 | 235.0 | 29.2 | -0.7 | -19.0 to +18.2 |
| 2022-2024 LOSO (vs DK) | all | 699 | 391 | 55.9 | -135.0 | 55.9 | -0.9 | -9.1 to +7.2 |
| 2022-2024 LOSO (vs DK) | <= -300 | 166 | 135 | 81.3 | -550.0 | 84.9 | -4.5 | -12.0 to +2.2 |
| 2022-2024 LOSO (vs DK) | -300 to -150 | 138 | 93 | 67.4 | -205.0 | 67.4 | 0.2 | -11.4 to +11.4 |
| 2022-2024 LOSO (vs DK) | -150 to +150 | 198 | 112 | 56.6 | -112.0 | 51.7 | 10.5 | -3.3 to +23.6 |
| 2022-2024 LOSO (vs DK) | dogs > +150 | 197 | 51 | 25.9 | 250.0 | 27.5 | -10.2 | -32.3 to +13.1 |
| 2025 holdout | all | 255 | 140 | 54.9 | -130.0 | 55.1 | -2.4 | -15.2 to +10.7 |
| 2025 holdout | <= -300 | 49 | 44 | 89.8 | -500.0 | 83.6 | 6.8 | -4.0 to +15.9 |
| 2025 holdout | -300 to -150 | 58 | 40 | 69.0 | -210.0 | 67.1 | 3.5 | -14.7 to +21.1 |
| 2025 holdout | -150 to +150 | 72 | 35 | 48.6 | -120.0 | 52.3 | -8.7 | -31.2 to +12.6 |
| 2025 holdout | dogs > +150 | 76 | 21 | 27.6 | 210.0 | 30.2 | -7.0 | -39.2 to +28.0 |
| 2025 holdout (vs DK) | all | 332 | 188 | 56.6 | -122.0 | 54.1 | 4.3 | -7.3 to +16.6 |
| 2025 holdout (vs DK) | <= -300 | 69 | 62 | 89.9 | -500.0 | 84.3 | 6.8 | -2.5 to +15.3 |
| 2025 holdout (vs DK) | -300 to -150 | 74 | 51 | 68.9 | -192.0 | 66.5 | 4.0 | -13.0 to +20.0 |
| 2025 holdout (vs DK) | -150 to +150 | 85 | 45 | 52.9 | -102.0 | 50.3 | 6.4 | -16.0 to +28.1 |
| 2025 holdout (vs DK) | dogs > +150 | 104 | 30 | 28.8 | 230.0 | 28.3 | 1.0 | -30.7 to +31.9 |
| 2026 to date | all | 144 | 71 | 49.3 | 103.5 | 51.9 | -3.9 | -25.2 to +21.5 |
| 2026 to date | <= -300 | 27 | 25 | 92.6 | -600.0 | 86.6 | 7.6 | -6.1 to +17.8 |
| 2026 to date | -300 to -150 | 27 | 16 | 59.3 | -205.0 | 68.1 | -13.6 | -41.0 to +13.0 |
| 2026 to date | -150 to +150 | 37 | 17 | 45.9 | 105.0 | 50.0 | -7.3 | -41.8 to +24.8 |
| 2026 to date | dogs > +150 | 53 | 13 | 24.5 | 270.0 | 27.4 | -2.3 | -53.3 to +60.8 |


**Calibration, 2022-2024 LOSO** (model win %, favorite side, game-level bootstrap CI)

| bin | n | pred_% | actual_% | ci95_lo | ci95_hi | actual-pred |
|---|---|---|---|---|---|---|
| 50-60 | 453 | 55.5 | 50.8 | 46.1 | 55.6 | -4.7 |
| 60-65 | 268 | 62.5 | 64.2 | 57.8 | 69.8 | 1.7 |
| 65-70 | 245 | 67.7 | 67.3 | 62.0 | 73.1 | -0.4 |
| 70-75 | 201 | 72.5 | 75.6 | 69.7 | 81.6 | 3.1 |
| 75-80 | 232 | 77.3 | 75.9 | 70.3 | 81.0 | -1.4 |
| 80-85 | 207 | 82.6 | 78.3 | 72.9 | 84.1 | -4.4 |
| 85-90 | 203 | 87.6 | 85.7 | 80.3 | 90.2 | -1.8 |
| 90-95 | 201 | 92.5 | 90.5 | 86.6 | 94.0 | -1.9 |
| 95-100 | 107 | 96.5 | 94.4 | 89.7 | 98.1 | -2.1 |


**Calibration, 2025 holdout** (model win %, favorite side, game-level bootstrap CI)

| bin | n | pred_% | actual_% | ci95_lo | ci95_hi | actual-pred |
|---|---|---|---|---|---|---|
| 50-60 | 155 | 55.8 | 50.3 | 42.6 | 58.7 | -5.5 |
| 60-65 | 88 | 62.2 | 64.8 | 54.5 | 75.0 | 2.6 |
| 65-70 | 92 | 67.6 | 63.0 | 53.3 | 73.9 | -4.5 |
| 70-75 | 86 | 72.4 | 70.9 | 60.5 | 80.2 | -1.5 |
| 75-80 | 84 | 77.2 | 82.1 | 73.8 | 90.5 | 4.9 |
| 80-85 | 71 | 82.6 | 83.1 | 74.6 | 91.5 | 0.5 |
| 85-90 | 54 | 87.3 | 87.0 | 77.8 | 94.4 | -0.3 |
| 90-95 | 59 | 92.3 | 93.2 | 86.4 | 98.3 | 0.9 |
| 95-100 | 31 | 96.5 | 100.0 | 100.0 | 100.0 | 3.5 |


**Calibration, 2026 to date** (model win %, favorite side, game-level bootstrap CI)

| bin | n | pred_% | actual_% | ci95_lo | ci95_hi | actual-pred |
|---|---|---|---|---|---|---|
| 50-60 | 65 | 55.3 | 67.7 | 56.9 | 78.5 | 12.4 |
| 60-65 | 36 | 62.6 | 72.2 | 58.3 | 86.1 | 9.6 |
| 65-70 | 32 | 67.7 | 68.8 | 53.1 | 84.4 | 1.0 |
| 70-75 | 28 | 72.5 | 60.7 | 42.9 | 78.6 | -11.8 |
| 75-80 | 28 | 77.2 | 82.1 | 67.9 | 96.4 | 5.0 |
| 80-85 | 40 | 82.3 | 87.5 | 77.5 | 97.5 | 5.2 |
| 85-90 | 21 | 87.7 | 90.5 | 76.2 | 100.0 | 2.8 |
| 90-95 | 29 | 92.9 | 96.6 | 89.7 | 100.0 | 3.6 |
| 95-100 | 34 | 97.0 | 97.1 | 91.2 | 100.0 | 0.1 |


### ML/spread consistency (book's own close spread through our distribution vs its no-vig ML)

| set | games | mean_|diff|_pts | disagree_ge3 | brier_spread_implied (disagreements) | brier_ml_novig (disagreements) | spread-favored side won_% | mean_pred_spread_side_% | mean_pred_ml_side_% |
|---|---|---|---|---|---|---|---|---|
| 2022-2024 LOSO | 2117 | 2.7669 | 735 | 0.1786 | 0.1772 | 58.7755 | 60.7022 | 55.4969 |
| 2025 holdout | 720 | 3.2779 | 330 | 0.1827 | 0.1804 | 56.0606 | 61.4964 | 56.0854 |
| 2026 to date | 313 | 1.4557 | 21 | 0.2070 | 0.1968 | 42.8571 | 58.0564 | 54.5164 |


By spread size (spread-implied minus ML no-vig, home perspective):

| |close spread| | games | spread_minus_ml_pts | home_win_pct | set |
|---|---|---|---|---|
| (-0.1, 3.0] | 479 | -0.02 | 49.48 | 2022-2024 LOSO |
| (3.0, 7.0] | 530 | -0.34 | 56.23 | 2022-2024 LOSO |
| (7.0, 10.0] | 278 | -0.47 | 46.04 | 2022-2024 LOSO |
| (10.0, 14.0] | 289 | -0.20 | 59.17 | 2022-2024 LOSO |
| (14.0, 21.0] | 335 | 0.70 | 67.16 | 2022-2024 LOSO |
| (21.0, 60.0] | 206 | 1.53 | 72.33 | 2022-2024 LOSO |
| (-0.1, 3.0] | 161 | -0.51 | 53.42 | 2025 holdout |
| (3.0, 7.0] | 219 | -0.53 | 51.60 | 2025 holdout |
| (7.0, 10.0] | 87 | -0.29 | 52.87 | 2025 holdout |
| (10.0, 14.0] | 97 | 0.57 | 59.79 | 2025 holdout |
| (14.0, 21.0] | 97 | 1.35 | 63.92 | 2025 holdout |
| (21.0, 60.0] | 59 | 2.11 | 81.36 | 2025 holdout |
| (-0.1, 3.0] | 63 | -0.07 | 50.79 | 2026 to date |
| (3.0, 7.0] | 77 | -0.16 | 51.95 | 2026 to date |
| (7.0, 10.0] | 39 | -0.72 | 61.54 | 2026 to date |
| (10.0, 14.0] | 40 | -0.04 | 55.00 | 2026 to date |
| (14.0, 21.0] | 47 | 0.81 | 74.47 | 2026 to date |
| (21.0, 60.0] | 47 | 1.23 | 82.98 | 2026 to date |

<!-- AUTO:ML:END -->

<!-- AUTO:TEAMTOTALS:BEGIN -->
_Generated by `python -m engine.cfb.totals.team_totals` (2022-24, LOSO projected margin; market total = provider open; 2237 games, 4474 team scores)._

Residual correlation (margin, total) measured around the MARKET total: **+0.075** (model-total version +0.075, used per Tim).

**75-90% band, over vs under (game-clustered CI)**

| kind | pairs | games | pred_% | actual_% | gap_pts | ci95 |
|---|---|---|---|---|---|---|
| over | 29433 | 2237 | 83.19 | 82.88 | -0.32 | -1.4 to +0.6 |
| under | 29976 | 2237 | 83.23 | 83.02 | -0.21 | -1.3 to +0.8 |


**Centering and spread**

| home_mean_resid | away_mean_resid | home_sd_resid | away_sd_resid | home_model_sd | away_model_sd |
|---|---|---|---|---|---|
| 0.04 | 0.23 | 11.46 | 10.63 | 11.45 | 10.62 |


**Reliability by band**

| kind | bin | n | pred | actual | gap |
|---|---|---|---|---|---|
| over | 50-60 | 12488 | 55.0 | 54.0 | -1.0 |
| over | 60-70 | 13393 | 65.1 | 64.5 | -0.6 |
| over | 70-75 | 7397 | 72.5 | 71.6 | -0.9 |
| over | 75-80 | 8171 | 77.6 | 76.7 | -0.8 |
| over | 80-85 | 9462 | 82.6 | 82.2 | -0.4 |
| over | 85-90 | 11800 | 87.6 | 87.7 | 0.1 |
| over | 90-95 | 16526 | 92.7 | 93.0 | 0.4 |
| over | 95-100 | 10243 | 97.4 | 97.8 | 0.4 |
| under | 50-60 | 12506 | 55.0 | 55.8 | 0.7 |
| under | 60-70 | 13384 | 65.1 | 65.7 | 0.6 |
| under | 70-75 | 7404 | 72.5 | 72.9 | 0.3 |
| under | 75-80 | 8237 | 77.5 | 77.9 | 0.4 |
| under | 80-85 | 9639 | 82.6 | 82.6 | 0.0 |
| under | 85-90 | 12100 | 87.6 | 86.8 | -0.8 |
| under | 90-95 | 17962 | 92.7 | 92.3 | -0.5 |
| under | 95-100 | 12722 | 96.3 | 95.6 | -0.7 |


<details><summary>Exact team scores: observed vs implied (key scores)</summary>


| score | observed_% | implied_% | ratio |
|---|---|---|---|
| 7 | 3.02 | 1.04 | 2.91 |
| 3 | 1.72 | 0.63 | 2.72 |
| 10 | 3.76 | 1.41 | 2.67 |
| 14 | 4.74 | 1.94 | 2.44 |
| 45 | 2.37 | 1.15 | 2.05 |
| 24 | 5.90 | 2.91 | 2.03 |
| 17 | 4.60 | 2.33 | 1.98 |
| 49 | 1.48 | 0.76 | 1.95 |
| 38 | 3.73 | 2.02 | 1.85 |
| 31 | 4.87 | 2.76 | 1.76 |
| 13 | 3.17 | 1.81 | 1.75 |
| 41 | 2.70 | 1.64 | 1.65 |
| 20 | 4.38 | 2.65 | 1.65 |
| 42 | 2.46 | 1.51 | 1.63 |
| 27 | 4.54 | 2.94 | 1.54 |


</details>

<!-- AUTO:TEAMTOTALS:END -->
