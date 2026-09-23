# Edge Index — sports betting analytics (edge-index.com)

Model-driven prop/spread picks with an audited public record. Owner: Tim.
Product thesis: 2-3 play daily cards built on receptions alt-ladder floors,
matchup-gated, graded publicly with CLV. Sell transparency, never win%.

## Layout
- `engine/` — v2 (current, leak-free). core/odds.py is the single source of
  truth for de-vig/EV/Kelly. nfl/ has props engine, backtests, floor/matchup
  studies. collector.py snapshots pregame odds (The Odds API).
- `backtest/` — v1 legacy. mlb/ pipeline is LIVE (morning_routine.py runs
  daily). nfl/ + nfl_fixed/ are near-duplicate legacy; superseded by engine/.
- `cfb-app/` — React/Vite site, deploys to Cloudflare Pages.
- `agent/` — Windows .bat entry points (scheduled): daily_publish.bat
  (routine -> npm build -> wrangler deploy; ORDER MATTERS), collect_odds.bat.
- `models/` — v1 model files, reference only.
- `ROADMAP.md` — READ THIS: all validated findings + product plan.

## Commands
- Publish site: `agent\daily_publish.bat` (never deploy dist without
  `npm run build` first — src/RecordTracker.jsx is auto-injected by the
  morning routine, dist goes stale silently)
- Odds snapshots: `python engine\collector.py --sport americanfootball_nfl`
  (add `--ladders` to view alt ladders)
- Data gate after any reseed: `python engine\nfl\verify_data.py`
- NFL studies: `python engine\nfl\floor_study.py`, `matchup_study.py`,
  `backtest.py`, `alt_backtest.py`
- Reseed NFL logs: `python backtest\nfl\nflverse_loader.py`
- Env: ODDS_API_KEY (The Odds API), CFBD_API_KEY (CFBD, free)

## Hard-won data rules (violations produced fake +15-78% ROI in the past)
1. PREGAME ONLY. Never store/pull odds for games already started. The 2025
   prop_lines rows in backtest/nfl/edge_index.db are contaminated with live
   in-game snapshots — never backtest against them (2024 lines are clean).
2. NO SELF-REFERENTIAL LINES. Never estimate a line from a player's average
   and then grade a strategy against that same line (v1's 97% tier bug).
3. VERIFY DATA IS ORGANIC. Synthetic seeds happened before (2025 game_logs
   were 96.7% even values). Run verify_data.py after any load; playoffs mean
   up to 21-22 weeks/player is normal.
4. Walk-forward only: a week's projection may use only games strictly before
   it. De-vig two-way markets before calling anything an edge.
5. Never trust a backtest slice found after looking (report it as hypothesis).

## Validated findings (real 2023-25 data; regenerate via the study scripts)
- Receptions alt floors at 0.6x expectation: 88.4% true (fair -762); books
  hang -175/-300 -> THE core edge. At 0.5x: 92.3% (fair -1195).
- Yardage alt floors are efficiently priced (0.6x rec_yds: 67%, fair -203).
  Only playable with a matchup case.
- Streaks add ~nothing beyond trailing average. Card copy only, never selection.
- Matchup gates: high-blitz DCs BOOST WR/TE receptions floors (91.5%/89.7%)
  and CRUSH RB rush floors (66.3%). Slot corner quality moves WR yardage
  (74% weak vs 66% elite). DC tiers: Bowen/Schwartz/Babich tough;
  Spagnuolo/Austin/Woods soft. Source: NFL_Coaches_Schemes_2024_2026.csv
  (Tim maintains; 'LA' Rams code mismatch drops Rams from joins — open bug).
- MLB: strikeout props +6.6% ROI on live record; hits props were -6.6% at
  -174 avg juice (cut). CFB spreads: ratings models do NOT clear the vig
  (tested 4 seasons, open+close, with/without SP+) — newsletter content only,
  no CFB spread picks.
- Card rules: max 2-3 plays/parlays via engine/parlay.py daily_card();
  negative-correlation legs blocked; flat 1u or quarter-Kelly capped 2%.

## Known issues / next build
- Card generator: join floor fair-prices x collector live ladders x matchup
  gates -> daily card + Floor Board page for the site (chip-row UX).
- mlb_umpire.py crashes daily in morning routine (line ~437, unfixed).
- nflverse legacy player_stats.csv is frozen at 2024; loader tops up per-season
  (stats_player_week_YYYY.csv). New schema: passing_interceptions, NaN-heavy
  (use the _i() helper pattern).
- Repo hygiene: stray shell-artifact files (`#`, `0.05`, `npm`, `findstr`),
  MLBHub.jsx exists in 3 places, backtest/nfl vs nfl_fixed need consolidation.
