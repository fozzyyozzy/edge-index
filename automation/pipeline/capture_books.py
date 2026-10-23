"""
capture_books.py — six-book price capture at the card's publish time (research; never changes a card).
For the slate's unstarted games, pulls receptions and rec_yds main lines AND alternate ladders from the six books Tim can
bet (DraftKings, FanDuel, BetMGM, Caesars, Fanatics, BetRivers), stores every book's price, and, for each published card
leg in those markets, records the best available price and book next to DK's.
  python pipeline/capture_books.py --season 2026 --week 7 --slate sun
Writes:
  lines/books/books_<season>_w<week>_<slate>_<UTC stamp>.json.gz   gzip JSON records: PulledAt,Game,Commence,Book,Player,
                                                               Market,Kind,Side,Point,Price (Kind = main | alt; never
                                                               overwritten). ~5.6 KB per game (vs ~91 KB as CSV): about
                                                               1.5 MB per season at one capture per game. Read with
                                                               read_capture().
  cards/bestprice_<season>_w<week>_<slate>.json                 per card leg (receptions / rec_yds): DK odds, best odds + book,
                                                               every book's odds at that rung; other markets listed as
                                                               not captured. The card JSON itself is not touched.
  lines/odds_usage_books.csv                                    one row per run. Kept apart from lines/odds_usage.csv so
                                                               this job never eats the card pulls' ODDS_WEEKLY_BUDGET.
Cost: live event odds cost 1 credit per market per region, and the six named books are one region -> 4 per game
(2 main + 2 alternate markets). Guards: skip (exit 3) if x-requests-remaining would fall under NFL_BOOKS_RESERVE
(default 100,000) or the pull would pass NFL_BOOKS_CAP credits (default 400).
Exit 3 = skipped (no unstarted games, or a guard). card.yml runs this with continue-on-error: it never blocks a card.
"""
import argparse, csv, json, os, sys
from datetime import datetime, timedelta, timezone
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, norm_name
from fetch_lines import get, slate_of, in_week

BOOKS = ["draftkings", "fanduel", "betmgm", "williamhill_us", "fanatics", "betrivers"]   # williamhill_us = Caesars
MARKETS = {"player_receptions": ("receptions", "main"), "player_reception_yds": ("rec_yds", "main"),
           "player_receptions_alternate": ("receptions", "alt"), "player_reception_yds_alternate": ("rec_yds", "alt")}
COLS = ["PulledAt", "Game", "Commence", "Book", "Player", "Market", "Kind", "Side", "Point", "Price"]
USAGE_COLS = ["pulled_at", "season", "week", "slate", "events", "cost", "remaining"]
PER_GAME = len(MARKETS)                                   # credits per event (1 per market, one region)


def guard(events, remaining, reserve, cap):
    """None if the pull may run, else the reason to skip"""
    if not events: return "no unstarted games on this slate this week"
    cost = len(events) * PER_GAME
    if cost > cap: return f"~{cost} credits would pass NFL_BOOKS_CAP={cap}"
    if remaining is not None and int(float(remaining)) - cost < reserve:
        return f"remaining {remaining} - ~{cost} would fall under NFL_BOOKS_RESERVE={reserve}"
    return None


def parse_event(d, game, commence, pulled_at):
    """rows for the listed books and markets in one /events/{id}/odds response"""
    rows = []
    for b in d.get("bookmakers", []):
        if b.get("key") not in BOOKS: continue
        for m in b.get("markets", []):
            if m.get("key") not in MARKETS: continue
            mkt, kind = MARKETS[m["key"]]
            for o in m.get("outcomes", []):
                rows.append(dict(PulledAt=pulled_at, Game=game, Commence=commence, Book=b["key"], Player=o.get("description"),
                                 Market=mkt, Kind=kind, Side=o["name"], Point=float(o["point"]), Price=int(o["price"])))
    return rows


