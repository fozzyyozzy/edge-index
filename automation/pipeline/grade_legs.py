"""
grade_legs.py — emits legs_<slate>.json: EVERY DK rung for every player on the slate, with an A+..F grade,
for the site's Legs tab and slip builder. Runs after floors.py (needs its matchup tags) in the card workflow.

  python pipeline/grade_legs.py --season 2026 --week 3 --slate sun --lines lines/dk_2026_w3_sun.csv

Grade = how often this rung HITS: 0.6*L10 + 0.4*L15 clear rate (recent form weighted, full sample respected). Not a value grade.
  A+  >= 90%   A  >= 85%   A-  >= 80%   B  70-79   C  60-69   D  < 60   F  hard hold
Modifiers (one step each, applied after the base letter, floor at D unless hard hold):
  +  last 3 all clear                  -  any of last 3 within 1 yard/1 unit of the rung (a "near miss" signal)
  -  est price worse than -400         -  one soft flag (opp D TOUGH or own volume TOUGH); both soft flags = two steps
  F  hard hold: team change this season, attempt prop with team favored >= 7, fewer than 10 games of data
"""
import argparse, io, json, os, sys, urllib.request
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from altline_engine import estimate_ladder, implied_prob
from common import norm_name, fetch_season, COL, load_real_ladders, P
from floors import INV, SLATE_DAYS, schedule, team_split

LETTERS = ["F", "D", "C", "B", "A-", "A", "A+"]
def base_letter(p):
    return "A+" if p >= .90 else "A" if p >= .85 else "A-" if p >= .80 else "B" if p >= .70 else "C" if p >= .60 else "D"
def step(letter, n):
    i = max(1, min(len(LETTERS) - 1, LETTERS.index(letter) + n)); return LETTERS[i]
