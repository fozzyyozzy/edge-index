// NFL team identity — the ONLY place team colors live. No logos (trademarked; site is betting-adjacent).
// Official primary color, except where the primary is too dark to read as a thin accent on the #060911
// background — those use the team's secondary (noted inline) or a lightened primary (BAL, NYJ, PHI, WAS).
// Keys are nflverse codes; "LA" is the Rams in nflverse, "LAR" kept as an alias for other feeds.
export const TEAM_COLORS = {
  ARI: "#97233F", ATL: "#A71930", BAL: "#6B4FBB", BUF: "#00338D",
  CAR: "#0085CA", CHI: "#C83803", /* navy primary */ CIN: "#FB4F14", CLE: "#FF3C00",
  DAL: "#003594", DEN: "#FB4F14", DET: "#0076B6", GB:  "#FFB612", /* dark green primary */
  HOU: "#A71930", /* deep steel primary */ IND: "#A2AAAD", /* dark blue primary */
  JAX: "#006778", KC:  "#E31837",
  LA:  "#FFA300", /* navy primary */ LAR: "#FFA300", LAC: "#0080C6", LV:  "#A5ACAF", /* black primary */
  MIA: "#008E97", MIN: "#4F2683", NE:  "#C60C30", /* navy primary */ NO:  "#D3BC8D",
  NYG: "#A71930", /* dark blue primary */ NYJ: "#18794E", PHI: "#1B7F88", PIT: "#FFB612",
  SEA: "#69BE28", /* navy primary */ SF:  "#AA0000", TB:  "#D50A0A", TEN: "#4B92DB",
  WAS: "#A13B3B",
};

export const teamColor = code => TEAM_COLORS[code] || "#333";

// Mirrors automation/pipeline/common.py norm_name so book names and nflverse names meet ("Deebo Samuel Sr." = "Deebo Samuel").
const NAME_ALIAS = { "cameron ward": "cam ward", "d.j. moore": "dj moore" };
export const normName = s => {
  const n = String(s || "").trim().replace(/\s+(jr\.?|sr\.?|ii|iii|iv)$/i, "").toLowerCase();
  return NAME_ALIAS[n] || n;
};
