"""
Edge Index — MLB Weekly Pipeline
Pulls pitcher K props and batter hit/total base props.
Uses Baseball Savant via pybaseball + The Odds API.

Usage:
  python mlb_pipeline.py --date 2026-04-15
  python mlb_pipeline.py --date 2026-04-15 --dry-run
"""
import os, sys, json, argparse, sqlite3
from datetime import datetime, date
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE_URL     = "https://api.the-odds-api.com/v4"
SPORT        = "baseball_mlb"
BOOKS        = ["draftkings", "fanduel", "betmgm"]
DB_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlb.db")

# ── PARK FACTORS ─────────────────────────────────────────────
# Offensive park factor (1.0 = neutral, >1.0 = hitter friendly)
PARK_FACTORS = {
    "COL":1.18,"CIN":1.08,"PHI":1.06,"BOS":1.05,"HOU":1.04,
    "NYY":1.03,"MIL":1.02,"TEX":1.02,"ATL":1.01,"LAD":1.00,
    "CHC":1.00,"STL":0.99,"MIN":0.98,"DET":0.98,"TOR":0.97,
    "CLE":0.97,"PIT":0.96,"MIA":0.95,"SF":0.94,"SD":0.94,"SEA":0.93,
    "OAK":0.95,"TB":0.98,"BAL":0.99,"NYM":0.97,"WAS":0.99,
    "KC":0.98,"LAA":0.99,"ARI":1.02,"CWS":1.01,
}

# K-friendly parks (hitter-unfriendly = pitcher friendly for Ks)
K_PARK_ADJ = {k: 1.0 + (1.0 - v) * 0.5 for k, v in PARK_FACTORS.items()}

# ── UMPIRE K TENDENCIES ───────────────────────────────────────
UMPIRE_K_ADJ = {
    # High K rate umpires (boost pitcher K props)
    "Laz Diaz":         +0.08,
    "CB Bucknor":       +0.06,
    "Angel Hernandez":  +0.07,
    "Tom Hallion":      +0.05,
    "Jim Reynolds":     +0.05,
    # Low K rate umpires (fade K props)
    "Joe West":         -0.05,
    "Bill Miller":      -0.04,
    "Tim Timmons":      -0.03,
    "Brian Gorman":     -0.03,
    "Dana DeMuth":      -0.04,
}

