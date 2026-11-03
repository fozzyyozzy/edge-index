# Week 8 receipts

## The record

14 legs graded, 6 hits, 42.9% hit rate. The model averaged 77.6% blended probability across those legs. At a 42.9% actual rate, the model ran hot by roughly 35 percentage points. Flat 1u P&L: -5.87u.

Ticket record: 0-4-0. Every ticket lost.

**SUN-1** (4 legs, est. +229): missed J.K. Dobbins (rush_yds), Jonathan Taylor (rush_att). Loss.
**SUN-2** (4 legs, est. +275): missed J.K. Dobbins (rush_yds), Jahmyr Gibbs (rec_yds), Jerry Jeudy (receptions), Derrick Henry (rush_att). Loss.
**SUN-3** (4 legs, est. +251): missed Omarion Hampton (rush_yds). Loss.
**TNF-1** (2 legs, est. +192): missed Darren Waller (rec_yds). Loss.

---

## What missed

| Player | Market | Rung | Actual | Missed by | Reason |
|---|---|---|---|---|---|
| J.K. Dobbins | rush_yds | 20 | 13 | 7 | game-script |
| Jonathan Taylor | rush_att | 14 | 8 | 6 | game-script |
| Jahmyr Gibbs | rec_yds | 20 | 15 | 5 | game-script |
| Jerry Jeudy | receptions | 2 | 0 | 2 | read-wrong |
| Derrick Henry | rush_att | 16 | 11 | 5 | game-script |
| Omarion Hampton | rush_yds | 25 | 20 | 5 | yard-short |
| Darren Waller | rec_yds | 20 | 11 | 9 | read-wrong |

Notes on reasoning: Dobbins (L10 10/10, L15 15/15, neutral defense) and Taylor (L10 10/10, L15 15/15, though opp_d TOUGH) both finished well short despite elite clear rates — the neutral-to-tough defensive context did not explain the magnitude, so game-script fits better. Henry (opp_d neutral, own_vol SOFT) and Gibbs (opp_d TOUGH, own_vol SOFT) each had favorable volume context but were held to well below their recent floors; TOUGH defense on Gibbs added pressure, but the under was widespread on the card, pointing to a broader game-script issue. Jeudy (0 receptions against a 2+ rung, L10 9/10) and Waller (L10 5/6, volatile last-three [36, 0, 50]) are read-wrong — the L10/L15 signal did not reflect real outcome variance. Hampton (5 yards short) qualifies as yard-short.

---

## Does 80% mean 80%

| Bucket | n | Hits | Actual rate |
|---|---|---|---|
| <75% | 2 | 1 | 50.0% |
| 75–85% | 12 | 5 | 41.7% |

The model was badly miscalibrated at the top of the range: legs modeled 75–85% hit at 41.7%, less than half the predicted rate.

---

## Price check

| Player | Market | Rung | Est | Real | Hit |
|---|---|---|---|---|---|
| J.K. Dobbins | rush_yds | 20 | -184 | -256 | No |
| Aaron Jones | rush_yds | 20 | -181 | -282 | Yes |
| Jonathan Taylor | rush_att | 14 | -319 | -241 | No |
| Kyren Williams | rush_yds | 40 | -291 | -425 | Yes |
| J.K. Dobbins | rush_yds | 20 | -184 | -256 | No |
| Jerry Jeudy | receptions | 2 | -248 | -223 | No |
| Derrick Henry | rush_att | 16 | -574 | -300 | No |
| Omarion Hampton | rush_yds | 25 | -165 | -217 | No |
| Trey McBride | receptions | 7 | -285 | -247 | Yes |
| Drake Maye | rush_att | 4 | -183 | -310 | Yes |
| Darren Waller | rec_yds | 20 | -108 | -108 | No |

Price estimates were mixed in direction but mostly too generous (estimates shorter than reality on the hits, longer on several misses); on the two largest gaps — Dobbins (est. -184, real -256) and Kyren Williams (est. -291, real -425) — the market priced both considerably shorter than the model, which suggests the model underprices these floor rungs systematically.

---

## The whole board

| Grade | n | Hits | Misses | Voids | Hit rate |
|---|---|---|---|---|---|
| A+ | 3 | 1 | 2 | 0 | 33.3% |
| A | 17 | 10 | 7 | 0 | 58.8% |
| A- | 71 | 55 | 16 | 0 | 77.5% |
| B | 103 | 72 | 30 | 1 | 70.6% |
| C | 74 | 50 | 22 | 2 | 68.1% |
| D | 0 | — | — | — | — |
| F | 102 | 34 | 62 | 6 | 33.3% |

Grades did not sort the board in the expected direction this week: A+ (33%) underperformed A (59%) which underperformed A- (78%), an inversion at the top that drove much of the ticket damage.

---

## Sunday prices

| Player | Market | Rung | Thursday | Published | Closing | Thu→Pub (pts) | Pub→Close (pts) |
|---|---|---|---|---|---|---|---|
| J.K. Dobbins | rush_yds | 20 | -137 | -256 | -261 | +14.1 | +0.4 |
| Aaron Jones | rush_yds | 20 | no Thursday price | -282 | -282 | — | 0.0 |
| Jonathan Taylor | rush_att | 14 | -258 | -241 | -165 | -1.4 | -8.4 |
| Kyren Williams | rush_yds | 40 | -429 | -425 | -464 | -0.1 | +1.3 |
| Jahmyr Gibbs | rec_yds | 20 | -356 | -253 | -242 | -6.4 | -0.9 |
| Jerry Jeudy | receptions | 2 | -212 | -223 | -238 | +1.1 | +1.4 |
| Derrick Henry | rush_att | 16 | -278 | -300 | -282 | +1.5 | -1.2 |
| Jameson Williams | rec_yds | 30 | -328 | -343 | -371 | +0.8 | +1.3 |
| Omarion Hampton | rush_yds | 25 | -222 | -217 | -228 | -0.5 | +1.1 |
| Trey McBride | receptions | 7 | -188 | -247 | -241 | +5.9 | -0.5 |
| Drake Maye | rush_att | 4 | -220 | -310 | -478 | +6.9 | +7.1 |

The most notable movement: Dobbins opened Thursday at -137 and had shortened to -256 by publish time (+14.1 implied-probability points), meaning the card locked into a price that the market had already moved hard — waiting for Thursday would not have helped on that leg, it would have cost access to a shorter number. On Taylor, the market moved against us after publication (-8.4 pts, closing at -165), suggesting the market had real information about his role that we did not. Overall, Friday publication did not produce a clear benefit; several legs where Thursday prices existed were already worse at publish time.

---

## What we held back

| Reason | n | Hits | Misses | Voids | Hit rate |
|---|---|---|---|---|---|
| team change | 2 | 0 | 0 | 2 | — (voided) |
| blowout risk | 3 | 2 | 1 | 0 | 66.7% |
| tough defense | 0 | — | — | — | — |
| low own volume | 27 | 20 | 7 | 0 | 74.1% |
| price worse than −450 | 28 | 19 | 8 | 1 | 69.4% |
| edge below +2 | 99 | 66 | 32 | 1 | 66.7% |
| grade below C | 24 | 15 | 7 | 2 | 68.2% |
| injury | 6 | 4 | 2 | 0 | 66.7% |
| held by hand | 0 | — | — | — | — |
| role down | 0 | — | — | — | — |

Team change holds voided — both players' statuses resolved before grading. Blowout risk: 3 legs, 2-1; sample is too small to say anything. Low own volume held 27 legs at 74.1% — the card hit 42.9%, so the legs held for low volume outperformed the legs played; the sample is large enough
