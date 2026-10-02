# Model change log

Changes to how the NFL card, grades and record are built. Newest first. Each entry: date, type, what changed, why,
and what it did to published cards.

## 2026-10-02 — Thursday Sunday-slate price snapshot (data collection, not a model change)

- **What:** `sun-snapshot.yml` runs Thursday 9:07 ET and saves DraftKings prices for the coming Sunday slate to
  `automation/lines/snapshots/` (`fetch_lines.py --snapshot`, pull time in the filename). No floors, card, site publish
  or newsletter draft. Friday's card puts each Sunday leg's Thursday price first in its `price_history`; the Card tab
  shows Thursday › published → current; Tuesday receipts report Thursday → published and published → close per leg.
- **Why:** to see how much Sunday prices move between Thursday and the Friday card, before deciding anything about
  when to publish.
- **Effect:** none on tickets, grades or CLV (CLV is still published vs close). About 14 requests per Sunday game
  (~196 a week), counted in the usage ledger and the weekly cap.

## 2026-10-02 — results and record (display / record-keeping, not a model change)

- **What:** `settle.py` (daily 10:07 ET, `settle.yml`) writes each final game's stat (`actual`) and per-rung result
  (hit / miss / void) into the week's legs JSON — nflverse only, never touching grades, prices or published fields;
  idempotent. The Legs tab shows a result circle per row and rung and a board tally (rows the table shows, best rung).
  Tuesday receipts add held legs graded by hold reason and the whole board by grade, cumulative. Cards now keep every
  hold in `held_all` (`held` stays the top 15 for display).
- **Why:** results the morning after, and a check on whether the holds and the letters are doing their job.
- **Effect:** none on cards or grades. Weeks 2–3 regraded (results unchanged). Held-by-reason for weeks 2–3 covers only
  each card's top-15 held list; full lists from Week 4 on.

## 2026-09-30 — bug fix: card legs must be graded C or better (R9)

- **What:** `build_card_json.py` now holds any floor whose Legs-board grade is below C (or that the Legs board didn't
  grade) with the reason "grade below C" — the same cutoff the Legs tab uses. New house rule R9. If that leaves no
  valid ticket (R7: a single-game slate needs 2 legs), the card has no ticket; it is never padded with a weaker leg.
- **Why:** the card checked edge (R4), price, matchup and volume but never the grade, so the Week 4 TNF card
  (built 2026-09-30 13:39 UTC) put a D-grade leg on TNF-1: Jerry Jeudy 15+ rec yds (−106), paired with Harold
  Fannin Jr. 25+ rec yds (−330, B).
- **Effect:** rebuilt from the same pull (prices 2026-09-30 13:39 UTC), Week 4 TNF has no ticket; Fannin 25+ rec yds
  is the only leg that clears every rule and is listed as a single. Jeudy's rungs are held "grade below C".
