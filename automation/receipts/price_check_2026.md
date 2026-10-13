# Price check, 2026 through week 5

Report only: no rule changes from this (R4 is revisited once held legs beat their prices over at least 4 weeks).

## Holds and carded legs (listed single prices)

Hit vs implied at the listed price; our probability recomputed walk-forward. Voids excluded. Sources: w3 mnf (top-15 holds only), w3 sun (top-15 holds only), w3 tnf (top-15 holds only), w4 mnf (every hold), w4 sun (every hold), w4 tnf (top-15 holds only), w5 mnf (every hold), w5 sun (every hold), w5 tnf (every hold).

| group | n | record | voids | hit | implied | ours | beat_price | roi | units |
|---|---|---|---|---|---|---|---|---|---|
| held: team change | 52 | 35-17 | 2 | 67.3 | 69.1 | 72.2 | -1.7 | -5.8 | -2.99 |
| held: team change (sole reason) | 7 | 7-0 | 0 | 100.0 | 62.8 | 70.0 | 37.2 | 64.1 | 4.49 |
| held: blowout risk | 11 | 8-3 | 0 | 72.7 | 75.9 | 74.2 | -3.2 | -5.1 | -0.56 |
| held: blowout risk (sole reason) | 2 | 0-2 | 0 | 0.0 | 65.2 | 70.9 | -65.2 | -100.0 | -2.0 |
| held: tough defense | 61 | 50-11 | 0 | 82.0 | 73.0 | 73.6 | 9.0 | 13.8 | 8.43 |
| held: tough defense (sole reason) | 14 | 11-3 | 0 | 78.6 | 66.2 | 72.2 | 12.4 | 16.1 | 2.26 |
| held: low own volume | 67 | 47-20 | 2 | 70.1 | 72.2 | 72.6 | -2.1 | -4.7 | -3.14 |
| held: low own volume (sole reason) | 5 | 3-2 | 0 | 60.0 | 69.7 | 76.1 | -9.7 | -20.6 | -1.03 |
| held: price worse than −450 | 68 | 54-14 | 3 | 79.4 | 83.8 | 78.6 | -4.3 | -5.3 | -3.61 |
| held: price worse than −450 (sole reason) | 2 | 1-1 | 0 | 50.0 | 83.3 | 83.3 | -33.3 | -41.0 | -0.82 |
| held: edge below +2 | 217 | 166-51 | 5 | 76.5 | 78.0 | 74.5 | -1.5 | -1.6 | -3.57 |
| held: edge below +2 (sole reason) | 87 | 65-22 | 0 | 74.7 | 75.5 | 72.8 | -0.8 | -0.6 | -0.52 |
| held: grade below C | 103 | 73-30 | 4 | 70.9 | 70.2 | 71.4 | 0.7 | 2.8 | 2.9 |
| held: grade below C (sole reason) | 10 | 7-3 | 1 | 70.0 | 55.1 | 64.6 | 14.9 | 31.0 | 3.1 |
| held: injury | 10 | 8-2 | 0 | 80.0 | 72.2 | 74.3 | 7.8 | 9.4 | 0.94 |
| held: held by hand | 1 | 1-0 | 0 | 100.0 | 76.6 | 82.4 | 23.4 | 30.6 | 0.31 |
| held: all, each leg once | 305 | 226-79 | 6 | 74.1 | 73.9 | 73.4 | 0.2 | 0.6 | 1.88 |
| carded legs | 28 | 22-6 | 0 | 78.6 | 73.2 | 77.2 | 5.4 | 9.4 | 2.63 |

## Legs board, C-or-better rungs (weeks 3, 4, 5)

Board prices = last pre-kickoff regrade. One rung per player/market = the row's best rung within the split.

| group | count | n | record | hit | implied | ours | beat_price | roi | units |
|---|---|---|---|---|---|---|---|---|---|
| worse than -500 | every rung | 886 | 796-90 | 89.8 | 91.0 | 82.8 | -1.1 | -1.2 | -10.91 |
| worse than -500 | one rung per player/market | 562 | 505-57 | 89.9 | 90.8 | 83.1 | -0.9 | -1.0 | -5.47 |
| -500 or better | every rung | 797 | 569-228 | 71.4 | 71.3 | 67.8 | 0.1 | 0.8 | 6.67 |
| -500 or better | one rung per player/market | 498 | 368-130 | 73.9 | 74.2 | 70.4 | -0.3 | 0.4 | 1.77 |
| -500 or better, edge >= +2 | every rung | 153 | 93-60 | 60.8 | 63.5 | 69.8 | -2.7 | -4.0 | -6.09 |
| -500 or better, edge >= +2 | one rung per player/market | 111 | 73-38 | 65.8 | 66.6 | 72.1 | -0.8 | 0.4 | 0.48 |
| -500 or better, edge < +2 | every rung | 634 | 468-166 | 73.8 | 73.1 | 67.4 | 0.7 | 1.9 | 12.11 |
| -500 or better, edge < +2 | one rung per player/market | 427 | 318-109 | 74.5 | 74.9 | 69.4 | -0.4 | 0.2 | 1.03 |

## Calibration: our probability vs DK's implied, one rung per player/market

Every settled C-or-better rung, the row's best rung only. Gap = hit % minus predicted %. Lower Brier / mean gap = tracks hit rates better. Our probability is capped at 90%. If DK keeps tracking better, test a blend that weights the market more (report only).

| source | rows | brier | mean_abs_gap |
|---|---|---|---|
| ours | 699 | 0.1419 | 5.5 |
| DK implied | 699 | 0.1394 | 2.3 |

| source | bucket | n | predicted | hit | gap |
|---|---|---|---|---|---|
| ours | < 60 | 16 | 47.1 | 75.0 | 27.9 |
| ours | 60-65 | 37 | 62.5 | 75.7 | 13.2 |
| ours | 65-70 | 94 | 68.5 | 70.2 | 1.7 |
| ours | 70-75 | 86 | 72.5 | 70.9 | -1.6 |
| ours | 75-80 | 132 | 77.2 | 76.5 | -0.7 |
| ours | 80-85 | 187 | 82.3 | 90.4 | 8.1 |
| ours | 85-90 | 125 | 86.6 | 93.6 | 7.0 |
| ours | 90+ | 22 | 90.0 | 95.5 | 5.5 |
| DK implied | < 60 | 20 | 51.4 | 60.0 | 8.6 |
| DK implied | 60-65 | 8 | 63.2 | 87.5 | 24.3 |
| DK implied | 65-70 | 34 | 67.8 | 73.5 | 5.7 |
| DK implied | 70-75 | 79 | 72.6 | 72.2 | -0.5 |
| DK implied | 75-80 | 149 | 77.7 | 75.8 | -1.9 |
| DK implied | 80-85 | 89 | 82.5 | 78.7 | -3.9 |
| DK implied | 85-90 | 100 | 86.9 | 87.0 | 0.1 |
| DK implied | 90+ | 220 | 94.4 | 92.7 | -1.7 |
