"""Does the matchup change steady-role floor clear rates? Joins the
coaches/scheme CSV to the floor study. 2024-25 games only."""
import sqlite3, numpy as np, pandas as pd
import os
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..")
DECAY=0.85
def be(p): return f"{-100*p/(1-p):+.0f}" if p>=0.5 else f"+{100*(1-p)/p:.0f}"
co=pd.read_csv(f"{ROOT}/backtest/nfl/NFL_Coaches_Schemes_2024_2026.csv")
co["zone"]=co.Zone_vs_Man_Pct.str.split("/").str[0].astype(float)
co=co.rename(columns={"Year":"season","Team":"opponent"})
co=co[["season","opponent","zone","Blitz_Rate_Pct","Slot_Corner_Grade","Defensive_Coordinator"]]
con=sqlite3.connect(f"{ROOT}/backtest/nfl/edge_index.db")
logs=pd.read_sql("""select gl.*,p.name,p.position from game_logs gl
  join players p on p.id=gl.player_id order by gl.player_id,gl.season,gl.week""",con)
print("opponent abbrevs not in coach csv:", sorted(set(logs.opponent.dropna())-set(co.opponent)))
rows=[]
for stat,minmu in (("rec_yds",25),("receptions",3),("rush_yds",30)):
    for pid,g in logs.groupby("player_id"):
        v=g[stat].fillna(0).values
        for i in range(len(v)):
            hist=v[max(0,i-16):i]
            if len(hist)<7 or hist.mean()<=0: continue
            w=DECAY**np.arange(len(hist)-1,-1,-1); w/=w.sum()
            mu=float(w@hist)
            if mu<minmu: continue
            cv=hist[-7:].std()/max(hist[-7:].mean(),1e-9)
            if cv>0.55: continue                     # steady-ish roles only
            line=np.floor(0.6*mu*2)/2+0.5 if stat!="receptions" else max(np.floor(0.6*mu)-0.5,0.5)
            rows.append(dict(stat=stat,pos=g.position.iloc[0],season=g.season.iloc[i],
                opponent=g.opponent.iloc[i],clear=int(v[i]>line)))
df=pd.DataFrame(rows)
df=df.merge(co,on=["season","opponent"],how="inner")
print(f"\n{len(df)} steady-role player-weeks joined to scheme data (depth 0.6)\n")
df["cov"]=pd.cut(df.zone,[0,64,74,101],labels=["man-heavy","mixed","zone-heavy"])
df["blz"]=pd.cut(df.Blitz_Rate_Pct,[0,22,29,100],labels=["low-blitz","mid","high-blitz"])
for seg,lab in (("cov","coverage"),("blz","blitz rate")):
    print(f"== clear rate by {lab} (receiving: WR/TE/RB rec; rushing separate) ==")
    m=df[df.stat!="rush_yds"].groupby(["stat","pos",seg],observed=True).clear.agg(["size","mean"])
    m=m[m["size"]>=40]; m["break_even"]=m["mean"].apply(be)
    print(m.round(3).to_string())
    if seg=="blz":
        r=df[df.stat=="rush_yds"].groupby(["pos",seg],observed=True).clear.agg(["size","mean"])
        r=r[r["size"]>=40]; r["break_even"]=r["mean"].apply(be)
        print(r.round(3).to_string())
    print()
# slot corner grade for WR receptions/yds
w=df[(df.pos=="WR")].copy()
w["slotq"]=pd.cut(w.Slot_Corner_Grade,[0,68,76,100],labels=["weak-slot","avg","elite-slot"])
m=w.groupby(["stat","slotq"],observed=True).clear.agg(["size","mean"])
m=m[m["size"]>=40]; m["break_even"]=m["mean"].apply(be)
print("== WR clear rate vs opponent slot corner quality =="); print(m.round(3).to_string())
# worst DCs to face (min 30 obs, receiving stats)
d=df[df.stat!="rush_yds"].groupby("Defensive_Coordinator").clear.agg(["size","mean"])
d=d[d["size"]>=45].sort_values("mean")
print("\n== toughest/softest DCs for steady-role receiving floors ==")
print(pd.concat([d.head(5),d.tail(5)]).round(3).to_string())
