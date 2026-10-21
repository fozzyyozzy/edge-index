# NFL Factor Study: Results

**Date:** 2026-10-21 · **Pre-registration:** `docs/nfl/PREREG_FACTORS.md` · **Status:** done; stopping for Tim.

## Audit trail (branch `nfl-verify`)

| Step | Commit / time (ET) |
|---|---|
| PREREG registered, before any feature was computed | `cfd74cb3`, 12:07 |
| Feature pipeline committed; no model fit, no test result | `bb7734cd` |
| **Registered fit/test, run once**, from `bb7734cd` | 12:10 (`data/nfl/verify/factor_run.json` blocks a re-run) |

- **No new Odds API credits:** it uses the 2025 DK prices already pulled.
- **Correction to `bb7734cd`'s message:** it says the commit includes the feature tables (`factor_rows_A/B.parquet`), but a local git-exclude rule kept them out. They're committed with these results instead. They are the deterministic output of `python -m engine.nfl.factor_study build` at `bb7734cd`, built before the run (file times 12:10:0x vs the run's 12:10:35).

## TL;DR

**No situational factor carries information beyond DK's price that's distinguishable from noise.**
- **The two that pass your rule (game script, weather) are inside noise.** They improve Brier by 0.0004–0.0005 on a base of ~0.196 (about 0.2%), with 95% CIs that include zero.
- **Man vs zone made predictions worse,** with a CI entirely above zero.
- **The card fails too.** Built only from legs where the combined passing factors "say better than price", it returned **−9.9%** (CI −18.6% to −1.2%) on weeks 10–18.

## 1. Data scope (checked before building)

- **Man/zone tags:** present every regular-season week of 2024 and 2025 (`pbp_participation.defense_man_zone_type`, ~1,100–1,300 tagged dropbacks per week).
- **Gaps:**
  - **Per-player routes:** `route` is the targeted receiver's only. "Per route" here means per on-field man/zone-tagged dropback.
  - **Alignment (slot/wide):** not in nflverse. That part of factor 4 was dropped.
  - **Volume/attempt props for big favorites:** not priced. A pull would cost about **16,320 credits** and needs approval, so factor 6 used receptions/rec_yds main-line unders.
- **Weather:** game-time actual (≈ the forecast). That's a mild look-ahead that, if anything, flatters F5.

## 2. Rows

| Set | Rows | Test rows (wks 10–18) | What |
|---|---|---|---|
| A (F1–F5) | 11,783 | 5,524 | DK alt Over rungs, receptions + rec_yds, p_hold 0.50–0.97, both de-vig methods |
| B (F6) | 5,702 | 2,783 | Two-way main lines (Over/Under), proportional de-vig |

Each factor is fit per market on weeks 1–9 as `logit p = logit p_DK + β·x`, with no intercept, so the factor alone must carry the improvement.

## 3. Results by factor (test weeks 10–18)

ΔBrier = factor − DK. Negative is better. The CI is game-clustered, from 10,000 bootstrap resamples.

| Factor | Brier DK (hold) | Brier factor (hold) | ΔBrier hold [95% CI] | ΔBrier anchor [95% CI] | **Rule** | Distinct from noise? |
|---|---|---|---|---|---|---|
| F1 Man vs zone | 0.19647 | 0.19782 | **+0.00135** [+0.00046, +0.00229] | +0.00134 [+0.00046, +0.00228] | fail | **worse, reliably** |
| **F2 Game script** | 0.19647 | 0.19609 | −0.00037 [−0.00096, +0.00024] | −0.00036 [−0.00094, +0.00025] | **PASS** | no |
| F3 Pass tendency | 0.19647 | 0.19680 | +0.00033 [−0.00030, +0.00096] | +0.00033 [−0.00030, +0.00096] | fail | no |
| F4 Defense weak points | 0.19647 | 0.19726 | +0.00079 [−0.00013, +0.00170] | +0.00080 [−0.00012, +0.00171] | fail | no |
| **F5 Weather** | 0.19647 | 0.19594 | −0.00053 [−0.00227, +0.00110] | −0.00052 [−0.00225, +0.00110] | **PASS** | no |
| F6 Unders (main lines) | 0.24699 | 0.24744 | +0.00045 [−0.00069, +0.00163] (single main-line de-vig) | | fail | no |
| **Combined (F2 + F5)** | 0.19647 | 0.19578 | −0.00069 [−0.00246, +0.00097] | −0.00067 [−0.00243, +0.00098] | **PASS** | **no** |

**What the fitted coefficients say** (weeks 1–9, hold method, per standard deviation of the feature):
- **F1 overfit.** Receptions β = +0.57 on the man/zone matchup in weeks 1–9, which didn't hold in weeks 10–18.
- **F2's direction is plausible:**
  - receptions: implied team total +0.11, underdog +0.05
  - rec_yds: underdog −0.09, implied total −0.02
- **F5's direction is plausible:** wind −0.13 to −0.14 for both markets. Precipitation is ~0.
- **F4:** the player's home/away split pointed the wrong way out of sample (receptions −0.39).

By design, a factor with no real information passes a point-estimate rule about half the time. Two of six passing, both inside noise, is what that looks like.

## 4. "Factor says better than price" cards (weeks 10–18)

- **Rule:** flat 1u singles; one leg per player-game-market; the floor-band rung (raw implied 60–95%) with the highest EV at DK's posted price; EV > 0.
- **Mean model p** is the factor model's probability of the chosen side, before any vig.

| Card | Status | Legs | Games | Hit | Avg implied | Mean model p | ROI | 95% CI |
|---|---|---|---|---|---|---|---|---|
| **Combined F2 + F5** | **registered** | 287 | 60 | 59.9% | 66.3% | 67.6% | **−9.91%** | [−18.64, −1.23] |
| Unders (F6) | registered only if F6 passed: **none** | | | | | | | |
| F1 man/zone | descriptive | 153 | 80 | 55.6% | 67.2% | 69.0% | −17.63% | [−30.52, −4.80] |
| F2 game script | descriptive | 70 | 28 | 58.6% | 64.2% | 64.7% | −8.47% | [−24.12, +6.34] |
| F3 pass tendency | descriptive | 8 | 6 | 50.0% | 63.1% | 63.5% | −20.23% | [−64.18, +37.89] |
| F4 defense weak points | descriptive | 249 | 106 | 57.4% | 66.5% | 68.1% | −13.61% | [−24.28, −3.47] |
| F5 weather | descriptive | 74 | 41 | 54.1% | 61.3% | 61.4% | −11.79% | [−28.44, +5.72] |
| F6 unders (main lines, either side) | descriptive | 520 | 132 | 52.1% | 52.6% | 55.6% | −0.76% | [−8.17, +6.84] |

- **Every card that picks legs where a factor "beats the price" lost.** Hit rates land 6–12 points below DK's implied probability: the legs a factor likes are the ones where it's overconfident.
- **The near-flat unders card** (−0.8%, CI spanning 0) is roughly what −110 main lines cost at random.

## 5. Conclusion

- **No real information beyond DK.** On 2025 DK receptions/rec_yds prices, none of the six situational factors (man/zone, game script, pass tendency, defense weak points, weather, unders) carries information beyond DK's de-vigged price that survives an out-of-sample test with its uncertainty shown.
- **Pass-but-noise:** game script and weather pass the registered rule, but only by noise-sized margins.
- **No profitable card:** a card built from them loses money at DK's prices.
- **Consistent with the earlier verification:** this matches `NFL_VERIFY_RESULTS.md`. DK's alt receptions/yards prices already reflect the public situational reads tested here.

**What isn't covered (Tim's call):**
- volume/attempt props (pass_att, rush_att, pass_cmps), about 16,320 credits
- alignment and true route data, which need a paid source (e.g. PFF)
- other books' prices (NBA item 2's cross-book idea applies here too)
- 2026 forward data for the two pass-in-noise factors, under a new pre-registration

## Files (branch `nfl-verify`)

| Path | Contents |
|---|---|
| `docs/nfl/PREREG_FACTORS.md` | Pre-registration |
| `engine/nfl/factor_study.py` | `build` / `run` |
| `data/nfl/verify/factor_rows_A.parquet`, `factor_rows_B.parquet` | Feature tables |
| `data/nfl/verify/factor_results.json` | Every number above, with coefficients and per-market Brier |
| `data/nfl/verify/factor_run.json` | Run marker |

The nflverse play-by-play and participation downloads are cached locally (gitignored).
