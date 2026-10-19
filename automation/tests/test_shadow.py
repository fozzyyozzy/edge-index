"""Configurable blend + shadow cards (research). The live blend is unchanged; shadow cards go to cards/shadow/, are never
published, are graded next to the live card on Tuesday, and never reach the newsletter."""
import json, os, subprocess, sys
import pandas as pd
import pytest
import yaml
from conftest import write_slate, run_card, row, GAMES, PIPE
from common import leg_prob, blend_prob, lower_window, LIVE_BLEND, BLEND_VARIANTS, MARKET_GAMES, PROB_CAP

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_live_blend_is_unchanged():
    assert LIVE_BLEND == dict(market_games=10, history_weight=None, cap=0.90) and BLEND_VARIANTS["live"][1] is LIVE_BLEND
    v = [5, 6, 3, 7, 8, 4, 6, 9, 2, 6, 5, 7, 6, 4, 8]
    h, g = 7, 10                                                         # L10 (7/10) is the lower add-one window here
    assert leg_prob(v, 5, 0.7) == pytest.approx(min((h + 1 + 10 * 0.7) / (g + 2 + 10), 0.90))


def test_variants_move_toward_the_market():
    h, g, pm = 10, 10, 0.70                                              # history 11/12 = 0.917, market 0.70
    p10, p20, p40 = (blend_prob(h, g, pm, mg, None, None) for mg in (10, 20, 40))
    assert p10 > p20 > p40 > pm
    assert blend_prob(h, g, pm, None, 0.10, 0.97) == pytest.approx(0.9 * 0.70 + 0.1 * 11 / 12)
    assert blend_prob(10, 10, 0.95, 10, None, 0.90) == 0.90 and blend_prob(10, 10, 0.95, None, 0.10, 0.97) > 0.90
    assert lower_window(9, 10, 13, 15) == (13, 15) and lower_window(8, 10, 14, 15) == (8, 10)


def test_reblend_live_reproduces_and_variants_shift():
    from grade_legs import reblend
    doc = dict(meta={}, players=[dict(player="P", market="receptions", last3=[5.0, 6.0, 4.0], opp_d="neutral",
                                      own_vol="neutral", target_competition=None,
                                      rungs=[dict(rung=3.0, est_odds=-300, l10="9/10", l15="13/15", novig_pct=72.0,
                                                  prob=0.0, grade="?", reasons=[])])])
    live = reblend(doc, LIVE_BLEND)["players"][0]["rungs"][0]
    assert live["prob"] == round(blend_prob(*lower_window(9, 10, 13, 15), 0.72, **LIVE_BLEND), 4)
    m40 = reblend(doc, BLEND_VARIANTS["m40"][1])["players"][0]["rungs"][0]
    assert m40["prob"] < live["prob"] and m40["edge_pts"] < live["edge_pts"]
    assert doc["players"][0]["rungs"][0]["prob"] == 0.0                  # the input document is not modified


def test_shadow_card_goes_to_its_own_folder_and_leaves_the_live_card_alone(slate_root):
    write_slate(slate_root, [row(f"S{i}", GAMES[i % 7], grade="A", odds=-250, edge=8) for i in range(10)])
    live = run_card(slate_root)
    before = open(os.path.join(slate_root, "cards", "card_2026_w9_sun.json"), encoding="utf-8").read()
    env = dict(os.environ, EDGE_ROOT=str(slate_root), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", "2026", "--week", "9",
                    "--slate", "sun", "--shadow", "m20"], env=env, check=True, capture_output=True)
    sh = json.load(open(os.path.join(slate_root, "cards", "shadow", "card_2026_w9_sun_m20.json"), encoding="utf-8"))
    assert sh["shadow"]["slug"] == "m20" and sh["shadow"]["blend"]["market_games"] == 20
    assert open(os.path.join(slate_root, "cards", "card_2026_w9_sun.json"), encoding="utf-8").read() == before
    assert live["tickets"]


