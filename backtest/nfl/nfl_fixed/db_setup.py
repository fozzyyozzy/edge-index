"""Edge Index — DB Setup"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "edge_index.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, team TEXT, position TEXT, active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS game_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER, season INTEGER NOT NULL, week INTEGER NOT NULL,
            game_date TEXT, team TEXT, opponent TEXT, home_away TEXT, result TEXT,
            team_score INTEGER, opp_score INTEGER,
            pass_att INTEGER DEFAULT 0, pass_cmp INTEGER DEFAULT 0,
            pass_yds INTEGER DEFAULT 0, pass_tds INTEGER DEFAULT 0,
            interceptions INTEGER DEFAULT 0, rush_att INTEGER DEFAULT 0,
            rush_yds INTEGER DEFAULT 0, rush_tds INTEGER DEFAULT 0,
            targets INTEGER DEFAULT 0, receptions INTEGER DEFAULT 0,
            rec_yds INTEGER DEFAULT 0, rec_tds INTEGER DEFAULT 0,
            game_spread REAL, game_total REAL, snap_pct REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS prop_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER, season INTEGER NOT NULL, week INTEGER NOT NULL,
            prop_type TEXT NOT NULL, direction TEXT NOT NULL,
            line REAL NOT NULL, odds INTEGER NOT NULL, source TEXT DEFAULT 'estimated'
        );
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER, season INTEGER NOT NULL, week INTEGER NOT NULL,
            prop_type TEXT NOT NULL, direction TEXT NOT NULL,
            line REAL NOT NULL, odds INTEGER NOT NULL,
            actual_value REAL NOT NULL, hit INTEGER NOT NULL,
            model_prob REAL, streak_at_time INTEGER,
            l6_hit_rate REAL, l10_hit_rate REAL, floor_gap REAL, tier TEXT,
            wager REAL DEFAULT 100, pnl REAL
        );
    """)
    conn.commit()
    conn.close()
    print(f"DB ready: {DB_PATH}")

if __name__ == "__main__":
    init_db()
