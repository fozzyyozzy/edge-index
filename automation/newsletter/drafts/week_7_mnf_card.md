# Week 7 MNF card

## Week 7 MNF Card — Edge Index

This is a single-game Monday Night Football slate. Under R1 and R7, the card is limited to one ticket of 2–3 legs, and any ticket with only two legs carries the "Reduced payout" label.

The model produced no qualifying legs for this slate. Every candidate that cleared the L10/L15 thresholds failed at least one hard gate — edge below +2 pts (R4), price worse than −450 (a hold reason), own volume low (R6 analog via own_vol TOUGH), or grade below C (R9). With no legs meeting the minimum standard, R9 applies: no ticket is built. The card has no ticket this slate.

## The tickets

None. No leg cleared all of R3, R4, R9, and the price/volume holds simultaneously. A ticket was not padded with a weaker leg (R9, R10).

## Floors as singles

No floors cleared the qualifying thresholds. The `floors_singles` field returned empty.

## Held back

| Player | Market | Rung | Est. price | L10 / L15 | Last 3 | Reasons |
|---|---|---|---|---|---|---|
| Javonte Williams | rush_yds | 40+ | −498 | 8/10 / 13/15 | 62, 45, 41 | own volume low; price worse than −450; edge −6.5 pts (< +2) |
| Javonte Williams | rush_att | 12+ | −593 | 8/10 / 13/15 | 19, 12, 11 | own volume low; price worse than −450; edge −8.0 pts (< +2); grade below C |
| Ryan Flournoy | rec_yds | 15+ | −509 | 10/10 / 11/15 | 37, 90, 40 | price worse than −450; edge −9.8 pts (< +2) |
| Dak Prescott | pass_yds | 240+ | −241 | 8/10 / 13/15 | 335, 316, 258 | edge +0.6 pts (< +2) |
| Jake Ferguson | receptions | 2+ | −388 | 8/10 / 13/15 | 3, 3, 2 | edge −4.5 pts (< +2) |
| CeeDee Lamb | receptions | 5+ | −555 | 8/10 / 12/15 | 17, 2, 9 | price worse than −450; edge −7.5 pts (< +2) |
| Dak Prescott | pass_cmps | 20+ | −578 | 8/10 / 13/15 | 32, 24, 34 | price worse than −450; edge −7.8 pts (< +2) |

A few observations on what the data shows, without drawing conclusions beyond it. Flournoy is 10/10 over the last ten games at 15+ receiving yards, but the L15 rate drops to 11/15, and the price is −509 — both the price hold and the edge gap (−9.8 pts) trigger independently. Prescott's pass_yds at 240+ is the closest call at +0.6 pts of edge, but R4 requires +2 pts minimum and it does not reach that. CeeDee Lamb's receptions last three (17 catches one game, 2 the next) illustrate the variance that makes the L15 rate (12/15) less convincing than it appears.

## Notes

No author notes were provided for this slate. The notes field was empty.

---

What would change our mind: any line move that pushes Prescott pass_yds to a rung where blended edge clears +2 pts, or a Flournoy line shift that drops the price below −450 while the L15 rate holds at 13/15 or better.

*(Prices as pulled Monday 3:10 PM ET)*
