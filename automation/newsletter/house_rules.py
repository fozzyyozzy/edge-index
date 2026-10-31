"""
house_rules.py — what the newsletter draft writer is allowed to say about rules, and the check every draft must pass.

The rules come from one place: the rules docstring of pipeline/build_card_json.py (R1..R11, LOCK). Hold reasons come from
pipeline/grade.py HOLD_CATS. "What changed" comes only from automation/MODEL_CHANGELOG.md, quoted verbatim.
2026-10-13: the Week 5 receipts draft invented "TOUGH D + SOFT volume capped at B" and read SOFT volume backwards.
"""
import os, re, sys
from datetime import date, timedelta

AUTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(AUTO, "pipeline", "build_card_json.py")
CHANGELOG = os.path.join(AUTO, "MODEL_CHANGELOG.md")

GLOSSARY = """Tag meanings (never reverse these):
- opp_d (opponent defense vs this stat): SOFT = gives up a lot (favorable for the over), TOUGH = stingy (unfavorable),
  neutral/AVG = middle. A tough defense costs a leg one grade step on the Legs board; it is not a hold.
- own_vol (the player's own team volume of that play type): SOFT = HIGH volume (favorable; shown "VOL HIGH" on the
  site), TOUGH = LOW volume (unfavorable; a hold: "own volume low"), neutral/AVG = middle.
- Grades A+ > A > A- > B > C > D > F grade the blended hit probability; F = a hard hold.
- Flags (one ticket max, not holds): "injury watch" (limited practice, or missed the game before last), "QB change"
  (a different QB led the team's last game than most of its last 10)."""


def house_rules(path=BUILDER):
    """{"LOCK": text, "R1": text, ...} parsed from build_card_json.py's rules docstring (continuation lines joined)."""
    src = open(path, encoding="utf-8").read()
    doc = src.split('"""')[1]
    rules, cur = {}, None
    for line in doc.splitlines():
        m = re.match(r"^  (LOCK|R\d+)\s+(.*)", line)
        if m:
            cur = m.group(1); rules[cur] = m.group(2).strip(); continue
        if cur and line.startswith("      ") and line.strip():
            rules[cur] += " " + line.strip(); continue
        if cur and not line.strip(): cur = None
        elif cur and not line.startswith(" "): cur = None
    return rules


def hold_reasons():
    sys.path.insert(0, os.path.join(AUTO, "pipeline"))
    from grade import HOLD_CATS
    return [name for _, name in HOLD_CATS]


def prompt_block():
    rules = house_rules()
    return ("HOUSE RULES (the only rules that exist; cite them by id, never invent, extend or propose one):\n"
            + "\n".join(f"  {k}: {v}" for k, v in rules.items())
            + "\nHold reasons the card uses: " + ", ".join(hold_reasons()) + ".\n\n" + GLOSSARY)


def changelog_entries(since, until, path=CHANGELOG):
    """[{date, title, text}] for changelog entries dated since < date <= until (dates are the '## YYYY-MM-DD' headers).
    Entries titled "shadow only" (research that changes no card) are skipped: the newsletter only reports live changes."""
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"(?m)^## ", text)[1:]
    out = []
    for p in parts:
        m = re.match(r"(\d{4}-\d{2}-\d{2}) — (.*)", p.splitlines()[0])
        if not m: continue
        d = date.fromisoformat(m.group(1))
        if since < d <= until and "shadow only" not in m.group(2).lower():
            out.append(dict(date=m.group(1), title=m.group(2).strip(), text=("## " + p).strip()))
    return out


def receipts_window(today=None):
    """changes to report in a receipts issue: the 7 days up to and including the day it's written"""
    today = today or date.today()
    return today - timedelta(days=7), today


# ── the check every draft must pass ────────────────────────────────────────────────────────────────────────────────
RULE_MAKING = [r"\bgoing forward\b", r"\bfrom now on\b", r"\bnew rule\b", r"\brule change\b", r"\bis capped at\b",
               r"\bwill be (capped|held|excluded|blocked|required)\b",
               r"\bwe will (now )?(hold|cap|require|exclude|block|drop|add|change)\b", r"\bstarting next week\b",
               r"\bshould (be|have been) (a )?(harder |stricter |hard )?(filter|hold|cap)\b",
               r"\bshould push (a|the) leg below\b"]
NAMED = {"lock", "house", "floor star", "bloom", "blowout", "edge", "grade", "injury", "team change", "price cap",
         "reduced payout", "one ticket", "card", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11"}


def _norm(s): return re.sub(r"\s+", " ", s).strip()


def check_draft(md, changelog_text=None):
    """problems (strings) with a draft; [] = clean.
    1. every rule id (R<n>) must exist in build_card_json.py; every 'the <name> rule' must be a known rule name
    2. no rule-making language outside quoted changelog lines ('> ...')
    3. a '## What changed' section holds only verbatim changelog quotes (or 'Nothing changed this week.')"""
    rules = house_rules()
    changelog_text = changelog_text if changelog_text is not None else open(CHANGELOG, encoding="utf-8").read()
    clog = _norm(changelog_text.replace("**", ""))
    problems = []
    body = "\n".join(l for l in md.splitlines() if not l.lstrip().startswith(">"))      # quotes are the changelog's words
    for rid in sorted(set(re.findall(r"\bR\d{1,2}\b", body))):
        if rid not in rules: problems.append(f"mentions rule {rid}, which isn't in build_card_json.py's house rules")
    for name in re.findall(r"\bthe ([A-Za-z][\w\- ]{1,24}?) rule\b", body, re.I):
        if name.lower() not in NAMED: problems.append(f"mentions 'the {name} rule', which isn't a house rule")
    for pat in RULE_MAKING:
        for m in re.finditer(pat, body, re.I):
            a, b = max(0, m.start() - 60), min(len(body), m.end() + 60)
            problems.append(f"rule-making language outside a changelog quote: \"...{_norm(body[a:b])}...\"")
    sec = re.search(r"(?ms)^## What change[sd]?\b.*?$(.*?)(?=^## |\Z)", md)
    if re.search(r"(?m)^## What changes\b", md):
        problems.append("section must be '## What changed' (quoting the changelog), not '## What changes'")
    if sec:
        for line in sec.group(1).splitlines():
            s = line.strip()
            if not s or s == "---" or s.startswith("*What would change our mind") or s.startswith("_What would change our mind"): continue
            if s.lower().rstrip(".") == "nothing changed this week": continue
            if re.match(r"^from the (model )?change ?log", s, re.I): continue
            if s.startswith(">"):
                q = _norm(s.lstrip("> ").replace("**", ""))
                if q and q not in clog: problems.append(f"'What changed' quotes text that isn't in MODEL_CHANGELOG.md: \"{q[:120]}\"")
                continue
            problems.append(f"'What changed' has text that isn't a changelog quote: \"{s[:120]}\"")
    return list(dict.fromkeys(problems))
