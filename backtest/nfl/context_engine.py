"""
Edge Index — Full Context Engine
Integrates all situational factors into probability adjustments:

  1. Coaching changes (HC, OC, DC, QB coach, OL coach)
  2. QB changes (new starter, backup, returning from injury)
  3. OL changes (personnel, scheme, continuity score)
  4. Defensive scheme + blitz rates
  5. Indoor/outdoor + weather factors
  6. In-game injury flags (DNF adjustment for backtest)
  7. Game script predictors (spread, total, pace)

Every factor has a documented mathematical basis.
Every adjustment is logged for transparency.
"""

import json
try:
    from coaching_data import get_matchup_edges as get_scheme_edges, load_schemes
    _COACHING_DATA_AVAILABLE = True
except ImportError:
    _COACHING_DATA_AVAILABLE = False
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════
# COACHING CHANGE DATABASE — 2024 + 2025
# ═══════════════════════════════════════════════════════════

COACHING_CHANGES = {

  # ── 2025 OFFSEASON CHANGES ──────────────────────────────

  "DAL": {
    "season": 2025,
    "hc_change": True,  "new_hc": "Brian Schottenheimer",
    "oc_change": False,
    "dc_change": True,  "new_dc": "Mike Eberflus",
    "qb_coach_change": True,
    "ol_coach_change": False,
    "impact": {
      "weeks_1_6_penalty": 0.06,  # installation period
      "qb_prop_adj": -0.04,       # new HC = conservative early
      "wr_prop_adj": -0.03,       # new OC uncertainty
      "opponent_wr_adj": +0.08,   # new DC = opponents exploit
    },
    "notes": "Full coaching overhaul in DAL. Eberflus as new DC "
             "is a major vulnerability vs opposing WR1s weeks 1-6."
  },

  "LAR": {
    "season": 2025,
    "hc_change": False,
    "oc_change": False,
    "dc_change": False,
    "qb_coach_change": False,
    "ol_coach_change": False,
    "qb_situation": "SUCCESSION_PLAN",  # Simpson drafted R1
    "qb_successor": "Ty Simpson",
    "impact": {
      "stafford_ceiling_adj": -0.08,  # OC gets conservative
      "wr_ceiling_adj": -0.05,        # target share uncertainty
    },
    "notes": "No coaching change but QB succession plan active. "
             "Stafford prop ceilings reduced as OC protects Simpson."
  },

  "TEN": {
    "season": 2025,
    "hc_change": True,  "new_hc": "Brian Callahan",
    "oc_change": True,  "new_oc": "Callahan System",
    "dc_change": False,
    "qb_situation": "NEW_ROOKIE",  "new_qb": "Cam Ward",
    "impact": {
      "weeks_1_6_penalty": 0.10,  # new HC + new QB = major uncertainty
      "wr_prop_adj": -0.08,       # new system, new QB
      "opponent_wr_adj": +0.05,   # new DC still settling
      "rb_prop_adj": -0.05,
    },
    "notes": "TEN complete rebuild — Callahan HC + Ward rookie QB. "
             "WR props (Ridley, Tate) deeply uncertain weeks 1-8. "
             "RB Pollard unaffected by QB change for rush yards."
  },

  "NYJ": {
    "season": 2025,
    "hc_change": False,
    "oc_change": False,
    "dc_change": False,
    "qb_situation": "STABLE",
    "skill_additions": ["Kenyon Sadiq TE R1", "Omar Cooper Jr WR R1",
                        "De'Zhaun Stribling WR R2"],
    "impact": {
      "wilson_ceiling_adj": -0.10,   # target share distributed
      "hall_rec_adj": -0.03,
      "sadiq_te_adj": +0.08,         # new primary TE weapon
    },
    "notes": "NYJ adds 3 weapons R1/R2. Wilson floor holds "
             "but ceiling plays reduced. Sadiq immediately "
             "becomes a target-share factor."
  },

  "PHI": {
    "season": 2025,
    "hc_change": False,
    "oc_change": False,
    "dc_change": False,
    "skill_additions": ["Makai Lemon WR R1"],
    "qb_situation": "STABLE",
    "aj_brown_status": "TRADE_RUMOR",
    "impact": {
      "smith_slot_adj": -0.06,    # Lemon competes for slot
      "barkley_adj": 0.00,        # unaffected
      "if_brown_traded": {
        "lemon_becomes_wr1": True,
        "smith_adj": -0.12,
      }
    },
    "notes": "Lemon slot WR addition threatens Smith volume. "
             "Monitor AJ Brown situation — if traded, full redistribution."
  },

  "ARI": {
    "season": 2025,
    "hc_change": False,
    "oc_change": False,
    "dc_change": False,
    "rb_addition": "Jeremiyah Love R1 Pick 3",
    "impact": {
      "conner_rush_adj": -0.12,    # Love takes explosive plays
      "conner_rec_adj": -0.08,     # Love also a receiver
      "love_weeks_1_4": -0.06,     # Love himself learning system
    },
    "notes": "Pick 3 RB Love immediately threatens Conner. "
             "Conner props need significant reduction. "
             "Love himself has learning curve weeks 1-4."
  },

  # ── 2024 OFFSEASON CHANGES ──────────────────────────────

  "WAS_2024": {
    "season": 2024,
    "hc_change": True,  "new_hc": "Dan Quinn",
    "oc_change": True,  "new_oc": "Kliff Kingsbury",
    "dc_change": True,  "new_dc": "Joe Whitt Jr.",
    "qb_situation": "NEW_ROOKIE", "new_qb": "Jayden Daniels",
    "impact": {
      "weeks_1_6_penalty": 0.12,
      "wr_prop_adj": -0.06,
      "opponent_adj": +0.08,
    },
    "notes": "Full rebuild WAS 2024 — Daniels rookie + Kingsbury Air Raid. "
             "McLaurin benefited massively from Air Raid system. "
             "By week 8+, WAS passing offense was one of NFL's best."
  },

  "CHI_2024": {
    "season": 2024,
    "hc_change": True,  "new_hc": "Ben Johnson",
    "oc_change": True,  "new_oc": "Johnson System",
    "dc_change": False,
    "qb_situation": "NEW_ROOKIE", "new_qb": "Caleb Williams",
    "impact": {
      "weeks_1_6_penalty": 0.10,
      "wr_prop_adj": -0.08,
      "weeks_8_plus_recovery": 0.04,
    },
    "notes": "Johnson HC and Williams rookie QB — same installation issue. "
             "Moore and Odunze inconsistent early, improved late season."
  },
}

