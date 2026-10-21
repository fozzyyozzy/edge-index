# NFL Early-Line, Cross-Market Lag and Cross-Book Results (2025 regular season)

**Date:** 2026-10-21 · **Pre-registration:** `docs/nfl/PREREG_EARLY_LINES.md` · **Status:** done; stopping for Tim.

## Audit trail (branch `nfl-verify`)

| Step | Commit / time (UTC) |
|---|---|
| PREREG registered, before any pull | `d1f94edb` |
| Pulls + analysis code committed, nothing run | `228f9129` |
| **Attempt 1** (17:05) | **crashed in test C** (a bug building the bet-side column) **before writing or printing any result**. Marker and traceback kept: `early_run_attempt1_crashed.json`, `early_stdout_attempt1_crashed.txt`. |
| One-line fix | `feed8b13` |
| **Attempt 2** | **crashed at the save step** (a tuple-keyed count table isn't JSON-serializable) before writing or printing any result. Kept: `early_run_attempt2_crashed.json`, `early_stdout_attempt2_crashed.txt`. |
| Generic JSON sanitizer; no analysis change | `13e91ce4` |
| **Attempt 3 (17:07) = the registered result** | **wrote `data/nfl/verify/early_results.json` in full.** It then failed only in a final console-summary print. |

No numbers were seen from attempts 1 or 2: each produced only a traceback and no results file. The analysis logic is identical across attempts, apart from the one-line bet-side fix in test C.

**Spend:** **38,610 credits** of the 42,000 cap, 100k reserve guard on. Account remaining after: 4,710,071.
- **Prop snapshots:** 816 calls at kickoff −72h, −24h and close, with **all US books** (`regions=us`).
- **Game lines:** 395 bulk snapshots of spreads/totals.

## TL;DR

1. **DK floor prices barely move after 72 hours out.** The typical de-vigged change from E72 to close is about **2.5 points** (2.0 from E24).
   - **Test A (movement):** three factor models "pass" by mean-squared-error gains of ~0.000001. That's about 0.2% of the move variance, with confidence intervals that include zero.
   - **Under §7 they're CANDIDATES only,** and in practice they predict nothing.
2. **Test B:** at the registered 2-point threshold, **no factor ever predicted a move that large, so there are zero favored legs and no candidate.**
   - **Model-free floor band:** buying the whole floor band early gave **no closing-line value** (E72: −0.01 pts; E24: **−0.18 pts, CI below 0**).
   - **Flat return at early prices:** −10.1% (E72) and −11.7% (E24) on test weeks.
3. **Test C (cross-market lag):** **no lag.**
   - **Lag regression:** prop moves after a game-line move have slope **−0.0002** per point of implied team total (CI −0.0025 to +0.0020).
   - **Bets after 1.5-point implied-total moves:** CLV −0.25 pts and ROI −6.3%, both CIs spanning 0.
4. **Cross-book (descriptive):** at the close, **42% of DK floor rungs have a better price at another US book**, by a median of 1.4 implied points (19 cents). FanDuel is most often best.
   - Buying every floor rung at the best available price improves the flat return from **−9.0% to −8.1%**. It's still deeply negative.

## Coverage

| Snapshot | DK games with props | DK receptions-alt players per game (median) | Lead time |
|---|---|---|---|
| E72 | 208 of 272 | 6 | 72.1h |
| E24 | 265 of 272 | 9 | 24.1h |
| Close (all books) | 272 of 272 | 11 | 0.2h |

- **Books returned:** DraftKings, FanDuel, BetOnline, Bovada, BetRivers, Caesars (williamhill_us), BetMGM, Fanatics.
- **No receptions-alt ladder at the close:** **BetMGM and Caesars** (0 games). Fanatics has no rec_yds alt ladder.
- **DK game lines:** E72, E24 and close for 272/272 games; the weekly Sunday-night OPEN for 256/272.

## Test A: do the factors predict DK's price movement?

- **Rows:** DK alt rungs priced at both S and close, with a settled outcome. E72: 21,487 (fit 10,405 / test 11,082). E24: 43,812 (22,425 / 21,387).
- **Δp** is the de-vigged close minus the early price.

| Model | E72 ΔMSE (hold) [95% CI] | E24 ΔMSE (hold) [95% CI] | Rule (both methods, ≥ 1 snapshot) | Direction accuracy (test) |
|---|---|---|---|---|
| F1 man/zone | −1.3e-6 [−3.8e-6, +1.4e-6] | +2.1e-6 [+0.4e-6, +4.0e-6] (worse) | **CANDIDATE** (E72) | 54.5% (E72) / 50.5% (E24) |
| F2 game script (DK early lines) | +1.8e-6 | +1.9e-6 | fail | 52.6% / 52.5% |
| F3 pass tendency | +0.6e-6 | −0.05e-6 [−0.5e-6, +0.4e-6] | **CANDIDATE** (E24) | 53.2% / 50.6% |
| F4 defense weak points | +1.1e-6 | +0.2e-6 | fail | 53.1% / 53.5% |
| F6 unders | +4.8e-6 | +0.6e-6 | fail | 47.6% / 48.7% |
| Combined (F1 + F3) | −0.7e-6 [−4.2e-6, +3.0e-6] | +2.1e-6 (worse) | **CANDIDATE** (E72) | 53.8% / 51.3% |

- **Scale:** the constant-model MSE is ~6.5e-4 at E72 (an RMS move of 2.55 pts) and ~4.0e-4 at E24 (2.01 pts). The "passing" gains are about 0.2% of that, and every CI includes 0.
- **Status:** these three are **CANDIDATES** under §7. Whether they get promoted depends on §8 (2026 weeks 7–18).
- **No practical use either way:** none produces a move prediction big enough to bet (Test B).

## Test B: legs factors favor, bought early

| Model | Favored legs at the **2-pt** threshold (registered) | At 1 pt (sensitivity) | At 3 pts |
|---|---|---|---|
| F1 | 0 | 14 (E72), 2 (E24) | 0 |
| F2-early | 0 | 173 (E72; ROI −3.7%) | 0 |
| F3 | 0 | 0 | 0 |
| F4 | 0 | 41 (E72) | 0 |
| F6 | 0 | 15 (E72; ROI −38%) | 0 |
| Combined | 0 | 13 (E72), 2 (E24) | 0 |

**Registered verdict for every model: no legs, so no CLV or profitability claim.** The 1-point sensitivity samples are too small to read.

**Model-free: every DK floor-band rung (raw implied 60–95%) bought early, held to the close:**

| Snapshot | Weeks | n | CLV hold (pts) [95% CI] | CLV anchor (pts) | Hit − closing p (pts) [95% CI] | Flat ROI at the early price [95% CI] |
|---|---|---|---|---|---|---|
| E72 | 10–18 | 2,172 | −0.01 [−0.24, +0.21] | +0.02 | −3.3 [−6.7, +0.0] | **−10.1%** [−14.6, −5.7] |
| E72 | all | 4,202 | +0.16 [−0.02, +0.33] | +0.15 | −1.5 [−3.9, +0.9] | −7.7% [−10.8, −4.5] |
| E24 | 10–18 | 3,802 | **−0.18** [−0.37, −0.02] | −0.18 | −4.1 [−6.5, −1.8] | **−11.7%** [−14.8, −8.6] |
| E24 | all | 7,946 | −0.01 [−0.12, +0.10] | −0.01 | −2.3 [−3.9, −0.8] | −9.1% [−11.2, −7.0] |

Early DK floor prices aren't systematically better than the close. If anything, E24 prices are slightly worse, and early-bought floor legs lose as much as or more than at the close.

## Test C: does the prop market lag game-line moves?

**Primary sample: all 18 weeks.**

| Trigger | Bets | Games | Sides | CLV hold (pts) [95% CI] | Hit − close | ROI [95% CI] | Verdict |
|---|---|---|---|---|---|---|---|
| **ΔITT ≥ 1.5 (registered)** | 191 | 35 | 119 Under / 72 Over | −0.25 [−1.05, +0.42] | +0.2 pts | −6.3% [−25.9, +15.7] | no lag, not exploitable |
| ΔITT ≥ 1.0 (sensitivity) | 486 | 81 | 252 U / 234 O | 0.00 [−0.37, +0.37] | +3.1 | +0.5% [−10.0, +11.0] | — |
| ΔITT ≥ 2.5 (sensitivity) | 36 | 8 | 21 U / 15 O | −0.56 | −17.0 | −39.6% [−74.2, +1.1] | — |
| **Spread toward underdog ≥ 1.5 (registered)** | 132 | 27 | Over | +0.15 [−0.48, +0.82] | −4.6 | −13.3% [−37.3, +9.2] | no lag, not exploitable |
| Spread ≥ 1.0 (sensitivity) | 462 | 83 | Over | +0.26 [−0.10, +0.66] | −6.1 | −17.4% [−29.2, −5.4] | — |
| Spread ≥ 2.5 (sensitivity) | 50 | 11 | Over | +0.45 | +2.9 | +2.0% [−29.8, +33.1] | — |

- **Lag regression:** prop Δp (buy → close) on the preceding ΔITT gives slope −0.00019 per point, CI [−0.0025, +0.0020], n = 4,515. **No lag.**
- **Weeks 10–18 alone** (ITT 1.5): 91 bets, CLV −0.56 pts, ROI −9.4%.
- **Caveat:** DK's props appear to adjust to game-line moves **within the same 1–2-day window**. A sub-hour lag can't be ruled out at this snapshot grid; testing it needs dense snapshots (about 261,000 credits).

## Cross-book price gaps (descriptive)

| Snapshot | DK floor rungs | Matched at another book | **Another book better** | Median gain when better | Most often best |
|---|---|---|---|---|---|
| Close | 8,836 | 8,383 | **42.1%** | 1.36 implied pts / **19 cents** | FanDuel 1,361 · Fanatics 606 · Bovada 567 · BetRivers 437 · Caesars 308 |
| E24 | 8,103 | 7,649 | 37.0% | 1.28 pts / 17 cents | FanDuel 926 · Fanatics 594 · BetRivers 458 |
| E72 | 4,324 | 3,808 | 38.4% | 1.40 pts / 19 cents | FanDuel 464 · Caesars 414 · Fanatics 282 |

- **Same-rung coverage vs DK's floor rungs at the close:**

| FanDuel | Bovada | BetRivers | Fanatics | BetOnline | BetMGM | Caesars |
|---|---|---|---|---|---|---|
| 92% | 76% | 43% | 37% | 30% | 17% | 15% |

- **Flat floor-band return at the close (n = 8,723):**
  - DK price: **−9.03%** [−11.09, −7.03]
  - best available US price: **−8.13%** [−10.21, −6.10]
- **Line shopping is real but small next to the vig on floors.** It recovers about 0.9 points of return.

## What this means

- **Timing isn't the missing edge.** On 2025 DK receptions/rec_yds props, nothing in entry timing creates an edge:
  - Early prices move little (2–2.5 pts RMS).
  - The factors don't predict which way they move.
  - Floors bought early lose as much as at the close.
  - Props show no measurable lag behind game-line moves at a 1–2-day scale.
- **Line shopping helps, but too little.** Shopping across 7 other books beats DK on about 40% of floor rungs, by around 19 cents. That's worth roughly +0.9 points of return, not enough to make floor betting profitable.
- **CANDIDATES (A: F1, F3, combined):** these pass only at the 1e-6 MSE level and predict no bettable move. §8's forward rule applies to them, but there's no practical reason to expect promotion.
- **Tim's decisions:**
  - whether to run the §8 forward check at all (Test C forward also needs about 4,000 credits of game lines)
  - whether any of the NBA items 2–4 still make sense given these results

## Files (branch `nfl-verify`)

| Path | Contents |
|---|---|
| `docs/nfl/PREREG_EARLY_LINES.md` | Pre-registration |
| `docs/nfl/EARLY_LINES_DRYRUN.md` | Dry-run costs |
| `engine/nfl/early_pull.py` | Pulls |
| `engine/nfl/early_tests.py` | Tests |
| `data/nfl/verify/early_props_2025.parquet` | 717,212 outcomes, 8 books, E72/E24/close |
| `data/nfl/verify/game_lines_2025.parquet` | 359,882 outcomes |
| `data/nfl/verify/early_results.json` | Every number above |
| `data/nfl/verify/early_run.json` | Attempt-3 marker |
| `*_attempt{1,2}_crashed.*` | The two failed attempts |
| `data/nfl/verify/odds_usage_nfl_verify.csv` | Every paid call |
