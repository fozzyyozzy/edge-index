"""
Edge Index — Defensive Scheme Engine
Adjusts prop probabilities based on opponent defensive scheme.

This is the matchup layer that sits ON TOP of the base model.
It answers: given this player vs this defense, does the
scheme create or suppress their prop value?

Key insight: Books price props using positional opponent rank.
They don't distinguish between:
  - Zone teams that allow slot yardage (bad for rec rank, good for slot)
  - Man teams that suppress slot but allow X receiver yards
  - Blitz teams that create big plays but reduce checkdowns
  
This scheme awareness is where lower-usage players become valuable.
"""

# ── Defensive scheme database ─────────────────────────────────────────────────
# Updated each offseason / when DC changes
# Coverage type: primary coverage shell
# Blitz rate: % of plays with 5+ rushers
# Zone rate: % of plays in zone coverage
# Man rate: % of plays in man coverage

DEFENSIVE_SCHEMES = {
    # ── Cover 2 / Tampa-2 (bend-don't-break zone) ─────────────────────────
    # Allows: slot yardage, TE crossing, RB dump-offs
    # Suppresses: deep shots, seam routes, X receiver
    "MIN": {
        "dc": "Brian Flores",
        "shell": "Tampa-2",
        "zone_rate": 0.72,
        "man_rate":  0.28,
        "blitz_rate": 0.18,
        "deep_allow": "LOW",      # suppresses vertical routes
        "slot_allow": "HIGH",     # zones create windows underneath
        "te_allow":   "HIGH",     # crossing routes kill Tampa-2
        "rb_rec_allow": "HIGH",   # checkdown heaven
        "notes": "Flores Tampa-2 — underneath routes always open. "
                 "RB dump-offs are the primary safety valve. "
                 "Slot WRs feast on the intermediate zones."
    },
    "SF": {
        "dc": "Nick Sorensen",
        "shell": "Cover-3",
        "zone_rate": 0.68,
        "man_rate":  0.32,
        "blitz_rate": 0.22,
        "deep_allow": "MEDIUM",
        "slot_allow": "HIGH",
        "te_allow":   "HIGH",
        "rb_rec_allow": "HIGH",
        "notes": "SF Cover-3 shells — curl/flat defenders leave "
                 "intermediate zones open. TEs on crossing routes "
                 "and RB screens are primary beneficiaries."
    },
    "BAL": {
        "dc": "Zach Orr",
        "shell": "Cover-2",
        "zone_rate": 0.64,
        "man_rate":  0.36,
        "blitz_rate": 0.24,
        "deep_allow": "LOW",
        "slot_allow": "HIGH",
        "te_allow":   "MEDIUM",
        "rb_rec_allow": "HIGH",
        "notes": "BAL Cover-2 with physical corners. Deep shots "
                 "suppressed. Short game and RB receiving opens up."
    },
    "KC": {
        "dc": "Steve Spagnuolo",
        "shell": "Match-Zone",
        "zone_rate": 0.60,
        "man_rate":  0.40,
        "blitz_rate": 0.28,
        "deep_allow": "MEDIUM",
        "slot_allow": "MEDIUM",
        "te_allow":   "LOW",      # Spagnuolo locks TEs
        "rb_rec_allow": "MEDIUM",
        "notes": "Spagnuolo match-zone — elite at disguising coverages. "
                 "TEs historically suppressed. Slot WRs get windows "
                 "but KC rotates well. Most efficient defense in league."
    },
    "PHI": {
        "dc": "Vic Fangio",
        "shell": "Cover-2",
        "zone_rate": 0.70,
        "man_rate":  0.30,
        "blitz_rate": 0.20,
        "deep_allow": "LOW",
        "slot_allow": "HIGH",
        "te_allow":   "HIGH",
        "rb_rec_allow": "HIGH",
        "notes": "Fangio Cover-2 is the softest shell in the league "
                 "for underneath routes. Notorious for surrendering "
                 "TE yardage and RB screens. But suppresses explosive plays."
    },

    # ── Heavy Man Coverage ─────────────────────────────────────────────────
    # Allows: WR1 yards (elite WRs win vs man), deep shots
    # Suppresses: slot WRs, RB dump-offs (CB stays on WR, S in box)
    "NYJ": {
        "dc": "Jeff Ulbrich",
        "shell": "Cover-1 Man",
        "zone_rate": 0.32,
        "man_rate":  0.68,
        "blitz_rate": 0.35,
        "deep_allow": "HIGH",     # man with single high = explosive plays
        "slot_allow": "LOW",
        "te_allow":   "MEDIUM",
        "rb_rec_allow": "LOW",    # extra DB in box, fewer checkdowns
        "notes": "NYJ press man with single high safety. "
                 "Elite WR1s win 1-on-1 and rack up yards. "
                 "Slot receivers get jammed. RB dump-offs contested. "
                 "WR1 rec yds OVER is the primary play vs NYJ."
    },
    "PIT": {
        "dc": "Teryl Austin",
        "shell": "Cover-3 Press",
        "zone_rate": 0.45,
        "man_rate":  0.55,
        "blitz_rate": 0.38,
        "deep_allow": "MEDIUM",
        "slot_allow": "LOW",
        "te_allow":   "LOW",
        "rb_rec_allow": "LOW",
        "notes": "PIT press coverage — physical at the line. "
                 "Slot and TE routes disrupted off the snap. "
                 "Only elite separation WRs consistently produce. "
                 "Chase, Jefferson, Hill win here. Slot WRs struggle."
    },
    "CLE": {
        "dc": "Jim Schwartz",
        "shell": "Cover-1",
        "zone_rate": 0.30,
        "man_rate":  0.70,
        "blitz_rate": 0.40,
        "deep_allow": "HIGH",
        "slot_allow": "LOW",
        "te_allow":   "LOW",
        "rb_rec_allow": "LOW",
        "notes": "Schwartz loves heavy man with single high. "
                 "Defense was bottom-5 in 2025 — good for WR1 props "
                 "but scheme suppresses slot and TE volume. "
                 "WR1 rec yds OVER is the play, everything else UNDER."
    },
    "NE": {
        "dc": "DeMarcus Covington",
        "shell": "Pattern-Match",
        "zone_rate": 0.50,
        "man_rate":  0.50,
        "blitz_rate": 0.25,
        "deep_allow": "MEDIUM",
        "slot_allow": "MEDIUM",
        "te_allow":   "LOW",
        "rb_rec_allow": "MEDIUM",
        "notes": "NE transitioning from Belichick era. "
                 "Pattern-match disguise — hard to predict. "
                 "TEs historically suppressed in NE schemes."
    },

    # ── Blitz-Heavy (benefits explosive plays, suppresses volume) ──────────
    "DAL": {
        "dc": "Mike Eberflus",
        "shell": "Cover-1 Blitz",
        "zone_rate": 0.35,
        "man_rate":  0.65,
        "blitz_rate": 0.48,
        "deep_allow": "HIGH",
        "slot_allow": "MEDIUM",
        "te_allow":   "MEDIUM",
        "rb_rec_allow": "LOW",
        "notes": "Eberflus aggressive blitz packages — NEW DC in 2025. "
                 "Installation period weakness weeks 1-6 (DC CHANGE EDGE). "
                 "High blitz rate creates 1-on-1 opportunities deep. "
                 "QB pass yds OVER and WR rec yds OVER are the plays."
    },
    "LAC": {
        "dc": "Jesse Minter",
        "shell": "Cover-2 Man",
        "zone_rate": 0.45,
        "man_rate":  0.55,
        "blitz_rate": 0.42,
        "deep_allow": "HIGH",
        "slot_allow": "LOW",
        "te_allow":   "MEDIUM",
        "rb_rec_allow": "LOW",
        "notes": "Minter blitz-heavy — creates big play opportunities. "
                 "WR1 rec yds OVER in 1-on-1 situations. "
                 "RB dump-off suppressed — backs stay in to block."
    },

    # ── Balanced / Multiple ────────────────────────────────────────────────
    "GB": {
        "dc": "Jeff Hafley",
        "shell": "Multiple",
        "zone_rate": 0.55,
        "man_rate":  0.45,
        "blitz_rate": 0.28,
        "deep_allow": "MEDIUM",
        "slot_allow": "MEDIUM",
        "te_allow":   "MEDIUM",
        "rb_rec_allow": "MEDIUM",
        "notes": "Hafley multiple scheme — hardest to predict. "
                 "No strong scheme tendencies. Use L6 rate as primary signal."
    },
    "DET": {
        "dc": "Aaron Glenn",
        "shell": "Cover-3",
        "zone_rate": 0.58,
        "man_rate":  0.42,
        "blitz_rate": 0.32,
        "deep_allow": "MEDIUM",
        "slot_allow": "HIGH",
        "te_allow":   "HIGH",
        "rb_rec_allow": "HIGH",
        "notes": "Glenn Cover-3 with aggressive corners. "
                 "Underneath zones open for slot and TE. "
                 "DET allows significant TE and slot yardage."
    },
    "HOU": {
        "dc": "Matt Burke",
        "shell": "Cover-3",
        "zone_rate": 0.60,
        "man_rate":  0.40,
        "blitz_rate": 0.30,
        "deep_allow": "MEDIUM",
        "slot_allow": "HIGH",
        "te_allow":   "HIGH",
        "rb_rec_allow": "HIGH",
        "notes": "HOU Cover-3 — slot routes and TE crossings available. "
                 "Defense improved in 2025 but still gives up underneath."
    },
}

