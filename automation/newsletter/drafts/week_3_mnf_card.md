# Week 3 MNF card

## The tickets

No tickets were built for this slate. The `tickets` array in the source data is empty, and the card rules require 3–4 legs per ticket before one can be issued. No qualifying combination cleared all filters simultaneously.

---

## Floors as singles

The `floors_singles` array in the source data is also empty. No legs cleared the floor threshold and passed the price, edge, and opponent-defense filters after the held list was removed.

---

## Held back

Every flagged leg fell into one of two rejection buckets. Reasons are taken directly from the data.

**Opponent defense too tough — model passes the rate test but the matchup overrides**

| Player | Market | Rung | Est. price | L10 / L15 | Last 3 | Reason |
|---|---|---|---|---|---|---|
| Luther Burden III | rec_yds | 25+ | -216 | 10/10 / 12/15 | 35, 63, 32 | opp D tough |
| Luther Burden III | receptions | 3+ | -239 | 10/10 / 12/15 | 3, 5, 3 | opp D tough |
| Rome Odunze | receptions | 2+ | -272 | 9/10 / 14/15 | 2, 2, 3 | opp D tough |
| Rome Odunze | rec_yds | 27+ | -109 | 8/10 / 12/15 | 8, 52, 43 | opp D tough |
| Cole Kmet | rec_yds | 9+ | -109 | 8/10 / 11/15 | 16, 35, 0 | opp D tough |
| Colston Loveland | rec_yds | 25+ | -186 | 8/10 / 11/15 | 91, 0, 3 | opp D tough |
| Colston Loveland | receptions | 3+ | -208 | 8/10 / 12/15 | 10, 0, 1 | opp D tough |

The three Bears skill players (Burden, Odunze, Kmet, Loveland) face the same defense. The floor rates are real, but the card rule is every leg winnable first. Sitting four Bears legs on a tough-D night is the right call even when the L10 is clean, particularly with Caleb Williams out and the offense in transition — see Notes below.

**Price worse than -450 or model edge below +2 points**

| Player | Market | Rung | Est. price | L10 / L15 | Last 3 | Reason |
|---|---|---|---|---|---|---|
| D'Andre Swift | rush_yds | 40+ | -493 | 9/10 / 13/15 | 40, 124, 45 | price > -450; edge -2.1 pts |
| Saquon Barkley | rush_yds | 40+ | -549 | 8/10 / 12/15 | 68, 83, 9 | price > -450; edge -7.3 pts |
| Jalen Hurts | pass_att | 24+ | -428 | 9/10 / 12/15 | 27, 25, 37 | edge -4.6 pts |
| Jalen Hurts | pass_yds | 170+ | -430 | 8/10 / 12/15 | 110, 203, 264 | edge -5.3 pts |
| Kyle Monangai | rush_att | 8+ | -309 | 9/10 / 11/15 | 6, 10, 10 | edge -4.7 pts |
| Kyle Monangai | rush_yds | 25+ | -397 | 8/10 / 11/15 | 14, 100, 47 | edge -7.4 pts |

Swift and Barkley both cross the -450 hard ceiling and both carry negative model edges, so they fail twice. The Hurts legs are priced at the edge of the ceiling and the edge is negative in both directions; holding is automatic. Monangai's edge numbers are the worst on the board despite clean opponent and volume grades.

---

## Notes

The following is the author's external read — scheme and injury context, not model output.

> Outside read (ESPN power rankings, Wk 3) — context, not model output.
>
> Pressure environment: league pressure rate 35%, highest through two weeks since 2009. Lean away from pass-yard overs on QBs with bad pass protection.
>
> QB injuries / changes:
> - CHI: Caleb Williams (hamstring) out, Tyson Bagent starts. Hold all CHI pass legs; Bears run volume likely rises.
> - WAS: Jayden Daniels (elbow) out, Mariota starts vs SEA. Hold WAS pass legs; SEA D is the toughest pass D on the board.
> - MIN: Kyler Murray returns from concussion at TB. Wentz-era receiver numbers understate Jefferson/Addison.
> - NYG: Jaxson Dart status TBD; Winston was 5/12 in relief. Nabers downgrade if Dart out.
> - HOU: Nico Collins (hamstring) missed Wk 2; Schultz 12/140 without him.
> - LAR: Puka Nacua (groin) — Adams is the volume target if Puka sits.
>
> Pressure matchups:
> - PIT @ CIN: Rodgers 8/24 under pressure; CIN generated 27 pressures in Wk 2. Rodgers pass unders.
> - JAX vs NE: Lawrence 38.5% completions under pressure; NE blitzed 18 times in Wk 2. Lawrence pass unders; floors on JAX receivers only at low rungs.
> - BAL @ DAL: BAL pass block win rate 33-38%, but DAL has 2 sacks all year. Neutral-to-good for Lamar.
>
> Usage notes:
> - Josh Allen: 70 of his 92 rush yards on scrambles; rush floor is scramble-driven, strongest vs man coverage.
> - Geno Smith averaging 5.8 air yards: Garrett Wilson receptions over > yards over.
> - Deshaun Watson ADOT 3.7: CLE backs and TE (Fannin) receptions floors; WR yard ceilings capped.
> - Tyler Shough: 14.3 QBR in first three quarters, 97.7 in the fourth. Full-game yards fine; avoid 1H props.
> - KC: Mahomes more under center / play-action with Kenneth Walker III; Walker rush volume is real.

---

What would change our mind: a line move of three or more points off the opener on any of the Burden, Odunze, or Walker legs, combined with confirmation that the opponent secondary is missing a starter — at that point the tough-D tag softens enough to revisit.

*(Prices as pulled Monday 4:03 PM ET)*
