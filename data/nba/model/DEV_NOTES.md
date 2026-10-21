# Phase 2 development log (train 2023-24, validation 2024-25; no 2025-26 row loaded)

All passes ran `python -m engine.nba.phase2 dev`. Only the 2023-24 and 2024-25 seasons are loaded; `model.guard` refuses holdout rows.

| Pass | Change | 2024-25 validation | Kept? |
|---|---|---|---|
| 1 | Families Poisson / NB / discretised normal, chosen by validation RPS | Points, P+R, P+A and PRA chose the normal, with slope ~1.20–1.25 (too timid at both ends); reb, ast, threes, R+A and steals pass. Log: `dev_log_pass1.json` | — |
| 2 | Added a discretised gamma | RPS still preferred the normal (the gamma overcorrects: hot above 90%). Summary: `dev_pass2_stdout.txt` | no |
| 3 | Added a per-market logistic recalibration, cross-fitted (each season's params predict the other season) | Slopes ~0.92, but points and its combos went 2–3 pts **hot** in the 75–90 bins on honest cross-fit. Log: `dev_log_pass3.json` | **rejected** |
| 4 | Recalibration removed; added `dresid`: the training residuals' own standardised shape, with the fitted mean and variance | `dresid` has the best RPS for pts, reb, ast, P+R, P+A, R+A and PRA. 9/10 markets pass all bars; blocks is INSUFFICIENT (B0). Log: `dev_log.json` | **frozen** |

The frozen config (`frozen_config.json`) holds:
- **Minutes:** halflife 5 games.
- **Rates:** halflife 10 games, kappa 100 for pts/reb/ast/combos; 20/100 for threes, 20/300 for steals, 40/300 for blocks.
- **Matchup exponent (gamma):** 0.5 or 1.0 by market.
- **Families:** dresid, except NB for threes, steals and blocks.
- **Refit:** all parameters were refit on 2023-24 + 2024-25.

**Known limit:** the selected rate halflife (10) and kappa (100) sit at the edge of the search grid. A wider grid wasn't searched, so the setting is noted rather than tuned.
