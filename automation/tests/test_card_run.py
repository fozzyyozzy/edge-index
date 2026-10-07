"""What card.yml relies on: a slate with no floors or no lines can't crash the build, every new card has an availability
snapshot for QA, a brief nflverse outage is retried, and the workflow runs QA before anything publishes."""
import json, os
import pytest
import yaml
from conftest import write_slate, run_card, row, GAMES
import availability, card_qa

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def qa(root, slate="sun"):
    card = json.load(open(os.path.join(root, "cards", f"card_2026_w9_{slate}.json"), encoding="utf-8"))
    legs = json.load(open(os.path.join(root, "cards", f"legs_2026_w9_{slate}.json")))
    av = json.load(open(os.path.join(root, "cards", f"availability_2026_w9_{slate}.json")))
    return card, {r.split(":")[0]: (ok, d) for r, ok, d in card_qa.check(card, legs, av)}


def test_lines_but_no_qualifying_floor_is_a_zero_ticket_card_that_passes(slate_root):
    """floors.py writes a header-less CSV when nothing qualifies (Week 3 MNF-style slate)"""
    write_slate(slate_root, [row("Only", GAMES[0])], slate="mnf")
    open(os.path.join(slate_root, "floors", "floors_2026_w9_mnf.csv"), "w").write("\n")
    run_card(slate_root, slate="mnf")
    card, res = qa(slate_root, "mnf")
    assert card["tickets"] == [] and card["candidates"] == []
    assert all(ok for ok, _ in res.values()), {k: d for k, (ok, d) in res.items() if not ok}


def test_no_lines_for_the_slate_fails_qa_and_says_why(slate_root):
    """props not posted yet at 9am: legs file has no players -> QA fails, nothing publishes, re-run by hand later"""
    write_slate(slate_root, [], slate="mnf")
    open(os.path.join(slate_root, "floors", "floors_2026_w9_mnf.csv"), "w").write("\n")
    run_card(slate_root, slate="mnf")
    _, res = qa(slate_root, "mnf")
    ok, detail = next(v for k, v in res.items() if k.startswith("Data"))
    assert not ok and "no DK lines" in detail


def test_builder_writes_the_snapshot_when_grade_legs_did_not(tmp_path, monkeypatch):
    """the Week 4 TNF QA failure (card built before availability.py existed) can't happen to a new card: loading
    the snapshot for a build creates it when it's missing, so card_qa.py always has one to read"""
    monkeypatch.setenv("EDGE_ROOT", str(tmp_path))
    import common
    monkeypatch.setattr(common, "ROOT", str(tmp_path))
    stub = dict(season=2026, week=9, fetched_at="t", sources={}, team_games={}, players={})
    monkeypatch.setattr(availability, "build", lambda s, w, stats=None: stub)
    f = availability.path(2026, 9, "mnf")
    assert not os.path.exists(f)
    assert availability.load(2026, 9, "mnf") == stub
    assert os.path.exists(f) and json.load(open(f)) == stub


def test_card_workflow_runs_qa_before_anything_publishes():
    wf = yaml.safe_load(open(os.path.join(REPO, ".github", "workflows", "card.yml"), encoding="utf-8"))
    steps = wf["jobs"]["run"]["steps"]
    names = [s.get("name", "") for s in steps]
    idx = lambda key: next(i for i, n in enumerate(names) if key in n)
    assert idx("grade every rung") < idx("build card") < idx("card QA") < idx("publish to site")
    for key in ("publish to site", "draft card issue", "open GitHub issue", "commit"):
        assert "env.QA == 'pass'" in steps[idx(key)]["if"], key
    assert "legs_coverage.py" in steps[idx("card QA")]["run"]           # dropped Legs rungs show up in the checklist
    fail = steps[idx("QA failed")]
    assert "env.QA == 'fail'" in fail["if"] and 'CARD FAILED QA' in fail["run"] and "exit 1" in fail["run"]


def test_failed_scheduled_settle_and_refresh_retry_once_card_never():
    wf = yaml.safe_load(open(os.path.join(REPO, ".github", "workflows", "retry-failed.yml"), encoding="utf-8"))
    on = wf.get("on") or wf.get(True)                                   # PyYAML reads the key `on` as True
    assert sorted(on["workflow_run"]["workflows"]) == ["refresh-odds", "settle-results"]   # never card-build-and-draft
    job = wf["jobs"]["retry"]
    assert "conclusion == 'failure'" in job["if"] and "event == 'schedule'" in job["if"]    # a retry (dispatch) isn't retried
    steps = "\n".join(s.get("run", "") for s in job["steps"])
    assert "sleep 3600" in steps and "-f retry=true" in steps
    names = {yaml.safe_load(open(f, encoding="utf-8"))["name"] for f in
             (os.path.join(REPO, ".github", "workflows", n) for n in ("settle.yml", "refresh-odds.yml"))}
    assert names == {"settle-results", "refresh-odds"}                  # the names retry-failed listens for
    ro = open(os.path.join(REPO, ".github", "workflows", "refresh-odds.yml"), encoding="utf-8").read()
    assert 'github.event.inputs.retry }}" != "true"' in ro               # a retry uses the scheduled slot guard