# ── Offensive scheme database ─────────────────────────────────────────────────
# Quick game / short passing offenses get RB reception bonus vs zone

OFFENSIVE_SCHEMES = {
    "MIN": {
        "oc": "Wes Phillips",
        "style": "Quick-Release",
        "avg_depth_of_target": 7.2,  # yards, low = short game
        "rb_target_share": 0.18,     # RB gets 18% of targets
        "slot_usage": "HIGH",
        "te_usage": "HIGH",
        "notes": "Darnold quick release system — RBs and slot TEs "
                 "are primary checkdown options. Short game is identity."
    },
    "PHI": {
        "oc": "Kellen Moore",
        "style": "RPO/Short",
        "avg_depth_of_target": 7.8,
        "rb_target_share": 0.16,
        "slot_usage": "HIGH",
        "te_usage": "MEDIUM",
        "notes": "PHI RPO system — Hurts checks down frequently. "
                 "Barkley gets meaningful target share even as rusher."
    },
    "SF": {
        "oc": "Robert Saleh",
        "style": "Shanahan Zone/Short",
        "avg_depth_of_target": 8.1,
        "rb_target_share": 0.20,
        "slot_usage": "HIGH",
        "te_usage": "HIGH",
        "notes": "Shanahan system maximizes RB receiving. "
                 "McCaffrey receives 6-8 targets/game in this scheme. "
                 "TE crossings are a staple."
    },
    "BAL": {
        "oc": "Todd Monken",
        "style": "West Coast Spread",
        "avg_depth_of_target": 8.4,
        "rb_target_share": 0.12,
        "slot_usage": "MEDIUM",
        "te_usage": "HIGH",
        "notes": "Monken spread — Andrews gets deep target share. "
                 "Lamar designed runs reduce passing volume but "
                 "when passing, TE is the primary read."
    },
    "KC": {
        "oc": "Matt Nagy",
        "style": "Reid West Coast",
        "avg_depth_of_target": 8.8,
        "rb_target_share": 0.14,
        "slot_usage": "MEDIUM",
        "te_usage": "HIGH",
        "notes": "Andy Reid offense — TE/RB combo is the backbone. "
                 "Kelce gets 7-9 targets per game historically. "
                 "Rice is the deep threat complement."
    },
}

