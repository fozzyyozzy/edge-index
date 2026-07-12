"""
Edge Index — OddsPapi WebSocket Live Feed
Streams live prop line changes during the season.
Run Thursday mornings to capture opening lines
and track line movement through game time.

Usage:
  export ODDS_API_KEY=your_key
  python propodds_ws.py --week 1 --season 2026
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import sqlite3
import argparse
import threading
from datetime import datetime
from db_setup import get_conn

API_KEY = os.environ.get("ODDS_API_KEY", "")
WS_URL  = "wss://v5.oddspapi.io/ws"

PROP_MARKET_MAP = {
    "player_receiving_yards": "rec_yds",
    "player_receptions":      "receptions",
    "player_rushing_yards":   "rush_yds",
    "player_passing_yards":   "pass_yds",
    "player_passing_attempts":"pass_att",
    "receiving_yards":        "rec_yds",
    "rushing_yards":          "rush_yds",
    "passing_yards":          "pass_yds",
    "receptions":             "receptions",
}

def build_name_map(conn):
    rows = conn.execute("SELECT id, name FROM players").fetchall()
    m = {}
    for pid, name in rows:
        m[name.lower()] = pid
        m[name.split()[-1].lower()] = pid
    return m

def run_ws(week, season):
    """Connect to WebSocket and capture prop line updates."""
    try:
        import websocket
    except ImportError:
        print("Install websocket-client: pip install websocket-client")
        return

    conn     = get_conn()
    name_map = build_name_map(conn)
    captured = {"count": 0, "lines": []}
    lock     = threading.Lock()

    def on_open(ws):
        print(f"Connected. Authenticating...")
        ws.send(json.dumps({
            "type":   "login",
            "apiKey": API_KEY,
        }))

    def on_message(ws, message):
        try:
            msg = json.loads(message)
            msg_type = msg.get("type") or msg.get("channel", "")

            if msg_type == "login":
                print(f"Auth: {msg.get('status','OK')}")
                # Subscribe to NFL odds channel
                ws.send(json.dumps({
                    "type":    "subscribe",
                    "channel": "odds",
                    "filters": {
                        "sport":    "americanfootball",
                        "markets":  list(PROP_MARKET_MAP.keys()),
                    }
                }))
                print("Subscribed to NFL prop odds stream")

            elif msg_type in ("odds", "odds_update"):
                data   = msg.get("data", {})
                market = str(data.get("market","")).lower()
                prop   = None

                for api_name, our_name in PROP_MARKET_MAP.items():
                    if api_name in market:
                        prop = our_name
                        break

                if not prop:
                    return

                player = str(data.get("participant") or
                             data.get("player","")).lower()
                pid    = name_map.get(player) or \
                         name_map.get(player.split()[-1] if player else "")

                if not pid:
                    return

                label  = str(data.get("label","")).lower()
                line   = data.get("line") or data.get("handicap")
                odds   = data.get("american") or data.get("odds")

                if not line or not odds:
                    return

                direction = "OVER" if "over" in label else \
                            "UNDER" if "under" in label else None
                if not direction:
                    return

                record = {
                    "player_id": pid,
                    "season":    season,
                    "week":      week,
                    "prop_type": prop,
                    "direction": direction,
                    "line":      float(line),
                    "odds":      int(float(odds)),
                    "source":    "live_ws_oddspapi",
                    "timestamp": datetime.now().isoformat(),
                }

                with lock:
                    captured["lines"].append(record)
                    captured["count"] += 1

                    # Batch write every 50 records
                    if captured["count"] % 50 == 0:
                        flush_to_db(conn, captured["lines"])
                        print(f"  Captured {captured['count']} prop updates")
                        captured["lines"] = []

        except Exception as e:
            print(f"Message error: {e}")

    def on_close(ws, code, msg):
        print(f"\nConnection closed ({code})")
        # Final flush
        if captured["lines"]:
            flush_to_db(conn, captured["lines"])
        print(f"Total prop updates captured: {captured['count']}")
        conn.close()

    def on_error(ws, error):
        print(f"WebSocket error: {error}")

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_close=on_close,
        on_error=on_error,
    )

    print(f"Connecting to OddsPapi WebSocket...")
    print(f"Capturing Week {week}, Season {season} prop lines")
    print(f"Press Ctrl+C to stop\n")

    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except KeyboardInterrupt:
        ws.close()

def flush_to_db(conn, lines):
    """Write captured lines to DB."""
    cursor = conn.cursor()
    for r in lines:
        cursor.execute("""
            INSERT OR REPLACE INTO prop_lines
            (player_id, season, week, prop_type, direction, line, odds, source)
            VALUES (?,?,?,?,?,?,?,?)
        """, (r["player_id"], r["season"], r["week"],
              r["prop_type"],  r["direction"],
              r["line"],       r["odds"], r["source"]))
    conn.commit()

if __name__ == "__main__":
    if not API_KEY:
        print("Set ODDS_API_KEY environment variable first.")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--week",   type=int, required=True)
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()

    run_ws(args.week, args.season)
