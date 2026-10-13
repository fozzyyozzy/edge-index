# Week 5 receipts

## The record

13 legs graded. 11 hits. Hit rate 84.6%.

The model averaged 77.4% across all legs. Actual hit rate came in at 84.6%, so the model ran cold by roughly 7 percentage points — the legs performed better than the numbers predicted.

Flat 1u P&L: +2.4u (net of losses on MNF-1 and SUN-2, gains on SUN-1 and TNF-1).

**Ticket record: 2-2-0**

| Ticket | Result | Units | Miss |
|--------|--------|-------|------|
| MNF-1 | LOSS | -1.0u | Kyren Williams — yard-short |
| SUN-1 | WIN | +1.86u | — |
| SUN-2 | LOSS | -1.0u | Juwan Johnson — read-wrong |
| TNF-1 | WIN | +0.97u | — |

TNF-1 was a two-leg single-game slate ticket. Reduced-payout rules applied and were disclosed at issue.

---

## What missed

| Player | Rung | Actual | Missed by | Reason |
|--------|------|--------|-----------|--------|
| Kyren Williams | 50 rush yds | 49 | 1 | yard-short |
| Juwan Johnson | 25 rec yds | 16 | 9 | read-wrong |

Kyren Williams ran 49 yards against a neutral defense on a floor rung. One yard. The clear rate was 9/10 L10 and 13/15 L15; last three games were 85, 88, and 80. Nothing in the setup flagged this. It is a yard-short miss, not a model failure.

Juwan Johnson is different. L10 was 10/10, L15 was 15/15, last three were 66, 53, and 59. But the opponent defense was rated TOUGH, and Johnson's own volume was SOFT. The model assigned A- grade and the card published it. A TOUGH defense tag against a receiver with soft volume should have been a harder filter. The grade did not reflect the conflict. That is a read-wrong miss.

---

## Does 80% mean 80%

| Bucket | Legs | Hits | Actual rate |
|--------|------|------|-------------|
| <75% | 3 | 3 | 100% |
| 75–85% | 10 | 8 | 80% |

The 75–85 bucket landed at exactly 80%, which is the midpoint of the band — clean calibration there. The <75 bucket is three legs and hit all three, which is a small sample; no conclusion is warranted from that cell alone.

---

## Price check

| Player | Market | Rung | Est | Real | Diff | Hit |
|--------|--------|------|-----|------|------|-----|
| Kyren Williams | rush yds | 50 | -286 | -330 | -44 | No |
| James Cook | rush yds | 74 | -110 | -110 | 0 | Yes |
| Davante Adams | receptions | 4 | -228 | -208 | +20 | Yes |
| Nico Collins | rec yds | 50 | -378 | -389 | -11 | Yes |
| Omarion Hampton | rush yds | 25 | -229 | -348 | -119 | Yes |
| Derrick Henry | rush yds | 60 | -268 | -296 | -28 | Yes |
| Joe Burrow | pass att | 30 | -371 | -313 | +58 | Yes |
| Juwan Johnson | rec yds | 25 | -250 | -330 | -80 | No |
| Pat Freiermuth | rec yds | 15 | -205 | -323 | -118 | Yes |
| Bijan Robinson | rush yds | 70 | -235 | -244 | -9 | Yes |
| Bucky Irving | rush yds | 40 | -201 | -240 | -39 | Yes |
| Chris Godwin | receptions | 3 | -302 | -257 | +45 | Yes |

Note: Omarion Hampton appears twice in the source data at identical values; it is counted once here.

Estimates ran generous overall. Nine of twelve legs had real prices shorter than estimated, meaning the market priced these legs higher than the model expected. The two legs where estimates ran tight (Burrow, Godwin) both hit. The two misses (Williams, Johnson) were both legs where real prices were substantially shorter than estimated — a pattern worth watching, as sharper market pricing on these rungs may signal something the model missed.

---

## The whole board