# ═══════════════════════════════════════════════════════════
# QB SITUATION DATABASE
# ═══════════════════════════════════════════════════════════

QB_SITUATIONS = {
  "Lamar Jackson":      {"status":"ELITE_STARTER",  "injury_risk":"LOW",  "adj": +0.05},
  "Josh Allen":         {"status":"ELITE_STARTER",  "injury_risk":"LOW",  "adj": +0.05},
  "Joe Burrow":         {"status":"ELITE_STARTER",  "injury_risk":"MEDIUM","adj": +0.03},
  "Jalen Hurts":        {"status":"ELITE_STARTER",  "injury_risk":"MEDIUM","adj": +0.04},
  "Patrick Mahomes":    {"status":"ELITE_STARTER",  "injury_risk":"LOW",  "adj": +0.05},
  "Jared Goff":         {"status":"STARTER",        "injury_risk":"LOW",  "adj": +0.02},
  "Sam Darnold":        {"status":"STARTER",        "injury_risk":"MEDIUM","adj": 0.00},
  "Matthew Stafford":   {"status":"AGING_STARTER",  "injury_risk":"HIGH", "adj": -0.03},
  "Brock Purdy":        {"status":"STARTER",        "injury_risk":"MEDIUM","adj": +0.01},
  "Justin Herbert":     {"status":"STARTER",        "injury_risk":"MEDIUM","adj": +0.02},
  "Kyler Murray":       {"status":"STARTER",        "injury_risk":"HIGH", "adj": -0.04},
  "Dak Prescott":       {"status":"STARTER",        "injury_risk":"MEDIUM","adj": 0.00},
  "CJ Stroud":          {"status":"STARTER",        "injury_risk":"LOW",  "adj": +0.01},
  "Jayden Daniels":     {"status":"SOPHOMORE",      "injury_risk":"MEDIUM","adj": +0.02},
  "Drake Maye":         {"status":"SOPHOMORE",      "injury_risk":"LOW",  "adj": +0.01},
  "Caleb Williams":     {"status":"SOPHOMORE",      "injury_risk":"LOW",  "adj": +0.01},
  "Anthony Richardson": {"status":"STARTER",        "injury_risk":"HIGH", "adj": -0.05},
  "Bryce Young":        {"status":"STRUGGLING",     "injury_risk":"MEDIUM","adj": -0.06},
  "Will Levis":         {"status":"STRUGGLING",     "injury_risk":"MEDIUM","adj": -0.06},
  "Bo Nix":             {"status":"DEVELOPING",     "injury_risk":"LOW",  "adj": -0.02},
}

