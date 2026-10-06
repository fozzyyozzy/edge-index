# Week 4 receipts

## The record

8 legs graded, 5 hits, 62.5% hit rate. Average model probability was 79.2%; actual rate was 62.5%, so the model ran hot by 16.7 percentage points this week. Flat 1u P&L: -1.33u on legs; ticket record 0-2-0, -2.0u on tickets.

SUN-1 (4 legs, est. +217): **LOSS** — missed Cooper Kupp (rec_yds), Christian McCaffrey (receptions).
SUN-2 (4 legs, est. +233): **LOSS** — missed Jacoby Brissett (pass_yds).

---

## What missed

| Player | Rung | Actual | Missed by | Reason |
|---|---|---|---|---|
| Cooper Kupp | 15+ rec_yds | 13 | 2 | yard-short |
| Christian McCaffrey | 4+ receptions | 3 | 1 | yard-short |
| Jacoby Brissett | 200+ pass_yds | 166 | 34 | read-wrong |

Kupp and McCaffrey both cleared their rungs in 9 of their last 10 appearances entering the week; both missed by the minimum margin with neutral opponent defense and neutral volume context. These are yard-short results, not model failures. Brissett is different. His own-volume flag was SOFT, his last 10 included a 95-yard line, and he fell 34 yards short. The note flags this was at floor rung, but a SOFT own-volume tag with a volatile recent line is a read-wrong miss; the SOFT tag should have been disqualifying.

---

## Does 80% mean 80%

| Bucket | N | Hit rate |
|---|---|---|
| 75–85% | 8 | 62.5% |

One bucket, one week — eight legs all priced 75–85%, hitting at 62.5% against an expected 79.2%. The model ran materially hot; calibration cannot be assessed from a single bucket and eight observations, but the gap is wide enough to note.

---

## Price check

| Player | Market | Rung | Est | Real | Diff | Hit |
|---|---|---|---|---|---|---|
| Jakobi Meyers | rec_yds | 25 | -237 | -295 | -58 | Y |
| Kyren Williams | rush_yds | 40 | -275 | -349 | -74 | Y |
| Cooper Kupp | rec_yds | 15 | -199 | -256 | -57 | N |
| Christian McCaffrey | receptions | 4 | -348 | -309 | +39 | N |
| Jaxon Smith-Njigba | rec_yds | 70 | -272 | -269 | +3 | Y |
| Brian Thomas Jr | receptions | 2 | -280 | -256 | +24 | Y |
| Jacoby Brissett | pass_yds | 200 | -306 | -280 | +26 | N |

Note: Kyren Williams appears twice in the source data at the same rung and odds; it is the same leg anchoring both tickets and is listed once here.

Estimates ran generous — five of seven legs were cheaper than estimated, some meaningfully so (Meyers -58, Williams -74, Kupp -57). The two legs where the market was looser than estimated (McCaffrey, Brissett) both missed, which is an unfavorable pattern worth tracking.

---

## The whole board

| Grade | N | Hits | Misses | Voids | Hit rate |
|---|---|---|---|---|---|
| A+ | 2 | 2 | 0 | 0 | 100% |
| A | 15 | 12 | 3 | 0 | 80% |
| A- | 78 | 66 | 11 | 1 | 85% |
| B | 89 | 67 | 19 | 3 | 75% |
| C | 80 | 65 | 15 | 0 | 81% |
| D | 19 | 12 | 6 | 1 | 63% |
| F | 188 | 53 | 125 | 10 | 28% |

The board sorted correctly at the extremes: A+ and A- hit well above B and D, and F hits at 28%. The C-grade rate (81%) running above B (75%) is a minor inversion, but both samples are large enough to treat seriously. Overall, higher grades hit more often — the model is sorting the board.

---

## Sunday prices

No Thursday prices were available for any leg this week. All Thursday moves are listed as "no Thursday price."

| Player | Market | Rung | Published | Closing | Pub→Close (implied prob pts) |
|---|---|---|---|---|---|
| Jakobi Meyers | rec_yds | 25 | -295 | -292 | -0.19 |
| Kyren Williams | rush_yds | 40 | -349 | -361 | +0.58 |
| Cooper Kupp | rec_yds | 15 | -256 | -236 | -1.67 |
| Christian McCaffrey | receptions | 4 | -309 | -309 | 0.00 |
| Jaxon Smith-Njigba | rec_yds | 70 | -269 | -259 | -0.75 |
| Brian Thomas Jr | receptions | 2 | -256 | -249 | -0.56 |
| Jacoby Brissett | pass_yds | 200 | -280 | -272 | -0.57 |

Positive pub-to-close means the price shortened (worse for late buyers); negative means it lengthened (better value available late). Five of seven legs drifted longer after publication — Kupp most sharply at -1.67 implied-probability points — suggesting the market was fading these rungs and that waiting for Friday or Saturday would have found better prices on most legs. With no Thursday data available this week, the Thursday-to-published move cannot be evaluated.

---

## What we held back

| Hold reason | N | Hits | Misses | Voids | Hit rate |
|---|---|---|---|---|---|
| edge below +2 | 108 | 82 | 21 | 5 | 76% |
| grade below C | 53 | 38 | 11 | 4 | 72% |
| price worse than -450 | 37 | 28 | 6 | 3 | 76% |
| low own volume | 33 | 22 | 9 | 2 | 67% |
| tough defense | 54 | 44 | 10 | 0 | 81% |
| team change | 20 | 13 | 5 | 2 | 65% |
| blowout risk | 4 | 3 | 1 | 0 | 75% |

**Edge below +2 (108 legs):** The held pool hit at 76%, above the card's 62.5% this week. That is a single-week result on a volatile sample; it does not mean the hold rule is wrong, but it is worth watching.

**Grade below C (53 legs):** 72% hit rate. Held correctly; these legs cleared at a lower rate than A/A- grades on the board.

**Price worse than -450 (37 legs):** 76% hit rate. The hold rule is keeping out legs that hit, but at prices that destroy value. The hold stands.

**Low own volume (33 legs):** 67% hit rate, the lowest of the meaningful hold categories. The Brissett miss this week fell into this bucket on the card itself; the hold flag existed and was overridden. That was wrong.

**Tough defense (54 legs):** 81% hit rate held back. The sample says these legs actually clear well; this deserves a closer look at whether "tough defense" is being applied too broadly.

**Team change (20 legs):** 65% hit rate, small sample — nothing to conclude.

**Blowout risk (4 legs):** Too small to say anything useful.

---

## What changes

**One change:** The SOFT own-volume flag must be a hard hold, not a soft caution. Brissett carried the flag, made the card, and missed by 34 yards. The data on held low-own-volume legs (67% hit rate) runs below every other hold category except team change. A SOFT tag combined with any volatility in the recent line should remove the leg from consideration, not lower its grade.

**One thing to watch:** The tough-defense hold category hit at 81% in the held pool this week, above even A- card legs. That is one week of data and not actionable yet, but if this persists over the next three to four weeks, the definition of "tough defense" as a disqualifier should be narrowed.

Nothing else changes this week.

---

What would change our mind: two or three consecutive weeks where A+ and A legs miss at rates consistent with A- or below would indicate the grade model is not separating signal from noise at the top of the board.
