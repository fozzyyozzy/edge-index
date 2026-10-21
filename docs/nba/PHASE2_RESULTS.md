# NBA Floor Lines — Phase 2 Results (registered holdout, 2025-26)

**Date:** 2026-10-21 · **Status:** Phase 2 is complete. Stopping for Tim.

## Audit trail (order proven by commit history on `nba-phase1`)

| Step | Commit / time (ET) |
|---|---|
| PREREG registered | `56619549`, 09:07 |
| PREREG amendment 1, made before any result or price was seen | `6893b7f8`, 09:23 |
| Full 2025-26 DK props pull, started after the amendment commit | finished 09:45 |
| Model frozen: code + `frozen_config.json` + dev logs + prices committed, no holdout scored | `48f5accc`, 10:07 |
| Cosmetic warning fix, no behavior change | `7785c591`, 10:08:13 |
| **Holdout run, once**, from commit `7785c591` | started 10:08:19 (`data/nba/model/holdout_run.json`) |

`phase2.py holdout` writes a marker file first and refuses to run again. All numbers below come from that single run (`data/nba/model/holdout_results.json`). The only exception is §6, a descriptive, unregistered check that uses no model.

## TL;DR

1. **Calibration: every card-eligible market passes every bar on the 2025-26 holdout.**
   - The seven markets are points, rebounds, assists, threes, P+R, P+A and PRA.
   - Slopes are 0.96–1.02, and every 60–95% bin is within ±2.3 pts.
   - R+A passes but is calibration-only. Steals pass (shadow-only). Blocks fail B1/B2 and are dropped.
2. **Market blend: the rule selects w = 0.1, the market-dominant default.**
   - Only w = 0.1 beats market-only under both de-vig methods, and only by about 0.00003 Brier.
   - Model-only is worse than the de-vigged DK price on points, rebounds, assists and every combo. It is better on threes, steals and blocks.
