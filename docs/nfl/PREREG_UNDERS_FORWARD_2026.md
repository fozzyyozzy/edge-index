# NFL Main-Line Unders, Forward Paper Test (rest of 2026): Pre-Registration

> **Status: approved by Tim 2026-10-22. Registered by the commit adding this file to `nfl-verify`,** before any bet in it is recorded.
> **PAPER ONLY. No real money,** whatever the result.
> **Amended 2026-10-23, before any forward data exists (§5):** there is now a single judgment at the end of the 2026 regular season, and FAIL is redefined. Where §5 and §3 conflict, §5 wins.

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

## 5. Amendment 1 (2026-10-23): judgment timing and FAIL rule

**Made before any forward data exists:**
- The capture job (PR `nfl-six-book-capture`) hasn't been merged, and no production capture has run.
- The only capture so far was a one-off smoke test of the script on 2026 week 7 Sunday prices (2026-10-22). Its file was deleted, it was never scored, and it's outside this test, which starts after the merge.

**Why it changed:** the 300-bet judgment couldn't answer the question. See the power note below: at 300 bets the 95% CI is about ±14 points, which can't tell a +2% edge from zero, or from −10%.

**The new rule (replaces §3's judgment; reporting stays as written):**
- **Weekly reports are descriptive only.** No decision, stop or continuation follows from any weekly number.
- **A single judgment** at the **end of the 2026 regular season**, on **all settled bets**, at the best price, using the same game-clustered bootstrap (10,000 resamples, seed 20261021).
  - **PASS:** the 95% CI's lower bound is > 0.
  - **FAIL:** the CI is **entirely below 0** (upper bound < 0).
  - **INCONCLUSIVE:** anything else.
- **The 300-bet trigger and the INSUFFICIENT rule are removed.**

**Power note:** from the 2024 and 2025 closing data, the same bet at the best of the six books.

| | 2024 | 2025 |
|---|---|---|
| Settled bets | 6,395 | 6,904 |
| Bets per game | 23.5 | 25.4 |
| SD of per-bet return | 0.958 | 0.953 |
| Design effect (game-clustered variance ÷ independent-bets variance) | **1.48** | **1.68** |
| Implied within-game correlation | 0.022 | 0.028 |

- **Why the correlation matters:** bets in the same game are correlated (the same player's receptions and yards, game script). So the effective sample is about 1.7× smaller than the bet count.
- **Assumptions below:** SD 0.956, design effect 1.68 (the larger), two-sided α = 0.05, 80% power.

| Settled bets | 95% CI half-width | Smallest edge detectable at 80% power |
|---|---|---|
| 300 (the old trigger) | ±14.0 pts | 20.0 pts |
| 1,000 | ±7.7 pts | 11.0 pts |
| ~4,060 (about 11 remaining weeks at ~370 bets/week) | ±3.8 pts | 5.4 pts |
| ~6,650 (one full season) | ±3.0 pts | 4.3 pts |

**Detecting a +2% edge** at 80% power needs **≈ 30,100 settled bets** (17,900 if bets were independent, × 1.68). That's about **4.5 full seasons** of this bet.

**What to expect:** a real edge of +2% to +4% will most likely end the 2026 season **INCONCLUSIVE.** PASS or FAIL this season needs a true effect of roughly ±5 points or more. That limit is stated now, before any data, so an INCONCLUSIVE result isn't read as support.
