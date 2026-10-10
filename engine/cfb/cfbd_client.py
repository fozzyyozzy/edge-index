"""CFBD v2 client: bearer auth, disk cache, call ledger, hard call cap.

Every live request is appended to data/cfb/_meta/api_calls.csv. Cached
responses are returned without touching the network or the ledger. The
API key is read from .env (CFBD_API_KEY) and is never printed or logged.
"""
from __future__ import annotations
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from engine.cfb import config

LEDGER_COLS = ["timestamp", "dataset", "endpoint", "params", "status",
               "rows", "cache_file"]


class CallCapExceeded(RuntimeError):
    pass


def _load_key() -> str:
    key = os.environ.get("CFBD_API_KEY", "")
    if not key and config.ENV_FILE.exists():
        from dotenv import dotenv_values
        key = dotenv_values(config.ENV_FILE).get("CFBD_API_KEY") or ""
    return key.strip().strip('"').strip("'")


def calls_used() -> int:
    if not config.LEDGER.exists():
        return 0
    with open(config.LEDGER, newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def calls_by_dataset() -> dict[str, int]:
    out: dict[str, int] = {}
    if config.LEDGER.exists():
        with open(config.LEDGER, newline="") as f:
            for r in csv.DictReader(f):
                out[r["dataset"]] = out.get(r["dataset"], 0) + 1
    return out


class CFBDClient:
    def __init__(self, cap: int = config.CALL_CAP):
        self.cap = cap
        self.live_calls = 0
        self._session = None

    def _http(self):
        if self._session is None:
            import requests
            key = _load_key()
            if not key:
                raise RuntimeError("CFBD_API_KEY not set (env or .env)")
            self._session = requests.Session()
            self._session.headers["Authorization"] = f"Bearer {key}"
            self._session.headers["Accept"] = "application/json"
        return self._session

    @staticmethod
    def cache_path(dataset: str, name: str) -> Path:
        return config.RAW / dataset / f"{name}.json"

    def is_cached(self, dataset: str, name: str) -> bool:
        return self.cache_path(dataset, name).exists()

    def get(self, dataset: str, endpoint: str, params: dict, name: str,
            refresh: bool = False):
        """Return the JSON for endpoint+params, from cache unless refresh."""
        path = self.cache_path(dataset, name)
        if path.exists() and not refresh:
            with open(path, encoding="utf-8") as f:
                return json.load(f)

        used = calls_used()
        if used >= self.cap:
            raise CallCapExceeded(
                f"call cap reached ({used}/{self.cap}); not calling {endpoint}")

        r = self._http().get(config.BASE_URL + endpoint, params=params,
                             timeout=120)
        self.live_calls += 1
        payload = None
        rows = ""
        if r.status_code == 200:
            payload = r.json()
            rows = len(payload) if isinstance(payload, list) else 1
        self._log(dataset, endpoint, params, r.status_code, rows, path)
        if r.status_code != 200:
            raise RuntimeError(f"{endpoint} {params} -> HTTP {r.status_code}: "
                               f"{r.text[:200]}")

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, path)
        return payload

    @staticmethod
    def _log(dataset, endpoint, params, status, rows, path):
        config.META.mkdir(parents=True, exist_ok=True)
        new = not config.LEDGER.exists()
        with open(config.LEDGER, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(LEDGER_COLS)
            w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        dataset, endpoint, json.dumps(params, sort_keys=True),
                        status, rows,
                        path.relative_to(config.ROOT).as_posix()])
