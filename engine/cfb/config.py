"""CFB Phase 1 config: seasons, paths, API call cap."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "cfb"
RAW = DATA / "raw"
CLEAN = DATA / "clean"
META = DATA / "_meta"
LEDGER = META / "api_calls.csv"
REPORT = ROOT / "docs" / "cfb" / "PHASE1_REPORT.md"
ENV_FILE = ROOT / ".env"

BASE_URL = "https://api.collegefootballdata.com"
SEASONS = list(range(2021, 2027))     # 2020 skipped (COVID schedules)
CURRENT_SEASON = 2026                 # in progress: only completed weeks get PBP

CALL_CAP = 600          # hard stop: total ledger calls for this phase
CONFIRM_ABOVE = 400     # full pull refuses without --confirm above this estimate

# A week counts as completed once its last kickoff is this many hours old.
WEEK_DONE_HOURS = 12

# Upper-bound PBP weeks per season, used by --dry-run before games are cached.
EST_REGULAR_WEEKS = 16
EST_POSTSEASON_WEEKS = 1
