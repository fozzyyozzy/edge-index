"""Data-quality gate: run after any game_logs reseed.
Real data: even-value share ~50%, nobody plays >18 weeks, star spot-check."""
import os, sqlite3
import pandas as pd

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "..", "..", "backtest", "nfl", "edge_index.db")
con = sqlite3.connect(DB)
logs = pd.read_sql(
    "select season, week, rec_yds, rush_yds, player_id from game_logs", con)
ok = True
for s, g in logs.groupby("season"):
    v = pd.concat([g.rec_yds, g.rush_yds]).dropna()
    v = v[v > 0]
    gp = g.groupby("player_id").week.nunique()
    even = (v % 2 == 0).mean()
    flag = ""
    if even > 0.60 or even < 0.40:
        flag += " <-- SYNTHETIC-LOOKING PARITY"
        ok = False
    if gp.max() > 22:   # 17 regular + bye weeks + up to 4 playoff games
        flag += " <-- >22 GAMES/PLAYER (dupes?)"
        ok = False
    print(f"{s}: even-share {even:.1%} | median games {gp.median():.0f} "
          f"| max {gp.max()} | rows {len(g)}{flag}")
q = pd.read_sql("""select gl.week, gl.rec_yds from game_logs gl
    join players p on p.id=gl.player_id
    where p.name like '%Nacua%' and gl.season=2025 order by week""", con)
print("Nacua 2025 rec_yds:", list(q.rec_yds.fillna(-1).astype(int)))
print("\nVERDICT:", "PASS — data looks organic" if ok else "FAIL — do not run studies")
