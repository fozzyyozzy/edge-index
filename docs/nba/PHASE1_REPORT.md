# NBA Floor Lines — Phase 1 Report (historical data)

**Date:** 2026-10-21 · **Scope:** Phase 1 of `NBA_FLOORS_BRIEF.md`, with Tim's Phase 0 decisions applied.
**No NFL code, data or schedule was changed.** The one shared-file edit is a single CI line (§8).
**Nothing is committed yet.**

## TL;DR

- **ESPN is the single box-score source** for history and daily use.
  - All three regular seasons are backfilled: 3 × 1,230 games and 97,240 player-game rows, in `data/nba/player_games.parquet`.
  - Every team-season has exactly 82 games. There are no duplicate `(game_id, player_id)` rows.
- **ESPN agrees with nba_api almost exactly:**
  - pts and fg3m are 100% identical.
  - reb is 99.99% identical and ast 99.995%.
  - minutes is 99.78% identical, and 100% within ±1 (ESPN rounds up).
  - **One systematic gap:** ESPN has no athlete record for Lachlan Olbrich (CHI, 2025-26). His 22 played games are missing from ESPN. They're logged, not patched.
- **Pregame DK spread and total** were pulled for all 3,690 games from Odds API historical snapshots. All are verified pregame. Cost: 9,740 credits.
- **Injuries:**
  - The official NBA PDF parser works on real reports and keeps the report timestamp.
  - ESPN fallback and a logged disagreement check are in place.
  - Both are reachable from Actions (Phase 0).
- **Crosswalk:** one ESPN ↔ NBA.com ↔ Odds API table.
  - 802 of 809 historical players have an NBA.com id. The other 7 only ever logged 0-minute games.
  - 143 of 143 Odds API player names from the Phase 0 pulls resolve.
- **Key check:** the GitHub `ODDS_API_KEY` secret is the same key as local. The probe workflows never had the key in their environment.
- **Tests:** 26 NBA tests are added and the full suite passes (236 tests, NFL + NBA).

---

## 1. What was built (all new; nothing in NFL paths)

| Path | Purpose |
|---|---|
| `engine/nba/espn.py` | ESPN scoreboard + box score: fetch, cache, parse. Excludes the NBA Cup final and All-Star games (ESPN files both as regular season). |
| `engine/nba/backfill.py` | Builds `player_games.parquet` and `games.parquet` with context columns. Re-runnable per season, e.g. `--seasons 2026-27` for the current season. |
| `engine/nba/hist_lines.py` | Pregame DK spread/total from Odds API historical snapshots. Has a reserve guard and usage log. |
| `engine/nba/injuries.py` | Official injury-report PDF: index, fetch, parse. ESPN injuries feed and the disagreement report. |
| `engine/nba/crosswalk.py` | Player ID crosswalk and the Odds API name resolver. |
| `engine/nba/crosscheck.py` | One-time ESPN vs nba_api agreement report. |
| `engine/nba/http.py`, `teams.py` | GET with retries (same policy as NFL `common.download`); team codes (NBA.com tricodes everywhere). |
| `automation/tests/nba/` | 26 tests: parser, crosswalk and injury tests on real fixtures, plus the data gate on the committed parquet. |
| `docs/nba/TODO_SHARED_CODE.md` | Decision 5: the golden-test work required before any NFL/NBA code sharing. |

**Data written** (under `data/nba/`). Everything except `raw/` is meant to be committed:

| File | Rows | Notes |
|---|---|---|
| `player_games.parquet` | 97,240 | 1.2 MB. One row per rostered player per game, DNPs kept (`played=False`, `dnp_reason`). |
| `games.parquet` | 3,690 | |
| `lines/pregame_spreads_totals.parquet` | 3,690 | DK home spread, total, snapshot time |
| `lines/odds_usage_nba.csv` | 487 | every paid call, with `x-requests-used/remaining/last` |
| `player_crosswalk.csv`, `rosters_espn.csv` | 883 / 517 | |
| `espn_issues.csv` | 33 | ESPN data defects (§3) |
| `crosscheck_summary.json`, `crosscheck_mismatches.csv` | — | §2 |
| `injuries/official_*.csv`, `espn_*.csv`, `disagree_*.csv` | — | sample run on the 10/21 07:45 AM report |
| `raw/` | — | **gitignored** (34 MB): trimmed ESPN summaries, nba_api logs, injury PDFs, historical snapshots. All re-fetchable. |

**Per-row columns:**
- **Identity:** `game_id, date (ET), season, espn_id, player, position, team, opp, home_away`
- **Box:** `starter, played, dnp_reason, minutes, pts, reb, ast, fg3m, fg3a, pra, pr, pa, ra`
- **Context:** `team_score, opp_score, margin, n_ot, team_games_played` (games before this one), `days_since_prev` (team), `b2b`, `player_days_since_prev`, `team_spread, game_total` (pregame DK)

