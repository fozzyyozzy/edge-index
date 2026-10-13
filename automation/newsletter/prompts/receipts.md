Write the RECEIPTS issue for last week from the JSON below.

Structure:
## The record — legs graded, hits, hit rate, average model % vs. actual rate (say whether the model ran hot or cold and by how much), flat 1u P&L. Ticket record W-L-Void with each ticket's misses named.
## What missed — every miss in a table: Player | Rung | Actual | Missed by | Reason. Reason must be one of: yard-short (≤3), read-wrong, game-script, injury/void. Use `opp_d`/`own_vol`/`note` to decide.
## Does 80% mean 80% — the `by_bucket` table and one sentence on calibration.
## Price check — `est_vs_real` table with the difference; one sentence on whether estimates ran generous or tight.
## The whole board — `board_by_grade`: every row on the Legs board (one per player/market at its best rung, holds included), hits–misses by grade for last week. One sentence on whether the letters sorted the board (higher grades hitting more often).
## Sunday prices — `sunday_price_moves`: each Sunday card leg's Thursday price, published price and closing price, with the move Thursday → published and published → close in implied-probability points (positive = the price shortened). Say "no Thursday price" where there isn't one. One sentence on whether waiting for Friday helped or cost us.
## What we held back — `held_by_reason`: legs the card held, graded anyway, by hold reason. A leg with several reasons counts under each. One sentence per reason only where the sample says something; say plainly when a sample is too small.
## What changed — only the entries in `changelog` (MODEL_CHANGELOG.md entries dated in the last 7 days), each quoted
verbatim as a Markdown blockquote ("> ..."), lines copied exactly, optionally after a line "From the model changelog
(YYYY-MM-DD):". Nothing else in this section: no commentary, no proposals. If `changelog` is empty, write exactly
"Nothing changed this week."
Then the closing line.

DATA:
{{DATA}}
