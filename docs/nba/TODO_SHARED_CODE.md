# TODO: extend golden tests before sharing any NFL code with NBA

**Decision (Tim, 2026-10-21):** NBA copies the NFL line fetcher (`automation/pipeline/fetch_lines.py`) and `automation/pipeline/altline_engine.py` into `engine/nba/`. It does not import or generalize them.

**Why:** the NFL golden-card fixtures (`automation/tests/make_fixtures.py`, 6 cases) cover only `build_card_json.py` and `card_qa.py`. Changes to the following would not be caught by CI:
- the fetcher
- `altline_engine`'s market, sigma and rung tables (only `estimate_ladder` reaches the golden output, via `odds_model_est`)
- `floors.py`
- `grade_legs.main`
- `refresh_odds.py`

## Before any future refactor that shares code between NFL and NBA

Do these in their own PR, with NFL behavior unchanged:

- [ ] **`fetch_lines.py`:** add a golden test from a recorded Odds API response (`/events` and `/events/{id}/odds` JSON saved as fixtures). It should assert:
  - ladder rows (rung = point + 0.5, Over only)
  - two-way rows
  - main-line selection
  - the usage-log row
- [ ] **`altline_engine.py`:** add snapshot tests for `estimate_ladder`, `fit_market_dist`, `pick_win_rung` and `parlay` across every market key in `YARD_MARKETS`/`COUNT_MARKETS`. This pins the sigma/sd tables and `DK_RUNGS`.
- [ ] **`common.py`:** add a test pinning `SOURCES["The Odds API"]` so it resolves to `americanfootball_nfl` for NFL callers. That's the first thing a sport parameter would touch.
- [ ] **`floors.py` / `grade_legs.main`:** add an offline fixture run, using nflverse extracts like `make_fixtures.py --extract`, so floor and grade output is pinned.
- [ ] Only then: move a shared piece to a sport-agnostic module. Keep NFL golden output byte-identical (`python automation/tests/make_fixtures.py --expected` shows no diff).

**Copies to keep in sync by hand until then:** `engine/nba/` versions of the fetcher and the alt-line math. They're added in Phase 3, when the daily pipeline is built. Each copied file names its NFL origin in its docstring.
