"""
parse_lines.py — turns raw DraftKings page pastes into the lines CSV the pipeline reads.

Save each DK prop page paste as a text file named by market:
    automation/lines/raw/w3/rec_yds.txt      (DK "Receiving Yards" page, select-all + copy + paste)
    automation/lines/raw/w3/receptions.txt
    automation/lines/raw/w3/pass_yds.txt
    automation/lines/raw/w3/pass_cmps.txt
    automation/lines/raw/w3/pass_att.txt
    automation/lines/raw/w3/rush_yds.txt
    automation/lines/raw/w3/rush_att.txt
Then:
    python automation/pipeline/parse_lines.py --season 2026 --week 3
Writes automation/lines/dk_2026_w3_all.csv and copies it to _tnf/_sun/_mnf (floors.py keeps only that slate's games).

Both DK paste formats are handled:
  A) page format:  "player image\\nName\\n\\n40+\\n\\n83+\\n−110\\n90+ ..."   (odds on the line after the main rung)
  B) link format:  "[Name](url)\\n40+50+83+−11090+100+ ..."                (everything on one line)
"""
import argparse, glob, os, re, shutil, sys
import pandas as pd

MARKETS = ["rec_yds", "receptions", "pass_yds", "pass_cmps", "pass_att", "rush_yds", "rush_att"]
RUNG = re.compile(r"^(\d+)\+$")
ODDS = re.compile(r"^[+\-−](\d{3,4})$")
LINK = re.compile(r"^\[(.+?)\]\(\S+\)\s*$")

def to_int(tok):
    return (-1 if tok[0] in "-−" else 1) * int(tok[1:])

def parse_page(text):
    lines = [l.strip() for l in text.splitlines()]
    out, player, i = {}, None, 0
    while i < len(lines):
        l = lines[i]
        if l == "player image":
            j = i + 1
            while j < len(lines) and not lines[j]: j += 1
            player = lines[j] if j < len(lines) else None; i = j + 1; continue
        m = RUNG.match(l)
        if m and player:
            j = i + 1
            while j < len(lines) and not lines[j]: j += 1
            if j < len(lines) and ODDS.match(lines[j]):
                out[player] = (float(m.group(1)), to_int(lines[j])); i = j
        i += 1
    return out

def parse_link_line(s):
    """'40+50+83+−11090+100+' -> main (83, -110). Odds are 3 digits unless a 4-digit read keeps rungs increasing."""
    toks = re.findall(r"(\d+)\+([+\-−]\d{3,4})?", s)
    rungs, main = [], None
    pos = 0
    # walk manually to resolve 3- vs 4-digit odds ambiguity
    i = 0
    while i < len(s):
        m = re.match(r"(\d+)\+", s[i:])
        if not m: i += 1; continue
        r = float(m.group(1)); i += m.end()
        om = re.match(r"([+\-−])(\d{3,4})", s[i:])
        if om:
            sign, digits = om.group(1), om.group(2)
            # prefer 3-digit odds if the remaining text still starts with a rung > r
            if len(digits) == 4:
                rest3 = s[i + 4:]; nxt = re.match(r"([1-9]\d*)\+", rest3)     # a rung never starts with 0
                if nxt and float(nxt.group(1)) > r: digits = digits[:3]
            main = (r, (-1 if sign in "-−" else 1) * int(digits)); i += 1 + len(digits)
        rungs.append(r)
    return main

def parse_links(text):
    out, player = {}, None
    for l in text.splitlines():
        l = l.strip()
        m = LINK.match(l)
        if m: player = m.group(1); continue
        if player and re.search(r"\d+\+", l):
            main = parse_link_line(l)
            if main: out[player] = main
            player = None
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--raw", default=None); a = ap.parse_args()
    raw = a.raw or f"automation/lines/raw/w{a.week}"
    if not os.path.isdir(raw): raw = f"lines/raw/w{a.week}"
    rows = []
    for mkt in MARKETS:
        p = os.path.join(raw, f"{mkt}.txt")
        if not os.path.exists(p): print(f"  (no {mkt}.txt)"); continue
        text = open(p, encoding="utf-8").read()
        got = parse_links(text) if "](" in text else parse_page(text)
        for player, (line, odds) in got.items(): rows.append((player, mkt, line, odds))
        print(f"  {mkt:<11} {len(got):>4} players")
    df = pd.DataFrame(rows, columns=["Player", "Market", "Line", "Odds"]).drop_duplicates(["Player", "Market"])
    base = os.path.dirname(os.path.dirname(raw))
    out = os.path.join(base, f"dk_{a.season}_w{a.week}_all.csv"); df.to_csv(out, index=False)
    for slate in ("tnf", "sun", "mnf"): shutil.copy(out, os.path.join(base, f"dk_{a.season}_w{a.week}_{slate}.csv"))
    print(f"wrote {out} ({len(df)} lines) + _tnf/_sun/_mnf copies")

if __name__ == "__main__":
    main()
