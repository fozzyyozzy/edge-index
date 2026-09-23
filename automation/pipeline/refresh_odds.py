"""
refresh_odds.py — after fetch_lines.py re-pulls a slate: move current prices onto the published card, flag new markets.
  python pipeline/refresh_odds.py --season 2026 --week 3 --slate sun
  python pipeline/refresh_odds.py --which-slate        prints the slate due for a scheduled refresh now (ET), else nothing

Card (cards/card_<season>_w<week>_<slate>.json): every leg on tickets and floors_singles gets current_odds / current_at
and a price_history point — only when the leg's game had not kicked off at that pull (so the last history point before
kickoff is the closing price grade.py uses). Nothing else on the card changes: tickets are locked at publish.
Legs / floors JSON (rebuilt from the same pull by grade_legs.py and floors.py just before this): any player/market DK
posted after the card was built gets posted_after_card: true. Those can never reach a ticket — build_card_json.py is not
re-run by a refresh.
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import norm_name, P, prices_pulled

ET = ZoneInfo("America/New_York")
# scheduled refreshes, ET: weekday -> hours (refresh-odds.yml has a UTC cron for each under both EDT and EST)
SCHEDULE = {"Wed": [15], "Thu": [9, 15, 19], "Fri": [15], "Sat": [12], "Sun": [9, 12], "Mon": [9, 15, 19]}
# first kickoff of each slate, minutes after Tuesday 00:00 ET — same rule as cfb-app/src/nflSlates.js
DAY = 1440
KICKOFF = {"tnf": 2 * DAY + 20 * 60 + 15, "sun": 5 * DAY + 13 * 60, "mnf": 6 * DAY + 20 * 60 + 15}
WEEKDAY = {"Tue": 0, "Wed": 1, "Thu": 2, "Fri": 3, "Sat": 4, "Sun": 5, "Mon": 6}

def upcoming_slate(now_et):
    t = WEEKDAY[now_et.strftime("%a")] * DAY + now_et.hour * 60 + now_et.minute
    return next((s for s in ("tnf", "sun", "mnf") if t < KICKOFF[s]), "tnf")

def which_slate(now=None):
    """The slate to refresh if now (ET) is a scheduled refresh hour, else None. Cron can run late; within the hour counts."""
    et = (now or datetime.now(timezone.utc)).astimezone(ET)
    return upcoming_slate(et) if et.hour in SCHEDULE.get(et.strftime("%a"), []) else None

def iso(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")) if s else None

def ladder_prices(season, week):
    """{(name, market, rung): (odds, pulled_at)} from the week's ladder (older ladders have no PulledAt column)."""
    path = P("lines", f"ladders_{season}_w{week}.csv")
    if not os.path.exists(path): return {}
    lad = pd.read_csv(path)
    if "PulledAt" not in lad:
        wk = P("lines", f"pulled_{season}_w{week}.txt")
        lad["PulledAt"] = open(wk).read().strip() if os.path.exists(wk) else None
    return {(norm_name(r.Player), r.Market, float(r.Rung)): (int(r.Odds), r.PulledAt) for r in lad.itertuples()}

def lock_published(leg, card):
    """Older cards predate the published_* fields: fill them from what the card showed at publish (never overwrite)."""
    if leg.get("published_odds") is None:
        pub = leg.get("odds_real") if leg.get("odds_real") is not None else leg.get("odds_est")
        at = card.get("published_at") or card.get("prices_pulled")
        leg.update(published_odds=pub, published_at=at, current_odds=leg.get("current_odds", pub),
                   current_at=leg.get("current_at", at))
    leg.setdefault("price_history", [dict(at=leg["published_at"], odds=leg["published_odds"])])

def refresh_card(card, prices, kick):
    moved = 0
    for leg in [l for t in card.get("tickets", []) for l in t["legs"]] + card.get("floors_singles", []):
        lock_published(leg, card)
        if leg.get("team") in kick: leg["kickoff"] = kick[leg["team"]]
        hit = prices.get((norm_name(leg["player"]), leg["market"], float(leg["rung"])))
        if not hit or not hit[1]: continue                                   # rung not on DK's ladder any more
        odds, at = hit
        cur = iso(leg.get("current_at"))
        if cur and iso(at) <= cur: continue                                  # not a newer pull
        if leg.get("kickoff") and iso(at) >= iso(leg["kickoff"]): continue   # pulled after kickoff: not a pregame price
        leg["current_odds"], leg["current_at"] = odds, at
        leg["price_history"].append(dict(at=at, odds=odds)); moved += 1
    card["current_at"] = max([l["current_at"] for t in card.get("tickets", []) for l in t["legs"]] or [card.get("current_at")],
                             key=lambda x: iso(x) or datetime.min.replace(tzinfo=timezone.utc))
    return moved

def flag_new_markets(path, key_rows, at_publish):
    if not os.path.exists(path): return 0
    d = json.load(open(path)); n = 0
    for r in d[key_rows]:
        r["posted_after_card"] = f"{norm_name(r['player'])}|{r['market']}" not in at_publish
        n += r["posted_after_card"]
    json.dump(d, open(path, "w"), **({"separators": (",", ":")} if key_rows == "players" else {"indent": 1}), allow_nan=False)
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which-slate", action="store_true")
    ap.add_argument("--season", type=int); ap.add_argument("--week", type=int); ap.add_argument("--slate")
    a = ap.parse_args()
    if a.which_slate:
        print(which_slate() or ""); return
    from floors import kickoffs
    card_path = P("cards", f"card_{a.season}_w{a.week}_{a.slate}.json")
    if not os.path.exists(card_path):
        print(f"no {a.slate} card yet for week {a.week}: legs/floors refreshed, nothing to lock or flag"); return
    card = json.load(open(card_path))
    moved = refresh_card(card, ladder_prices(a.season, a.week), kickoffs(a.season, a.week))
    json.dump(card, open(card_path, "w"), indent=1, allow_nan=False)
    at_publish = set(card.get("markets_at_publish") or [])
    flagged = (flag_new_markets(P("cards", f"legs_{a.season}_w{a.week}_{a.slate}.json"), "players", at_publish),
               flag_new_markets(P("floors", f"floors_{a.season}_w{a.week}_{a.slate}.json"), "rows", at_publish)) \
        if at_publish else ("-", "-")
    print(f"{a.slate} card: {moved} leg prices moved (pull {prices_pulled(a.season, a.week, a.slate)}); "
          f"posted after card: {flagged[0]} legs rows, {flagged[1]} floor rows")

if __name__ == "__main__":
    main()