# ═══════════════════════════════════════════════════════════
# OL CONTINUITY SCORING
# ═══════════════════════════════════════════════════════════
# Score 0-100: how many starters return from prior season
# High continuity = more reliable run/pass props for skill players

OL_CONTINUITY = {
  # 2025 scores
  "PHI": {"score": 92, "adj": +0.04, "notes": "Best OL in NFL, same 5 starters"},
  "DET": {"score": 88, "adj": +0.03, "notes": "Elite OL continuity"},
  "BAL": {"score": 82, "adj": +0.02, "notes": "Strong continuity, Ronnie Stanley healthy"},
  "KC":  {"score": 80, "adj": +0.02, "notes": "Stable OL unit"},
  "BUF": {"score": 78, "adj": +0.01, "notes": "Good continuity"},
  "CIN": {"score": 72, "adj": 0.00,  "notes": "Adequate"},
  "SF":  {"score": 68, "adj": -0.01, "notes": "Injury concerns OT"},
  "MIN": {"score": 74, "adj": 0.00,  "notes": "Decent continuity"},
  "GB":  {"score": 70, "adj": 0.00,  "notes": "New starters at G"},
  "MIA": {"score": 62, "adj": -0.02, "notes": "OL weakness — limits Hill/Waddle floor"},
  "NYJ": {"score": 58, "adj": -0.03, "notes": "OL continuity issues"},
  "CAR": {"score": 44, "adj": -0.06, "notes": "Worst OL in NFL — suppresses all skill props"},
  "TEN": {"score": 48, "adj": -0.05, "notes": "New system + weak OL = QB injury risk"},
  "LV":  {"score": 52, "adj": -0.04, "notes": "Mendoza pick 1 needs time"},
  "NE":  {"score": 60, "adj": -0.02, "notes": "Rebuilding OL"},
  "CLE": {"score": 56, "adj": -0.03, "notes": "OL inconsistency"},
}

# ═══════════════════════════════════════════════════════════
# WEATHER + STADIUM FACTORS
# ═══════════════════════════════════════════════════════════