# ── Scheme adjustment calculator ──────────────────────────────────────────────

def get_scheme_adjustment(
    player_pos: str,
    player_role: str,    # 'slot_wr', 'x_wr', 'te', 'rb', 'qb'
    prop_type: str,
    opponent: str,
    offense_team: str = None
) -> dict:
    """
    Calculate scheme-based probability adjustment.
    Returns adjustment value and explanation.
    
    player_pos:  'WR', 'RB', 'TE', 'QB'
    player_role: specific role within position
    prop_type:   'rec_yds', 'receptions', 'rush_yds', 'pass_yds', etc.
    opponent:    team abbreviation (defense)
    offense_team: team abbreviation (offense) for OC scheme check
    """
    
    defense = DEFENSIVE_SCHEMES.get(opponent, {})
    offense = OFFENSIVE_SCHEMES.get(offense_team, {})
    
    if not defense:
        return {
            "adjustment": 0.0,
            "confidence": "NEUTRAL",
            "reason": f"No scheme data for {opponent}",
            "edge": False,
        }
    
    adj   = 0.0
    notes = []
    edge  = False
    
    zone_rate  = defense.get("zone_rate", 0.5)
    blitz_rate = defense.get("blitz_rate", 0.25)
    shell      = defense.get("shell", "Multiple")
    
    # ── RB receiving props vs zone ─────────────────────────────────────────
    if player_pos == "RB" and prop_type in ("receptions", "rec_yds"):
        rb_allow = defense.get("rb_rec_allow", "MEDIUM")
        
        if rb_allow == "HIGH":
            adj += 0.12
            notes.append(f"{opponent} {shell} → RB dump-offs open")
            edge = True
        elif rb_allow == "LOW":
            adj -= 0.08
            notes.append(f"{opponent} {shell} → man coverage limits RB routes")
        
        # Additional bonus if offense is a short-game system
        if offense:
            rb_share = offense.get("rb_target_share", 0.12)
            if rb_share >= 0.16:
                adj += 0.05
                notes.append(f"{offense_team} targets RBs heavily ({rb_share:.0%} share)")
                edge = True
    
    # ── Slot WR props vs zone ──────────────────────────────────────────────
    elif player_pos == "WR" and player_role == "slot_wr":
        slot_allow = defense.get("slot_allow", "MEDIUM")
        
        if slot_allow == "HIGH":
            adj += 0.10
            notes.append(f"{opponent} {shell} → slot routes find windows")
            edge = True
        elif slot_allow == "LOW":
            adj -= 0.10
            notes.append(f"{opponent} {shell} → press disrupts slot timing")
    
    # ── X/Z WR props vs man ────────────────────────────────────────────────
    elif player_pos == "WR" and player_role == "x_wr":
        man_rate = defense.get("man_rate", 0.5)
        deep_allow = defense.get("deep_allow", "MEDIUM")
        
        if man_rate >= 0.55 and deep_allow == "HIGH":
            adj += 0.08
            notes.append(f"{opponent} heavy man → elite WR1 wins 1-on-1")
            edge = True
        elif zone_rate >= 0.60:
            adj -= 0.05
            notes.append(f"{opponent} zone → WR1 sees bracket coverage")
    
    # ── TE props ───────────────────────────────────────────────────────────
    elif player_pos == "TE":
        te_allow = defense.get("te_allow", "MEDIUM")
        
        if te_allow == "HIGH" and prop_type in ("receptions", "rec_yds"):
            adj += 0.10
            notes.append(f"{opponent} zone → TE crossings open")
            edge = True
        elif te_allow == "LOW":
            adj -= 0.08
            notes.append(f"{opponent} brackets TE — volume suppressed")
    
    # ── QB props ───────────────────────────────────────────────────────────
    elif player_pos == "QB":
        if prop_type == "pass_yds":
            if blitz_rate >= 0.40:
                adj += 0.07
                notes.append(f"{opponent} blitzes {blitz_rate:.0%} → big play opportunities")
                edge = True
            elif zone_rate >= 0.65:
                adj -= 0.05
                notes.append(f"{opponent} coverage zone → limits explosive plays")
        
        elif prop_type == "pass_att":
            if blitz_rate >= 0.40:
                adj -= 0.04
                notes.append(f"{opponent} blitz → faster decisions, fewer attempts")
    
    # ── DC change multiplier ───────────────────────────────────────────────
    dc = defense.get("dc", "")
    if dc and "NEW" in defense.get("notes", ""):
        adj += 0.06
        notes.append(f"NEW DC {dc} — installation period, weeks 1-6 edge")
        edge = True
    
    # Determine confidence level
    if abs(adj) >= 0.10:
        confidence = "HIGH" if adj > 0 else "FADE"
    elif abs(adj) >= 0.05:
        confidence = "MEDIUM" if adj > 0 else "SLIGHT FADE"
    else:
        confidence = "NEUTRAL"
    
    return {
        "adjustment": round(adj, 3),
        "confidence": confidence,
        "opponent_scheme": shell,
        "opponent_dc": defense.get("dc", "Unknown"),
        "zone_rate": zone_rate,
        "blitz_rate": blitz_rate,
        "edge": edge,
        "notes": notes,
        "defense_summary": defense.get("notes", ""),
    }


