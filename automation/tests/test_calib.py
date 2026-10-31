"""Shadow-only probability-first cards (pfirst, calib) and the calibration model (calib.py). Nothing here touches the live
card: leakage (features only from before kickoff), the pfirst/calib selection rules, and reproducible retro builds."""
import json, os, subprocess, sys
import numpy as np
import pandas as pd
import pytest
from conftest import cand, write_slate, row, GAMES, PIPE
import calib
from build_card_json import build_tickets_pfirst, PF_WINDOW, dec


def pc(player, team, opp, prob, odds=-250, grade="A", **kw):
    c = cand(player, team, opp, grade=grade, odds=odds, **kw); c["prob"] = prob; c["model_pct"] = 100 * prob
    return c


# ── leakage ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def fake_data(week_n_value=0.0):
    """two players, 2025 weeks 1-17 and 2026 weeks 1-8; week 8 (the slate's own week) and later carry week_n_value"""
    rows = []
    for key in ("pat a", "lee b"):
        for season, weeks in ((2025, range(1, 18)), (2026, range(1, 10))):
            for w in weeks:
                v = week_n_value if (season == 2026 and w >= 8) else 5.0 + (w % 3)
                rows.append(dict(key=key, season=season, week=w, receptions=v, targets=v + 2, carries=1.0,
                                 receiving_yards=10 * v, rushing_yards=3.0, passing_yards=0, attempts=0, completions=0))
    snaps = pd.DataFrame([dict(key=k, week=w, snap=(0.0 if w >= 8 else 0.8)) for k in ("pat a", "lee b") for w in range(1, 10)])
    return calib.Data(2026, stats=pd.DataFrame(rows), snaps=snaps)


def board(actual=None):
    return dict(meta=dict(generated="2026-11-01T12:00+00:00"), players=[
        dict(player=n, pos="WR", team="AAA", opp="BBB", market="receptions", opp_d_rank=10, own_vol_rank=20, spread=-3.0,
             game_total=44.5, team_total=23.75, injury=None, actual=actual,
             rungs=[dict(rung=4.0, est_odds=-300, novig_pct=72.0, result="hit" if actual else None)])
        for n in ("Pat A", "Lee B")])


def test_features_use_only_games_before_the_slate_week():
    low, high = calib.board_rows(board(), fake_data(0.0), 8), calib.board_rows(board(), fake_data(99.0), 8)
    assert [it["f"] for it in low] == [it["f"] for it in high]            # week 8+ stats can't move a week-8 feature
    assert [it["trend"] for it in low] == [it["trend"] for it in high]    # role trend: snaps/targets before week 8 only


def test_box_score_fields_on_the_board_never_reach_features():
    d = fake_data()
    a = calib.board_rows(board(actual=0.0), d, 8); b = calib.board_rows(board(actual=12.0), d, 8)
    assert [it["f"] for it in a] == [it["f"] for it in b]
    assert not any(k in calib.FEATS for k in ("actual", "result", "settled", "y"))


def test_pregame_board_takes_the_last_version_generated_before_kickoff(monkeypatch):
    ko = pd.Timestamp("2026-11-01T17:00+00:00")
    monkeypatch.setattr(calib, "first_kickoff", lambda *a: ko)
    v = lambda t: dict(meta=dict(generated=t), players=[])
    doc, src = calib.pregame_board(2026, 9, "sun", versions=[("regrade", v("2026-11-01T17:30+00:00")),
                                                             ("refresh", v("2026-11-01T16:00+00:00")),
                                                             ("card", v("2026-10-30T18:00+00:00"))])
    assert src == "refresh"                                          # the post-kickoff regrade is skipped
    doc, src = calib.pregame_board(2026, 9, "sun", versions=[("regrade", v("2026-11-01T17:30+00:00"))])
    assert doc is None


def test_training_weeks_stop_before_the_card_week(monkeypatch):
    seen = []
    monkeypatch.setattr(calib, "training_items", lambda season, weeks, data: (seen.extend(weeks) or [], {}))
    monkeypatch.setattr(calib, "fit", lambda X, y, **k: dict(n=0))
    monkeypatch.setattr(calib, "matrix", lambda items, cols: np.zeros((0, len(cols))))
    calib.fit_for_week(2026, 9, data=object())
    assert seen and max(seen) == 8


