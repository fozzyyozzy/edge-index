"""
Edge Index — Posted Plays Logger
Locks in exactly what went public each day BEFORE results come in.
This is the ground truth for model validation — not the full model output.

Run AFTER finalizing the card, BEFORE deploying:
  python mlb_posted_plays.py --date 2026-05-16 ^
    --plays "Bryce Elder,Aaron Judge,Alejandro Osuna,Tyrone Taylor,Caleb Durbin" ^
    --fades "Eduardo Rodriguez,Sandy Alcantara,Christian Walker,Alec Bohm"

Backfill past dates:
  python mlb_posted_plays.py --date 2026-05-15 ^
    --plays "Spencer Strider,Kyle Freeland,Marcell Ozuna,Aaron Judge,Colson Montgomery,Bryan Reynolds,Mike Trout" ^
    --fades "Bo Bichette,Alec Bohm,Aaron Nola,Sean Burke,Manny Machado,Taylor Ward"

List all posted cards:
  python mlb_posted_plays.py --list

Show one day:
  python mlb_posted_plays.py --show 2026-05-16

Grade a completed day (after results file exists):
  python mlb_posted_plays.py --grade 2026-05-16
"""
import os, sys, json, argparse, glob
from datetime import date, datetime

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, "posted_cards")
os.makedirs(CARDS_DIR, exist_ok=True)

# ── HELPERS ───────────────────────────────────────────────────

def card_path(game_date):
    return os.path.join(CARDS_DIR, f"posted_card_{game_date}.json")

def results_path(game_date):
    return os.path.join(BASE_DIR, f"mlb_results_{game_date}.json")

def plays_path(game_date):
    return os.path.join(BASE_DIR, f"mlb_plays_{game_date}.json")

def k_unders_path(game_date):
    return os.path.join(BASE_DIR, f"mlb_k_unders_{game_date}.json")

def lines_path(game_date):
    return os.path.join(BASE_DIR, f"mlb_lines_{game_date}.json")

def load_under_odds(game_date):
    """Build a name -> real UNDER odds index from the day's odds-puller output.
    The under-odds the book offered are stored in mlb_lines_*.json as
    prop 'hits_under' / 'strikeouts_under' (side 'under'); the posted-card
    builder previously hardcoded odds_under=None and the grader fell back to
    +110. This captures the actual number at post time.

    Prefers DraftKings (matches the card's source book), then the best (most
    plus / least negative) available, so a fade's payout reflects reality."""
    path = lines_path(game_date)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    # name(lower) -> {"hits": [(book, odds), ...], "strikeouts": [...]}
    buckets = {}
    for p in data.get("props", []):
        prop = p.get("prop", "")
        if p.get("side") != "under":
            continue
        if prop == "hits_under":
            kind = "hits"
        elif prop == "strikeouts_under":
            kind = "strikeouts"
        else:
            continue
        nm = (p.get("player") or "").strip().lower()
        if not nm:
            continue
        buckets.setdefault(nm, {}).setdefault(kind, []).append(
            (p.get("book", ""), p.get("odds")))

    def pick(offers):
        if not offers:
            return None
        # prefer draftkings if present
        dk = [o for b, o in offers if b == "draftkings" and o is not None]
        if dk:
            return dk[0]
        vals = [o for _, o in offers if o is not None]
        if not vals:
            return None
        # "best" under price for the bettor = highest american number
        try:
            return max(vals, key=lambda x: int(x))
        except (TypeError, ValueError):
            return vals[0]

    index = {}
    for nm, kinds in buckets.items():
        index[nm] = {
            "hits": pick(kinds.get("hits", [])),
            "strikeouts": pick(kinds.get("strikeouts", [])),
        }
    return index

def load_plays_file(game_date):
    """Load full model output to pull signal data for posted players.

    When a player has multiple entries (e.g. hits + total_bases), keep
    the entry from the highest-priority tier. Prevents the bug where
    a player's AUTO hits play was selected by auto_pick but the SKIP
    or VALUE_TB_SHADOW total_bases entry got written to the card
    (because the latter happened to load last and overwrote the index).
    """
    path = plays_path(game_date)
    if not os.path.exists(path):
        return {}

    with open(path) as f:
        data = json.load(f)

    # Lower number = higher priority (kept when there are duplicates).
    # Ordering reflects which tier auto_pick is most likely to have
    # selected; we want the index to reflect the SAME entry.
    TIER_PRIORITY = {
        "AUTO": 0, "T1": 1, "VALUE_TB": 2, "T2": 3,
        "JUICE": 4, "VALUE_TB_SHADOW": 5, "SKIP": 6,
    }

    index = {}
    for p in data.get("pitcher_plays", []) + data.get("batter_plays", []):
        if not p:
            continue
        key = p["player"].lower()
        existing = index.get(key)
        if existing is None:
            index[key] = p
        else:
            new_pri = TIER_PRIORITY.get(p.get("tier", ""), 99)
            old_pri = TIER_PRIORITY.get(existing.get("tier", ""), 99)
            if new_pri < old_pri:
                index[key] = p  # new entry has higher priority
    return index