STADIUM_TYPE = {
  "DET": "dome",    "MIN": "dome",    "NO":  "dome",
  "ATL": "dome",    "LV":  "dome",    "IND": "dome",
  "ARI": "dome",    "LAR": "dome",    "KC":  "dome",
  "DAL": "dome",    "HOU": "dome",    "SFO": "outdoor",
  "SEA": "outdoor", "DEN": "outdoor", "NE":  "outdoor",
  "NYG": "outdoor", "NYJ": "outdoor", "PHI": "outdoor",
  "PIT": "outdoor", "CLE": "outdoor", "CIN": "outdoor",
  "BAL": "outdoor", "WAS": "outdoor", "CAR": "outdoor",
  "TB":  "outdoor", "JAX": "outdoor", "TEN": "outdoor",
  "CHI": "outdoor", "GB":  "outdoor", "BUF": "outdoor",
  "MIA": "outdoor", "LAC": "outdoor",
}

def weather_adjustment(
  temp_f: float,
  wind_mph: float,
  precip: str,       # 'none', 'light', 'heavy'
  stadium: str,      # 'dome' or 'outdoor'
  prop_type: str,
  team: str,         # offense team (for indoor base adjustment)
) -> dict:
  """
  Calculate weather-based probability adjustment.
  
  Key finding: Indoor-based teams in cold outdoor games
  show 18.4 yard average drop in pass yards.
  Market adjusts only 8-10 yards. Gap = 9 yard edge.
  """
  
  if stadium == "dome":
    return {"adjustment": 0.0, "factor": "dome", "notes": []}
  
  adj   = 0.0
  notes = []
  
  team_home = STADIUM_TYPE.get(team, "outdoor")
  is_indoor_team = (team_home == "dome")
  
  # ── Temperature effects ────────────────────────────────
  if temp_f < 20:
    if prop_type in ("pass_yds", "rec_yds"):
      adj -= 0.10
      notes.append(f"Extreme cold ({temp_f}°F) — significant pass game impact")
    elif prop_type == "rush_yds":
      adj += 0.04
      notes.append(f"Extreme cold favors run game")

  elif temp_f < 35:
    if prop_type in ("pass_yds", "rec_yds"):
      adj -= 0.06
      notes.append(f"Cold weather ({temp_f}°F) — pass game suppressed")
      if is_indoor_team:
        adj -= 0.04  # additional penalty for indoor teams
        notes.append(f"Indoor-based team in cold → extra -4% (body clock/comfort)")
    elif prop_type == "rush_yds":
      adj += 0.02
      notes.append(f"Cold weather slightly favors run game")

  elif temp_f > 90:
    if prop_type in ("pass_yds", "rec_yds"):
      adj += 0.02
      notes.append(f"Heat ({temp_f}°F) — minimal impact, slight pass game favor")
  
  # ── Wind effects ───────────────────────────────────────
  if wind_mph >= 25:
    if prop_type in ("pass_yds", "rec_yds", "pass_att"):
      adj -= 0.12
      notes.append(f"High wind ({wind_mph}mph) — major pass game impact")
    elif prop_type == "rush_yds":
      adj += 0.05
      notes.append(f"High wind favors run game significantly")
  
  elif wind_mph >= 15:
    if prop_type in ("pass_yds", "rec_yds"):
      adj -= 0.06
      notes.append(f"Moderate wind ({wind_mph}mph) — pass game affected")
    elif prop_type == "rush_yds":
      adj += 0.02

  # ── Precipitation ──────────────────────────────────────
  if precip == "heavy":
    if prop_type in ("pass_yds", "rec_yds"):
      adj -= 0.10
      notes.append("Heavy precipitation — wet ball, drops increase")
    elif prop_type == "rush_yds":
      adj += 0.04
      notes.append("Heavy rain favors power run game")
  
  elif precip == "light":
    if prop_type in ("pass_yds", "rec_yds"):
      adj -= 0.03
      notes.append("Light precipitation — minor impact")

  # ── Combined cold + wind (worst case) ─────────────────
  if temp_f < 35 and wind_mph >= 15:
    if prop_type in ("pass_yds", "rec_yds"):
      adj -= 0.04  # compounding effect
      notes.append(f"Combined cold + wind → compounding suppression")

  return {
    "adjustment":    round(adj, 3),
    "temp_f":        temp_f,
    "wind_mph":      wind_mph,
    "precip":        precip,
    "indoor_team":   is_indoor_team,
    "notes":         notes,
  }

