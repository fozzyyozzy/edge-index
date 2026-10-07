# Model change log

Changes to how the NFL card, grades and record are built. Newest first. Each entry: date, type, what changed, why,
and what it did to published cards.

## 2026-10-07 — downloads survive upstream changes (process, not a model change)

- **What:**
  - **One download path.** Every outside download (nflverse stats, schedule, injuries and snap counts; The Odds API)
    goes through `common.download()`.
  - **Retries.** Three tries per URL with backoff (5s, then 15s) on network errors, timeouts, 429 and 5xx. A 404 or
    another permanent error moves straight on.
  - **Fallbacks.** Each nflverse file falls back to its `.csv.gz` copy, and the schedule also to the nfldata mirror.
    The Odds API has no second source, so it gets retries only.
  - **Errors.** When every source fails, the error names the source and every URL tried, with API keys redacted.
  - **Automatic retry.** `retry-failed.yml` re-runs a failed scheduled settle-results or refresh-odds run once,
    about an hour later. The refresh retry uses the scheduled slot guard. card.yml is never retried automatically.
  - **Test.** `tests/test_downloads.py` fails if any pipeline or newsletter code opens a URL outside `download()`,
    puts a download URL anywhere but `common.SOURCES`, or adds a source without a fallback or a written reason.
- **Why:** on 2026-10-06 at 19:47 UTC nflverse replaced `games.csv` with `games.csv.gz`. Every schedule read
  returned 404, and the 20:13 UTC settle run failed. It was patched by hand at 08:39 ET today, before the week 5 TNF
  card.
- **Effect:** none on cards or grades.

## 2026-10-07 — fix: tough defense was counted twice (grade step + card hold)

- **What:** `build_card_json.py` no longer holds a leg for "opp D tough". The Legs grade still takes one step off for a
  tough opposing defense (`grade_legs.py`, unchanged). Those legs now compete on grade and edge like everything else,
  and every other hold stays: injury, team change, blowout, own volume low, price past −450, edge below +2 (R4,
  unchanged), grade below C.
