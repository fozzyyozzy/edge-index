# NFL early-line, cross-book and cross-market dry runs (2025 season)

**Date:** 2026-10-21 · **Paid Odds API calls made: 0.** Stopping for Tim's approval of costs and the draft PREREG (`PREREG_EARLY_LINES_DRAFT.md`).

**Pricing:** historical event odds cost **10 credits × markets returned × regions**, and empty responses are free. Historical bulk featured-market odds cost the same per call but cover every listed game.
- **Region rule:** up to **10 bookmakers count as one region.** So asking for DraftKings + FanDuel + BetMGM in one call costs **the same** as DraftKings alone.
- **Event ids:** all 2025 ids are already cached (`data/nfl/verify/raw/events_by_date.json`, 64 dates), so id lookups cost **0**.
- **Scope:** 272 regular-season games in 126 kickoff windows over 18 weeks (285 games and 139 windows with playoffs).

## 1. Early DK props: kickoff − 72h and kickoff − 24h

**Plan:** for each game, one historical event-odds call at kickoff − 72h and one at kickoff − 24h. Markets: `player_receptions`, `player_receptions_alternate`, `player_reception_yds`, `player_reception_yds_alternate`. The close (kickoff − 14 min) is already pulled.

| Scope | Calls | Worst-case credits | Note |
|---|---|---|---|
| Regular season, 72h + 24h | 544 | **21,760** | 40 per call if all 4 markets return; an empty response is free |
| + playoffs | 570 | 22,800 | |
| **Recommended:** the same calls with `bookmakers=draftkings,fanduel,betmgm` | 544 | **21,760** (no change) | Gives cross-book early prices for free |

**Coverage by timestamp, measured without paying.** This is the 2026 live collector (`data/odds_snapshots.db`), NFL events only:

| Hours before kickoff | Pulls | Events | DK receptions alt present | DK rec_yds alt present | Median players per game (rec alt) |
|---|---|---|---|---|---|
| 0–6 | 17 | 16 | 100% | 100% | 13 |
| 6–24 | 46 | 31 | 100% | 100% | 11 |
| 24–48 | 43 | 19 | 100% | 100% | 11 |
| 48–72 | 73 | 53 | 100% | 100% | 10 |
| 72–96 | 72 | 51 | 100% | 100% | 9 |
| 96–168 | 108 | 37 | 89% | 89% | 9 |

- **Reading the 2026 proxy:** DK posts these ladders for essentially every game by 72h out, but with **fewer players** (about 9 vs 13 at kickoff). Thin early ladders mean fewer early-close pairs than close rows. Expect roughly 70% of close player-markets to have a 72h price. That's an estimate from the 2026 proxy, not a 2025 measurement.
- **What's known about 2025:** the old 2025 database rows can't show timing (no timestamps). The only 2025 timing fact on hand: weekly DK coverage existed for all four markets every week (`NFL_VERIFY_COST.md`).

## 3. Cross-book: FanDuel + BetMGM at the same close timestamp

**Plan:** the same calls as the DK close pull (kickoff − 10 min), with `bookmakers=fanduel,betmgm` and the same 4 markets. The Odds API returns the snapshot at or before the requested time, so it's the same 5-minute snapshot DK came from.

| Scope | Credits |
|---|---|
| Regular season, 272 games | ≤ **10,880** |
| + playoffs | ≤ 11,400 |

- **Coverage evidence (2025, presence only, from the contaminated old rows; prices never used):**
  - **FanDuel:** all 4 markets every week, at 2,171–2,203 player-weeks per market (DK 2,217–2,246).
  - **BetMGM:** receptions and rec_yds mains, and rec_yds alt (1,743 player-weeks, a thinner ladder), but **no receptions alternate rows at all in 2025.**
  - Either BetMGM doesn't offer a receptions alt ladder through the Odds API, or the old loader didn't request it. Unknown. The pull would answer it, and an empty market costs nothing.
- **Lesson for future pulls:** the 2025 DK close pull could have included FanDuel and BetMGM at no extra cost. Every future pull should request all three books.

## 4. Cross-market lag: DK game spreads and totals

**Plan:** historical **bulk** odds (`/historical/sports/americanfootball_nfl/odds`, `markets=spreads,totals`, DraftKings). One call covers every game listed at that moment, at 20 credits per call.

| Snapshot | Calls | Credits |
|---|---|---|
| Close: each kickoff window − 10 min | 126 | 2,520 |
| Kickoff − 24h, per window | 126 | 2,520 |
| Kickoff − 72h, per window | 126 | 2,520 |
| Open: one weekly snapshot, the previous Sunday 23:55 ET, when look-ahead lines are up | 18 | 360 |
| **Total, regular season** | **396** | **≤ 7,920** |

- **Coverage: not measured; nothing on hand shows it.** No DK NFL game-line history exists locally. The 2026 collector stored props only. nflverse has closing spreads/totals for every 2025 game, but those aren't DK's and have no timestamps. DK posts NFL spreads/totals for every game days ahead as a rule, so coverage at E72 and E24 is expected to be complete. The pull would confirm it, and empty snapshots are free.
- **"Open":** this is an approximation. DK's true first number is often earlier, during the prior week. The weekly snapshot catches every game's line as of Sunday night.
- **"Right after a move" is coarse at this grid.** A move is seen between game-line snapshots, and props can only be bought at the next prop snapshot (72h or 24h).
  - A finer test needs dense prop snapshots: hourly props over the last 24h ≈ 24 × 40 × 272 ≈ **261,000 credits**. Not recommended now.
  - The coarse grid answers whether props lag at the 1–2-day scale first.

## Totals for approval

| Item | Credits (regular season) | Needs approval (> 2,000) |
|---|---|---|
| 1 Early props 72h + 24h (DK + FD + MGM in the same calls) | ≤ 21,760 | yes |
| 3 Cross-book close (FD + MGM) | ≤ 10,880 | yes |
| 4 Game lines open/72h/24h/close | ≤ 7,920 | yes |
| **All three** | **≤ 40,560** | |

**Account:** 4,748,681 credits remaining after the last NFL pull. The cycle resets around Nov 1–2.