## 2. ESPN vs nba_api cross-check (Decision 1)

nba_api `LeagueGameLog` was pulled once, locally, for 2023-24 to 2025-26 (79,358 player-game rows). Rows were joined on (NBA.com id via the crosswalk, date).

| | Rows |
|---|---|
| ESPN rows marked played | 79,511 |
| Matched to nba_api | 79,336 |
| ESPN-only | 175: **all 0 minutes with an all-zero line** (sub-minute check-ins nba_api sometimes omits) |
| nba_api-only | 22: **all Lachlan Olbrich**, see §3 |
| Team mismatches on matched rows | 0 |

| Stat | Exact agreement | Within ±1 | Mismatches | Pattern |
|---|---|---|---|---|
| minutes | 99.78% | 100% | 174 | 170 are ESPN +1. ESPN rounds seconds up where stats.nba.com rounds down. |
| pts | **100%** | 100% | 0 | |
| reb | 99.99% | 100% | 8 | ±1, no direction (stat corrections) |
| ast | 99.995% | 100% | 4 | ±1, no direction |
| fg3m | **100%** | 100% | 0 | |

Agreement is the same in each season (minutes 99.76–99.83%; the others ≥ 99.98%). Mismatching rows are in `data/nba/crosscheck_mismatches.csv`.

**Effect on the model:** none worth acting on.
- **Minutes:** the +1 rounding shows up in 0.2% of rows and only in minutes. It will be the same in training and in daily serving, because both use ESPN.
- **Zero-minute rows:** I tried reclassifying ESPN's 0-minute rows as not played. That made agreement *worse*, because nba_api itself keeps about 226 such rows. So ESPN's own `played` flag stays.

## 3. Systematic gap: ESPN is missing one player

ESPN lists Lachlan Olbrich (CHI, 2025-26) in 33 box scores with **no athlete id**: no record, `--` minutes and an all-zero line. nba_api shows he actually played 22 of those games, up to 17 minutes.

- He is not on any current ESPN roster and has no ESPN search result.
- His rows can't be keyed, so they're dropped and logged to `data/nba/espn_issues.csv`.
- Per the single-source decision, they are **not** filled in from nba_api.
- **Visible effect:** in those 22 CHI team-games, box points and minutes don't sum to the final (off by up to 17 minutes).
- **How the data gate handles it:** it allows a mismatch only for team-games listed in `espn_issues.csv`, and fails if that file grows past 3 distinct players.
- **Daily risk:** if ESPN drops a player you'd want to bet, he'd be missing from his own history. The id-less row is logged every run, so it will be visible. Worth a card-QA check in Phase 3.

Nothing else is missing. Every other team-game's box points equal the final score exactly. Minutes sum to 240 + 25 per overtime within ±3 in 99.9% of team-games and within ±5 in all of them. Every team-game has exactly 5 starters.

Data-organic checks (rule 3) pass:
- even-value shares are 40–65% for pts/reb/ast/minutes
- `pra = pts + reb + ast` holds everywhere
- minutes are between 0 and 54
- the season-high 83 points (Bam Adebayo, 2026-03-10) is real; nba_api shows the same line

## 4. Pregame spreads / totals

ESPN has no historical lines (`pickcenter` is empty). They come from Odds API historical snapshots instead (`engine/nba/hist_lines.py`):
- **Snapshot timing:** one snapshot per game date, taken 10 minutes before that date's first tip.
- **Pregame only:** an event is kept only if its tip is after the snapshot. Each game keeps its latest pregame snapshot, because a snapshot also lists later days' games.
- **Coverage:** 3,690 of 3,690 games have a DK spread and a total, and 0 snapshots fall at or after tip (a data-gate test checks this).
- **Timing:** median 74 minutes before tip, max ~11 hours (late games on days with an early tip). These are **pregame, not closing** lines.
- **Spreads:** 15% of team-games carry |spread| ≥ 12, the brief's default blowout threshold.
- **Cost:** 487 snapshots × 20 credits = **9,740 credits**, confirmed by `x-requests-last` = 20 per call. Used went 2,793 → 12,513, and 4,987,487 credits remain.

This spend wasn't explicitly requested. I judged it inside "pregame spread/total if obtainable", and it's 0.2% of quota.

## 5. Injuries (Decision 2)

**Primary: official NBA injury report PDF.**
- It's published every 15 minutes on game days. The parser handles the awkward parts of the PDF:
  - multi-page reports
  - grouped date/time/matchup/team cells
  - reasons that wrap above and below the player's line
  - team-level `NOT YET SUBMITTED` rows, which drift between columns
- `Last, First` names are flipped to "First Last" (suffixes kept) and team names mapped to tricodes. Every row carries `report_time` (ET, from the PDF header) and `source_url`.
- The parser fails loudly on any unknown status or unmapped team.
- Tests run against a committed real report (10/21/26 07:30 AM, 78 rows, 5 pages).
- **Caveat:** game times print as "07:00 (ET)" with no AM/PM. Treat them as PM; the schedule comes from ESPN anyway.

