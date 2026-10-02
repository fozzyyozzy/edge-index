# Model change log

Changes to how the NFL card, grades and record are built. Newest first. Each entry: date, type, what changed, why,
and what it did to published cards.

## 2026-10-02 — bug fix: R2 repeated-star cap was only checked on the later ticket

- **What:** `build_card_json.py` now limits each ticket to one player shared with all the other tickets combined.
  The limit applies to every ticket the shared player is on, not just the ticket that takes him second.
- **Why:** R2 says a ticket may carry at most one repeated star. The code counted repeats only on the ticket being
  built, so the first ticket could share one star with SUN-2 and another with SUN-3. The Week 4 Sunday rebuild had
  this problem: SUN-1 shared Jakobi Meyers with SUN-2 and Rashee Rice with SUN-3.
- **Effect:** Week 4 Sunday SUN-3 no longer repeats Rice (see the R6 entry below for the final tickets). The
  published Week 3 Sunday card had the same violation: SUN-1 shared Derrick Henry and Juwan Johnson with other
  tickets. It stays as published and graded, because the record is locked. No other 2026 card is affected.

## 2026-10-02 — bug fix: R6 injury holds were never implemented

- **What:** new `pipeline/availability.py`, run by `grade_legs.py` (snapshot saved to
  `cards/availability_<season>_w<week>_<slate>.json`) and read by `build_card_json.py`, so the Legs tab and the card
  hold the same players for the same reasons. Sources are nflverse snap counts, nflverse weekly stats and the nflverse
  injury report, plus a manual file, `notes/holds_<season>_w<week>.csv` (Player,Reason).
  - **Hold** (grade F on the Legs tab, never on a ticket):
    - no offensive snaps in the team's most recent game;
    - report status Out, Doubtful or Questionable;
    - did not practice (a veteran rest day doesn't count);
    - held by hand.
  - **Injury watch** (a flag on the Legs tab and Card tab; it doesn't change the grade):
    - no offensive snaps in the game before that, but played the most recent one;
    - limited in practice with no game status yet.
- **Why:** R6 said "team-change and injury holds are hard holds", but only team change was in the code. The Week 4
  Sunday card (prices 2026-10-02 17:51 UTC) used Nico Collins 50+ rec yds (−327, A+) as the anchor leg of both SUN-1
  and SUN-2. Collins missed Weeks 2–3 (hamstring), was limited in practice and is questionable, and nothing caught it.
  His L10/L15 come from games played before the injury.
- **Effect:** Week 4 Sunday was rebuilt from the same 17:51 UTC prices, with no new odds pull. Collins is held by hand
  ("questionable, returning from 2-game hamstring absence") and by the automatic rule. The other automatic holds are
  Puka Nacua, Jaylen Wright and Isaiah Davis. New tickets:
  - **SUN-1 (+227):** Meyers 25+ rec yds, Rice 4+ rec, Kupp 15+ rec yds, McCaffrey 4+ rec.
  - **SUN-2 (+302):** Meyers 25+ rec yds, Kyren Williams 12+ rush att, Pat Bryant 15+ rec yds, Prescott 240+ pass yds.
  - **SUN-3 (+218):** Brian Thomas Jr. 2+ rec, Brissett 210+ pass yds, Smith-Njigba 80+ rec yds. The R2 fix above
    took Rice off this ticket; at 3 legs it still clears +200.

  No grade changed except on the held players. The card was published without waiting for Friday's final injury
  report. Meyers (limited in practice, thumb) is on SUN-1 and SUN-2 as an injury watch. The card is locked from here:
  injury-watch flags may update, the tickets won't.

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
