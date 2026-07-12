"""
Edge Index — NFL Coaching & Scheme Database 2024-2026
Source: NFL_Coaches_Schemes_2024_2026.csv (Gemini) with corrections applied.

CORRECTIONS APPLIED vs original CSV:
  2025 NE  HC: Jerod Mayo → Mike Vrabel
  2025 NO  HC: Dennis Allen → Kellen Moore
  2025 LV  HC: Antonio Pierce → Pete Carroll
  2025 CHI HC: Matt Eberflus → Ben Johnson
  2025 DAL HC: Mike McCarthy → Brian Schottenheimer
  2026 NE  HC: Jerod Mayo → Mike Vrabel (same)
  2026 NO  HC: Dennis Allen → Kellen Moore (same)

IMPORTANT NOTE ON 2025/2026 DATA:
  Scheme stats (zone%, blitz%, avg depth) for 2025+ are
  PROJECTIONS based on coordinator history, not real results.
  Replace with real PFF/TruMedia data when available.
"""

import csv, io, os

_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                    "NFL_Coaches_Schemes_2024_2026.csv")

# HC corrections — Gemini errors
_HC_CORRECTIONS = {
    ("2025","NE"):  "Mike Vrabel",
    ("2025","NO"):  "Kellen Moore",
    ("2025","LV"):  "Pete Carroll",
    ("2025","CHI"): "Ben Johnson",
    ("2025","DAL"): "Brian Schottenheimer",
    ("2026","NE"):  "Mike Vrabel",
    ("2026","NO"):  "Kellen Moore",
    ("2026","LV"):  "Pete Carroll",
    ("2026","CHI"): "Ben Johnson",
    ("2026","DAL"): "Brian Schottenheimer",
}

def load_schemes():
    """
    Load all coaching/scheme data into a dict keyed by (year, team).
    Returns dict with full row data plus computed edge flags.
    """
    if not os.path.exists(_CSV):
        print(f"WARNING: {_CSV} not found. Copy CSV to backtest folder.")
        return {}

    schemes = {}
    with open(_CSV) as f:
        for row in csv.DictReader(f):
            year = row["Year"]
            team = row["Team"]

            # Apply HC corrections
            hc = _HC_CORRECTIONS.get((year, team), row["Head_Coach"])

            # Parse zone/man split
            zm = row.get("Zone_vs_Man_Pct","50/50").split("/")
            zone_pct = int(zm[0]) if len(zm)==2 else 50
            man_pct  = 100 - zone_pct

            blitz_rate = float(row.get("Blitz_Rate_Pct", 25))
            slot_grade = float(row.get("Slot_Corner_Grade", 70))
            avg_dot    = float(row.get("Avg_Depth_Of_Target", 8))
            rb_share   = float(row.get("RB_Target_Share_Pct", 14))
            slot_usage = float(row.get("Slot_Usage_Pct", 50))

            rp = row.get("Run_Pass_Ratio","45/55").split("/")
            run_pct  = int(rp[0]) if len(rp)==2 else 45
            pass_pct = 100 - run_pct

            schemes[(year, team)] = {
                # Coaching staff
                "year":       year,
                "team":       team,
                "hc":         hc,
                "oc":         row["Offensive_Coordinator"],
                "dc":         row["Defensive_Coordinator"],
                # Offensive tendencies
                "off_system": row["Offensive_System"],
                "avg_dot":    avg_dot,
                "run_pct":    run_pct,
                "pass_pct":   pass_pct,
                "rb_share":   rb_share,
                "slot_usage": slot_usage,
                # Defensive tendencies
                "def_shell":  row["Primary_Coverage_Shell"],
                "zone_pct":   zone_pct,
                "man_pct":    man_pct,
                "blitz_rate": blitz_rate,
                "slot_cb":    row["Slot_Corner_Name"],
                "slot_grade": slot_grade,
                "coverage_notes": row.get("Coverage_Allowed_Notes",""),
                # Computed edge flags
                "rb_dump_off_edge":    zone_pct >= 65 and rb_share >= 16,
                "slot_wr_edge":        zone_pct >= 70 and slot_grade < 72,
                "te_crossing_edge":    zone_pct >= 65 and "seam" in row.get("Coverage_Allowed_Notes","").lower(),
                "blitz_pass_yds_edge": blitz_rate >= 35,
                "short_game_off":      avg_dot <= 7.5 and rb_share >= 16,
            }

    return schemes

