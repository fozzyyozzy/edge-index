# CFB Forward Test: 2026 weeks 4+ (pre-registered)

**Pre-registered 2026-10-10 by Tim, before any forward capture was logged.**
Model: the Phase 3 frozen primary (`engine/cfb/model/params.json`, sha256 prefix
`1f56d630ad42`, commit `fb01f2fd`). The model does not change during the test.
**$0 is wagered until the test passes.**

## Why

The 2025 holdout passed on CLV (60.5% of moves toward the model) but failed on k
(+0.16, CI spanning 0). Historical "opens" from CFBD are of uneven quality: DK's 2023 open
equals its close 47% of the time, and the 2026 to-date CLV is implausibly high (88-91%).
This test uses lines **we** timestamp, so bet time and close are known exactly. Since Amendment 1 (below), those lines come from DK snapshots via The Odds API.

## Pass bars

1. **Sample:** 150 games with |model edge| ≥ 1.5 points at bet time. The evaluation
   sample is the **first 150** qualifying games by kickoff. No optional stopping: the
   verdict is computed once, on those 150.
2. **CLV:** the DK close moves toward the model in **≥ 57%** of those games where it moves.
3. **Average move toward the model > +0.3 points** (signed by the model's side; games with
   no move count as 0).
4. **Ratings-only (QB term off) is reported alongside**, computed the same way on the same
   captures. It is informational and not a pass bar.
5. **$0 until 1-3 pass.** ATS results are informational.

Status is IN PROGRESS until 150 qualifying games have a close; then PASSED or FAILED.

## Definitions (fixed before the first capture)

- **Games:** FBS vs FBS, regular season, `week ≥ 4`, with a DraftKings spread at capture.
- **Bet-time line:** the DK spread in the **first** `project_week` log row for that game
  whose capture time is before kickoff. Later projection rows are kept but not scored.
- **Edge:** `projected_home_margin − (−dk_spread)`, from the same row (frozen primary).
  Ratings-only uses `proj_ratings_only` from the same row.
- **Close:** the DK spread in the **last** `capture-close` row taken **before kickoff**
  and after the bet-time capture.
- **Move:** `(−close_spread) − (−bet_spread)`, in home points. "Toward the model" means
  the move has the same sign as the edge.
- **Pregame only:** neither logger ever writes a row for a game that has kicked off.
- **Fresh ratings:** `project_week` refuses to log while any completed FBS game before the
  week's cutoff lacks plays, because the first capture is the scored one.
  Run `update_week` first.

## Weekly procedure

```
python -m engine.cfb.update_week                                   # Sun after ~10:30 ET (~5 calls)
python -m engine.cfb.model.project_week --season 2026 --week N     # 1 call; logs bet-time rows
python -m engine.cfb.model.project_week --season 2026 --week N     # again Mon/Tue as more DK lines post
python -m engine.cfb.model.forward capture-close --season 2026 --week N   # 1 call per run
python -m engine.cfb.model.forward score                           # 0 calls; updates this file
python -m engine.cfb.lines.ladder_edge                             # 0 calls; logs + grades paper rungs (lift + EV at posted price)
python -m engine.cfb.model.forward weekly --week N                 # after week N grades (Sun, post update_week): dated entry below
```

- **Projections:** run `project_week` after `update_week`, and again whenever new DK lines
  have posted (CFBD had only 18 of 59 week-7 lines by Saturday). Only a game's first
  logged line counts, so games that post later get their own first capture then.
- **Closes:** run `capture-close` shortly before each kickoff window, for example weeknight
  games about 1 hour before kickoff, and Saturday around 11:30, 15:00, 18:30 and 21:30 ET.
  Each run logs only games that haven't started. A game's close is its last pre-kickoff
  capture.
- **API budget:** about 2-3 projection calls plus about 6 close calls a week, roughly 35 a
  month. The ledger is `data/cfb/_meta/api_calls.csv`.

## Known limits (pre-registered)

- **The "DK close" is the last DK line CFBD had at our final pre-kickoff capture,** not
  DK's true closing number. CFBD's refresh cadence is unknown, so there may be some lag.
  Phase 5 swaps in The Odds API.
- **Bet time is when the line was captured,** not when a bet could have been placed.
- **QB news enters live only through `data/cfb/manual/qb_overrides.csv`.**

## Logs (committed, append-only)

- `data/cfb/forward/projections_log.csv`: capture time, game, kickoff, DK spread/total,
  the line used, ratings margin, QB delta/note, primary and ratings-only projections, σ,
  and params hash.
- `data/cfb/forward/closes_log.csv`: capture time, game, kickoff, DK spread/total, and
  the providers seen.

## Amendment 1 (2026-10-12, Phase 4 brief §2), made before any game was scored