| Grade | Legs | Hits | Misses | Hit rate |
|-------|------|------|--------|----------|
| A+ | 2 | 2 | 0 | 100% |
| A | 17 | 14 | 3 | 82% |
| A- | 56 | 49 | 7 | 88% |
| B | 77 | 65 | 12 | 84% |
| C | 71 | 46 | 24 | 65% |
| D | 6 | 5 | 1 | 83% |
| F | 173 | 49 | 115 | 28% |

The board sorted cleanly at the top and the bottom. A+/A/A- all cleared 82% or better; F landed at 28%. The D grade is six legs and 83% — an anomaly at that sample size, not a signal. The card drew exclusively from A+, A, A-, and B, and the B legs (84%) performed in line with everything above them this week. The letter sorted the board correctly.

---

## Sunday prices

| Player | Market | Rung | Thursday | Published | Closing | Thu→Pub (pts) | Pub→Close (pts) |
|--------|--------|------|----------|-----------|---------|----------------|-----------------|
| Nico Collins | rec yds | 50 | -428 | -389 | -395 | -1.51 | +0.25 |
| Omarion Hampton | rush yds | 25 | -352 | -348 | -372 | -0.20 | +1.13 |
| Derrick Henry | rush yds | 60 | -382 | -296 | -278 | -4.51 | -1.20 |
| Joe Burrow | pass att | 30 | -324 | -313 | -300 | -0.63 | -0.79 |
| Juwan Johnson | rec yds | 25 | -374 | -330 | -358 | -2.16 | +1.42 |
| Pat Freiermuth | rec yds | 15 | -339 | -323 | -317 | -0.86 | -0.34 |
| Bijan Robinson | rush yds | 70 | -267 | -244 | -280 | -1.82 | +2.75 |

All seven Sunday legs had Thursday prices available. Every single Thursday price was shorter than the published Friday price — the market softened across the board from Thursday to publication, meaning waiting for Friday got us better numbers on all seven legs. After publication, four of seven legs tightened again (shortened toward closing), so the published price was the best available price on most legs. Waiting for Friday helped; holding through to close would have cost us on four of the seven.

---

## What we held back

| Reason | n | Hits | Misses | Hit rate |
|--------|---|------|--------|----------|
| edge below +2 | 108 | 79 | 29 | 73% |
| grade below C | 54 | 35 | 19 | 65% |
| price worse than -450 | 28 | 20 | 8 | 71% |
| low own volume | 33 | 25 | 8 | 76% |
| team change | 22 | 13 | 9 | 59% |
| blowout risk | 4 | 4 | 0 | 100% |
| injury | 7 | 5 | 2 | 71% |
| tough defense | 0 | — | — | — |
| held by hand | 0 | — | — | — |

Edge below +2 is the largest hold bucket at 108 legs and hit at 73% — below the card's 84.6%, which supports keeping the edge threshold where it is. Grade below C hit at 65%, confirming the grade filter is doing real work. The price cap above -450 held 28 legs that hit at 71%; those prices carried less value than the card's average even when they won, so the cap holds. Low own volume held 33 legs at 76% — lower than the card rate, a modest endorsement of the volume filter. Team change at 59% on 22 legs is the sharpest validation here; legs held for that reason missed at a rate nearly double the card's miss rate. Blowout risk is four legs and all four hit, which is too small to draw any conclusion. Injury is seven legs, similarly small.

---

## What changes

One adjustment is supported by the data.

The Juwan Johnson miss came from a leg where the defense tag was TOUGH and own volume was SOFT, yet the grade was A-. Those two flags in combination should push a leg below the card threshold regardless of clear rate. The current model weights historical hit rate heavily enough that it can override adverse context. Going forward: any leg with opp_d TOUGH and own_vol SOFT is capped at B grade on the card, regardless of L10/L15. One week is a small sample, but the logic holds independently of this result.

Nothing else changes this week. The price estimate gaps are worth monitoring over a longer sample before touching the pricing model.

---

*What would change our mind: if the TOUGH defense / SOFT volume combination shows a hit rate above 80% across 20 or more graded legs, we revisit the cap.*
