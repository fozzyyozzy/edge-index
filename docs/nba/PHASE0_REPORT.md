# NBA Floor Lines — Phase 0 Report (recon & plumbing)

**Date:** 2026-10-20 (opening night) · **Scope:** Phase 0 of `NBA_FLOORS_BRIEF.md` only.
Nothing was built. No NFL code, workflow, data, or schedule was changed.

## TL;DR — three things Tim needs to know

1. **`cdn.nba.com` is blocked from everywhere we tried.** It returned 403 (Akamai "Access Denied") from both Tim's PC and a GitHub Actions runner. `www.nba.com` returned 403 too. The brief's planned daily box-score source doesn't work.
   - **ESPN's public JSON API works from both places.** Its box scores carry MIN/PTS/REB/AST/3PT plus a starter flag. I propose it as the daily source.
2. **`stats.nba.com` (nba_api) works from Tim's PC and times out from Actions**, as the brief predicted. That's fine for the one-time historical backfill. It can't be on the daily path.
3. **Real Odds API cost is 9 credits per game** for the 9 requested markets (DraftKings, one region). A full 11-game slate cost **99 credits**.
   - At ~210 games/month, that's **~1,900 credits/month per daily pull**.
   - The local `ODDS_API_KEY` reports **~4.997M credits remaining** (2,761 used this period). That's far above the 500/month free plan the brief assumed, so quota is very likely not a constraint. Tim should confirm the GitHub secret is the same key.

---

## 1. Connectivity matrix

Probe scripts were run on Tim's PC (residential ISP) and on an `ubuntu-latest` GitHub Actions runner. The runner probe ran from a throwaway branch `nba-phase0-probe` (deleted afterward; see §5). Timeout was 30s unless noted.

| Endpoint | Tim's PC | Actions runner | Notes |
|---|---|---|---|
| `nba_api` `LeagueGameLog` 2025-26 (stats.nba.com) | ✅ 2.6s, 26,651 player-game rows | ❌ read timeout (30s) | |
| `nba_api` `BoxScoreTraditionalV3` (stats.nba.com) | ✅ 0.2s | ❌ read timeout (30s) | |
| `nba_api` `LeagueGameLog`, 90s timeout | — | ❌ read timeout (90s) | Not slow — silently dropped. Datacenter IPs are blocked. |
| raw `stats.nba.com/stats/scoreboardv2` + browser headers | ❌ timeout | ❌ timeout | My hand-rolled headers don't satisfy it locally either. `nba_api`'s headers do. Ignore this row. |
| `nba_api.live` ScoreBoard (cdn.nba.com) | ❌ 403 | ❌ 403 | |
| `cdn.nba.com` todaysScoreboard / scheduleLeagueV2 / boxscore | ❌ 403 | ❌ 403 | Akamai "Access Denied", with or without browser UA/Referer/Origin |
| `www.nba.com` | ❌ 403 | — | |
| ESPN `site.api.espn.com` scoreboard (by date) | ✅ | ✅ | 15 games on 2026-04-10 |
| ESPN `summary?event=` box score | ✅ | ✅ | Labels: MIN, PTS, FG, 3PT, FT, REB, AST, TO, STL, BLK, OREB, DREB, PF, +/-; `starter` flag; DNPs listed |
| `official.nba.com` injury-report index page | ✅ 60 PDF links | ✅ 60 PDF links | |
| Official injury PDF (`ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMPM.pdf`) | ✅ 85 KB PDF | ✅ 85 KB PDF | Published several times a day (latest seen: 02:45 PM ET). Needs PDF table parsing. |
| ESPN injuries JSON | ✅ 27 teams / 94 entries | ✅ same | Machine-readable fallback; less authoritative than the official report |

