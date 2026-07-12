"""
Timestamped MLB pitcher-strikeout line collector (The Odds API v4).

Every pull stores a snapshot per (event, pitcher, book): line + both prices +
pull time + first-pitch time. The LAST pregame snapshot is the closing line,
which powers CLV grading — the roadmap's leading indicator of long-term profit.

Usage:
    python -m engine.mlb.collect_k_odds --once            # one pull, store
    python -m engine.mlb.collect_k_odds --once --emit-json cfb-app/public/data/line_shop.json
    python -m engine.mlb.collect_k_odds --clv 2026-07-12  # CLV report for a date

Setup: put ODDS_API_KEY=... in the repo-root .env (player props require a
paid The Odds API plan; markets used: pitcher_strikeouts).
Costs 1 request/event/pull — a 15-game slate x 3 pulls/day ~= 45 req/day.
"""
import argparse, json, os, sqlite3, sys, time
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "data", "k_odds.sqlite")
BASE = "https://api.the-odds-api.com/v4"
SPORT = "baseball_mlb"
MARKET = "pitcher_strikeouts"
BOOKS = {"draftkings": "DK", "fanduel": "FD", "betmgm": "MGM", "caesars": "CZR"}


def api_key():
    k = os.environ.get("ODDS_API_KEY")
    if k: return k
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for ln in open(env):
            if ln.strip().startswith("ODDS_API_KEY"):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No ODDS_API_KEY found (env var or .env). Get one at the-odds-api.com "
             "— player props need a paid tier.")


def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS k_lines (
        pulled_at TEXT, event_id TEXT, commence TEXT, pitcher TEXT,
        book TEXT, line REAL, over_odds INTEGER, under_odds INTEGER)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_ev ON k_lines(event_id, pitcher, book)")
    return con


def pull(key, con):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    evs = requests.get(f"{BASE}/sports/{SPORT}/events",
                       params={"apiKey": key}, timeout=20).json()
    if not isinstance(evs, list):
        sys.exit(f"API error: {evs}")
    pregame = [e for e in evs if e.get("commence_time", "") > now]
    rows, remaining = 0, "?"
    for ev in pregame:
        r = requests.get(f"{BASE}/sports/{SPORT}/events/{ev['id']}/odds",
                         params={"apiKey": key, "regions": "us",
                                 "markets": MARKET, "oddsFormat": "american"},
                         timeout=20)
        remaining = r.headers.get("x-requests-remaining", remaining)
        data = r.json()
        for bm in data.get("bookmakers", []):
            if bm["key"] not in BOOKS: continue
            for mk in bm.get("markets", []):
                if mk["key"] != MARKET: continue
                by = {}
                for o in mk.get("outcomes", []):
                    k2 = (o.get("description"), o.get("point"))
                    by.setdefault(k2, {})[o["name"]] = o["price"]
                for (pitcher, line), sides in by.items():
                    con.execute("INSERT INTO k_lines VALUES (?,?,?,?,?,?,?,?)",
                                (now, ev["id"], ev["commence_time"], pitcher,
                                 BOOKS[bm["key"]], line,
                                 sides.get("Over"), sides.get("Under")))
                    rows += 1
        time.sleep(0.3)
    con.commit()
    print(f"{now}: stored {rows} lines from {len(pregame)} events "
          f"(API requests remaining: {remaining})")
    return rows


def latest_snapshot(con):
    """Newest row per (pitcher, book) among games not yet started."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = con.execute("""
        SELECT pitcher, book, line, over_odds, under_odds, MAX(pulled_at), commence
        FROM k_lines WHERE commence > ? GROUP BY pitcher, book, line""", (now,))
    return cur.fetchall()


def emit_line_shop(con, out_path):
    sys.path.insert(0, ROOT)
    try:
        from engine.core.odds import devig_two_way, prob_to_american
    except Exception:
        devig_two_way = None
    rows = latest_snapshot(con)
    by_pitcher = {}
    for pitcher, book, line, over, under, ts, commence in rows:
        by_pitcher.setdefault(pitcher, []).append(
            dict(book=book, line=line, over=over, under=under))
    pitchers = []
    for pitcher, books in sorted(by_pitcher.items()):
        # best over price at each pitcher's modal line
        lines = {}
        for b in books: lines.setdefault(b["line"], []).append(b)
        main_line = max(lines, key=lambda L: len(lines[L]))
        quotes = [b for b in lines[main_line] if b["over"] is not None]
        if not quotes: continue
        best = max(quotes, key=lambda b: b["over"])
        fair = None
        if devig_two_way:
            probs = [devig_two_way(b["over"], b["under"])[0]
                     for b in quotes if b["under"] is not None]
            if probs:
                fair = prob_to_american(sum(probs) / len(probs))
        pitchers.append(dict(
            pitcher=pitcher, line=main_line,
            fair_over=round(fair) if fair else None,
            books=[dict(b, best=(b is best)) for b in quotes]))
    payload = dict(generated=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   market=MARKET, pitchers=pitchers)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(payload, open(out_path, "w"), indent=1)
    print(f"wrote {out_path}: {len(pitchers)} pitchers")


def clv_report(con, date):
    """Compare each pitcher's first vs last pregame snapshot for a date."""
    cur = con.execute("""
        SELECT pitcher, book, line, over_odds, pulled_at, commence FROM k_lines
        WHERE commence LIKE ? ORDER BY pulled_at""", (date + "%",))
    hist = {}
    for pitcher, book, line, over, ts, commence in cur.fetchall():
        hist.setdefault((pitcher, book), []).append((ts, line, over))
    print(f"CLV report {date} — line & price movement (first pull -> close):")
    for (pitcher, book), snaps in sorted(hist.items()):
        if len(snaps) < 2: continue
        f, l = snaps[0], snaps[-1]
        if f[1] != l[1] or abs((f[2] or 0) - (l[2] or 0)) >= 10:
            print(f"  {pitcher:<24} {book}: {f[1]} @ {f[2]}  ->  {l[1]} @ {l[2]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="single pull")
    ap.add_argument("--emit-json", default=None, help="write line_shop.json here")
    ap.add_argument("--clv", default=None, metavar="YYYY-MM-DD")
    args = ap.parse_args()
    con = db()
    if args.clv:
        clv_report(con, args.clv)
    elif args.once or args.emit_json:
        if args.once:
            pull(api_key(), con)
        if args.emit_json:
            emit_line_shop(con, args.emit_json)
    else:
        ap.print_help()
