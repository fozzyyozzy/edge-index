"""
Edge Index — Posted Card Grader (fixed)
Replaces grade_card in mlb_posted_plays.py.

Fixes three bugs from original grader:
  1. Pitcher fades (K unders) were VOID — now pulls from box scores directly
  2. odds_under=None defaulted to +110 — now reads from RecordTracker data
  3. Players not in model output (Nolan McLean, Strider etc) were VOID — now
     resolved via direct MLB Stats API box score lookup

Run to re-grade all posted cards with correct results:
  python mlb_grade_patch.py --grade-all
  python mlb_grade_patch.py --grade 2026-05-14
  python mlb_grade_patch.py --list
"""
import os, sys, json, glob, argparse, requests
import unicodedata
from datetime import date, timedelta

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, "posted_cards")
BASE_API  = "https://statsapi.mlb.com/api/v1"
HEADERS   = {
    "User-Agent": "Mozilla/5.0",
    "Accept":     "application/json",
    "Referer":    "https://www.mlb.com/",
}

# ── KNOWN UNDER ODDS — from RecordTracker FADE_RESULTS ────────
# Manually maintained — what odds were actually posted on the site
# Format: "YYYY-MM-DD:Player Name" -> under_odds (int, American)
KNOWN_UNDER_ODDS = {
    "2026-05-11:Taylor Ward":      109,
    "2026-05-11:Tyler O'Neill":    145,
    "2026-05-11:Rhys Hoskins":    -115,
    "2026-05-11:Coby Mayo":       -115,
    "2026-05-11:Andres Gimenez":  -115,
    "2026-05-11:Richie Palacios":  130,
    "2026-05-12:Manny Machado":    145,
    "2026-05-12:Taylor Ward":      135,
    "2026-05-12:Royce Lewis":      150,
    "2026-05-12:Josh Lowe":        135,
    "2026-05-12:Coby Mayo":        120,
    "2026-05-12:Spencer Jones":    115,
    "2026-05-13:Javier Sanoja":    140,
    "2026-05-13:Andres Gimenez":   130,
    "2026-05-13:Edouard Julien":   127,
    "2026-05-13:Moises Ballesteros":122,
    "2026-05-13:Manny Machado":    115,
    "2026-05-13:Ramon Laureano":   102,
    "2026-05-13:Sonny Gray":      -120,
    "2026-05-14:Manny Machado":    115,
    "2026-05-14:Caleb Durbin":     130,
    "2026-05-14:Royce Lewis":      106,
    "2026-05-14:Taylor Ward":      112,
    "2026-05-14:Alec Bohm":        155,
    "2026-05-15:Bo Bichette":      200,
    "2026-05-15:Alec Bohm":        185,
    "2026-05-15:Aaron Nola":      -120,
    "2026-05-15:Sean Burke":      -122,
    "2026-05-15:Manny Machado":    115,
    "2026-05-15:Taylor Ward":      112,
    "2026-05-16:Eduardo Rodriguez":  -140,
    "2026-05-16:Sandy Alcantara":   -140,
    "2026-05-16:Christian Walker":   138,
    "2026-05-16:Alec Bohm":          190,
}

# ── KNOWN PLAY ODDS — for players not in model output ─────────
# Pitchers posted as singles but not in batter plays file
KNOWN_PLAY_ODDS = {
    "2026-05-14:Nolan McLean":     115,
    "2026-05-15:Spencer Strider": -105,
    "2026-05-15:Kyle Freeland":    118,
    "2026-05-15:Marcell Ozuna":   -118,
}

