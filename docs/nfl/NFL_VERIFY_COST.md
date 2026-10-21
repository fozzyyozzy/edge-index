# NFL verification: dry-run cost of 2025 DK alt-ladder prices (receptions, rec_yds)

**Date:** 2026-10-21 · **Paid Odds API calls made: 0.** Report 1 of 4 in Tim's queue. Stopping after it.

**Companion:** `docs/nfl/PREREG_NFL_DRAFT.md` (a draft for approval; nothing runs before it's approved).

## Why a new pull is needed

- **"Books hang −175/−300" has no source.**
  - It appears only as prose in `CLAUDE.md:55-56` and `ROADMAP.md:49/51`. No script, file or price table produces it.
  - `engine/nfl/floor_study.py` says "no odds needed": it measures how often players clear 0.6× their expectation, never what DK charged for that rung.
- **No usable DraftKings price data exists for this test.**

| Source | Season | DK receptions alt? | Usable? |
|---|---|---|---|
| `backtest/nfl/edge_index.db` `prop_lines` | 2024 | **No:** FanDuel only (16,658 rows) | no DK |
| same | 2025 | DK 22,530 rows | **No: contaminated with live in-game snapshots, no timestamps** (CLAUDE.md rule 1) |
| `data/odds_snapshots.db`, `automation/lines/` | 2026 wk 1–6 | Yes, real pregame DK ladders | Yes, but only 6 weeks (see the PREREG's secondary test) |

## Plan priced

- **Request:** Odds API historical event odds, DraftKings only (1 region), one snapshot per game at **kickoff − 10 minutes**. That's the same timing as the NBA pull. Any event whose kickoff is at or before the snapshot is refused, so every price is pregame.
- **Markets (4):**
  - `player_receptions`, `player_receptions_alternate`
  - `player_reception_yds`, `player_reception_yds_alternate`
  - The main lines are needed for both de-vig methods.
- **Cost per game:** 10 × markets returned × 1 region, so **40 credits** when all 4 return. Empty responses are free.
- **Event ids:** one historical `/events` call per game date (1 credit each, 64 dates). Each call lists every not-yet-started game.

| Scope | Games | Prop credits | Event-id lookups | **Total** |
|---|---|---|---|---|
| 2025 regular season | 272 | 10,880 | ≤ 64 | **≤ 10,944** |
| + playoffs (WC 6, DIV 4, CON 2, SB 1) | 13 | 520 | (included) | **≤ 11,464** |

- **Approval:** this is over the 2,000-credit threshold, so it needs your approval.
- **Quota:** 4,760,197 credits remain this cycle, and the next reset is about Nov 1–2.

## Coverage, without paying

- **2025 market existence:**
  - The contaminated 2025 rows were checked for **presence only** (their prices are never used). They show DK carried all four markets every week, 1–21:
    - weeks 1–17: about 100–145 players per week
    - weeks 18–21: 23–59
  - This is consistent with the Odds API's historical endpoint, which it came from (the old loader, `backtest/nfl/odds_api_loader.py`).
  - Week 22 (the Super Bowl) has no rows in that table either way.
- **2026 proxy:** in the live pipeline's DK pulls, both alt markets appeared for **every** event in weeks 3–6 (16/16, 17/17, 15/15, 14/14), and the two-way mains did too, apart from one missing week-3 TNF two-way.
- **Not knowable without paying:**
  - ladder depth per player at the kickoff − 10 min snapshot
  - whether every game's snapshot has all 4 markets (late scratches drop players)

**Option if you want certainty before the full spend:** one game per week, 22 games, ≤ 880 credits. That's under 2,000, but you said don't pull, so it waits.

## Recommendation

Approve the full pull (**≤ 11,464 credits**) together with the PREREG. The pull starts only after the approved PREREG is committed, the same order as NBA. Nothing has been pulled.
