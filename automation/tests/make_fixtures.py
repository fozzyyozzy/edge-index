"""
make_fixtures.py — golden-rebuild fixtures for test_golden.py.

Each case snapshots the inputs build_card_json.py reads (floors CSV, legs JSON, availability snapshot, ladders, DK main
lines, pull time, notes) from the commit that built that card, into tests/fixtures/<case>/ laid out like automation/.
expected_card.json is what the CURRENT builder makes from them. A rule change that moves any card must update
expected_card.json in the same commit (python automation/tests/make_fixtures.py --expected) — that is the point.

  python automation/tests/make_fixtures.py --extract      re-snapshot inputs from git (and build missing availability)
  python automation/tests/make_fixtures.py --expected     rebuild every expected_card.json with the current builder
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PIPE = os.path.join(REPO, "automation", "pipeline")
FIX = os.path.join(HERE, "fixtures")

# case -> (commit the inputs come from, season, week, slate, why that commit)
CASES = {
    "2026_w4_sun": ("a1d71f9c", 2026, 4, "sun", "grade-first rebuild, published 2026-10-02 20:20 UTC (prices 17:51 UTC)"),
    "2026_w4_tnf": ("64881c57", 2026, 4, "tnf", "R9 rebuild (no ticket), prices 2026-09-30 13:39 UTC"),
    # the Week 3 Sunday legs as published (7553b8e8) predate blended probabilities (no prob/edge_pts), so this case
    # uses the regraded Week 3 board on main (same prices, grades recomputed when blended probability shipped)
    "2026_w3_sun": ("25fc99f6", 2026, 3, "sun", "regraded Week 3 board (published card 7553b8e8 can't be rebuilt as-is)"),
    "2026_w3_tnf": ("25fc99f6", 2026, 3, "tnf", "regraded Week 3 board (the TNF legs as published predate blended probability)"),
    "2026_w3_mnf": ("61aade4", 2026, 3, "mnf", "Week 3 MNF card build"),
    "2026_w4_mnf": ("2d932a2", 2026, 4, "mnf", "Week 4 MNF card build"),
}

def inputs(season, week, slate):
    return [f"floors/floors_{season}_w{week}_{slate}.csv", f"cards/legs_{season}_w{week}_{slate}.json",
            f"cards/availability_{season}_w{week}_{slate}.json", f"lines/ladders_{season}_w{week}.csv",
            f"lines/dk_{season}_w{week}_{slate}.csv", f"lines/pulled_{season}_w{week}_{slate}.txt",
            f"lines/pulled_{season}_w{week}.txt", f"notes/notes_{season}_w{week}.md"]

def git_show(commit, rel):
    try:
        return subprocess.check_output(["git", "show", f"{commit}:automation/{rel}"], cwd=REPO, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None

def extract(case):
    commit, season, week, slate, why = CASES[case]
    root = os.path.join(FIX, case)
    shutil.rmtree(root, ignore_errors=True)
    for rel in inputs(season, week, slate):
        b = git_show(commit, rel)
        if b is None: continue
        os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
        open(os.path.join(root, rel), "wb").write(b)
    av = os.path.join(root, f"cards/availability_{season}_w{week}_{slate}.json")
    note = f"inputs from {commit}: {why}"
    if not os.path.exists(av):                       # cards built before availability.py existed: snapshot it now
        sys.path.insert(0, PIPE)
        import availability
        snap = availability.build(season, week)
        snap["players"] = {k: v for k, v in snap["players"].items() if not v.get("manual")}   # no manual file then
        json.dump(snap, open(av, "w", encoding="utf-8"), indent=1)
        note += f"; availability built {snap['fetched_at']} (none existed when the card was built)"
    json.dump(dict(case=case, commit=commit, season=season, week=week, slate=slate, note=note),
              open(os.path.join(root, "case.json"), "w"), indent=1)
    print(f"{case}: {note}")

def rebuild(case, out_dir=None):
    """run the current builder on a copy of the fixture; returns the card dict"""
    meta = json.load(open(os.path.join(FIX, case, "case.json")))
    tmp = out_dir or tempfile.mkdtemp(prefix=f"golden_{case}_")
    shutil.copytree(os.path.join(FIX, case), tmp, dirs_exist_ok=True)
    env = dict(os.environ, EDGE_ROOT=tmp, PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, os.path.join(PIPE, "build_card_json.py"), "--season", str(meta["season"]),
                    "--week", str(meta["week"]), "--slate", meta["slate"]], env=env, check=True, capture_output=True)
    f = os.path.join(tmp, "cards", f"card_{meta['season']}_w{meta['week']}_{meta['slate']}.json")
    card = json.load(open(f, encoding="utf-8"))
    if out_dir is None: shutil.rmtree(tmp, ignore_errors=True)
    return card

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true"); ap.add_argument("--expected", action="store_true")
    ap.add_argument("cases", nargs="*")
    a = ap.parse_args()
    for case in a.cases or list(CASES):
        if a.extract: extract(case)
        if a.expected:
            card = rebuild(case)
            json.dump(card, open(os.path.join(FIX, case, "expected_card.json"), "w", encoding="utf-8"), indent=1)
            print(f"{case}: expected_card.json -> {len(card['tickets'])} tickets: " +
                  " | ".join(f"{t['name']} {t['est_american']:+d}" for t in card["tickets"]))