**Fallback: ESPN injuries feed.**
- It's machine-readable and includes ESPN ids, but only says Out or Day-To-Day.
- The disagreement check compares out vs not-out for teams on the official report.
- The 07:45 AM sample had 4 disagreements, all two-way/G League or Doubtful players that ESPN doesn't list. That's expected: ESPN omits G League assignments.

## 6. Player ID crosswalk

`data/nba/player_crosswalk.csv` is keyed on ESPN id. It gives the NBA.com id, the match method, every team the player appeared for (traded players keep one row, e.g. `TOR|IND`), seasons, and first/last game. It also includes the 74 current-roster players with no game yet.

**ESPN ↔ NBA.com:**
- **By name key:** 800 players matched on (date, team, name key). The key ignores accents, case, punctuation and Jr./Sr./II–V suffixes, and normalizes a small nickname list (Nic/Nicolas, Herb/Herbert, Moe/Moritz…).
- **By stat line:** 2 more matched on an exact stat line within the team-game. The line must be distinctive (≥ 5 min) and unique on both sides: Nate/Nathan Mensah, Yongxi Cui/"Cui Cui".
- **Conflicts:** 0. No NBA.com id is used twice.
- **Unmatched:** 7 historical ESPN players. All of them only ever logged 0-minute games, so nba_api has nothing to match.
- An earlier loose stat-line fallback produced 3 wrong matches on 1-minute 0/0/0 lines. It was tightened, and a test pins the behavior.

**Odds API → ESPN:**
- `match_odds_name(name, (home, away))` resolves within the event's two teams first.
- A traded player is then resolved by a unique name league-wide.
- When the name is ambiguous it returns **None rather than guessing** (e.g. two Jalen Williamses, neither in this game).
- Manual fixes go in `data/nba/crosswalk_overrides.csv`; none are needed yet.
- **Real check:** all 143 distinct player names from the 13 Phase 0 DK pulls resolve.

**Tests cover:** suffixes (Jr./III), accents (Jokić, Dončić, Valančiūnas, Bertāns), punctuation (P.J., De'Aaron, Gilgeous-Alexander), nicknames, a traded player (by name and in the NBA.com match), same-name players, statline matching, and overrides.

## 7. Key check and probe logs

**Same key:**
- A throwaway branch (`nba-keycheck`) ran a workflow that read `secrets.ODDS_API_KEY` and printed only:
  - a 12-character SHA-256 prefix
  - the key length
  - the account counters from the free `/events` endpoint
- Local and runner values were identical:
  - prefix `9029fc074b55`
  - length 32
  - `x-requests-used` 2,773 and `x-requests-remaining` 4,997,227 from both, read back to back
- Branch deleted from origin and locally.

**Probe logs never printed the key:**
- The two Phase 0 probe runs (`nba-phase0-probe`) **never referenced any secret**: their workflow had no `secrets.` expression, so the key was never in the runner's environment.
- Their captured stdout files (committed to the throwaway branch, checked from git objects) and the key-check result file were searched for the key value: **not present** in any of the 4 commits.
- GitHub also masks registered secrets in logs.
- **Not checked:** I couldn't download the raw Actions logs. That needs a signed-in GitHub token, and `gh` isn't installed here. Tim can open the runs in the Actions tab to eyeball them.

## 8. Shared-file change (CI only)

`.github/workflows/tests.yml` now also installs `engine/nba/requirements.txt` (pyarrow, pdfplumber, requests). Without this, CI can't read the parquet or run the PDF tests. No NFL code or behavior changes, and the 210 pre-existing tests still pass.

## 9. Decisions recorded for Phase 3 (not built: Phase 1 only)

- **Decision 3:** add the `player_threes` main line to the odds pull (10 credits/game).
- **Decision 4:** morning, pre-lock, and several closing windows for staggered tips, with the pull timestamp stored on every price. At ~210 games/month and about 4–5 pulls per game that's roughly 9–10k credits/month, which still fits the quota.
- **Decision 5:** the fetcher and alt-line math get copied into `engine/nba/` in Phase 3, not shared (see `TODO_SHARED_CODE.md`).

## 10. Housekeeping

- **Credits this phase:** 9,740 (historical lines). The key-check `/events` calls were free.
- **Throwaway branches:** `nba-phase0-probe` and `nba-keycheck` are both deleted.
- **Local installs:** `nba_api` and `pdfplumber` were installed into the local Python for the one-time cross-check and the parser.
- **gitleaks:** not installed on this PC, and nothing was pushed. It must run before the commit is pushed (brief rule).
- **To refresh the current season:** `python -m engine.nba.backfill --seasons 2026-27`. The ESPN cache makes reruns cheap; the daily automation for this is Phase 3.

**Stopping here for Tim.**