def test_fit_recovers_a_known_logistic_and_is_deterministic():
    rng = np.random.default_rng(1); X = rng.normal(size=(4000, 2))
    y = (rng.random(4000) < 1 / (1 + np.exp(-(0.5 + 1.5 * X[:, 0])))).astype(float)
    m1, m2 = calib.fit(X, y, lam=0.0), calib.fit(X, y, lam=0.0)
    assert m1 == m2
    assert calib.predict(m1, [[0, 0]])[0] == pytest.approx(1 / (1 + np.exp(-0.5)), abs=0.03)


def test_calib_grades_and_role_down():
    assert [calib.grade_of(p) for p in (.86, .81, .76, .70, .61, .59)] == ["A+", "A", "A-", "B", "C", "D"]
    assert calib.role_down({"tgt": (8.0, [5.0, 5.5])}, 0.25)            # both games > 25% below the prior average
    assert not calib.role_down({"tgt": (8.0, [5.0, 7.5])}, 0.25)        # only one game down
    assert not calib.role_down({"tgt": (1.0, [0.0, 0.0])}, 0.25)        # no real prior role to lose


# ── pfirst / calib selection ────────────────────────────────────────────────────────────────────────────────────────
def test_pfirst_picks_the_most_likely_ticket_inside_the_payout_window():
    cs = [pc(f"P{i}", *GAMES[i], prob=p, odds=o) for i, (p, o) in enumerate(
        [(.90, -450), (.88, -400), (.86, -350), (.80, -250), (.75, -220), (.70, -200), (.72, -210)])]
    t = build_tickets_pfirst(cs, "sun", 1)[0]
    assert PF_WINDOW[0] <= t["est_payout"] <= PF_WINDOW[1] and not t["reduced"]
    best = 0
    from itertools import combinations
    for n in (3, 4):
        for combo in combinations(cs, n):
            pay = np.prod([dec(c["odds_est"]) for c in combo])
            if PF_WINDOW[0] <= pay <= PF_WINDOW[1]: best = max(best, np.prod([c["prob"] for c in combo]))
    assert t["model_hit"] == pytest.approx(best, abs=1e-3)


def test_pfirst_sharing_rules_r2_r11():
    star = pc("Star", *GAMES[0], prob=.92, odds=-300)
    watch = pc("Watch", *GAMES[1], prob=.91, odds=-300, watch=["injury watch: limited Thu"])
    rest = [pc(f"P{i}", *GAMES[i], prob=.85 - .01 * i, odds=-260) for i in range(2, 7)]
    tix = build_tickets_pfirst([star, watch] + rest, "sun", 3)
    players = [l["player"] for t in tix for l in t["legs"]]
    assert players.count("Watch") <= 1                                   # R11: a watch flag goes on one ticket
    assert players.count("Star") <= 2
    for i, t in enumerate(tix):                                          # R2: at most one player shared per ticket
        mine = {l["player"] for l in t["legs"]}
        others = {l["player"] for j, u in enumerate(tix) if j != i for l in u["legs"]}
        assert len(mine & others) <= 1
        assert len({frozenset([l["team"], l["opp"]]) for l in t["legs"]}) == len(t["legs"])   # one leg per game


def test_pfirst_c_legs_only_when_needed_never_fourth_and_no_third_ticket_on_a_c():
    bs = [pc(f"B{i}", *GAMES[i], prob=.8, odds=-300, grade="B") for i in range(3)]
    cs = [pc(f"C{i}", *GAMES[3 + i], prob=.95, odds=-300, grade="C") for i in range(3)]
    t = build_tickets_pfirst(bs + cs, "sun", 3)
    assert all(l["grade"] != "C" for l in t[0]["legs"])                  # C-free beats a likelier ticket with a C
    for x in t:
        if len(x["legs"]) == 4: assert all(l["grade"] != "C" for l in x["legs"])
    assert len(t) < 3 or all(l["grade"] != "C" for l in t[2]["legs"])


def test_role_down_leg_cannot_anchor():
    down = pc("Down", *GAMES[0], prob=.95, odds=-300, grade="A+"); down["role_down"] = True
    rest = [pc(f"P{i}", *GAMES[i], prob=.80, odds=-300, grade="A") for i in range(1, 6)]
    for t in build_tickets_pfirst([down] + rest, "sun", 2):
        top = max(t["legs"], key=lambda c: (c["grade"], c["prob"]))
        assert not top.get("role_down")


def test_single_game_two_legs_is_reduced():
    cs = [pc("A", "AAA", "BBB", prob=.9, odds=-400), pc("B", "BBB", "AAA", prob=.9, odds=-400)]
    t = build_tickets_pfirst(cs, "tnf", 1)
    assert len(t) == 1 and len(t[0]["legs"]) == 2 and t[0]["reduced"]


