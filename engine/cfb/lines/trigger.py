"""Trigger the cfb-lines workflow from a Windows scheduled task (Tim, 2026-10-19).

    python -m engine.cfb.lines.trigger --slot tue10       # what each scheduled task runs
    python -m engine.cfb.lines.trigger --test             # free no-op: dispatches a --dry-run capture

GitHub's own crons ran 2-6 h late all of week 7, so every slot was skipped. Each Windows task
(registered by agent/register_cfb_slot_tasks.ps1, wake-to-run) calls the workflow's
workflow_dispatch `slot` input at the slot time; the workflow tags the capture with the intended
slot and its real lag and marks it served, so the GitHub crons (kept as backup) then skip it.

Token: a fine-grained GitHub token scoped to THIS repo only, permission Actions: read & write.
Read from env CFB_GH_TOKEN or %USERPROFILE%\\.edge-index\\gh_actions_token.txt (outside the repo;
never committed, never printed). Each call is logged to %USERPROFILE%\\.edge-index\\trigger.log.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "fozzyyozzy/edge-index"
WORKFLOW = "cfb_lines.yml"
HOME = Path(os.environ.get("USERPROFILE") or Path.home()) / ".edge-index"
TOKEN_FILE = HOME / "gh_actions_token.txt"
LOG = HOME / "trigger.log"


def token() -> str:
    t = os.environ.get("CFB_GH_TOKEN", "").strip()
    if not t and TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not t:
        sys.exit(f"no token: put a fine-grained token (this repo only, Actions read/write) in {TOKEN_FILE}")
    return t


def log(msg: str) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def dispatch(inputs: dict) -> int:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
        data=json.dumps({"ref": "main", "inputs": inputs}).encode(),
        headers={"Authorization": f"Bearer {token()}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "edge-index-cfb-trigger"},
        method="POST")
    try:
        status = urllib.request.urlopen(req, timeout=30).status
    except urllib.error.HTTPError as e:
        status = e.code
    log(f"dispatch {inputs} -> HTTP {status}")
    return status


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slot", help="slot name from engine/cfb/lines/slots.py, e.g. tue10")
    g.add_argument("--test", action="store_true", help="free no-op: a --dry-run capture (0 credits)")
    a = ap.parse_args(argv)
    inputs = ({"slot": "", "args": "--label manual --ladders none --dry-run"} if a.test else {"slot": a.slot})
    status = dispatch(inputs)
    print(f"dispatch {inputs} -> HTTP {status}")
    return 0 if status == 204 else 1


if __name__ == "__main__":
    raise SystemExit(main())
