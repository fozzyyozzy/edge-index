# NFL Floor Verification: Results

**Date:** 2026-10-21 · **Pre-registration:** `docs/nfl/PREREG_NFL.md` · **Status:** done; stopping for Tim. NBA items 2–4 wait.

## Audit trail (branch `nfl-verify`)

| Step | Commit / time (ET) |
|---|---|
| PREREG registered, before any pull | `725a3f1a`, 10:24 |
| CLAUDE.md / ROADMAP.md: "−175/−300" marked UNVERIFIED | `f3ee16d0` |
| 2025 DK prices + replay code committed, analysis not yet run | `e3257900` |
| **Registered analysis, run once**, from `e3257900` | 10:33 (`data/nfl/verify/analysis_run.json` blocks a re-run) |

- **Pull:** **11,354 credits** (cap 12,000; 100k reserve guard).
  - All 285 games, 67,710 DK outcomes.
  - Every snapshot was 14 minutes before kickoff.
  - 281 of 285 games had all four markets.
- **Matching:** 109 of 8,836 floor-band rungs (1.2%) didn't match an nflverse player and are **UNGRADEABLE**; another 4 are VOID.

## Verdicts

| Test | 2025 regular season (registered) | Verdict |
|---|---|---|
| **Q1** Flat-bet every DK floor-band alt rung (implied 60–95%) | **−9.03%**, CI [−11.1, −7.0], n = 8,723 | The market is not beatable flat; every bin loses |
| **Q2** Model vs de-vigged DK (Brier) | market-only best; no blend qualifies; the live blend is worse than market | **w = 0.1** (market-dominant) |
| **Q3** The live card's own picks, single legs, **WITH** injuries (primary) | **−13.99%**, CI [−22.5, −5.8], n = 347 | **REFUTED** |
| Q3 WITHOUT injuries (sensitivity) | −13.85%, CI [−22.2, −6.0], n = 387 | REFUTED |
| **Q4** The "0.6× receptions floor at −175/−300" claim | DK median price **−1040** (IQR −1680 to −620); ROI −4.75%, CI [−6.8, −2.7] | **NOT SUPPORTED** |

**In one line:** players do clear 0.6× receptions floors ~85% of the time, but DK prices that rung at about −1040, not −175/−300, so the edge isn't there. The card's selection rules lost about 14% per leg on real 2025 prices.

## Q1. Market efficiency (no model)

| Market | n | Hit | Avg implied | Flat ROI | 95% CI |
|---|---|---|---|---|---|
| All | 8,723 | 70.45% | 77.05% | **−9.03%** | [−11.09, −7.03] |
| Receptions | 4,404 | 69.73% | 77.48% | −10.50% | [−12.73, −8.22] |
| rec_yds | 4,319 | 71.17% | 76.62% | −7.53% | [−9.94, −5.20] |
| Playoffs (all) | 434 | 68.66% | 76.53% | −10.00% | [−23.08, +2.63] |

### Receptions by implied bin
De-vig is the hold method.

| Bin | n | Implied | De-vigged | Hit | ROI | 95% CI |
|---|---|---|---|---|---|---|
| 60–65 | 641 | 62.4 | 58.9 | 53.8 | −13.8% | [−19.7, −7.8] |
| 65–70 | 637 | 67.5 | 63.7 | 56.7 | −16.0% | [−21.7, −10.3] |
| 70–75 | 623 | 72.4 | 68.3 | 62.0 | −14.5% | [−19.7, −9.4] |
| 75–80 | 615 | 77.5 | 73.1 | 71.4 | −7.9% | [−12.5, −3.3] |
| 80–85 | 581 | 82.4 | 77.8 | 74.7 | −9.4% | [−13.5, −5.2] |
| 85–90 | 657 | 87.4 | 82.5 | 80.1 | −8.5% | [−12.0, −5.0] |
| 90–95 | 650 | 92.5 | 87.3 | 89.2 | −3.6% | [−6.1, −1.1] |

rec_yds behaves the same way: −10% to −12% below 75% implied, −2.7% to −7% above. Full tables are in `data/nfl/verify/results_2025.json`.

## Q2. Does the model add information?

- **Rows:** 10,620 priced rungs with p_hold 0.50–0.97 and both de-vig methods.
  - 99.7% use the player's own two-way hold.
  - The anchor rung was found for 55%; the rest use the game or season median.