def test_pfirst_card_keeps_price_window_and_holds_and_drops_r4(slate_root):
    rows = [row(f"S{i}", GAMES[i % 7], grade="A", odds=-300, edge=-5.0) for i in range(6)]   # every edge below R4's +2
    rows.append(row("Juiced", GAMES[6], grade="A+", odds=-500, edge=5.0))                     # outside -450..-200
    rows.append(row("Plus", GAMES[0], grade="A+", odds=-150, edge=5.0))
    rows.append(row("Held", GAMES[1], grade="A+", odds=-300, edge=5.0, team_change=True, prev_team="ZZZ"))
    write_slate(slate_root, rows)
    env = dict(os.environ, EDGE_ROOT=str(slate_root), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", "2026", "--week", "9",
                    "--slate", "sun", "--shadow", "pfirst"], env=env, check=True, capture_output=True)
    sh = json.load(open(os.path.join(slate_root, "cards", "shadow", "card_2026_w9_sun_pfirst.json"), encoding="utf-8"))
    names = {c["player"] for c in sh["candidates"]}
    assert {f"S{i}" for i in range(6)} <= names                          # no R4
    assert not names & {"Juiced", "Plus", "Held"}                        # price window; holds still hold
    assert sh["tickets"] and sh["shadow"]["select"] == "probability-first"
    assert not os.path.exists(os.path.join(slate_root, "cards", "card_2026_w9_sun.json"))   # never the live card file


# ── reproducibility ─────────────────────────────────────────────────────────────────────────────────────────────────
def test_retro_build_is_reproducible(slate_root):
    write_slate(slate_root, [row(f"S{i}", GAMES[i % 7], grade="A", odds=-250 - 10 * i, edge=1.0) for i in range(8)])
    env = dict(os.environ, EDGE_ROOT=str(slate_root), PYTHONIOENCODING="utf-8")
    out = []
    for _ in range(2):
        subprocess.run([sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", "2026", "--week", "9",
                        "--slate", "sun", "--shadow", "pfirst"], env=env, check=True, capture_output=True)
        out.append(json.load(open(os.path.join(slate_root, "cards", "shadow", "card_2026_w9_sun_pfirst.json"), encoding="utf-8"))["tickets"])
    assert out[0] == out[1]


def test_calib_scoring_is_reproducible_and_marks_unscored_rungs():
    d = fake_data(); b = board()
    b["players"][0]["rungs"].append(dict(rung=9.0, est_odds=120))        # no market price -> can't be scored
    items = calib.board_rows(b, d, 8)
    X = calib.matrix(items * 50, calib.FEATS)
    model = calib.fit(X, [i % 2 for i in range(len(X))], cols=calib.FEATS)
    s1, s2 = calib.score_board(b, 2026, 8, model, d), calib.score_board(b, 2026, 8, model, d)
    assert s1 == s2
    r = s1["players"][0]["rungs"]
    assert r[0]["calib"] and r[0]["grade"] == calib.grade_of(r[0]["prob"])
    assert r[1]["grade"] == "F"
    assert b["players"][0]["rungs"][0].get("calib") is None               # the input board is not modified


def test_shadow_only_changelog_entries_stay_out_of_the_newsletter(tmp_path):
    from datetime import date
    sys.path.insert(0, os.path.join(os.path.dirname(PIPE), "newsletter"))
    import house_rules as hr
    p = tmp_path / "cl.md"
    p.write_text("# log\n\n## 2026-11-01 — research: pfirst and calib cards (shadow only, not live)\n\nx\n\n"
                 "## 2026-10-31 — rule change: something live\n\ny\n", encoding="utf-8")
    got = hr.changelog_entries(date(2026, 10, 25), date(2026, 11, 2), path=str(p))
    assert [e["date"] for e in got] == ["2026-10-31"]


def test_study_scores_cards_the_simple_way():
    from calib_study import score_card
    card = dict(tickets=[dict(est_payout=2.6, legs=[dict(player="Pat A", market="receptions", rung=4.0)]),
                         dict(est_payout=3.0, legs=[dict(player="Lee B", market="receptions", rung=4.0)]),
                         dict(est_payout=3.0, legs=[dict(player="Nobody", market="receptions", rung=4.0)])])
    act = {("pat a", "receptions"): 5.0, ("lee b", "receptions"): 2.0}
    assert score_card(card, act) == [("WIN", 1.6), ("LOSS", -1.0), ("VOID", 0.0)]
