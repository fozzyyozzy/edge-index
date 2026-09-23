"""
floors.py — floor scan for one slate. Opponents, game day, and spreads come from the nflverse schedule.
  python pipeline/floors.py --season 2026 --week 3 --slate sun --lines lines/dk_2026_w3_sun.csv
Writes floors_<season>_w<week>_<slate>.csv with: L10/L15 clear rate at the floor rung, est odds,
opponent-defense tag, own-volume tag, spread (for the blowout flag), and last 3.
Also writes floors_<season>_w<week>_<slate>.json for the site's Floor Lines tab (card.yml copies it to
cfb-app/public/data/nfl_floors_<slate>.json).
"""
import argparse, io, json, os, sys, urllib.request
from datetime import datetime, timezone
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from altline_engine import estimate_ladder
from common import norm_name, fetch_season, COL, load_real_ladders, P, prices_pulled

INV = {"rec_yds": "targets", "receptions": "targets", "pass_yds": "attempts", "pass_cmps": "attempts",
       "pass_att": "attempts", "rush_yds": "carries", "rush_att": "carries"}
SLATE_DAYS = {"tnf": {"Thursday"}, "sun": {"Sunday", "Saturday"}, "mnf": {"Monday"}}

def schedule(season, week):
    req = urllib.request.Request("https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv", headers={"User-Agent": "Mozilla/5.0"})
    g = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()), low_memory=False)
    return g[(g.season == season) & (g.week == week)]

def kickoffs(season, week):
    """{team: kickoff as UTC ISO} for the week, from the nflverse schedule (gameday + gametime are Eastern)."""
    from zoneinfo import ZoneInfo
    out = {}
    for g in schedule(season, week).itertuples():
        if not isinstance(g.gametime, str): continue
        t = datetime.fromisoformat(f"{g.gameday}T{g.gametime}").replace(tzinfo=ZoneInfo("America/New_York"))
        iso = t.astimezone(timezone.utc).isoformat(timespec="minutes")
        out[g.home_team] = out[g.away_team] = iso
    return out

