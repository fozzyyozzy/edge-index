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
| worse than -500 | every rung | 939 | 845-94 | 90.0 | 91.0 | 82.9 | -1.0 | -1.1 | -9.97 |
| worse than -500 | one rung per player/market | 594 | 534-60 | 89.9 | 90.8 | 83.1 | -0.9 | -0.9 | -5.39 |
| -500 or better | every rung | 870 | 622-248 | 71.5 | 70.9 | 67.7 | 0.5 | 1.5 | 13.18 |
| -500 or better | one rung per player/market | 533 | 396-137 | 74.3 | 74.2 | 70.5 | 0.1 | 0.8 | 4.15 |
| -500 or better, edge >= +2 | every rung | 168 | 100-68 | 59.5 | 63.1 | 69.4 | -3.6 | -5.7 | -9.65 |
| -500 or better, edge >= +2 | one rung per player/market | 122 | 79-43 | 64.8 | 66.0 | 71.7 | -1.3 | -0.6 | -0.75 |
| -500 or better, edge < +2 | every rung | 692 | 514-178 | 74.3 | 72.8 | 67.2 | 1.5 | 3.2 | 22.18 |
| -500 or better, edge < +2 | one rung per player/market | 456 | 343-113 | 75.2 | 75.0 | 69.6 | 0.2 | 1.0 | 4.68 |

## Calibration: our probability vs DK's implied, one rung per player/market

Every settled C-or-better rung, the row's best rung only. Gap = hit % minus predicted %. Lower Brier / mean gap = tracks hit rates better. Our probability is capped at 90%. If DK keeps tracking better, test a blend that weights the market more (report only).

| source | rows | brier | mean_abs_gap |
|---|---|---|---|
| ours | 742 | 0.1412 | 5.0 |
| DK implied | 742 | 0.1384 | 2.4 |

| source | bucket | n | predicted | hit | gap |
|---|---|---|---|---|---|
| ours | < 60 | 16 | 47.1 | 75.0 | 27.9 |
| ours | 60-65 | 41 | 62.7 | 75.6 | 12.9 |
| ours | 65-70 | 95 | 68.5 | 70.5 | 2.1 |
| ours | 70-75 | 91 | 72.5 | 72.5 | 0.1 |
| ours | 75-80 | 145 | 77.3 | 77.9 | 0.6 |
| ours | 80-85 | 198 | 82.2 | 88.9 | 6.7 |
| ours | 85-90 | 133 | 86.6 | 94.0 | 7.3 |
| ours | 90+ | 23 | 90.0 | 95.7 | 5.7 |
| DK implied | < 60 | 22 | 51.6 | 59.1 | 7.5 |
| DK implied | 60-65 | 8 | 63.2 | 87.5 | 24.3 |
| DK implied | 65-70 | 35 | 67.8 | 74.3 | 6.4 |
| DK implied | 70-75 | 83 | 72.7 | 73.5 | 0.8 |
| DK implied | 75-80 | 158 | 77.8 | 76.6 | -1.2 |
| DK implied | 80-85 | 98 | 82.5 | 78.6 | -3.9 |
| DK implied | 85-90 | 106 | 86.9 | 87.7 | 0.8 |
| DK implied | 90+ | 232 | 94.4 | 92.2 | -2.1 |
