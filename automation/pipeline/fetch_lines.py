"""
fetch_lines.py — pulls DraftKings alternate-line ladders for NFL games from The Odds API.
Replaces pasting. Writes:
  lines/ladders_<season>_w<week>.csv      Player,Market,Rung,Odds,Game,Commence,PulledAt   (every rung, real prices)
  lines/dk_<season>_w<week>_{all,tnf,sun,mnf}.csv   Player,Market,Line,Odds       (main line = rung priced closest to -110)
  lines/pulled_<season>_w<week>[_<slate>].txt       when this pull happened (UTC ISO)
  lines/odds_usage.csv                              one row per run: requests spent and quota left
Only games that have NOT kicked off are pulled. A pull replaces the ladder rows of the games it fetched and keeps
every other game's rows (so a TNF-only refresh doesn't wipe Sunday's ladders, and a started game keeps its last
pre-kickoff prices).
Env: ODDS_API_KEY; ODDS_WEEKLY_BUDGET (default 3000) caps requests per NFL week across every caller.
Cost: 1 request per market per event -> 7 per game.
  python pipeline/fetch_lines.py --season 2026 --week 3                 (all games in the next 7 days)
  python pipeline/fetch_lines.py --season 2026 --week 3 --slate sun     (just that slate's unstarted games)
Exit 3 = skipped because the weekly budget would be exceeded.
"""
import argparse, csv, json, os, shutil, sys, urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P

BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
MARKETS = {                      # Odds API market key -> pipeline market
    "player_reception_yds_alternate": "rec_yds",
    "player_receptions_alternate": "receptions",
    "player_pass_yds_alternate": "pass_yds",
    "player_pass_completions_alternate": "pass_cmps",
    "player_pass_attempts_alternate": "pass_att",
    "player_rush_yds_alternate": "rush_yds",
    "player_rush_attempts_alternate": "rush_att",
}
ET = ZoneInfo("America/New_York")
LADDER_COLS = ["Player", "Market", "Rung", "Odds", "Game", "Commence", "PulledAt"]
USAGE_COLS = ["pulled_at", "season", "week", "slate", "events", "cost", "remaining"]

def slate_of(commence_iso):
    """Thursday game -> tnf, Monday -> mnf, anything else (Sun, Sat, Fri, international) -> sun. ET weekday."""
    d = datetime.fromisoformat(commence_iso.replace("Z", "+00:00")).astimezone(ET).strftime("%A")
    return "tnf" if d == "Thursday" else "mnf" if d == "Monday" else "sun"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "edge-index/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        h = r.headers
        return json.loads(r.read()), h.get("x-requests-remaining"), h.get("x-requests-last")

def week_usage(season, week):
    path = P("lines", "odds_usage.csv")
    if not os.path.exists(path): return 0
    u = pd.read_csv(path)
    return int(u[(u.season == season) & (u.week == week)].cost.sum())