# ── DB SETUP ─────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mlb_pitchers (
            player_id    TEXT,
            name         TEXT,
            team         TEXT,
            season       INTEGER,
            g            INTEGER,
            gs           INTEGER,
            ip           REAL,
            so           INTEGER,
            bb           INTEGER,
            h            INTEGER,
            era          REAL,
            whip         REAL,
            k_per_9      REAL,
            k_pct        REAL,
            PRIMARY KEY (player_id, season)
        );

        CREATE TABLE IF NOT EXISTS mlb_batters (
            player_id    TEXT,
            name         TEXT,
            team         TEXT,
            season       INTEGER,
            g            INTEGER,
            ab           INTEGER,
            h            INTEGER,
            hr           INTEGER,
            rbi          INTEGER,
            avg          REAL,
            obp          REAL,
            slg          REAL,
            k_pct        REAL,
            bb_pct       REAL,
            hard_hit_pct REAL,
            PRIMARY KEY (player_id, season)
        );

        CREATE TABLE IF NOT EXISTS mlb_pitcher_logs (
            player_id    TEXT,
            name         TEXT,
            team         TEXT,
            opp          TEXT,
            season       INTEGER,
            game_date    TEXT,
            game_num     INTEGER,
            ip           REAL,
            so           INTEGER,
            h            INTEGER,
            er           INTEGER,
            bb           INTEGER,
            pitch_count  INTEGER,
            PRIMARY KEY (player_id, season, game_date)
        );

        CREATE TABLE IF NOT EXISTS mlb_batter_logs (
            player_id    TEXT,
            name         TEXT,
            team         TEXT,
            opp          TEXT,
            season       INTEGER,
            game_date    TEXT,
            game_num     INTEGER,
            ab           INTEGER,
            h            INTEGER,
            hr           INTEGER,
            rbi          INTEGER,
            bb           INTEGER,
            k            INTEGER,
            tb           INTEGER,
            PRIMARY KEY (player_id, season, game_date)
        );

        CREATE TABLE IF NOT EXISTS mlb_prop_lines (
            player_id    TEXT,
            name         TEXT,
            prop_type    TEXT,
            line         REAL,
            odds         INTEGER,
            source       TEXT,
            game_date    TEXT,
            team         TEXT,
            opp          TEXT,
            PRIMARY KEY (player_id, prop_type, line, game_date, source)
        );
    """)
    conn.commit()
    return conn

# ── PYBASEBALL DATA PULLER ────────────────────────────────────
def pull_pitcher_logs(season, player_id=None):
    """
    Pull pitcher game logs via pybaseball statcast.
    Falls back to demo data if pybaseball unavailable.
    """
    try:
        import pybaseball
        pybaseball.cache.enable()

        if player_id:
            start = f"{season}-03-01"
            end   = f"{season}-11-01"
            data  = pybaseball.statcast_pitcher(start, end, player_id=player_id)

            if data.empty:
                return None

            # Aggregate to game level
            data['game_date'] = pd.to_datetime(data['game_date']).dt.date.astype(str)
            grouped = data.groupby('game_date').agg(
                so=('events', lambda x: (x.isin(['strikeout','strikeout_double_play'])).sum()),
                h=('events', lambda x: (x.isin(['single','double','triple','home_run'])).sum()),
                bb=('events', lambda x: (x.isin(['walk','hit_by_pitch'])).sum()),
                pitch_count=('pitch_number', 'max'),
            ).reset_index()

            return grouped

    except ImportError:
        print("  pybaseball not installed — using manual data")
    except Exception as e:
        print(f"  pybaseball error: {e}")

    return None

def pull_batter_logs(season, player_id=None):
    """Pull batter game logs via pybaseball."""
    try:
        import pybaseball
        pybaseball.cache.enable()

        if player_id:
            start = f"{season}-03-01"
            end   = f"{season}-11-01"
            data  = pybaseball.statcast_batter(start, end, player_id=player_id)

            if data.empty:
                return None

            data['game_date'] = pd.to_datetime(data['game_date']).dt.date.astype(str)
            grouped = data.groupby('game_date').agg(
                ab=('at_bat_number', 'nunique'),
                h=('events', lambda x: x.isin(['single','double','triple','home_run']).sum()),
                hr=('events', lambda x: (x=='home_run').sum()),
                bb=('events', lambda x: x.isin(['walk','hit_by_pitch']).sum()),
                k=('events', lambda x: x.isin(['strikeout','strikeout_double_play']).sum()),
                tb=('events', lambda x: (
                    x.isin(['single']).sum() * 1 +
                    x.isin(['double']).sum() * 2 +
                    x.isin(['triple']).sum() * 3 +
                    x.isin(['home_run']).sum() * 4
                )),
            ).reset_index()

            return grouped

    except Exception as e:
        print(f"  Batter log error: {e}")

    return None

# ── CONTEXT ENGINE ────────────────────────────────────────────
def pitcher_k_context(pitcher_name, opp_team, home_team,
                       pitcher_k_pct, opp_team_k_pct,
                       park_factor=1.0, umpire_adj=0.0,
                       pitcher_hand="R", days_rest=4,
                       prior_k_totals=None):
    """
    Full context model for pitcher K props.
    Returns model probability and analysis notes.
    """
    notes = []

    # ── BASE RATE ─────────────────────────────────────────────
    # Weighted blend of pitcher K rate vs team K rate
    base_k_rate = pitcher_k_pct * 0.65 + opp_team_k_pct * 0.35
    notes.append(f"Pitcher K%: {pitcher_k_pct*100:.1f}% | Opp K%: {opp_team_k_pct*100:.1f}%")

    # ── PARK FACTOR ───────────────────────────────────────────
    park_adj = K_PARK_ADJ.get(home_team, 1.0) - 1.0
    if abs(park_adj) > 0.02:
        direction = "pitcher-friendly" if park_adj > 0 else "hitter-friendly"
        notes.append(f"Park: {home_team} ({direction}, {park_adj:+.1%} K adj)")

    # ── UMPIRE ────────────────────────────────────────────────
    if abs(umpire_adj) > 0.02:
        direction = "high K rate" if umpire_adj > 0 else "low K rate"
        notes.append(f"Umpire: {direction} ({umpire_adj:+.1%})")

    # ── REST/FATIGUE ──────────────────────────────────────────
    rest_adj = 0.0
    if days_rest <= 3:
        rest_adj = -0.06
        notes.append(f"Short rest ({days_rest} days) — fatigue risk")
    elif days_rest >= 7:
        rest_adj = +0.03
        notes.append(f"Extra rest ({days_rest} days) — fresh arm")

    # ── STREAK ────────────────────────────────────────────────
    streak = 0
    l5_avg = 0
    if prior_k_totals and len(prior_k_totals) >= 3:
        l5 = prior_k_totals[-5:]
        l5_avg = np.mean(l5)
        for v in reversed(l5):
            if v >= 5:  # hitting at least 5 Ks
                streak += 1
            else:
                break
        if streak >= 3:
            notes.append(f"Active {streak}-start K streak (L5 avg: {l5_avg:.1f} Ks)")

    return {
        "base_k_rate":  round(base_k_rate, 3),
        "park_adj":     round(park_adj, 3),
        "umpire_adj":   round(umpire_adj, 3),
        "rest_adj":     round(rest_adj, 3),
        "streak":       streak,
        "l5_avg_k":     round(l5_avg, 1),
        "notes":        notes,
    }

def batter_hit_context(batter_name, pitcher_hand,
                        batter_avg, batter_vs_lhp, batter_vs_rhp,
                        park_factor=1.0, days_rest=1,
                        prior_hits=None, prior_tb=None):
    """Context model for batter hit/total base props."""
    notes = []

    # ── PLATOON ADVANTAGE ─────────────────────────────────────
    platoon_avg = batter_vs_lhp if pitcher_hand == "L" else batter_vs_rhp
    platoon_adj = platoon_avg - batter_avg
    if abs(platoon_adj) > 0.020:
        adv = "platoon advantage" if platoon_adj > 0 else "platoon disadvantage"
        notes.append(f"{adv} vs {pitcher_hand}HP ({platoon_avg:.3f} vs {batter_avg:.3f} season avg)")

    # ── PARK FACTOR ───────────────────────────────────────────
    park_adj = park_factor - 1.0
    if abs(park_adj) > 0.02:
        direction = "hitter-friendly" if park_adj > 0 else "pitcher-friendly"
        notes.append(f"Park factor: {direction} ({park_adj:+.1%})")

    # ── STREAK ────────────────────────────────────────────────
    hit_streak = 0
    if prior_hits and len(prior_hits) >= 3:
        for v in reversed(prior_hits):
            if v >= 1:
                hit_streak += 1
            else:
                break
        if hit_streak >= 5:
            notes.append(f"Active {hit_streak}-game hit streak")

    return {
        "platoon_avg":  round(platoon_avg, 3),
        "platoon_adj":  round(platoon_adj, 3),
        "park_adj":     round(park_adj, 3),
        "hit_streak":   hit_streak,
        "notes":        notes,
    }

# ── PRINT REPORT ──────────────────────────────────────────────
def print_mlb_playbook(pitcher_plays, batter_plays, game_date):
    print(f"\n{'='*65}")
    print(f"EDGE INDEX MLB — {game_date}")
    print(f"{'='*65}")

    if pitcher_plays:
        print(f"\n⚾ PITCHER STRIKEOUT PROPS")
        print(f"{'─'*65}")
        for p in sorted(pitcher_plays, key=lambda x: x["model_prob"], reverse=True):
            tier_icon = "⚡" if p["tier"]=="AUTO" else "★" if p["tier"]=="T1" else "◆"
            print(f"\n  {p['pitcher']} vs {p['opp']} ({p['home']})")
            print(f"  K OVER {p['line']}  |  Odds: {p['odds']}  |  Model: {p['model_prob']*100:.0f}%  {tier_icon} {p['tier']}")
            print(f"  L5 avg: {p['l5_avg_k']} Ks  |  Streak: {p['streak']} starts  |  K%: {p['base_k_rate']*100:.1f}%")
            for note in p["notes"][:3]:
                print(f"    → {note}")
            if p.get("alt_lines"):
                print(f"  Alt lines: {p['alt_lines']}")

    if batter_plays:
        print(f"\n🏃 BATTER HIT/TOTAL BASE PROPS")
        print(f"{'─'*65}")
        for p in sorted(batter_plays, key=lambda x: x["model_prob"], reverse=True):
            tier_icon = "⚡" if p["tier"]=="AUTO" else "★" if p["tier"]=="T1" else "◆"
            print(f"\n  {p['batter']} ({p['team']}) vs {p['opp']} {pitcher_hand_str(p.get('pitcher_hand','R'))}")
            print(f"  {p['prop'].upper()} OVER {p['line']}  |  Odds: {p['odds']}  |  Model: {p['model_prob']*100:.0f}%  {tier_icon} {p['tier']}")
            print(f"  Hit streak: {p['hit_streak']}g  |  vs pitcher: {p['platoon_avg']:.3f}")
            for note in p["notes"][:2]:
                print(f"    → {note}")

def pitcher_hand_str(h):
    return f"(vs {'LHP' if h=='L' else 'RHP'})"

# ── DEMO RUN ──────────────────────────────────────────────────
DEMO_PITCHERS = [
    {
        "pitcher": "Zack Wheeler", "team":"PHI", "opp":"NYM", "home":"PHI",
        "line": 6.5, "odds": -130,
        "pitcher_k_pct": 0.298, "opp_team_k_pct": 0.248,
        "pitcher_hand": "R", "days_rest": 5,
        "prior_ks": [8, 7, 6, 9, 7, 8, 6, 10, 7, 8],
        "umpire": "Laz Diaz",
    },
    {
        "pitcher": "Gerrit Cole", "team":"NYY", "opp":"BOS", "home":"NYY",
        "line": 7.5, "odds": -115,
        "pitcher_k_pct": 0.312, "opp_team_k_pct": 0.228,
        "pitcher_hand": "R", "days_rest": 4,
        "prior_ks": [9, 8, 6, 11, 8, 7, 9, 8, 10, 7],
        "umpire": "Tom Hallion",
    },
    {
        "pitcher": "Spencer Strider", "team":"ATL", "opp":"MIA", "home":"ATL",
        "line": 8.5, "odds": -120,
        "pitcher_k_pct": 0.378, "opp_team_k_pct": 0.265,
        "pitcher_hand": "R", "days_rest": 5,
        "prior_ks": [10, 9, 11, 8, 12, 10, 9, 11, 8, 10],
        "umpire": "Angel Hernandez",
    },
    {
        "pitcher": "Framber Valdez", "team":"HOU", "opp":"TEX", "home":"HOU",
        "line": 5.5, "odds": -140,
        "pitcher_k_pct": 0.225, "opp_team_k_pct": 0.238,
        "pitcher_hand": "L", "days_rest": 5,
        "prior_ks": [6, 5, 7, 4, 6, 5, 7, 6, 5, 8],
        "umpire": "Bill Miller",
    },
]

DEMO_BATTERS = [
    {
        "batter":"Freddie Freeman","team":"LAD","opp":"SD","home":"LAD",
        "prop":"hits","line":1.5,"odds":-130,
        "batter_avg":0.298,"batter_vs_lhp":0.312,"batter_vs_rhp":0.289,
        "pitcher_hand":"R","prior_hits":[2,1,2,1,2,2,1,2,1,2],
    },
    {
        "batter":"Juan Soto","team":"NYY","opp":"BOS","home":"NYY",
        "prop":"total_bases","line":1.5,"odds":-120,
        "batter_avg":0.288,"batter_vs_lhp":0.305,"batter_vs_rhp":0.278,
        "pitcher_hand":"R","prior_hits":[2,1,3,0,2,1,2,3,1,2],
        "prior_tb":[3,1,5,0,4,2,3,5,2,4],
    },
    {
        "batter":"Yordan Alvarez","team":"HOU","opp":"TEX","home":"HOU",
        "prop":"hits","line":1.5,"odds":-140,
        "batter_avg":0.302,"batter_vs_lhp":0.318,"batter_vs_rhp":0.295,
        "pitcher_hand":"L","prior_hits":[2,2,1,2,1,2,2,1,2,2],
    },
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",    default=date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--init-db", action="store_true")
    args = parser.parse_args()

    if args.init_db:
        conn = init_db()
        print(f"MLB database initialized: {DB_PATH}")
        conn.close()

    print(f"Edge Index MLB Pipeline — {args.date}")
    print(f"{'─'*65}")

    pitcher_plays = []
    batter_plays  = []

    # ── PROCESS PITCHERS ──────────────────────────────────────
    for p in DEMO_PITCHERS:
        ctx = pitcher_k_context(
            pitcher_name  = p["pitcher"],
            opp_team      = p["opp"],
            home_team     = p["home"],
            pitcher_k_pct = p["pitcher_k_pct"],
            opp_team_k_pct= p["opp_team_k_pct"],
            park_factor   = PARK_FACTORS.get(p["home"], 1.0),
            umpire_adj    = UMPIRE_K_ADJ.get(p["umpire"], 0.0),
            pitcher_hand  = p["pitcher_hand"],
            days_rest     = p["days_rest"],
            prior_k_totals= p["prior_ks"],
        )

        # Calculate probability of hitting K line
        prior = p["prior_ks"]
        l10   = sum(1 for k in prior[-10:] if k >= p["line"]) / min(10, len(prior))
        l5    = sum(1 for k in prior[-5:]  if k >= p["line"]) / min(5,  len(prior))

        streak = ctx["streak"]
        base   = l5 * 0.55 + l10 * 0.30

        # Adjustments
        adj = (
            ctx["park_adj"] * 0.5 +
            ctx["umpire_adj"] +
            ctx["rest_adj"] +
            (0.05 if streak >= 3 else 0)
        )

        model_prob = min(0.95, max(0.30, base + adj))

        if model_prob >= 0.80 and streak >= 3:
            tier = "AUTO"
        elif model_prob >= 0.65:
            tier = "T1"
        elif model_prob >= 0.55:
            tier = "T2"
        else:
            tier = "SKIP"

        if tier != "SKIP":
            pitcher_plays.append({
                **p, **ctx,
                "model_prob": round(model_prob, 3),
                "tier": tier,
                "l5": round(l5, 3),
                "l10": round(l10, 3),
                "alt_lines": [p["line"] - 1.0, p["line"] - 0.5],
            })

    # ── PROCESS BATTERS ───────────────────────────────────────
    for b in DEMO_BATTERS:
        ctx = batter_hit_context(
            batter_name   = b["batter"],
            pitcher_hand  = b["pitcher_hand"],
            batter_avg    = b["batter_avg"],
            batter_vs_lhp = b["batter_vs_lhp"],
            batter_vs_rhp = b["batter_vs_rhp"],
            park_factor   = PARK_FACTORS.get(b["home"], 1.0),
            prior_hits    = b["prior_hits"],
        )

        prior = b.get("prior_tb") or b["prior_hits"]
        l10   = sum(1 for v in prior[-10:] if v >= b["line"]) / min(10, len(prior))
        l5    = sum(1 for v in prior[-5:]  if v >= b["line"]) / min(5,  len(prior))

        base = l5 * 0.55 + l10 * 0.30
        adj  = ctx["platoon_adj"] * 0.3 + ctx["park_adj"] * 0.2

        model_prob = min(0.95, max(0.30, base + adj))

        if model_prob >= 0.78 and ctx["hit_streak"] >= 5:
            tier = "AUTO"
        elif model_prob >= 0.65:
            tier = "T1"
        elif model_prob >= 0.55:
            tier = "T2"
        else:
            tier = "SKIP"

        if tier != "SKIP":
            batter_plays.append({
                **b, **ctx,
                "model_prob": round(model_prob, 3),
                "tier": tier,
            })

    print_mlb_playbook(pitcher_plays, batter_plays, args.date)

    # Save output
    out = {
        "date": args.date,
        "generated": datetime.now().isoformat(),
        "pitcher_plays": pitcher_plays,
        "batter_plays":  batter_plays,
    }
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"mlb_plays_{args.date}.json"
    )
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved to mlb_plays_{args.date}.json")