def best_for_legs(card, rows):
    """per card leg: every book's Over price at the leg's rung (alt rung, or a main line at the same point), best of them"""
    df = pd.DataFrame(rows, columns=COLS)
    if len(df):
        df = df[df.Side == "Over"].assign(key=df.Player.map(norm_name))
    legs = {}
    for src in ("candidates", "floors_singles"):
        for x in card.get(src, []):
            legs.setdefault((x["player"], x["market"], float(x["rung"])), x)
    for t in card.get("tickets", []):
        for x in t.get("legs", []):
            legs.setdefault((x["player"], x["market"], float(x["rung"])), x)
    out = []
    for (player, market, rung), x in sorted(legs.items()):
        rec = dict(player=player, market=market, rung=rung, card_odds=x.get("published_odds", x.get("odds_real", x.get("odds_est"))))
        if market not in ("receptions", "rec_yds"):
            out.append({**rec, "captured": False, "note": "market not captured (receptions / rec_yds only)"}); continue
        at = df[(df.key == norm_name(player)) & (df.Market == market) & (df.Point == rung - 0.5)] if len(df) else df
        by_book = {}
        for r in at.itertuples():                      # a book may post the rung both as main and alt: keep the better
            if r.Book not in by_book or _dec(r.Price) > _dec(by_book[r.Book]): by_book[r.Book] = int(r.Price)
        best = max(by_book.items(), key=lambda kv: (_dec(kv[1]), kv[0] == "draftkings")) if by_book else (None, None)
        out.append({**rec, "captured": True, "dk_odds": by_book.get("draftkings"), "best_odds": best[1], "best_book": best[0],
                    "books": by_book, "books_posting": len(by_book),
                    "best_beats_dk": bool(best[1] is not None and by_book.get("draftkings") is not None
                                          and _dec(best[1]) > _dec(by_book["draftkings"]))})
    return out


def write_capture(rows, path):
    """rows -> gzip JSON records (pandas infers gzip from .gz)"""
    pd.DataFrame(rows, columns=COLS).to_json(path, orient="records", compression="gzip")


def read_capture(path):
    return pd.read_json(path, orient="records", compression="gzip", dtype={"Price": "int64", "Point": "float64"})


def _dec(o):
    return 1 + (100 / -o if o < 0 else o / 100)


def log_usage(row):
    path = P("lines", "odds_usage_books.csv"); new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=USAGE_COLS)
        if new: w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", choices=["tnf", "sun", "mnf"], required=True)
    ap.add_argument("--days", type=int, default=None, help="look-ahead window (default: 2 for tnf/mnf, 5 for sun)")
    a = ap.parse_args()
    key = os.environ.get("ODDS_API_KEY") or sys.exit("set ODDS_API_KEY")
    reserve = int(os.environ.get("NFL_BOOKS_RESERVE", "100000"))
    cap = int(os.environ.get("NFL_BOOKS_CAP", "400"))
    days = a.days or (5 if a.slate == "sun" else 2)

    events, rem, _ = get(f"/events?apiKey={key}")            # free
    now = datetime.now(timezone.utc)
    start = lambda e: datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
    events = [e for e in events if now < start(e) <= now + timedelta(days=days) and slate_of(e["commence_time"]) == a.slate]
    events = in_week(events, a.season, a.week)
    why = guard(events, rem, reserve, cap)
    if why:
        print(f"::notice::six-book capture skipped: {why}"); sys.exit(3)

    pulled_at = now.isoformat(timespec="minutes")
    rows, cost = [], 0
    for e in events:
        path = (f"/events/{e['id']}/odds?apiKey={key}&regions=us&bookmakers={','.join(BOOKS)}"
                f"&markets={','.join(MARKETS)}&oddsFormat=american")
        try:
            d, rem, last = get(path)
        except Exception as ex:
            print("  skip", e["away_team"], "@", e["home_team"], ex); continue
        cost += int(last or 0)
        rows += parse_event(d, f"{e['away_team']} @ {e['home_team']}", e["commence_time"], pulled_at)

    stamp = now.strftime("%Y-%m-%dT%H%MZ")
    out = P("lines", "books", f"books_{a.season}_w{a.week}_{a.slate}_{stamp}.json.gz")
    write_capture(rows, out)
    log_usage(dict(pulled_at=pulled_at, season=a.season, week=a.week, slate=a.slate, events=len(events), cost=cost,
                   remaining=rem))
    card_path = P("cards", f"card_{a.season}_w{a.week}_{a.slate}.json")
    if os.path.exists(card_path):
        legs = best_for_legs(json.load(open(card_path, encoding="utf-8")), rows)
        json.dump(dict(season=a.season, week=a.week, slate=a.slate, pulled_at=pulled_at, books=BOOKS,
                       source=os.path.relpath(out, P()).replace(os.sep, "/"), legs=legs),
                  open(P("cards", f"bestprice_{a.season}_w{a.week}_{a.slate}.json"), "w"), indent=1)
        better = sum(1 for l in legs if l.get("best_beats_dk"))
        print(f"best prices for {len(legs)} card legs ({better} beat DK)")
    print(f"wrote {out}: {len(rows)} prices from {len(events)} games; {cost} credits, {rem} remaining")


if __name__ == "__main__":
    main()