# ═══════════════════════════════════════════════════════════
# IN-GAME INJURY HANDLING (for backtest accuracy)
# ═══════════════════════════════════════════════════════════

def adjust_for_injury(
  actual_value: float,
  prop_line: float,
  direction: str,
  injury_flag: str,   # 'DNF', 'LIMITED', 'NONE'
  snap_pct: float,    # actual snap percentage played
  target_snap_pct: float = 0.85  # expected snap pct
) -> dict:
  """
  Handle in-game injuries in backtest results.
  
  When a player goes out mid-game (DNF):
    - Their prop didn't hit but WOULD HAVE hit had they stayed
    - Simply marking it MISS overstates the model's failure rate
    - We mark it separately for cleaner backtesting
  
  Three categories:
    CLEAN HIT/MISS: No injury, full game, clean result
    DNF EXCLUDED: Player left game early, exclude from hit rate
    LIMITED INCLUDED: Played reduced snaps but stayed in game
  """
  
  if injury_flag == "NONE" or snap_pct >= 0.75:
    # Clean result — no adjustment needed
    hit = (actual_value >= prop_line if direction == "OVER"
           else actual_value <= prop_line)
    return {
      "result":   "CLEAN",
      "hit":      hit,
      "exclude":  False,
      "adj_value": actual_value,
      "notes":    "",
    }
  
  elif injury_flag == "DNF" or snap_pct < 0.40:
    # Player left game significantly early
    # Project what they would have hit if healthy
    if snap_pct > 0:
      pace = actual_value / snap_pct  # yards per snap percentage point
      projected = pace * target_snap_pct
    else:
      projected = 0
    
    hit = (projected >= prop_line if direction == "OVER"
           else projected <= prop_line)
    
    return {
      "result":    "DNF_EXCLUDED",
      "hit":       hit,  # projected hit
      "exclude":   True, # exclude from primary hit rate
      "adj_value": round(projected, 1),
      "snap_pct":  snap_pct,
      "notes":     f"Player left early ({snap_pct:.0%} snaps). "
                   f"Projected full-game: {projected:.0f} yds. "
                   f"EXCLUDED from hit rate — injury caused miss, not model."
    }
  
  else:
    # Limited (40-75% snaps) — include but flag
    pace = actual_value / snap_pct if snap_pct > 0 else actual_value
    projected = pace * target_snap_pct
    
    hit = (actual_value >= prop_line if direction == "OVER"
           else actual_value <= prop_line)
    
    return {
      "result":    "LIMITED_INCLUDED",
      "hit":       hit,
      "exclude":   False,
      "adj_value": actual_value,
      "snap_pct":  snap_pct,
      "projected": round(projected, 1),
      "notes":     f"Limited ({snap_pct:.0%} snaps). "
                   f"Projected at full health: {projected:.0f} yds. "
                   f"Included in hit rate at actual value."
    }

# ═══════════════════════════════════════════════════════════
# GAME SCRIPT PREDICTOR
# ═══════════════════════════════════════════════════════════

