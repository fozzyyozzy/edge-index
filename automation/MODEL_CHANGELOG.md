# Model change log

Changes to how the NFL card, grades and record are built. Newest first. Each entry: date, type, what changed, why,
and what it did to published cards.

## 2026-09-30 — bug fix: card legs must be graded C or better (R9)

- **What:** `build_card_json.py` now holds any floor whose Legs-board grade is below C (or that the Legs board didn't
  grade) with the reason "grade below C" — the same cutoff the Legs tab uses. New house rule R9. If that leaves no
  valid ticket (R7: a single-game slate needs 2 legs), the card has no ticket; it is never padded with a weaker leg.
- **Why:** the card checked edge (R4), price, matchup and volume but never the grade, so the Week 4 TNF card
  (built 2026-09-30 13:39 UTC) put a D-grade leg on TNF-1: Jerry Jeudy 15+ rec yds (−106), paired with Harold
  Fannin Jr. 25+ rec yds (−330, B).
- **Effect:** rebuilt from the same pull (prices 2026-09-30 13:39 UTC), Week 4 TNF has no ticket; Fannin 25+ rec yds
  is the only leg that clears every rule and is listed as a single. Jeudy's rungs are held "grade below C".
