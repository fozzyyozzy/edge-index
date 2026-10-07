"""House rules on small made-up cards. Ticket assembly (R1, R2, R7, R8, R10, R11, one leg per game) calls
build_card_json.build_tickets() directly; candidate selection and holds (R3, R4, R5, R6, R9, price cap) run the whole
builder on a fake slate. card_qa.py must pass the built cards and catch doctored ones."""
import copy
from collections import Counter
import pytest
from conftest import cand, ranked, GAMES, write_slate, run_card, row
from build_card_json import build_tickets, TARGET_DEC, dec
import card_qa


def players_on(tickets):
    return Counter(p for t in tickets for p in {l["player"] for l in t["legs"]})


def shared_per_ticket(tickets):
    on = players_on(tickets)
    return {t["name"]: sorted(l["player"] for l in t["legs"] if on[l["player"]] > 1) for t in tickets}


def deep_pool(n=14, grade="A", odds=-250):
    """n non-star candidates, two per game, so every ticket can fill without repeats"""
    return [cand(f"P{i}", *GAMES[i % len(GAMES)], grade=grade, odds=odds, l10=0.8, l15=0.8) for i in range(n)]


# ── R1 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_r1_at_most_three_tickets_of_three_or_four_legs():
    t = build_tickets(ranked(deep_pool(20)), "sun", 3)
    assert 2 <= len(t) <= 3
    assert all(3 <= len(x["legs"]) <= 4 for x in t)


def test_r1_no_ticket_when_fewer_than_three_legs_fit():
    pool = [cand("A1", *GAMES[0]), cand("A2", *GAMES[1])]
    assert build_tickets(ranked(pool), "sun", 3) == []


# ── R2 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_r2_non_star_never_repeats():
    t = build_tickets(ranked(deep_pool(9)), "sun", 3)
    assert max(players_on(t).values()) == 1


def test_r2_star_at_most_two_tickets():
    pool = [cand("Star", *GAMES[0], grade="A+", edge=9)] + deep_pool(12)
    t = build_tickets(ranked(pool), "sun", 3)
    assert players_on(t)["Star"] == 2


def test_r2_each_ticket_shares_at_most_one_player():
    """the Week 4 Sunday bug: SUN-1 shared Meyers with SUN-2 and Rice with SUN-3"""
    stars = [cand("Meyers", *GAMES[0], grade="A+", edge=9), cand("Rice", *GAMES[1], grade="A+", edge=8),
             cand("Kupp", *GAMES[2], grade="A+", edge=7)]
    t = build_tickets(ranked(stars + deep_pool(12, grade="B")), "sun", 3)
    assert len(t) == 3
    assert all(len(s) <= 1 for s in shared_per_ticket(t).values()), shared_per_ticket(t)