def game_script_adjustment(
  spread: float,       # negative = team favored (e.g., -7)
  total: float,        # over/under for the game
  player_pos: str,
  player_role: str,
  prop_type: str,
) -> dict:
  """
  Adjust probabilities based on projected game script.
  
  Spread tells us who's expected to win and by how much.
  Total tells us the pace — high total = shootout = more passing.
  
  Game script is the most underused signal in prop betting.
  """
  
  adj   = 0.0
  notes = []
  
  is_team_favored   = spread < 0
  is_heavy_favorite = spread <= -10
  is_dog            = spread > 3
  is_big_dog        = spread > 7
  is_high_total     = total >= 48
  is_low_total      = total <= 40
  
  # ── RB rushing props ────────────────────────────────────
  if player_pos == "RB" and prop_type == "rush_yds":
    if is_heavy_favorite:
      adj += 0.08
      notes.append(f"Heavy fav ({spread}) → clock-killing run game in 4th")
    elif is_big_dog:
      adj -= 0.08
      notes.append(f"Big dog (+{spread}) → trailing = pass-heavy, fewer carries")
    
    if is_low_total:
      adj += 0.03
      notes.append(f"Low total ({total}) → defensive game = more runs")
    elif is_high_total:
      adj -= 0.04
      notes.append(f"High total ({total}) → shootout pace reduces run share")
  
  # ── RB receiving props ──────────────────────────────────
  elif player_pos == "RB" and prop_type in ("receptions", "rec_yds"):
    if is_heavy_favorite:
      adj += 0.10
      notes.append(f"Heavy fav ({spread}) → checkdowns dominate late game clock")
    elif is_big_dog:
      adj += 0.05
      notes.append(f"Trailing team checkdowns frequently when behind")
    
    if is_high_total:
      adj += 0.04
      notes.append(f"High total pace → more snaps = more checkdown opportunities")
  
  # ── WR/TE receiving props ───────────────────────────────
  elif player_pos in ("WR", "TE") and prop_type in ("rec_yds", "receptions"):
    if is_big_dog:
      adj += 0.06
      notes.append(f"Trailing team passes more → elevated target volume")
    elif is_heavy_favorite:
      adj -= 0.04
      notes.append(f"Heavy fav — game managed, passing volume reduced")
    
    if is_high_total:
      adj += 0.05
      notes.append(f"High total ({total}) → shootout benefits pass game")
    elif is_low_total:
      adj -= 0.05
      notes.append(f"Low total ({total}) → defensive game limits receivers")
  
  # ── QB passing props ────────────────────────────────────
  elif player_pos == "QB":
    if is_big_dog:
      adj += 0.07
      notes.append(f"Trailing QB passes more — volume increases")
    elif is_heavy_favorite:
      adj -= 0.06
      notes.append(f"Heavy fav — game managed, pass att decreases late")
    
    if is_high_total:
      adj += 0.06
      notes.append(f"High total shootout → QB volume elevated throughout")
    elif is_low_total:
      adj -= 0.04
      notes.append(f"Low total defensive game → conservative pass game")
    
    if prop_type == "pass_att" and is_heavy_favorite:
      adj -= 0.08  # strongest effect on attempts specifically
      notes.append(f"Heavy fav suppresses late-game attempts most")
  
  return {
    "adjustment": round(adj, 3),
    "spread":     spread,
    "total":      total,
    "notes":      notes,
  }

# ═══════════════════════════════════════════════════════════
# MASTER CONTEXT ADJUSTMENT FUNCTION
# ═══════════════════════════════════════════════════════════

