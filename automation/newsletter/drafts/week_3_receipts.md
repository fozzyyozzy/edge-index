# Week 3 receipts

# Edge Index — Week 3 Receipts

## The record

13 legs graded. 12 hits. Hit rate: 92.3%.

Average model probability: 86.4%. Actual rate: 92.3%. The model ran cold by roughly 6 percentage points — the legs cleared more often than the numbers said they should.

Flat 1u P&L: +3.73u across the card.

| Ticket | Result | Legs | Miss |
|--------|--------|------|------|
| SUN-1 | WIN +2.21u | 4-0 | — |
| SUN-2 | WIN +2.19u | 3-0 | — |
| SUN-3 | LOSS -1.00u | 3-1 | Evan Engram — read-wrong |
| TNF-1 | WIN +1.00u | 2-0 | — |

Ticket record: 3-1-0.

TNF-1 is flagged hand-built, pre-automation. CLV data is not available for that ticket's legs. The +1.00u result is recorded but the price-efficiency analysis below excludes those two legs.

---

## What missed

| Player | Rung | Actual | Missed by | Reason |
|--------|------|--------|-----------|--------|
| Evan Engram | 2+ receptions | 0 | 2 | read-wrong |

Engram was L10 8/10, L15 12/15, last three showing 3, 4, and 1 reception. The opposition was rated neutral and own-team volume was neutral. Zero catches is a tail outcome the clear rate does not predict well, but the note data shows no injury flag and no blowout context. This is read-wrong: the profile was sound, the result was a bad game, not a structural misread or a data failure.

The miss was by 2 receptions, which exceeds the yard-short threshold (the rule applies specifically to yardage props, but the distance here — needing 2, getting 0 — puts this clearly in the hard-miss category, not a near-miss).

---

## Does 80% mean 80%

| Bucket | Legs | Hits | Hit rate |
|--------|------|------|----------|
| <75% | 1 | 1 | 100% |
| 75–85% | 1 | 0 | 0% |
| 85%+ | 9 | 9 | 100% |

Three buckets, 11 graded legs (two TNF legs excluded from calibration for missing grade data). The 75–85 bucket contains one leg, the Engram miss. The sample is too small at the bucket level to draw calibration conclusions; one bad game swings the middle bucket to 0%. The 85%+ bucket ran perfect on 9 legs, which is above expectation and consistent with the model running cold overall this week.

---

## Price check

| Player | Market | Rung | Est. | Real | Diff |
|--------|--------|------|------|------|------|
| Derrick Henry | rush_yds | 60 | -435 | -377 | +58 |
| Juwan Johnson | receptions | 3 | -251 | -228 | +23 |
| Omarion Hampton | rush_att | 12 | -739 | -431 | +308 |
| Courtland Sutton | receptions | 3 | -251 | -232 | +19 |
| Rashee Rice | receptions | 4 | -208 | -192 | +16 |
| Kyren Williams | rush_att | 12 | -166 | -152 | +14 |
| George Kittle | rec_yds | 25 | -353 | -407 | -54 |
| Cade Otton | rec_yds | 15 | -221 | -299 | -78 |
| Evan Engram | receptions | 2 | -419 | -366 | +53 |

Positive difference means the estimate was more expensive (generous to the market) than the real price; negative means the estimate was cheaper than the real price. Eight of nine legs had estimates available. Five ran generous — the model priced the legs harder than the books did. Two rec_yds legs (Kittle, Otton) ran tight — the market was more expensive than estimated. The Hampton rush_att estimate was dramatically generous at -739 versus a real -431; that is the largest gap in the set and warrants a note on how attempt props are being priced. Overall, estimates leaned generous, meaning entry was at better value than the model expected on most legs.

---

## What changes

One adjustment is supported by the data.

The Hampton rush_att gap (-739 estimated, -431 real, a 308-point difference) is not a one-leg anomaly to dismiss. Attempt props for high-usage backs appear to be systematically overpriced in the model. Before next week, the attempt-prop pricing inputs should be reviewed to check whether the model is double-counting usage signals. If the gap persists in a second sample, the estimate methodology for rush_att needs a correction factor. Nothing changes in selection rules or rung floors based on this week.

No other adjustments are supported by one week of data.

---

What would change our mind: two consecutive weeks where 85%+ bucket legs clear below 80% would indicate the model is assigning floor probabilities too aggressively and the rung floors need to move up.