- **Why:** the defense was counted twice, once in the grade and again as a hard hold. The held-legs record says the
  hold cost us. Held for tough defense, Weeks 3–4 (Week 3 kept only each card's top-15 holds):
  - **All held for tough D:** 50–11 (82.0%). Average implied probability at the listed single price was 73.0%,
    ours 73.6%. Flat 1u at the listed prices: +13.8% ROI, +8.43u.
  - **Held only for tough D:** 11–3 (78.6%), implied 66.2%, ROI +16.1%.

  This is a hypothesis-grade sample: two weeks, and correlated legs (same player, same game). The held-legs price
  check stays in the Tuesday receipts.
- **Effect on Weeks 3–4:** rebuilt from each card's saved inputs with the current builder, with and without the
  hold. Week 3 TNF and Week 4 MNF are unchanged; the rest change:

  | Card | Before | After |
  |---|---|---|
  | Week 3 Sunday | SUN-1 W, SUN-2 L, SUN-3 L | SUN-1 W, SUN-2 L, SUN-3 L |
  | Week 3 MNF | no ticket | MNF-1 +100 W |
  | Week 4 TNF | no ticket | TNF-1 −147 W |
  | Week 4 Sunday | SUN-1 L, SUN-2 L | SUN-1 L, SUN-2 W, SUN-3 L |

  - Week 3 Sunday: Brenton Strange and Jakobi Meyers (tough D) replace Cade Otton and Juwan Johnson, who move to SUN-3.
  - Week 3 MNF: Luther Burden III and Rome Odunze, both C and both tough D.
  - Week 4 TNF: DK Metcalf (tough D) with Harold Fannin Jr.
  - Week 4 Sunday: Cade Otton (tough D) replaces Brissett on SUN-2. The new SUN-3 is Brissett, Ty Johnson (tough D)
    and Jaylin Noel.

  Published cards are locked (their newsletters went out), so none of this changes the record. The golden fixtures
  are updated to the new rule in the same commit.

## 2026-10-04 — bug fix: Legs board dropped D-graded rungs inside a ladder (display; cards unaffected)

- **What:** `grade_legs.py` now shows every DK rung from the lowest up to the last one graded C or better, D rungs in
  between included. Rungs past −450 are marked "price past −450, not card-eligible", and rungs past −600 get one note,
  "price past −600: not card-eligible" (it replaces "juice past −600: not playable in a parlay"). Every rung it leaves off goes
  into a new `omitted` record with the reason:
  - above the last rung graded C or better;
  - held (only the 3 rungs nearest the DK line are shown);
  - no rung graded C or better;
  - no NFL game log, so his team is unknown.

  `pipeline/legs_coverage.py` checks every DK rung on a slate is either shown or recorded with a reason. card.yml
  adds its result to the QA checklist as a warning that doesn't block the card, and the tests run it on real Week 4
  data.
- **Why:** the trim kept only C-or-better rungs wherever they sat, so rungs a modifier pushed to D left holes:
  - C.J. Stroud showed 160 and 200 but not 170, 180 or 190;
  - Trevor Lawrence was missing 190;
  - 40 holes in all on the Week 4 Sunday board, every one graded D (price past −400/−600, near miss, tough matchup).
- **Effect on cards:** none. Every rung that was missing from the Sunday board graded D or F, so the card builder
  (which uses C or better only) never lost a candidate. Rebuilding Week 4 Sunday from the old and the new Legs file
  gives identical candidates and tickets.

## 2026-10-03 — card QA gate and test suite (process, plus one rule clarification)

- **What:**
  - **`pipeline/card_qa.py`** checks a built card against every house rule, independently of the code that built it:
    R1–R11, the −450 cap, one leg per game, the published price, and that prices and availability actually loaded.
    It recomputes injury holds and flags from the availability snapshot rather than trusting the card.
  - **`card.yml` runs it** right after the card is built.
    - Pass: the checklist goes into the newsletter draft issue.
    - Fail: nothing publishes (no site data, no draft, no card commit), an issue titled "CARD FAILED QA" opens with
      the checklist, and the run fails. Only the Odds API usage-ledger row is committed, so the weekly cap stays right.
  - **`automation/tests`** (pytest; `tests.yml` runs it on every push and pull request):
    - every pipeline script parses and imports;
    - golden rebuilds of Week 3 Sunday, Week 4 TNF and Week 4 Sunday from their saved inputs;
    - house rules on made-up cards;
    - settle and grade on fixed box scores.
- **Rule clarification (R10):** a C leg is never a 4th leg. Three legs already make a ticket, so if no B-or-better
  4th leg fits, the ticket runs at reduced payout instead. Before, a C could fill the 4th spot when nothing better fit.
  None of the saved cards changed.
- **Found on the way:** the odds-refresh job rewrites a slate's legs file, floors and price-pull file with current
  prices after the card is published. Tickets and published prices are untouched (checked for Week 4 Sunday), but a
  later rebuild from main would not use publish-time prices. A rule-fix rebuild under the lock rule must start from
  the card commit's inputs. The golden fixtures do exactly that.
- **Empty slates (found in a dry run of Monday's MNF job):**
  - **Crash fixed:** when no floor leg qualifies, `floors.py` writes an empty file and `build_card_json.py` used to
    crash on it. It now builds a 0-ticket card, which passes QA like Week 4 TNF.
  - **No lines fails QA:** if the slate has no DraftKings lines at all (props not posted by the 9am run), QA fails
    with "no DK lines for this slate's games". Nothing publishes, and a manual card.yml run once props are up
    rebuilds it.
  - **Retries:** availability fetches from nflverse retry 3 times.
  - **Week 4 TNF:** it fails QA only because its card predates availability snapshots. A new card always has one,
    because the build writes it if the Legs grader didn't.
- **Effect:** no published card changed. The Week 4 Sunday fixture rebuilds the live card exactly (SUN-1 +217,
  SUN-2 +233).

## 2026-10-02 — standing rule: a card locks when its newsletter is sent

- **Rule:** before a slate's newsletter is sent, a rule fix may rebuild that card. The rebuild uses the same pulled
  prices, with no new odds pull, and gets a change-log entry. Once the newsletter is sent, the card is locked: no
  rebuilds and no swaps, for any reason. Prices, results and injury-watch flags may still update, but tickets can't.
- **Why:** Week 4 Sunday was rebuilt twice on 2026-10-02 after going live on the site (R6, then grade-first). Both
  times the newsletter hadn't been sent, so nobody had been sold those tickets. That window needs a clear end.
- **Applied:** Week 4 Sunday's rebuilt 2-ticket card (entry below) replaced the live one at 20:20 UTC (www.edge-index.com serving it). Its
  newsletter has not been sent yet.

## 2026-10-02 — strategy change: legs are chosen by grade first (R3, R8, R10, R11)

- **What:** `build_card_json.py` picks legs by Legs-board grade instead of raw clear rate.
  - **R3:** each player/market offers its best-graded qualifying rung. A qualifying rung is any rung at or below the
    floor rung that still clears L10 ≥ 80% and L15 ≥ 73% and passes R4, R9 and the −450 cap. Ties go to higher edge.
    Before, the card only saw the floor rung itself (the highest one that clears).
  - **R10:** candidates rank by grade (A+ > A > A− > B > C), then edge. A C leg is used only when no B-or-better
    leg can fill the spot. A third ticket that would need a C leg is not built, because R1 allows two.
  - **R8:** the 4th leg comes from the best grade available, and payout only chooses within that grade.
  - **R11:** a player with an injury-watch flag goes on one ticket at most.
- **Why:** the published Week 4 Sunday card (prices 2026-10-02 17:51 UTC) used Pat Bryant 15+ rec yds (C) and Dak
  Prescott 240+ pass yds (B, +2.0 edge) while A-tier legs went unused.
  - Kyren Williams 40+ rush yds (A+, −349) and Brian Thomas Jr. 15+ rec yds (A−) were never candidates. Their floor
    rungs were 60+ (C) and 27+ (C).
  - Kyren 12+ rush att (B) outranked them on L10+L15 sum.
  - Prescott was SUN-2's 4th leg because his price landed closest to 3.0x.
- **Evidence:** settled board hit rates by grade, Week 3 (TNF, Sunday, MNF) plus Week 4 TNF:

  | Grade | Every settled rung | Best rung per row |
  |---|---|---|
  | A-tier (A+/A/A−) | 129/141 (91.5%) | 83/91 (91%) |
  | B | 225/256 (88%) | 104/118 (88%) |
  | C | 225/288 (78%) | 69/83 (83%) |
  | D | 29/39 (74%) | 8/10 (80%) |
  | F | 210/496 (42%) | 81/166 (49%) |

  Within the A tier, by rung: A+ 4/4, A 8/10, A− 117/127. This is a hypothesis, not a validated finding.
  - Small samples: only 4 A+ rungs and 10 A rungs.
  - Most rows come from one Sunday board.
  - Rungs on the same player and game are correlated.
  - The cut was read after the question was asked (CLAUDE.md rule 5).

  Re-check once Weeks 4–6 settle.
- **Effect:** Week 4 Sunday was rebuilt from the same 17:51 UTC prices and the same availability snapshot.
  The card that went live earlier today (SUN-1 +227, SUN-2 +302, SUN-3 +218) is replaced before the newsletter went
  out. New card, 2 tickets, no C legs:
  - **SUN-1 (+217):** Jakobi Meyers 25+ rec yds (−295, A+, injury watch), Kyren Williams 40+ rush yds (−349, A+),
    Cooper Kupp 15+ rec yds (−256, A), Christian McCaffrey 4+ rec (−309, A−).
  - **SUN-2 (+233):** Kyren Williams 40+ rush yds (−349, A+), Jaxon Smith-Njigba 70+ rec yds (−269, A),
    Brian Thomas Jr. 2+ rec (−256, A−), Jacoby Brissett 200+ pass yds (−280, A−).

  A third ticket would have needed Calvin Ridley 7+ rec yds (C) after Jaylin Noel (B) and Rashee Rice (B), so it
  isn't built. Kyren is the one repeated star. Meyers is on one ticket only (R11).

## 2026-10-02 — bug fix: R2 repeated-star cap was only checked on the later ticket

- **What:** `build_card_json.py` now limits each ticket to one player shared with all the other tickets combined.
  The limit applies to every ticket the shared player is on, not just the ticket that takes him second.
- **Why:** R2 says a ticket may carry at most one repeated star. The code counted repeats only on the ticket being
  built, so the first ticket could share one star with SUN-2 and another with SUN-3. The Week 4 Sunday rebuild had
  this problem: SUN-1 shared Jakobi Meyers with SUN-2 and Rashee Rice with SUN-3.
- **Effect:** Week 4 Sunday SUN-3 no longer repeats Rice (see the R6 entry below for the tickets published then; the grade-first entry above replaced them). The
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
