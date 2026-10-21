"""Paths for the NBA tests; importing it puts the repo root on sys.path so engine.nba imports."""
import os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FIX = os.path.join(REPO, "automation", "tests", "fixtures", "nba")
if REPO not in sys.path:
    sys.path.insert(0, REPO)