NEAR = {"rec_yds": 3, "rush_yds": 3, "pass_yds": 10, "receptions": 0, "pass_cmps": 1, "pass_att": 1, "rush_att": 1}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", required=True); ap.add_argument("--lines", required=True); ap.add_argument("--ladders", default=None, help="ladders CSV from fetch_lines.py; real prices override estimates")
    a = ap.parse_args()

    w = pd.concat([fetch_season(y) for y in (a.season - 2, a.season - 1, a.season)])
    cur = w[w.season == a.season]; prev = w[w.season == a.season - 1]; gp = cur.week.nunique() if len(cur) else 0
    w26 = min(0.6, gp / 8)
    d_prev = team_split(prev, "opponent_team").groupby("opponent_team").mean(numeric_only=True)
    o_prev = team_split(prev, "team").groupby("team").mean(numeric_only=True)
    if gp:
        d_cur = team_split(cur, "opponent_team").groupby("opponent_team").mean(numeric_only=True)
        o_cur = team_split(cur, "team").groupby("team").mean(numeric_only=True)
        D = (1 - w26) * d_prev + w26 * d_cur.reindex(d_prev.index).fillna(d_prev)
        O = (1 - w26) * o_prev + w26 * o_cur.reindex(o_prev.index).fillna(o_prev)
    else: D, O = d_prev, o_prev
    def tag(series, team):
        r = series.rank(ascending=False); x = r.get(team)
        return "?" if x is None or pd.isna(x) else ("SOFT" if x <= 8 else "TOUGH" if x >= 25 else "neutral")
    sch = schedule(a.season, a.week); sch = sch[sch.weekday.isin(SLATE_DAYS[a.slate])]
    OPP, SPREAD, GAME = {}, {}, {}
    for g in sch.itertuples():
        OPP[g.away_team] = g.home_team; OPP[g.home_team] = g.away_team
        SPREAD[g.home_team] = -g.spread_line; SPREAD[g.away_team] = g.spread_line
        GAME[g.away_team] = GAME[g.home_team] = f"{g.away_team}@{g.home_team}"
    team_now = cur.groupby("key")["team"].last() if gp else prev.groupby("key")["team"].last()
    team_prev = prev.groupby("key")["team"].last()

    REAL = load_real_ladders(a.ladders or a.lines.replace("dk_", "ladders_").rsplit("_", 1)[0] + ".csv")
    lines = pd.read_csv(a.lines); out = []
    for r in lines.itertuples():
        key = norm_name(r.Player); col = COL[r.Market]; inv = INV[r.Market]
        g = w[(w.key == key) & (w[inv].fillna(0) > 0)].sort_values(["season", "week"])
        v = g[col].fillna(0).to_numpy(); tm = team_now.get(key); opp = OPP.get(tm)
        if opp is None: continue
        cat = "pass" if r.Market in ("pass_yds", "pass_cmps", "pass_att", "rec_yds", "receptions") else "rush"
        oppd, vol = tag(D[cat + "_yds"], opp), tag(O[cat + "_att"], tm)
        spread = SPREAD.get(tm)
        holds = []
        if len(v) < 10: holds.append("fewer than 10 games")
        if team_prev.get(key) and tm and team_prev.get(key) != tm: holds.append(f"team change ({team_prev.get(key)}->{tm})")
        if r.Market in ("pass_att", "pass_cmps") and spread is not None and spread <= -7: holds.append(f"blowout risk (fav by {-spread:g})")
        ladder = REAL.get((key, r.Market)) or estimate_ladder(r.Market, float(r.Line), int(r.Odds))[0]
        rungs = []; real = (key, r.Market) in REAL
        for t, o in sorted(ladder):
            if len(v) < 10:
                rungs.append(dict(rung=t, est_odds=o, grade="F", reasons=holds)); continue
            l10 = float((v[-10:] >= t).mean()); l15 = float((v[-15:] >= t).mean())
            p = 0.6 * l10 + 0.4 * l15; letter = base_letter(p); why = []
            last3 = v[-3:]
            if holds: letter = "F"; why = holds
            else:
                if (last3 >= t).all(): letter = step(letter, +1); why.append("last 3 all clear")
                if any(0 <= t - x <= NEAR[r.Market] for x in last3): letter = step(letter, -1); why.append("near miss in last 3")
                if o < -600: letter = step(letter, -2); why.append("juice past -600: not playable in a parlay")
                elif o < -400: letter = step(letter, -1); why.append("price worse than -400")
                soft = (oppd == "TOUGH") + (vol == "TOUGH")
                if soft: letter = step(letter, -soft); why.append("; ".join(x for x in ("opp D tough" if oppd == "TOUGH" else "", "own volume low" if vol == "TOUGH" else "") if x))
            rungs.append(dict(rung=t, est_odds=o, implied_pct=round(100 * implied_prob(o), 1), l10=f"{int(round(l10*10))}/10",
                              l15=f"{int(round(l15*15))}/15", clear_pct=round(100 * p, 1), grade=letter, reasons=why))
        out.append(dict(player=r.Player, pos=(g.position.iloc[-1] if len(g) else None), team=tm, opp=opp, game=GAME.get(tm), market=r.Market, main_line=float(r.Line), prices="real" if real else "estimated",
                        main_odds=int(r.Odds), opp_d=oppd, own_vol=vol, spread=spread, games=int(len(v)),
                        last3=[float(x) for x in v[-3:]], rungs=rungs))
    # trim: keep C and up; held players (all F) keep the 3 rungs nearest the main line so the hold reason still shows
    KEEP = {"A+", "A", "A-", "B", "C"}
    trimmed = []
    for p in out:
        good = [r for r in p["rungs"] if r["grade"] in KEEP]
        if good:
            p["rungs"] = good
        elif p["rungs"] and all(r["grade"] == "F" for r in p["rungs"]):
            p["rungs"] = sorted(p["rungs"], key=lambda r: abs(r["rung"] - p["main_line"]))[:3]
            p["rungs"].sort(key=lambda r: r["rung"]); p["held"] = True
        else:
            continue
        trimmed.append(p)
    out = trimmed
    meta = dict(season=a.season, week=a.week, slate=a.slate, generated=pd.Timestamp.now(tz='UTC').isoformat(),
                grade_key="Grade = how often this rung hits (60% last-10 + 40% last-15 clear rate, with form/price/matchup modifiers). It says nothing about whether the price is good. A+>=90 A>=85 A->=80 B 70-79 C 60-69 D<60 F=hard hold.",
                rules=["3-4 legs per ticket", "no shared legs across tickets (A+ may anchor two)", "floor rung is the floor rung",
                       "never a leg we know is overpriced", "no attempt props when favored by 7+", "flat units"])
    path = P("cards", f"legs_{a.season}_w{a.week}_{a.slate}.json")
    json.dump(dict(meta=meta, players=out), open(path, "w"), separators=(",", ":"))
    n = sum(len(p["rungs"]) for p in out); a_plus = sum(1 for p in out for r in p["rungs"] if r["grade"] == "A+")
    print(f"wrote {path}: {len(out)} player/markets, {n} rungs graded, {a_plus} A+")

if __name__ == "__main__":
    main()
