# Week 6 receipts

## Week 6 Receipts — 2026 Season

## The record

10 legs graded. 4 hits. Hit rate: 40%.

Average model probability: 74.8%. Actual rate: 40%. The model ran hot by 34.8 percentage points. That is the widest gap this season.

Flat 1u P&L: -4.24u. Ticket record: 0-3-0.

| Ticket | Legs | Result | Misses |
|--------|------|--------|--------|
| SUN-1 | 4 | LOSS | Omarion Hampton (rush_att), Bijan Robinson (rush_yds), Juwan Johnson (rec_yds) |
| SUN-2 | 3 | LOSS | Kyren Williams (rush_yds) |
| SUN-3 | 3 | LOSS | Xavier Hutchinson (rec_yds), Davante Adams (receptions) |

---

## What missed

| Player | Rung | Actual | Missed by | Reason |
|--------|------|--------|-----------|--------|
| Omarion Hampton | 8 rush_att | 7 | 1 | yard-short |
| Bijan Robinson | 70 rush_yds | 61 | 9 | read-wrong |
| Juwan Johnson | 25 rec_yds | 0 | 25 | injury/void |
| Kyren Williams | 60 rush_yds | 50 | 10 | game-script |
| Xavier Hutchinson | 15 rec_yds | 10 | 5 | read-wrong |
| Davante Adams | 4 receptions | 3 | 1 | yard-short |

Notes on each:

**Hampton** — one carry short, L10 10/10 and L15 15/15 entering the game. The opp_d was TOUGH; own_vol was SOFT (high team volume). The defense won a coin flip. Classified yard-short given the 1-carry margin.

**Robinson** — no structural problem in the note: opp_d neutral, own_vol SOFT, last three games showed 194/145/86. He had rushed for 70+ in 9 of his last 10. Nothing in the tags points to a systemic read error; the game produced 61. Read-wrong: the model's blended probability was priced correctly but the game outcome fell in the 10% tail.

**Johnson** — 0 receiving yards. Last three: 53/59/16. The note shows no injury flag in the data provided, but a zero-yard game from a player with a 14/15 clear rate almost always traces to game-script disruption or a hidden status issue. Reason logged as injury/void pending any additional game log; absent that data field, the most consistent explanation is game-script/injury.

**Williams** — opp_d SOFT, own_vol neutral. Hit 60+ in 8 of last 10. The favorable defense and the miss together suggest the Rams' game script reduced his carries rather than the matchup going against him. Game-script.

**Hutchinson** — opp_d SOFT, own_vol SOFT. Last three: 51/46/65. A favorable defense and a 10-yard outcome is a read-wrong; no tag here flags a known depressor.

**Adams** — one catch short in a favorable matchup (opp_d SOFT, own_vol SOFT). Last three: 7/4/5. Yard-short given the 1-catch margin.

---

## Does 80% mean 80%

| Bucket | Legs | Hit rate |
|--------|------|----------|
| <75% | 4 | 25% |
| 75–85% | 6 | 50% |

Both buckets came in well below their model expectations. The <75 bucket implies something around 65–74% and hit 25%; the 75–85 bucket should clear roughly 75–85% and hit 50%. One week is 10 legs and nothing here is diagnostic, but the model ran cold at every level this slate.

---

## Price check

| Player | Market | Rung | Est | Real | Diff | Hit |
|--------|--------|------|-----|------|------|-----|
| Nico Collins | rec_yds | 50 | -267 | -272 | -5 | Y |
| Omarion Hampton | rush_att | 8 | -343 | -349 | -6 | N |
| Bijan Robinson | rush_yds | 70 | -310 | -314 | -4 | N |
| Juwan Johnson | rec_yds | 25 | -245 | -306 | -61 | N |
| Nico Collins* | rec_yds | 50 | -267 | -272 | -5 | Y |
| Chris Godwin | receptions | 3 | -226 | -202 | +24 | Y |
| Kyren Williams | rush_yds | 60 | -170 | -184 | -14 | N |
| Xavier Hutchinson | rec_yds | 15 | -111 | -111 | 0 | N |
| Bucky Irving | receptions | 2 | -208 | -188 | +20 | Y |
| Davante Adams | receptions | 4 | -210 | -196 | +14 | N |

