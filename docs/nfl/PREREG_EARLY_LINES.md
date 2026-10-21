# NFL Early-Line and Cross-Market Lag Tests: Pre-Registration

> **Status: approved by Tim 2026-10-21. Registered by the commit that adds this file to `nfl-verify`.**
> - **Order:** this commit → pulls (cap **42,000 credits** total, 100k reserve guard) → each test runs **once** (marker files).
> - **Decisions (Tim, 2026-10-21):**
>   - B threshold 2 pts, with 1 and 3 pts as non-gating sensitivity
>   - C trigger 1.5 pts, with 1.0 and 2.5 as non-gating sensitivity
>   - weather excluded from A/B
>   - C primary = all 18 weeks
>   - any 2025 pass is a CANDIDATE only (§7)
>   - forward promotion rule written now (§8)

## 0. Questions

- **A. Movement:** do the factor features predict which way DK's receptions/rec_yds prices move between an early snapshot and the close?
- **B. CLV and return:** legs the factors favor, bought at **early** prices:
  - do they hit above the **closing** de-vigged probability?
  - what is their flat return at the early price?
- **C. Cross-market lag:** when DK's game total or spread moves, do the affected players' prop prices lag? Do props bought after the move, in the direction it implies, beat the closing de-vigged price?

## 1. Data

- **Snapshots:** E72 = kickoff − 72h, E24 = kickoff − 24h, CLOSE = kickoff − 10 min.
  - Every prop call requests **all US books** (`regions=us`). That's the same cost as DK alone.
  - **The tests use DraftKings only.** Other books are descriptive (§6b).
  - The close is re-requested once per game with all US books. DK's close prices for the tests stay the ones already pulled (`hist_props_2025.parquet`).
- **Game lines:** spreads/totals at OPEN (weekly, the previous Sunday 23:55 ET), E72, E24 and CLOSE, from bulk calls with `regions=us`. Test C uses DK's numbers.
- **Outcomes:** nflverse weekly stats. Unmatched = UNGRADEABLE, excluded and counted.
- **De-vig, both methods as in NBA §6.2/§9.1:** hold-based from the same snapshot's two-way main line, and ladder-anchored.
- **Split:** fit = 2025 weeks 1–9, test = weeks 10–18 (regular season only).

## 2. Features: all known at the early snapshot

| Factor | As in `PREREG_FACTORS.md` | Changes for an early bet |
|---|---|---|
| F1 man/zone | same | none |
| F2 game script | — | **Replaced:** `implied_total` and `team_spread` from **DK game lines at the same early snapshot** (the factor study used nflverse closing lines, which aren't known at an early snapshot). |
| F3 pass tendency, F4 defense weak points | same | none |
| F5 weather | — | **Excluded from A and B:** there are no point-in-time forecasts. |
| F6 unders | same, on main lines | none |

All rolling features keep the strict as-of rule: only games before the row's game.

## 3. Test A: does a factor predict price movement?

- **Unit:** a (player, market, rung k, early snapshot S ∈ {E72, E24}) where rung k has a DK alt price at both S and CLOSE.
- **Target:** `Δp = p_CLOSE(k) − p_S(k)`, de-vigged, computed separately per method.
- **Model:** per factor, per market, per S, per method: linear regression `Δp ~ β·x`, fit on weeks 1–9.
- **Baseline:** the fit-week mean Δp (a constant).
- **Pass:** test-week MSE below the baseline's under **both** de-vig methods, for **at least one** of E72/E24. Each S is reported separately.
- **Also reported:** directional accuracy, i.e. the share of test rows where sign(predicted − baseline) = sign(Δp − baseline), with a game-clustered CI. And whether the MSE gain's CI excludes 0 ("distinct from noise").
- **Combined model:** the passing factors fit jointly, same rule.

## 4. Test B: factor-favored legs bought early: CLV and return

- **Favored legs** (test weeks 10–18, each S): the factor's (or the combined model's) predicted Δp ≥ **+0.02**, i.e. the price is expected to shorten by 2+ points.
  - **Sensitivity:** +0.01 and +0.03, reported, **non-gating**.
  - **Which models:** B runs for every factor's A model, whether or not it passed A, and for the combined model if one exists. Each gets its own verdict, all subject to §7.
  - Only floor-band rungs (raw implied 60–95% at S).
  - One leg per player-game-market, the largest predicted Δp.
- **Metrics:**
  1. **Price CLV:** mean `p_CLOSE(k) − p_S(k)` (de-vigged), with a game-clustered 95% CI, per method.
  2. **Hit vs close:** hit rate − mean `p_CLOSE(k)`, with CI.
  3. **Flat return at the early price:** flat 1u singles settled at the S price, ROI with CI.
- **Verdicts:**
  - **CLV CONFIRMED** if metric 1's CI is above 0 under both methods.
  - **PROFITABLE** if metric 3's CI lower bound is > 0.
  - Otherwise "not confirmed" / "not profitable".
- **Also reported, model-free:** the same metrics for all floor-band rungs at E72 and E24, unselected, to show general early-vs-close drift.

## 5. Test C: cross-market lag

- **Game-line move:** for each team-game, the change in implied team total `ΔITT` and in team spread between consecutive game-line snapshots:
  - OPEN→E72 (props bought at E72)
  - E72→E24 (props bought at E24)
