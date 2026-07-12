"""Do high-floor players clear below-expectation alt depths more often
than generic pricing assumes? Tests Tim's alt-line strategy from the
distribution side (game logs are clean; no odds needed)."""
import sqlite3, numpy as np, pandas as pd
import os
DB=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","backtest/nfl","edge_index.db")
DECAY=0.85
def be_odds(p): return -100*p/(1-p) if p>=0.5 else 100*(1-p)/p
con=sqlite3.connect(DB)
logs=pd.read_sql("""select gl.*,p.name,p.position from game_logs gl
  join players p on p.id=gl.player_id order by gl.player_id,gl.season,gl.week""",con)
rows=[]
for stat in ("rec_yds","receptions","rush_yds"):
    for pid,g in logs.groupby("player_id"):
        v=g[stat].fillna(0).values; snap=g["snap_pct"].fillna(0).values
        pos=g["position"].iloc[0]
        for i in range(len(v)):
            hist=v[max(0,i-16):i]          # up to 16 prior games
            if len(hist)<7 or hist.mean()<=0: continue
            w=DECAY**np.arange(len(hist)-1,-1,-1); w/=w.sum()
            mu=float(w@hist)
            if (stat=="rec_yds" and mu<25) or (stat=="receptions" and mu<3) or (stat=="rush_yds" and mu<30):
                continue                    # only real roles, like Tim bets
            cv=hist[-7:].std()/max(hist[-7:].mean(),1e-9)   # role volatility
            for r in (0.5,0.6,0.7,0.8):
                line=np.floor(r*mu*2)/2+0.5 if stat!="receptions" else max(np.floor(r*mu)-0.5,0.5)
                streak=int((hist[-7:]>line).sum())          # cleared depth k of last 7
                rows.append(dict(stat=stat,pos=pos,depth=r,mu=mu,cv=cv,
                    streak=streak,clear=int(v[i]>line)))
df=pd.DataFrame(rows)
print(f"{len(df)} player-week-depth observations (roles only)\n")
print("== clear rate by depth (all roles) ==")
g=df.groupby(["stat","depth"]).clear.agg(["size","mean"])
g["break_even"]=g["mean"].apply(lambda p: f"{be_odds(p):+.0f}")
print(g.round(3).to_string())
print("\n== does STABILITY matter? (low-cv = steady role, at depth 0.6) ==")
d=df[df.depth==0.6].copy(); d["stable"]=pd.qcut(d.cv,3,labels=["steady","mid","volatile"])
g=d.groupby(["stat","stable"],observed=True).clear.agg(["size","mean"])
g["break_even"]=g["mean"].apply(lambda p: f"{be_odds(p):+.0f}")
print(g.round(3).to_string())
print("\n== does the STREAK add info beyond the average? (depth 0.6) ==")
d["sbin"]=pd.cut(d.streak,[-1,4,5,6,7],labels=["<=4/7","5/7","6/7","7/7"])
g=d.groupby(["stat","sbin"],observed=True).clear.agg(["size","mean"])
g["break_even"]=g["mean"].apply(lambda p: f"{be_odds(p):+.0f}")
print(g.round(3).to_string())
