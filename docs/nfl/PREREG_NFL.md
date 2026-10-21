# NFL Floor Verification: Pre-Registration

> **Status: approved by Tim 2026-10-21. Registered by the commit that adds this file to branch `nfl-verify`,** before any 2025 price is pulled or any replay is run.
> - **Order:** this commit → DK pull (cap 12,000 credits, 100,000 reserve guard) → replay and analysis **once**. A marker file blocks a re-run.
> - **Models:** frozen exactly as on `main` at `5081b73d`.
> - **2025 pull:** costed in `NFL_VERIFY_COST.md`.

## 0. The question

Does the NFL floor edge survive real DraftKings prices? The edge is receptions alt floors clearing far more often than their price implies. The "books hang −175/−300" figure in CLAUDE.md/ROADMAP has no price source; **this test is its first check.**

## 1. Data

- **Prices:** DK only, one Odds API historical snapshot per 2025 game at **kickoff − 10 min**. Markets:
  - `player_receptions`, `player_receptions_alternate`
  - `player_reception_yds`, `player_reception_yds_alternate`
  - An event whose kickoff is at or before the snapshot is refused.
  - The contaminated 2025 `prop_lines` rows in `backtest/nfl/edge_index.db` are **never** used for prices (CLAUDE.md rule 1).