def get_matchup_edges(offense_team, defense_team, year, player_pos, prop_type):
    """
    Given an offensive player's team vs a defensive team,
    return scheme-based probability adjustments.

    Returns: dict with adjustment float and explanation list
    """
    schemes = load_schemes()
    yr = str(year)

    off = schemes.get((yr, offense_team), {})
    def_ = schemes.get((yr, defense_team), {})

    if not off or not def_:
        return {"adjustment": 0.0, "notes": [], "edge": False}

    adj   = 0.0
    notes = []
    edge  = False

    zone_pct   = def_.get("zone_pct", 50)
    blitz_rate = def_.get("blitz_rate", 25)
    slot_grade = def_.get("slot_grade", 72)
    rb_share   = off.get("rb_share", 14)
    off_dot    = off.get("avg_dot", 8)
    def_notes  = def_.get("coverage_notes","").lower()

    # ── RB receiving vs zone ────────────────────────────────────────────
    if player_pos == "RB" and prop_type in ("receptions","rec_yds"):
        if zone_pct >= 65:
            adj += 0.10
            notes.append(f"{defense_team} zone ({zone_pct}%) → RB dump-offs open")
            edge = True
        if off.get("short_game_off") and zone_pct >= 60:
            adj += 0.05
            notes.append(f"{offense_team} short game system + zone = double edge")
            edge = True
        if "rb screens open" in def_notes:
            adj += 0.04
            notes.append(f"{defense_team} scheme notes: RB screens open")

    # ── Slot WR vs zone + weak slot corner ─────────────────────────────
    elif player_pos == "WR" and prop_type in ("rec_yds","receptions"):
        if zone_pct >= 70 and slot_grade < 72:
            adj += 0.12
            notes.append(f"{defense_team} zone ({zone_pct}%) + weak slot CB "
                         f"{def_.get('slot_cb')} ({slot_grade:.0f} grade)")
            edge = True
        elif zone_pct >= 65:
            adj += 0.06
            notes.append(f"{defense_team} zone ({zone_pct}%) opens WR windows")
        if "slot underneath" in def_notes or "short underneath" in def_notes:
            adj += 0.04
            notes.append(f"Scheme note: slot underneath routes open")

    # ── TE crossing routes vs zone ──────────────────────────────────────
    elif player_pos == "TE" and prop_type in ("rec_yds","receptions"):
        if zone_pct >= 65 and ("seam" in def_notes or "mid te" in def_notes):
            adj += 0.12
            notes.append(f"{defense_team} zone vulnerable to TE seam routes")
            edge = True
        elif zone_pct >= 60:
            adj += 0.06
            notes.append(f"{defense_team} zone ({zone_pct}%) creates TE windows")

    # ── QB pass yards vs blitz ──────────────────────────────────────────
    elif player_pos == "QB" and prop_type in ("pass_yds","pass_att"):
        if blitz_rate >= 40:
            adj += 0.08
            notes.append(f"{defense_team} blitz rate {blitz_rate}% → quick shots, big plays")
            edge = True
        elif blitz_rate >= 30:
            adj += 0.04
            notes.append(f"{defense_team} moderate blitz rate {blitz_rate}%")
        # Mobile QBs in favorable rushing situations
        if prop_type == "pass_yds" and zone_pct >= 70:
            adj -= 0.04
            notes.append(f"Heavy zone suppresses explosive pass plays")

    # ── Short passing offense vs zone bonus ────────────────────────────
    if off.get("short_game_off") and zone_pct >= 65 and player_pos in ("WR","TE","RB"):
        adj += 0.03
        notes.append(f"{offense_team} short game system ({off_dot:.1f} avg DOT) thrives vs zone")

    # ── Blitz rate edge for any skill player ───────────────────────────
    if blitz_rate >= 40 and player_pos in ("WR","TE") and prop_type in ("rec_yds","receptions"):
        adj += 0.05
        notes.append(f"Heavy blitz creates 1-on-1 opportunities for receivers")
        edge = True

    return {
        "adjustment": round(adj, 3),
        "notes":      notes,
        "edge":       edge,
        "def_shell":  def_.get("def_shell",""),
        "def_dc":     def_.get("dc",""),
        "slot_cb":    def_.get("slot_cb",""),
        "slot_grade": slot_grade,
        "zone_pct":   zone_pct,
        "blitz_rate": blitz_rate,
    }

def print_top_edges(year="2025"):
    """Print the best scheme matchup edges for a given year."""
    schemes = load_schemes()
    yr      = str(year)
    teams   = [t for (y,t) in schemes if y==yr]

    print(f"\nTOP SCHEME EDGES — {year}")
    print("="*65)

    edges = []
    for off_team in teams:
        for def_team in teams:
            if off_team == def_team:
                continue
            # Check RB dump-off edge
            result = get_matchup_edges(off_team, def_team, year, "RB", "receptions")
            if result["adjustment"] >= 0.12:
                edges.append((result["adjustment"], off_team, "RB", "receptions",
                              def_team, result["notes"]))
            # Check WR slot edge
            result = get_matchup_edges(off_team, def_team, year, "WR", "rec_yds")
            if result["adjustment"] >= 0.14:
                edges.append((result["adjustment"], off_team, "WR", "rec_yds",
                              def_team, result["notes"]))
            # Check TE edge
            result = get_matchup_edges(off_team, def_team, year, "TE", "rec_yds")
            if result["adjustment"] >= 0.12:
                edges.append((result["adjustment"], off_team, "TE", "rec_yds",
                              def_team, result["notes"]))

    edges.sort(reverse=True)
    for adj, off, pos, prop, def_t, notes in edges[:15]:
        print(f"\n+{adj:.0%} | {off} {pos} {prop} vs {def_t}")
        for note in notes:
            print(f"  → {note}")

if __name__ == "__main__":
    import shutil, os
    # Copy CSV to backtest folder if running from outputs
    src = '/mnt/user-data/uploads/NFL_Coaches_Schemes_2024_2026.csv'
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'NFL_Coaches_Schemes_2024_2026.csv')
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)

    schemes = load_schemes()
    print(f"Loaded {len(schemes)} team-year records")
    print(f"Years: {sorted(set(y for y,t in schemes))}")
    print(f"Teams: {len(set(t for y,t in schemes))}")

    # Sample edge lookup
    print("\nSAMPLE: SF WR rec_yds vs ATL (2025)")
    result = get_matchup_edges("SF","ATL","2025","WR","rec_yds")
    print(f"  Adjustment: {result['adjustment']:+.1%}")
    print(f"  Shell: {result['def_shell']}")
    print(f"  Slot CB: {result['slot_cb']} ({result['slot_grade']:.0f})")
    for n in result["notes"]:
        print(f"  → {n}")

    print_top_edges("2025")
