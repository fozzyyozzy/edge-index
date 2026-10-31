# Calibration study, 2026 (SHADOW ONLY, not live)

Research report: nothing here changes the live card, the Legs board, the record or the newsletter.

## Verdict

**calib does NOT beat the DK-only baseline.** Leave-one-week-out pooled log loss 0.5087 (model) vs 0.4866 (DK no-vig, refit) vs 0.4848 (DK no-vig, raw); difference +0.0221 per rung, 90% week-bootstrap interval [+0.0120, +0.0344]. Brier 0.1654 vs 0.1577 (refit) vs 0.1570 (raw).

Walk-forward (train on earlier weeks only, the version a live card could have used; weeks 4, 5, 6, 7, 8): log loss 0.5322 model vs 0.5077 DK refit vs 0.5010 DK raw.

## Data

3302 settled, priced rungs from the pregame Legs boards, weeks 3-8 (week 1-2 have no boards; week 8 has TNF only so far). Base hit rate 77.6%. Voids (no box-score row) dropped. Held rows have no price on the board and aren't in the data.

Board version used per slate (last generated before the slate's first kickoff; 'working file' = the current file qualifies; a sha = an older git version, because the current file was regenerated after kickoff):

| slate | source |
|---|---|
| w3 mnf | working file |
| w3 sun | working file |
| w3 tnf | working file |
| w4 mnf | working file |
| w4 sun | working file |
| w4 tnf | working file |
| w5 mnf | working file |
| w5 sun | working file |
| w5 tnf | working file |
| w6 mnf | working file |
| w6 sun | ec6fcb07 |
| w6 tnf | working file |
| w7 mnf | working file |
| w7 sun | e22356c8 |
| w7 tnf | working file |
| w8 sun | working file |
| w8 tnf | working file |

Role trend needs 4+ current-season games (last 2 vs up to 4 before); 43% of rungs have none (mostly weeks 3-4) and get a missing indicator.

## Model vs DK, leave-one-week-out

| week | rungs | hit | ll_model | ll_dk_refit | ll_dk_raw | brier_model | brier_dk_refit | brier_dk_raw | model_better |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 659 | 82.9% | 0.4205 | 0.4178 | 0.4196 | 0.1314 | 0.1291 | 0.1294 | NO |
| 4 | 651 | 79.3% | 0.513 | 0.4926 | 0.4905 | 0.1641 | 0.1594 | 0.1586 | NO |
| 5 | 584 | 77.9% | 0.5132 | 0.4925 | 0.4921 | 0.1691 | 0.1608 | 0.1604 | NO |
| 6 | 542 | 75.5% | 0.5385 | 0.4849 | 0.4858 | 0.1769 | 0.1585 | 0.1584 | NO |
| 7 | 817 | 72.8% | 0.5629 | 0.5437 | 0.5357 | 0.1874 | 0.1806 | 0.1781 | NO |
| 8 | 49 | 83.7% | 0.3523 | 0.3268 | 0.3382 | 0.1 | 0.0942 | 0.0972 | NO |
| pooled | 3302 | 77.6% | 0.5087 | 0.4866 | 0.4848 | 0.1654 | 0.1577 | 0.157 | NO |

L2 sensitivity (pooled LOWO log loss; the model uses lambda = 1):

| lam | ll_model | ll_dk_refit |
|---|---|---|
| 0.1 | 0.509 | 0.4866 |
| 1.0 | 0.5087 | 0.4866 |
| 10.0 | 0.5064 | 0.4866 |
| 100.0 | 0.4981 | 0.488 |

Feature groups added to DK alone (pooled LOWO; diagnostic only, not used to pick the model):

| features | ll | brier |
|---|---|---|
| DK only | 0.4866 | 0.1577 |
| DK + L10/L15 | 0.4899 | 0.1591 |
| DK + market/position | 0.4898 | 0.1589 |
| DK + role trend + flags | 0.489 | 0.1583 |
| full model | 0.5087 | 0.1654 |

## Reliability (pooled, out-of-week)

| source | bin | n | predicted | actual |
|---|---|---|---|---|
| model | 0.00-0.50 | 235 | 38.2% | 55.3% |
| model | 0.50-0.60 | 237 | 55.4% | 61.6% |
| model | 0.60-0.70 | 388 | 65.6% | 66.5% |
| model | 0.70-0.75 | 294 | 72.7% | 71.4% |
| model | 0.75-0.80 | 372 | 77.7% | 80.1% |
| model | 0.80-0.85 | 423 | 82.7% | 80.9% |
| model | 0.85-0.90 | 612 | 87.5% | 85.3% |
| model | 0.90-1.00 | 741 | 92.9% | 88.5% |
| DK refit | 0.00-0.50 | 143 | 41.9% | 48.3% |
| DK refit | 0.50-0.60 | 213 | 55.0% | 54.0% |
| DK refit | 0.60-0.70 | 441 | 65.7% | 63.9% |
| DK refit | 0.70-0.75 | 366 | 72.7% | 72.4% |
| DK refit | 0.75-0.80 | 417 | 77.4% | 76.3% |
| DK refit | 0.80-0.85 | 495 | 82.6% | 83.4% |
| DK refit | 0.85-0.90 | 646 | 87.7% | 88.4% |
| DK refit | 0.90-1.00 | 581 | 91.9% | 91.0% |
| DK raw | 0.00-0.50 | 127 | 42.5% | 45.7% |
| DK raw | 0.50-0.60 | 234 | 54.7% | 55.1% |
| DK raw | 0.60-0.70 | 509 | 65.5% | 64.4% |
| DK raw | 0.70-0.75 | 451 | 72.5% | 73.2% |
| DK raw | 0.75-0.80 | 422 | 77.4% | 79.9% |
| DK raw | 0.80-0.85 | 559 | 82.4% | 84.3% |
| DK raw | 0.85-0.90 | 695 | 87.5% | 89.8% |
| DK raw | 0.90-1.00 | 305 | 90.9% | 93.4% |

## Hit rate by calib grade (out-of-week)

A+ >= .85, A >= .80, A- >= .75, B >= .68, C >= .60, D below.

| grade | n | model | dk_novig | hit |
|---|---|---|---|---|
| A+ | 1353 | 90.5% | 85.8% | 87.1% |
| A | 423 | 82.7% | 79.0% | 80.9% |
| A- | 372 | 77.7% | 75.7% | 80.1% |
| B | 402 | 71.7% | 71.2% | 71.6% |
| C | 280 | 64.3% | 66.8% | 64.3% |
| D | 472 | 46.8% | 56.4% | 58.5% |

## Coefficients (fit on every labelled week; per standard deviation of the feature)

| feature | coef_per_sd | mean | sd |
|---|---|---|---|
| novig | 0.735 | 1.277 | 0.691 |
| m_rush_yds | -0.23 | 0.169 | 0.375 |
| spread | 0.151 | -0.552 | 4.959 |
| pos_TE | -0.144 | 0.127 | 0.333 |
| oppd_rank | 0.136 | 0.518 | 0.276 |
| car_logratio | 0.136 | 0.004 | 0.127 |
| m_rush_att | -0.134 | 0.094 | 0.292 |
| role_na | 0.126 | 0.432 | 0.495 |
| l10 | 0.117 | 1.26 | 0.666 |
| m_pass_att | -0.075 | 0.082 | 0.274 |
| pos_QB | 0.074 | 0.365 | 0.481 |
| pos_RB | 0.071 | 0.266 | 0.442 |
| vol_rank | 0.07 | 0.385 | 0.269 |
| game_total | 0.065 | 44.901 | 3.211 |
| gt_na | 0.046 | 0.581 | 0.493 |
| tt_na | 0.046 | 0.581 | 0.493 |
| inj_watch | -0.039 | 0.028 | 0.164 |
| snap_delta | 0.035 | 0.013 | 0.084 |
| m_pass_cmps | -0.023 | 0.06 | 0.237 |
| l15 | -0.017 | 1.279 | 0.743 |
| qb_change | -0.016 | 0.035 | 0.183 |
| team_total | 0.011 | 22.552 | 2.389 |
| m_receptions | 0.01 | 0.162 | 0.369 |
| m_pass_yds | 0.004 | 0.18 | 0.384 |
| tgt_logratio | 0.004 | 0.026 | 0.221 |
| pos_other | 0.0 | 0.0 | 1.0 |
| oppd_na | 0.0 | 0.0 | 1.0 |
| vol_na | 0.0 | 0.0 | 1.0 |
| spread_na | 0.0 | 0.0 | 1.0 |
| (intercept) | 1.426 |  |  |

## Role down: threshold study (out-of-week model predictions)

Fires when, for snap share or the market's volume (targets / carries), BOTH of the last two games are below the prior-games average by more than the threshold (relative; prior role at least 20% snaps / 2 per game). shortfall = model minus actual on the flagged rungs (positive = they hit less than predicted).

| threshold | player_markets | rungs | hit | model | dk | shortfall_vs_model | shortfall_vs_dk | se |
|---|---|---|---|---|---|---|---|---|
| 15% | 115/677 (17.0%) | 265 | 72.8% | 69.7% | 75.5% | -3.2 | 2.7 | 2.7 |
| 20% | 73/677 (10.8%) | 180 | 67.8% | 67.8% | 74.2% | -0.0 | 6.5 | 3.5 |
| 25% | 54/677 (8.0%) | 134 | 61.9% | 66.1% | 73.8% | 4.2 | 11.8 | 4.2 |
| 30% | 45/677 (6.6%) | 109 | 67.0% | 65.1% | 73.2% | -1.9 | 6.2 | 4.5 |
| 40% | 28/677 (4.1%) | 59 | 67.8% | 61.8% | 74.8% | -6.0 | 7.0 | 6.1 |
| 50% | 10/677 (1.5%) | 17 | 70.6% | 53.4% | 67.2% | -17.2 | -3.3 | 11.1 |

calib uses threshold 25% (calib.ROLE_DOWN): the only one where flagged rungs hit below both the model and DK. It was picked after looking at this table (6 thresholds tried, ~1 SE), so treat it as a hypothesis (CLAUDE.md rule 5).

## Retro cards, weeks 4-8, played slates (IN-SAMPLE for calib's fit choices)

Each slate rebuilt offline from the files at its card's publish commit (no odds pull). live = the card as published. calib uses a model fit with that week left out (so weeks 4-7 are scored by a model that saw later weeks; week 8's model is weeks 3-7 only, the walk-forward one). Every card scored the same way: all legs clear = win at the card's estimated payout, any miss = loss (receipts use real closing prices; these won't match the record to the cent).