- **Outcomes:** nflverse `stats_player_week_2025` (receptions, receiving_yards), the source the live pipeline grades from.
- **Unmatched rows:** a DK name with no nflverse match (`norm_name` + team) is **UNGRADEABLE**: counted, never WIN/LOSS.
- **Scope:**
  - **Primary:** 2025 regular season, weeks 1–18.
  - **Reported separately:** the 2025 playoffs (Q1, Q2 and Q4 only; the card's slate logic is regular-season).
- **Secondary forward check:** 2026 weeks 3–6, the pipeline's own pregame DK ladders and cards (`automation/lines`, `automation/cards`). It's reported separately and costs nothing.

## 2. Frozen models: no tuning

| ID | Probability |
|---|---|
| **MO** (model-only) | `common.leg_prob(values, rung, p_market=None)`: the lower L10/L15 add-one rate, capped at 0.90 |
| **LB** (live blend) | `common.leg_prob(values, rung, p_market=novig)`: market = 10 games, cap 0.90. **What the card uses.** |
| **FS** (floor study) | `engine/nfl/floor_study.py` μ: DECAY 0.85, ≤ 16 prior games, ≥ 7 required |

- **History rules:** as `floors.py`/`grade_legs.py` (regular season S−2…S, involvement games, `grading_history` minimums).
- **Honesty caveat:** 2025 outcomes were visible when these rules were built. 2025 therefore tests **the market and the frozen rules as they stand**. Calibration on 2025 is reported, **not gating**. The 2026 forward check is the clean test.

## 3. Replay method (Q3)

The **live scripts themselves** are run for each 2025 week and slate (tnf/sun/mnf, via `floors.SLATE_DAYS`): `floors.py` → `grade_legs.py` → `build_card_json.py`, at `5081b73d`.
- **Root:** each run uses a temporary automation root (`EDGE_ROOT`).
- **Inputs:** that week's DK ladders, two-way lines and main lines, built from the pulled snapshots in the pipeline's own file formats.
- **Walk-forward:** every nflverse load the scripts make (`fetch_season`, availability's snap counts and stats) is patched to return **only weeks before the replayed week** of the current season. The replay asserts it.
- **Markets:** receptions and rec_yds only (the only ones priced here). The live card also uses pass/rush markets, so replayed tickets are built from a smaller menu than the live card had.
- **Injuries, two variants. Both are run and both reported:**
  - **WITH (primary):** `availability.build` as live, using:
    - nflverse snap counts and weekly stats before the week ("missed one of the team's last two games")
    - nflverse `injuries_2025` for the week: Out/Doubtful/Questionable and DNP are holds; Limited with no status is an injury-watch flag (R11)
    - QB-change flags
  - **Limits of WITH:**
    - the injury report is the week's final state, while the live card is built Friday 09:00 ET and may have seen an earlier one
    - manual holds (`notes/holds_*.csv`) can't be reconstructed and aren't applied
  - **WITHOUT (sensitivity):** an empty availability snapshot, so no injury holds or flags at all.
- **Not reconstructable:**
  - manual holds
  - any hand edit made before a card locked (MODEL_CHANGELOG)
  - the Thursday price snapshot used for Sunday cards (display only; no rule reads it)

## 4. Pre-registered tests

### Q1. Market efficiency (no model)
- **What's measured:** flat 1u on **every** DK alt Over rung with raw implied probability in [0.60, 0.95), by market and 5-pt bin, at the posted price.
- **Uncertainty:** game-clustered 95% bootstrap CI (10,000 resamples, seed 20261021).
- **Also reported:** hit rate vs raw implied and vs de-vigged probability.

### Q2. Does the model add information? (NBA PREREG §9.3–9.4 rule)
- **Rows:** `p_hold` ∈ [0.50, 0.97] with both de-vig methods (hold-based and ladder-anchored, as defined in NBA §6.2/§9.1).
- **Brier compared:** market-only (both methods), MO, LB, and `w·MO + (1−w)·p_m` for w ∈ {0.1, 0.2, 0.4, 0.6}.
- **Weight rule:**
  - A blend qualifies only if it beats market-only under **both** methods.
  - Pick the lowest hold-method Brier, with ties going to the smaller w. If none qualify, w = 0.1.
  - The per-market valve then applies.
- **Also reported:** whether LB beats market-only under both methods.

### Q3. The live card's selections (the product test)
- **Unit:** every **card candidate** `build_card_json.py` produces: one leg per player-market, the R3 best-graded qualifying rung after R4 (edge ≥ +2), the −450 price cap, R9 (grade ≥ C) and the R6 holds.
- **Metric:** flat 1u singles. ROI with a game-clustered 95% bootstrap CI.
- **Primary verdict: WITH injuries, single legs.**
  - **CONFIRMED** if the CI's lower bound is > 0.
  - **REFUTED** if its upper bound is < 0.
  - **INCONCLUSIVE** otherwise.
  - WITHOUT gets the same verdict, as a sensitivity.
- **Tickets (descriptive, not a verdict):** the replayed cards' tickets (R1–R11, `build_tickets`). Each ticket settles WIN only if every leg wins, paying the product of decimal prices. Reported:
  - ticket count, hit rate, ROI
  - the product of the legs' MO and LB probabilities vs the ticket's actual hit rate
  - **compounded vig:** the ticket's implied probability (product of raw implied) ÷ the product of de-vigged probabilities

### Q4. The "0.6× floor at −175/−300" claim
- **Rows:** player-weeks with FS μ_receptions ≥ 3.
- **The rung:** the DK alt rung nearest `max(floor(0.6μ) − 0.5, 0.5)`, ties going to the lower rung.
- **Reported:** median and IQR of DK's price, hit rate, flat ROI with the clustered CI.
- **Verdict:**
  - **Supported** only if the median DK price is longer than **−400** **and** flat ROI's CI lower bound is > 0.
  - Otherwise **not supported**, with the reason.
- **Comparison:** the same for rec_yds at 0.6×, using the study's yardage line `floor(1.2μ)/2 + 0.5`.

### Calibration (reported, not gating)
Reliability tables and calibration slope (p 0.50–0.97) for MO and LB per market.

## 5. Integrity

- **One run:** the analysis runs **once**, and a marker file blocks a re-run. If code is fixed afterwards, both runs are reported and the first stands.
- **No tuning:** nothing is retuned on 2025 prices. A rule change suggested by the results gets a new pre-registration, judged on 2026 forward data.
- **Slices found after looking** are hypotheses only (CLAUDE.md rule 5).
- **Live pipeline untouched:** nothing here changes a locked card or the live pipeline.
