# Lines

Default: `fetch_lines.py` pulls every DK alternate-line rung from The Odds API (secret `ODDS_API_KEY`).
Outputs: `ladders_<season>_w<week>.csv` (every rung, real price) and `dk_<season>_w<week>_<slate>.csv` (main lines).

Fallback (no key or API down): paste DK pages into `raw/w<week>/<market>.txt` and run `parse_lines.py` — see the
comments at the top of that file. The estimator prices the ladder when only main lines are available.