*Nico Collins appears twice in the source data; both rows are identical and one is a duplicate.

Most estimates were within 6 points of the real price. The outlier is Juwan Johnson at -61: the model estimated -245 and the market priced -306, a significant underestimate of how short the book set that line. Excluding Johnson, estimates were slightly generous (real prices tended to be a bit shorter than estimated), which is the preferred direction. Johnson is worth monitoring as a pricing exception.

---

## The whole board

| Grade | Legs | Hits | Misses | Voids | Hit rate |
|-------|------|------|--------|-------|----------|
| A+ | 1 | 1 | 0 | 0 | 100% |
| A | 17 | 8 | 8 | 1 | 50% |
| A- | 63 | 52 | 10 | 1 | 83% |
| B | 60 | 50 | 10 | 0 | 83% |
| C | 65 | 50 | 14 | 1 | 77% |
| D | 11 | 10 | 1 | 0 | 91% |
| F | 195 | 57 | 134 | 4 | 29% |

The grades did not sort cleanly this week: A graded at 50% while A-, B, C, and D all clustered between 77–91%, and D outperformed A. F at 29% correctly sits at the bottom, and A+ at 100% correctly sits at the top, but the middle of the board inverted. The sample within any single grade is small and one week is not sufficient to draw structural conclusions, but the A tier underperformed relative to grades below it.

---

## Sunday prices

| Player | Market | Rung | Thursday | Published | Closing | Thu→Pub (pts) | Pub→Close (pts) |
|--------|--------|------|----------|-----------|---------|----------------|-----------------|
| Nico Collins | rec_yds | 50 | -299 | -272 | -284 | -1.82 | +0.84 |
| Omarion Hampton | rush_att | 8 | no Thursday price | -349 | -364 | — | +0.72 |
| Bijan Robinson | rush_yds | 70 | -297 | -314 | -345 | +1.03 | +1.68 |
| Juwan Johnson | rec_yds | 25 | -302 | -306 | -319 | +0.25 | +0.76 |
| Chris Godwin | receptions | 3 | -200 | -202 | -194 | +0.22 | -0.90 |
| Kyren Williams | rush_yds | 60 | -186 | -184 | -171 | -0.25 | -1.69 |
| Xavier Hutchinson | rec_yds | 15 | no Thursday price | -111 | -110 | — | -0.23 |
| Bucky Irving | receptions | 2 | -181 | -188 | -193 | +0.86 | +0.59 |
| Davante Adams | receptions | 4 | -231 | -196 | -203 | -3.57 | +0.78 |

Positive points = price shortened (less favorable); negative = price lengthened (more favorable).

Waiting for Friday was a mixed result: Collins moved in our favor by 1.82 points between Thursday and publication, and Adams moved favorably by 3.57 points, but Robinson cost 1.03 points and Bucky Irving cost 0.86. On the five legs with Thursday prices, three moved against us Thursday to publish and two moved in our favor — no consistent directional advantage from waiting.

---

## What we held back

| Reason | Held | Hits | Misses | Voids | Hit rate |
|--------|------|------|--------|-------|----------|
| team change | 16 | 12 | 4 | 0 | 75% |
| blowout risk | 5 | 5 | 0 | 0 | 100% |
| tough defense | 0 | — | — | — | — |
| low own volume | 32 | 27 | 5 | 0 | 84% |
| price worse than −450 | 28 | 26 | 2 | 0 | 93% |
| edge below +2 | 88 | 67 | 20 | 1 | 76% |
| grade below C | 49 | 33 | 13 | 3 | 69% |
| injury | 
