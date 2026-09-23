# Edge Index — newsletter automation (handoff for Claude Code)

Everything runs on GitHub Actions in the existing repo. Four scheduled jobs, one manual step (paste lines), one approval (send the draft).

## Install (do this once, tonight)
1. Copy this `automation/` folder into the repo root (`C:\Users\tyose\edge-index\automation\`).
   Move `automation/.github/workflows/*.yml` into the repo's existing `.github/workflows/`.
2. Repo → Settings → Secrets and variables → Actions:
   - Secrets: `ANTHROPIC_API_KEY`, `ODDS_API_KEY` (The Odds API — real DK ladders; without it the job falls back to pastes)
   - Variable: `CURRENT_WEEK` = `3`
3. Substack: no API, so each run saves the issue to `newsletter/drafts/*.md` AND opens a GitHub issue labeled `newsletter`
   with the full text. Copy it into a Substack post, edit, send. (Create the `newsletter` label once in the repo.)
4. `pip install -r automation/requirements.txt` locally and run the smoke test below.

## Smoke test (local, ~2 min)
    cd edge-index
    python automation/pipeline/parse_lines.py --season 2026 --week 3
    python automation/pipeline/floors.py --season 2026 --week 3 --slate sun --lines automation/lines/dk_2026_w3_sun.csv
    python automation/pipeline/build_card_json.py --season 2026 --week 3 --slate sun
    DRY_RUN=1 python automation/newsletter/draft.py --kind card --season 2026 --week 3 --slate sun
    DRY_RUN=1 python automation/newsletter/draft.py --kind intro
(Windows: `set DRY_RUN=1` then the command.)

## Weekly rhythm
| When | You | Action |
|---|---|---|
| Wed AM | nothing (ladders fetched from The Odds API; pastes only as fallback) | `card` → floors → tickets → site JSON → draft issue |
| Fri AM | optional `notes/notes_<season>_w<week>.md` | same |
| Mon AM | nothing | same |
| Tue AM | nothing | `tuesday` → refresh nflverse → grade last week → receipts draft issue → bump `CURRENT_WEEK` |
| any | open the GitHub issue, paste into Substack, edit, send | — |

The card job fails loudly if the lines file for that slate is missing. That is intentional.

## What each file does
- `pipeline/fetch_lines.py` — pulls every DK alternate-line rung for every game from The Odds API (7 markets x games per pull; ~112 requests for a full week). Writes `lines/ladders_*.csv` (real prices) and the `dk_*.csv` main-line files. floors.py / grade_legs.py use real ladders when present and fall back to the estimator otherwise; the Legs JSON marks each player `prices: real|estimated`.
- `pipeline/parse_lines.py` — fallback: turns your raw DK page pastes (`lines/raw/w<week>/<market>.txt`) into the lines CSV. Both DK formats.
- `pipeline/floors.py` — floor scan: highest DK rung with L10>=80% and L15>=73%; est odds from the ladder model;
  opponent-defense + own-volume tags from nflverse team splits (prev season blended with current, weight = games/8 capped .6);
  opponents and spreads from the nflverse schedule. No hand-coded matchups.
- `pipeline/build_card_json.py` — applies the house rules R1–R7 (documented at the top of the file) and writes the card JSON.
- `pipeline/grade_legs.py` — grades EVERY DK rung A+..F for the site's Legs tab (`public/data/nfl_legs_<slate>.json`). Spec for the React tab: `LEGS_TAB_SPEC.md`.
- `pipeline/grade.py` — Tuesday grading against nflverse actuals; writes `receipts/*.json` and appends `receipts/season_ledger.csv`.
- `pipeline/altline_engine.py` — the ladder model (DK hold curve, ladder estimation, breakeven, parlay math).
- `newsletter/draft.py` + `newsletter/prompts/` — Claude writes the issue from JSON only; saved to `newsletter/drafts/` and posted as a GitHub issue. Never publishes anywhere.
- `lines/`, `notes/` — your two inputs. `cards/`, `receipts/` — outputs, committed by the bot.

## Known gaps (in priority order)
1. **Estimated odds run 10–25% generous on deep rungs.** Real prices from Week 2 slips are in the conversation; refit
   `HOLD_A/HOLD_B/EST_HOLD_BUMP` in `altline_engine.py` once ~30 est/real pairs are in `receipts/season_ledger.csv` (`odds_real` column —
   fill it in the card JSON before Tuesday if you placed the ticket; grade.py carries it through).
2. **The site's own calibrated model is not wired in.** The card runs on nflverse clear rates. When `generate_nfl_data.py` exposes
   per-player probabilities, replace `model_pct` in `build_card_json.py` with the site's number. That is the single biggest upgrade.
3. **Injury/inactive holds** are manual (notes file). nflverse injuries feed exists; a `hold` step could read it.
4. **Single-game correlation** is flagged, not modeled.
5. **Request budget.** The Odds API free plan is 500 requests/month; a full-week pull is ~112. Three pulls a week needs the $30 plan. `--days` limits the pull to the coming slate.

## Do not
- Publish a season win-rate/ROI before 100 graded card legs (the prompts enforce this; keep it).
- Mix personal slips into `cards/`. Personal bets are tracked separately, never graded as the card.
- Let the draft step publish anywhere. It writes a file and an issue; sending is you, in Substack.
