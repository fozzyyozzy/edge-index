"""
fetch_lines.py — pulls DraftKings alternate-line ladders for every NFL game from The Odds API.
Replaces pasting. Writes:
  lines/ladders_<season>_w<week>.csv      Player,Market,Rung,Odds,Game,Commence   (every rung, real prices)
  lines/dk_<season>_w<week>_{all,tnf,sun,mnf}.csv   Player,Market,Line,Odds       (main line = rung priced closest to -110)
Env: ODDS_API_KEY.   Cost: 1 request per market per event -> 7 x games per pull (~112 for a full week).
  python pipeline/fetch_lines.py --season 2026 --week 3            (all games in the next 7 days)
  python pipeline/fetch_lines.py --season 2026 --week 3 --days 2   (just the next slate)
"""
import argparse, json, os, shutil, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
import pandas as pd

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

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "edge-index/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        remaining = r.headers.get("x-requests-remaining"); used = r.headers.get("x-requests-used")
        return json.loads(r.read()), remaining, used

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--days", type=int, default=7); ap.add_argument("--book", default="draftkings")
    ap.add_argument("--out", default="lines"); a = ap.parse_args()
    key = os.environ.get("ODDS_API_KEY") or sys.exit("set ODDS_API_KEY")

    events, rem, _ = get(f"{BASE}/events?apiKey={key}")
    now = datetime.now(timezone.utc); horizon = now + timedelta(days=a.days)
    events = [e for e in events if now <= datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")) <= horizon]
    print(f"{len(events)} events in window; {rem} requests remaining before pull")

    rows = []
    mk = ",".join(MARKETS)
    for e in events:
        url = f"{BASE}/events/{e['id']}/odds?apiKey={key}&regions=us&bookmakers={a.book}&markets={mk}&oddsFormat=american"
        try:
            d, rem, used = get(url)
        except Exception as ex:
            print("  skip", e["away_team"], "@", e["home_team"], ex); continue
        game = f"{e['away_team']} @ {e['home_team']}"
        for b in d.get("bookmakers", []):
            for m in b["markets"]:
                mkt = MARKETS.get(m["key"])
                if not mkt: continue
                for o in m["outcomes"]:
                    if o["name"] != "Over": continue
                    rung = float(o["point"]) + 0.5 if float(o["point"]) % 1 else float(o["point"])   # 69.5 -> 70+
                    rows.append(dict(Player=o["description"], Market=mkt, Rung=rung, Odds=int(o["price"]),
                                     Game=game, Commence=e["commence_time"]))
        print(f"  {game}: {sum(1 for r in rows if r['Game']==game)} rungs  (remaining {rem})")

    lad = pd.DataFrame(rows).drop_duplicates(["Player", "Market", "Rung"])
    os.makedirs(a.out, exist_ok=True)
    lad.to_csv(f"{a.out}/ladders_{a.season}_w{a.week}.csv", index=False)

    # main line per player/market = the rung priced closest to even money (what DK shows as the O/U line)
    lad["dist"] = (lad.Odds.abs() - 110).abs() + (lad.Odds > 0) * 5
    main = lad.sort_values("dist").groupby(["Player", "Market"], as_index=False).first()[["Player", "Market", "Rung", "Odds"]]
    main = main.rename(columns={"Rung": "Line"})
    allp = f"{a.out}/dk_{a.season}_w{a.week}_all.csv"; main.to_csv(allp, index=False)
    for slate in ("tnf", "sun", "mnf"): shutil.copy(allp, f"{a.out}/dk_{a.season}_w{a.week}_{slate}.csv")
    print(f"wrote {len(lad)} rungs for {main.Player.nunique()} players -> ladders + dk_*.csv")

if __name__ == "__main__":
    main()
