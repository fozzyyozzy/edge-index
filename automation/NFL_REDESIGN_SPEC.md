# NFL side redesign — spec for Claude Code (cfb-app/src, React + Vite, Cloudflare)

## Nav (NFL)
    Card · Legs · Floor Lines · Matchups · Record · FAQ
- **Card** — the plays. Reads `nfl_card_<slate>.json` (tnf | sun | mnf; segmented control). Each ticket: legs with rung, real
  price, L10/L15, last 3, matchup tag; ticket payout, model hit, and the label (`Bloom: +200 target met` or
  `Reduced payout: floors held, not stretched — still recommended`). "Held back" list with reasons. Author notes if present.
  Timestamp line from the fetch: *(Prices as pulled <time>)* at the bottom, italic, parentheses.
- **Legs** — every graded rung + slip builder. `LEGS_TAB_SPEC.md`. Absorbs the old Props tab. Usage (targets/carries/share) is
  a row inside each player's expanded ladder, not its own tab.
- **Floor Lines** — keep as is; it now refreshes from the same pipeline.
- **Matchups** — replaces Usage. `MATCHUPS_TAB_SPEC.md`.
- **Record** — existing, plus the grade-receipts table (A+/A/A−/B hit rates by week) from `receipts/season_ledger.csv`.

## Data pattern
The site injects `const` arrays into JSX between `// AUTO-GENERATED START/END` markers (see `generate_nfl_data.py` inject()).
The card workflow currently copies JSON files to `cfb-app/public/data/`. Either pattern works; **pick one and use it for all
three new tabs.** Simplest: fetch the JSON at runtime (`fetch('/data/nfl_legs_sun.json')`) — no build step, no injection.
Files written by the pipeline each run:
    public/data/nfl_card_<slate>.json      tickets, held, floors_singles, notes
    public/data/nfl_legs_<slate>.json      every player/market/rung graded (see LEGS_TAB_SPEC.md for shape)
    public/data/nfl_matchups.json          defenses x slots + edge_leans (see MATCHUPS_TAB_SPEC.md)

## Team identity
No NFL logos (trademarked; the site is betting-adjacent). Abbreviations in the site's mono font, with the team's primary color
as a left-border accent on rows. A `TEAM_COLORS` map in one file; nothing else.

## Copy rules for every tab (one line under each title)
- Legs: "Grade = how often this rung hits. It says nothing about whether the price is good."
- Matchups: "1 = fewest yards allowed to that position (tough). 32 = most (soft). Blend shown in the corner."
- Card: "Card tickets are graded Tuesday. Personal slips are not the card."
