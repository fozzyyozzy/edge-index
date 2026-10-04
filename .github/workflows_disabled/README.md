# Disabled workflows

GitHub Actions only runs files in `.github/workflows/`. Files here are kept for reference and never run.

- `weekly_update.yml` — the original 2025 pick-sheet job (April 2026 setup): Pro Football Reference scraper
  (`scrapers/pfr_scraper.py`) -> `scripts/generate_pick_sheet.py`, committing `data/processed/`, `data/logs/`,
  `outputs/` to main. Hard-coded to the 2025 season, so from January on every run clamped to week 18 and committed
  another "auto: Week 18 data update". Schedule removed 2026-09-24 (it committed outside the `data-main` queue);
  moved here 2026-10-03 so it can't be dispatched either. Nothing in the current pipeline (automation/) reads its
  output. To restore: move it back to `.github/workflows/`.
