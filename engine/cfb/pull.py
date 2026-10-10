"""Pull CFBD raw data into data/cfb/raw (cached; re-runs cost zero calls).

    python -m engine.cfb.pull --seasons 2021-2026 --dry-run
    python -m engine.cfb.pull --seasons 2021-2026 --confirm
    python -m engine.cfb.pull --seasons 2026 --datasets plays --weeks 6 --refresh

PBP is pulled per (season, season type, week) only for weeks that are over;
weeks come from the cached games response, so `games` is always pulled first.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta, timezone

from engine.cfb import config
from engine.cfb.cfbd_client import CFBDClient, CallCapExceeded, calls_used

# name -> (endpoint, params(season)). One call per season each.
SEASON_DATASETS = {
    "games":      ("/games",               lambda y: {"year": y, "seasonType": "both"}),
    "lines":      ("/lines",               lambda y: {"year": y, "seasonType": "both"}),
    "advanced":   ("/stats/game/advanced", lambda y: {"year": y, "seasonType": "both"}),
    "ppa_games":  ("/ppa/games",           lambda y: {"year": y, "seasonType": "both"}),
    "returning":  ("/player/returning",    lambda y: {"year": y}),
    "talent":     ("/talent",              lambda y: {"year": y}),
    "recruiting": ("/recruiting/teams",    lambda y: {"year": y}),
    "sp":         ("/ratings/sp",          lambda y: {"year": y}),
    "fpi":        ("/ratings/fpi",         lambda y: {"year": y}),
    "elo":        ("/ratings/elo",         lambda y: {"year": y}),
    "coaches":    ("/coaches",             lambda y: {"year": y}),
    "portal":     ("/player/portal",       lambda y: {"year": y}),
    # Patreon-only per the v2 spec; opt in with --datasets weather.
    "weather":    ("/games/weather",       lambda y: {"year": y, "seasonType": "both"}),
}
ONCE_DATASETS = {"venues": ("/venues", {})}
OPT_IN = {"weather"}
DEFAULT_DATASETS = (["games"] + [d for d in SEASON_DATASETS if d not in OPT_IN and d != "games"]
                    + list(ONCE_DATASETS) + ["plays"])


def parse_seasons(s: str) -> list[int]:
    out: list[int] = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _parse_ts(s: str | None):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def completed_weeks(games: list[dict], now: datetime | None = None) -> list[tuple[str, int]]:
    """(seasonType, week) pairs whose last kickoff is WEEK_DONE_HOURS old."""
    now = now or datetime.now(timezone.utc)
    last: dict[tuple[str, int], datetime] = {}
    for g in games:
        st, wk, ts = g.get("seasonType"), g.get("week"), _parse_ts(g.get("startDate"))
        if st not in ("regular", "postseason") or wk is None or ts is None:
            continue
        k = (st, int(wk))
        last[k] = max(last.get(k, ts), ts)
    cut = now - timedelta(hours=config.WEEK_DONE_HOURS)
    return sorted(k for k, ts in last.items() if ts <= cut)


def plays_name(season: int, st: str, wk: int) -> str:
    return f"{season}_wk{wk:02d}" if st == "regular" else f"{season}_post_wk{wk:02d}"


def estimate_weeks(season: int) -> int:
    """Upper-bound PBP calls for a season whose games aren't cached yet."""
    if season < config.CURRENT_SEASON:
        return config.EST_REGULAR_WEEKS + config.EST_POSTSEASON_WEEKS
    days = (datetime.now(timezone.utc).date() - datetime(season, 8, 24).date()).days
    return max(0, min(config.EST_REGULAR_WEEKS, days // 7))


def plan(client: CFBDClient, seasons, datasets, refresh, weeks_filter):
    """List of (dataset, endpoint, params, cache_name, estimated?) still to fetch."""
    todo = []
    for ds in datasets:
        if ds in ONCE_DATASETS:
            ep, params = ONCE_DATASETS[ds]
            if refresh or not client.is_cached(ds, "all"):
                todo.append((ds, ep, params, "all", False))
            continue
        for y in seasons:
            if ds == "plays":
                gpath = client.cache_path("games", str(y))
                if not gpath.exists():
                    todo += [("plays", "/plays", {"year": y}, f"{y}_est{i}", True)
                             for i in range(estimate_weeks(y))]
                    continue
                games = json.loads(gpath.read_text(encoding="utf-8"))
                for st, wk in completed_weeks(games):
                    if weeks_filter and wk not in weeks_filter:
                        continue
                    name = plays_name(y, st, wk)
                    if refresh or not client.is_cached("plays", name):
                        todo.append(("plays", "/plays",
                                     {"year": y, "week": wk, "seasonType": st},
                                     name, False))
            else:
                ep, pfn = SEASON_DATASETS[ds]
                if refresh or not client.is_cached(ds, str(y)):
                    todo.append((ds, ep, pfn(y), str(y), False))
    return todo


def summarize(todo) -> None:
    by: dict[str, list] = {}
    for t in todo:
        by.setdefault(t[0], []).append(t)
    print(f"{'dataset':<12}{'calls':>7}  note")
    for ds, items in by.items():
        est = any(t[4] for t in items)
        print(f"{ds:<12}{len(items):>7}  {'upper-bound estimate (games not cached yet)' if est else ''}")
    print(f"{'TOTAL':<12}{len(todo):>7}")
    print(f"ledger so far: {calls_used()} calls; cap {config.CALL_CAP}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seasons", default=f"{config.SEASONS[0]}-{config.SEASONS[-1]}")
    ap.add_argument("--datasets", nargs="+", default=DEFAULT_DATASETS,
                    choices=list(SEASON_DATASETS) + list(ONCE_DATASETS) + ["plays"])
    ap.add_argument("--weeks", type=int, nargs="+",
                    help="limit plays to these week numbers (with --refresh)")
    ap.add_argument("--refresh", action="store_true",
                    help="re-fetch the selected datasets/seasons even if cached")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--confirm", action="store_true",
                    help=f"allow a pull estimated above {config.CONFIRM_ABOVE} calls")
    ap.add_argument("--cap", type=int, default=config.CALL_CAP)
    a = ap.parse_args(argv)

    seasons = parse_seasons(a.seasons)
    # games first: plays weeks are planned from the cached games response
    datasets = sorted(set(a.datasets), key=lambda d: (d != "games", d == "plays"))
    client = CFBDClient(cap=a.cap)
    todo = plan(client, seasons, datasets, a.refresh, set(a.weeks or []))

    print(f"seasons {seasons[0]}-{seasons[-1]}  datasets: {', '.join(datasets)}")
    summarize(todo)
    if a.dry_run:
        return 0
    if len(todo) > config.CONFIRM_ABOVE and not a.confirm:
        print(f"estimate > {config.CONFIRM_ABOVE}: re-run with --confirm after sign-off")
        return 2
    if calls_used() + len(todo) > a.cap:
        print(f"estimate would pass the {a.cap}-call cap; aborting before any call")
        return 2

    failures = []
    try:
        for ds in datasets:
            if ds == "plays":
                continue
            for t in plan(client, seasons, [ds], a.refresh, set()):
                try:
                    client.get(t[0], t[1], t[2], t[3], refresh=a.refresh)
                except RuntimeError as e:
                    if isinstance(e, CallCapExceeded):
                        raise
                    failures.append(str(e))
                    print("  FAIL", e)
        if "plays" in datasets:
            for t in plan(client, seasons, ["plays"], a.refresh, set(a.weeks or [])):
                if t[4]:
                    failures.append(f"plays {t[2]['year']}: games not cached, skipped")
                    continue
                try:
                    client.get(t[0], t[1], t[2], t[3], refresh=a.refresh)
                except RuntimeError as e:
                    if isinstance(e, CallCapExceeded):
                        raise
                    failures.append(str(e))
                    print("  FAIL", e)
    except CallCapExceeded as e:
        print("STOPPED:", e)
        failures.append(str(e))
    print(f"live calls this run: {client.live_calls}; ledger total: {calls_used()}")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