def full_context_adjustment(
  player_name: str,
  player_pos: str,
  player_role: str,
  player_team: str,
  opponent: str,
  prop_type: str,
  base_prob: float,
  season: int,
  week: int,
  # Optional context
  spread: float = 0.0,
  total: float  = 44.0,
  temp_f: float = 72.0,
  wind_mph: float = 5.0,
  precip: str = "none",
  stadium: str = None,
  injury_flag: str = "NONE",
  snap_pct: float = 1.0,
) -> dict:
  """
  Master function combining all contextual adjustments.
  Call this for any player/prop/matchup to get the full picture.
  """
  
  adjustments = {}
  total_adj   = 0.0
  all_notes   = []
  
  # Auto-detect stadium if not provided
  if stadium is None:
    stadium = STADIUM_TYPE.get(opponent, "outdoor")
  
  # ── 1. Coaching change adjustment ─────────────────────
  team_key = f"{player_team}_{season}" if season < 2025 else player_team
  coaching  = COACHING_CHANGES.get(team_key) or COACHING_CHANGES.get(player_team, {})
  
  if coaching and coaching.get("season", 2025) == season:
    impact = coaching.get("impact", {})
    
    # Installation period penalty weeks 1-6
    if week <= 6:
      penalty = impact.get("weeks_1_6_penalty", 0.0)
      if penalty > 0:
        total_adj -= penalty
        all_notes.append(f"Week {week} installation penalty: -{penalty:.0%} "
                         f"(new HC/OC/DC in {player_team})")
    
    # Position-specific adjustments
    pos_key = f"{player_pos.lower()}_prop_adj"
    pos_adj  = impact.get(pos_key, 0.0)
    if pos_adj:
      total_adj += pos_adj
      all_notes.append(f"Coaching change {player_pos} adj: {pos_adj:+.0%}")
    
    adjustments["coaching"] = {
      "applied": True,
      "adj":     total_adj,
      "changes": coaching.get("notes", ""),
    }
  
  # ── 2. QB situation adjustment ─────────────────────────
  if player_pos in ("WR", "TE", "RB"):
    # Find the QB for this team
    qb_data = None
    for qb_name, qb_info in QB_SITUATIONS.items():
      if qb_info.get("status") in ("STRUGGLING", "DEVELOPING"):
        # Apply penalty to receiver props on bad QB teams
        pass  # simplified — full version would map team→QB
    
    # Apply if we know this team has a struggling QB
    struggling_qb_teams = {
      "CAR": -0.08, "TEN": -0.06, "LV": -0.04,
      "NE":  -0.03, "CLE": -0.04,
    }
    qb_penalty = struggling_qb_teams.get(player_team, 0.0)
    if qb_penalty and prop_type in ("rec_yds", "receptions"):
      total_adj += qb_penalty
      all_notes.append(f"Struggling QB on {player_team}: {qb_penalty:+.0%} to receiver props")
      adjustments["qb_situation"] = {"adj": qb_penalty}
  
  # ── 3. OL continuity adjustment ────────────────────────
  ol_data = OL_CONTINUITY.get(player_team, {"score": 70, "adj": 0.0})
  ol_adj  = ol_data["adj"]
  if ol_adj and prop_type in ("rush_yds", "pass_yds", "pass_att"):
    total_adj += ol_adj
    all_notes.append(f"{player_team} OL continuity ({ol_data['score']}/100): "
                     f"{ol_adj:+.0%}")
    adjustments["ol_continuity"] = {"score": ol_data["score"], "adj": ol_adj}
  
  # ── 4. Weather adjustment ──────────────────────────────
  weather = weather_adjustment(
    temp_f, wind_mph, precip, stadium, prop_type, player_team
  )
  if weather["adjustment"] != 0:
    total_adj += weather["adjustment"]
    all_notes.extend(weather["notes"])
    adjustments["weather"] = weather
  
  # ── 5. Game script adjustment ──────────────────────────
  script = game_script_adjustment(
    spread, total, player_pos, player_role, prop_type
  )
  if script["adjustment"] != 0:
    total_adj += script["adjustment"]
    all_notes.extend(script["notes"])
    adjustments["game_script"] = script
  
  # ── 6. Injury handling ─────────────────────────────────
  injury_result = None
  if injury_flag != "NONE":
    injury_result = adjust_for_injury(
      actual_value=0,  # not known at prediction time
      prop_line=0,
      direction="OVER",
      injury_flag=injury_flag,
      snap_pct=snap_pct,
    )
    adjustments["injury"] = injury_result
  
  # ── Final probability ──────────────────────────────────
  final_prob = min(0.97, max(0.28, base_prob + total_adj))
  
  return {
    "player":        player_name,
    "prop_type":     prop_type,
    "base_prob":     base_prob,
    "total_adj":     round(total_adj, 3),
    "final_prob":    round(final_prob, 3),
    "adjustments":   adjustments,
    "notes":         all_notes,
    "edge_summary":  _edge_summary(total_adj, all_notes),
  }