Capture moved to The Odds API (`engine/cfb/lines/capture.py`, `.github/workflows/cfb_lines.yml`).
The first week-7 kickoff is 2026-10-13 23:00 UTC, so no forward game had been scored. The pass
bars above don't change. Line sources change:

- **Bet-time line:** the DK spread in the **earliest `bet` snapshot** (Tue 10 AM ET) for the
  game. If the game wasn't listed by then, its **first-seen** DK snapshot. The first-seen line
  is also reported alongside, for every game.
- **Close:** the DK spread in the **last snapshot before kickoff** taken after the bet snapshot.
  Snapshots never include games that have started.
- **Projection at the bet line:** the frozen model recomputed at that line,
  `L + k[bucket]·(ratings_margin − L) + b_qb·qb_delta`. Its inputs are taken from the latest
  `projections_log.csv` row captured at or before the bet snapshot (else the earliest row).
  Ratings-only = the same with `qb_delta = 0`.
- **Fallback:** a game with no DK snapshot is scored on the CFBD-captured lines as originally
  defined (`source = cfbd_fallback`).

## Ladder-shape bar (pre-registered 2026-10-12, Phase 4 brief §5, before any rung was graded)

Tests whether DK's alt-spread **pricing** is off, independent of our projection.

- **Shape edge** = our Phase 3 probability **centered at DK's own main line** (frozen σ and
  spikes) − DK's no-vig probability (proportional de-vig within each home/away rung pair).
- **Candidate rungs:** getting points (rung > 0), priced −500 to −150, shape edge ≥ 3 pp, in
  `data/cfb/lines/paper_rungs_2026.csv`. Laying rungs are logged for diagnostics only.
- **Unit:** one rung per game per side, from the game's **bet-time ladder** (earliest `bet`
  snapshot, else its first captured ladder). Among that ladder's candidate rungs for that
  side, it's the one with the largest shape edge.
- **Sample:** the first **60 games** by kickoff with a graded unit.
- **Pass:** realized hit rate − mean DK no-vig probability **≥ +3.0 points**, with a 95% CI
  (game-clustered bootstrap, 2,000 draws) **excluding 0**.
- **$0 until passed.** Grading uses `games.parquet` final margins only.
- **Status** is written to `docs/cfb/PHASE4_REPORT.md` by `python -m engine.cfb.lines.ladder_edge`.

## Floor-card bar (pre-registered 2026-10-12, Phase 5 brief §5E, before any card is published or graded)

- **What's graded:** the **floor legs** (one per game, the highest-probability eligible leg) of
  each published card (`data/cfb/cards/card_<season>_wk<NN>.json`), built from the **Tue 10 AM ET
  DK snapshot** at its posted prices, 1 unit each. Pushes are void. Results come from
  `games.parquet` only.
- **Pass:** after **>= 100 graded floor legs**: ROI at posted prices **> 0**, with a
  game-clustered 95% bootstrap CI (2,000 draws) whose **lower bound is > -2%**, **and** a
  realized hit rate **>=** the mean implied break-even of those legs' posted prices.
- **Reported, not barred:** second legs and tickets, and the split by evidence label
  (SPREAD-CLV, ALT-SHAPE, ML-SHADED, TEAM-TOTAL, PAPER-UNPROVEN).
- **$0 until passed.** Paper only: not on the site or in the newsletter.

**Graded tracks and diagnostics (Tim, 2026-10-12; none of these is a new bar):**
- **Track 1, floor card:** the floor legs above (the bar).
- **Track 2, edge list:** every main spread with |edge| >= 1.5 vs the **Tuesday 10 AM** DK line
  (**one bet per game, on the model's side**: home or away, favorite or dog; the two sides' edges are exact negatives, so only one can reach +1.5. Wording clarified 2026-10-12; no rule change), graded at that posted line and price, 1 unit each.
  It's reported separately in `forward weekly`, and it complements the CLV forward test.
- **Diagnostic:** `ALT-SHAPE` floor legs split by game spread, |DK main line| <= 14 vs > 14
  (hit, break-even, ROI). This is where our σ and DK's ladder disagree most.
- **Ticket rule (2026-10-13):** each game appears on **at most one ticket per slate** (any market,
  any leg; this replaces the floor-star exception).
- **Ticket rule:** at most 2 `ALT-SHAPE` legs per ticket, with the rest from other labels; a
  ticket that can't reach +200 under the rules is labeled "reduced payout, floors held".

## Clarification (2026-10-23): late bet-time snapshot. Not a bar change

The week-8 Tue 10 AM capture ran at 13:03 ET (PC shut down overnight; 183 min late). Rule, Tim's:
- **Counts as the bet line:** a `bet`-labeled DK snapshot taken on the game week's Tuesday
  **before 18:00 ET** (`source = dk_tue_bet`). An afternoon Tuesday price is still a real early-week
  price, and some of the move has already happened, so the lag can only make CLV look worse.
