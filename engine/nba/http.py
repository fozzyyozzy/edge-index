"""GET with retries + backoff for NBA sources (same policy as automation/pipeline/common.download:
3 tries, 5s then 15s, retry network errors / 429 / 5xx, never retry 400/401/404/410/422).
API keys are redacted from every error message."""
from __future__ import annotations
import os
import re
import time

import requests

TRIES = 3
RETRY_WAIT = float(os.environ.get("EDGE_RETRY_WAIT", "5"))
NO_RETRY = {400, 401, 403, 404, 410, 422}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/130.0 Safari/537.36"}


class FetchError(RuntimeError):
    pass


def redact(s: str) -> str:
    return re.sub(r"(apiKey=)[^&\s]+", r"\1REDACTED", str(s))


def get(url: str, params: dict | None = None, timeout: float = 30, headers: dict | None = None) -> requests.Response:
    last = None
    for i in range(TRIES):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers=headers or UA)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
            if r.status_code in NO_RETRY:
                break
        except requests.RequestException as e:
            last = f"{type(e).__name__}: {e}"
        if i < TRIES - 1:
            time.sleep(RETRY_WAIT * 3 ** i)
    raise FetchError(redact(f"{url} failed after retries: {last}"))


def get_json(url: str, params: dict | None = None, timeout: float = 30, headers: dict | None = None):
    return get(url, params, timeout, headers).json()
