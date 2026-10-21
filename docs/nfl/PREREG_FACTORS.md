# NFL Factor Study: Pre-Registration

> **Status:** approved in substance by Tim (2026-10-21 instructions). Feature definitions written by Claude.
> **Registered** by the commit that adds this file to `nfl-verify`, **before** any feature is computed against an outcome.
> **Run:** fit on weeks 1–9, test on weeks 10–18, **once.** A marker file blocks a re-run.
> No new Odds API pull: it uses the 2025 DK prices already pulled (`data/nfl/verify/hist_props_2025.parquet`).

## 0. Question

Do situational reads carry information **beyond DraftKings' price**? Each factor is tested on its own:

> Does it predict `outcome − p_DK(de-vigged)`?

## 1. Data scope, checked before building

| Need | Source | 2024 | 2025 | Gap |
|---|---|---|---|---|
| Man/zone per dropback | nflverse `pbp_participation` → `defense_man_zone_type` | all REG weeks, ~11.2k tagged dropbacks/half | all REG weeks, ~22k tagged | none |
| Receiver routes | `pbp_participation.route` = **targeted receiver's route only** | | | **No per-player route participation.** Routes are approximated by "on field (`offense_players`) on a man/zone-tagged dropback". |
| Alignment (slot/wide) | not in nflverse (participation, FTN charting, PFR) | | | **Not available.** The alignment part of factor 4 is dropped. |
| Targets, yards, pass-rate-over-expected (`pass_oe`), win probability, weather text | nflverse `play_by_play` | ✓ | ✓ | none |
| Spread, total, roof, wind | nflverse schedule (`spread_line`, `total_line`, `roof`, `wind`) | ✓ | ✓ | These are closing lines; wind is game-time actual (≈ the forecast). Noted as a mild look-ahead on weather. |
| Player ids, positions | nflverse weekly player stats | ✓ | ✓ | DK name → gsis id via `norm_name` + team; unmatched rows are dropped (counted). |
| Volume props for big favorites (attempts, carries) | **not pulled** | | | **Not testable without a new pull.** Est. `pass_att`, `rush_att`, `pass_cmps` main + alt, 2025 REG: 6 markets × 10 × 272 ≈ **16,320 credits**, which needs approval. Factor 6 is tested on receptions/rec_yds main-line unders only. |

## 2. Rows and target

- **Rows A, factors 1–5:** 2025 regular-season DK alt **Over** rungs for receptions and rec_yds where both `p_hold` and `p_anchor` exist and `p_hold` ∈ [0.50, 0.97]. These are the NFL PREREG Q2 rows and de-vig definitions.
- **Rows B, factor 6 (unders):** the two-way **main lines** (Over and Under) for receptions and rec_yds.
  - Market probability: proportional de-vig of the two sides. On a two-way main line, both de-vig methods reduce to this, because the anchor rung *is* the main line. Factor 6's "both methods" test is therefore this one de-vig, stated plainly.
  - The model predicts P(Over). Under = 1 − P(Over). Brier is the same for both sides.
- **Outcome:** clear or not, from nflverse weekly stats. VOID and UNGRADEABLE rows are excluded.
- **Split:** fit = weeks 1–9, test = weeks 10–18.

## 3. Features: computed only from games strictly before the row's game

- **Windows:** "Last 16" means the entity's last 16 regular-season games before the row's game, across 2024 and 2025. Implemented as an as-of join on (season, week) with exact matches excluded.
- **Normalization:** every feature is z-scored using **fit-week rows only** (mean/sd from weeks 1–9). Then a missing feature is set to 0, meaning no information.

| Factor | Features (receptions rows use counts; rec_yds rows use yards where noted) |
|---|---|
| **F1 man vs zone** | `mz = (opp_man_rate − league_man_rate) × (player_man_rate − player_zone_rate)`. **opp_man_rate:** the opponent defense's MAN share of man/zone-tagged dropbacks, last 16. **player rate:** targets per on-field tagged dropback (receptions rows) or receiving yards per on-field tagged dropback (rec_yds rows), vs man and vs zone, each shrunk as `x/(n+40)`, last 16. One feature. |
| **F2 game script** | `implied_team_total = (total ± spread)/2`; `team_spread` (+ = underdog). Two features. |
| **F3 pass tendency** | Team mean `pass_oe` (last 16); team neutral-script pass rate (pass share of plays with wp 0.20–0.80, quarters 1–3, last 16). Two features. |
| **F4 defense weak points** | `opp_allowed`: the opponent's per-game receptions (or rec yards) allowed to the player's **role group**, last 16, ÷ league per-game average for that group, − 1. **Role:** WR1/WR2/WR3+ by the player's target-share rank among his team's WRs over his last 4 games; TE; RB. Plus `home` (+1/−1) and `home_split`: the player's last-16 home mean − away mean, shrunk ×n/(n+8), on the row's stat. Three features. *(Alignment: not available.)* |
| **F5 weather** | Outdoor games only (`roof` ∈ {outdoors, open}; otherwise 0): `wind` mph and `precip` (1 if the play-by-play weather text mentions rain/snow/showers/sleet). Two features. |
| **F6 unders** (rows B) | `hot` = (last-3 mean − last-16 mean)/max(last-16 sd, 1) on the row's stat; `hot_x_tough` = hot × (−opp_allowed); `big_fav` = 1 if team spread ≤ −10. Three features. |

## 4. Model and pass rule

- **Model, per factor and per de-vig method m:**
  - `logit P(y) = logit(p_m) + Σ β_j x_j`, with **no intercept**, so the factor alone must carry the improvement.
  - β is fit separately for receptions and rec_yds, by maximum likelihood on fit weeks 1–9.
- **Test, weeks 10–18:** `Brier(p_factor)` vs `Brier(p_m)` on the same rows.
- **A factor PASSES only if test Brier is lower than DK's de-vigged price under BOTH methods** (rows A: hold and anchor; rows B: the shared main-line de-vig).
  - This is Tim's rule.
  - Also reported for each: ΔBrier with a game-clustered 95% bootstrap CI (10,000 resamples, seed 20261021).
  - A pass whose CI includes 0 is labeled **"passes, not distinguishable from noise."**
- **Failing factors are dropped, not tuned.**
- **Combined model:** the features of every factor that passed rows A fit together, same rule. F6 is evaluated on its own rows, so it's combined only with itself.

## 5. "Factor says better than price" card (weeks 10–18)

- **If the combined model exists:**
  - One leg per player-game-market. The leg is the floor-band rung (raw implied 60–95%) with the highest EV at DK's posted price.
  - A leg is taken only if `p_combined × decimal − 1 > 0` under the hold method.
  - Flat 1u singles. ROI with a game-clustered 95% CI.
- **Unders card:** the same for rows B, on whichever side is +EV.
- **If nothing passes:** there is no registered card.
- **Either way, per-factor cards are reported as descriptive only.** Each uses that factor's own model on weeks 10–18, with the same leg rule and labeled not-registered. That way the "what would a factor card have returned" question gets an answer whatever the verdicts.

## 6. Integrity

- **Multiple testing:** 6 factors are tested. With a point-estimate rule, a factor with no real information passes about half the time. That's why the CI label in §4 is reported alongside every pass.
- **Slices found after looking** (by team, week, role) are hypotheses only (CLAUDE.md rule 5).
- **No production use:** nothing here changes the live pipeline or a card.