- **Later than that:** the bet line is the first DK snapshot captured on or after that Tuesday
  (`source = bet_late`). It is never the close (the close stays the last `close`-labeled pregame
  snapshot strictly after the bet snapshot, else CFBD's DK close).
- **Always shown:** each weekly entry gives the bet snapshot's lag behind Tue 10:00 ET. A week with any
  game at `bet_late` or lag > 90 min is a **late-bet week**; CLV/ATS to date are reported both with and
  without late-bet weeks. The pass bars, the sample definition and the frozen model are unchanged.
- **Week 8 rows logged Friday:** `project_week` first ran for week 8 on Fri 2026-10-23 (14:02 UTC prices),
  so the 49 log rows carry Friday lines. The scorer re-derives the bet line from the DK snapshots and takes
  only `ratings_margin` / `qb_delta` from the log (as-of week-8 ratings, cutoff = the week's first kickoff),
  so all 49 are scored at the Tuesday 13:03 ET line; the rows are kept as logged. The 7 week-8 games that
  kicked off before Friday were never logged pregame and are not scored.

## Weekly log

Appended after each week grades by `python -m engine.cfb.model.forward weekly --week N`. Informational; the bars above decide.

### Week 7 (2026), graded 2026-10-19
- **This week, close source:** cfbd 59 (no DK close snapshot: CFBD DraftKings closing line)
- **This week:** 59 games logged, 59 with a close, 8 at |edge| >= 1.5. CLV toward model: **33.3%** of 6 moves, avg move +0.06 pts (ratings-only 33.3%, +0.06). ATS vs bet-time line (|edge| >= 1.5): **2-6 (25.0%)**, ratings-only 2-6 (25.0%).
- **To date (weeks 4+), close source:** cfbd 59 (no DK close snapshot: CFBD DraftKings closing line)
- **To date (weeks 4+):** 59 games logged, 59 with a close, 8 at |edge| >= 1.5 (8/150 toward the bar). CLV toward model: **33.3%** of 6 moves, avg move +0.06 pts (ratings-only 33.3%, +0.06). ATS vs bet-time line (|edge| >= 1.5): **2-6 (25.0%)**, ratings-only 2-6 (25.0%).
- **Rung log (shape-bar sample, to date):** 21 graded games / 24 rungs; hit 62.5% vs DK no-vig 73.0% (**lift -10.5 pp**, 95% CI -31.5 to +8.7); break-even at posted prices 78.1%; **EV at posted price: predicted -0.010, realized -0.189 units/rung** (CI -0.456 to +0.057). 21/60 toward the bar.
- **Floor card (to date):** 11 graded floor legs, hit 81.8% vs mean implied break-even 72.0%, **ROI at posted prices +14.0%** (game-clustered CI -22.6 to +41.7); IN PROGRESS: 11/100 graded floor legs; $0. By market: {'ALT-SHAPE': {'legs': 6, 'hit': 1.0, 'roi': 0.413}, 'ML-SHADED': {'legs': 2, 'hit': 0.5, 'roi': -0.296}, 'TEAM-TOTAL': {'legs': 3, 'hit': 0.667, 'roi': -0.116}}.
- **ALT-SHAPE split by game spread (diagnostic, not a bar):** {'|spread| <= 14': {'legs': 5, 'hit_%': 100.0, 'breakeven_%': 70.5, 'roi_%': 42.8}, '|spread| > 14': {'legs': 1, 'hit_%': 100.0, 'breakeven_%': 74.9, 'roi_%': 33.6}}.
- **Hook losses (diagnostic):** 1 this week (UMass Minutemen +6.5 [edge] loss on 7); 1 to date. Legs that lost/pushed landing exactly on the key they stopped short of (the next rung across it would have won).
- **Edge list, main spreads at the Tuesday line (separate track):** 8 graded, hit 25.0% vs break-even 53.0%, ROI -52.8% (game-clustered CI -100.0 to -5.0).

## Current score

<!-- AUTO:SCORE:BEGIN -->
_Scored 2026-10-12T11:17:31+00:00 by `python -m engine.cfb.model.forward score`._

**Status: IN PROGRESS: 0/150 qualifying games; $0**

```json
{
  "scored_at": "2026-10-12T11:17:31+00:00",
  "games_logged": 59,
  "games_with_close": 0,
  "line_source": {
    "dk_first_seen": 59
  },
  "primary": {
    "games_edge": 0,
    "moves": 0,
    "toward_share_pct": NaN,
    "avg_move_toward_model": NaN,
    "corr": NaN
  },
  "ratings_only": {
    "games_edge": 0,
    "moves": 0,
    "toward_share_pct": NaN,
    "avg_move_toward_model": NaN,
    "corr": NaN
  },
  "status": "IN PROGRESS: 0/150 qualifying games; $0"
}
```
<!-- AUTO:SCORE:END -->
