"""The Legs board shows every DK rung from the lowest up to the last one graded C or better, and accounts for every
rung it leaves off. The Week 4 bug: D-graded rungs inside a ladder were dropped (Stroud 170/180/190, Lawrence 190)."""
import copy, json, os
import numpy as np
import pandas as pd
import pytest
from grade_legs import trim_ladders, grade_rung
from legs_coverage import check

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ladder_2026_w4")


def player(name, grades, main=None, market="pass_yds", start=160, stepv=10, odds=-300):
    rungs = [dict(rung=float(start + i * stepv), est_odds=odds, grade=g, reasons=[], _pre_comp=g) for i, g in enumerate(grades)]
    return dict(player=name, market=market, main_line=main or rungs[len(rungs) // 2]["rung"], rungs=rungs)


def rungs_of(p): return [r["rung"] for r in p["rungs"]]


# ── trim_ladders ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_d_rungs_inside_the_ladder_stay():
    """Stroud: 160 A-, 170-190 D, 200 C, 210+ D -> show 160 through 200"""
    shown, omitted = trim_ladders([player("Stroud", ["A-", "D", "D", "D", "C", "D", "D"])])
    assert rungs_of(shown[0]) == [160, 170, 180, 190, 200]
    assert omitted == [dict(player="Stroud", market="pass_yds", rungs=[210.0, 220.0], reason="above the last rung graded C or better")]


def test_ladder_starts_at_the_lowest_dk_rung():
    shown, _ = trim_ladders([player("Tuten", ["D", "D", "D", "C", "C"], market="rush_yds", start=20)])
    assert rungs_of(shown[0])[0] == 20


def test_held_player_shows_three_rungs_nearest_the_line_and_records_the_rest():
    p = player("Held", ["F"] * 7, main=190.0)
    for r in p["rungs"]: r["reasons"] = ["team change (A->B)"]
    shown, omitted = trim_ladders([p])
    assert shown[0]["held"] and rungs_of(shown[0]) == [180, 190, 200]
    assert sorted(omitted[0]["rungs"]) == [160, 170, 210, 220] and omitted[0]["reason"].startswith("held (team change")


def test_player_with_no_c_or_better_rung_is_recorded_not_dropped():
    shown, omitted = trim_ladders([player("Weak", ["D", "D", "D"])])
    assert shown == [] and omitted[0]["reason"] == "no rung graded C or better" and len(omitted[0]["rungs"]) == 3


def test_target_competition_rung_counts_for_the_range_and_comp_held():
    p = player("Rival", ["D", "D", "D"], market="receptions", start=2, stepv=1)
    p["rungs"][1]["_pre_comp"] = "C"                     # C before the new-target-competition step
    shown, omitted = trim_ladders([p])
    assert rungs_of(shown[0]) == [2, 3] and shown[0]["comp_held"]
    assert omitted[0]["rungs"] == [4.0]


def test_unknown_team_is_recorded_with_its_dk_rungs():
    _, omitted = trim_ladders([], skipped=[("Darius Slayton", "receptions", "no NFL game log found, so his team is unknown")],
                              REAL={("darius slayton", "receptions"): [(2.0, -300), (3.0, -120)]})
    assert omitted == [dict(player="Darius Slayton", market="receptions", rungs=[2.0, 3.0],
                            reason="no NFL game log found, so his team is unknown")]


# ── grade_rung: price markers ─────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("odds,note", [(-449, None), (-450, None), (-451, "price past -450, not card-eligible"),
                                       (-520, "price past -450, not card-eligible"), (-600, "price past -450, not card-eligible"),
                                       (-601, "price past -600: not card-eligible"), (-1520, "price past -600: not card-eligible")])
def test_rungs_past_minus_450_carry_one_card_eligibility_note(odds, note):
    _, why, _ = grade_rung(0.86, 200, odds, np.array([300.0, 300.0, 300.0]), "pass_yds", [], "neutral", "neutral", [])
    notes = [w for w in why if "not card-eligible" in w]
    assert notes == ([note] if note else [])                        # exactly one note, never both


def test_holds_grade_f_with_the_hold_reasons():
    assert grade_rung(0.9, 200, -200, np.array([300.0] * 3), "pass_yds", ["team change (A->B)"], "neutral", "neutral", []) \
        == ("F", ["team change (A->B)"], None)


