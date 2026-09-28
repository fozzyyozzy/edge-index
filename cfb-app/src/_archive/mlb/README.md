# MLB — paused until 2027

Taken off the public site on 2026-09-28. Nothing here is imported, so Vite neither builds nor serves it.

- `KBoard.jsx`, `MLBHub.jsx` (Full Card), `RecordTracker.jsx` (MLB Record) — the three MLB tabs.
- `data/daily_card.json`, `data/record.json` — the MLB data they fetched from `/data/` (moved out of `public/` so the
  URLs no longer resolve).

To bring MLB back:
1. Move the three components back to `cfb-app/src/` and the two JSON files back to `cfb-app/public/data/`.
2. Re-add the MLB section to `NAV_SECTIONS` in `cfb-app/src/App.jsx` (see git history for commit "Pause MLB until 2027").
3. Restore the MLB routine step in `agent/daily_publish.bat`.

`backtest/mlb/morning_routine.py` still writes to the original paths (`cfb-app/src/MLBHub.jsx`,
`cfb-app/src/RecordTracker.jsx`, `cfb-app/public/data/`), so move the files back before running it again.
