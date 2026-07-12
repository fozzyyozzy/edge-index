"""Tim's bailout-RB thesis: pass-catching RBs clear reception floors
MORE often vs good blitzing defenses (checkdowns/hot routes vs pressure).
Splits RB reception floors by receiving role x opponent blitz rate."""
import os, sqlite3
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DECAY = 0.85
def be(p): return f"{-100*p/(1-p):+.0f}" if p >= 0.5 else f"+{100*(1-p)/p:.0f}"

co = pd.read_csv(os.path.join(ROOT, "backtest", "nfl",
                              "NFL_Coaches_Schemes_2024_2026.csv"))
co = co.rename(columns={"Year": "season", "Team": "opponent"})
co["zone"] = co.Zone_vs_Man_Pct.str.split("/").str[0].astype(float)
co = co[["season", "opponent", "Blitz_Rate_Pct", "zone"]]

con = sqlite3.connect(os.path.join(ROOT, "backtest", "nfl", "edge_index.db"))
logs = pd.read_sql("""select gl.*, p.name, p.position from game_logs gl
    join players p on p.id=gl.player_id where p.position='RB'
    order by gl.player_id, gl.season, gl.week""", con)
logs = logs.drop_duplicates(subset=["player_id", "season", "week"])

rows = []
for pid, g in logs.groupby("player_id"):
    rec = g.receptions.fillna(0).values
    tgt = g.targets.fillna(0).values
    for i in range(len(rec)):
        h_rec, h_tgt = rec[max(0, i-16):i], tgt[max(0, i-16):i]
        if len(h_rec) < 7 or h_rec.mean() <= 0:
            continue
        w = DECAY ** np.arange(len(h_rec)-1, -1, -1); w /= w.sum()
        mu = float(w @ h_rec)
        if mu < 1.5:
            continue
        line = max(np.floor(0.6 * mu) - 0.5, 0.5)   # 0.6x-depth reception alt
        rows.append(dict(season=g.season.iloc[i], opponent=g.opponent.iloc[i],
                         name=g.name.iloc[i], mu=round(mu, 1), line=line,
                         tgt_role=float(np.mean(h_tgt[-7:])),
                         clear=int(rec[i] > line)))
df = pd.DataFrame(rows).merge(co, on=["season", "opponent"], how="inner")
df["role"] = pd.cut(df.tgt_role, [0, 2.5, 4, 99],
                    labels=["low-tgt RB", "mid", "bailout RB (4+ tgt)"])
df["blz"] = pd.cut(df.Blitz_Rate_Pct, [0, 22, 29, 100],
                   labels=["low-blitz", "mid", "high-blitz"])
print(f"{len(df)} RB player-weeks (0.6x-depth reception alt)\n")
g = df.groupby(["role", "blz"], observed=True).clear.agg(["size", "mean"])
g = g[g["size"] >= 25]; g["break_even"] = g["mean"].apply(be)
print(g.round(3).to_string())
print("\nzone-heavy vs man-heavy (bailout RBs only):")
b = df[df.role == "bailout RB (4+ tgt)"].copy()
b["cov"] = pd.cut(b.zone, [0, 64, 74, 101], labels=["man-heavy", "mixed", "zone-heavy"])
g2 = b.groupby("cov", observed=True).clear.agg(["size", "mean"])
g2 = g2[g2["size"] >= 20]; g2["break_even"] = g2["mean"].apply(be)
print(g2.round(3).to_string())