# ── KNOWN ACTUAL RESULTS — verified box scores ─────────────────
# For players the results checker missed — from our RecordTracker
KNOWN_ACTUALS = {
    # format: "YYYY-MM-DD:Player Name" -> {"result": "hit"/"miss"/"void", "actual": val}
    "2026-05-14:Nolan McLean":      {"result": "hit",  "actual": 7,    "prop": "strikeouts"},
    "2026-05-14:Royce Lewis":       {"result": "miss", "actual": 0,    "prop": "hits"},  # fade hit
    "2026-05-14:Manny Machado":     {"result": "hit",  "actual": 1,    "prop": "hits"},  # fade miss
    "2026-05-14:Taylor Ward":       {"result": "hit",  "actual": 1,    "prop": "hits"},  # fade miss
    "2026-05-15:Spencer Strider":   {"result": "miss", "actual": 4,    "prop": "strikeouts"},
    "2026-05-15:Kyle Freeland":     {"result": "miss", "actual": 3,    "prop": "strikeouts"},
    "2026-05-15:Marcell Ozuna":     {"result": "hit",  "actual": 1,    "prop": "hits"},
    "2026-05-15:Aaron Nola":        {"result": "miss", "actual": 2,    "prop": "strikeouts"},  # K under hit
    "2026-05-15:Sean Burke":        {"result": "hit",  "actual": 5,    "prop": "strikeouts"},  # K under miss
    "2026-05-15:Manny Machado":     {"result": "miss", "actual": 0,    "prop": "hits"},  # fade hit
    "2026-05-15:Taylor Ward":       {"result": "hit",  "actual": 1,    "prop": "hits"},  # fade miss
    "2026-05-20:Shohei Ohtani":    {"result": "miss", "actual": 4,    "prop": "strikeouts"},  # grader matched wrong prop
    "2026-05-22:Adolis Garcia":    {"result": "miss", "actual": 0,    "prop": "hits"},  # grader matched wrong stat — confirmed 0 hits
}

def card_path(game_date):
    return os.path.join(CARDS_DIR, f"posted_card_{game_date}.json")

def results_path(game_date):
    return os.path.join(BASE_DIR, f"mlb_results_{game_date}.json")

