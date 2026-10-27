# Week 7 receipts

## The record

15 legs graded, 7 hits, 46.7% hit rate. Average model probability was 79.7%; actual rate was 46.7%. The model ran hot by 33 percentage points. Flat 1u P&L: −5.77u.

Ticket record: 0-4-0. Every ticket lost.

**SUN-1** (4 legs, est. +200): miss — Alvin Kamara rush_yds (read-wrong)
**SUN-2** (4 legs, est. +242): miss — Nico Collins rec_yds (game-script), Aaron Jones rush_yds (yard-short), J.K. Dobbins rush_yds (read-wrong)
**SUN-3** (4 legs, est. +220): miss — Matthew Stafford pass_yds (game-script), Juwan Johnson receptions (read-wrong), Kenneth Walker III rush_att (yard-short)
**TNF-1** (3 legs, est. +166): miss — TreVeyon Henderson rush_yds (read-wrong)

---

## What missed

| Player | Rung | Actual | Missed by | Reason |
|---|---|---|---|---|
| Alvin Kamara | 10 rush_yds | 5 | 5 | read-wrong |
| Nico Collins | 50 rec_yds | 6 | 44 | game-script |
| Aaron Jones | 30 rush_yds | 26 | 4 | yard-short |
| J.K. Dobbins | 30 rush_yds | 23 | 7 | read-wrong |
| Matthew Stafford | 220 pass_yds | 195 | 25 | game-script |
| Juwan Johnson | 3 receptions | 1 | 2 | read-wrong |
| Kenneth Walker III | 16 rush_att | 14 | 2 | yard-short |
| TreVeyon Henderson | 20 rush_yds | 9 | 11 | read-wrong |

Notes on categorization: Kamara entered at L10 10/10, L15 15/15 against a neutral defense with neutral own volume — nothing in the tags flagged this; the outcome (5 yards on a 10-yard rung) looks like a read-wrong. Collins had a tough defense tag; 6 yards on a 50-yard rung fits game-script driven by that matchup. Aaron Jones missed by 4 yards with a neutral defense and neutral volume — yard-short. Dobbins had a soft defense and missed by 7; that is a read-wrong, not a matchup failure. Stafford's pass volume was tagged SOFT (favorable) and his last three were 317/383/222; the low output reads as game-script. Johnson's last three were 6/4/0 — high variance for the rung; read-wrong. Walker missed by 2 attempts against a tough defense — yard-short. Henderson had favorable volume and neutral defense; the 9-yard result on a 20-yard rung is read-wrong.

---

## Does 80% mean 80%

| Bucket | Legs | Hit rate |
|---|---|---|
| <75% | 1 | 0.0% |
| 75–85% | 14 | 50.0% |

One bucket with 14 legs showing 50% against a modeled rate near 80% is a meaningful miss, not noise; the model overestimated hit probability on this slate by roughly 30 points in the core range where nearly all legs sat.

---

## Price check

| Player | Market | Rung | Est | Real | Diff | Hit |
|---|---|---|---|---|---|---|
| Alvin Kamara | rush_yds | 10 | −190 | −294 | −104 | No |
| Jaxon Smith-Njigba | rec_yds | 70 | −284 | −294 | −10 | Yes |
| Jonathan Taylor | rush_att | 14 | −639 | −350 | +289 | Yes |
| Jaxon Smith-Njigba | rec_yds | 70 | −284 | −294 | −10 | Yes |
| Nico Collins | rec_yds | 50 | −236 | −254 | −18 | No |
| Aaron Jones | rush_yds | 30 | −177 | −209 | −32 | No |
| J.K. Dobbins | rush_yds | 30 | −285 | −422 | −137 | No |
| Matthew Stafford | pass_yds | 220 | −353 | −307 | +46 | No |
| Juwan Johnson | receptions | 3 | −336 | −291 | +45 | No |
| Kenneth Walker III | rush_att | 16 | −441 | −272 | +169 | No |
| D'Andre Swift | rush_yds | 40 | −315 | −382 | −67 | Yes |
| TreVeyon Henderson | rush_yds | 20 | −155 | −194 | −39 | No |