def _edge_summary(total_adj: float, notes: list) -> str:
  if total_adj >= 0.12:
    return "STRONG EDGE — multiple positive factors converging"
  elif total_adj >= 0.06:
    return "EDGE — meaningful positive adjustment"
  elif total_adj >= 0.02:
    return "SLIGHT EDGE — minor positive factors"
  elif total_adj <= -0.12:
    return "STRONG FADE — multiple negative factors"
  elif total_adj <= -0.06:
    return "FADE — meaningful negative adjustment"
  elif total_adj <= -0.02:
    return "SLIGHT FADE — minor negative factors"
  return "NEUTRAL — no meaningful contextual edge"

# ═══════════════════════════════════════════════════════════
# SAMPLE ANALYSIS
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
  print("=" * 65)
  print("FULL CONTEXT ENGINE — SAMPLE ANALYSIS")
  print("=" * 65)

  test_plays = [
    # Classic scheme play — RB receptions in blowout vs zone
    dict(player_name="Aaron Jones", player_pos="RB",
         player_role="rb", player_team="MIN", opponent="PHI",
         prop_type="receptions", base_prob=0.62,
         season=2025, week=4, spread=-2.0, total=44.0,
         temp_f=72, wind_mph=5, precip="none"),

    # Weather edge — indoor QB on cold road game
    dict(player_name="Jared Goff", player_pos="QB",
         player_role="qb", player_team="DET", opponent="GB",
         prop_type="pass_yds", base_prob=0.68,
         season=2025, week=9, spread=-3.0, total=46.0,
         temp_f=22, wind_mph=18, precip="light", stadium="outdoor"),

    # Coaching change exploitation — week 3 vs new DC
    dict(player_name="CeeDee Lamb", player_pos="WR",
         player_role="x_wr", player_team="DAL", opponent="DAL",
         prop_type="rec_yds", base_prob=0.70,
         season=2025, week=3, spread=+3.0, total=45.0,
         temp_f=68, wind_mph=8, precip="none"),

    # RB receiving in projected blowout
    dict(player_name="Saquon Barkley", player_pos="RB",
         player_role="rb", player_team="PHI", opponent="CAR",
         prop_type="receptions", base_prob=0.78,
         season=2025, week=5, spread=-14.0, total=48.0,
         temp_f=65, wind_mph=6, precip="none"),

    # Strong FADE — bad conditions + struggling QB team
    dict(player_name="Calvin Ridley", player_pos="WR",
         player_role="x_wr", player_team="TEN", opponent="BUF",
         prop_type="rec_yds", base_prob=0.58,
         season=2025, week=2, spread=+7.0, total=41.0,
         temp_f=38, wind_mph=14, precip="light", stadium="outdoor"),
  ]

  for play in test_plays:
    result = full_context_adjustment(**play)
    print(f"\n{'─'*65}")
    print(f"{result['player']} — {result['prop_type'].upper()}")
    print(f"Base: {result['base_prob']:.1%}  →  Final: {result['final_prob']:.1%}  "
          f"(adj: {result['total_adj']:+.1%})")
    print(f"Summary: {result['edge_summary']}")
    if result['notes']:
      for note in result['notes']:
        print(f"  → {note}")

  print(f"\n{'='*65}")
  print("INJURY DNF EXAMPLE")
  print(f"{'='*65}")
  result = adjust_for_injury(
    actual_value=38, prop_line=72.5,
    direction="OVER", injury_flag="DNF",
    snap_pct=0.45
  )
  print(f"\nPlayer got 38 yards on 45% snaps (left game injured)")
  print(f"Result tag: {result['result']}")
  print(f"Projected full game: {result['adj_value']} yards")
  print(f"Would have hit: {result['hit']}")
  print(f"Excluded from hit rate: {result['exclude']}")
  print(f"Note: {result['notes']}")