| Brier (pooled) | market-only | MO (model-only) | **LB (live blend)** | w = 0.1 | w = 0.2 | w = 0.4 | w = 0.6 |
|---|---|---|---|---|---|---|---|
| hold de-vig | **0.18836** | 0.20242 | 0.19255 | 0.18837 | 0.18869 | 0.19026 | 0.19307 |
| anchor de-vig | **0.18829** | 0.20242 | 0.19255 | 0.18831 | 0.18864 | 0.19024 | 0.19306 |

- **No blend beats market-only under both methods,** so the rule gives **w = 0.1**.
- **The live card's blend (LB) is worse than DK's price alone,** in both markets and under both methods.
- **Per market:** receptions at w = 0.1 edges market-only by about 0.0001; rec_yds doesn't. The valve gives both w = 0.1.

**Calibration (not gating):**
- **Model-only is badly overconfident:** slope 0.66 (rec_yds) and 0.67 (receptions). The L10/L15 clear rates of floor players overstate the next game.
- **The live blend is calibrated** (slope 0.98), but only because it leans on DK's price.

## Q3. The live card's selections, replayed

- **How:** the live scripts (`floors.py` → `grade_legs.py` → `build_card_json.py`) were run for every 2025 week and slate, walk-forward.
- **Output per variant:** 52 cards, with 367 candidate legs WITH injuries and 407 WITHOUT.
- **Injury rebuild:** the WITH variant reconstructed injury holds and flags from nflverse snap counts and weekly injury reports.

| Variant | Legs | Hit | Avg implied | Mean card probability (LB) | ROI | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| **WITH injuries (primary)** | 347 (+20 void) | 58.8% | 68.2% | 73.7% | **−13.99%** | [−22.49, −5.84] | **REFUTED** |
| WITHOUT injuries | 387 (+20 void) | 58.9% | 68.4% | 73.8% | −13.85% | [−22.22, −6.00] | REFUTED |

The card's legs hit **15 points below the card's own probability**, and 9 below DK's implied.

| By market (WITH) | n | Hit | ROI |
|---|---|---|---|
| rec_yds | 196 | 57.1% | −15.8% [−26.3, −5.8] |
| Receptions | 151 | 60.9% | −11.6% [−23.6, +0.04] |

| By grade (WITH) | A+ | A | A− | B | C |
|---|---|---|---|---|---|
| n | 22 | 57 | 82 | 93 | 93 |
| Hit | 63.6% | 68.4% | 63.4% | 53.8% | 52.7% |
| ROI | −17.2% | −9.6% | −10.3% | −18.7% | −14.5% |

**Tickets (descriptive), built by `build_tickets`, R1–R11:**

| Variant | Tickets | Hit | ROI | 95% CI | Avg payout | Mean LB product | Mean MO product | Mean implied product | Compounded vig |
|---|---|---|---|---|---|---|---|---|---|
| WITH | 53 | 24.5% | −25.5% | [−61.2, +15.7] | 3.15× | 42.3% | 55.4% | 33.6% | **1.209** |
| WITHOUT | 58 | 22.4% | −35.3% | [−62.6, −5.1] | 3.04× | 43.2% | 56.3% | 34.3% | 1.206 |

- **What it means:** DK charges about **21% compounded vig** on a 3–4-leg floor ticket, and the tickets hit below even DK's implied probability.
- **Caveat:** the replay's tickets come from receptions/rec_yds only. The live card also draws on pass/rush markets.

### Post-run note (does not change the registered result)

- **What happened:** 18 of the 20 VOID legs are **week-1 offseason movers** (Brandin Cooks DAL→NO, Davante Adams NYJ→LA, Stefon Diggs HOU→NE, Adam Thielen CAR→MIN, Jonnu Smith MIA→PIT). The other 2 are week 10.
  - Before a player's first game for a new team, `floors.py` and `grade_legs.py` take his team from last season (`team_now = prev...last()`).
  - So movers are graded on old-team history, **and the R6 team-change hold can't fire in week 1.**
  - This is a live-pipeline gap that applies to 2026 week 1 as well.
- **Settlement sensitivity:** settling those legs by the player's actual game (any team) gives WITH **−13.21%** [−21.53, −5.12] (n 367) and WITHOUT −13.16% [−21.28, −5.26]. Still REFUTED. The registered result stands.
- File: `data/nfl/verify/q3_settlement_sensitivity.json`.