Estimates were mostly tighter than market (underestimated the price) — 8 of 12 legs came in cheaper than estimated, meaning the card got better prices than the model projected on most legs; the two large outliers in the other direction (Jonathan Taylor at −639 est vs. −350 real, Kenneth Walker at −441 est vs. −272 real) represent the model overpricing those rungs by a wide margin.

---

## The whole board

| Grade | Legs | Hits | Misses | Hit rate |
|---|---|---|---|---|
| A+ | 3 | 2 | 1 | 66.7% |
| A | 19 | 12 | 7 | 63.2% |
| A− | 82 | 58 | 24 | 70.7% |
| B | 103 | 77 | 26 | 74.8% |
| C | 83 | 60 | 21 | 72.3% |
| D | 0 | — | — | — |
| F | 119 | 36 | 80 | 30.3% |

The grades did not sort the board the way the model intends: A+ and A legs hit at lower rates than B and C legs this week, so the letter's selectivity did not add value on this slate relative to the broader held population at those grade levels.

---

## Sunday prices

| Player | Market | Rung | Thursday | Published | Closing | Thu→Pub (pts) | Pub→Close (pts) |
|---|---|---|---|---|---|---|---|
| Alvin Kamara | rush_yds | 10 | −318 | −294 | −268 | −1.46 | −1.79 |
| Jaxon Smith-Njigba | rec_yds | 70 | −262 | −294 | −288 | +2.24 | −0.39 |
| Jonathan Taylor | rush_att | 14 | −454 | −350 | −403 | −4.17 | +2.34 |
| Jameson Williams | rec_yds | 30 | −323 | −333 | −314 | +0.55 | −1.06 |
| Nico Collins | rec_yds | 50 | −242 | −254 | −239 | +0.99 | −1.25 |
| Aaron Jones | rush_yds | 30 | no Thursday price | −209 | −206 | — | −0.32 |
| J.K. Dobbins | rush_yds | 30 | −475 | −422 | −408 | −1.77 | −0.53 |
| Matthew Stafford | pass_yds | 220 | −399 | −307 | −356 | −4.53 | +2.64 |
| Juwan Johnson | receptions | 3 | −296 | −291 | −317 | −0.32 | +1.59 |
| Kenneth Walker III | rush_att | 16 | −277 | −272 | −321 | −0.36 | +3.13 |
| Michael Wilson | rec_yds | 30 | −345 | −320 | −321 | −1.34 | +0.06 |

Waiting for Friday helped on balance: seven of the ten legs with Thursday prices saw the published price improve (lengthen) relative to Thursday, and the two largest Thursday-to-published moves were both in the card's favor (Jonathan Taylor −4.17 pts, Matthew Stafford −4.53 pts), though both of those legs lost.

---

## What we held back

| Reason | Held | Hits | Misses | Hit rate |
|---|---|---|---|---|
| team change | 5 | 3 | 2 | 60.0% |
| blowout risk | 0 | — | — | — |
| tough defense | 0 | — | — | — |
| low own volume | 27 | 22 | 5 | 81.5% |
| price worse than −450 | 29 | 23 | 6 | 79.3% |
| edge below +2 | 102 | 63 | 39 | 61.8% |
| grade below C | 21 | 10 | 10 | 47.6% |
| injury | 3 | 1 | 2 | 66.7% |
| held by hand | 0 | — | — | — |

**Low own volume (27 legs, 81.5%):** The legs held for this reason hit at a rate well above the card's 46.7%, which is what the hold is designed to protect — but the sample is small enough that one week's result does not reverse the rule's logic.

**Price worse than −450 (29 legs, 79.3%):** Similar picture: legs held for extreme price hit at 79%, well above the card