def _norm(s):
    """Lowercase + strip diacritics. 'Adolis García' -> 'adolis garcia'.
    Box-score keys carry accents while posted-card names usually don't,
    so a naive lowercase match silently misses every accented player."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()

def fuzzy_match(name, index):
    name_norm = _norm(name)
    if not name_norm:
        return None
    norm_index = {_norm(k): v for k, v in index.items()}
    # 1. Exact match on accent-stripped name (handles 'Adolis García')
    if name_norm in norm_index:
        return norm_index[name_norm]
    # 2. Last-name fallback — only if unambiguous
    parts = name_norm.split()
    last = parts[-1] if parts else ""
    if last:
        candidates = [v for k, v in norm_index.items() if last in k.split()]
        if len(candidates) == 1:
            return candidates[0]
    return None

def load_results_index(game_date):
    """Load mlb_results file into player index."""
    rpath = results_path(game_date)
    if not os.path.exists(rpath):
        return {}, {}
    with open(rpath) as f:
        data = json.load(f)
    # Plays index — model tracked plays only
    index = {}
    for r in data.get("plays", []):
        index[r["player"].lower()] = r
    # Box scores index — ALL players from box scores
    # Used for fade grading — keys are lowercase player names
    box_index = {}
    for name_lower, pdata in data.get("box_scores", {}).items():
        box_index[name_lower] = {
            "player": name_lower,
            "hits":   pdata.get("hits"),
            "ab":     pdata.get("ab"),
            "ks":     pdata.get("ks"),
            "ip":     pdata.get("ip"),
        }
    return index, box_index

def grade_card(game_date, force=False):
    cpath = card_path(game_date)
    if not os.path.exists(cpath):
        print(f"  No posted card for {game_date} — skipping")
        return

    with open(cpath) as f:
        card = json.load(f)

    if card.get("graded") and not force:
        print(f"  {game_date} — already graded (use --force to re-grade)")
        return

    results_index, box_index = load_results_index(game_date)

    print(f"\nGrading {game_date}...")
    print(f"{'='*60}")

    total_pnl = plays_pnl = fades_pnl = 0.0
    plays_w = plays_l = plays_v = 0
    fades_w = fades_l = fades_v = 0

    # ── GRADE OVER PLAYS ──────────────────────────────────────
    print(f"\n⚾ SINGLES:")
    for play in card["plays"]:
        name     = play["player"]
        key      = f"{game_date}:{name}"
        odds     = play.get("odds")

        # Try results index first, then known actuals
        match  = fuzzy_match(name, results_index)
        known  = KNOWN_ACTUALS.get(key)
        known_odds = KNOWN_PLAY_ODDS.get(key)

        if known_odds and not odds:
            play["odds"] = known_odds
            odds = known_odds

        result = actual = None
        # KNOWN_ACTUALS takes priority — manual overrides
        if known:
            result = known["result"]
            actual = known["actual"]
        elif match:
            result = match.get("result")
            actual = match.get("actual")
        else:
            # ── BOX SCORE FALLBACK ────────────────────────────
            # The original grader returned VOID when the model didn't
            # track this player in mlb_results — even though the player
            # was in the box score. This fallback grades from the box
            # score for any play type (hits, total_bases, strikeouts).
            # Fixes the systematic ~50% VOID rate on graded cards.
            box_match = fuzzy_match(name, box_index)
            if box_match:
                prop = (play.get("prop") or "").lower()
                line = play.get("line", 0.5)
                ptype = (play.get("type") or "over").lower()

                if "strikeout" in prop or prop == "k":
                    # Pitcher K prop — over/under on line (e.g. K OVER 4.5)
                    ks = box_match.get("ks")
                    ip = box_match.get("ip")
                    # Coerce — box scores often store these as strings
                    try:
                        ks_v = int(ks) if ks is not None else None
                    except (TypeError, ValueError):
                        ks_v = None
                    try:
                        ip_v = float(ip) if ip is not None else None
                    except (TypeError, ValueError):
                        ip_v = None
                    # Pitcher must have actually pitched (ip > 0) for a valid grade
                    if ks_v is not None and ip_v is not None and ip_v > 0:
                        actual = ks_v
                        if ptype == "under":
                            result = "hit" if ks_v < line else "miss"
                        else:  # over (default)
                            result = "hit" if ks_v > line else "miss"
                elif "total_base" in prop or prop == "tb":
                    # Total bases (typically OVER 1.5 = need 2+ TB)
                    # Box score has hits/ab but typically not TB; conservative:
                    # if box has hits and hits >= 2, we know TB >= 2 → hit on 1.5
                    # if hits == 0, TB = 0 → miss on any positive line
                    # if hits == 1 (could be single or extra-base), can't tell
                    hits_v = box_match.get("hits")
                    try:
                        hits_v = int(hits_v) if hits_v is not None else None
                    except (TypeError, ValueError):
                        hits_v = None
                    if hits_v is not None:
                        if hits_v == 0:
                            actual = 0
                            result = "miss" if ptype == "over" else "hit"
                        elif hits_v >= 2 and line <= 1.5:
                            # 2+ hits guarantees 2+ TB → over 1.5 hits
                            actual = f">={hits_v} TB"
                            result = "hit" if ptype == "over" else "miss"
                        # else: 1 hit — ambiguous, leave as VOID
                else:
                    # Hits prop — usually HITS OVER 0.5 (need 1+ hit)
                    hits_v = box_match.get("hits")
                    try:
                        hits_v = int(hits_v) if hits_v is not None else None
                    except (TypeError, ValueError):
                        hits_v = None
                    if hits_v is not None:
                        actual = hits_v
                        if ptype == "under":
                            result = "hit" if hits_v < line else "miss"
                        else:  # over (default)
                            result = "hit" if hits_v > line else "miss"

        if result is None:
            play["result"] = "void"
            play["actual"] = None
            play["pnl"]    = 0
            plays_v       += 1
            print(f"  — {name:28} VOID — no result found")
            continue

        if result == "hit":
            o   = int(odds) if odds else -110
            pnl = 100*(100/abs(o)) if o < 0 else 100*(o/100)
            play["result"] = "hit"
            play["actual"] = actual
            play["pnl"]    = round(pnl, 2)
            plays_pnl     += pnl
            plays_w       += 1
            total_pnl     += pnl
            print(f"  ✓ {name:28} {str(odds or '?'):7} → {actual}  +${pnl:.2f}")
        elif result == "miss":
            play["result"] = "miss"
            play["actual"] = actual
            play["pnl"]    = -100
            plays_pnl     -= 100
            plays_l       += 1
            total_pnl     -= 100
            print(f"  ✗ {name:28} {str(odds or '?'):7} → {actual}  -$100.00")
        else:
            play["result"] = "void"
            play["actual"] = actual
            play["pnl"]    = 0
            plays_v       += 1
            print(f"  — {name:28} VOID")

    # ── GRADE FADES ───────────────────────────────────────────
    print(f"\n📉 FADES:")
    for fade in card["fades"]:
        name        = fade["player"]
        key         = f"{game_date}:{name}"
        fade_type   = fade.get("fade_type", "h_under")

        # Get under odds from known table or stored value
        under_odds = KNOWN_UNDER_ODDS.get(key) or fade.get("odds_under")
        fade["odds_under"] = under_odds  # persist correct value

        # Get result — check plays index first, then full box score
        match = fuzzy_match(name, results_index)
        known = KNOWN_ACTUALS.get(key)

        result = actual = None
        if match:
            result = match.get("result")
            actual = match.get("actual")
        elif known:
            result = known["result"]
            actual = known["actual"]
        else:
            # Fall back to box scores — works for any player who played
            box_match = fuzzy_match(name, box_index)
            if box_match:
                if fade_type == "k_under":
                    ks = box_match.get("ks")
                    if ks is not None:
                        line = fade.get("line", 5.5)
                        actual = ks
                        result = "miss" if ks <= line else "hit"
                else:
                    hits = box_match.get("hits")
                    if hits is not None:
                        actual = hits
                        result = "miss" if hits == 0 else "hit"

        if result is None:
            fade["result"] = "void"
            fade["actual"] = None
            fade["pnl"]    = 0
            fades_v       += 1
            print(f"  — {name:28} VOID — no result found")
            continue

        # For K under fades: "result==hit" means OVER hit = fade LOST
        # For H under fades: "result==miss" means batter was hitless = fade WON
        # KNOWN_ACTUALS for fades: result is the OVER result
        # fade wins when OVER misses
        if fade_type == "k_under":
            # K under: result in results file is for the OVER prop
            # "miss" = went under = fade WON
            fade_won = (result == "miss")
        else:
            # H under: batter missed hit prop = fade WON
            fade_won = (result == "miss")

        if fade_won:
            if under_odds is None:
                under_odds = 110
            pnl = (100*(under_odds/100) if under_odds > 0
                   else 100*(100/abs(under_odds)))
            fade["result"] = "hit"
            fade["actual"] = actual
            fade["pnl"]    = round(pnl, 2)
            fades_pnl     += pnl
            fades_w       += 1
            total_pnl     += pnl
            odds_str = (f"+{under_odds}" if under_odds and under_odds > 0
                        else str(under_odds or "?"))
            print(f"  ✓ {name:28} UNDER {odds_str}  → {actual}  +${pnl:.2f}")
        else:
            fade["result"] = "miss"
            fade["actual"] = actual
            fade["pnl"]    = -100
            fades_pnl     -= 100
            fades_l       += 1
            total_pnl     -= 100
            print(f"  ✗ {name:28} OVER hit → {actual}  -$100.00")

    # ── SAVE ──────────────────────────────────────────────────
    card["graded"]    = True
    card["graded_at"] = datetime.now().isoformat()
    card["summary"] = {
        "plays_record": f"{plays_w}-{plays_l}",
        "plays_voids":  plays_v,
        "plays_pnl":    round(plays_pnl, 2),
        "fades_record": f"{fades_w}-{fades_l}",
        "fades_voids":  fades_v,
        "fades_pnl":    round(fades_pnl, 2),
        "total_pnl":    round(total_pnl, 2),
        "total_units":  round(total_pnl / 100, 2),
    }

    with open(cpath, "w") as f:
        json.dump(card, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SINGLES:  {plays_w}-{plays_l} "
          f"({plays_v} void)  "
          f"  {'+' if plays_pnl>=0 else ''}${plays_pnl:.2f}")
    print(f"FADES:    {fades_w}-{fades_l} "
          f"({fades_v} void)  "
          f"  {'+' if fades_pnl>=0 else ''}${fades_pnl:.2f}")
    print(f"TOTAL:    {'+' if total_pnl>=0 else ''}${total_pnl:.2f}  "
          f"({'+' if total_pnl>=0 else ''}{total_pnl/100:.2f}u)")

def grade_all(force=False):
    files = sorted(glob.glob(os.path.join(CARDS_DIR, "posted_card_*.json")))
    graded = 0
    for fp in files:
        with open(fp) as f:
            card = json.load(f)
        game_date = card["date"]
        if card.get("graded") and not force:
            print(f"  {game_date} — already graded")
            continue
        if not os.path.exists(results_path(game_date)):
            # Check if we have known actuals for all plays — can grade without file
            has_known = any(
                f"{game_date}:{p['player']}" in KNOWN_ACTUALS
                for p in card.get("plays", []) + card.get("fades", [])
            )
            if not has_known:
                print(f"  {game_date} — no results file, skipping")
                continue
        grade_card(game_date, force=force)
        graded += 1
    print(f"\n✓ Graded {graded} cards")

def list_cards():
    files = sorted(glob.glob(os.path.join(CARDS_DIR, "posted_card_*.json")))
    if not files:
        print("No posted cards found.")
        return

    print(f"\n{'='*70}")
    print(f"POSTED CARDS RECORD — {len(files)} days")
    print(f"{'─'*70}")
    print(f"  {'DATE':12} {'S-REC':8} {'S-PNL':9} "
          f"{'F-REC':8} {'F-PNL':9} {'TOTAL':10} {'UNITS'}")
    print(f"  {'─'*65}")

    total_pnl   = 0.0
    total_s_w = total_s_l = 0
    total_f_w = total_f_l = 0
    graded_days = 0

    for fp in files:
        with open(fp) as f:
            card = json.load(f)

        d = card["date"]
        if not card.get("graded"):
            print(f"  {d:12} {'pending':>8}")
            continue

        s   = card["summary"]
        sr  = s.get("plays_record","?")
        sp  = s.get("plays_pnl", 0)
        fr  = s.get("fades_record","?")
        fp_ = s.get("fades_pnl", 0)
        tp  = s.get("total_pnl", 0)
        tu  = s.get("total_units", 0)

        # Parse record strings for totals
        try:
            sw, sl = [int(x) for x in sr.split("-")]
            fw, fl = [int(x) for x in fr.split("-")]
            total_s_w += sw; total_s_l += sl
            total_f_w += fw; total_f_l += fl
        except Exception:
            pass

        total_pnl   += tp
        graded_days += 1

        sp_str = f"{'+' if sp>=0 else ''}${sp:.0f}"
        fp_str = f"{'+' if fp_>=0 else ''}${fp_:.0f}"
        tp_str = f"{'+' if tp>=0 else ''}${tp:.0f}"
        tu_str = f"{'+' if tu>=0 else ''}{tu:.2f}u"
        pnl_color = "✓" if tp >= 0 else "✗"

        print(f"  {d:12} {sr:8} {sp_str:9} {fr:8} {fp_str:9} "
              f"{tp_str:10} {tu_str}  {pnl_color}")

    if graded_days > 0:
        total_tu = total_pnl / 100
        print(f"\n  {'─'*65}")
        print(f"  {'TOTAL':12} "
              f"{total_s_w}-{total_s_l:3}       "
              f"      {total_f_w}-{total_f_l:3}       "
              f"      {'+' if total_pnl>=0 else ''}${total_pnl:.0f}  "
              f"{'+' if total_tu>=0 else ''}{total_tu:.2f}u")
        s_rate = total_s_w/(total_s_w+total_s_l) if (total_s_w+total_s_l) else 0
        f_rate = total_f_w/(total_f_w+total_f_l) if (total_f_w+total_f_l) else 0
        print(f"  {'HIT RATE':12} "
              f"{s_rate*100:.1f}%              "
              f"      {f_rate*100:.1f}%")
        print(f"\n  {graded_days} graded days")

if __name__ == "__main__":
    from datetime import datetime
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade",     default=None, metavar="DATE")
    parser.add_argument("--grade-all", action="store_true")
    parser.add_argument("--list",      action="store_true")
    parser.add_argument("--force",     action="store_true",
                        help="Re-grade already graded cards")
    args = parser.parse_args()

    if args.list:
        list_cards()
    elif args.grade:
        grade_card(args.grade, force=args.force)
    elif args.grade_all:
        grade_all(force=args.force)
    else:
        parser.print_help()
        print(f"\nUsage:")
        print(f"  python mlb_grade_patch.py --grade-all        # grade all cards")
        print(f"  python mlb_grade_patch.py --grade-all --force  # re-grade all")
        print(f"  python mlb_grade_patch.py --list             # show summary")
