# Matchups tab — spec for Claude Code

Reads `public/data/nfl_matchups.json` (written by `pipeline/matchups.py`).

    { meta: { season, week, blend, rank_key, slots: ["QB","RB","WR1","WR2","TE","RUN","PASS"] },
      defenses: [ { team, slots: { QB: { yds_pg, cur_pg, prev_pg, home_pg, away_pg, n_cur, rank }, RB: {...}, ... } } ],
      edge_leans: [ { player, team, opp, home, slot, opp_rank, opp_yds_pg, tag: "SOFT"|"TOUGH", game, day, roof } ] }

## Section 1 — Heat map (the whole tab's reason to exist)
A 32 x 7 grid. Rows = defenses (abbreviation + team-color accent). Columns = QB · RB · WR1 · WR2 · TE · RUN · PASS.
Cell = yards allowed per game to that slot; **cell color = rank** on a diverging scale: rank 1–8 red (tough for the offense),
9–24 neutral/dark, 25–32 green (soft). Number in the cell, rank on hover (or small superscript).
Controls above the grid:
- Sort by column (click a header). Default sort: PASS.
- Toggle **Blend / 2026 only** (uses `yds_pg` vs `cur_pg`; when `cur_pg` is null show "—").
- Toggle **All / Home / Away** (uses `home_pg` / `away_pg` — these are all-season, both years).
- Search team.
Corner text: `meta.blend` (e.g. "75% 2025 / 25% 2026 (2 wks)") so nobody mistakes early-season ranks for settled ones.
Keep it dense — this is meant to read like a spreadsheet, not cards. Sticky header row and sticky team column; horizontal
scroll on mobile inside its own container.

## Section 2 — Edge Leans (this week)
Two lists from `edge_leans`, SOFT first (sorted worst-defense first), then TOUGH.
Row: `Player · slot · TEAM vs/@ OPP · opp rank (yds allowed) · day` with the `roof` shown as a small tag when it is `outdoors`
(weather matters) and hidden for domes. Filter chips: slot, day (Thu/Sun/Mon), Soft/Tough.
One line under the header: "Leans are matchup only. A soft matchup with no volume is not a floor — check the Legs tab."
Each row links to the player in the Legs tab (`#legs?player=<name>`) when that player has graded rungs.

## Out of scope for v1
Scheme labels (man/zone, blitz rate) — those come from the author's notes until there is a data source.
