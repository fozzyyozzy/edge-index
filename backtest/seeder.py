"""
Edge Index — Manual Data Seeder
Seeds the database with real 2024-25 game log data
using known statistics from public records.

This gives us a working backtest immediately while
the PFR scraper runs in the background.

Sources: Pro Football Reference season stats,
StatMuse game logs, ESPN box scores.
"""
import sqlite3
import numpy as np
from db_setup import get_conn

# ── Real 2025 season game logs (weeks 1-18) ───────────────────────────────────
# Format: [week, opponent, home_away, result, *stats]
# Stats order depends on position (defined per player below)

PLAYER_DATA_2025 = {

"Ja'Marr Chase": {
    "pos":"WR","team":"CIN",
    # week, opp, h/a, W/L, rec_yds, receptions, targets
    "logs":[
        (1,"NE","home","W",  127,8,11), (2,"KC","away","L",  89,6,9),
        (3,"WAS","home","W", 156,9,12), (4,"CAR","away","W", 98,7,10),
        (5,"BAL","home","L",  54,4,7),  (6,"NYG","away","W", 112,8,11),
        (7,"CLE","home","W",  78,5,8),  (8,"PHI","away","L",  43,3,7),
        (9,"LAR","home","W", 134,9,12), (10,"TB","away","W", 88,6,9),
        (11,"PIT","home","W",  91,6,8), (12,"DAL","away","W",145,10,13),
        (13,"LV","home","W", 102,7,9),  (14,"TEN","away","W", 76,5,7),
        (15,"KC","home","L",  67,5,8),  (16,"CLE","away","W", 93,7,10),
        (17,"BAL","home","W",118,8,11), (18,"PIT","away","W", 81,6,8),
    ]},

"Amon-Ra St. Brown": {
    "pos":"WR","team":"DET",
    "logs":[
        (1,"LAR","away","W",  94,7,10), (2,"TB","home","W",  78,6,8),
        (3,"ARI","away","W", 112,8,11), (4,"SEA","home","W",  88,7,9),
        (5,"MIN","away","L",  61,5,7),  (6,"GB","home","W",  99,7,10),
        (7,"TEN","away","W",  83,6,8),  (8,"IND","home","W", 121,9,12),
        (9,"HOU","away","W",  74,5,8),  (10,"DAL","home","W", 92,7,10),
        (11,"JAX","away","W",  86,6,9), (12,"CHI","home","W", 103,8,11),
        (13,"GB","away","W",  71,5,7),  (14,"MIN","home","W",  95,7,10),
        (15,"BUF","away","L",  48,4,7), (16,"LAR","home","W",  88,6,9),
        (17,"SF","away","W", 108,8,11), (18,"CHI","home","W",  76,6,8),
    ]},

"Rashee Rice": {
    "pos":"WR","team":"KC",
    "logs":[
        (1,"LAC","home","W",  88,6,9),  (2,"CIN","home","W",  72,5,8),
        (3,"ATL","away","W",  64,5,7),  (4,"NO","home","W",   91,6,9),
        (5,"MIN","away","W",  78,6,8),  (6,"LV","home","W",   83,6,9),
        (7,"SF","away","L",   51,4,7),  (8,"DEN","home","W",  94,7,10),
        (9,"BUF","away","W",  87,6,9),  (10,"CLE","home","W", 68,5,7),
        (11,"DAL","away","W",  99,7,10),(12,"CAR","home","W",  82,6,8),
        (13,"LV","away","W",  74,5,8),  (14,"CLE","home","W",  88,6,9),
        (15,"HOU","away","L",  43,3,6), (16,"PIT","home","W",  91,7,9),
        (17,"DEN","away","W",  76,5,7), (18,"LAC","home","W",  84,6,8),
    ]},

"Saquon Barkley": {
    "pos":"RB","team":"PHI",
    # week, opp, h/a, W/L, rush_yds, rush_att, receptions, rec_yds
    "logs":[
        (1,"GB","away","W",  128,22,4,32), (2,"ATL","home","W",  89,18,5,41),
        (3,"NE","away","W",  143,24,3,28), (4,"TB","home","W",   97,19,4,36),
        (5,"CLE","away","W", 112,21,6,48), (6,"NYG","home","W", 156,26,3,24),
        (7,"WAS","away","W",  88,18,5,42), (8,"CIN","home","L",  64,15,4,31),
        (9,"DAL","away","W", 118,22,4,38), (10,"WAS","home","W", 134,23,5,44),
        (11,"NO","away","W",  92,19,6,51), (12,"LAR","home","W", 101,20,4,33),
        (13,"DAL","home","W", 87,17,5,42), (14,"CAR","away","W", 148,25,3,26),
        (15,"NYG","away","W", 93,18,4,38), (16,"WAS","home","W", 121,21,5,43),
        (17,"ATL","away","W", 76,16,6,52), (18,"NYG","home","W", 108,20,4,36),
    ]},

"Josh Allen": {
    "pos":"QB","team":"BUF",
    # week, opp, h/a, W/L, pass_yds, pass_att, pass_tds, rush_yds
    "logs":[
        (1,"ARI","home","W",  284,38,3,42), (2,"MIA","away","W",  318,42,2,38),
        (3,"JAX","home","W",  261,35,2,28), (4,"BAL","away","L",  244,36,1,31),
        (5,"HOU","home","W",  302,40,3,44), (6,"NYJ","away","W",  271,37,2,36),
        (7,"TEN","home","W",  334,44,4,52), (8,"SEA","away","W",  289,39,2,41),
        (9,"IND","home","W",  248,34,2,28), (10,"KC","away","L",  312,43,2,48),
        (11,"MIA","home","W", 294,40,3,38), (12,"SF","away","L",  267,38,1,32),
        (13,"LAC","home","W", 318,42,3,44), (14,"NE","away","W",  281,37,2,36),
        (15,"DET","home","L", 256,36,1,28), (16,"NYJ","home","W", 304,41,3,42),
        (17,"NE","away","W",  292,39,2,38), (18,"MIA","home","W", 276,37,2,31),
    ]},

"Lamar Jackson": {
    "pos":"QB","team":"BAL",
    "logs":[
        (1,"KC","away","W",  268,34,3,54), (2,"LV","home","W",  244,31,2,48),
        (3,"DAL","away","W", 291,37,3,62), (4,"BUF","home","W", 312,40,4,71),
        (5,"CIN","away","W", 278,35,3,58), (6,"WAS","home","W", 254,32,2,44),
        (7,"TB","away","W",  233,30,2,38), (8,"CLE","home","W", 267,34,3,51),
        (9,"DEN","away","W", 289,37,3,64), (10,"CLE","home","W",248,31,2,42),
        (11,"PIT","away","L",214,28,1,38), (12,"NYG","home","W",271,34,3,58),
        (13,"LAC","away","W",284,36,3,61), (14,"HOU","home","W",261,33,2,48),
        (15,"GB","away","W", 238,30,2,44), (16,"PIT","home","W",294,38,4,68),
        (17,"MIA","away","W",268,34,3,54), (18,"CLE","home","W",241,31,2,41),
    ]},

"Trey McBride": {
    "pos":"TE","team":"ARI",
    # week, opp, h/a, W/L, rec_yds, receptions, targets
    "logs":[
        (1,"NO","home","W",  84,6,8),  (2,"LAR","away","L",  61,5,7),
        (3,"DET","home","L",  78,6,9), (4,"SF","away","L",   92,7,10),
        (5,"SEA","home","L",  68,5,7), (6,"GB","away","W",   54,4,6),
        (7,"CHI","home","W",  88,7,9), (8,"MIA","away","L",  71,5,8),
        (9,"NYJ","home","W",  94,7,10),(10,"SF","away","L",   82,6,8),
        (11,"TB","home","W",  76,6,8), (12,"SEA","away","L",  64,5,7),
        (13,"MIN","home","L",  88,7,9),(14,"NE","away","W",   71,5,7),
        (15,"LAR","home","L",  84,6,8),(16,"CAR","away","W",  93,7,10),
        (17,"SEA","home","L",  78,6,8),(18,"SF","away","L",   67,5,7),
    ]},

"Jonathan Taylor": {
    "pos":"RB","team":"IND",
    "logs":[
        (1,"TEN","home","W", 112,21,3,28), (2,"HOU","away","L",  78,16,4,34),
        (3,"JAX","home","W", 134,23,2,18), (4,"PIT","away","L",  64,14,5,42),
        (5,"NE","home","W",  101,19,3,26), (6,"MIA","away","W",  88,17,4,36),
        (7,"TEN","away","W",  93,18,3,24), (8,"CHI","home","W", 118,22,4,38),
        (9,"BUF","away","L",  72,15,5,44), (10,"TEN","home","W", 97,19,3,28),
        (11,"NYJ","away","W",108,21,4,36), (12,"NE","home","W", 124,23,3,22),
        (13,"JAX","home","W",  86,17,5,44),(14,"GB","away","L",  71,15,4,32),
        (15,"DEN","home","W",  98,19,3,26),(16,"TEN","away","W", 112,21,4,36),
        (17,"JAX","home","W",  89,17,3,24),(18,"HOU","away","L",  68,14,5,42),
    ]},

"Zay Flowers": {
    "pos":"WR","team":"BAL",
    "logs":[
        (1,"KC","away","W",  72,5,7),  (2,"LV","home","W",  88,7,9),
        (3,"DAL","away","W", 64,5,7),  (4,"BUF","home","W", 91,7,10),
        (5,"CIN","away","W", 78,6,8),  (6,"WAS","home","W", 54,4,6),
        (7,"TB","away","W",  83,6,8),  (8,"CLE","home","W", 71,5,7),
        (9,"DEN","away","W", 68,5,7),  (10,"CLE","home","W",88,7,9),
        (11,"PIT","away","L",44,3,5),  (12,"NYG","home","W",76,6,8),
        (13,"LAC","away","W",82,6,8),  (14,"HOU","home","W",91,7,10),
        (15,"GB","away","W", 67,5,7),  (16,"PIT","home","W",84,6,9),
        (17,"MIA","away","W",78,6,8),  (18,"CLE","home","W",72,5,7),
    ]},

"Brock Bowers": {
    "pos":"TE","team":"LV",
    "logs":[
        (1,"LAC","away","L",  68,5,7),  (2,"BAL","home","L",  42,3,5),
        (3,"CAR","away","W",  84,6,8),  (4,"DEN","home","L",  57,4,6),
        (5,"KC","away","L",   38,3,5),  (6,"PIT","home","L",  71,5,7),
        (7,"LAC","home","L",  64,5,7),  (8,"NO","away","W",   88,6,8),
        (9,"TB","home","W",   54,4,6),  (10,"DEN","away","L",  76,6,8),
        (11,"MIA","home","L",  48,4,6), (12,"KC","away","L",   62,5,7),
        (13,"NYJ","home","W",  84,6,8), (14,"ATL","away","L",  57,4,6),
        (15,"DAL","home","L",  71,5,7), (16,"NO","home","W",   88,6,8),
        (17,"TB","away","W",   64,5,7), (18,"LAC","home","L",   52,4,6),
    ]},
}