def analyze_slate(games: list) -> list:
    """
    Analyze a full week's slate for scheme-based edges.
    
    games: list of dicts with:
      {player, pos, role, prop_type, opponent, offense_team, base_prob, line, odds}
    
    Returns sorted list of edges with scheme adjustments applied.
    """
    results = []
    
    for game in games:
        scheme = get_scheme_adjustment(
            player_pos=game.get("pos"),
            player_role=game.get("role", game.get("pos").lower()),
            prop_type=game.get("prop_type"),
            opponent=game.get("opponent"),
            offense_team=game.get("team"),
        )
        
        base_prob      = game.get("base_prob", 0.65)
        adj_prob       = min(0.97, max(0.30, base_prob + scheme["adjustment"]))
        implied_market = 1 / (1 + (abs(game.get("odds", -115)) / 100))
        edge_pct       = adj_prob - implied_market
        
        results.append({
            **game,
            "base_prob":     base_prob,
            "scheme_adj":    scheme["adjustment"],
            "adj_prob":      round(adj_prob, 3),
            "implied":       round(implied_market, 3),
            "edge_pct":      round(edge_pct, 3),
            "scheme_conf":   scheme["confidence"],
            "is_edge":       scheme["edge"] and edge_pct > 0.05,
            "scheme_notes":  scheme["notes"],
            "dc":            scheme["opponent_dc"],
            "scheme":        scheme["opponent_scheme"],
        })
    
    return sorted(results, key=lambda x: x["edge_pct"], reverse=True)


