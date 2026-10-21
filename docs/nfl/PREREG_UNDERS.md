# NFL Main-Line Unders at Best Available Price: Pre-Registration

> **Status: approved by Tim 2026-10-21.**
> - Book list and line rule were chosen by Tim (2026-10-21) after seeing the free 2025 recompute.
> - Registered by the commit adding this file to `nfl-verify`, **before any 2024 price is pulled.**
> - **Order:** this commit → 2024 pull (cap 12,000 credits, 100k reserve guard) → the 2024 test **once** (marker file).

## 0. Hypothesis and why 2024

- **Hypothesis:** straight bets on **receptions and rec_yds main-line Unders**, at the best available price among the books Tim can use, have positive flat return.
- **Where it came from:** it was **found after looking at 2025** (`MAIN_LINES_CHECK.md`). 2025 is therefore *not* evidence: it is the discovery sample.
- **The test:** **2024 is the independent test.** Its prices have not been pulled or looked at in any form. The 2024 `prop_lines` rows in `backtest/nfl/edge_index.db` hold FanDuel receptions alts and DK yardage alts with no timestamps, and are not used.

## 1. The bet

| Item | Definition |
|---|---|
| **Books (frozen)** | DraftKings, FanDuel, BetMGM, Caesars (`williamhill_us`), Fanatics, BetRivers (Maryland-licensed; **no offshore books**) |
| Markets | `player_receptions`, `player_reception_yds`: main (two-way) lines only |
| Side | **Under** |
| Unit | One bet per player-game-market |
| **Line** | DK's main line when DK posts one. Otherwise the most common line among the listed books, with ties going to the **lower** line. |
| **Price** | The best (highest-paying) Under price among listed books **at that line** |
| Stake | Flat 1u, straight bets |
| Price time | **Close:** the Odds API historical snapshot at kickoff − 10 min, `regions=us` (it returns ~kickoff − 14 min on the 5-minute grid) |
| Settlement | nflverse weekly stats. Under wins if stat < line; push (refund, return 0) if equal; a player who didn't play is VOID (excluded, counted); an unmatched player is UNGRADEABLE (excluded, counted). |
| Scope | Regular season only |

## 2. Primary test: 2024 regular season (registered)

- **Metric:** flat ROI at the **best listed price**, pooled across both markets.
- **CI:** a 95% bootstrap CI clustered by game (10,000 resamples, seed 20261021).
- **PASS** if the CI's lower bound is **> 0**. **FAIL** otherwise.
- **Also reported (non-gating):**
  - per-market ROI
  - **DK-only:** DK's own Under price at DK's line, on lines DK posts
  - hit rate
  - average price and implied probability
  - books at the line
  - which book supplied the best price
  - season halves (weeks 1–9 / 10–18)
- **Sample size:** expect ~5,000–7,000 bets. A real edge of about +3% is detectable at that size. If 2024 has fewer than 2,000 settled bets, the verdict is **INSUFFICIENT**.

## 3. Forward rule (2026)

- **The bet:** the same bet, priced at the **live pipeline's publish-time snapshot**. That's the pull `build_card_json.py` publishes from (`lines/pulled_<season>_w<week>_<slate>.txt`), across **all listed books**.
- **Capture gap:** the live pipeline pulls **DraftKings only** today. Pricing at all listed books needs a publish-time capture with `regions=us`, at ~20 credits per game per pull (receptions + rec_yds mains). It's **not built here.** Building it means a pipeline change (its own PR) and Tim's approval.
- **Until then:** forward bets are priced **DK-only** and labeled so.
- **Reporting:** weekly; bet count, ROI, CI.
- **Judged once, at 300 settled bets** (both markets, from the first forward week with capture):
  - **PASS:** the ROI CI's lower bound is > 0.
  - **FAIL:** the point estimate is ≤ 0.
  - **INCONCLUSIVE:** the point estimate is > 0 but the CI spans 0. That outcome goes to Tim's decision, not an automatic extension.
- **No tuning:** nothing about the bet (books, line rule, markets, side) changes between 2024 and the forward test.

## 4. Descriptive only (reported, not gating)

- **2026 weeks 3–6, DK-only:**
  - **Prices:** the live pipeline's committed two-way pulls (`automation/lines/twoway_2026_w*.csv`), the last pregame DK pull per game.
  - **Bets:** the same Under bet, DK price at DK's line.
  - **Settlement:** from nflverse.
  - **Cost:** zero credits.
- **2-leg Under parlays (2024 and 2025):**
  - **Pairs:** every cross-game pair of that season's qualifying Under legs within the same week. No same-game pairs.
  - **Pricing:** both legs at the **same listed book**: the single book with the highest combined decimal price for that pair, at the legs' reference lines.
  - **Settlement:** a void leg drops the pair to a single at that book; a push leg likewise.
  - **Reported:** win rate (both legs win) vs the product of the legs' hit rates; flat ROI per pair; and the same legs as **straight** bets at each leg's best listed price, for comparison. The CI is a bootstrap over weeks, since pairs share legs.
  - These are many overlapping pairs, so this describes the average pair, not a bettable card.

## 5. Integrity

- **Order:** the bet definition, books, line rule and pass rule are fixed here, before 2024 data exists locally.
- **Once only:** the 2024 test runs once (marker file). A crash before results are written is logged and re-run; the first completed run stands.
- **Slices are hypotheses:** any slice of 2024 found after looking (team, week, line range) is a hypothesis only (CLAUDE.md rule 5).
- **Limits are not modeled:** account limits and bet-size caps on props aren't modeled. A pass says the prices were beatable on paper, not that the volume can be bet.
