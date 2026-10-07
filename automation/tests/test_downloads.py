"""Every outside download goes through common.download(): retries with backoff, then a fallback source, then one clear
error naming the source and every URL (keys redacted). The static test fails if a new download bypasses it."""
import ast, glob, gzip, os, urllib.error
import pytest
import common
from common import SOURCES, download, read_csv_source, DownloadError

AUTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(glob.glob(os.path.join(AUTO, "pipeline", "*.py")) + glob.glob(os.path.join(AUTO, "newsletter", "*.py")))
# Calls that open a URL. Only common.download() may make them.
URL_CALLS = {"urlopen", "urlretrieve", "Request", "get", "post", "put", "request"}
NET_MODULES = {"urllib", "urllib.request", "requests", "http.client", "httpx", "aiohttp"}
# The one network call allowed outside download(): an upload, not a download. A retried POST could create duplicate
# drafts, and it only runs with --to beehiiv (the newsletter goes out through Substack).
ALLOWED = {("newsletter/draft.py", "beehiiv_draft")}
# Sources with no second copy anywhere: retries only.
NO_FALLBACK = {"The Odds API": "a single paid API; no mirror exists"}


def rel(path): return os.path.relpath(path, AUTO).replace(os.sep, "/")


def enclosing_functions(tree):
    owner = {}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(fn): owner.setdefault(id(n), fn.name)
    return owner


@pytest.mark.parametrize("path", FILES, ids=rel)
def test_no_network_call_bypasses_download(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    owner, bad = enclosing_functions(tree), []
    imports_net = any(isinstance(n, ast.Import) and any(a.name in NET_MODULES for a in n.names) or
                      isinstance(n, ast.ImportFrom) and (n.module or "") in NET_MODULES for n in ast.walk(tree))
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call): continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
        base = ast.unparse(f.value) if isinstance(f, ast.Attribute) else ""
        is_net = name in ("urlopen", "urlretrieve") or (name == "Request" and "urllib" in base) or \
                 (imports_net and name in ("get", "post", "put", "request") and base.split(".")[0] in ("requests", "httpx", "session"))
        if not is_net: continue
        where = (rel(path), owner.get(id(n)))
        if where == ("pipeline/common.py", "download") or where in ALLOWED: continue
        bad.append(f"{rel(path)}:{n.lineno} {ast.unparse(n)[:80]} (in {owner.get(id(n))})")
    assert not bad, "network calls outside common.download():\n" + "\n".join(bad)


@pytest.mark.parametrize("path", FILES, ids=rel)
def test_download_urls_live_only_in_SOURCES(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body
                  and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    owner, bad = enclosing_functions(tree), []
    in_sources = set()
    if rel(path) == "pipeline/common.py":                         # the SOURCES / NFLVERSE assignments, and the UA header
        for n in tree.body:
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("SOURCES", "NFLVERSE") for t in n.targets):
                in_sources |= {id(c) for c in ast.walk(n)}
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "://" in n.value and id(n) not in docstrings:
            if id(n) in in_sources or "User-Agent" in n.value or n.value.startswith("edge-index/"): continue
            if (rel(path), owner.get(id(n))) in ALLOWED: continue
            bad.append(f"{rel(path)}:{n.lineno} {n.value[:80]!r}")
    assert not bad, "URL literals outside common.SOURCES (add them there and fetch with download()):\n" + "\n".join(bad)


def test_every_source_has_a_fallback_or_a_reason():
    for name, urls in SOURCES.items():
        assert len(urls) >= 2 or name in NO_FALLBACK, f"{name}: add a fallback URL or a NO_FALLBACK reason"


# ── behaviour ─────────────────────────────────────────────────────────────────────────────────────────────────────
class Resp:
    def __init__(self, body, headers=None): self.body, self.headers = body, headers or {}
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *a): return False


@pytest.fixture
def net(monkeypatch):
    """scripted urlopen: {url: [outcome, ...]}; an outcome is bytes, an int (HTTP error code) or an Exception"""
    monkeypatch.setattr(common, "RETRY_WAIT", 0)
    calls, script = [], {}
    def fake(req, timeout=0):
        url = req.full_url; calls.append(url)
        out = script[url].pop(0) if script.get(url) else 404
        if isinstance(out, int): raise urllib.error.HTTPError(url, out, "err", {}, None)
        if isinstance(out, Exception): raise out
        return Resp(out, {"x-requests-remaining": "100"})
    monkeypatch.setattr(common.urllib.request, "urlopen", fake)
    monkeypatch.setitem(SOURCES, "test source", ["https://a.example/x_{season}.csv?apiKey=SECRET123",
                                                 "https://b.example/x_{season}.csv.gz"])
    return script, calls


def test_transient_errors_are_retried_then_succeed(net):
    script, calls = net
    script["https://a.example/x_2026.csv?apiKey=SECRET123"] = [OSError("reset"), 503, b"a,b\n1,2\n"]
    raw, headers, url = download("test source", season=2026)
    assert raw == b"a,b\n1,2\n" and len(calls) == 3 and url.startswith("https://a.example")


def test_404_moves_straight_to_the_fallback(net):
    script, calls = net
    script["https://a.example/x_2026.csv?apiKey=SECRET123"] = [404]
    script["https://b.example/x_2026.csv.gz"] = [gzip.compress(b"a,b\n3,4\n")]
    df = read_csv_source("test source", season=2026)                    # gzip detected from the bytes
    assert len(calls) == 2 and df.to_dict("records") == [{"a": 3, "b": 4}]


def test_total_failure_names_the_source_and_every_url_without_the_key(net):
    script, calls = net
    script["https://a.example/x_2026.csv?apiKey=SECRET123"] = [500, 500, 500]
    script["https://b.example/x_2026.csv.gz"] = [TimeoutError("timed out")] * 3
    with pytest.raises(DownloadError) as e:
        download("test source", season=2026)
    msg = str(e.value)
    assert msg.startswith("test source: every source failed")
    assert "https://a.example/x_2026.csv?apiKey=REDACTED -> HTTP 500 (attempt 3)" in msg
    assert "https://b.example/x_2026.csv.gz -> TimeoutError" in msg
    assert "SECRET123" not in msg and len(calls) == 6


def test_odds_api_goes_through_download_with_the_key_redacted(monkeypatch):
    import fetch_lines
    seen = {}
    def fake_download(source, timeout=120, **fmt):
        seen.update(source=source, **fmt); return b'[{"id": 1}]', {"x-requests-remaining": "9", "x-requests-last": "1"}, "u"
    monkeypatch.setattr(fetch_lines, "download", fake_download)
    assert fetch_lines.get("/events?apiKey=K") == ([{"id": 1}], "9", "1")
    assert seen == dict(source="The Odds API", path="/events?apiKey=K")
    assert common.redact("https://x/y?apiKey=K&regions=us") == "https://x/y?apiKey=REDACTED&regions=us"


def test_the_scanners_catch_a_bypass(tmp_path):
    """control: a new script that downloads on its own must fail both static checks"""
    bad = tmp_path / "new_scraper.py"
    bad.write_text('import urllib.request\n'
                   'def grab():\n'
                   '    return urllib.request.urlopen("https://example.com/data.csv").read()\n')
    with pytest.raises(AssertionError, match="network calls outside"):
        test_no_network_call_bypasses_download(str(bad))
    with pytest.raises(AssertionError, match="URL literals outside"):
        test_download_urls_live_only_in_SOURCES(str(bad))
