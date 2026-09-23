"""
Batch alt-line runner
=====================
1. Parse DK ladder pastes (the text you copy off the DK props page) into ladders.
2. Pull your projections from the Model_Projections tab (Player | Market | Projection).
3. Run altline_engine on every player/market, write results to the Alt_Line_Edges tab.

Usage:
  python run_altlines.py dk_rec_yds.txt:rec_yds dk_recs.txt:receptions dk_pass_yds.txt:pass_yds dk_rush_yds.txt:rush_yds

Each .txt is one DK paste saved as a file. Rungs without odds are kept and scored
(model% + breakeven) so you can compare against DK by eye; rungs with odds get EV.
"""
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from altline_engine import evaluate, pick_win_rung, disagreement_flag
WIN_FLOOR = 0.75   # change with: python run_altlines.py --floor 0.80 ...
SHRINK = 0.4       # Final = market + SHRINK*(yours - market). --shrink 1.0 = trust your number fully

SHEET_ID = "1i-1V84KckPMk0wF7coklceT5m4JsO3HP63NMw9OrsrY"
CREDENTIALS_PATH = "edge-index-scraper-9eff2ef43944.json"
OUT_TAB = "Alt_Line_Edges"

RUNG_RE = re.compile(r"^(\d+)\+$")
ODDS_RE = re.compile(r"^[+\-−](\d{3,4})$")   # DK uses a unicode minus (U+2212)


def parse_dk_paste(text: str) -> Dict[str, List[Tuple[float, Optional[int]]]]:
    """Returns {player: [(threshold, odds_or_None), ...]}"""
    lines = [l.strip() for l in text.splitlines()]
    ladders: Dict[str, List[Tuple[float, Optional[int]]]] = {}
    player = None
    i = 0
    while i < len(lines):
        l = lines[i]
        if l == "player image":
            # next non-empty line is the player name
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            player = lines[j] if j < len(lines) else None
            if player:
                ladders[player] = []
            i = j + 1
            continue
        m = RUNG_RE.match(l)
        if m and player:
            threshold = float(m.group(1))
            odds = None
            # look ahead past blank lines for an odds token
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            if j < len(lines):
                om = ODDS_RE.match(lines[j])
                if om:
                    sign = -1 if lines[j][0] in "-−" else 1
                    odds = sign * int(om.group(1))
                    i = j
            ladders[player].append((threshold, odds))
        i += 1
    return {p: l for p, l in ladders.items() if l}


FLOOR7: Dict[Tuple[str, str], float] = {}
_SUFFIX = re.compile(r"\s+(jr\.?|sr\.?|ii|iii|iv)$", re.I)
_ALIAS = {"cameron ward": "cam ward", "d.j. moore": "dj moore"}
def norm_name(s: str) -> str:
    s = _SUFFIX.sub("", s.strip()).lower()
    return _ALIAS.get(s, s)

def load_projections_csv(path: str) -> Dict[Tuple[str, str], float]:
    import csv
    proj = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r.get("Final") or r.get("Projection")
            try:
                key = (norm_name(r["Player"]), r["Market"].strip())
                proj[key] = float(v)
                if r.get("Floor7"):
                    FLOOR7[key] = float(r["Floor7"])
            except (TypeError, ValueError, KeyError):
                pass
    return proj


def load_projections() -> Dict[Tuple[str, str], float]:
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    sh = gspread.authorize(creds).open_by_key(SHEET_ID)
    rows = sh.worksheet("Model_Projections").get_all_values()[1:]
    proj = {}
    for r in rows:
        if len(r) >= 3 and r[0] and r[1] and r[2]:
            try:
                proj[(norm_name(r[0]), r[1].strip())] = float(r[2])
            except ValueError:
                pass
    return proj, sh


def write_results(sh, results: List[dict]):
    try:
        ws = sh.worksheet(OUT_TAB)
    except Exception:
        ws = sh.add_worksheet(OUT_TAB, rows=2000, cols=14)
        ws.append_row(["Timestamp", "Player", "Market", "Projection", "Market_Median",
                       "Edge", "EV_Rung", "EV_Odds_est", "EV_Model_Pct", "EV_per_unit",
                       "WIN_Rung", "WIN_Odds_est", "WIN_Model_Pct", "Verdict"])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    out = []
    for r in results:
        b = r["best"]; w = r.get("win")
        edge = (r["projection"] - r["market_median"]) if r["projection"] else 0
        verdict = ("no projection" if not r["projection"] else "REVIEW" if r.get("review")
                   else "UNDER side" if edge < 0 else "BET" if (b or w) else "pass")
        out.append([ts, r["player"], r["market"], r["projection"], round(r["market_median"], 1), round(edge, 1),
                    b.threshold if b else "", b.odds if b else "", round(b.p_model*100, 1) if b else "", round(b.ev_per_unit, 3) if b else "",
                    w.threshold if w else "", w.odds if w else "", round(w.p_model*100, 1) if w else "", verdict])
    ws.append_rows(out, value_input_option="RAW")
    print(f"wrote {len(out)} rows to {OUT_TAB}")


def main(argv):
    global WIN_FLOOR, SHRINK
    if "--shrink" in argv:
        i = argv.index("--shrink"); SHRINK = float(argv[i+1]); argv = argv[:i] + argv[i+2:]
    if "--floor" in argv:
        i = argv.index("--floor"); WIN_FLOOR = float(argv[i+1]); argv = argv[:i] + argv[i+2:]
    proj_csv = None
    if "--proj" in argv:
        i = argv.index("--proj"); proj_csv = argv[i+1]; argv = argv[:i] + argv[i+2:]
    if not argv:
        print(__doc__)
        return
    proj, sh = load_projections()
    if proj_csv:
        proj.update(load_projections_csv(proj_csv))   # CSV overrides the sheet tab
    print(f"loaded {len(proj)} projections")
    results = []
    for arg in argv:
        path, market = arg.split(":")
        ladders = parse_dk_paste(open(path, encoding="utf-8").read())
        print(f"{path}: {len(ladders)} players")
        for player, ladder in ladders.items():
            raw = proj.get((norm_name(player), market))
            p = raw
            if raw is not None:
                # first pass with no projection just to learn the market median, then shrink toward it
                mkt = evaluate(player, market, ladder, projection=None)["market_median"]
                p = round(mkt + SHRINK * (raw - mkt), 1)
            try:
                res = evaluate(player, market, ladder, projection=p)
                res["raw_projection"] = raw
            except ValueError as e:
                print("  skip:", e)
                continue
            res["win"] = pick_win_rung(res, WIN_FLOOR, FLOOR7.get((norm_name(player), market))) if p else None
            res["review"] = disagreement_flag({"projection": raw, "market_median": res["market_median"]}, tol=0.6)
            results.append(res)
            if res["review"]:
                print(f"  REVIEW {player:<22} {market:<10} log {raw:g} -> shrunk {p:g} vs market {res['market_median']:.1f} -- check role")
            elif res["win"]:
                w = res["win"]
                print(f"  WIN  {player:<24} {market:<10} {w.threshold:g}+ {w.odds:+d} (est)  model {w.p_model*100:.1f}%  "
                      f"implied {w.p_implied*100:.1f}%  EV {w.ev_per_unit:+.2f}")
    write_results(sh, results)


if __name__ == "__main__":
    main(sys.argv[1:])