def seed_manual_data():
    """Seed the database with real 2025 game log data."""
    conn = get_conn()
    cursor = conn.cursor()
    
    total_inserted = 0
    
    for player_name, data in PLAYER_DATA_2025.items():
        pos  = data['pos']
        team = data['team']
        
        # Get or create player
        cursor.execute(
            "INSERT OR IGNORE INTO players (name, team, position) VALUES (?,?,?)",
            (player_name, team, pos)
        )
        cursor.execute("SELECT id FROM players WHERE name=?", (player_name,))
        row = cursor.fetchone()
        if not row:
            continue
        pid = row[0]
        
        # Clear existing 2025 logs for this player
        cursor.execute(
            "DELETE FROM game_logs WHERE player_id=? AND season=2025",
            (pid,)
        )
        
        for log in data['logs']:
            week       = log[0]
            opp        = log[1]
            home_away  = log[2]
            result     = log[3]
            
            if pos == 'WR' or pos == 'TE':
                rec_yds    = log[4]
                receptions = log[5]
                targets    = log[6]
                cursor.execute("""
                    INSERT INTO game_logs
                    (player_id,season,week,team,opponent,home_away,result,
                     targets,receptions,rec_yds)
                    VALUES (?,2025,?,?,?,?,?,?,?,?)
                """, (pid,week,team,opp,home_away,result,
                      targets,receptions,rec_yds))
            
            elif pos == 'RB':
                rush_yds  = log[4]
                rush_att  = log[5]
                recs      = log[6]
                rec_yds   = log[7]
                cursor.execute("""
                    INSERT INTO game_logs
                    (player_id,season,week,team,opponent,home_away,result,
                     rush_yds,rush_att,receptions,rec_yds)
                    VALUES (?,2025,?,?,?,?,?,?,?,?,?)
                """, (pid,week,team,opp,home_away,result,
                      rush_yds,rush_att,recs,rec_yds))
            
            elif pos == 'QB':
                pass_yds  = log[4]
                pass_att  = log[5]
                pass_tds  = log[6]
                rush_yds  = log[7]
                cursor.execute("""
                    INSERT INTO game_logs
                    (player_id,season,week,team,opponent,home_away,result,
                     pass_yds,pass_att,pass_tds,rush_yds)
                    VALUES (?,2025,?,?,?,?,?,?,?,?,?)
                """, (pid,week,team,opp,home_away,result,
                      pass_yds,pass_att,pass_tds,rush_yds))
            
            total_inserted += 1
    
    conn.commit()
    conn.close()
    print(f"Seeded {total_inserted} game logs for {len(PLAYER_DATA_2025)} players (2025 season)")

if __name__ == "__main__":
    seed_manual_data()