| variant | slates | tickets | no_ticket | record | units | roi |
|---|---|---|---|---|---|---|
| live | 13 | 14 | 5 | 2-12 | -9.17 | -65.5% |
| legacy | 13 | 16 | 4 | 4-12 | -6.18 | -38.6% |
| m20 | 13 | 11 | 6 | 2-9 | -4.71 | -42.8% |
| m40e0 | 13 | 10 | 6 | 1-9 | -8.03 | -80.3% |
| m40em1 | 13 | 12 | 5 | 3-9 | -3.65 | -30.4% |
| pfirst_norole | 13 | 20 | 1 | 7-13 | -3.75 | -18.8% |
| pfirst | 13 | 20 | 1 | 8-12 | -1.24 | -6.2% |
| pfirst_dog | 13 | 20 | 1 | 8-12 | -1.88 | -9.4% |
| calib | 13 | 20 | 1 | 5-15 | -8.82 | -44.1% |

### By slate

| slate | variant | commit | tickets | W | L | V | units | role_down_cands |
|---|---|---|---|---|---|---|---|---|
| w4 tnf | live | 64881c57 | 0 | 0 | 0 | 0 | 0 |  |
| w4 tnf | legacy | 64881c57 | 1 | 1 | 0 | 0 | 0.68 |  |
| w4 tnf | m20 | 64881c57 | 0 | 0 | 0 | 0 | 0 |  |
| w4 tnf | m40e0 | 64881c57 | 0 | 0 | 0 | 0 | 0 |  |
| w4 tnf | m40em1 | 64881c57 | 0 | 0 | 0 | 0 | 0 |  |
| w4 tnf | pfirst_norole | 64881c57 | 1 | 1 | 0 | 0 | 1.76 |  |
| w4 tnf | pfirst | 64881c57 | 1 | 1 | 0 | 0 | 1.76 |  |
| w4 tnf | pfirst_dog | 64881c57 | 1 | 1 | 0 | 0 | 1.76 |  |
| w4 tnf | calib | 64881c57 | 1 | 1 | 0 | 0 | 1.76 | 0 |
| w4 sun | live | a1d71f9c | 2 | 0 | 2 | 0 | -2.0 |  |
| w4 sun | legacy | a1d71f9c | 3 | 1 | 2 | 0 | 0.31 |  |
| w4 sun | m20 | a1d71f9c | 2 | 0 | 2 | 0 | -2.0 |  |
| w4 sun | m40e0 | a1d71f9c | 2 | 0 | 2 | 0 | -2.0 |  |
| w4 sun | m40em1 | a1d71f9c | 2 | 1 | 1 | 0 | 1.31 |  |
| w4 sun | pfirst_norole | a1d71f9c | 3 | 0 | 3 | 0 | -3.0 |  |
| w4 sun | pfirst | a1d71f9c | 3 | 0 | 3 | 0 | -3.0 |  |
| w4 sun | pfirst_dog | a1d71f9c | 3 | 0 | 3 | 0 | -3.0 |  |
| w4 sun | calib | a1d71f9c | 3 | 0 | 3 | 0 | -3.0 | 0 |
| w4 mnf | live | 2d932a2d | 0 | 0 | 0 | 0 | 0 |  |
| w4 mnf | legacy | 2d932a2d | 0 | 0 | 0 | 0 | 0 |  |
| w4 mnf | m20 | 2d932a2d | 0 | 0 | 0 | 0 | 0 |  |
| w4 mnf | m40e0 | 2d932a2d | 0 | 0 | 0 | 0 | 0 |  |
| w4 mnf | m40em1 | 2d932a2d | 0 | 0 | 0 | 0 | 0 |  |
| w4 mnf | pfirst_norole | 2d932a2d | 1 | 1 | 0 | 0 | 0.69 |  |
| w4 mnf | pfirst | 2d932a2d | 1 | 1 | 0 | 0 | 0.69 |  |
| w4 mnf | pfirst_dog | 2d932a2d | 1 | 1 | 0 | 0 | 0.69 |  |
| w4 mnf | calib | 2d932a2d | 1 | 1 | 0 | 0 | 0.63 | 0 |
| w5 tnf | live | fdfc4128 | 1 | 1 | 0 | 0 | 0.97 |  |
| w5 tnf | legacy | fdfc4128 | 1 | 1 | 0 | 0 | 0.97 |  |
| w5 tnf | m20 | fdfc4128 | 1 | 1 | 0 | 0 | 0.97 |  |
| w5 tnf | m40e0 | fdfc4128 | 1 | 1 | 0 | 0 | 0.97 |  |
| w5 tnf | m40em1 | fdfc4128 | 1 | 1 | 0 | 0 | 0.97 |  |
| w5 tnf | pfirst_norole | fdfc4128 | 1 | 1 | 0 | 0 | 1.55 |  |
| w5 tnf | pfirst | fdfc4128 | 1 | 1 | 0 | 0 | 1.55 |  |
| w5 tnf | pfirst_dog | fdfc4128 | 1 | 0 | 1 | 0 | -1.0 |  |
| w5 tnf | calib | fdfc4128 | 1 | 0 | 1 | 0 | -1.0 | 0 |
| w5 sun | live | 27945be7 | 2 | 1 | 1 | 0 | 0.86 |  |
| w5 sun | legacy | 27945be7 | 2 | 1 | 1 | 0 | 0.86 |  |
| w5 sun | m20 | 27945be7 | 2 | 1 | 1 | 0 | 2.32 |  |
| w5 sun | m40e0 | 27945be7 | 2 | 0 | 2 | 0 | -2.0 |  |
| w5 sun | m40em1 | 27945be7 | 2 | 1 | 1 | 0 | 1.07 |  |
| w5 sun | pfirst_norole | 27945be7 | 3 | 2 | 1 | 0 | 2.07 |  |
| w5 sun | pfirst | 27945be7 | 3 | 2 | 1 | 0 | 2.07 |  |
| w5 sun | pfirst_dog | 27945be7 | 3 | 2 | 1 | 0 | 2.07 |  |
| w5 sun | calib | 27945be7 | 3 | 0 | 3 | 0 | -3.0 | 2 |
| w5 mnf | live | 3c7c21db | 1 | 0 | 1 | 0 | -1.0 |  |
| w5 mnf | legacy | 3c7c21db | 1 | 0 | 1 | 0 | -1.0 |  |
| w5 mnf | m20 | 3c7c21db | 1 | 0 | 1 | 0 | -1.0 |  |
| w5 mnf | m40e0 | 3c7c21db | 1 | 0 | 1 | 0 | -1.0 |  |
| w5 mnf | m40em1 | 3c7c21db | 1 | 0 | 1 | 0 | -1.0 |  |
| w5 mnf | pfirst_norole | 3c7c21db | 1 | 1 | 0 | 0 | 1.61 |  |
| w5 mnf | pfirst | 3c7c21db | 1 | 1 | 0 | 0 | 1.61 |  |
| w5 mnf | pfirst_dog | 3c7c21db | 1 | 1 | 0 | 0 | 1.61 |  |
| w5 mnf | calib | 3c7c21db | 1 | 0 | 1 | 0 | -1.0 | 0 |
| w6 tnf | live | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | legacy | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | m20 | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | m40e0 | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | m40em1 | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | pfirst_norole | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | pfirst | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | pfirst_dog | e3720d79 | 0 | 0 | 0 | 0 | 0 |  |
| w6 tnf | calib | e3720d79 | 0 | 0 | 0 | 0 | 0 | 0 |
| w6 sun | live | 7bcf5db2 | 3 | 0 | 3 | 0 | -3.0 |  |
| w6 sun | legacy | 7bcf5db2 | 3 | 0 | 3 | 0 | -3.0 |  |
| w6 sun | m20 | 7bcf5db2 | 2 | 0 | 2 | 0 | -2.0 |  |
| w6 sun | m40e0 | 7bcf5db2 | 1 | 0 | 1 | 0 | -1.0 |  |
| w6 sun | m40em1 | 7bcf5db2 | 2 | 0 | 2 | 0 | -2.0 |  |
| w6 sun | pfirst_norole | 7bcf5db2 | 3 | 0 | 3 | 0 | -3.0 |  |
| w6 sun | pfirst | 7bcf5db2 | 3 | 0 | 3 | 0 | -3.0 |  |
| w6 sun | pfirst_dog | 7bcf5db2 | 3 | 0 | 3 | 0 | -3.0 |  |
| w6 sun | calib | 7bcf5db2 | 3 | 2 | 1 | 0 | 2.1 | 3 |
| w6 mnf | live | ff4cec6b | 0 | 0 | 0 | 0 | 0 |  |
| w6 mnf | legacy | ff4cec6b | 0 | 0 | 0 | 0 | 0 |  |
| w6 mnf | m20 | ff4cec6b | 0 | 0 | 0 | 0 | 0 |  |
| w6 mnf | m40e0 | ff4cec6b | 0 | 0 | 0 | 0 | 0 |  |
| w6 mnf | m40em1 | ff4cec6b | 0 | 0 | 0 | 0 | 0 |  |
| w6 mnf | pfirst_norole | ff4cec6b | 1 | 0 | 1 | 0 | -1.0 |  |
| w6 mnf | pfirst | ff4cec6b | 1 | 0 | 1 | 0 | -1.0 |  |
| w6 mnf | pfirst_dog | ff4cec6b | 1 | 1 | 0 | 0 | 0.91 |  |
| w6 mnf | calib | ff4cec6b | 1 | 0 | 1 | 0 | -1.0 | 0 |
| w7 tnf | live | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 tnf | legacy | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 tnf | m20 | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 tnf | m40e0 | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 tnf | m40em1 | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 tnf | pfirst_norole | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 tnf | pfirst | 2ae22351 | 1 | 1 | 0 | 0 | 1.51 |  |
| w7 tnf | pfirst_dog | 2ae22351 | 1 | 1 | 0 | 0 | 1.51 |  |
| w7 tnf | calib | 2ae22351 | 1 | 0 | 1 | 0 | -1.0 | 1 |
| w7 sun | live | 3aac87e3 | 3 | 0 | 3 | 0 | -3.0 |  |
| w7 sun | legacy | 3aac87e3 | 3 | 0 | 3 | 0 | -3.0 |  |
| w7 sun | m20 | 3aac87e3 | 2 | 0 | 2 | 0 | -2.0 |  |
| w7 sun | m40e0 | 3aac87e3 | 2 | 0 | 2 | 0 | -2.0 |  |
| w7 sun | m40em1 | 3aac87e3 | 2 | 0 | 2 | 0 | -2.0 |  |
| w7 sun | pfirst_norole | 3aac87e3 | 3 | 0 | 3 | 0 | -3.0 |  |
| w7 sun | pfirst | 3aac87e3 | 3 | 0 | 3 | 0 | -3.0 |  |
| w7 sun | pfirst_dog | 3aac87e3 | 3 | 0 | 3 | 0 | -3.0 |  |
| w7 sun | calib | 3aac87e3 | 3 | 0 | 3 | 0 | -3.0 | 4 |
| w7 mnf | live | 78afa1e7 | 0 | 0 | 0 | 0 | 0 |  |
| w7 mnf | legacy | 78afa1e7 | 0 | 0 | 0 | 0 | 0 |  |
| w7 mnf | m20 | 78afa1e7 | 0 | 0 | 0 | 0 | 0 |  |
| w7 mnf | m40e0 | 78afa1e7 | 0 | 0 | 0 | 0 | 0 |  |
| w7 mnf | m40em1 | 78afa1e7 | 0 | 0 | 0 | 0 | 0 |  |
| w7 mnf | pfirst_norole | 78afa1e7 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 mnf | pfirst | 78afa1e7 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 mnf | pfirst_dog | 78afa1e7 | 1 | 0 | 1 | 0 | -1.0 |  |
| w7 mnf | calib | 78afa1e7 | 1 | 0 | 1 | 0 | -1.0 | 0 |
| w8 tnf | live | 1d7a0512 | 1 | 0 | 1 | 0 | -1.0 |  |
| w8 tnf | legacy | 1d7a0512 | 1 | 0 | 1 | 0 | -1.0 |  |
| w8 tnf | m20 | 1d7a0512 | 0 | 0 | 0 | 0 | 0 |  |
| w8 tnf | m40e0 | 1d7a0512 | 0 | 0 | 0 | 0 | 0 |  |
| w8 tnf | m40em1 | 1d7a0512 | 1 | 0 | 1 | 0 | -1.0 |  |
| w8 tnf | pfirst_norole | 1d7a0512 | 1 | 1 | 0 | 0 | 0.57 |  |
| w8 tnf | pfirst | 1d7a0512 | 1 | 1 | 0 | 0 | 0.57 |  |
| w8 tnf | pfirst_dog | 1d7a0512 | 1 | 1 | 0 | 0 | 0.57 |  |
| w8 tnf | calib | 1d7a0512 | 1 | 1 | 0 | 0 | 0.69 | 1 |

