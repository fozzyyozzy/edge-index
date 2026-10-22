# NFL Main-Line Unders at Best Maryland Price: Results

**Date:** 2026-10-22 · **Pre-registration:** `docs/nfl/PREREG_UNDERS.md` · **Status:** done; stopping for Tim.

## Audit trail (branch `nfl-verify`)

| Step | Commit / time (UTC) |
|---|---|
| Book list and line rule chosen by Tim after the free 2025 recompute | (this session) |
| PREREG registered, before any 2024 price was pulled | `964035d0` |
| 2024 pull + test code committed, test not run | `bd65f7b4` |
| **Registered 2024 test, run once**, from `bd65f7b4` | 2026-10-22 18:25 (`data/nfl/verify/unders_run.json`) |

- **Code checks before the run:** the code was only smoke-tested on 2025 (the discovery season) and 2026 weeks 3–6. No 2024 outcome was looked at before the run.
- **Spend:** **5,498 credits** (cap 12,000).
  - 57 event-id lookups, plus 272 closing snapshots with every US book, for receptions and rec_yds main lines (117,012 outcomes).
  - Account remaining: 4,704,553.

**The bet:**
- **Markets:** receptions and rec_yds main-line **Unders**, one per player-game-market.
- **Line:** DK's line.
- **Price:** the best price among **DraftKings, FanDuel, BetMGM, Caesars, Fanatics, BetRivers**, at the close.
- **Staking:** flat straight bets.

## Verdict: 2024 regular season (registered)

| | Bets | Hit | Avg implied | **Flat ROI** | **95% CI** (game-clustered) | Verdict |
|---|---|---|---|---|---|---|
| **Best Maryland price (primary)** | 6,395 | 53.4% | 52.6% | **+1.46%** | **[−1.42, +4.32]** | **FAIL** (CI not above 0) |
| Receptions | 3,071 | 53.8% | 52.6% | +2.12% | [−1.21, +5.38] | — |
| rec_yds | 3,324 | 53.0% | 52.6% | +0.85% | [−2.33, +4.04] | — |
| Weeks 1–9 | 3,363 | 54.2% | | +3.07% | [−0.79, +7.10] | — |
| Weeks 10–18 | 3,032 | 52.5% | | −0.33% | [−4.48, +3.71] | — |
| **DK only** (non-gating) | 5,993 | 52.9% | 53.6% | **−1.36%** | [−4.29, +1.56] | — |

- **Excluded:** 56 bets were UNGRADEABLE and 7 VOID.
- **Where the best price came from:** DraftKings 2,325 · BetMGM 1,105 · FanDuel 1,032 · BetRivers 1,011 · Caesars 922. Fanatics was never best. A median of 4 listed books posted DK's line.

**The 2025 Unders result does not replicate in 2024 at the registered bar.**
- **Point estimate:** still positive at the best Maryland price (+1.5%, vs +4.0% in 2025), but the interval includes zero and the second half of 2024 was flat.
- **Line shopping:** across the six Maryland books it is worth about **2.8 points**: −1.36% at DK alone vs +1.46% at the best listed price. That's the most consistent finding here, not the Under side itself.

## Descriptive (non-gating)

| Sample | Bets | Hit | Flat ROI | 95% CI |
|---|---|---|---|---|
| 2025, best Maryland price (discovery season) | 6,904 | 54.9% | +3.98% | [+1.08, +6.93] |
| 2025, DK only | 5,726 | 55.2% | +3.43% | [+0.19, +6.65] |
| **2026 weeks 3–6, DK only** | 1,363 | 51.1% | **−3.82%** | [−9.62, +2.00] |

- **2026 forward data:** the live pipeline's last pregame DK pull per game, so it's DK only. It runs the other way so far.
- **By market:** receptions −4.4%, rec_yds −3.3%.

### 2-leg Under parlays (cross-game, both legs at one listed book)

- **Pairs:** every cross-game pair of that season's Under legs within the same week.
- **Pricing:** each pair priced at the single listed book with the best combined price.
- **Compared with:** the same legs as straight bets at each leg's best price, 0.5u each.

| Season | Pairs | Avg parlay price | Both legs won | Leg hit² | **Parlay ROI** [95% CI, week bootstrap] | **Same legs straight** [95% CI] |
|---|---|---|---|---|---|---|
| 2024 | 1,046,257 | 3.61 (+261) | 28.6% | 28.5% | **+1.15%** [−5.81, +8.67] | +1.50% [−1.96, +5.15] |
| 2025 | 1,079,015 | 3.59 (+259) | 30.1% | 30.1% | **+6.20%** [+0.72, +11.12] | +3.98% [+1.11, +6.47] |

- **Leg outcomes are independent:** cross-game Under legs win together at about the product of their hit rates (28.6% vs 28.5%; 30.1% vs 30.1%). There's no correlation to exploit.
- **Parlays amplify whatever the legs have.** In 2025, when the legs were profitable, parlays returned more (+6.2% vs +4.0%), but with roughly double the spread. In 2024, when they weren't, parlays were about the same as straights with a much wider interval.
- **Same-book pricing usually costs:** pricing both legs at one book (it must post both lines) gives up some of the per-leg best price. Parlays don't create an edge where the straights don't have one.

## Forward rule (2026), as registered

- **The bet:** the same bet, priced at the live pipeline's publish-time snapshot, across all six listed books.
- **Reporting:** weekly; **judged once at 300 settled bets**.
  - PASS: the CI's lower bound is above 0.
  - FAIL: the point estimate is ≤ 0.
  - INCONCLUSIVE: anything else, which goes to Tim's decision.
- **Not built:** the live pipeline pulls **DraftKings only**. An all-book publish-time capture (`regions=us`, about 20 credits per game per pull) would be its own pipeline PR, needing Tim's approval.
- **Until then:** forward results would be DK-only. Weeks 3–6 already show −3.8% there.

## What this means

- **No bettable Unders edge yet.** The "main-line Unders" pattern from 2025 failed its registered out-of-sample test on 2024.
  - It's positive at the best Maryland price, but not distinguishable from zero.
  - It's negative at DraftKings alone, in both 2024 and early 2026.
- **Line shopping is real.** Across the six Maryland books it's worth about 2–3 points of return on these main lines in both seasons. Any future props product should price at the best available book, not DK alone.
- **Parlays don't help.** 2-leg parlays add variance, not edge.

**Tim's calls:**
- whether to keep running the forward rule (DK-only now, or after an all-book capture is built)
- whether to drop the Unders idea at this point

## Files (branch `nfl-verify`)

| Path | Contents |
|---|---|
| `docs/nfl/PREREG_UNDERS.md` | Pre-registration |
| `engine/nfl/unders_pull.py` | Pull |
| `engine/nfl/unders_test.py` | Test |
| `data/nfl/verify/close_mains_2024.parquet` | 2024 prices |
| `data/nfl/verify/unders_results.json` | Every number above |
| `data/nfl/verify/unders_run.json` | Run marker |
