# Edge Index — NBA Floor Lines: Build Brief for Claude Code

**Repo:** `C:\Users\tyose\edge-index\` (github.com/fozzyyozzy/edge-index)
**Owner:** Tim · **Written:** 2026-10-20 (NBA opening night)
**Status:** PAPER ONLY. No public card, no stake, until the Phase 4 bars pass.

---

## 0. What we're building, and what we're carrying over from NFL

"Floor bets" here means the same thing as the NFL Floor Lines page: the **alt-line over rung a player clears most of the time**, priced roughly -150 to -500. It's the target-60–88%-calibrated-probability band, aiming near 75%. Those legs then get stacked into 3–4-leg cross-game tickets, using the existing card rules and the Bloom +200 target.

**Lessons from the NFL season that must be built in from day one, not retrofitted:**

1. **Market-blend the probability.** The NFL finding was that the model's probability ran hotter than DraftKings'. Legs where the model "beat" the price hit *below* implied. The NBA probability must be a blend of model and de-vigged market from the start, with the blend weight a tunable parameter and shadow variants logged.
2. **Grade-first leg selection, not price-first.** Pick the rung for clear rate, then check price.
3. **Hard holds beat clever adjustments.** For example, Team2025 ≠ current team was a hard REVIEW hold. The NBA equivalents are in Phase 3.
4. **Pre-register the bars before looking at results.** Write them to `docs/nba/PREREG.md` and commit *before* any backtest output is read.
5. **Tests + QA gate on every push.** Extend the existing `tests.yml` and Card QA gate rather than building a parallel system.
6. **Real data only.** No synthetic actuals anywhere. Every graded leg must trace to a real box score.

---

## Phase 0 — Recon & plumbing check (do this first, report back, don't build yet)

1. **Inventory reusable NFL pieces** and report which can be generalized vs. copied:
   - `scraper/altline_engine.py` (DK ladder pricing, win-mode, parlay math)
   - `fetch_lines.py` (The Odds API ladder fetch)
   - `floors.py`, `build_card_json.py` (rules R1–R7), `grade.py`
   - the Card QA gate in `card.yml`, `tests.yml`, golden-card tests
   - Propose a layout. Default: `engine/nba/`, `data/nba/`, `.github/workflows/nba_*.yml`. Shared code should move to a sport-agnostic module only if that's low-risk; don't break NFL.
2. **Connectivity test — critical.** `stats.nba.com` (what `nba_api` hits) is widely reported to block datacenter/cloud IPs and to use bot protection. That means it will likely fail from GitHub Actions. Test explicitly:
   - `nba_api` call from Tim's PC (expected: works)
   - same call from a GitHub Actions runner (expected: fails or times out)
   - `cdn.nba.com` live endpoints (scoreboard, box score) from Actions (reported to work from anywhere)
   - Report results. **Design constraint: daily automation must not depend on Tim's PC being awake** (it sleeps while he's at work).
3. **Odds API check.** Confirm DK returns NBA alternate ladders for these markets via `/events/{eventId}/odds`:
   `player_points_alternate`, `player_rebounds_alternate`, `player_assists_alternate`, `player_points_rebounds_assists_alternate`, `player_threes_alternate`
   Also confirm the main `player_points`, `player_rebounds`, `player_assists` and `player_points_rebounds_assists` markets. Main lines are needed for the de-vig, since alt ladders are usually over-only.
   - Log the `x-requests-used` / `x-requests-remaining` headers for one full-slate pull and **report the real per-slate credit cost**.
   - Rough expectation: NBA has a slate almost every night. That likely means 1,000+ credits/month on top of NFL usage, which is far past the 500/month free plan. Tim decides on the paid tier; don't silently cut markets to fit.

**Deliverable:** `docs/nba/PHASE0_REPORT.md`, covering the reuse map, connectivity matrix, real credit cost per slate, and proposed layout. Stop and wait for Tim.

---

## Phase 1 — Historical data

**Seasons:** 2023-24, 2024-25, 2025-26 regular season. Add 2026-27 as it's played.

**Per player-game row:**
- `game_id, date, season, player_id, player, team, opp, home_away, starter, minutes`
- `pts, reb, ast, fg3m, pra` (+ `pr, pa, ra` cheaply)
- Context: `rest_days`, `b2b` flag, `team_games_played`, final margin (for blowout study), and pregame spread/total if obtainable.

**Sourcing:**
- Historical backfill can be a **one-time local run** with `nba_api` on Tim's PC (rate-limited, cached to `data/nba/raw/`, committed as parquet).
- Ongoing daily logs must come from a source that works in Actions. Use the `cdn.nba.com` box scores, or another source verified in Phase 0. Don't build the daily path on `stats.nba.com`.
- **Injury/availability:** find a machine-readable source for the official NBA injury report and verify it's reachable from Actions. Report what's available.

**Tests:** row counts per team-season are ~82 games; no duplicate `(game_id, player_id)`; minutes sum per team-game ≈ 240 (265 for OT).

---

## Phase 2 — Floor model & backtest

### Model structure (keep it simple; volume first)
NFL found volume was the input that mattered most. In the NBA, **minutes is the volume**.

- **P(clear rung) = P(stat ≥ rung)**, built from:
  1. **Minutes projection.** Recency-weighted recent minutes, with starter/bench role, B2B, and blowout risk from the spread.
  2. **Per-minute rate** for each stat (recency-weighted, shrunk toward the player's longer baseline).
  3. **Distribution.** Fit the right count distribution per market (e.g., Poisson or negative binomial for reb/ast/threes; something with appropriate variance for points/PRA). Validate the choice on held-out data; don't assume it.
- **Matchup (opponent pace, opponent allowed-by-position) is a test, not a default.** Add it only if it improves held-out calibration. That's the same standard that rejected implied team totals on NFL.
- **Market blend:** `p_final = w * p_model + (1 - w) * p_market_devig`. Report results for several `w` values. No `w` is "the" setting until Phase 4 forward data picks it.

### Backtest
- Train on 2023-24 + 2024-25; hold out **2025-26** entirely.
- For every player-game-market, evaluate rungs in the floor band and score calibration with:
  - reliability table by 5-pt probability bins (the "Does 80% mean 80%?" panel, for NBA)
  - calibration slope
  - Brier score vs. a **naive baseline**: last-N-game clear rate at the same rung
- If historical alt-ladder prices aren't available, say so plainly. The market-blend evaluation then happens forward-only in Phase 4. **Do not estimate historical prices and present them as real.**

### Pre-registration (commit `docs/nba/PREREG.md` BEFORE running the holdout)
Proposed bars. Tim may edit before commit:
- Calibration slope on holdout within **0.90–1.10**
- In the 70–90% bins, |predicted − actual| ≤ **3 pts** for each bin with n ≥ 300
- Brier beats the naive clear-rate baseline
- No single market more than 5 pts hot in the 75%+ bins (any market that fails is dropped, not tuned on the holdout)

**Deliverable:** `docs/nba/PHASE2_RESULTS.md` with the reliability table per market, which markets pass, and which fail and get dropped. Stop and wait for Tim.

---

## Phase 3 — Daily pipeline (paper)

### Daily flow (GitHub Actions, no dependency on Tim's PC)
1. **Morning (~11:00 ET):** schedule + injuries, then fetch DK ladders (only the markets that passed Phase 2), then score every rung, apply holds, assign grades, write `data/nba/daily/YYYY-MM-DD.json`.
2. **Pre-lock recheck (~60–90 min before the first tip):** re-pull the injury report and flag/hold any leg whose status changed. NBA availability news breaks late; this step matters more than in NFL.
3. **Overnight grade (~03:00 ET):** grade every logged rung (card *and* held/shadow) from real box scores and append to `data/nba/graded/`.

### Hard holds (REVIEW, not on card)
- **Availability:** any player listed questionable/doubtful/GTD, or on a minutes restriction.
- **Role change:** new team, or a starter↔bench change, since the data window. This is the NBA version of Team2025 ≠ current team. It matters early this season with major offseason moves (e.g., the 76ers adding James and Brown).
- **Thin sample:** fewer than N games in the current role (default N = 8, matching the NFL min).
- **Rest risk:** second night of a B2B for players with a history of resting on B2Bs.
- **Blowout risk:** spread ≥ a threshold (default 12) gets a minutes haircut in the projection, and a hold if the leg's clear probability depends on full minutes. Tune the threshold on 2025-26 data and report it.
- **Teammate return/absence:** a key teammate returning or newly out changes usage. Flag it in v1 (review), and model it later only if data supports it.

### Grading & card
- Grade every rung A+ through F on calibrated clear probability, same scale as the NFL Legs plan.
- The floor rung is the deepest rung meeting the probability floor and priced +EV or at worst market. Show MAX PRICE (longest price still worth taking).
- Ticket builder reuses rules R1–R7 and the existing QA gate: 3–4 legs, 2–3 tickets per slate, no shared legs across tickets except a designated floor star, Bloom +200 target with "reduced payout, floors held" labeling.
- **NBA same-game correlation: needs a decision from Tim** (see §5). Blowouts cut minutes for starters on *both* teams, so same-game floor legs likely fail together. Measure this on 2025-26 (joint vs. independent clear rates for same-game leg pairs) and report it. Don't add a rule on your own.
- Log **shadow cards** for each blend weight `w`, as done for NFL.

### Site
- New tab group "NBA (2026-27 · Paper)" with **Floor Lines** (daily) and **Record**. Match the existing NFL components and styling. Use team abbreviations/colors only, no logos.
- NBA Record is its own clean record, separate from NFL.

---

## Phase 4 — Forward test & go/no-go

- Paper card runs daily. Everything is graded in public-ready format but not published.
- **Pre-registered forward bars** (commit before the forward test starts):
  - ≥ **150 graded card legs** before any public record claim (NBA volume makes this reachable in weeks, not months)
  - Forward calibration slope 0.90–1.10; 70–90% bins within ±4 pts
  - Card legs' hit rate ≥ the de-vigged implied probability of their prices (otherwise the model isn't beating the market, however good calibration looks)
  - CLV tracked on every leg (price at publish vs. closing price, de-vigged)
- Weekly auto-report `docs/nba/weekly/` comparing the live blend vs. shadow blends.
- Go-public decision is Tim's, made against these bars, not on a hot week.

---

## 5. Decisions Tim owns (defaults in brackets)

1. **Markets in v1** [points, rebounds, assists, PRA; threes as shadow-only]
2. **Odds API tier**, after Phase 0 reports real credit cost [upgrade if NBA + NFL > 500/mo]
3. **Same-game legs on NBA tickets** [allowed, max 2 per game per ticket, pending the Phase 3 correlation study]
4. **Blowout threshold** [spread ≥ 12, tuned in Phase 3]
5. **Newsletter:** fold NBA into The Edge Index later, or keep it site-only during paper [site-only until bars pass]

---

## Working rules for Claude Code
- Work phase by phase. **Stop at the end of each phase** with the report file and wait for Tim.
- Don't modify NFL behavior. Any shared-code refactor gets its own PR, with NFL golden-card tests passing.
- Secrets via GitHub Actions secrets only (`ODDS_API_KEY` exists). Run gitleaks before pushing.
- Retries/fallbacks on every external download, matching the NFL reliability work.
- Never fabricate data, prices, or results. If something isn't available, say so in the report.