def log_usage(row):
    path = P("lines", "odds_usage.csv"); new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=USAGE_COLS)
        if new: w.writeheader()
        w.writerow(row)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--days", type=int, default=7); ap.add_argument("--book", default="draftkings")
    ap.add_argument("--slate", choices=["tnf", "sun", "mnf"], default=None, help="only this slate's games")
    ap.add_argument("--out", default=None); a = ap.parse_args()
    key = os.environ.get("ODDS_API_KEY") or sys.exit("set ODDS_API_KEY")
    budget = int(os.environ.get("ODDS_WEEKLY_BUDGET", "3000"))
    a.out = a.out or P("lines")

    events, rem, _ = get(f"{BASE}/events?apiKey={key}")          # the events list doesn't count against the quota
    now = datetime.now(timezone.utc); horizon = now + timedelta(days=a.days)
    start = lambda e: datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
    events = [e for e in events if now < start(e) <= horizon]      # not kicked off yet
    if a.slate: events = [e for e in events if slate_of(e["commence_time"]) == a.slate]
    used = week_usage(a.season, a.week); estimate = len(events) * len(MARKETS)
    print(f"{len(events)} unstarted {a.slate or 'all-slate'} events in window; quota remaining {rem}; "
          f"week {a.week} used {used}/{budget}, this pull ~{estimate}")
    if used + estimate > budget:
        print(f"::warning::skipping pull: {used} + ~{estimate} would pass the weekly budget of {budget}")
        sys.exit(3)
    if not events:
        print("nothing to pull"); return

    pulled_at = now.isoformat(timespec="minutes")
    rows, cost, pulled_games = [], 0, set()
    mk = ",".join(MARKETS)
    for e in events:
        url = f"{BASE}/events/{e['id']}/odds?apiKey={key}&regions=us&bookmakers={a.book}&markets={mk}&oddsFormat=american"
        try:
            d, rem, last = get(url)
        except Exception as ex:
            print("  skip", e["away_team"], "@", e["home_team"], ex); continue
        cost += int(last or 0)
        game = f"{e['away_team']} @ {e['home_team']}"; pulled_games.add(game)
        for b in d.get("bookmakers", []):
            for m in b["markets"]:
                mkt = MARKETS.get(m["key"])
                if not mkt: continue
                for o in m["outcomes"]:
                    if o["name"] != "Over": continue
                    rung = float(o["point"]) + 0.5 if float(o["point"]) % 1 else float(o["point"])   # 69.5 -> 70+
                    rows.append(dict(Player=o["description"], Market=mkt, Rung=rung, Odds=int(o["price"]),
                                     Game=game, Commence=e["commence_time"], PulledAt=pulled_at))
        print(f"  {game}: {sum(1 for r in rows if r['Game']==game)} rungs  (cost {last}, remaining {rem})")
    log_usage(dict(pulled_at=pulled_at, season=a.season, week=a.week, slate=a.slate or "all",
                   events=len(pulled_games), cost=cost, remaining=rem))
    print(f"spent {cost} requests; quota remaining {rem}; week {a.week} total {used + cost}/{budget}")
    if not rows:
        print("::warning::no rungs came back; ladders and pull times left as they were"); return

    # merge: replace the fetched games' rows, keep every other game's (older rows get PulledAt from the pulled_ file)
    os.makedirs(a.out, exist_ok=True)
    lpath = f"{a.out}/ladders_{a.season}_w{a.week}.csv"
    new = pd.DataFrame(rows, columns=LADDER_COLS).drop_duplicates(["Player", "Market", "Rung"])
    if os.path.exists(lpath):
        old = pd.read_csv(lpath)
        if "PulledAt" not in old:
            prev = f"{a.out}/pulled_{a.season}_w{a.week}.txt"
            old["PulledAt"] = open(prev).read().strip() if os.path.exists(prev) else None
        lad = pd.concat([old[~old.Game.isin(pulled_games)][LADDER_COLS], new], ignore_index=True)
    else:
        lad = new
    lad.to_csv(lpath, index=False)

    # when prices were pulled: per slate that had games in this pull, plus the week-level file (latest pull)
    for s in sorted({slate_of(r["Commence"]) for r in rows}):
        open(f"{a.out}/pulled_{a.season}_w{a.week}_{s}.txt", "w").write(pulled_at)
    open(f"{a.out}/pulled_{a.season}_w{a.week}.txt", "w").write(pulled_at)

    # main line per player/market = the rung priced closest to even money (what DK shows as the O/U line)
    lad = lad.copy()
    lad["dist"] = (lad.Odds.abs() - 110).abs() + (lad.Odds > 0) * 5
    main = lad.sort_values("dist").groupby(["Player", "Market"], as_index=False).first()[["Player", "Market", "Rung", "Odds"]]
    main = main.rename(columns={"Rung": "Line"})
    allp = f"{a.out}/dk_{a.season}_w{a.week}_all.csv"; main.to_csv(allp, index=False)
    for slate in ("tnf", "sun", "mnf"): shutil.copy(allp, f"{a.out}/dk_{a.season}_w{a.week}_{slate}.csv")
    print(f"wrote {len(new)} new rungs ({len(lad)} in the week's ladder) for {main.Player.nunique()} players -> ladders + dk_*.csv")

if __name__ == "__main__":
    main()