def team_split(df, by):
    return (df.groupby([by, "season", "week"]).agg(pass_yds=("passing_yards", "sum"), rush_yds=("rushing_yards", "sum"),
                                                     pass_att=("attempts", "sum"), rush_att=("carries", "sum")).reset_index())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", required=True); ap.add_argument("--lines", required=True); ap.add_argument("--ladders", default=None, help="ladders CSV from fetch_lines.py; real prices override estimates"); ap.add_argument("--out")
    ap.add_argument("--w26", type=float, default=None, help="weight on current-season splits; default = games_played/8 capped at .6")
    a = ap.parse_args()
    out = a.out or P("floors", f"floors_{a.season}_w{a.week}_{a.slate}.csv")

    w = pd.concat([fetch_season(y) for y in (a.season - 2, a.season - 1, a.season)])
    cur = w[w.season == a.season]; gp = cur.week.nunique() if len(cur) else 0
    w26 = a.w26 if a.w26 is not None else min(0.6, gp / 8)          # trust current season more as it accrues
    prev = w[w.season == a.season - 1]

    d_prev = team_split(prev, "opponent_team").groupby("opponent_team").mean(numeric_only=True)
    o_prev = team_split(prev, "team").groupby("team").mean(numeric_only=True)
    if gp:
        d_cur = team_split(cur, "opponent_team").groupby("opponent_team").mean(numeric_only=True)
        o_cur = team_split(cur, "team").groupby("team").mean(numeric_only=True)
        D = (1 - w26) * d_prev + w26 * d_cur.reindex(d_prev.index).fillna(d_prev)
        O = (1 - w26) * o_prev + w26 * o_cur.reindex(o_prev.index).fillna(o_prev)
    else:
        D, O = d_prev, o_prev

    def tag(series, team):
        r = series.rank(ascending=False); x = r.get(team)
        return "?" if x is None or pd.isna(x) else ("SOFT" if x <= 8 else "TOUGH" if x >= 25 else "neutral")

    sch = schedule(a.season, a.week); sch = sch[sch.weekday.isin(SLATE_DAYS[a.slate])]
    OPP, SPREAD = {}, {}
    for g in sch.itertuples():
        OPP[g.away_team] = g.home_team; OPP[g.home_team] = g.away_team
        SPREAD[g.home_team] = -g.spread_line; SPREAD[g.away_team] = g.spread_line   # negative = favored
    team_now = cur.groupby("key")["team"].last() if gp else prev.groupby("key")["team"].last()
    team_prev = prev.groupby("key")["team"].last()

    REAL = load_real_ladders(a.ladders or a.lines.replace("dk_", "ladders_").rsplit("_", 1)[0] + ".csv")
    lines = pd.read_csv(a.lines); rows = []
    for r in lines.itertuples():
        key = norm_name(r.Player); col = COL[r.Market]; inv = INV[r.Market]
        g = w[(w.key == key) & (w[inv].fillna(0) > 0)].sort_values(["season", "week"])
        v = g[col].fillna(0).to_numpy()
        if len(v) < 10: continue
        tm = team_now.get(key); opp = OPP.get(tm)
        if opp is None: continue
        ladder = REAL.get((key, r.Market)) or estimate_ladder(r.Market, float(r.Line), int(r.Odds))[0]
        best = None
        for t, o in sorted(ladder):
            if o < -600: continue
            l10 = (v[-10:] >= t).mean(); l15 = (v[-15:] >= t).mean()
            if l10 >= 0.8 and l15 >= 0.73: best = (t, o, l10, l15)
        if not best: continue
        t, o, l10, l15 = best
        streak = 0
        for x in v[::-1]:                                         # consecutive clears, most recent game backwards
            if x < t: break
            streak += 1
        cat = "pass" if r.Market in ("pass_yds", "pass_cmps", "pass_att", "rec_yds", "receptions") else "rush"
        rows.append(dict(Player=r.Player, Team=tm, Opp=opp, Market=r.Market, Main=r.Line, MainOdds=r.Odds, Rung=f"{t:g}+",
                         EstOdds=o, L10=f"{int(round(l10*10))}/10", L15=f"{int(round(l15*15))}/15",
                         OppD=tag(D[cat + "_yds"], opp), OwnVol=tag(O[cat + "_att"], tm), Spread=SPREAD.get(tm),
                         TeamChange=bool(team_prev.get(key) and team_prev.get(key) != tm), PrevTeam=team_prev.get(key, ""),
                         Last3=[int(x) for x in v[-3:]],    # plain ints: np.int64 wrote "np.int64(126)" into the CSV
                         Pos=g.position.iloc[-1], Games=int(len(v)), Avg10=round(float(v[-10:].mean()), 1), Streak=streak,
                         Real=(key, r.Market) in REAL))
    df = pd.DataFrame(rows)
    if len(df):
        df["score"] = df.L10.str.split("/").str[0].astype(int) + (df.OppD == "SOFT") - 2 * (df.OppD == "TOUGH") - (df.OwnVol == "TOUGH")
        df = df.sort_values(["score", "EstOdds"], ascending=[False, False]).drop(columns="score")
    df.to_csv(out, index=False)
    write_site_json(df, a, out.rsplit(".", 1)[0] + ".json")
    print(f"wrote {out}: {len(df)} floor legs  (current-season weight {w26:.2f}, {gp} wk played)")

def american(p):
    """probability -> fair American odds (no vig)"""
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))

def write_site_json(df, a, path):
    rows = []
    for r in df.itertuples():
        l10 = int(r.L10.split("/")[0]) / 10; l15 = int(r.L15.split("/")[0]) / 15
        clear = 0.6 * l10 + 0.4 * l15                              # same blend grade_legs.py grades on
        o = int(r.EstOdds)
        rows.append(dict(player=r.Player, team=r.Team, opp=r.Opp, pos=r.Pos, market=r.Market, rung=float(r.Rung.rstrip("+")),
                         odds=o, real=bool(r.Real), main_line=float(r.Main), main_odds=int(r.MainOdds),
                         l10=r.L10, l15=r.L15, clear_pct=round(100 * clear, 1),
                         implied_pct=round(100 * (-o / (-o + 100) if o < 0 else 100 / (o + 100)), 1),
                         fair_odds=american(min(clear, 0.99)) if clear > 0 else None,
                         avg10=float(r.Avg10), streak=int(r.Streak), games=int(r.Games), last3=list(r.Last3),
                         opp_d=r.OppD, own_vol=r.OwnVol, spread=None if pd.isna(r.Spread) else float(r.Spread),
                         team_change=bool(r.TeamChange), prev_team=r.PrevTeam if isinstance(r.PrevTeam, str) and r.PrevTeam else None))
    meta = dict(season=a.season, week=a.week, slate=a.slate, generated=datetime.now(timezone.utc).isoformat(timespec="minutes"),
                prices_pulled=prices_pulled(a.season, a.week, a.slate))
    json.dump(dict(meta=meta, rows=rows), open(path, "w"), indent=1, allow_nan=False)
    print(f"wrote {path}")

if __name__ == "__main__":
    main()
