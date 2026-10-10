# CFB Forward Test: 2026 weeks 4+ (pre-registered)

**Pre-registered 2026-10-10 by Tim, before any forward capture was logged.**
Model: the Phase 3 frozen primary (`engine/cfb/model/params.json`, sha256 prefix
`1f56d630ad42`, commit `fb01f2fd`). The model does not change during the test.
**$0 is wagered until the test passes.**

## Why

The 2025 holdout passed on CLV (60.5% of moves toward the model) but failed on k
(+0.16, CI spanning 0). Historical "opens" from CFBD are of uneven quality: DK's 2023 open
equals its close 47% of the time, and the 2026 to-date CLV is implausibly high (88-91%).
This test uses lines **we** timestamp, so bet time and close are known exactly.

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

## Current score

<!-- AUTO:SCORE:BEGIN -->
_Scored 2026-10-10T17:29:44+00:00 by `python -m engine.cfb.model.forward score`._

**Status: no projections logged yet**

```json
{
  "scored_at": "2026-10-10T17:29:44+00:00",
  "status": "no projections logged yet"
}
```
<!-- AUTO:SCORE:END -->
