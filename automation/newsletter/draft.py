"""
draft.py — writes a newsletter issue from structured JSON via the Claude API.
Substack has no posting API, so the issue is saved as Markdown in newsletter/drafts/ and, in Actions,
opened as a GitHub issue titled with the subject line. You copy it into Substack, edit, send.
(Beehiiv path kept behind --to beehiiv for later.)

  python newsletter/draft.py --kind card     --season 2026 --week 3 --slate sun
  python newsletter/draft.py --kind receipts --season 2026 --week 2
  python newsletter/draft.py --kind intro

Env: ANTHROPIC_API_KEY (GitHub secret). Beehiiv keys only if --to beehiiv.
Set DRY_RUN=1 to print the issue instead of saving it.
"""
import argparse, json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*p): return os.path.join(ROOT, *p)

MODEL = "claude-sonnet-4-6"

def claude(system, user):
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(model=MODEL, max_tokens=2500, system=system,
                               messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in r.content if b.type == "text")

def beehiiv_draft(subject, html):
    pub = os.environ["BEEHIIV_PUBLICATION_ID"]; key = os.environ["BEEHIIV_API_KEY"]
    body = json.dumps({"subject_line": subject, "preview_text": subject, "status": "draft",
                       "content": {"free": {"web": html, "email": html}}}).encode()
    req = urllib.request.Request(f"https://api.beehiiv.com/v2/publications/{pub}/posts", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["card", "receipts", "intro"], required=True)
    ap.add_argument("--season", type=int); ap.add_argument("--week", type=int); ap.add_argument("--slate")
    ap.add_argument("--to", choices=["file", "beehiiv"], default="file")
    a = ap.parse_args()

    system = open(P("newsletter", "prompts", "system.md")).read()
    tmpl = open(P("newsletter", "prompts", f"{a.kind}.md")).read()
    if a.kind == "card":
        data = json.load(open(P("cards", f"card_{a.season}_w{a.week}_{a.slate}.json")))
        subject = f"Week {a.week} {a.slate.upper()} card"
    elif a.kind == "receipts":
        data = json.load(open(P("receipts", f"receipts_{a.season}_w{a.week}.json")))
        subject = f"Week {a.week} receipts"
    else:
        data = {}; subject = "Edge Index: what this is, and the rules"
    user = tmpl.replace("{{DATA}}", json.dumps(data, indent=1, default=str))
    md = claude(system, user)

    if os.environ.get("DRY_RUN"):
        print(md); return
    if a.to == "file":
        os.makedirs(P("newsletter", "drafts"), exist_ok=True)
        slug = subject.lower().replace(" ", "_")
        path = P("newsletter", "drafts", f"{slug}.md")
        open(path, "w", encoding="utf-8").write(f"# {subject}\n\n{md}\n")
        open(P("newsletter", "drafts", "LATEST_SUBJECT.txt"), "w").write(subject)
        print("draft saved:", path); return
    try:
        import markdown; html = markdown.markdown(md, extensions=["tables"])
    except ImportError:
        html = "<pre>" + md + "</pre>"
    res = beehiiv_draft(subject, html)
    print("beehiiv draft saved:", res.get("data", {}).get("id"))

if __name__ == "__main__":
    main()