**What this means for the design** (the constraint is that daily automation must not depend on Tim's PC):

- **Historical backfill (Phase 1):** one-time local `nba_api` run on Tim's PC, cached to `data/nba/raw/`. Works today.
- **Daily logs/grading (Phase 3):** ESPN box scores from Actions (confirmed working there). Cross-check ESPN against nba_api on the backfill seasons before trusting it, by matching per-player pts/reb/ast/3pm/minutes on a sample of games. Player-ID mapping ESPN↔NBA is needed; join on name + team + date, with a manual override table, like `norm_name` in NFL.
- **Injuries:** primary is the official NBA injury PDF (reachable from Actions; needs `pdfplumber`-style table parsing and a QA check on the row count). ESPN injuries JSON is the fallback. The official report carries Out/Doubtful/Questionable/Probable/Available, which maps directly onto the brief's availability hold.
- **No working source found for:** historical alt-ladder prices. The Odds API's historical endpoint could provide them at a much higher per-call cost; I did not test or price it. Per the brief, the market-blend evaluation is forward-only unless Tim wants that priced.

## 2. Odds API — real credit cost

Pulled `GET /v4/sports/basketball_nba/events/{id}/odds?regions=us&bookmakers=draftkings&oddsFormat=american` with all 9 markets. Pregame only: the event start was checked before each call, and the Celtics@Pistons game starting at 19:10Z was **not** pulled.

| Pull | Events | `x-requests-last` per event | Total credits | `x-requests-used` before → after |
|---|---|---|---|---|
| Tonight (76ers@Knicks, OKC@Spurs) | 2 | 9 | 18 | 2,644 → 2,662 |
| **Full slate, Wed 2026-10-21 ET** | **11** | **9** | **99** | 2,662 → 2,761 |

The events list (`/events`) is free (`x-requests-last: 0`). Cost is markets returned × regions, so 9 markets × 1 = 9 per game. All 9 markets came back for all 13 games, including tomorrow's slate pulled ~28h early.

**Market availability (DraftKings, 13 games):**

| Market | Sides | Players / game | Max rungs / player | Alt rungs priced −150…−500 |
|---|---|---|---|---|
| `player_points` | Over/Under | 10.8 | 1 line | — |
| `player_rebounds` | Over/Under | 10.5 | 1 line | — |
| `player_assists` | Over/Under | 8.1 | 1 line | — |
| `player_points_rebounds_assists` | Over/Under | 8.5 | 1 line | — |
| `player_points_alternate` | **Over only** | 11.0 | 9 | 251 |
| `player_rebounds_alternate` | **Over only** | 10.8 | 15 | 224 |
| `player_assists_alternate` | **Over only** | 8.4 | 12 | 118 |
| `player_points_rebounds_assists_alternate` | **Over only** | 8.5 | 10 | 129 |
| `player_threes_alternate` | **Over only** | 9.7 | 7 | 113 |

All 5 alt ladders exist on DK and are Over-only, as expected. The main two-way markets are present for de-vig. Alt prices span roughly −4,700 to +3,000, so the −150…−500 floor band is well populated (835 rungs across 13 games).

**Gap:** there is no main `player_threes` market in the request. Threes would have no two-way line to de-vig against. Adding `player_threes` costs +1 credit/game. Recommended if threes stays as a shadow market.

**Monthly projection.** The 2026-27 regular season is 1,230 games over ~177 days, about 7 games/night or ~210 games/month.

| Pulls per game | Credits/game | Credits/month |
|---|---|---|
| 1 (morning card) | 9 (10 with `player_threes`) | ~1,900 (~2,100) |
| 2 (+ pre-lock reprice) | 18–20 | ~3,800–4,200 |
| 3 (+ near-tip close for CLV) | 27–30 | ~5,700–6,300 |

The closing pull could request only the markets that hold card or shadow legs, which cuts cost proportionally. The pre-lock injury recheck itself needs no odds credits.

**Quota.** The local key shows `x-requests-remaining` 4,997,239 after these pulls, which implies a plan of about 5M/month. That's consistent with `engine/cfb/lines/capture.py`'s 100,000-credit "NFL reserve" guard. If the GitHub secret is the same key, NBA's ~2–6k/month is under 0.2% of quota and **no tier change is needed**. Tim should confirm, since the brief assumed the 500/month free plan. No markets were cut.

One guard to add when building: NFL's `fetch_lines.py` enforces `ODDS_WEEKLY_BUDGET` from its own `automation/lines/odds_usage.csv`. NBA pulls won't appear there, so NBA needs its own budget/reserve guard, modeled on CFB's `capture.py`, which reads `x-requests-used`/`remaining`.

## 3. Reuse map (NFL → NBA)

Key: **A** = import as-is · **B** = generalize with a small parameter · **C** = copy and adapt into `engine/nba/` · **D** = not relevant.

| File | Class | What carries over | What's NFL-specific |
|---|---|---|---|
| `engine/core/odds.py` | **A** | de-vig, EV, Kelly (¼, 2% cap), parlay prob/decimal | nothing |
| `engine/parlay.py` | **A** | `Leg` (has `sport`), `daily_card`, correlation haircuts | nothing (not used by the floors pipeline today) |
| `automation/pipeline/common.py` | **A** for the helpers, **B** for `SOURCES` | `download()` retries (3 tries, 5s/15s backoff, no retry on 4xx, key redacted), `novig`, `blend_prob`/`leg_prob`/`price_fields`, `norm_name` | `SOURCES["The Odds API"]` hard-codes `americanfootball_nfl`; nflverse sources; `COL`; week-keyed `grading_history`; `tag_rank` (32 teams) |
| `automation/pipeline/altline_engine.py` (`scraper/` has a byte-identical copy) | **B** | `implied_prob`, `Dist`, `parlay`, `pick_win_rung` (`MAX_LEG_JUICE=-400`) | market sets, sigma/sd tables, `DK_RUNGS`, receptions-Poisson special case. An NBA market would silently fall to a normal with sd 4.5, so it needs an NBA table. |
| `automation/pipeline/fetch_lines.py` | **C** | Over-only ladder parsing (`rung = point + 0.5`), two-way pull for de-vig, usage logging | `MARKETS`, tnf/sun/mnf slates, `in_week` via nflverse kickoffs, week-based budget and file names |
| `automation/pipeline/build_card_json.py` | **B** for `build_tickets`, **C** for `main` | R1–R11 ticket construction (pure function) | `SINGLE_GAME={tnf,mnf,snf}`; R5 checks `pass_att`/`pass_cmps` when favored by 7+; Thursday snapshot; `week` in paths |
| `automation/pipeline/card_qa.py` | **B** | R1–R11 checks, issue-on-fail flow | own copy of `SINGLE_GAME`, `GRADE_OK`, `FLOOR_STAR`; R5 is attempt-prop specific |
| `automation/pipeline/grade_legs.py` | **B** for `grade_rung`/`trim_ladders`, **C** for `main` | rung grading A+–F, ladder trimming, re-blend | WR/TE positions, `NEAR`, target competition |
| `automation/pipeline/grade.py` | **C** | `settle`, `clv_pts`, `dec` | nflverse weekly settlement; week-keyed ledger |
| `automation/pipeline/floors.py` | **C** (logic only) | floor-scan loop | nflverse schedule, NFL volume stats, L10/L15 rule |
| `automation/pipeline/refresh_odds.py` | **C** | `refresh_card`, `flag_new_markets` | hard-coded Tue–Mon NFL week schedule |
| `engine/collector.py` | **B** | already takes a sport arg; `MARKETS` per sport | `_nfl_week` ledger; no retries |
| `engine/cfb/lines/capture.py` | template | logs `x-requests-used`/`remaining`, reserve guard | CFB-specific |

**Test coverage caveat.** Golden fixtures (`automation/tests/make_fixtures.py`, 6 cases) protect only `build_card_json.py` and `card_qa.py`. Other modules have partial unit tests. Those cover `common.download`, `grade_legs.grade_rung`/`trim_ladders`, `settle`, and `price_check`. **Not covered:** `fetch_lines.py`, `floors.py`, `grade_legs.main`, `refresh_odds.py`, and all of `engine/`. A shared-code refactor of those wouldn't be caught by CI.

**Existing NBA references:** none in code. There's the `ROADMAP.md` "November (NBA)" note and a comment in `engine/core/tracking.py:30`.

## 4. Proposed layout

Default from the brief, adjusted to how the repo is actually organized:

```
engine/nba/                 # NBA-only code (copy-and-adapt, class C)
  sources.py                #   ESPN box/schedule, official injury PDF parser, nba_api backfill (local only)
  fetch_lines.py            #   Odds API pull: date-keyed slates, own budget/reserve guard
  ladder.py                 #   NBA market/sigma/rung table for altline_engine-style pricing
  model.py, floors.py, grade.py, build_card.py, card_qa.py
data/nba/
  raw/                      #   nba_api backfill cache (parquet), ESPN daily JSON
  lines/  daily/  graded/
docs/nba/                   #   brief, PREREG.md, phase reports, weekly/
.github/workflows/nba_morning.yml, nba_prelock.yml, nba_grade.yml
automation/tests/nba/       #   picked up by the existing tests.yml (it runs on every push)
```

- **Import only class-A code** (`engine/core/odds.py`, the pure helpers in `automation/pipeline/common.py`). Leave every NFL file untouched in the NBA build.
- **Defer class-B generalizations** (sport key in `common.SOURCES`, per-sport tables in `altline_engine.py`, `SINGLE_GAME` in `build_tickets`/`card_qa`). Each would be its own PR with the golden tests passing. Since golden tests don't cover `altline_engine`'s tables or `fetch_lines`, those two should stay copied, not shared, for now.
- **Date-keyed, not week-keyed.** NBA slates are ET dates. Every NFL "week" concept becomes `YYYY-MM-DD`.
- **Workflows need their own concurrency group, or the shared commit-to-main group.** The NFL jobs commit to main under a shared concurrency group (`sun-snapshot.yml`). NBA jobs that commit data must join it to avoid push races.

## 5. Housekeeping from this phase

- **Throwaway branch.** `nba-phase0-probe` was pushed with a single push-triggered workflow (no secrets used) that committed its results to the branch. It also triggered the read-only `tests.yml`. The branch has been deleted from origin and locally; nothing was merged to main.
- **Odds API spend for this phase:** 117 credits (18 + 99).
- **Raw responses** (13 events) are saved locally, outside the repo, in the session scratchpad. They weren't committed, because Phase 1 hasn't defined `data/nba/` yet.

## 6. Decisions for Tim before Phase 1

1. Approve **ESPN** as the daily box-score source, with an nba_api cross-check on backfill seasons, and the **official injury PDF** (ESPN fallback) for availability.
2. Confirm the GitHub `ODDS_API_KEY` secret is the ~5M-credit key, so no tier change is needed.
3. Add `player_threes` (+1 credit/game) so threes can be de-vigged?
4. Approve the layout above: NBA code copied, NFL untouched, and shared-code refactors as separate PRs.
