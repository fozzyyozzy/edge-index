"""
Diagnostic — see exactly what The Odds API returns for one game.
Run this to debug the 0 lines issue.

  python diagnose_api.py
"""
import sys, os, requests, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY  = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT    = "americanfootball_nfl"

def get(endpoint, params):
    p = {"apiKey": API_KEY}
    p.update(params)
    r = requests.get(f"{BASE_URL}{endpoint}", params=p, timeout=20)
    print(f"  HTTP {r.status_code}")
    print(f"  Credits remaining: {r.headers.get('x-requests-remaining','?')}")
    print(f"  Credits used:      {r.headers.get('x-requests-last','?')}")
    return r

# ── Step 1: Get Week 1 2024 events ───────────────────────────────────────────
print("=" * 60)
print("STEP 1: Get NFL events for Week 1 2024")
print("=" * 60)

r = get(f"/historical/sports/{SPORT}/events", {
    "date":       "2024-09-08T18:00:00Z",
    "dateFormat": "iso",
})

if r.status_code != 200:
    print(f"ERROR: {r.text}")
    sys.exit(1)

data     = r.json()
events   = data.get("data", [])
snapshot = data.get("timestamp","")
print(f"\nSnapshot timestamp: {snapshot}")
print(f"Events found: {len(events)}")

if not events:
    print("No events — try different date")
    sys.exit(1)

# Show first 3 events
print("\nFirst 3 events:")
for e in events[:3]:
    print(f"  {e.get('id')} | {e.get('away_team')} @ {e.get('home_team')} | {e.get('commence_time','')[:16]}")

# ── Step 2: Pull odds for first event ────────────────────────────────────────
first_event = events[0]
event_id    = first_event.get("id")
kickoff     = first_event.get("commence_time","")
away        = first_event.get("away_team","")
home        = first_event.get("home_team","")

print(f"\n{'='*60}")
print(f"STEP 2: Pull prop odds for {away} @ {home}")
print(f"Event ID: {event_id}")
print(f"Kickoff:  {kickoff}")
print(f"{'='*60}")

# Try multiple timestamps to find when props were available
from datetime import datetime, timedelta
kickoff_dt = datetime.fromisoformat(kickoff[:19].replace('Z',''))

timestamps_to_try = [
    ("48hrs before kickoff", (kickoff_dt - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")),
    ("24hrs before kickoff", (kickoff_dt - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")),
    ("6hrs before kickoff",  (kickoff_dt - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")),
    ("1hr before kickoff",   (kickoff_dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")),
]

working_timestamp = None
for label, ts in timestamps_to_try:
    print(f"\nTrying {label} ({ts})...")
    r2 = get(f"/historical/sports/{SPORT}/events/{event_id}/odds", {
        "date":       ts,
        "regions":    "us",
        "markets":    "player_reception_yds",
        "oddsFormat": "american",
    })

    if r2.status_code == 200:
        d2        = r2.json()
        game_data = d2.get("data", {})
        books     = game_data.get("bookmakers", [])
        print(f"  Bookmakers returned: {len(books)}")

        # Historical event odds wraps response in {timestamp, data: {bookmakers}}
        if isinstance(r2.json().get("data"), dict):
            books = r2.json()["data"].get("bookmakers", [])
        if books:
            working_timestamp = ts
            for bm in books[:2]:
                markets = bm.get("markets", [])
                print(f"  Book: {bm.get('key')} — {len(markets)} markets")
                for m in markets[:1]:
                    outcomes = m.get("outcomes", [])
                    print(f"    Market: {m.get('key')} — {len(outcomes)} outcomes")
                    for o in outcomes[:3]:
                        print(f"      {o.get('description','?')} {o.get('name','?')} {o.get('point','?')} @ {o.get('price','?')}")
            break
        else:
            print(f"  No bookmakers at this timestamp")
    else:
        print(f"  Response: {r2.text[:200]}")

# ── Step 3: If nothing worked, check what markets ARE available ───────────────
if not working_timestamp:
    print(f"\n{'='*60}")
    print("STEP 3: Check available markets for this event")
    print(f"{'='*60}")

    # Try h2h to confirm event is accessible at all
    r3 = get(f"/historical/sports/{SPORT}/events/{event_id}/odds", {
        "date":       timestamps_to_try[1][1],  # 24hrs before
        "regions":    "us",
        "markets":    "h2h",
        "oddsFormat": "american",
    })
    print(f"\nh2h market test:")
    if r3.status_code == 200:
        d3    = r3.json()
        books = d3.get("data",{}).get("bookmakers",[])
        print(f"  Books with h2h: {len(books)}")
        print(f"  This confirms event ID is valid")
        print(f"\n  Issue: player props may need different market keys")
        print(f"  or props weren't available at the timestamps tried")
    else:
        print(f"  {r3.text[:200]}")

print(f"\n{'='*60}")
print("DIAGNOSIS COMPLETE")
print("Paste this full output and we'll fix the loader.")
print(f"{'='*60}")