# ── legs_coverage.check ───────────────────────────────────────────────────────────────────────────────────────────
def ladder(rows, commence="2026-10-04T17:00:00Z"):
    return pd.DataFrame([dict(Player=p, Market=m, Rung=t, Odds=-200, Game="X @ Y", Commence=commence, PulledAt="t") for p, m, t in rows])


def test_check_flags_a_silently_dropped_rung():
    lad = ladder([("Stroud", "pass_yds", t) for t in (160, 170, 180)])
    legs = dict(players=[dict(player="Stroud", market="pass_yds", rungs=[dict(rung=160.0), dict(rung=180.0)])], omitted=[])
    assert [(g["rung"], g["reason"]) for g in check(lad, legs, "sun")] == [(170.0, None)]


def test_check_accepts_a_rung_with_a_recorded_reason_and_ignores_other_slates():
    lad = pd.concat([ladder([("Stroud", "pass_yds", 160), ("Stroud", "pass_yds", 170)]),
                     ladder([("Rodgers", "pass_yds", 200)], commence="2026-10-02T00:15:00Z")])   # Thursday night ET
    legs = dict(players=[dict(player="Stroud", market="pass_yds", rungs=[dict(rung=160.0)])],
                omitted=[dict(player="Stroud", market="pass_yds", rungs=[170.0], reason="above the last rung graded C or better")])
    assert [g["reason"] for g in check(lad, legs, "sun")] == ["above the last rung graded C or better"]


# ── real Week 4 data: zero unexplained gaps ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("slate", ["sun", "tnf"])
def test_week4_every_dk_rung_is_shown_or_explained(slate):
    g = json.load(open(os.path.join(FIX, f"graded_{slate}.json"), encoding="utf-8"))
    lad = pd.read_csv(os.path.join(FIX, "ladders_2026_w4.csv"))
    real = {}
    for r in lad.itertuples():
        from common import norm_name
        real.setdefault((norm_name(r.Player), r.Market), []).append((float(r.Rung), int(r.Odds)))
    shown, omitted = trim_ladders(copy.deepcopy(g["players"]), [tuple(x) for x in g["skipped"]], real)
    gaps = check(lad, dict(players=shown, omitted=omitted), slate)
    assert [x for x in gaps if x["reason"] is None] == []


def test_week4_stroud_and_lawrence_ladders_have_no_holes():
    g = json.load(open(os.path.join(FIX, "graded_sun.json"), encoding="utf-8"))
    shown, _ = trim_ladders(copy.deepcopy(g["players"]), [tuple(x) for x in g["skipped"]])
    by = {(p["player"], p["market"]): rungs_of(p) for p in shown}
    assert by[("C.J. Stroud", "pass_yds")] == [160, 170, 180, 190, 200]
    assert by[("Trevor Lawrence", "pass_yds")] == [180, 190, 200, 210, 220, 230]
    lad = pd.read_csv(os.path.join(FIX, "ladders_2026_w4.csv"))
    dk = lad.groupby(["Player", "Market"]).Rung.apply(lambda x: sorted(set(map(float, x)))).to_dict()
    held = {(p["player"], p["market"]) for p in shown if p.get("held")}
    for k, rs in by.items():                  # every ladder = DK's rungs from its lowest up to the top one shown
        if k in held or k not in dk: continue
        assert rs == [t for t in dk[k] if t <= rs[-1]], k


def test_the_check_catches_the_original_bug():
    """replay the old trim (keep only C-or-better rungs, record nothing): the check must flag the Stroud holes"""
    g = json.load(open(os.path.join(FIX, "graded_sun.json"), encoding="utf-8"))
    old = [dict(p, rungs=[r for r in p["rungs"] if r["grade"] in ("A+", "A", "A-", "B", "C")]) for p in g["players"]]
    old = [p for p in old if p["rungs"]]
    gaps = check(pd.read_csv(os.path.join(FIX, "ladders_2026_w4.csv")), dict(players=old), "sun")
    silent = {(x["player"], x["rung"]) for x in gaps if x["reason"] is None and x["market"] == "pass_yds"}
    assert {("C.J. Stroud", 170.0), ("C.J. Stroud", 180.0), ("C.J. Stroud", 190.0), ("Trevor Lawrence", 190.0)} <= silent