def test_grade_scores_old_rule_and_new_rule_the_same_way(tmp_path, monkeypatch):
    import common, grade
    monkeypatch.setattr(common, "ROOT", str(tmp_path))
    leg = lambda p, rung, odds=-200: dict(player=p, market="receptions", rung=rung, odds_est=odds, published_odds=odds)
    os.makedirs(tmp_path / "cards" / "shadow")
    json.dump(dict(tickets=[dict(name="SUN-1", legs=[leg("A", 3), leg("B", 3)])]), open(tmp_path / "cards" / "card_2026_w9_sun.json", "w"))
    json.dump(dict(shadow=dict(slug="m20", label="market = 20 games", blend={}), tickets=[dict(name="SUN-1", legs=[leg("A", 3)])]),
              open(tmp_path / "cards" / "shadow" / "card_2026_w9_sun_m20.json", "w"))
    act = {("a", "receptions"): 5.0, ("b", "receptions"): 1.0}
    out = grade.shadow_vs_live(2026, 9, act)
    assert out["live"]["record"]["LOSS"] == 1 and out["live"]["legs_hit"] == 1 and out["live"]["legs_graded"] == 2
    assert out["m20"]["record"]["WIN"] == 1 and out["m20"]["units"] == 0.5
    monkeypatch.setattr(common, "ROOT", str(tmp_path / "empty"))
    assert grade.shadow_vs_live(2026, 9, act) is None


def test_newsletter_never_sees_shadow_results(tmp_path, monkeypatch):
    sys.path.insert(0, os.path.join(REPO, "automation", "newsletter"))
    import draft
    rec = tmp_path / "receipts_2026_w9.json"
    json.dump(dict(week=9, ticket_record={}, shadow={"m20": {"units": 9.9}}), open(rec, "w"))
    real_p = draft.P
    monkeypatch.setattr(draft, "P", lambda *p: str(rec) if p[0] == "receipts" else real_p(*p))
    seen = []
    monkeypatch.setattr(draft, "claude", lambda s, u: (seen.append(u), "## What changed\n\nNothing changed this week.\n")[1])
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.setattr(sys, "argv", ["draft.py", "--kind", "receipts", "--season", "2026", "--week", "9"])
    draft.main()
    assert seen and '"shadow"' not in seen[0] and "9.9" not in seen[0]


def test_card_workflow_builds_shadows_without_ever_blocking_or_publishing_them():
    wf = yaml.safe_load(open(os.path.join(REPO, ".github", "workflows", "card.yml"), encoding="utf-8"))
    steps = wf["jobs"]["run"]["steps"]; names = [s.get("name", "") for s in steps]
    i = next(k for k, n in enumerate(names) if n.startswith("shadow cards"))
    assert names.index(next(n for n in names if n.startswith("build card"))) < i
    assert "--shadow" in steps[i]["run"] and "::warning::" in steps[i]["run"]          # a failure only warns
    pub = next(s for s in steps if s.get("name") == "publish to site")["run"]
    assert "shadow" not in pub                                                           # never copied to the site
    assert json.load(open(os.path.join(REPO, "automation", "shadow_blends.json"))) == ["m20", "m40", "mkt10", "m40e0", "m40em1"]


def test_relaxed_r4_variants_are_shadow_only_and_keep_every_other_rule(slate_root):
    from common import SHADOW_RULES
    assert SHADOW_RULES == {"m40e0": {"min_edge": 0.0}, "m40em1": {"min_edge": -1.0}}
    assert BLEND_VARIANTS["m40e0"][1] == BLEND_VARIANTS["m40em1"][1] == BLEND_VARIANTS["m40"][1]
    import build_card_json
    assert build_card_json.MIN_EDGE_PTS == 2.0 and build_card_json.MAX_LEG_JUICE == -450      # live R4 / cap untouched
    write_slate(slate_root, [row(f"S{i}", GAMES[i % 7], grade="A", odds=-250, edge=8) for i in range(8)])
    env = dict(os.environ, EDGE_ROOT=str(slate_root), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", "2026", "--week", "9",
                    "--slate", "sun", "--shadow", "m40em1"], env=env, check=True, capture_output=True)
    sh = json.load(open(os.path.join(slate_root, "cards", "shadow", "card_2026_w9_sun_m40em1.json"), encoding="utf-8"))
    assert sh["shadow"]["min_edge"] == -1.0
    assert all(c["odds_est"] >= -450 and c["grade"] in ("A+", "A", "A-", "B", "C") for c in sh["candidates"])
