# NFL Main-Line Unders, Forward Paper Test (rest of 2026): Pre-Registration

> **Status: approved by Tim 2026-10-22. Registered by the commit adding this file to `nfl-verify`,** before any bet in it is recorded.
> **PAPER ONLY. No real money,** whatever the result.

## 0. This is a new test, not a rescue

- **The earlier result stands:** the registered 2024 test of this bet **FAILED** (`UNDERS_RESULTS.md`: +1.46%, CI −1.42 to +4.32). This forward test doesn't change, re-score or reinterpret that verdict.
- **What this asks:** does the same bet, priced the way it would actually be placed (at the card's publish time, best of six books), show positive return on fresh 2026 data?
- **Its own verdict:** it's judged on its own sample. Its verdict is reported next to the 2024 FAIL, never in place of it.

## 1. Data

- **Prices:** the six-book capture, `automation/pipeline/capture_books.py` (PR `nfl-six-book-capture`).
  - It runs in `card.yml` right after a card passes QA, so its timestamp is the card's publish time.
  - Each run writes `automation/lines/books/books_<season>_w<week>_<slate>_<stamp>.csv` with every book's main-line Over/Under prices.
  - **If a game has more than one capture** (e.g. a manual card rebuild), the **earliest** capture for that game is used.
- **Books (frozen):** DraftKings, FanDuel, BetMGM, Caesars (`williamhill_us`), Fanatics, BetRivers.
  - A book that posts no main line for a player simply isn't a candidate. In the first live capture (2026 week 7 Sunday), Caesars posted alt ladders only and Fanatics posted few mains.
- **Start:** the first slate captured after the PR is merged. Every slate after that is in.
- **End:** the last 2026 regular-season game.
- **Outcomes:** nflverse weekly stats, as in every NFL verification here.

## 2. The bet (same definition as `PREREG_UNDERS.md` §1)

| Item | Definition |
|---|---|
| Markets | receptions, rec_yds: **main** (two-way) lines |
| Side | **Under** |
| Universe | every player-market with a main line in the capture, across all captured games (not just card legs) |
| Unit | one bet per player-game-market |
| Line | DK's main line in the capture. Otherwise the most common line among the six books, with ties going to the lower line. |
| Price | the best Under price among the six books at that line, in that capture |
| Stake | flat 1u, straight, **paper** |
| Settlement | Under wins if stat < line; push = 0; didn't play = VOID (excluded, counted); unmatched name = UNGRADEABLE (excluded, counted) |

## 3. Reporting and the single judgment

- **Weekly (non-binding):** cumulative bets, hit rate, flat ROI, a game-clustered 95% CI, and the same bet at **DK's price only**, for comparison.
- **The judgment happens once:** after the first week in which cumulative settled bets reach **300**. It covers every bet settled through that week, at the best price.
  - **PASS:** the CI's lower bound is > 0.
  - **FAIL:** the point estimate is ≤ 0.
  - **INCONCLUSIVE:** a positive point estimate with a CI that spans 0. That outcome goes to Tim's decision, not an automatic extension.
- **INSUFFICIENT:** the 2026 regular season ends before 300 settled bets.
- **CI method:** game-clustered bootstrap, 10,000 resamples, seed 20261021.
- **No mid-test changes:** nothing about the bet (books, line rule, markets, side, timing) changes during the test. Slices found while watching are hypotheses only (CLAUDE.md rule 5).

## 4. What a PASS would and wouldn't mean

- **It would:** show the publish-time, best-of-six Under price beat the outcomes on 2026 data.
- **It wouldn't:** overturn the 2024 FAIL. It wouldn't authorize real-money use either, which stays a separate decision for Tim. And it says nothing about account limits on props.