### Tickets

| slate | variant | ticket | result | units | payout | model | legs |
|---|---|---|---|---|---|---|---|
| w4 tnf | legacy | TNF-1 | WIN | 0.68 | -147 | 0.651 | DK Metcalf 3+ receptions (-344) / Harold Fannin Jr. 25+ rec_yds (-330) |
| w4 tnf | pfirst_norole | TNF-1 | WIN | 1.76 | +176 | 0.365 | DK Metcalf 3+ receptions (-344) / Harold Fannin Jr. 25+ rec_yds (-330) / Pat Freiermuth 15+ rec_yds (-378) / Deshaun Watson 16+ pass_cmps (-337) |
| w4 tnf | pfirst | TNF-1 | WIN | 1.76 | +176 | 0.365 | DK Metcalf 3+ receptions (-344) / Harold Fannin Jr. 25+ rec_yds (-330) / Pat Freiermuth 15+ rec_yds (-378) / Deshaun Watson 16+ pass_cmps (-337) |
| w4 tnf | pfirst_dog | TNF-1 | WIN | 1.76 | +176 | 0.365 | DK Metcalf 3+ receptions (-344) / Harold Fannin Jr. 25+ rec_yds (-330) / Pat Freiermuth 15+ rec_yds (-378) / Deshaun Watson 16+ pass_cmps (-337) |
| w4 tnf | calib | TNF-1 | WIN | 1.76 | +176 | 0.403 | Deshaun Watson 16+ pass_cmps (-337) / DK Metcalf 3+ receptions (-344) / Harold Fannin Jr. 25+ rec_yds (-330) / Pat Freiermuth 15+ rec_yds (-378) |
| w4 sun | live | SUN-1 | LOSS | -1.0 | +217 | 0.407 | Jakobi Meyers 25+ rec_yds (-295) / Kyren Williams 40+ rush_yds (-349) / Cooper Kupp 15+ rec_yds (-256) / Christian McCaffrey 4+ receptions (-309) |
| w4 sun | live | SUN-2 | LOSS | -1.0 | +233 | 0.377 | Kyren Williams 40+ rush_yds (-349) / Jaxon Smith-Njigba 70+ rec_yds (-269) / Brian Thomas Jr 2+ receptions (-256) / Jacoby Brissett 200+ pass_yds (-280) |
| w4 sun | legacy | SUN-1 | LOSS | -1.0 | +217 | 0.407 | Jakobi Meyers 25+ rec_yds (-295) / Kyren Williams 40+ rush_yds (-349) / Cooper Kupp 15+ rec_yds (-256) / Christian McCaffrey 4+ receptions (-309) |
| w4 sun | legacy | SUN-2 | WIN | 2.31 | +231 | 0.378 | Kyren Williams 40+ rush_yds (-349) / Jaxon Smith-Njigba 70+ rec_yds (-269) / Brian Thomas Jr 2+ receptions (-256) / Cade Otton 15+ rec_yds (-287) |
| w4 sun | legacy | SUN-3 | LOSS | -1.0 | +389 | 0.342 | Jacoby Brissett 200+ pass_yds (-280) / Ty Johnson 5+ rush_yds (-107) / Jaylin Noel 12+ rec_yds (-116) |
| w4 sun | m20 | SUN-1 | LOSS | -1.0 | +144 | 0.485 | Kyren Williams 40+ rush_yds (-349) / Jakobi Meyers 25+ rec_yds (-295) / Omarion Hampton 12+ rush_att (-241) |
| w4 sun | m20 | SUN-2 | LOSS | -1.0 | +307 | 0.331 | Kyren Williams 40+ rush_yds (-349) / Jaxon Smith-Njigba 7+ receptions (-157) / Ty Johnson 5+ rush_yds (-107) |
| w4 sun | m40e0 | SUN-1 | LOSS | -1.0 | +182 | 0.364 | Jakobi Meyers 25+ rec_yds (-295) / Kyren Williams 40+ rush_yds (-349) / Jaxon Smith-Njigba 7+ receptions (-157) |
| w4 sun | m40e0 | SUN-2 | LOSS | -1.0 | +239 | 0.322 | Kyren Williams 40+ rush_yds (-349) / Jaylin Noel 12+ rec_yds (-116) / Omarion Hampton 12+ rush_att (-241) |
| w4 sun | m40em1 | SUN-1 | LOSS | -1.0 | +217 | 0.315 | Jakobi Meyers 25+ rec_yds (-295) / Kyren Williams 40+ rush_yds (-349) / Cooper Kupp 15+ rec_yds (-256) / Christian McCaffrey 4+ receptions (-309) |
| w4 sun | m40em1 | SUN-2 | WIN | 2.31 | +231 | 0.294 | Kyren Williams 40+ rush_yds (-349) / Jaxon Smith-Njigba 70+ rec_yds (-269) / Brian Thomas Jr 2+ receptions (-256) / Cade Otton 15+ rec_yds (-287) |
| w4 sun | pfirst_norole | SUN-1 | LOSS | -1.0 | +151 | 0.497 | Jakobi Meyers 25+ rec_yds (-295) / Christian McCaffrey 4+ receptions (-309) / Omarion Hampton 12+ rush_att (-241) |
| w4 sun | pfirst_norole | SUN-2 | LOSS | -1.0 | +153 | 0.495 | Kyren Williams 40+ rush_yds (-349) / Brian Thomas Jr 2+ receptions (-256) / Omarion Hampton 12+ rush_att (-241) |
| w4 sun | pfirst_norole | SUN-3 | LOSS | -1.0 | +151 | 0.439 | Cooper Kupp 15+ rec_yds (-256) / Cade Otton 15+ rec_yds (-287) / TreVeyon Henderson 8+ rush_att (-294) |
| w4 sun | pfirst | SUN-1 | LOSS | -1.0 | +151 | 0.497 | Jakobi Meyers 25+ rec_yds (-295) / Christian McCaffrey 4+ receptions (-309) / Omarion Hampton 12+ rush_att (-241) |
| w4 sun | pfirst | SUN-2 | LOSS | -1.0 | +153 | 0.495 | Kyren Williams 40+ rush_yds (-349) / Brian Thomas Jr 2+ receptions (-256) / Omarion Hampton 12+ rush_att (-241) |
| w4 sun | pfirst | SUN-3 | LOSS | -1.0 | +151 | 0.439 | Cooper Kupp 15+ rec_yds (-256) / Cade Otton 15+ rec_yds (-287) / TreVeyon Henderson 8+ rush_att (-294) |
| w4 sun | pfirst_dog | SUN-1 | LOSS | -1.0 | +153 | 0.484 | Jakobi Meyers 25+ rec_yds (-295) / Cooper Kupp 2+ receptions (-294) / Kyren Williams 12+ rush_att (-245) |
| w4 sun | pfirst_dog | SUN-2 | LOSS | -1.0 | +151 | 0.46 | Cooper Kupp 2+ receptions (-294) / Cade Otton 15+ rec_yds (-287) / Brian Thomas Jr 2+ receptions (-256) |
| w4 sun | pfirst_dog | SUN-3 | LOSS | -1.0 | +150 | 0.404 | Xavier Worthy 15+ rec_yds (-446) / Jaxon Smith-Njigba 60+ rec_yds (-411) / Christian McCaffrey 4+ receptions (-309) / Chris Godwin 2+ receptions (-414) |
| w4 sun | calib | SUN-1 | LOSS | -1.0 | +156 | 0.658 | Brian Thomas Jr 2+ receptions (-256) / Christian McCaffrey 4+ receptions (-309) / Cooper Kupp 15+ rec_yds (-256) |
| w4 sun | calib | SUN-2 | LOSS | -1.0 | +150 | 0.648 | Trevor Lawrence 210+ pass_yds (-414) / Daniel Jones 180+ pass_yds (-444) / Christian McCaffrey 4+ receptions (-309) / Jaxon Smith-Njigba 60+ rec_yds (-411) |
| w4 sun | calib | SUN-3 | LOSS | -1.0 | +156 | 0.606 | Brock Purdy 190+ pass_yds (-394) / Jakobi Meyers 3+ receptions (-348) / Chris Godwin 2+ receptions (-414) / Garrett Wilson 50+ rec_yds (-359) |
| w4 mnf | pfirst_norole | MNF-1 | WIN | 0.69 | -146 | 0.591 | Juwan Johnson 25+ rec_yds (-288) / Bijan Robinson 60+ rush_yds (-397) |
| w4 mnf | pfirst | MNF-1 | WIN | 0.69 | -146 | 0.591 | Juwan Johnson 25+ rec_yds (-288) / Bijan Robinson 60+ rush_yds (-397) |
| w4 mnf | pfirst_dog | MNF-1 | WIN | 0.69 | -146 | 0.591 | Juwan Johnson 25+ rec_yds (-288) / Bijan Robinson 60+ rush_yds (-397) |
| w4 mnf | calib | MNF-1 | WIN | 0.63 | -158 | 0.61 | Chris Olave 60+ rec_yds (-328) / Bijan Robinson 60+ rush_yds (-397) |
| w5 tnf | live | TNF-1 | WIN | 0.97 | -103 | 0.59 | Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | legacy | TNF-1 | WIN | 0.97 | -103 | 0.59 | Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | m20 | TNF-1 | WIN | 0.97 | -103 | 0.551 | Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | m40e0 | TNF-1 | WIN | 0.97 | -103 | 0.516 | Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | m40em1 | TNF-1 | WIN | 0.97 | -103 | 0.516 | Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | pfirst_norole | TNF-1 | WIN | 1.55 | +155 | 0.464 | Cade Otton 15+ rec_yds (-337) / Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | pfirst | TNF-1 | WIN | 1.55 | +155 | 0.464 | Cade Otton 15+ rec_yds (-337) / Bucky Irving 40+ rush_yds (-240) / Chris Godwin 3+ receptions (-257) |
| w5 tnf | pfirst_dog | TNF-1 | LOSS | -1.0 | +164 | 0.372 | CeeDee Lamb 5+ receptions (-373) / Chris Godwin 15+ rec_yds (-363) / Cade Otton 15+ rec_yds (-337) / Dak Prescott 220+ pass_yds (-386) |
| w5 tnf | calib | TNF-1 | LOSS | -1.0 | +155 | 0.388 | Chris Godwin 15+ rec_yds (-363) / Emeka Egbuka 15+ rec_yds (-373) / Ryan Flournoy 15+ rec_yds (-408) / CeeDee Lamb 5+ receptions (-373) |
| w5 sun | live | SUN-1 | WIN | 1.86 | +186 | 0.437 | Nico Collins 50+ rec_yds (-389) / Omarion Hampton 25+ rush_yds (-348) / Derrick Henry 60+ rush_yds (-296) / Joe Burrow 30+ pass_att (-313) |
| w5 sun | live | SUN-2 | LOSS | -1.0 | +210 | 0.388 | Omarion Hampton 25+ rush_yds (-348) / Juwan Johnson 25+ rec_yds (-330) / Pat Freiermuth 15+ rec_yds (-323) / Bijan Robinson 70+ rush_yds (-244) |
| w5 sun | legacy | SUN-1 | WIN | 1.86 | +186 | 0.437 | Nico Collins 50+ rec_yds (-389) / Omarion Hampton 25+ rush_yds (-348) / Derrick Henry 60+ rush_yds (-296) / Joe Burrow 30+ pass_att (-313) |
| w5 sun | legacy | SUN-2 | LOSS | -1.0 | +210 | 0.388 | Omarion Hampton 25+ rush_yds (-348) / Juwan Johnson 25+ rec_yds (-330) / Pat Freiermuth 15+ rec_yds (-323) / Bijan Robinson 70+ rush_yds (-244) |
| w5 sun | m20 | SUN-1 | LOSS | -1.0 | +124 | 0.504 | Omarion Hampton 25+ rush_yds (-348) / Derrick Henry 60+ rush_yds (-296) / Juwan Johnson 25+ rec_yds (-330) |
| w5 sun | m20 | SUN-2 | WIN | 3.32 | +332 | 0.292 | Omarion Hampton 25+ rush_yds (-348) / Xavier Hutchinson 15+ rec_yds (-114) / Rome Odunze 40+ rec_yds (-127) |
| w5 sun | m40e0 | SUN-1 | LOSS | -1.0 | +124 | 0.453 | Omarion Hampton 25+ rush_yds (-348) / Derrick Henry 60+ rush_yds (-296) / Juwan Johnson 25+ rec_yds (-330) |
| w5 sun | m40e0 | SUN-2 | LOSS | -1.0 | +246 | 0.306 | Omarion Hampton 25+ rush_yds (-348) / Xavier Hutchinson 15+ rec_yds (-114) / Harold Fannin Jr. 25+ rec_yds (-231) |
| w5 sun | m40em1 | SUN-1 | WIN | 2.07 | +207 | 0.324 | Omarion Hampton 25+ rush_yds (-348) / Nico Collins 50+ rec_yds (-389) / Derrick Henry 60+ rush_yds (-296) / Joe Burrow 22+ pass_cmps (-239) |
| w5 sun | m40em1 | SUN-2 | LOSS | -1.0 | +136 | 0.419 | Omarion Hampton 25+ rush_yds (-348) / Juwan Johnson 25+ rec_yds (-330) / Bijan Robinson 70+ rush_yds (-244) |
| w5 sun | pfirst_norole | SUN-1 | WIN | 1.56 | +156 | 0.492 | Nico Collins 50+ rec_yds (-389) / Omarion Hampton 8+ rush_att (-434) / Derrick Henry 60+ rush_yds (-296) / Juwan Johnson 3+ receptions (-423) |
| w5 sun | pfirst_norole | SUN-2 | LOSS | -1.0 | +151 | 0.488 | Derrick Henry 60+ rush_yds (-296) / Pat Freiermuth 15+ rec_yds (-323) / Harold Fannin Jr. 25+ rec_yds (-231) |
| w5 sun | pfirst_norole | SUN-3 | WIN | 1.51 | +151 | 0.407 | Joe Burrow 30+ pass_att (-313) / Daniel Jones 18+ pass_cmps (-235) / Rome Odunze 25+ rec_yds (-299) |
| w5 sun | pfirst | SUN-1 | LOSS | -1.0 | +151 | 0.488 | Derrick Henry 60+ rush_yds (-296) / Pat Freiermuth 15+ rec_yds (-323) / Harold Fannin Jr. 25+ rec_yds (-231) |
| w5 sun | pfirst | SUN-2 | WIN | 1.56 | +156 | 0.466 | Nico Collins 50+ rec_yds (-389) / Derrick Henry 60+ rush_yds (-296) / Luther Burden III 25+ rec_yds (-436) / Juwan Johnson 3+ receptions (-423) |
| w5 sun | pfirst | SUN-3 | WIN | 1.51 | +151 | 0.407 | Joe Burrow 30+ pass_att (-313) / Christian Watson 40+ rec_yds (-313) / Cam Skattebo 2+ receptions (-226) |
| w5 sun | pfirst_dog | SUN-1 | LOSS | -1.0 | +151 | 0.488 | Derrick Henry 60+ rush_yds (-296) / Pat Freiermuth 15+ rec_yds (-323) / Harold Fannin Jr. 25+ rec_yds (-231) |
| w5 sun | pfirst_dog | SUN-2 | WIN | 1.56 | +156 | 0.466 | Nico Collins 50+ rec_yds (-389) / Derrick Henry 60+ rush_yds (-296) / Luther Burden III 25+ rec_yds (-436) / Juwan Johnson 3+ receptions (-423) |
| w5 sun | pfirst_dog | SUN-3 | WIN | 1.51 | +151 | 0.407 | Joe Burrow 30+ pass_att (-313) / Christian Watson 40+ rec_yds (-313) / Cam Skattebo 2+ receptions (-226) |
| w5 sun | calib | SUN-1 | LOSS | -1.0 | +150 | 0.483 | Tyler Shough 190+ pass_yds (-422) / Luther Burden III 25+ rec_yds (-436) / Michael Wilson 50+ rec_yds (-297) / Brock Purdy 180+ pass_yds (-431) |
| w5 sun | calib | SUN-2 | LOSS | -1.0 | +152 | 0.407 | Daniel Jones 160+ pass_yds (-449) / Joe Burrow 200+ pass_yds (-430) / Cam Ward 28+ pass_att (-356) / Bo Nix 180+ pass_yds (-329) |
| w5 sun | calib | SUN-3 | LOSS | -1.0 | +157 | 0.382 | Joe Burrow 200+ pass_yds (-430) / Justin Herbert 26+ pass_att (-434) / Aaron Rodgers 180+ pass_yds (-394) / Chris Olave 60+ rec_yds (-286) |
| w5 mnf | live | MNF-1 | LOSS | -1.0 | +268 | 0.346 | Kyren Williams 50+ rush_yds (-330) / James Cook 74+ rush_yds (-110) / Davante Adams 4+ receptions (-208) |
| w5 mnf | legacy | MNF-1 | LOSS | -1.0 | +268 | 0.346 | Kyren Williams 50+ rush_yds (-330) / James Cook 74+ rush_yds (-110) / Davante Adams 4+ receptions (-208) |
| w5 mnf | m20 | MNF-1 | LOSS | -1.0 | +168 | 0.423 | Kyren Williams 60+ rush_yds (-187) / James Cook 70+ rush_yds (-134) |
| w5 mnf | m40e0 | MNF-1 | LOSS | -1.0 | +193 | 0.369 | Kyren Williams 60+ rush_yds (-187) / James Cook 74+ rush_yds (-110) |
| w5 mnf | m40em1 | MNF-1 | LOSS | -1.0 | +193 | 0.369 | Kyren Williams 60+ rush_yds (-187) / James Cook 74+ rush_yds (-110) |
| w5 mnf | pfirst_norole | MNF-1 | WIN | 1.61 | +161 | 0.387 | Puka Nacua 60+ rec_yds (-441) / Davante Adams 4+ receptions (-208) / Matthew Stafford 22+ pass_cmps (-228) |
| w5 mnf | pfirst | MNF-1 | WIN | 1.61 | +161 | 0.387 | Puka Nacua 60+ rec_yds (-441) / Davante Adams 4+ receptions (-208) / Matthew Stafford 22+ pass_cmps (-228) |
| w5 mnf | pfirst_dog | MNF-1 | WIN | 1.61 | +161 | 0.387 | Puka Nacua 60+ rec_yds (-441) / Davante Adams 4+ receptions (-208) / Matthew Stafford 22+ pass_cmps (-228) |
| w5 mnf | calib | MNF-1 | LOSS | -1.0 | +152 | 0.32 | Matthew Stafford 230+ pass_yds (-385) / Puka Nacua 60+ rec_yds (-441) / Tyler Higbee 2+ receptions (-399) / Kyren Williams 50+ rush_yds (-330) |
| w6 sun | live | SUN-1 | LOSS | -1.0 | +208 | 0.413 | Nico Collins 50+ rec_yds (-272) / Omarion Hampton 8+ rush_att (-349) / Bijan Robinson 70+ rush_yds (-314) / Juwan Johnson 25+ rec_yds (-306) |
| w6 sun | live | SUN-2 | LOSS | -1.0 | +216 | 0.42 | Nico Collins 50+ rec_yds (-272) / Chris Godwin 3+ receptions (-202) / Kyren Williams 60+ rush_yds (-184) |
| w6 sun | live | SUN-3 | LOSS | -1.0 | +340 | 0.303 | Xavier Hutchinson 15+ rec_yds (-111) / Bucky Irving 2+ receptions (-188) / Davante Adams 4+ receptions (-196) |
| w6 sun | legacy | SUN-1 | LOSS | -1.0 | +208 | 0.413 | Nico Collins 50+ rec_yds (-272) / Omarion Hampton 8+ rush_att (-349) / Bijan Robinson 70+ rush_yds (-314) / Juwan Johnson 25+ rec_yds (-306) |
| w6 sun | legacy | SUN-2 | LOSS | -1.0 | +216 | 0.42 | Nico Collins 50+ rec_yds (-272) / Chris Godwin 3+ receptions (-202) / Kyren Williams 60+ rush_yds (-184) |
| w6 sun | legacy | SUN-3 | LOSS | -1.0 | +340 | 0.303 | Xavier Hutchinson 15+ rec_yds (-111) / Bucky Irving 2+ receptions (-188) / Davante Adams 4+ receptions (-196) |
| w6 sun | m20 | SUN-1 | LOSS | -1.0 | +163 | 0.45 | Nico Collins 50+ rec_yds (-272) / Omarion Hampton 8+ rush_att (-349) / Chris Godwin 3+ receptions (-202) |
| w6 sun | m20 | SUN-2 | LOSS | -1.0 | +381 | 0.291 | Nico Collins 50+ rec_yds (-272) / KaVontae Turpin 7+ rec_yds (-110) / Tyler Shough 230+ pass_yds (-119) |
| w6 sun | m40e0 | SUN-1 | LOSS | -1.0 | +196 | 0.373 | Nico Collins 50+ rec_yds (-272) / Omarion Hampton 25+ rush_yds (-224) / Chris Godwin 3+ receptions (-202) |
| w6 sun | m40em1 | SUN-1 | LOSS | -1.0 | +212 | 0.321 | Nico Collins 40+ rec_yds (-435) / Omarion Hampton 8+ rush_att (-349) / Bijan Robinson 70+ rush_yds (-314) / Chris Godwin 3+ receptions (-202) |
| w6 sun | m40em1 | SUN-2 | LOSS | -1.0 | +211 | 0.319 | Nico Collins 40+ rec_yds (-435) / Tyler Shough 220+ pass_yds (-157) / Kyren Williams 60+ rush_yds (-184) |
| w6 sun | pfirst_norole | SUN-1 | LOSS | -1.0 | +158 | 0.513 | Nico Collins 50+ rec_yds (-272) / Omarion Hampton 20+ rush_yds (-380) / Chris Godwin 3+ receptions (-202) |
| w6 sun | pfirst_norole | SUN-2 | LOSS | -1.0 | +151 | 0.444 | Nico Collins 50+ rec_yds (-272) / Bijan Robinson 16+ rush_att (-285) / Derrick Henry 70+ rush_yds (-278) |
| w6 sun | pfirst_norole | SUN-3 | LOSS | -1.0 | +151 | 0.435 | Juwan Johnson 25+ rec_yds (-306) / Tre Tucker 25+ rec_yds (-271) / Dalton Schultz 3+ receptions (-263) |
| w6 sun | pfirst | SUN-1 | LOSS | -1.0 | +151 | 0.491 | Nico Collins 50+ rec_yds (-272) / Matthew Stafford 230+ pass_yds (-441) / Chris Godwin 3+ receptions (-202) |
| w6 sun | pfirst | SUN-2 | LOSS | -1.0 | +156 | 0.453 | Nico Collins 50+ rec_yds (-272) / Bijan Robinson 70+ rush_yds (-314) / Bucky Irving 14+ rush_att (-238) |
| w6 sun | pfirst | SUN-3 | LOSS | -1.0 | +150 | 0.431 | Kyren Williams 12+ rush_att (-355) / Kimani Vidal 10+ rush_yds (-315) / Cade Otton 3+ receptions (-208) |
| w6 sun | pfirst_dog | SUN-1 | LOSS | -1.0 | +151 | 0.491 | Nico Collins 50+ rec_yds (-272) / Matthew Stafford 230+ pass_yds (-441) / Chris Godwin 3+ receptions (-202) |
| w6 sun | pfirst_dog | SUN-2 | LOSS | -1.0 | +150 | 0.455 | Nico Collins 50+ rec_yds (-272) / Patrick Mahomes 180+ pass_yds (-423) / Cade Otton 3+ receptions (-208) |
| w6 sun | pfirst_dog | SUN-3 | LOSS | -1.0 | +151 | 0.413 | Juwan Johnson 25+ rec_yds (-306) / Puka Nacua 70+ rec_yds (-303) / Bucky Irving 14+ rush_att (-238) |
| w6 sun | calib | SUN-1 | LOSS | -1.0 | +156 | 0.63 | Kimani Vidal 10+ rush_yds (-315) / Nico Collins 40+ rec_yds (-435) / Cam Ward 28+ pass_att (-378) / DK Metcalf 3+ receptions (-404) |
| w6 sun | calib | SUN-2 | WIN | 1.54 | +154 | 0.586 | Kimani Vidal 10+ rush_yds (-315) / Tre Tucker 25+ rec_yds (-271) / Aaron Rodgers 20+ pass_cmps (-246) |
| w6 sun | calib | SUN-3 | WIN | 1.56 | +156 | 0.449 | Drake Maye 15+ rush_yds (-327) / Dalton Schultz 3+ receptions (-263) / Bucky Irving 14+ rush_att (-238) |
| w6 mnf | pfirst_norole | MNF-1 | LOSS | -1.0 | +153 | 0.37 | Jayden Daniels 25+ rush_yds (-308) / Christian McCaffrey 50+ rush_yds (-227) / Brock Purdy 10+ rush_yds (-309) |
| w6 mnf | pfirst | MNF-1 | LOSS | -1.0 | +153 | 0.37 | Jayden Daniels 25+ rush_yds (-308) / Christian McCaffrey 50+ rush_yds (-227) / Brock Purdy 10+ rush_yds (-309) |
| w6 mnf | pfirst_dog | MNF-1 | WIN | 0.91 | -110 | 0.505 | Christian McCaffrey 50+ rush_yds (-227) / Brock Purdy 10+ rush_yds (-309) |
| w6 mnf | calib | MNF-1 | LOSS | -1.0 | +176 | 0.449 | Jayden Daniels 6+ rush_att (-294) / Austin Ekeler 10+ rush_yds (-366) / Brock Purdy 10+ rush_yds (-309) / Christian McCaffrey 40+ rush_yds (-447) |
| w7 tnf | live | TNF-1 | LOSS | -1.0 | +166 | 0.473 | Rome Odunze 30+ rec_yds (-255) / D'Andre Swift 40+ rush_yds (-382) / TreVeyon Henderson 20+ rush_yds (-194) |
| w7 tnf | legacy | TNF-1 | LOSS | -1.0 | +166 | 0.473 | Rome Odunze 30+ rec_yds (-255) / D'Andre Swift 40+ rush_yds (-382) / TreVeyon Henderson 20+ rush_yds (-194) |
| w7 tnf | m20 | TNF-1 | LOSS | -1.0 | +111 | 0.524 | TreVeyon Henderson 20+ rush_yds (-194) / Rome Odunze 30+ rec_yds (-255) |
| w7 tnf | m40e0 | TNF-1 | LOSS | -1.0 | +111 | 0.487 | Rome Odunze 30+ rec_yds (-255) / TreVeyon Henderson 20+ rush_yds (-194) |
| w7 tnf | m40em1 | TNF-1 | LOSS | -1.0 | +166 | 0.384 | Rome Odunze 30+ rec_yds (-255) / D'Andre Swift 40+ rush_yds (-382) / TreVeyon Henderson 20+ rush_yds (-194) |
| w7 tnf | pfirst_norole | TNF-1 | LOSS | -1.0 | +151 | 0.427 | D'Andre Swift 40+ rush_yds (-382) / Kalif Raymond 2+ receptions (-396) / Luther Burden III 30+ rec_yds (-435) / Rome Odunze 25+ rec_yds (-344) |
| w7 tnf | pfirst | TNF-1 | WIN | 1.51 | +151 | 0.398 | D'Andre Swift 40+ rush_yds (-382) / Rome Odunze 25+ rec_yds (-344) / Drake Maye 4+ rush_att (-446) / Caleb Williams 10+ rush_yds (-388) |
| w7 tnf | pfirst_dog | TNF-1 | WIN | 1.51 | +151 | 0.398 | D'Andre Swift 40+ rush_yds (-382) / Rome Odunze 25+ rec_yds (-344) / Drake Maye 4+ rush_att (-446) / Caleb Williams 10+ rush_yds (-388) |
| w7 tnf | calib | TNF-1 | LOSS | -1.0 | +156 | 0.324 | Rhamondre Stevenson 2+ receptions (-347) / Kalif Raymond 2+ receptions (-396) / Luther Burden III 30+ rec_yds (-435) / Rome Odunze 25+ rec_yds (-344) |
| w7 sun | live | SUN-1 | LOSS | -1.0 | +200 | 0.462 | Alvin Kamara 10+ rush_yds (-294) / Jaxon Smith-Njigba 70+ rec_yds (-294) / Jonathan Taylor 14+ rush_att (-350) / Jameson Williams 30+ rec_yds (-333) |
| w7 sun | live | SUN-2 | LOSS | -1.0 | +242 | 0.423 | Jaxon Smith-Njigba 70+ rec_yds (-294) / Nico Collins 50+ rec_yds (-254) / Aaron Jones 30+ rush_yds (-209) / J.K. Dobbins 30+ rush_yds (-422) |
| w7 sun | live | SUN-3 | LOSS | -1.0 | +220 | 0.359 | Matthew Stafford 220+ pass_yds (-307) / Juwan Johnson 3+ receptions (-291) / Kenneth Walker III 16+ rush_att (-272) / Michael Wilson 30+ rec_yds (-320) |
| w7 sun | legacy | SUN-1 | LOSS | -1.0 | +200 | 0.462 | Alvin Kamara 10+ rush_yds (-294) / Jaxon Smith-Njigba 70+ rec_yds (-294) / Jonathan Taylor 14+ rush_att (-350) / Jameson Williams 30+ rec_yds (-333) |
| w7 sun | legacy | SUN-2 | LOSS | -1.0 | +242 | 0.423 | Jaxon Smith-Njigba 70+ rec_yds (-294) / Nico Collins 50+ rec_yds (-254) / Aaron Jones 30+ rush_yds (-209) / J.K. Dobbins 30+ rush_yds (-422) |
| w7 sun | legacy | SUN-3 | LOSS | -1.0 | +220 | 0.359 | Matthew Stafford 220+ pass_yds (-307) / Juwan Johnson 3+ receptions (-291) / Kenneth Walker III 16+ rush_att (-272) / Michael Wilson 30+ rec_yds (-320) |
| w7 sun | m20 | SUN-1 | LOSS | -1.0 | +200 | 0.396 | Jonathan Taylor 14+ rush_att (-350) / Jaxon Smith-Njigba 70+ rec_yds (-294) / Alvin Kamara 10+ rush_yds (-294) / Jameson Williams 30+ rec_yds (-333) |
| w7 sun | m20 | SUN-2 | LOSS | -1.0 | +315 | 0.304 | Jonathan Taylor 14+ rush_att (-350) / Nico Collins 50+ rec_yds (-254) / Matthew Stafford 22+ pass_cmps (-205) / Trey McBride 7+ receptions (-180) |
| w7 sun | m40e0 | SUN-1 | LOSS | -1.0 | +245 | 0.308 | Jaxon Smith-Njigba 70+ rec_yds (-294) / Alvin Kamara 10+ rush_yds (-294) / Aaron Jones 30+ rush_yds (-209) / Jameson Williams 30+ rec_yds (-333) |
| w7 sun | m40e0 | SUN-2 | LOSS | -1.0 | +178 | 0.377 | Jaxon Smith-Njigba 70+ rec_yds (-294) / Nico Collins 50+ rec_yds (-254) / Matthew Stafford 22+ pass_cmps (-205) |
| w7 sun | m40em1 | SUN-1 | LOSS | -1.0 | +186 | 0.356 | Jaxon Smith-Njigba 70+ rec_yds (-294) / Alvin Kamara 10+ rush_yds (-294) / Jonathan Taylor 14+ rush_att (-350) / J.K. Dobbins 30+ rush_yds (-422) |
| w7 sun | m40em1 | SUN-2 | LOSS | -1.0 | +204 | 0.329 | Jaxon Smith-Njigba 70+ rec_yds (-294) / Aaron Jones 25+ rush_yds (-316) / Jameson Williams 30+ rec_yds (-333) / Matthew Stafford 220+ pass_yds (-307) |
| w7 sun | pfirst_norole | SUN-1 | LOSS | -1.0 | +150 | 0.541 | Alvin Kamara 10+ rush_yds (-294) / Jaxon Smith-Njigba 70+ rec_yds (-294) / Nico Collins 50+ rec_yds (-254) |
| w7 sun | pfirst_norole | SUN-2 | LOSS | -1.0 | +152 | 0.486 | Nico Collins 50+ rec_yds (-254) / Juwan Johnson 3+ receptions (-291) / Chase Brown 3+ receptions (-291) |
| w7 sun | pfirst_norole | SUN-3 | LOSS | -1.0 | +153 | 0.47 | Jonathan Taylor 14+ rush_att (-350) / J.K. Dobbins 30+ rush_yds (-422) / Jameson Williams 30+ rec_yds (-333) / Darnell Washington 10+ rec_yds (-448) |
| w7 sun | pfirst | SUN-1 | LOSS | -1.0 | +150 | 0.541 | Alvin Kamara 10+ rush_yds (-294) / Jaxon Smith-Njigba 70+ rec_yds (-294) / Nico Collins 50+ rec_yds (-254) |
| w7 sun | pfirst | SUN-2 | LOSS | -1.0 | +151 | 0.48 | Nico Collins 50+ rec_yds (-254) / Aaron Jones 25+ rush_yds (-316) / Kenneth Walker III 16+ rush_att (-272) |
| w7 sun | pfirst | SUN-3 | LOSS | -1.0 | +153 | 0.47 | Jonathan Taylor 14+ rush_att (-350) / J.K. Dobbins 30+ rush_yds (-422) / Jameson Williams 30+ rec_yds (-333) / Darnell Washington 10+ rec_yds (-448) |
| w7 sun | pfirst_dog | SUN-1 | LOSS | -1.0 | +150 | 0.541 | Alvin Kamara 10+ rush_yds (-294) / Jaxon Smith-Njigba 70+ rec_yds (-294) / Nico Collins 50+ rec_yds (-254) |
| w7 sun | pfirst_dog | SUN-2 | LOSS | -1.0 | +151 | 0.48 | Nico Collins 50+ rec_yds (-254) / Aaron Jones 25+ rush_yds (-316) / Kenneth Walker III 16+ rush_att (-272) |
| w7 sun | pfirst_dog | SUN-3 | LOSS | -1.0 | +151 | 0.447 | J.K. Dobbins 30+ rush_yds (-422) / Jameson Williams 30+ rec_yds (-333) / Tre Tucker 20+ rec_yds (-425) / Patrick Mahomes 180+ pass_yds (-382) |
| w7 sun | calib | SUN-1 | LOSS | -1.0 | +151 | 0.486 | J.K. Dobbins 30+ rush_yds (-422) / Matthew Stafford 20+ pass_cmps (-430) / Aaron Jones 8+ rush_att (-346) / Joe Burrow 220+ pass_yds (-364) |
| w7 sun | calib | SUN-2 | LOSS | -1.0 | +151 | 0.451 | J.K. Dobbins 30+ rush_yds (-422) / Nico Collins 40+ rec_yds (-437) / Chris Godwin 25+ rec_yds (-436) / Aaron Rodgers 20+ pass_cmps (-291) |
| w7 sun | calib | SUN-3 | LOSS | -1.0 | +159 | 0.392 | Jacoby Brissett 20+ pass_cmps (-434) / Tyler Shough 190+ pass_yds (-334) / Patrick Mahomes 180+ pass_yds (-382) / Daniel Jones 150+ pass_yds (-355) |
| w7 mnf | pfirst_norole | MNF-1 | LOSS | -1.0 | -182 | 0.569 | Dak Prescott 220+ pass_yds (-432) / Jake Ferguson 2+ receptions (-388) |
| w7 mnf | pfirst | MNF-1 | LOSS | -1.0 | -182 | 0.569 | Dak Prescott 220+ pass_yds (-432) / Jake Ferguson 2+ receptions (-388) |
| w7 mnf | pfirst_dog | MNF-1 | LOSS | -1.0 | -182 | 0.569 | Dak Prescott 220+ pass_yds (-432) / Jake Ferguson 2+ receptions (-388) |
| w7 mnf | calib | MNF-1 | LOSS | -1.0 | -182 | 0.636 | Dak Prescott 220+ pass_yds (-432) / Jake Ferguson 2+ receptions (-388) |
| w8 tnf | live | TNF-1 | LOSS | -1.0 | +192 | 0.425 | John Metchie III 10+ rec_yds (-193) / Darren Waller 20+ rec_yds (-108) |
| w8 tnf | legacy | TNF-1 | LOSS | -1.0 | +192 | 0.425 | John Metchie III 10+ rec_yds (-193) / Darren Waller 20+ rec_yds (-108) |
| w8 tnf | m40em1 | TNF-1 | LOSS | -1.0 | +142 | 0.402 | John Metchie III 10+ rec_yds (-193) / Darren Waller 15+ rec_yds (-168) |
| w8 tnf | pfirst_norole | TNF-1 | WIN | 0.57 | -175 | 0.566 | Tucker Kraft 25+ rec_yds (-414) / Christian Watson 40+ rec_yds (-377) |
| w8 tnf | pfirst | TNF-1 | WIN | 0.57 | -175 | 0.566 | Tucker Kraft 25+ rec_yds (-414) / Christian Watson 40+ rec_yds (-377) |
| w8 tnf | pfirst_dog | TNF-1 | WIN | 0.57 | -175 | 0.566 | Tucker Kraft 25+ rec_yds (-414) / Christian Watson 40+ rec_yds (-377) |
| w8 tnf | calib | TNF-1 | WIN | 0.69 | -145 | 0.446 | Christian Watson 40+ rec_yds (-377) / Darren Waller 10+ rec_yds (-298) |