3. **The product question (unregistered descriptive, §6): DK prices NBA floor ladders about efficiently.**
   - Flat-betting every card-market alt rung priced at 60–95% implied lost **−6.05%** (n = 189,355). Every bin lost between −4.6% and −7.9%.
   - The NFL receptions edge (true 88% vs books' −175/−300) **does not carry over** to NBA alt ladders on a flat basis.
   - The model is calibrated, but on these markets it doesn't know more than DK's price.

## 1. Frozen model (`engine/nba/model.py`, `data/nba/model/frozen_config.json`)

- **Mean:** P(stat ≥ k) is built from a mean μ = minutes projection × per-minute rate × matchup factor, then a per-market count distribution. Every input comes from games strictly before the game date.
- **Minutes:**
  - Formula: `1.862 + 0.894·m_ewma + 2.077·start5 + 0.304·b2b + 0.055·|spread| − 0.152·|spread|·start5`.
  - `m_ewma` uses a 5-game halflife; `start5` is the share of the last 5 games started.
  - The target game's own starter flag is never used.
  - Starters lose about 0.1 minute per point of spread. The small positive back-to-back term is noted, not interpreted.
- **Rates:** recency-weighted and shrunk toward the player's previous-season rate (or the position league rate).
- **Matchup factor:** opponent allowed-rate ^ γ.

| Market | Rate halflife | κ | γ | Distribution |
|---|---|---|---|---|
| pts | 10 | 100 | 0.5 | dresid (var 3.65 μ) |
| reb | 10 | 100 | 0.5 | dresid (var 1.25 μ + 0.018 μ²) |
| ast | 10 | 100 | 1.0 | dresid (var 1.31 μ) |
| fg3m | 20 | 100 | 0.5 | negative binomial (θ 11.8) |
| P+R | 10 | 100 | 0.5 | dresid (var 3.92 μ) |
| P+A | 10 | 100 | 1.0 | dresid (var 3.71 μ) |
| R+A | 10 | 100 | 0.5 | dresid (var 1.51 μ) |
| PRA | 10 | 100 | 1.0 | dresid (var 4.08 μ) |
| stl | 20 | 300 | 0.5 | negative binomial (θ 13.3) |
| blk | 40 | 300 | 0.5 | negative binomial (θ 6.6) |

`dresid` = the training residuals' own standardized shape (401 quantiles), scaled by the fitted variance.

### How it was chosen
Development was done on 2023-24 (fit) → 2024-25 (validation), and choices were by validation ranked-probability score (RPS). It took four passes (`data/nba/model/DEV_NOTES.md`):
1. With normal/NB/Poisson, points and the points combos were **too timid at both ends** (slope ~1.2).
2. Adding a gamma family didn't fix it.
3. A cross-fitted logistic recalibration fixed the slope but made points-family bins 2–3 pts **hot**. It was rejected.
4. The empirical-residual shape had the best RPS and calibrated well. It was frozen, then refit on both seasons.

**Caveat:** this iteration happened on validation, never the holdout. Rate halflife 10 / κ 100 sit at the edge of the search grid; that's noted, not tuned.

## 2. Calibration bars (PREREG §3), holdout 2025-26

- **Sample:** 14,255 eligible player-games: ≥ 8 prior games this season and trailing-10 minutes ≥ 20, both strictly before the game date.
- **Brier comparison:** on the evaluation band, against the naive last-10 clear rate on the same rows.

| Market | Role | Slope (0.50–0.97) | Diag slope (0.60–0.90) | Brier model / naive | B0 | B1 | B2 | B3 | B4 | **Result** |
|---|---|---|---|---|---|---|---|---|---|---|
| Points | card | 0.989 | 1.003 | 0.1477 / 0.1578 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| Rebounds | card | 0.990 | 1.023 | 0.1510 / 0.1634 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| Assists | card | 0.982 | 1.072 | 0.1621 / 0.1753 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| Threes | card | 0.958 | 0.984 | 0.1700 / 0.1846 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| P+R | card | 1.016 | 1.021 | 0.1461 / 0.1564 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| P+A | card | 1.004 | 1.016 | 0.1455 / 0.1554 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| PRA | card | 1.013 | 1.019 | 0.1439 / 0.1541 | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| R+A | calibration-only | 1.005 | 1.002 | 0.1479 / 0.1596 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS (not card-eligible, §9.6) |
| Steals | shadow | 0.956 | 0.994 | 0.2157 / 0.2347 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS (shadow first forward month) |
| Blocks | shadow | **0.858** | 0.889 | 0.2122 / 0.2323 | ✓ | **✗** | **✗** | ✓ | ✓ | **FAIL: dropped from v1** |

### Reliability, hit rate − mean p (pts) by bin
Each cell is the gap, with (n rungs).

| Market | 60–65 | 65–70 | 70–75 | 75–80 | 80–85 | 85–90 | 90–95 |
|---|---|---|---|---|---|---|---|
| Points | +1.3 (11,430) | +0.6 | +1.1 | +0.7 | +0.9 | +0.4 | −0.3 (23,313) |
| Rebounds | −0.9 (4,340) | −0.4 | +0.3 | −0.4 | −0.6 | +0.3 | 0.0 (8,482) |
| Assists | −0.4 (2,937) | +0.8 | −0.3 | 0.0 | +1.7 | +1.0 | −0.8 (3,217) |
| Threes | +0.5 (2,112) | −0.1 | −1.4 | −2.3 | −0.7 | +0.4 | −0.6 (1,827) |
| P+R | −0.1 (14,141) | +0.8 | +0.8 | +0.7 | +0.7 | +0.4 | +0.3 (29,952) |
| P+A | +0.5 (13,392) | +0.9 | +0.9 | +1.1 | +1.1 | +0.3 | 0.0 (29,025) |
| PRA | +0.7 (14,932) | +0.5 | +1.0 | +0.7 | +0.7 | +0.6 | +0.2 (35,237) |
| R+A | 0.0 (6,404) | 0.0 | 0.0 | −0.2 | 0.0 | +0.1 | +0.2 (13,613) |
| Steals | −1.8 (2,269) | −2.6 | −0.5 | −1.2 | −1.5 (371) | −3.9 (121) | −10.4 (16) |
| Blocks | −5.2 (516) | −1.6 | −0.1 | −4.3 | −6.3 (173) | −7.4 (49) | +2.6 (39) |

- **Points family:** runs slightly conservative (hit ≥ p), the safe direction.
- **Threes:** the most negative card market, at −2.3 in 75–80, but within the ±3 bar.
- **Steals/blocks:** run hot in the high bins on thin samples. Blocks fail B1 and B2 (−4.3 at n = 369 in 75–80).

Full tables (5–95) are in `holdout_results.json`.

## 3. Market blend (PREREG §6 + amendment §9)

- **Prices:** DK, one snapshot per game at tip − 10 min (`data/nba/lines/hist_props_2025-26.parquet`): 985,346 outcomes, 1,230/1,230 games.
- **Name matching:** 175 of 17,995 player-game names didn't resolve through the crosswalk and are excluded.
- **Rows:** 219,846 priced alt rungs with both de-vig methods and `p_hold` ∈ [0.50, 0.97], for eligible player-games. Of these, 208,055 were card-market rows pooled for the weight.
- **De-vig sources:**
  - `p_hold`: 91% own two-way hold, 8% market median, 1% game median.
  - `p_anchor`: 91% anchored, 8% game median, 1% season median.
- **The two methods agree almost exactly.** DK's alt rung at the main line is usually priced at the main Over price, so the anchor markup r ≈ 1 + hold.

**Pooled Brier, card markets:**

| | market-only | model-only | w = 0.1 | w = 0.2 | w = 0.4 | w = 0.6 |
|---|---|---|---|---|---|---|
| hold de-vig | 0.186248 | 0.192327 | **0.186217** | 0.186329 | 0.186978 | 0.188193 |
| anchor de-vig | 0.186260 | 0.192327 | **0.186230** | 0.186341 | 0.186988 | 0.188201 |

- **Qualifying weights** (beat market-only under both methods): **{0.1}** only. **Pooled weight = 0.1** by rule §9.3.
- **Per-market valve (§9.4):** the pooled weight is already 0.1, so every card market uses **w = 0.1**.
  - On points, P+R, P+A and PRA, w = 0.1 is fractionally worse than market-only (by < 0.0001). The valve's answer is the same: w = 0.1.

| Market | n | market-only (hold) | model-only | best of the blends | Model vs market |
|---|---|---|---|---|---|
| Points | 46,814 | 0.18113 | 0.18770 | 0.18116 (w 0.1) | market better |
| Rebounds | 33,311 | 0.18942 | 0.19318 | 0.18931 (w 0.1/0.2) | market better |
| Assists | 18,366 | 0.19674 | 0.20271 | 0.19663 (w 0.1) | market better |
| Threes | 18,165 | 0.19017 | **0.18994** | 0.18926 (w 0.6) | **model better** |
| P+R | 31,126 | 0.18593 | 0.19320 | 0.18595 | market better |
| P+A | 28,319 | 0.18415 | 0.19200 | 0.18419 | market better |
| PRA | 31,954 | 0.18435 | 0.19305 | 0.18441 | market better |
| Steals (shadow) | 8,438 | 0.22882 | **0.22679** | 0.22667 (w 0.6) | model better |
| Blocks (shadow) | 3,353 | 0.23255 | **0.23013** | 0.23012 (w 0.6) | model better |

The threes, steals and blocks per-market weights are **diagnostics only** (§6.5 step 6). They don't change the pooled weight, and a market-specific weight would need a new pre-registration judged on forward data.

**Market-only reliability in the floor band (diagnostic §9.5, pooled card markets, hold method):**

| De-vigged p bin | 60–65 | 65–70 | 70–75 | 75–80 | 80–85 | 85–90 | 90–95 |
|---|---|---|---|---|---|---|---|
| n | 19,669 | 20,133 | 21,203 | 22,580 | 25,429 | 31,358 | 9,187 |
| hit − p | −1.1 | 0.0 | 0.0 | +0.7 | +1.2 | +1.6 | +2.0 |

The anchor method is within 0.2 pts in every bin. De-vigging the alt ladders by the main-line hold slightly over-removes vig at the deep floors: actual hit rates are 1–2 pts above the de-vigged probability from 80% up. The raw prices still lose money (§6).

## 4. Verdict against the pre-registered bars

| Market | v1 status |
|---|---|
| Points, Rebounds, Assists, Threes, P+R, P+A, PRA | **Passed. Card-eligible, at blend weight w = 0.1.** |
| R+A | Passed. Calibration-only by amendment §9.6 (DK offered no historical alt ladder). |
| Steals | Passed. Shadow-only for the first forward month (model-only evaluation). |
| Blocks | **Failed (B1 slope 0.858, B2 bin 75–80 −4.3). Dropped from v1.** Any revival needs a new pre-registration judged on 2026-27 forward data. |

## 5. What the blend result means

At w = 0.1, a card leg's probability is 90% DK's de-vigged price and 10% model. On points, rebounds, assists and the combos, the holdout says the model's independent information is **worth about nothing relative to DK's price**: model-only Brier is 0.004–0.009 worse than market-only. Threes is the one card market where the model alone beat the market, by a small margin (0.18994 vs 0.19017).

## 6. Unregistered descriptive: are NBA floor ladders mispriced? (`holdout_market_descriptive.json`)

**Not part of the pre-registration. No model, no selection.**
- **Rows:** every DK alt Over rung priced at 60–95% raw implied probability, for players who played.
- **Settlement:** at the posted price against the ESPN box.

| Card-market raw implied bin | n | avg implied | hit | flat ROI |
|---|---|---|---|---|
| 60–65 | 25,434 | 62.5% | 57.5% | −7.9% |
| 65–70 | 23,805 | 67.5% | 62.3% | −7.6% |
| 70–75 | 24,283 | 72.5% | 67.8% | −6.5% |
| 75–80 | 25,102 | 77.6% | 72.6% | −6.4% |
| 80–85 | 26,335 | 82.5% | 78.2% | −5.3% |
| 85–90 | 29,556 | 87.6% | 83.3% | −4.9% |
| 90–95 | 34,840 | 92.6% | 88.3% | −4.6% |
| **All card markets** | **189,355** | | | **−6.05%** |

By market: pts −5.0%, ast −5.8%, P+A −5.7%, P+R −6.3%, PRA −6.3%, reb −6.5%, threes −7.6%, steals −10.3%, blocks −13.6%.

**This is the opposite of the NFL receptions finding.** NBA floor rungs hit at about their de-vigged probability, and the raw prices carry roughly 4–8% juice, so flat floor betting loses.

**What this implies for Phase 3 (Tim's call):**
- A floor card is only +EV if legs are **selected** where the model disagrees with DK and is right. The holdout Brier says that disagreement carries little information on the main markets.
- **Selecting legs by model edge on this holdout would be a slice found after looking** (CLAUDE.md rule 5). I did not do it. That question belongs to the Phase 4 forward test, with CLV, under the pre-registered bars.
- The closest thing to a lead is threes, the one card market where the model beat the market's Brier, and possibly steals/blocks. **That's a hypothesis, not a finding.**

## 7. Data, spend, caveats

- **Odds API this phase:** 225,970 credits (full props pull; the 7 sample games were reused from cache). Account: 239,803 used, 4,760,197 remaining.
- **Not scored:** 175 player-game names (1%) with no crosswalk match have no blend rows. In forward grading they'd be **UNGRADEABLE** (PREREG §7).
- **Holdout definition:** the ESPN box, with Olbrich's dropped rows (Phase 1 §3) absent. He never reaches eligibility as an ESPN player.
- **Tests:** `automation/tests/nba/` has 41 tests: eligibility leakage, the holdout guard, the slope fit, the naive baseline's strict-before rule, and the distribution families.

**Stopping here for Tim.**
