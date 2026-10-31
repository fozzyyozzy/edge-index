"""The live card is probability-first from Week 9, 2026 (common.LIVE_PFIRST_FROM): no edge minimum (R4 retired), legs
priced -450..-200 (R12), grade then probability in the +150..+250 window (R8/R10), and the role-down hold (R13), which
only removes legs. The Week 1-8 rules keep running as the "legacy" shadow and must reproduce the last legacy card."""
import json, os, subprocess, sys
import pytest
from conftest import write_slate, row, GAMES, PIPE
from make_fixtures import FIX
import card_qa
from common import card_rules, LIVE_PFIRST_FROM

ENV = lambda root: dict(os.environ, EDGE_ROOT=str(root), PYTHONIOENCODING="utf-8")


def build(root, week=9, slate="sun", shadow=None):
    args = [sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", "2026", "--week", str(week), "--slate", slate]
    if shadow: args += ["--shadow", shadow]
    subprocess.run(args, env=ENV(root), check=True, capture_output=True)
    f = (os.path.join(root, "cards", "shadow", f"card_2026_w{week}_{slate}_{shadow}.json") if shadow
         else os.path.join(root, "cards", f"card_2026_w{week}_{slate}.json"))
    return json.load(open(f, encoding="utf-8"))


def flag_roles(root, flagged, week=9, slate="sun", reason="role down: carries 20→12→8"):
    f = os.path.join(root, "cards", f"legs_2026_w{week}_{slate}.json")
    d = json.load(open(f, encoding="utf-8"))
    for p in d["players"]:
        p["role_down"] = p["player"] in flagged
        p["role_reason"] = reason if p["role_down"] else None
    json.dump(d, open(f, "w", encoding="utf-8"))


def qa_fails(root, card, week=9, slate="sun"):
    legs = json.load(open(os.path.join(root, "cards", f"legs_2026_w{week}_{slate}.json"), encoding="utf-8"))
    av = json.load(open(os.path.join(root, "cards", f"availability_2026_w{week}_{slate}.json"), encoding="utf-8"))
    return [r for r, ok, _ in card_qa.check(card, legs, av) if not ok]


def test_rules_switch_at_week_9_only():
    assert LIVE_PFIRST_FROM == (2026, 9)
    assert card_rules(2026, 8)["select"] == "legacy" and card_rules(2026, 8)["min_edge"] == 2.0
    r = card_rules(2026, 9)
    assert r["select"] == "prob" and r["min_edge"] is None and r["role_hold"] and not r.get("dog_hold")
    assert card_rules(2026, 9, "legacy")["select"] == "legacy" and card_rules(2026, 9, "legacy")["min_edge"] == 2.0


def test_week9_live_card_is_probability_first_and_passes_qa(slate_root):
    rows = [row(f"S{i}", GAMES[i % 7], grade="A", odds=-300 + 10 * i, edge=-3.0) for i in range(7)]
    write_slate(slate_root, rows, week=9)
    c = build(slate_root)
    assert c["selection"] == "probability-first" and c["role_hold"]
    assert c["tickets"] and all(-450 <= l["odds_est"] <= -200 for t in c["tickets"] for l in t["legs"])
    assert all(t["est_payout"] <= 3.5 for t in c["tickets"])
    assert {x["player"] for x in c["candidates"]} == {f"S{i}" for i in range(7)}     # no edge minimum
    assert qa_fails(slate_root, c) == []


def test_role_down_blocks_a_leg_from_every_ticket(slate_root):
    rows = [row(f"S{i}", GAMES[i % 7], grade="A", odds=-300, edge=5.0) for i in range(7)]
    write_slate(slate_root, rows, week=9)
    before = build(slate_root)
    star = before["tickets"][0]["legs"][0]["player"]
    flag_roles(slate_root, {star})
    after = build(slate_root)
    assert star not in {l["player"] for t in after["tickets"] for l in t["legs"]}
    assert star not in {x["player"] for x in after["candidates"]}
    h = next(h for h in after["held_all"] if h["Player"] == star)
    assert h["Reasons"][0] == "role down: carries 20→12→8"


def test_role_down_never_adds_a_leg(slate_root):
    rows = [row(f"S{i}", GAMES[i % 7], grade="A", odds=-300, edge=5.0) for i in range(7)]
    write_slate(slate_root, rows, week=9)
    base = build(slate_root)
    flag_roles(slate_root, {"S2", "S5"})
    after = build(slate_root)
    pool_before = {x["player"] for x in base["candidates"]}
    pool_after = {x["player"] for x in after["candidates"]}
    assert pool_after == pool_before - {"S2", "S5"}                      # only removals
    held_before = {h["Player"] for h in base["held_all"]}
    assert {h["Player"] for h in after["held_all"]} == held_before | {"S2", "S5"}


def test_role_down_does_not_touch_legacy_cards(slate_root):
    rows = [row(f"S{i}", GAMES[i % 7], grade="A", odds=-300, edge=5.0) for i in range(7)]
    write_slate(slate_root, rows, week=8)
    base = build(slate_root, week=8)
    flag_roles(slate_root, {"S0", "S1"}, week=8)
    assert build(slate_root, week=8)["tickets"] == base["tickets"]


def test_qa_fails_a_role_down_leg_on_a_ticket(slate_root):
    rows = [row(f"S{i}", GAMES[i % 7], grade="A", odds=-300, edge=5.0) for i in range(7)]
    write_slate(slate_root, rows, week=9)
    c = build(slate_root)
    flag_roles(slate_root, {c["tickets"][0]["legs"][0]["player"]})       # flagged after the build: QA must catch it
    assert "R13 no role-down leg on a ticket" in qa_fails(slate_root, c)


def test_underdog_rushing_hold_is_shadow_only(slate_root):
    rows = [row(f"R{i}", GAMES[i % 7], grade="A", odds=-300, edge=5.0, market="rush_att", spread=7.5) for i in range(4)]
    rows += [row(f"W{i}", GAMES[i % 7], grade="A", odds=-300, edge=5.0) for i in range(4, 7)]
    write_slate(slate_root, rows, week=9)
    live, dog = build(slate_root), build(slate_root, shadow="pfirst_dog")
    assert {f"R{i}" for i in range(4)} <= {x["player"] for x in live["candidates"]}
    assert not {f"R{i}" for i in range(4)} & {x["player"] for x in dog["candidates"]}
    assert any(r.startswith("underdog rushing (dog by 7.5)") for h in dog["held_all"] for r in h["Reasons"])


def test_legacy_shadow_reproduces_the_week8_sunday_live_card(tmp_path):
    """the last card built under the old rules, rebuilt by --shadow legacy from its publish-commit inputs"""
    import shutil
    root = tmp_path / "w8"; shutil.copytree(os.path.join(FIX, "2026_w8_sun"), root)
    pub = json.load(open(os.path.join(FIX, "2026_w8_sun", "published_card.json"), encoding="utf-8"))
    leg = lambda l: (l["player"], l["market"], l["rung"], l["odds_est"], l["grade"])
    tix = lambda c: [(t["name"], t["est_payout"], t["reduced"], [leg(l) for l in t["legs"]]) for t in c["tickets"]]
    legacy = build(root, week=8, shadow="legacy")
    assert tix(legacy) == tix(pub)
    assert tix(build(root, week=8)) == tix(pub)                          # and Week 8's live rules are still legacy