# ── one leg per game, R7 ──────────────────────────────────────────────────────────────────────────────────────────
def test_one_leg_per_game_on_multi_game_slates():
    pool = [cand(f"G{i}", *GAMES[i // 2]) for i in range(10)]          # two players per game
    for x in build_tickets(ranked(pool), "sun", 3):
        games = Counter(frozenset([l["team"], l["opp"]]) for l in x["legs"])
        assert max(games.values()) == 1


def test_r7_single_game_two_leg_ticket_is_reduced_and_correlated():
    pool = [cand("T1", *GAMES[0]), cand("T2", *GAMES[0][::-1])]
    t = build_tickets(ranked(pool), "tnf", 1)
    assert len(t) == 1 and len(t[0]["legs"]) == 2
    assert t[0]["reduced"] and t[0]["correlated"]


def test_r7_single_game_slate_builds_one_ticket():
    pool = [cand(f"T{i}", *GAMES[0]) for i in range(8)]
    assert len(build_tickets(ranked(pool), "tnf", 1)) == 1


# ── R8 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_r8_fourth_leg_only_when_three_fall_short():
    short = build_tickets(ranked(deep_pool(8, odds=-250)), "sun", 1)[0]          # 1.4^3 = 2.74x < 3.0x
    assert len(short["legs"]) == 4
    long = build_tickets(ranked(deep_pool(8, odds=-150)), "sun", 1)[0]           # 1.67^3 = 4.6x
    assert len(long["legs"]) == 3 and not long["reduced"]


def test_r8_payout_is_the_product_and_label_matches():
    for x in build_tickets(ranked(deep_pool(14)), "sun", 3):
        d = 1.0
        for l in x["legs"]: d *= dec(l["odds_est"])
        assert x["est_payout"] == round(d, 2)
        assert x["reduced"] == (d < TARGET_DEC)


def test_r8_fourth_leg_comes_from_the_best_grade_not_the_closest_payout():
    base = [cand(f"A{i}", *GAMES[i], grade="A", odds=-250, edge=9) for i in range(3)]          # 2.74x
    closer_b = cand("CloserB", *GAMES[3], grade="B", odds=-300, edge=8)                       # -> 3.66x
    farther_a = cand("FartherAminus", *GAMES[4], grade="A-", odds=-180, edge=3)               # -> 4.27x
    t = build_tickets(ranked(base + [closer_b, farther_a]), "sun", 1)[0]
    assert t["legs"][3]["player"] == "FartherAminus"


# ── R10 ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_r10_grade_first_then_edge():
    pool = [cand("B_big_edge", *GAMES[0], grade="B", edge=15), cand("Aplus", *GAMES[1], grade="A+", edge=2.5),
            cand("A_hi", *GAMES[2], grade="A", edge=6), cand("A_lo", *GAMES[3], grade="A", edge=3)]
    assert [c["player"] for c in ranked(pool)] == ["Aplus", "A_hi", "A_lo", "B_big_edge"]
    t = build_tickets(ranked(pool), "sun", 1)[0]
    assert [l["player"] for l in t["legs"][:3]] == ["Aplus", "A_hi", "A_lo"]


def test_r10_no_c_leg_when_a_b_fits():
    pool = [cand("A1", *GAMES[0]), cand("A2", *GAMES[1]), cand("B1", *GAMES[2], grade="B", edge=2.1),
            cand("C1", *GAMES[3], grade="C", edge=12)]
    t = build_tickets(ranked(pool), "sun", 1)[0]
    assert "C1" not in [l["player"] for l in t["legs"]]


def test_r10_never_a_c_fourth_leg():
    pool = [cand(f"A{i}", *GAMES[i], odds=-250) for i in range(3)] + [cand("C1", *GAMES[3], grade="C", odds=-200, edge=12)]
    t = build_tickets(ranked(pool), "sun", 1)[0]                     # 2.74x: short of +200, but no B-or-better 4th
    assert [l["player"] for l in t["legs"]] == ["A0", "A1", "A2"] and t["reduced"]


def test_r10_c_leg_only_when_nothing_better_can_fill():
    pool = [cand("A1", *GAMES[0], odds=-150), cand("A2", *GAMES[1], odds=-150), cand("C1", *GAMES[2], grade="C", odds=-150)]
    t = build_tickets(ranked(pool), "sun", 3)
    assert len(t) == 1 and "C1" in [l["player"] for l in t[0]["legs"]]


def test_r10_two_tickets_beat_a_third_that_needs_a_c():
    good = [cand(f"A{i}", *GAMES[i % 7], grade="A", l10=0.8, l15=0.8, odds=-150) for i in range(6)]
    weak = [cand(f"C{i}", *GAMES[(i + 2) % 7], grade="C", l10=0.8, l15=0.8, odds=-150) for i in range(3)]
    t = build_tickets(ranked(good + weak), "sun", 3)
    assert len(t) == 2
    assert all(l["grade"] != "C" for x in t for l in x["legs"])


# ── R11 ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_r11_injury_watch_star_goes_on_one_ticket():
    pool = [cand("Watched", *GAMES[0], grade="A+", edge=9, watch=["injury watch: limited in practice (thumb)"])] + deep_pool(12)
    assert players_on(build_tickets(ranked(pool), "sun", 3))["Watched"] == 1
    pool[0]["injury_watch"] = None                                       # same star without the flag repeats
    assert players_on(build_tickets(ranked(pool), "sun", 3))["Watched"] == 2


# ── candidate selection and holds, end to end (R3, R4, R5, R6, R9, price cap) ─────────────────────────────────────
def filler(n=6):
    return [row(f"Fill{i}", GAMES[i % 7], grade="A-", odds=-250, edge=3.0) for i in range(n)]


def held_reasons(card, player):
    return [r for h in card["held_all"] if h["Player"] == player for r in h["Reasons"]]


def test_r3_best_graded_rung_at_or_below_the_floor(slate_root):
    kyren = row("Kyren", GAMES[0], market="rush_yds", floor=60, grade="C", odds=-108, edge=10.7, extra_rungs=[
        (40, -349, "A+", 5.7, 1.0, 1.0),           # best grade, below the floor: chosen
        (30, -790, "A+", 6.0, 1.0, 1.0),           # A+ with more edge but past the -450 cap
        (20, -300, "A+", 8.0, 0.7, 1.0),           # A+ but L10 70%: not a qualifying rung
        (70, -100, "A+", 9.0, 0.9, 0.9)])          # above the floor rung: never
    write_slate(slate_root, [kyren] + filler())
    card = run_card(slate_root)
    k = [c for c in card["candidates"] if c["player"] == "Kyren"]
    assert len(k) == 1 and k[0]["rung"] == 40 and k[0]["grade"] == "A+" and k[0]["floor_rung"] == 60


@pytest.mark.parametrize("bad,reason", [
    (dict(edge=1.5), "edge"),                                                        # R4
    (dict(grade="D"), "grade below C"),                                              # R9
    (dict(odds=-500), "price worse than -450"),                                      # price cap
    (dict(market="pass_att", floor=30, spread=-8.0), "blowout risk"),                 # R5
    (dict(team_change=True, prev_team="OLD"), "team change"),                        # R6
    (dict(own_vol="TOUGH"), "own volume low"),
])
def test_holds_keep_a_leg_off_the_card(slate_root, bad, reason):
    kw = dict(bad); grade = kw.pop("grade", "A"); odds = kw.pop("odds", -250); edge = kw.pop("edge", 4.0)
    write_slate(slate_root, [row("Bad", GAMES[0], grade=grade, odds=odds, edge=edge, **kw)] + filler())
    card = run_card(slate_root)
    assert "Bad" not in {c["player"] for c in card["candidates"]}
    assert any(reason in r for r in held_reasons(card, "Bad")), held_reasons(card, "Bad")


def test_tough_defense_is_not_a_hold(slate_root):
    """the Legs grade already steps a tough-D leg down; the card no longer holds it too (double count, 2026-10-07)"""
    write_slate(slate_root, [row("ToughD", GAMES[0], grade="B", opp_d="TOUGH")] + filler())
    card = run_card(slate_root)
    assert "ToughD" in {c["player"] for c in card["candidates"]}
    assert not any("opp D tough" in r for r in held_reasons(card, "ToughD"))


def test_r6_injury_holds_from_the_availability_snapshot(slate_root):
    avail = dict(season=2026, week=9, fetched_at="t", sources=dict(snap_counts="test", injuries="test"),
                 team_games={GAMES[1][0]: {"7": ["missed"], "8": []}},                 # 'missed' sat out week 8
                 players={"byhand": dict(team=None, hold=[], flag=[], manual=[dict(reason="questionable", market=None)]),
                          "listed": dict(team=GAMES[2][0], hold=["questionable (knee)"], flag=[]),
                          "watched": dict(team=GAMES[3][0], hold=[], flag=["limited in practice (thumb), no game status yet"])})
    rows = [row("ByHand", GAMES[0]), row("Missed", GAMES[1]), row("Listed", GAMES[2]), row("Watched", GAMES[3], grade="A+", edge=9)]
    write_slate(slate_root, rows + filler(8), avail=avail)
    card = run_card(slate_root)
    names = {c["player"] for c in card["candidates"]}
    assert not {"ByHand", "Missed", "Listed"} & names
    assert any("held by hand" in r for r in held_reasons(card, "ByHand"))
    assert any("no offensive snaps in wk 8" in r for r in held_reasons(card, "Missed"))
    assert any("questionable" in r for r in held_reasons(card, "Listed"))
    w = [c for c in card["candidates"] if c["player"] == "Watched"][0]                  # a flag, not a hold
    assert w["injury_watch"] and players_on(card["tickets"])["Watched"] == 1             # R11


# ── card_qa: passes built cards, catches doctored ones ────────────────────────────────────────────────────────────
@pytest.fixture
def built(slate_root):
    stars = [row(f"Star{i}", GAMES[i], grade="A+", odds=-250, edge=8 - i) for i in range(3)]
    write_slate(slate_root, stars + [row(f"B{i}", GAMES[(i + 3) % 7], grade="B", odds=-200, edge=3) for i in range(8)])
    card = run_card(slate_root)
    import json, os
    legs = json.load(open(os.path.join(slate_root, "cards", "legs_2026_w9_sun.json")))
    avail = json.load(open(os.path.join(slate_root, "cards", "availability_2026_w9_sun.json")))
    return card, legs, avail


def failing(card, legs, avail):
    return [r.split(" ")[0] for r, ok, _ in card_qa.check(card, legs, avail) if not ok]


def test_qa_passes_a_built_card(built):
    card, legs, avail = built
    assert card["tickets"] and failing(card, legs, avail) == []


def test_qa_catches_a_low_grade_leg(built):
    card, legs, avail = copy.deepcopy(built)
    card["tickets"][0]["legs"][0]["grade"] = "D"
    assert "R9" in failing(card, legs, avail)


def test_qa_catches_a_ticket_sharing_two_players(built):
    card, legs, avail = copy.deepcopy(built)
    t1, t2 = card["tickets"][0], card["tickets"][1]
    t2["legs"] = [l for l in t2["legs"] if l["player"] not in {x["player"] for x in t1["legs"]}][:2] + t1["legs"][:2]
    assert "R2" in failing(card, legs, avail)


def test_qa_catches_injury_holds_and_watch_repeats(built):
    card, legs, avail = copy.deepcopy(built)
    on = players_on(card["tickets"]); rep = next(p for p, n in on.items() if n == 2)
    one = next(p for p, n in on.items() if n == 1)
    l1 = next(l for t in card["tickets"] for l in t["legs"] if l["player"] == one)
    avail["players"] = {rep.lower(): dict(team=None, hold=[], flag=["limited in practice (thumb)"]),
                        one.lower(): dict(team=None, hold=["out (knee)"], flag=[])}
    f = failing(card, legs, avail)
    assert "R11" in f and "R6" in f


def test_qa_catches_a_c_leg_while_a_b_sat_unused(built):
    card, legs, avail = copy.deepcopy(built)
    leg = card["tickets"][0]["legs"][-1]; leg["grade"] = "C"
    for p in legs["players"]:                                     # keep the Legs board consistent so only R10 trips
        for r in p["rungs"]:
            if p["player"] == leg["player"] and r["rung"] == leg["rung"]: r["grade"] = "C"
    used = {l["player"] for t in card["tickets"] for l in t["legs"]}
    spare = [c for c in card["candidates"] if c["player"] not in used]
    if not spare:
        spare_c = copy.deepcopy(card["candidates"][-1]); spare_c.update(player="Spare", team="ZZZ", opp="YYY", grade="B")
        card["candidates"].append(spare_c)
    assert "R10" in failing(card, legs, avail)


def test_qa_catches_a_wrong_payout(built):
    card, legs, avail = copy.deepcopy(built)
    card["tickets"][0]["est_payout"] += 1
    assert "R8" in failing(card, legs, avail)


def test_qa_catches_missing_availability(built):
    card, legs, avail = copy.deepcopy(built)
    avail["sources"]["injuries"] = "unavailable (HTTPError)"
    assert "Data:" in failing(card, legs, avail)