# ── Sample usage / weekly edge finder ────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("SCHEME ENGINE — SAMPLE WEEKLY ANALYSIS")
    print("=" * 65)
    
    # Sample slate — mix of high and low usage players
    sample_plays = [
        # High-usage players
        {"player":"Ja'Marr Chase",    "pos":"WR","role":"x_wr",   "prop_type":"rec_yds",   "team":"CIN","opponent":"MIN","base_prob":0.72,"line":72.5, "odds":-115},
        {"player":"Saquon Barkley",   "pos":"RB","role":"rb",     "prop_type":"receptions","team":"PHI","opponent":"MIN","base_prob":0.78,"line":4.5,  "odds":-115},
        {"player":"Travis Kelce",     "pos":"TE","role":"te",     "prop_type":"rec_yds",   "team":"KC", "opponent":"CLE","base_prob":0.68,"line":54.5, "odds":-115},
        {"player":"Josh Allen",       "pos":"QB","role":"qb",     "prop_type":"pass_yds",  "team":"BUF","opponent":"DAL","base_prob":0.74,"line":268.5,"odds":-115},
        
        # LOWER USAGE — scheme creates edge
        {"player":"Aaron Jones",      "pos":"RB","role":"rb",     "prop_type":"receptions","team":"MIN","opponent":"PHI","base_prob":0.62,"line":3.5,  "odds":-115},
        {"player":"Cole Kmet",        "pos":"TE","role":"te",     "prop_type":"rec_yds",   "team":"CHI","opponent":"PHI","base_prob":0.58,"line":38.5, "odds":-115},
        {"player":"Rhamondre Stevenson","pos":"RB","role":"rb",   "prop_type":"receptions","team":"NE", "opponent":"MIN","base_prob":0.60,"line":2.5,  "odds":-115},
        {"player":"Gabe Davis",       "pos":"WR","role":"x_wr",   "prop_type":"rec_yds",   "team":"JAX","opponent":"CLE","base_prob":0.55,"line":44.5, "odds":-115},
    ]
    
    results = analyze_slate(sample_plays)
    
    print(f"\n{'Player':<22} {'Pos':<4} {'Prop':<12} {'vs':<4} {'Base':>6} {'Adj':>6} {'Adj%':>6} {'Edge':>7} {'Conf':<12} {'Scheme'}")
    print("-" * 110)
    
    for r in results:
        edge_flag = "★ EDGE" if r["is_edge"] else ""
        print(f"{r['player']:<22} {r['pos']:<4} {r['prop_type']:<12} {r['opponent']:<4} "
              f"{r['base_prob']:>5.1%} {r['scheme_adj']:>+5.1%} {r['adj_prob']:>5.1%} "
              f"{r['edge_pct']:>+6.1%} {r['scheme_conf']:<12} {r['scheme']} {edge_flag}")
    
    print(f"\n{'='*65}")
    print("SCHEME EDGE PLAYS THIS WEEK:")
    print(f"{'='*65}")
    for r in results:
        if r["is_edge"]:
            print(f"\n  ★ {r['player']} {r['prop_type'].upper()} {r['line']}")
            print(f"    Base prob: {r['base_prob']:.1%} → Scheme-adjusted: {r['adj_prob']:.1%}")
            print(f"    Edge vs market: {r['edge_pct']:+.1%}")
            for note in r["scheme_notes"]:
                print(f"    → {note}")
    
    print(f"\n{'='*65}")
    print("NOTE ON LOWER-USAGE PLAYERS:")
    print(f"{'='*65}")
    print("""
  Aaron Jones (MIN RBs) vs PHI Cover-2:
    Base: 62% (low usage, small role)
    After scheme: 62% + 17% = 79%
    Line: 3.5 receptions at -115 (53% implied)
    Edge: +26 percentage points
    
    Why: Darnold's quick release system + PHI Fangio Cover-2
    = DOUBLE scheme advantage. Fangio zones leave flat routes
    open AND MIN targets RBs at 18% clip. Aaron Jones
    is NOT in anyone's top-50 tracker but THIS matchup
    makes his 3.5 receptions line near-automatic.
    
  Cole Kmet (CHI TE) vs PHI Cover-2:
    Base: 58% (low usage, bad QB)
    After scheme: 58% + 10% = 68%
    Line: 38.5 rec yards at -115
    Edge: +15 percentage points
    
    Fangio Cover-2 surrenders TE crossings.
    Even with Caleb Williams at QB, the route concept
    exists in the playbook. Kmet OVER is a scheme play
    not a usage play.
    
  THIS IS THE EDGE:
    High-usage players are efficiently priced.
    Low-usage players in GREAT SCHEME MATCHUPS are not.
    The market doesn't separate Kmet in Cover-2 from
    Kmet in Cover-1. We do. That's the edge.
""")