def load_k_unders_file(game_date):
    """Load K under analysis for fade signal data."""
    path = k_unders_path(game_date)
    if not os.path.exists(path):
        return {}

    try:
        with open(path) as f:
            data = json.load(f)
        index = {}
        for p in data.get("pitchers", []):
            if p:
                index[p.get("pitcher", "").lower()] = p
        return index
    except Exception:
        return {}

import unicodedata

def _norm(s):
    """Lowercase + strip diacritics. 'Adolis García' -> 'adolis garcia'.
    Critical because box-score keys carry accents ('garc\u00eda') while
    posted-card names usually don't ('Adolis Garcia'), so a naive lowercase
    comparison silently misses every accented player."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def fuzzy_match(name, index):
    """Match player name to plays index — handles partial matches and accents."""
    name_norm = _norm(name)
    if not name_norm:
        return None

    # Build a normalized view of the index keys once per call. Keys in the
    # index are already lowercased but may still carry accents.
    norm_index = {_norm(k): v for k, v in index.items()}

    # 1. Exact match on the accent-stripped name (handles 'Adolis García')
    if name_norm in norm_index:
        return norm_index[name_norm]

    # 2. Fall back to last-name substring — but only if it's unambiguous
    parts = name_norm.split()
    last = parts[-1] if parts else ""
    if last:
        candidates = [v for k, v in norm_index.items() if last in k.split()]
        if len(candidates) == 1:
            return candidates[0]
        # multiple matches on last name -> can't safely pick one; refuse

    return None

# ── CORE: LOG THE CARD ────────────────────────────────────────

def log_card(game_date, play_names, fade_names, note=""):
    """
    Save the posted card for a given date.
    Pulls signal data from plays/k-unders files automatically.
    """
    existing_path = card_path(game_date)
    if os.path.exists(existing_path):
        print(f"Card already exists for {game_date}.")
        resp = input("Overwrite? (y/n): ").strip().lower()
        if resp != "y":
            print("Aborted.")
            return

    plays_index    = load_plays_file(game_date)
    k_under_index  = load_k_unders_file(game_date)
    under_odds_idx = load_under_odds(game_date)

    # ── OVER PLAYS ────────────────────────────────────────────
    posted_plays = []
    for name in play_names:
        name = name.strip()
        if not name:
            continue

        match = fuzzy_match(name, plays_index)

        play_entry = {
            "player":     name,
            "type":       "over",
            # Signal data — pulled from model if available
            "prop":       match.get("prop")       if match else None,
            "line":       match.get("line")       if match else None,
            "odds":       match.get("odds")       if match else None,
            "tier":       match.get("tier")       if match else None,
            "model_prob": match.get("model_prob") if match else None,
            "l5":         match.get("l5")         if match else None,
            "l10":        match.get("l10")        if match else None,
            "streak":     match.get("streak")     if match else None,
            "home":       match.get("home")       if match else None,
            "opp":        match.get("opp")        if match else None,
            # Book implied probability
            "book_implied": None,  # calculated below
            # Results — filled in later by --grade
            "result":     None,
            "actual":     None,
            "pnl":        None,
        }

        # Calculate book implied probability
        if play_entry["odds"] is not None:
            odds = int(play_entry["odds"])
            if odds < 0:
                play_entry["book_implied"] = round(abs(odds) / (abs(odds) + 100), 4)
            else:
                play_entry["book_implied"] = round(100 / (odds + 100), 4)

            # Edge = model_prob - book_implied
            if play_entry["model_prob"] and play_entry["book_implied"]:
                play_entry["edge"] = round(
                    play_entry["model_prob"] - play_entry["book_implied"], 4)

        posted_plays.append(play_entry)

        status = "✓ signals loaded" if match else "⚠ no signal data"
        tier   = play_entry.get("tier") or "?"
        odds   = play_entry.get("odds") or "?"
        print(f"  PLAY  {name:28} {tier:6} {str(odds):8} {status}")

    # ── FADE PLAYS ────────────────────────────────────────────
    posted_fades = []
    for name in fade_names:
        name = name.strip()
        if not name:
            continue

        # Fades can be batters (from plays) or pitchers (from k-unders)
        match      = fuzzy_match(name, plays_index)
        k_match    = fuzzy_match(name, k_under_index)

        # Real UNDER odds captured from the day's lines file (was hardcoded
        # None, which forced the grader to assume +110). h_under -> hits,
        # k_under -> strikeouts.
        kind = "strikeouts" if k_match else "hits"
        uo = under_odds_idx.get(name.strip().lower(), {})
        real_under = uo.get(kind)

        fade_entry = {
            "player":      name,
            "type":        "fade",
            "fade_type":   "k_under" if k_match else "h_under",
            # Batter signal data
            "prop":        match.get("prop")       if match else None,
            "line":        match.get("line")       if match else None,
            "odds_over":   match.get("odds")       if match else None,
            "model_prob":  match.get("model_prob") if match else None,
            "l5":          match.get("l5")         if match else None,
            "l10":         match.get("l10")        if match else None,
            "streak":      match.get("streak")     if match else None,
            "home":        match.get("home")       if match else None,
            "opp":         match.get("opp")        if match else None,
            # Real under odds from lines file (None only if not found)
            "odds_under":  real_under,
            "book_implied_over":  None,
            "fade_edge":   None,
            # Results
            "result":      None,  # "hit" = under hit (fade won)
            "actual":      None,
            "pnl":         None,
        }

        # Book implied for OVER side (if in plays file)
        if fade_entry["odds_over"] is not None:
            odds = int(fade_entry["odds_over"])
            if odds < 0:
                fade_entry["book_implied_over"] = round(
                    abs(odds) / (abs(odds) + 100), 4)
            else:
                fade_entry["book_implied_over"] = round(
                    100 / (odds + 100), 4)

        posted_fades.append(fade_entry)

        status = "✓ signals loaded" if (match or k_match) else "⚠ no signal data"
        ft     = "K-UNDER" if k_match else "H-UNDER"
        uodisp = (f"U:{real_under:+d}" if isinstance(real_under, int)
                  else (f"U:{real_under}" if real_under not in (None, "")
                        else "U:?? (not in lines)"))
        print(f"  FADE  {name:28} {ft:8} {uodisp:18} {status}")

    # ── SAVE ──────────────────────────────────────────────────
    card = {
        "date":      game_date,
        "logged_at": datetime.now().isoformat(),
        "note":      note,
        "plays":     posted_plays,
        "fades":     posted_fades,
        "graded":    False,
    }

    with open(card_path(game_date), "w") as f:
        json.dump(card, f, indent=2)

    print(f"\n✓ Card saved: posted_cards/posted_card_{game_date}.json")
    print(f"  {len(posted_plays)} plays · {len(posted_fades)} fades")
    print(f"\n  Run tomorrow morning to grade:")
    print(f"  python mlb_posted_plays.py --grade {game_date}")

# ── GRADE: FILL IN RESULTS ────────────────────────────────────

def grade_card(game_date):
    """
    After results file exists, fill in outcomes for each posted play.
    Reads mlb_results_YYYY-MM-DD.json and matches to posted card.
    """
    cpath = card_path(game_date)
    rpath = results_path(game_date)

    if not os.path.exists(cpath):
        print(f"No posted card for {game_date}")
        print(f"Run: python mlb_posted_plays.py --date {game_date} --plays ...")
        return

    if not os.path.exists(rpath):
        print(f"No results file for {game_date}")
        print(f"Run: python mlb_results_checker.py --date {game_date}")
        return

    with open(cpath) as f:
        card = json.load(f)

    with open(rpath) as f:
        results = json.load(f)

    # Index results by player name
    results_index = {}
    for r in results.get("plays", []):
        results_index[r["player"].lower()] = r

    print(f"\nGrading posted card for {game_date}...")
    print(f"{'='*60}")

    total_pnl  = 0.0
    plays_pnl  = 0.0
    fades_pnl  = 0.0
    plays_w    = 0
    plays_l    = 0
    fades_w    = 0
    fades_l    = 0

    # ── GRADE OVER PLAYS ──────────────────────────────────────
    print(f"\n⚾ SINGLES:")
    for play in card["plays"]:
        match = fuzzy_match(play["player"], results_index)

        if not match:
            play["result"] = "void"
            play["actual"] = None
            play["pnl"]    = 0
            print(f"  — {play['player']:28} VOID — not in results")
            continue

        actual = match.get("actual")
        result = match.get("result")
        odds   = play.get("odds")

        if result == "hit":
            o   = int(odds) if odds else -110
            pnl = 100*(100/abs(o)) if o < 0 else 100*(o/100)
            play["result"] = "hit"
            play["actual"] = actual
            play["pnl"]    = round(pnl, 2)
            plays_pnl     += pnl
            plays_w       += 1
            total_pnl     += pnl
            print(f"  ✓ {play['player']:28} {str(odds):6} → {actual} "
                  f"+${pnl:.2f}")
        elif result == "miss":
            play["result"] = "miss"
            play["actual"] = actual
            play["pnl"]    = -100
            plays_pnl     -= 100
            plays_l       += 1
            total_pnl     -= 100
            print(f"  ✗ {play['player']:28} {str(odds):6} → {actual} "
                  f"-$100.00")
        else:
            play["result"] = "void"
            play["actual"] = actual
            play["pnl"]    = 0
            print(f"  — {play['player']:28} VOID")

    # ── GRADE FADES ───────────────────────────────────────────
    print(f"\n📉 FADES:")
    for fade in card["fades"]:
        match = fuzzy_match(fade["player"], results_index)

        if not match:
            fade["result"] = "void"
            print(f"  — {fade['player']:28} VOID — not in results")
            continue

        actual = match.get("actual")
        result = match.get("result")
        line   = fade.get("line") or 0.5

        # Fade wins if OVER missed (player stayed under)
        fade_won = (result == "miss")

        under_odds = fade.get("odds_under")
        try:
            under_odds = int(float(str(under_odds).replace("+", ""))) \
                if under_odds not in (None, "") else 110
        except (TypeError, ValueError):
            under_odds = 110  # default plus money if unparseable/unknown

        if fade_won:
            pnl = (100*(under_odds/100) if under_odds > 0
                   else 100*(100/abs(under_odds)))
            fade["result"] = "hit"
            fade["actual"] = actual
            fade["pnl"]    = round(pnl, 2)
            fades_pnl     += pnl
            fades_w       += 1
            total_pnl     += pnl
            print(f"  ✓ {fade['player']:28} UNDER → {actual} "
                  f"+${pnl:.2f}")
        else:
            fade["result"] = "miss"
            fade["actual"] = actual
            fade["pnl"]    = -100
            fades_pnl     -= 100
            fades_l       += 1
            total_pnl     -= 100
            print(f"  ✗ {fade['player']:28} OVER hit → {actual} "
                  f"-$100.00")

    # ── SUMMARY ───────────────────────────────────────────────
    card["graded"]    = True
    card["graded_at"] = datetime.now().isoformat()
    card["summary"] = {
        "plays_record": f"{plays_w}-{plays_l}",
        "plays_pnl":    round(plays_pnl, 2),
        "fades_record": f"{fades_w}-{fades_l}",
        "fades_pnl":    round(fades_pnl, 2),
        "total_pnl":    round(total_pnl, 2),
        "total_units":  round(total_pnl / 100, 2),
    }

    with open(cpath, "w") as f:
        json.dump(card, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SINGLES:  {plays_w}-{plays_l}  "
          f"  {'+' if plays_pnl>=0 else ''}${plays_pnl:.2f}")
    print(f"FADES:    {fades_w}-{fades_l}  "
          f"  {'+' if fades_pnl>=0 else ''}${fades_pnl:.2f}")
    print(f"TOTAL:    {'+' if total_pnl>=0 else ''}${total_pnl:.2f}  "
          f"({'+' if total_pnl>=0 else ''}{total_pnl/100:.2f}u)")
    print(f"\n✓ Graded card saved")

# ── LIST / SHOW ───────────────────────────────────────────────

def list_cards():
    """Show all posted cards and their status."""
    files = sorted(glob.glob(os.path.join(CARDS_DIR, "posted_card_*.json")))

    if not files:
        print("No posted cards found.")
        print(f"Cards directory: {CARDS_DIR}")
        return

    print(f"\n{'='*65}")
    print(f"POSTED CARDS — {len(files)} days")
    print(f"{'─'*65}")
    print(f"  {'DATE':12} {'PLAYS':7} {'FADES':7} "
          f"{'GRADED':8} {'P&L':10} {'RECORD'}")
    print(f"  {'─'*55}")

    total_pnl  = 0.0
    total_days = 0

    for fp in files:
        with open(fp) as f:
            card = json.load(f)

        d        = card["date"]
        n_plays  = len(card["plays"])
        n_fades  = len(card["fades"])
        graded   = "✓" if card.get("graded") else "pending"
        summary  = card.get("summary", {})
        pnl      = summary.get("total_pnl", 0)
        pr       = summary.get("plays_record", "-")
        fr       = summary.get("fades_record", "-")
        record   = f"S:{pr} F:{fr}" if card.get("graded") else "—"
        pnl_str  = (f"{'+' if pnl>=0 else ''}${pnl:.0f}"
                    if card.get("graded") else "—")

        if card.get("graded"):
            total_pnl  += pnl
            total_days += 1

        print(f"  {d:12} {n_plays:7} {n_fades:7} "
              f"{graded:8} {pnl_str:10} {record}")

    if total_days > 0:
        print(f"\n  {'─'*55}")
        print(f"  TOTAL ({total_days} graded days): "
              f"{'+' if total_pnl>=0 else ''}${total_pnl:.0f}  "
              f"({'+' if total_pnl>=0 else ''}{total_pnl/100:.2f}u)")

def show_card(game_date):
    """Show a single posted card in detail."""
    cpath = card_path(game_date)
    if not os.path.exists(cpath):
        print(f"No card for {game_date}")
        return

    with open(cpath) as f:
        card = json.load(f)

    print(f"\n{'='*65}")
    print(f"POSTED CARD — {game_date}")
    print(f"{'─'*65}")

    print(f"\n⚾ PLAYS ({len(card['plays'])}):")
    for p in card["plays"]:
        tier  = p.get("tier") or "?"
        odds  = p.get("odds") or "?"
        mp    = p.get("model_prob")
        bi    = p.get("book_implied")
        edge  = p.get("edge")
        res   = p.get("result") or "pending"
        pnl   = p.get("pnl")

        mp_str   = f"{mp*100:.0f}%" if mp else "?"
        bi_str   = f"{bi*100:.0f}%" if bi else "?"
        edge_str = f"{edge*100:+.1f}%" if edge else "?"
        res_str  = (f"✓ +${pnl:.2f}" if res=="hit"
                    else f"✗ -$100" if res=="miss"
                    else "— VOID" if res=="void"
                    else "PENDING")

        print(f"  {p['player']:28} {tier:5} {str(odds):7} "
              f"model:{mp_str:5} book:{bi_str:5} "
              f"edge:{edge_str:7} {res_str}")

    print(f"\n📉 FADES ({len(card['fades'])}):")
    for f_ in card["fades"]:
        ft    = f_.get("fade_type", "h_under").upper()
        bi    = f_.get("book_implied_over")
        res   = f_.get("result") or "pending"
        pnl   = f_.get("pnl")
        bi_str = f"{bi*100:.0f}% OVER implied" if bi else "?"
        res_str = (f"✓ +${pnl:.2f}" if res=="hit"
                   else f"✗ -$100" if res=="miss"
                   else "— VOID" if res=="void"
                   else "PENDING")

        print(f"  {f_['player']:28} {ft:8} {bi_str:20} {res_str}")

    if card.get("graded"):
        s = card["summary"]
        print(f"\n{'─'*65}")
        print(f"SINGLES: {s['plays_record']}  "
              f"{'+' if s['plays_pnl']>=0 else ''}${s['plays_pnl']:.2f}")
        print(f"FADES:   {s['fades_record']}  "
              f"{'+' if s['fades_pnl']>=0 else ''}${s['fades_pnl']:.2f}")
        print(f"TOTAL:   {'+' if s['total_pnl']>=0 else ''}${s['total_pnl']:.2f}  "
              f"({'+' if s['total_pnl']>=0 else ''}{s['total_units']:.2f}u)")

# ── BACKFILL ──────────────────────────────────────────────────

HISTORICAL_CARDS = {
    "2026-05-08": {
        "plays": ["Kyle Bradish","Connelly Early","Jacob Lopez","Max Fried"],
        "fades": [],
    },
    "2026-05-09": {
        "plays": ["Colson Montgomery","Ernie Clement","Miguel Vargas",
                  "Cam Schlittler","Joe Ryan","Edward Cabrera",
                  "Ketel Marte","Addison Barger","Nico Hoerner",
                  "Aaron Judge","Xander Bogaerts"],
        "fades": [],
    },
    "2026-05-10": {
        "plays": ["Bryce Elder","Noah Cameron","Logan Henderson",
                  "Ernie Clement","Nico Hoerner","Miguel Vargas",
                  "Jonathan Aranda","Xander Bogaerts","Rafael Devers",
                  "Aaron Judge","Colson Montgomery","Brendan Donovan"],
        "fades": [],
    },
    "2026-05-11": {
        "plays": ["Kevin Gausman","Jonathan Aranda","Junior Caminero",
                  "Aaron Judge","Lenyn Sosa","Ernie Clement",
                  "Pete Alonso","Gunnar Henderson"],
        "fades": ["Taylor Ward","Tyler O'Neill","Rhys Hoskins",
                  "Coby Mayo","Andres Gimenez","Richie Palacios"],
    },
    "2026-05-12": {
        "plays": ["Colson Montgomery","Aaron Judge","Miguel Vargas",
                  "Xander Bogaerts","Jonathan Aranda","Bryan Reynolds",
                  "Junior Caminero","Mickey Moniak","Zack Wheeler",
                  "Ernie Clement","Bo Bichette","Lenyn Sosa",
                  "Pete Alonso","Matt Vierling"],
        "fades": ["Manny Machado","Taylor Ward","Royce Lewis",
                  "Josh Lowe","Coby Mayo","Spencer Jones"],
    },
    "2026-05-13": {
        "plays": ["Gunnar Henderson","Dylan Cease","Mickey Moniak",
                  "Jacob Misiorowski","Colson Montgomery","Junior Caminero",
                  "Miguel Vargas","Tyrone Taylor","Xander Bogaerts",
                  "Jonathan Aranda","Ernie Clement"],
        "fades": ["Javier Sanoja","Andres Gimenez","Edouard Julien",
                  "Moises Ballesteros","Manny Machado","Ramon Laureano",
                  "Sonny Gray"],
    },
    "2026-05-14": {
        "plays": ["Nolan McLean","Chris Sale","Colson Montgomery",
                  "Bo Bichette","Xander Bogaerts","Nico Hoerner",
                  "Christian Walker","Seiya Suzuki","Mickey Moniak",
                  "Ryan Jeffers","Miguel Vargas"],
        "fades": ["Manny Machado","Caleb Durbin","Royce Lewis",
                  "Taylor Ward","Alec Bohm"],
    },
    "2026-05-15": {
        "plays": ["Spencer Strider","Kyle Freeland","Marcell Ozuna",
                  "Aaron Judge","Mike Trout","Colson Montgomery",
                  "Bryan Reynolds"],
        "fades": ["Bo Bichette","Alec Bohm","Aaron Nola","Sean Burke",
                  "Manny Machado","Taylor Ward"],
    },
}

def backfill_all():
    """Backfill posted cards for all historical dates."""
    print(f"Backfilling {len(HISTORICAL_CARDS)} historical cards...")
    for game_date, card_data in sorted(HISTORICAL_CARDS.items()):
        cpath = card_path(game_date)
        if os.path.exists(cpath):
            print(f"  {game_date} — already exists, skipping")
            continue

        plays_index = load_plays_file(game_date)
        posted_plays = []
        posted_fades = []

        for name in card_data["plays"]:
            match = fuzzy_match(name, plays_index)
            entry = {
                "player":     name,
                "type":       "over",
                "prop":       match.get("prop")       if match else None,
                "line":       match.get("line")       if match else None,
                "odds":       match.get("odds")       if match else None,
                "tier":       match.get("tier")       if match else None,
                "model_prob": match.get("model_prob") if match else None,
                "l5":         match.get("l5")         if match else None,
                "l10":        match.get("l10")        if match else None,
                "streak":     match.get("streak")     if match else None,
                "home":       match.get("home")       if match else None,
                "opp":        match.get("opp")        if match else None,
                "book_implied": None,
                "result":     None,
                "actual":     None,
                "pnl":        None,
            }
            if entry["odds"]:
                odds = int(entry["odds"])
                entry["book_implied"] = round(
                    abs(odds)/(abs(odds)+100) if odds<0 else 100/(odds+100), 4)
                if entry["model_prob"] and entry["book_implied"]:
                    entry["edge"] = round(
                        entry["model_prob"] - entry["book_implied"], 4)
            posted_plays.append(entry)

        for name in card_data["fades"]:
            match = fuzzy_match(name, plays_index)
            entry = {
                "player":     name,
                "type":       "fade",
                "fade_type":  "h_under",
                "prop":       match.get("prop")       if match else None,
                "line":       match.get("line")       if match else None,
                "odds_over":  match.get("odds")       if match else None,
                "model_prob": match.get("model_prob") if match else None,
                "l5":         match.get("l5")         if match else None,
                "l10":        match.get("l10")        if match else None,
                "streak":     match.get("streak")     if match else None,
                "home":       match.get("home")       if match else None,
                "opp":        match.get("opp")        if match else None,
                "odds_under": None,
                "book_implied_over": None,
                "result":     None,
                "actual":     None,
                "pnl":        None,
            }
            if entry["odds_over"]:
                odds = int(entry["odds_over"])
                entry["book_implied_over"] = round(
                    abs(odds)/(abs(odds)+100) if odds<0 else 100/(odds+100), 4)
            posted_fades.append(entry)

        card = {
            "date":      game_date,
            "logged_at": datetime.now().isoformat(),
            "note":      "backfilled",
            "plays":     posted_plays,
            "fades":     posted_fades,
            "graded":    False,
        }

        with open(cpath, "w") as f:
            json.dump(card, f, indent=2)

        print(f"  {game_date} — {len(posted_plays)} plays, "
              f"{len(posted_fades)} fades saved")

    print(f"\n✓ Backfill complete")
    print(f"Now grade each day:")
    print(f"  python mlb_posted_plays.py --grade-all")

def grade_all():
    """Grade all ungraded posted cards that have results files."""
    files = sorted(glob.glob(os.path.join(CARDS_DIR, "posted_card_*.json")))
    graded = 0

    for fp in files:
        with open(fp) as f:
            card = json.load(f)

        if card.get("graded"):
            continue

        game_date = card["date"]
        if not os.path.exists(results_path(game_date)):
            print(f"  {game_date} — no results file yet, skipping")
            continue

        print(f"\n{'─'*40}")
        grade_card(game_date)
        graded += 1

    print(f"\n✓ Graded {graded} cards")

# ── ENTRY POINT ───────────────────────────────────────────────

def auto_pick(game_date):
    """Auto-select today's plays and fades using audit-validated rules:

    SINGLES — odds-bucket aware per audit of 23 graded cards:
      AUTO:  -150 to -249   (kept: 71%/67% hit, +$12/bet — best AUTO bucket)
      AUTO:  -120 to -149   (REJECTED: 27% hit, -$53/bet — model overconfident)
      AUTO:  -250+ / +money (REJECTED: no positive data)
      T1:    +money to -119 (kept: 75-80% hit, +$29-63/bet)
      T1:    -120 to -149   (REJECTED: 62% hit, +$4/bet — marginal, bloats card)
      T1:    -150 to -199   (REJECTED: 30% hit, -$51/bet — T1 disaster zone)
      VALUE_TB: all kept    (audit pattern: 69% hit, +$45/bet)

    FADES — audit-tightened to drop loser bucket:
      under_odds >= -110 AND l14_avg < 0.100  (57% hit, +$20/bet EV)
      under_odds < -110 REJECTED (33% hit, -$29/bet — paying juice on fades loses)

    K-UNDERS: confidence != 'LOW' from mlb_k_unders_*.json
    CARD-EXISTS: post-once-then-lock (caller handles; this fn just picks)

    Returns (play_names, fade_names) lists of bare names matching the model files.
    """
    plays_p = plays_path(game_date)
    if not os.path.exists(plays_p):
        print(f"  ✗ No plays file for {game_date} — run pipeline first")
        return [], []

    with open(plays_p, encoding="utf-8") as f:
        plays_data = json.load(f)

    pitcher_plays = plays_data.get("pitcher_plays", []) or []
    batter_plays  = plays_data.get("batter_plays",  []) or []
    fade_plays    = plays_data.get("fade_plays",    []) or []

    # ── SINGLES (odds-bucket aware, based on audit data) ────────
    # Each tier has different profitable odds ranges per the 23-card audit:
    #   AUTO  profitable at -150 to -249    (71% / 67% hit)
    #   AUTO  unprofitable at -120 to -149  (27% hit, -$53/bet) — REJECT
    #   AUTO  unprofitable at -250+         (no data, presume bad)
    #   AUTO  unprofitable at +money        (small sample, lossy)
    #   T1    profitable at +money to -119  (75-80% hit, +$29-63/bet)
    #   T1    weak at -120 to -149          (62% hit, +$4/bet) — REJECT
    #     (positive EV but volume-heavy ~0.9/day, marginal value, bloats card)
    #   T1    unprofitable at -150 to -199  (30% hit, -$51/bet) — REJECT
    #   VALUE_TB always KEEP (audit showed 69% hit, +$45/bet)
    def passes_filter(p):
        tier = p.get("tier", "")
        if tier == "VALUE_TB":
            return True
        try:
            o = int(p.get("odds", 0))
        except (TypeError, ValueError):
            return False
        if tier == "AUTO":
            return -249 <= o <= -150
        if tier == "T1":
            return o >= -119  # captures +money, -101 to -119 only
        return False

    selected_plays = []
    for p in pitcher_plays + batter_plays:
        if not p:
            continue
        if not passes_filter(p):
            continue
        name = p.get("player", "").strip()
        if name and name not in selected_plays:
            selected_plays.append(name)

    # ── FADES (audit-tightened: l14<.100 AND under_odds >= -110) ──
    # Audit (74 graded fades) found:
    #   under_odds >= -110: 57% hit, +$20/bet EV (improved from +$15 by dropping <-110 bucket)
    #   under_odds <  -110: 33% hit, -$29/bet (REJECTED — paying juice on fades loses)
    #   By coldness: all graded fades had l14 < .080 in practice, so the .100 gate
    #     is functionally moot but kept as a safety net for any future edge case.
    selected_fades = []
    for f in fade_plays:
        if not f:
            continue
        try:
            l14 = float(f.get("l14_avg", 0.999))
        except (TypeError, ValueError):
            continue
        if l14 >= 0.100:
            continue
        # NEW: under_odds gate — skip if odds are -111 or worse
        u_odds = f.get("under_odds") or f.get("odds_under") or 110
        try:
            uo = int(u_odds)
        except (TypeError, ValueError):
            continue
        if uo < -110:
            continue
        name = f.get("player", "").strip()
        if name and name not in selected_fades:
            selected_fades.append(name)

    # ── K-UNDERS (include any with confidence > LOW) ───────────
    # mlb_k_unders_*.json is a top-level JSON array of play dicts,
    # not a wrapping object. Handle both shapes defensively.
    k_p = k_unders_path(game_date)
    if os.path.exists(k_p):
        try:
            with open(k_p, encoding="utf-8") as f:
                k_data = json.load(f)
            if isinstance(k_data, list):
                k_plays = k_data
            elif isinstance(k_data, dict):
                k_plays = k_data.get("plays", []) or k_data.get("k_unders", [])
            else:
                k_plays = []
            for k in k_plays:
                if not isinstance(k, dict):
                    continue
                conf = (k.get("confidence", "") or "").upper()
                if conf == "LOW":
                    continue
                name = k.get("player", "").strip()
                if name and name not in selected_fades:
                    selected_fades.append(name)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"  ⚠ Could not parse k_unders file: {e}")

    return selected_plays, selected_fades



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",       default=None)
    parser.add_argument("--plays",      default="",
                        help="Comma-separated player names for OVER plays")
    parser.add_argument("--fades",      default="",
                        help="Comma-separated player names for fade/under plays")
    parser.add_argument("--note",       default="")
    parser.add_argument("--grade",      default=None, metavar="DATE",
                        help="Grade a completed day")
    parser.add_argument("--grade-all",  action="store_true",
                        help="Grade all ungraded cards with results files")
    parser.add_argument("--list",       action="store_true",
                        help="List all posted cards")
    parser.add_argument("--show",       default=None, metavar="DATE",
                        help="Show detail for one card")
    parser.add_argument("--backfill",   action="store_true",
                        help="Backfill all historical cards from May 8")
    parser.add_argument("--auto",       action="store_true",
                        help="Auto-pick today's plays/fades from model output. "
                             "Audit-based rules: AUTO -150 to -249, T1 +money to -119, "
                             "all VALUE_TB; fades l14<.100 AND under_odds>=-110; "
                             "K-unders confidence>LOW. "
                             "Skips silently if a card already exists for the date.")
    args = parser.parse_args()

    if args.list:
        list_cards()

    elif args.show:
        show_card(args.show)

    elif args.grade:
        grade_card(args.grade)

    elif args.grade_all:
        grade_all()

    elif args.backfill:
        backfill_all()

    elif args.auto:
        game_date = args.date or str(date.today())
        existing = card_path(game_date)
        if os.path.exists(existing):
            print(f"  Card already exists for {game_date} - skipping (post-once-then-lock)")
            sys.exit(0)
        play_names, fade_names = auto_pick(game_date)
        if not play_names and not fade_names:
            print(f"  Auto-pick found no qualifying plays/fades for {game_date}")
            print(f"    Rules: AUTO -150 to -249, T1 +money to -119, all VALUE_TB; fades l14<.100 + under>=-110")
            sys.exit(0)
        print(f"\nAuto-posting card for {game_date}...")
        print(f"  Selected: {len(play_names)} plays | {len(fade_names)} fades")
        log_card(game_date, play_names, fade_names,
                 note="AUTO-POSTED via --auto mode")

    elif args.date:
        play_names = [p for p in args.plays.split(",") if p.strip()]
        fade_names = [f for f in args.fades.split(",") if f.strip()]

        if not play_names and not fade_names:
            print("No plays or fades specified.")
            print('Usage: python mlb_posted_plays.py --date 2026-05-16 '
                  '--plays "Player A,Player B" --fades "Player C"')
            sys.exit(1)

        print(f"\nLogging posted card for {args.date}...")
        log_card(args.date, play_names, fade_names, args.note)

    else:
        parser.print_help()
        print(f"\nQuick start:")
        print(f"  1. Backfill history:  python mlb_posted_plays.py --backfill")
        print(f"  2. Grade history:     python mlb_posted_plays.py --grade-all")
        print(f"  3. See summary:       python mlb_posted_plays.py --list")
        print(f"  4. Log today:         python mlb_posted_plays.py "
              f"--date {date.today()} --plays 'A,B,C' --fades 'D,E'")
