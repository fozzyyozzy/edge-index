# CFB Phase 1 Report: Data Foundation

Pulled 2026-10-10 (2026 season in progress: PBP through week 5; week 6 is underway).
Brief: `docs/CFB_PHASE1_BRIEF.md`.

## Top line

- **Hard checks: all pass.** 0 duplicate primary keys in every table; spread sign
  convention verified on 18,609 line rows (0 disagreements); 100% PBP coverage of
  completed FBS-involved games in finished weeks; no `/plays` response looks capped.
- **API calls: 167 of the 600 cap** (dry-run ceiling was 164; +3 because 2025 lists
  extra postseason "weeks" 13-14 and 2023 lists weeks 11-15 for lower-division playoffs;
  four of those came back empty). A second `pull` run costs **0 calls**.
- **Things to know before Phase 2** (details below):
  1. DraftKings has no lines at all in 2021-2022. Bovada is the only provider with
     opening spreads in every season.
  2. 0.22% of FBS scrimmage plays are exact repeats in CFBD's feed under new `play_id`s.
     They are kept and flagged `is_duplicate`. Filter them before aggregating PPA.
  3. 5.0% of FBS games have PBP running scores that disagree with the official final
     (missing last scoring play, scoring credited to the wrong team). **Take results
     and margins from `games`, never from PBP.**
  4. Weather is a Patreon-only endpoint. Skipped; the `--datasets weather` hook stays in.

## Commands

```
python -m engine.cfb.pull --seasons 2021-2026 --dry-run   # estimate, 0 calls
python -m engine.cfb.pull --seasons 2021-2026             # pull what's not cached
python -m engine.cfb.pull --seasons 2026 --datasets plays --weeks 6 --refresh
python -m engine.cfb.build_tables                          # raw -> clean parquet, 0 calls
python -m engine.cfb.validate                              # checks -> this report's AUTO section
python -m engine.cfb.update_week [--dry-run]               # in-season incremental
```

Every live request is logged to `data/cfb/_meta/api_calls.csv` (timestamp, dataset,
endpoint, params, status, rows, cache file). The client refuses to call past the cap
(default 600, `--cap`). A full pull estimated above 400 calls refuses to run without `--confirm`.

## What was pulled (raw rows from the API, by season)

| dataset | endpoint | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| games | `/games?seasonType=both` | 2,454 | 3,705 | 3,734 | 3,801 | 3,831 | 3,679 |
| plays | `/plays` per (seasonType, week) | 158,498 | 252,262 | 254,088 | 277,044 | 293,383 | 123,870 |
| lines | `/lines?seasonType=both` | 887 | 1,463 | 1,416 | 1,573 | 1,597 | 1,187 |
| advanced | `/stats/game/advanced` | 1,774 | 2,918 | 2,984 | 3,212 | 3,316 | 1,428 |
| ppa_games | `/ppa/games` | 1,657 | 1,672 | 1,702 | 1,711 | 1,742 | 685 |
| returning | `/player/returning` | 128 | 130 | 131 | 133 | 134 | 136 |
| talent | `/talent` | 224 | 233 | 238 | 134 | 134 | 138 |
| recruiting | `/recruiting/teams` | 191 | 184 | 177 | 194 | 232 | 221 |
| sp | `/ratings/sp` | 131 | 132 | 134 | 135 | 137 | 139 |
| fpi | `/ratings/fpi` | 130 | 131 | 133 | 134 | 136 | 138 |
| elo | `/ratings/elo` | 130 | 131 | 133 | 134 | 136 | 138 |
| coaches | `/coaches?year=` | 152 | 146 | 143 | 152 | 161 | 138 |
| portal | `/player/portal` | 1,770 | 2,273 | 2,502 | 3,378 | 4,499 | 4,474 |
| venues | `/venues` (once) | 852 total | | | | | |
| weather | `/games/weather` | **skipped: requires Patreon** (per v2 spec) | | | | | |