- **Trigger:** `|ΔITT| ≥ 1.5` points.
  - **Sensitivity:** 1.0 and 2.5, reported, **non-gating**.
  - Separately, `|Δspread| ≥ 1.5`: the team moving toward underdog implies more passing, so its pass-catchers' Overs.
- **Bet direction:** ITT up → **Over**, ITT down → **Under**, on the receptions and rec_yds **main lines** (two-way, so both directions are bettable) of that team's WR/TE/RB with a main line at the buy snapshot.
- **Metrics:** at the buy snapshot vs CLOSE:
  - price CLV for the bet side (closing de-vig minus buy de-vig, same line; lines that changed use the alt rung at the buy line if priced, otherwise excluded)
  - hit minus closing de-vig
  - flat ROI at the buy price
  - game-clustered CIs
- **Lag regression:** `Δp_prop(buy→CLOSE) ~ ΔITT(previous window)`. A coefficient > 0 with a CI excluding 0 is evidence of lag.
- **Sample:** there are no fitted parameters (the thresholds are fixed here). **Primary sample is all 18 regular-season weeks; weeks 10–18 are also reported.**
- **Verdict:**
  - **LAG CONFIRMED** if mean CLV's CI > 0 **and** the lag coefficient's CI > 0.
  - **EXPLOITABLE** if flat ROI's CI lower bound is > 0.

## 6b. Cross-book price gaps (descriptive)

- **Rows:** every DK floor-band alt Over rung (raw implied 60–95%) at CLOSE, E24 and E72.
- **Comparison:** the same player, market and point at each other US book in the same snapshot.
- **Reported:**
  - the share of DK rungs where at least one other book is **better**, i.e. pays more (higher decimal)
  - the median and mean improvement, in implied-probability points and in American-odds cents
  - which books are most often best
  - each book's floor-rung coverage relative to DK
- **Also:** the flat return of the floor band when every leg is bought at the **best available** US price instead of DK's. Descriptive; same settlement as `NFL_VERIFY_RESULTS.md` Q1.

## 6. Integrity

- **Order:** every rule above is fixed before any early or game-line price is pulled.
- **Once only:** each test runs once, with marker files.
- **No tuning:** failing factors are dropped, not tuned.
- **Slices are hypotheses:** by team, week or role (CLAUDE.md rule 5).
- **Snapshot thinness:** early ladders are thinner than close ones, so the set of players with early prices is not random. Results describe **posted-early** players.
- **No production impact:** nothing here changes the live pipeline.

## 7. Multiple comparisons: every 2025 pass is a CANDIDATE

- **How many tests:** A runs 4 factors (F1, F2-early, F3, F4) + F6 + combined, × 2 snapshots × 2 de-vig methods. B runs the same models at 3 thresholds. C runs 2 triggers × 3 thresholds.
- **Why:** with this many, some will pass by chance.
- **Rule: any 2025 pass**, in A, B (CLV or PROFITABLE) or C (LAG or EXPLOITABLE), is reported as **CANDIDATE**, never "confirmed".
- **Promotion:** a candidate is promoted only by §8.

## 8. Forward promotion rule (2026), written now

- **Data:** the live pipeline's own timestamped DraftKings pulls.
  - `refresh-odds` and `card` re-run `fetch_lines.py` at fixed slots (Thu 09:00/15:00/19:00, Fri 15:00, Sat 12:00, Sun 09:00/12:00, Mon 09:00/15:00/19:00 ET), and `sun-snapshot` runs Thu 09:07 ET.
  - Each pull is committed (`automation/lines/ladders_2026_w*.csv`, `twoway_*`, `snapshots/`) with its `PulledAt` time. Git history is the price record.
  - The standalone `EdgeIndexCollector` task is currently disabled. If Tim re-enables it, its `data/odds_snapshots.db` pulls count too.
- **Forward snapshots, per game:**
  - **E72f:** the DK pull nearest kickoff − 72h, within ±12h.
  - **E24f:** nearest kickoff − 24h, within ±6h.
  - **CLOSEf:** the last pull before kickoff, at most 6h before it. Games without one are excluded and counted.
- **Forward game lines (C):** the live pipeline doesn't store spreads/totals. Forward C uses historical bulk game-line calls at the same E72f/E24f/CLOSEf times plus the weekly OPEN. That's about 20 credits per call, roughly 4,000 credits for weeks 7–18, subject to the 2,000-credit approval rule.
- **What is frozen:**
  - the 2025 fit (coefficients from 2025 weeks 1–9, **no refit**)
  - thresholds, de-vig methods, leg rule, trigger
- **Window:** 2026 week 7 through week 18 (or the last regular-season week played).
- **Promotion: a CANDIDATE is PROMOTED only if all hold on the forward window:**
  1. The same rule passes:
     - A: MSE beats the constant under both methods.
     - B/C: the mean CLV CI is above 0 under both methods, or the ROI CI is above 0, for a PROFITABLE/EXPLOITABLE claim.
  2. There are at least **6 forward weeks** and **≥ 150 legs** (B/C) or **≥ 1,500 rows** (A).
  3. The effect has the same sign as in 2025.
- **Not yet:** a candidate short of the sample minimum stays CANDIDATE ("insufficient, keep collecting").
- **Demotion:** a candidate whose forward point estimate has the opposite sign is **dropped**.
- **No production use:** nothing is used on a card or in subscriber copy until promoted.
