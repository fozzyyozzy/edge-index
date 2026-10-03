"""Shared helpers: pipeline on sys.path, made-up candidates for build_tickets(), and made-up slates (a whole fake
automation/ folder) for running build_card_json.py end to end without the network."""
import json, os, subprocess, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(os.path.dirname(HERE), "pipeline")
sys.path.insert(0, PIPE); sys.path.insert(0, HERE)


def cand(player, team, opp, grade="A", odds=-250, edge=4.0, l10=0.9, l15=14 / 15, market="receptions", rung=4.0,
         star=None, watch=None):
    """one card candidate, shaped like build_card_json.py's"""
    star = (l10 >= 0.9 and l15 >= 13 / 15) if star is None else star
    return dict(player=player, team=team, opp=opp, market=market, rung=rung, floor_rung=rung, odds_est=odds,
                odds_real=odds, l10=l10, l15=l15, star=star, grade=grade, edge_pts=edge, model_pct=85.0,
                injury_watch=watch, published_odds=odds)


def ranked(cands):
    """sorted the way build_card_json.py sorts (R10: grade, then edge, then price)"""
    from build_card_json import GRADE_RANK
    return sorted(cands, key=lambda c: (-GRADE_RANK[c["grade"]], -c["edge_pts"], c["odds_est"]))


GAMES = [("AAA", "BBB"), ("CCC", "DDD"), ("EEE", "FFF"), ("GGG", "HHH"), ("III", "JJJ"), ("KKK", "LLL"), ("MMM", "NNN")]


def write_slate(root, rows, season=2026, week=9, slate="sun", avail=None):
    """A fake automation/ folder for build_card_json.py. rows: dicts with player, team, opp, market, floor (rung),
    rungs [(rung, odds, grade, edge, l10, l15)], and optional opp_d/own_vol/spread/team_change."""
    for d in ("floors", "cards", "lines", "notes"): os.makedirs(os.path.join(root, d), exist_ok=True)
    fl, players, dk, lad = [], [], [], []
    for r in rows:
        fr = next(x for x in r["rungs"] if x[0] == r["floor"])
        fl.append(dict(Player=r["player"], Team=r["team"], Opp=r["opp"], Market=r["market"], Main=r["floor"] + 2.5,
                       MainOdds=-115, Rung=f"{r['floor']:g}+", EstOdds=fr[1], L10=f"{round(fr[4] * 10)}/10",
                       L15=f"{round(fr[5] * 15)}/15", OppD=r.get("opp_d", "neutral"), OwnVol=r.get("own_vol", "neutral"),
                       Spread=r.get("spread", -3.0), OppDRank=16, OwnVolRank=16, TeamChange=r.get("team_change", False),
                       PrevTeam=r.get("prev_team", ""), Last3=str([r["floor"] + 5] * 3), EdgePts=fr[3]))
        players.append(dict(player=r["player"], pos="WR", team=r["team"], opp=r["opp"], market=r["market"],
                            spread=r.get("spread", -3.0), rungs=[
            dict(rung=t, est_odds=o, grade=g, edge_pts=e, prob=0.85, fair_odds=-560, novig_pct=70.0, clear_pct=90.0,
                 l10=f"{round(a * 10)}/10", l15=f"{round(b * 15)}/15", reasons=r.get("reasons", []))
            for t, o, g, e, a, b in r["rungs"]]))
        dk.append(dict(Player=r["player"], Market=r["market"], Line=r["floor"] + 2.5, Odds=-115))
        lad += [dict(Player=r["player"], Market=r["market"], Rung=t, Odds=o) for t, o, *_ in r["rungs"]]
    import pandas as pd
    pd.DataFrame(fl).to_csv(os.path.join(root, "floors", f"floors_{season}_w{week}_{slate}.csv"), index=False)
    pd.DataFrame(dk, columns=["Player", "Market", "Line", "Odds"]).to_csv(            # headers even when empty,
        os.path.join(root, "lines", f"dk_{season}_w{week}_{slate}.csv"), index=False)  # as fetch_lines.py writes them
    pd.DataFrame(lad, columns=["Player", "Market", "Rung", "Odds"]).to_csv(
        os.path.join(root, "lines", f"ladders_{season}_w{week}.csv"), index=False)
    open(os.path.join(root, "lines", f"pulled_{season}_w{week}_{slate}.txt"), "w").write("2026-11-06T14:00+00:00")
    json.dump(dict(meta=dict(season=season, week=week, slate=slate), players=players),
              open(os.path.join(root, "cards", f"legs_{season}_w{week}_{slate}.json"), "w"))
    json.dump(avail or dict(season=season, week=week, fetched_at="2026-11-06T14:00+00:00",
                            sources=dict(snap_counts="test", injuries="test"), team_games={}, players={}),
              open(os.path.join(root, "cards", f"availability_{season}_w{week}_{slate}.json"), "w"))


def run_card(root, season=2026, week=9, slate="sun"):
    """build_card_json.py on a fake automation/ folder (EDGE_ROOT); returns the card"""
    env = dict(os.environ, EDGE_ROOT=str(root), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", str(season), "--week",
                    str(week), "--slate", slate], env=env, check=True, capture_output=True)
    return json.load(open(os.path.join(root, "cards", f"card_{season}_w{week}_{slate}.json"), encoding="utf-8"))


def row(player, game, grade="A", odds=-250, edge=4.0, market="receptions", floor=4.0, extra_rungs=(), **kw):
    """a fake floor row whose floor rung clears 9/10, 14/15"""
    team, opp = game
    rungs = [(floor, odds, grade, edge, 0.9, 14 / 15)] + list(extra_rungs)
    return dict(player=player, team=team, opp=opp, market=market, floor=floor, rungs=rungs, **kw)


@pytest.fixture
def slate_root(tmp_path):
    return tmp_path