## Q4. The "0.6× receptions floor at −175/−300" claim

| | n | Rung match | **DK median price** | IQR | Hit | Implied | ROI | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Receptions, 0.6×μ (μ ≥ 3) | 1,359 | 85% exact rung | **−1040** | −1680 to −620 | 84.8% | 89.0% | −4.75% | [−6.82, −2.65] | **NOT SUPPORTED** |
| rec_yds, 0.6×μ (μ ≥ 25) | 1,707 | nearest rung | −241 | −344 to −168 | 64.9% | 69.2% | −6.49% | [−9.68, −3.32] | (comparison) |

- **The study's clear rate is roughly right.** 84.8% in 2025, vs the claimed 88.4% (the 0.6× rung here uses DK's nearest rung).
- **The claimed price is not.** DK hangs that rung at about **−1040**, not −175/−300, which is more than the −762 that 88% would be fair at.

## 2026 forward check (weeks 3–6; the pipeline's own pregame ladders and published cards; no credits)

**Clean out-of-sample, but small.** Rungs pulled after their kickoff were dropped.

| Test | Result |
|---|---|
| Q1 flat floor band | **−6.04%**, CI [−10.72, −1.54] (1,864 rungs, 61 games). Receptions −8.67% [−13.67, −3.89]; rec_yds −3.43% [−8.93, +1.84]. |
| Q2 | Market-only 0.20292 · LB **0.20175** · w = 0.4 **0.20056**. **All four blends beat market-only under both methods; LB beats market** (2,499 rows). |
| Q4 receptions 0.6× | Median DK **−1060**, hit 85.6% vs implied 89.8%, ROI −4.34% [−8.57, −0.44]. Not supported. |
| Q3 published card legs (all 7 markets) | 73 legs, hit 64.4% vs implied 69.6%, **−7.51%** [−28.1, +12.5]: **INCONCLUSIVE**. Receptions/rec_yds legs only: 45, −0.65% [−24.6, +21.0]. |
| Tickets | 10 graded, 3 won, −19.9%; compounded vig 1.214. 2 more are ungradeable: the week-3/4 cards predate the `candidates` field, and their legs weren't in `floors_singles`. |

- **Q2 cuts the other way on these four weeks:** model information helps here, but over the full 2025 season it didn't. With 61 games, that's a **hypothesis for forward tracking**, not a finding (rule 5).
- **Q1 and Q4 agree with 2025.**

## What this means

1. **The documented core edge is refuted on real prices.**
   - It rested on clear rates (true) and an unsourced book price (false). DK prices receptions floors near or beyond fair: about −1040 at 0.6×.
   - Flat floor betting loses 6–9%. The live card's 2025-replayed selections lost 14% per leg, with a confidence interval entirely below zero.
2. **The card's probability runs hot.** Selected legs hit 15 points below the card's stated probability. On its own, the model is overconfident (slope ~0.66); the live blend is only calibrated because it leans on DK.
3. **2026 so far is too small to overturn this.** Q1 and Q4 replicate. Q3 is inconclusive. Q2's positive blend signal is worth tracking forward under a new pre-registration.

**Decisions for Tim (none taken):**
- the card's "edge" copy and product positioning
- whether the live card continues as-is, shadow-only, or with w = 0.1
- a separate fix for the week-1 mover gap
- whether the Q2 2026 signal gets its own forward pre-registration

## Files (branch `nfl-verify`)

| Path | Contents |
|---|---|
| `docs/nfl/PREREG_NFL.md` | The pre-registration |
| `docs/nfl/NFL_VERIFY_COST.md` | The cost dry run |
| this file | Results |
| `engine/nfl/verify_pull.py` | Pull |
| `engine/nfl/verify_replay.py` | Replay and analysis |
| `data/nfl/verify/hist_props_2025.parquet` | Prices |
| `data/nfl/verify/odds_usage_nfl_verify.csv` | Every paid call |
| `data/nfl/verify/results_2025.json` | Registered results, with every candidate leg |
| `data/nfl/verify/results_forward_2026.json` | Forward check |
| `data/nfl/verify/q3_settlement_sensitivity.json` | Post-run settlement sensitivity |
| `data/nfl/verify/replay/*/cards/card_2025_*.json` | The replayed cards |
| `data/nfl/verify/replay_log.txt` | Every script's output |

No live pipeline file, workflow or published card was changed.
