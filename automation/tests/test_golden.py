"""Golden rebuilds: the current builder, run on each saved slate's inputs, must reproduce expected_card.json exactly.
A rule change that moves a card has to update the fixture in the same commit:
    python automation/tests/make_fixtures.py --expected
and the diff of expected_card.json is the review of what the change did to real cards."""
import json, os
import pytest
from make_fixtures import CASES, FIX, rebuild
import card_qa


@pytest.mark.parametrize("case", sorted(CASES))
def test_rebuild_matches_expected(case):
    expected = json.load(open(os.path.join(FIX, case, "expected_card.json"), encoding="utf-8"))
    got = json.loads(json.dumps(rebuild(case)))
    if got != expected:
        diffs = [k for k in sorted(set(got) | set(expected)) if got.get(k) != expected.get(k)]
        tick = lambda c: [(t["name"], t["est_american"], [(l["player"], l["rung"], l["market"]) for l in t["legs"]]) for t in c["tickets"]]
        pytest.fail(f"{case}: rebuilt card differs in {diffs}\nexpected tickets {tick(expected)}\ngot      tickets {tick(got)}\n"
                    "If the change is intended: python automation/tests/make_fixtures.py --expected, and commit the fixture.")


@pytest.mark.parametrize("case", sorted(CASES))
def test_expected_card_passes_qa(case):
    root = os.path.join(FIX, case); m = json.load(open(os.path.join(root, "case.json")))
    s, w, sl = m["season"], m["week"], m["slate"]
    card = json.load(open(os.path.join(root, "expected_card.json"), encoding="utf-8"))
    legs = json.load(open(os.path.join(root, "cards", f"legs_{s}_w{w}_{sl}.json"), encoding="utf-8"))
    av = json.load(open(os.path.join(root, "cards", f"availability_{s}_w{w}_{sl}.json"), encoding="utf-8"))
    failed = [(r, d) for r, ok, d in card_qa.check(card, legs, av) if not ok]
    assert not failed, failed


def test_week4_sunday_under_current_rules():
    """the card that went live 2026-10-02 20:20 UTC (a1d71f9c: SUN-1 +217, SUN-2 +233) was built with the tough-D hold.
    Without it (2026-10-07, MODEL_CHANGELOG) the same inputs give SUN-1 unchanged, Otton on SUN-2, and a third ticket."""
    c = json.load(open(os.path.join(FIX, "2026_w4_sun", "expected_card.json"), encoding="utf-8"))
    assert [(t["name"], t["est_american"]) for t in c["tickets"]] == [("SUN-1", 217), ("SUN-2", 231), ("SUN-3", 389)]
    assert c["prices_pulled"] == "2026-10-02T17:51+00:00"
