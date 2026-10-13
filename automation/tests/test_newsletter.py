"""The newsletter draft writer can only describe rules that exist (build_card_json.py) and changes that were logged
(MODEL_CHANGELOG.md, quoted). 2026-10-13: the Week 5 receipts draft invented "TOUGH D + SOFT volume capped at B"."""
import os, re, sys
from datetime import date
import pytest

AUTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AUTO, "newsletter"))
import house_rules as hr

CLOG = open(hr.CHANGELOG, encoding="utf-8").read()
INVENTED = """## What changes

One adjustment is supported by the data.

The Juwan Johnson miss came from a leg where the defense tag was TOUGH and own volume was SOFT, yet the grade was A-.
Going forward: any leg with opp_d TOUGH and own_vol SOFT is capped at B grade on the card, regardless of L10/L15.
"""


def test_house_rules_are_exactly_the_builders():
    doc = open(hr.BUILDER, encoding="utf-8").read().split('"""')[1]
    ids = re.findall(r"(?m)^  (LOCK|R\d+)\s", doc)
    rules = hr.house_rules()
    assert list(rules) == ids and {"LOCK", "R1", "R4", "R11"} <= set(rules)
    assert "QB change" in rules["R11"] and "edge >= +2" in rules["R4"]


@pytest.mark.parametrize("text", [
    "Under R12 the card now caps tough defenses.",                      # no R12
    "The volume-cap rule kept two legs off.",                           # no such named rule
    INVENTED,                                                           # the Week 5 invention
    "A TOUGH defense tag against a receiver with soft volume should have been a harder filter.",
    "From now on we will hold every RB facing a top-8 defense.",
])
def test_a_draft_mentioning_a_rule_that_does_not_exist_fails(text):
    assert hr.check_draft(text, CLOG)


@pytest.mark.parametrize("text", [
    "R4 held 29 legs on edge; R2 let Hampton anchor two tickets as a floor star.",
    "The floor star rule let Kyren anchor both tickets. Both held under the LOCK rule.",
    "## What changed\n\nNothing changed this week.\n",
])
def test_drafts_that_stick_to_house_rules_pass(text):
    assert hr.check_draft(text, CLOG) == []


def test_what_changed_must_quote_the_changelog_verbatim():
    real = next(l for l in CLOG.splitlines() if l.startswith("- **What:**") and len(l) > 40)
    ok = f"## What changed\n\nFrom the model changelog (2026-10-07):\n> {real}\n\n## The record\n"
    assert hr.check_draft(ok, CLOG) == []
    paraphrased = "## What changed\n\n> We stopped holding legs against tough defenses because it seemed unfair.\n"
    assert any("isn't in MODEL_CHANGELOG" in p for p in hr.check_draft(paraphrased, CLOG))
    commentary = "## What changed\n\n> " + real + "\n\nThis should help the card a lot.\n"
    assert any("isn't a changelog quote" in p for p in hr.check_draft(commentary, CLOG))


def test_quoted_changelog_lines_may_use_rule_words():
    """a changelog quote can say 'going forward'; the check only polices the draft's own words"""
    md = "## What changed\n\n> " + "A tough defense costs a leg one grade step going forward." + "\n"
    assert all("rule-making" not in p for p in hr.check_draft(md, "A tough defense costs a leg one grade step going forward."))


def test_prompt_carries_every_house_rule_and_the_tag_glossary():
    blk = hr.prompt_block()
    assert all(f"  {k}: " in blk for k in hr.house_rules())
    assert "SOFT = HIGH volume" in blk and "own volume low" in blk
    system = open(os.path.join(AUTO, "newsletter", "prompts", "system.md"), encoding="utf-8").read()
    assert "{{HOUSE_RULES}}" in system and "Never invent, extend, propose or announce a rule" in system
    receipts = open(os.path.join(AUTO, "newsletter", "prompts", "receipts.md"), encoding="utf-8").read()
    assert "## What changed" in receipts and "concrete rule or model adjustments" not in receipts


def test_receipts_changelog_window_is_the_last_seven_days():
    got = [e["date"] for e in hr.changelog_entries(*hr.receipts_window(date(2026, 10, 13)))]
    assert got and all("2026-10-07" <= d <= "2026-10-13" for d in got)
    assert "2026-10-02" not in got


def test_draft_rewrites_once_then_flags(monkeypatch, capsys):
    import draft
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.setattr(sys, "argv", ["draft.py", "--kind", "receipts", "--season", "2026", "--week", "5"])
    calls = []
    def bad_then_good(system, user):
        calls.append(user)
        assert "HOUSE RULES" in system and "{{HOUSE_RULES}}" not in system
        return INVENTED if len(calls) == 1 else "## What changed\n\nNothing changed this week.\n"
    monkeypatch.setattr(draft, "claude", bad_then_good)
    draft.main()
    out = capsys.readouterr().out
    assert len(calls) == 2 and "broke these rules" in calls[1] and "DRAFT CHECK FAILED" not in out

    calls.clear()
    monkeypatch.setattr(draft, "claude", lambda s, u: (calls.append(u), INVENTED)[1])
    draft.main()
    out = capsys.readouterr().out
    assert len(calls) == 2                                              # one rewrite, no more
    assert "DRAFT CHECK FAILED" in out and "draft check failed" in out  # warning on top of the draft, and in the log