Postseason PBP is included: all FBS bowls and CFP games are CFBD postseason week 1
(`raw/plays/<season>_post_wk01.json`). The 2021 responses are smaller because CFBD
returns fewer lower-division games/plays for 2021. FBS-involved coverage is the same.

**API calls:** 167 / 600 (games 6, lines 6, advanced 6, ppa_games 6, returning 6,
talent 6, recruiting 6, sp 6, fpi 6, elo 6, coaches 6, portal 6, venues 1, plays 94).

**Weekly in-season update (`update_week.py`): ~5 calls.** It refreshes 2026 games,
lines (includes the upcoming week's lines), advanced and ppa_games (4 calls), plus 1 per
newly finished week of PBP. Files under 6 hours old are not re-fetched, so a second run
the same day is 0 calls. The hard limit is 10 per run. Not scheduled.

## Clean tables (`data/cfb/clean/`)

| table | rows | key | notes |
|---|---|---|---|
| games | 21,204 | game_id | all divisions; flags below |
| lines | 18,632 | game_id + provider | long format, every provider |
| plays | 1,359,145 | play_id | 65.5 MB, **gitignored** (over the ~50 MB limit); rebuild with build_tables |
| game_team_stats | 15,634 | game_id + team | `adv_*` from /stats/game/advanced, `ppa_*` from /ppa/games |
| team_season | 802 | season + team_id | FBS teams only: priors + coach + portal |
| benchmarks | 808 | season + team | SP+/FPI/Elo: **benchmarks only, not model inputs** |
| venues | 852 | venue_id | |

`data/cfb/raw/` (945 MB) is gitignored via `data/cfb/.gitignore`. The root `.gitignore`
is unchanged.

**Lines convention.** `spread`, `spread_open` and `games.consensus_close_spread` are
from the **home team's perspective: negative = home favored**, exactly as CFBD returns
them. Checked against `formatted_spread` on every parseable row: 0 of 18,609 disagree.
Example: 2026 wk2 Florida A&M @ Miami, consensus -59.5, final 77-7.

**Column notes**
- `games`: `kickoff_utc` (UTC); `kickoff_local_hour` (venue tz; null for TBD kickoffs or
  unknown tz, which covers only 7 non-TBD FBS games); `neutral_site` (explicit, never
  inferred); `both_fbs`, `fbs_vs_fcs`, `fbs_involved`; `is_postseason`; `is_bowl`
  (postseason FBS-vs-FBS, **includes CFP games**); `is_cfp`, `cfp_round`; `bowl_name`;
  `margin_home`; `consensus_close_spread` (median of every provider's spread, **completed
  games only**); `n_spread_providers`; `home/away_pregame_elo` (CFBD's own).
  Non-CFP bowls, where opt-outs bite, are `is_bowl & ~is_cfp`.
- `lines`: `spread, spread_open, total, total_open, home_ml, away_ml, formatted_spread`
  per provider. For upcoming 2026 games, `spread` is the current line, not a close.
- `plays`: `offense_id`/`defense_id` (matched to the game's home/away IDs, 0 unmatched);
  `play_type_group` in rush / pass / special / penalty / other (full mapping in the
  validation section); `is_scrimmage` = rush + pass + fumble plays; `is_garbage_time` =
  **null, Phase 2 defines it**; `is_duplicate` (see above); `ppa`; `season/week/season_type`
  taken from the request (the API omits them); `clock_minutes/clock_seconds`.
- `team_season`: `talent`; `recruiting_rank/points`; `ret_*` returning production;
  `coach`, `coach_first_year`, `coach_first_year_source`, `n_head_coaches` (>1 = mid-season
  change); `portal_in/portal_out` (name match on origin/destination).

## Endpoints unavailable or shaped differently

- `/games/weather`: Patreon-only. Skipped.
- `/plays` needs `year` + `week` (no season-wide pull). There's one call per (seasonType, week).
  It returns no season/week fields, and no team IDs (names only).
- Talent, recruiting, returning, SP+, FPI and Elo are keyed by **team name only**.
  They're joined to CFBD team IDs through the games table. Every FBS name matched; the only
  unmatched row is SP+'s `nationalAverages` pseudo-team.
- `/coaches?year=Y` returns only season Y for each coach, so career history isn't
  available from one call (affects the first-year flag; see below).
- `/ratings/elo` without `week` returns one end-of-season (or current, for 2026) value.
- `/talent` covers about 225 teams through 2023 and FBS only from 2024.

## Judgment calls

1. **Postseason PBP** is pulled for every postseason week CFBD lists. Lower-division
   playoff weeks cost 7 extra calls (2023 post wk11-15, 2025 post wk13-14; 4 empty). This is cheap and keeps the plan simple.
2. **Finished-week rule**: a week's PBP is pulled once its last kickoff is 12+ hours old.
   2026 week 6 (in progress) has 12 completed midweek FBS games. Their PBP waits for
   `update_week`, and validation excludes them from coverage.
3. **Duplicate plays are flagged, not dropped**, so every raw row stays. Key: same game,
   period, clock, down, distance, yards-to-goal and text (scrimmage plays only).
4. **`consensus_close_spread` = median of every provider row**, including CFBD's
   `consensus`/`teamrankings` aggregates (2021-23), and null for games not yet played.
5. **`coach_first_year`**: primary coach = most games that season. First year = a
   different primary coach than the prior season. For 2021 (no 2020 pulled) it falls
   back to a hire date within the 12 months before Sept 1 (`coach_first_year_source`).
   Interim coaches count as a change (e.g. 2025 Oklahoma State: Meacham).
6. **FBS game-count range** in validation was widened from 750-900 to 750-950. Actual
   counts are 910-934 for 2023-25, from real FBS growth to 134-136 teams.
7. **Venue timezones**: CFBD supplies 364 of 852. For 373 more, the timezone comes from
   the state, but only for single-timezone states. Split-timezone states are left null.
8. **Not reused**: the legacy `data/cfbd_cache/` (2022-25 regular-season games/lines)
   was not reused. It would have saved about 8 calls but mixed two cache layouts.
9. **Benchmarks are end-of-season values** (current values for 2026). They contain
   postseason information, so they're for comparison only and never walk-forward inputs.

## Open questions for Tim

1. **Line-movement design (Phase 4):** opening spreads exist for Bovada in every season,
   for DK only from 2023, and for ESPN Bet in 2024-25. Should 2021-22 line movement be
   Bovada-only, or should Phase 4 start in 2023?
2. **Bowls:** `is_bowl` and `is_cfp` are flagged. Should opt-outs exclude all non-CFP
   bowls from training, or only some?
3. **Benchmarks walk-forward:** do you want weekly Elo/SP+ snapshots for a fair in-season
   comparison? Elo takes a `week` param (about 16 calls/season); SP+ is only end-of-season.
4. **Committed parquet:** the small clean tables (about 6 MB) are committed and
   `plays.parquet` is not. Weekly updates will rewrite the committed files. Should
   all of `clean/` be gitignored instead?
5. **2026 week 6 PBP:** run `python -m engine.cfb.update_week` tomorrow (about 5 calls)?

## Validation results

<!-- AUTO:BEGIN -->
_Generated by `python -m engine.cfb.validate` at 2026-10-10 09:22._

**Hard-check failures:** none  
**Warnings:** 
- DraftKings absent in 2021
- DraftKings absent in 2022
- 2/25 sampled games: PBP score != final

### 1. Games per season
| season | total | completed | fbs_involved | both_fbs | fbs_vs_fcs | bowls | cfp | neutral |
|---|---|---|---|---|---|---|---|---|
| 2021 | 2454 | 2454 | 887 | 770 | 117 | 38 | 3 | 68 |
| 2022 | 3705 | 3705 | 896 | 776 | 120 | 42 | 3 | 135 |
| 2023 | 3734 | 3724 | 910 | 792 | 118 | 42 | 3 | 148 |
| 2024 | 3801 | 3799 | 920 | 799 | 121 | 46 | 11 | 194 |
| 2025 | 3831 | 3831 | 934 | 808 | 126 | 46 | 11 | 130 |
| 2026 | 3679 | 1672 | 888 | 761 | 127 | 0 | 0 | 37 |


### 2. Play-by-play coverage and truncation checks
Scope: completed FBS-involved games in weeks that are over (12 completed games in the in-progress week excluded; update_week.py picks them up).

| season | completed_fbs_games | with_plays | median_plays | p05_plays | under_100 | pct_with_plays |
|---|---|---|---|---|---|---|
| 2021 | 887 | 887 | 179.0 | 152.0 | 5 | 100.0 |
| 2022 | 896 | 896 | 178.0 | 152.0 | 7 | 100.0 |
| 2023 | 910 | 910 | 174.0 | 150.0 | 1 | 100.0 |
| 2024 | 919 | 919 | 176.0 | 152.0 | 3 | 100.0 |
| 2025 | 934 | 934 | 177.0 | 151.0 | 0 | 100.0 |
| 2026 | 390 | 390 | 175.0 | 154.0 | 0 | 100.0 |

Games with < 100 plays: 16
| game_id | season | week | home_team | away_team | n_plays | max_period |
|---|---|---|---|---|---|---|
| 401643737 | 2024 | 8 | Utah State | New Mexico | 40 | 1 |
| 401282051 | 2021 | 1 | Florida International | Long Island University | 45 | 4 |
| 401309543 | 2021 | 1 | Toledo | Norfolk State | 53 | 4 |
| 401282178 | 2021 | 1 | UTEP | Bethune-Cookman | 65 | 4 |
| 401404104 | 2022 | 10 | Oklahoma | Baylor | 78 | 4 |
| 401282612 | 2021 | 1 | Pittsburgh | Massachusetts | 81 | 3 |
| 401415237 | 2022 | 7 | UNLV | Air Force | 81 | 4 |
| 401416627 | 2022 | 8 | Miami (OH) | Western Michigan | 82 | 4 |
| 401426609 | 2022 | 12 | UTEP | Florida International | 85 | 4 |
| 401426615 | 2022 | 13 | Florida Atlantic | Western Kentucky | 87 | 5 |
| 401525832 | 2023 | 2 | TCU | Nicholls | 87 | 4 |
| 401416645 | 2022 | 12 | Central Michigan | Western Michigan | 96 | 4 |
| 401628324 | 2024 | 1 | Kentucky | Southern Miss | 97 | 3 |
| 401301000 | 2021 | 2 | Tulane | Morgan State | 97 | 3 |
| 401634301 | 2024 | 1 | California | UC Davis | 98 | 3 |
| 401403982 | 2022 | 2 | Utah | Southern Utah | 99 | 4 |

Completed FBS-vs-FBS games with NO plays: 0
Per-week /plays responses checked: 90; row counts range 147-35,773 (none round: True); FBS plays/game per week ranges 140-192. Flagged weeks (round count, any FBS game missing, >1 FBS game ending before Q4, or <150 FBS plays/game):
| season | season_type | week | rows | games_in_response | fbs_games | fbs_with_plays | fbs_plays_per_game | fbs_before_q4 | fbs_missing | round_count |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | regular | 15 | 147 | 1 | 1.0 | 1.0 | 147.0 | 0.0 | 0.0 | False |
| 2024 | regular | 1 | 22356 | 133 | 100.0 | 100.0 | 172.4 | 2.0 | 0.0 | False |
| 2024 | regular | 16 | 799 | 5 | 1.0 | 1.0 | 146.0 | 0.0 | 0.0 | False |
| 2025 | regular | 16 | 825 | 5 | 1.0 | 1.0 | 140.0 | 0.0 | 0.0 | False |

FBS-involved games whose PBP ends before Q4 (weather-shortened or CFBD feed gap): 5
| game_id | season | week | home_team | away_team | n_plays | max_period |
|---|---|---|---|---|---|---|
| 401282612 | 2021 | 1 | Pittsburgh | Massachusetts | 81 | 3 |
| 401301000 | 2021 | 2 | Tulane | Morgan State | 97 | 3 |
| 401634301 | 2024 | 1 | California | UC Davis | 98 | 3 |
| 401628324 | 2024 | 1 | Kentucky | Southern Miss | 97 | 3 |
| 401643737 | 2024 | 8 | Utah State | New Mexico | 40 | 1 |

Our scrimmage plays / CFBD advanced offense plays per team-game (n=15,604): median 1.000, p05 0.963, p95 1.014. Team-games below 0.8: 21
Duplicate scrimmage plays in the CFBD feed (same game, clock, down, distance, spot, text; new play_id), FBS-involved games: 1,450 of 655,229 (0.22%) in 503 games. Kept, flagged `is_duplicate`.

### 3. PPA coverage (scrimmage plays)
| season | scrimmage | with_ppa | pct_ppa |
|---|---|---|---|
| 2021 | 119860 | 119567 | 99.8 |
| 2022 | 191429 | 190877 | 99.7 |
| 2023 | 193272 | 192898 | 99.8 |
| 2024 | 208920 | 208217 | 99.7 |
| 2025 | 218473 | 218029 | 99.8 |
| 2026 | 91670 | 91136 | 99.4 |

<details><summary>play_type -> play_type_group mapping</summary>

| play_type_group | play_type | n |
|---|---|---|
| other | Timeout | 57717 |
| other | End Period | 17817 |
| other | Fumble Recovery (Own) | 6514 |
| other | End of Game | 5983 |
| other | End of Half | 5418 |
| other | Fumble Recovery (Opponent) | 5027 |
| other | Pass Completion | 1579 |
| other | Uncategorized | 1003 |
| other | Fumble Return Touchdown | 463 |
| other | End of Regulation | 323 |
| other | Fumble | 237 |
| other | placeholder | 41 |
| pass | Pass Reception | 257795 |
| pass | Pass Incompletion | 173719 |
| pass | Sack | 28466 |
| pass | Passing Touchdown | 23919 |
| pass | Pass Interception Return | 5656 |
| pass | Interception | 5613 |
| pass | Interception Return Touchdown | 1174 |
| pass | Pass | 3 |
| penalty | Penalty | 69637 |
| rush | Rush | 490860 |
| rush | Rushing Touchdown | 24415 |
| special | Punt | 65493 |
| special | Kickoff | 63896 |
| special | Kickoff Return (Offense) | 19042 |
| special | Field Goal Good | 16507 |
| special | Field Goal Missed | 5279 |
| special | Punt Return | 3295 |
| special | Blocked Field Goal | 582 |
| special | Blocked Punt | 479 |
| special | Safety | 391 |
| special | Kickoff Return Touchdown | 325 |
| special | Punt Return Touchdown | 172 |
| special | Blocked Punt Touchdown | 132 |
| special | Missed Field Goal Return | 51 |
| special | Blocked Field Goal Touchdown | 40 |
| special | Defensive 2pt Conversion | 35 |
| special | Two Point Pass | 33 |
| special | Two Point Rush | 13 |
| special | Missed Field Goal Return Touchdown | 1 |

</details>

### 4. Lines coverage (completed FBS-involved games)
| season | games | pct_close | pct_open |
|---|---|---|---|
| 2021 | 887 | 100.0 | 99.0 |
| 2022 | 896 | 99.6 | 91.3 |
| 2023 | 910 | 99.7 | 93.3 |
| 2024 | 919 | 98.4 | 93.7 |
| 2025 | 934 | 100.0 | 100.0 |
| 2026 | 402 | 100.0 | 100.0 |

**Season x provider: % of completed FBS-involved games with a close / open spread**

| provider | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| Bovada | 99 / 99 | 92 / 91 | 91 / 91 | 87 / 87 | 100 / 100 | 98 / 98 |
| DraftKings | - | - | 83 / 83 | 88 / 78 | 86 / 73 | 100 / 98 |
| William Hill (New Jersey) | 97 / 0 | 97 / 0 | 62 / 0 | - | - | - |
| ESPN Bet | - | - | 32 / 0 | 97 / 89 | 94 / 94 | - |
| consensus | 98 / 0 | 98 / 0 | 3 / 0 | - | - | - |
| teamrankings | 87 / 0 | 85 / 0 | 6 / 0 | - | - | - |
| numberfire | 16 / 0 | - | - | - | - | - |
| Caesars Sportsbook (Colorado) | 0 / 0 | 1 / 0 | 3 / 0 | - | - | - |
| Caesars (Pennsylvania) | 2 / 0 | - | - | - | - | - |

Sign convention (spread is home-perspective, negative = home favored): 18,609 rows parseable from formatted_spread, 0 disagree.
Example: 2026 wk2 Florida A&M @ Miami: consensus -59.5 (home favored), final 77.0-7.0.

### 5. Final scores vs PBP (random 25 completed games)
Matches: 23/25. PBP score = highest running score in the plays (CFBD play scores are post-play).
| game_id | season | home_team | away_team | home_points | away_points | home_score | away_score | match |
|---|---|---|---|---|---|---|---|---|
| 401309569 | 2021 | Central Michigan | Toledo | 26.0 | 23.0 | 23 | 23 | False |
| 401520445 | 2023 | Army | Navy | 17.0 | 11.0 | 9 | 17 | False |

All completed FBS-involved games with PBP: 248 of 4936 (5.0%) disagree with the final score.

### 6. Spread sanity (completed FBS-vs-FBS, consensus close)
| season | games | fav_cover_pct | avg_ats_miss |
|---|---|---|---|
| 2021 | 769.0 | 51.1 | 12.5 |
| 2022 | 773.0 | 47.1 | 12.0 |
| 2023 | 789.0 | 49.2 | 12.1 |
| 2024 | 798.0 | 49.0 | 12.1 |
| 2025 | 808.0 | 50.6 | 11.8 |
| 2026 | 283.0 | 52.2 | 11.4 |

DraftKings close only:

| season | games | fav_cover_pct | avg_ats_miss |
|---|---|---|---|
| 2023 | 727.0 | 50.2 | 12.1 |
| 2024 | 786.0 | 49.7 | 12.1 |
| 2025 | 761.0 | 51.0 | 11.8 |
| 2026 | 283.0 | 52.2 | 11.5 |


### 7. Primary keys and joins
| table | rows | key | duplicates |
|---|---|---|---|
| games | 21204 | game_id | 0 |
| lines | 18632 | game_id+provider | 0 |
| plays | 1359145 | play_id | 0 |
| game_team_stats | 15634 | game_id+team | 0 |
| team_season | 802 | season+team_id | 0 |
| benchmarks | 808 | season+team | 0 |
| venues | 852 | venue_id | 0 |

| check | count |
|---|---|
| plays.offense_id null | 0 |
| plays.defense_id null | 0 |
| benchmarks.team_id null (name not in games) | 6 |
| team_season talent null | 2 |
| team_season recruiting null | 1 |
| team_season returning null | 10 |
| team_season coach null | 0 |
| games kickoff_local_hour null (tz unknown or TBD) | 2381 |
| lines game_id not in games | 0 |

Benchmark names not matched to a team_id: nationalAverages

### 8. API calls (ledger)
| dataset | calls |
|---|---|
| games | 6 |
| elo | 6 |
| portal | 6 |
| ppa_games | 6 |
| recruiting | 6 |
| returning | 6 |
| lines | 6 |
| sp | 6 |
| fpi | 6 |
| coaches | 6 |
| venues | 1 |
| advanced | 6 |
| talent | 6 |
| plays | 94 |

Total: 167 / cap 600

<!-- AUTO:END -->
