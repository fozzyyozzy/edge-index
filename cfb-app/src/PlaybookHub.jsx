import { useState } from "react";

// ── SAMPLE DATA (replace with weekly_plays_w{N}_{year}.json import) ──
const SAMPLE_PLAYS = [
  {
    player:"Travis Kelce", pos:"TE", team:"KC", opp:"BAL",
    prop:"receptions", posted_line:4.5, tier:"AUTO", model_prob:0.95,
    streak:10, l6:1.0, l10:1.0, wma:6.2, sma_4:6.0, line_vs_wma:1.7,
    sigma_gap:1.7, spread:3.0, total:47.0, is_dome:true,
    wind:0, temp:65, precip:false, game_window:"TNF",
    adj_streak:0.12, adj_line:0.10, adj_gs:0.0, adj_matchup:0.0,
    adj_weather:0.0, adj_rest:-0.03, adj_travel:-0.04, total_adj:0.15,
    gs_notes:[], mu_notes:[], wx_notes:["🏟️ Indoor — weather neutral"],
    rest_notes:["TNF short week — offensive rhythm disrupted"],
    alt_lines:[3.5],
  },
  {
    player:"Derrick Henry", pos:"RB", team:"BAL", opp:"KC",
    prop:"rush_yds", posted_line:88.5, tier:"AUTO", model_prob:0.89,
    streak:10, l6:1.0, l10:1.0, wma:132.5, sma_4:135.0, line_vs_wma:44.0,
    sigma_gap:3.3, spread:-3.0, total:47.0, is_dome:true,
    wind:0, temp:65, precip:false, game_window:"TNF",
    adj_streak:0.12, adj_line:0.10, adj_gs:0.0, adj_matchup:-0.06,
    adj_weather:0.0, adj_rest:-0.03, adj_travel:-0.04, total_adj:0.09,
    gs_notes:[], mu_notes:["KC strong run D (DVOA -12%) — tough matchup"],
    wx_notes:["🏟️ Indoor — weather neutral"],
    rest_notes:["TNF short week — offensive rhythm disrupted"],
    alt_lines:[67.5,70.5,74.5,78.5,82.5,85.5],
  },
  {
    player:"Patrick Mahomes", pos:"QB", team:"KC", opp:"BAL",
    prop:"pass_yds", posted_line:236.5, tier:"AUTO", model_prob:0.95,
    streak:10, l6:1.0, l10:1.0, wma:278.7, sma_4:277.0, line_vs_wma:42.2,
    sigma_gap:3.7, spread:3.0, total:47.0, is_dome:true,
    wind:0, temp:65, precip:false, game_window:"TNF",
    adj_streak:0.12, adj_line:0.10, adj_gs:0.0, adj_matchup:0.0,
    adj_weather:0.0, adj_rest:-0.03, adj_travel:-0.04, total_adj:0.15,
    gs_notes:[], mu_notes:[],
    wx_notes:["🏟️ Indoor — weather neutral"],
    rest_notes:["TNF short week — offensive rhythm disrupted"],
    alt_lines:[231.5,234.5,235.5],
  },
  {
    player:"Jalen Hurts", pos:"QB", team:"PHI", opp:"DAL",
    prop:"rush_yds", posted_line:48.5, tier:"AUTO", model_prob:0.96,
    streak:10, l6:1.0, l10:1.0, wma:78.0, sma_4:77.5, line_vs_wma:29.5,
    sigma_gap:3.6, spread:-7.0, total:46.5, is_dome:true,
    wind:0, temp:65, precip:false, game_window:"SUN_EARLY",
    adj_streak:0.12, adj_line:0.10, adj_gs:0.02, adj_matchup:0.0,
    adj_weather:0.0, adj_rest:0.0, adj_travel:0.0, total_adj:0.24,
    gs_notes:[], mu_notes:[],
    wx_notes:["🏟️ Indoor — weather neutral"], rest_notes:[],
    alt_lines:[29.5,33.5,36.5,39.5,43.5],
  },
  {
    player:"Ja'Marr Chase", pos:"WR", team:"CIN", opp:"PIT",
    prop:"rec_yds", posted_line:88.5, tier:"T1", model_prob:0.78,
    streak:3, l6:0.83, l10:0.80, wma:119.8, sma_4:118.0, line_vs_wma:31.3,
    sigma_gap:1.2, spread:-2.0, total:48.5, is_dome:false,
    wind:6, temp:48, precip:true, game_window:"SUN_EARLY",
    adj_streak:0.02, adj_line:0.06, adj_gs:0.05, adj_matchup:0.05,
    adj_weather:-0.06, adj_rest:0.0, adj_travel:0.0, total_adj:0.12,
    gs_notes:["High total (48.5) → shootout pace boosts targets"],
    mu_notes:["PIT zone-heavy (60%) — slot WRs/TEs thrive vs zone"],
    wx_notes:["Rain/snow — wet ball reduces passing volume and accuracy"],
    rest_notes:[],
    alt_lines:[64.5,72.5,79.5,83.5,86.5],
  },
  {
    player:"Saquon Barkley", pos:"RB", team:"PHI", opp:"DAL",
    prop:"rush_yds", posted_line:88.5, tier:"T1", model_prob:0.74,
    streak:3, l6:0.83, l10:0.80, wma:110.2, sma_4:108.0, line_vs_wma:21.7,
    sigma_gap:1.4, spread:-7.0, total:46.5, is_dome:true,
    wind:0, temp:65, precip:false, game_window:"SUN_EARLY",
    adj_streak:0.02, adj_line:0.06, adj_gs:0.07, adj_matchup:0.0,
    adj_weather:0.0, adj_rest:0.0, adj_travel:0.0, total_adj:0.08,
    gs_notes:["Big favorite (-7) → heavy run game late"],
    mu_notes:[],
    wx_notes:["🏟️ Indoor — weather neutral"], rest_notes:[],
    alt_lines:[69.5,74.5,79.5,83.5,86.5],
  },
  {
    player:"Josh Allen", pos:"QB", team:"BUF", opp:"MIA",
    prop:"pass_yds", posted_line:298.5, tier:"T1", model_prob:0.71,
    streak:4, l6:0.83, l10:0.80, wma:319.2, sma_4:323.0, line_vs_wma:20.7,
    sigma_gap:1.1, spread:-4.0, total:50.5, is_dome:true,
    wind:14, temp:42, precip:false, game_window:"SUN_AFT",
    adj_streak:0.02, adj_line:0.06, adj_gs:0.06, adj_matchup:0.0,
    adj_weather:0.0, adj_rest:-0.06, adj_travel:0.0, total_adj:0.08,
    gs_notes:["Shootout total (50.5) → pass volume premium"],
    mu_notes:["MIA weak pass D (DVOA +12%) — favorable matchup"],
    wx_notes:["🏟️ Indoor — weather neutral"],
    rest_notes:["Opponent off bye — significant rest disadvantage"],
    alt_lines:[194.5,219.5,229.5,235.5],
  },
  {
    player:"CeeDee Lamb", pos:"WR", team:"DAL", opp:"PHI",
    prop:"rec_yds", posted_line:88.5, tier:"T2", model_prob:0.65,
    streak:3, l6:0.83, l10:0.70, wma:111.2, sma_4:108.5, line_vs_wma:22.7,
    sigma_gap:1.1, spread:7.0, total:46.5, is_dome:true,
    wind:0, temp:65, precip:false, game_window:"SNF",
    adj_streak:0.02, adj_line:0.06, adj_gs:0.07, adj_matchup:-0.06,
    adj_weather:0.0, adj_rest:0.0, adj_travel:0.0, total_adj:0.02,
    gs_notes:["Dog (+7) → trailing = pass heavy"],
    mu_notes:["PHI strong pass D (DVOA -15%) — tough matchup"],
    wx_notes:["🏟️ Indoor — weather neutral"], rest_notes:[],
    alt_lines:[71.5,76.5,79.5,82.5,86.5],
  },
];

const PARLAYS = [
  {
    legs:[
      {player:"Travis Kelce",  prop:"RECEPTIONS OVER 4.5",  odds:-180, prob:0.95},
      {player:"Jalen Hurts",   prop:"RUSH YDS OVER 48.5",   odds:-145, prob:0.96},
      {player:"Derrick Henry", prop:"RUSH YDS OVER 88.5",   odds:-150, prob:0.89},
    ],
    parlay_odds:"+298", hit_prob:0.813, ev:2.63, type:"3-leg",
  },
  {
    legs:[
      {player:"Patrick Mahomes", prop:"PASS YDS OVER 236.5", odds:-130, prob:0.95},
      {player:"Saquon Barkley",  prop:"RUSH YDS OVER 88.5",  odds:-140, prob:0.74},
    ],
    parlay_odds:"+198", hit_prob:0.703, ev:1.19, type:"2-leg",
  },
  {
    legs:[
      {player:"Jalen Hurts",   prop:"RUSH YDS OVER 48.5",  odds:-145, prob:0.96},
      {player:"Ja'Marr Chase", prop:"REC YDS OVER 88.5",   odds:-120, prob:0.78},
      {player:"Josh Allen",    prop:"PASS YDS OVER 298.5",  odds:-130, prob:0.71},
    ],
    parlay_odds:"+312", hit_prob:0.533, ev:1.22, type:"3-leg",
  },
];

// ── HELPERS ──────────────────────────────────────────────────
const PROP_LABEL = {
  rec_yds:"Rec Yds", receptions:"Receptions", rush_yds:"Rush Yds",
  pass_yds:"Pass Yds", pass_att:"Pass Att", targets:"Targets",
};

const WINDOW_LABEL = {
  TNF:"Thursday Night", SUN_EARLY:"Sunday Early",
  SUN_AFT:"Sunday Afternoon", SNF:"Sunday Night", MNF:"Monday Night",
};

const TIER_CONFIG = {
  AUTO: { label:"AUTO", color:"#00ff88", bg:"#00ff8818", border:"#00ff8840", icon:"⚡" },
  T1:   { label:"TIER 1", color:"#f5c518", bg:"#f5c51818", border:"#f5c51840", icon:"★" },
  T2:   { label:"TIER 2", color:"#00e5ff", bg:"#00e5ff18", border:"#00e5ff40", icon:"◆" },
};

const POS_COLOR = { QB:"#a855f7", RB:"#00c896", WR:"#00e5ff", TE:"#f5c518" };

function adjBar(value, max=0.15) {
  const pct = Math.min(Math.abs(value) / max * 100, 100);
  const color = value >= 0 ? "#00ff88" : "#ff4757";
  return (
    <div style={{display:"flex", alignItems:"center", gap:6}}>
      <div style={{width:60, height:4, background:"#ffffff12", borderRadius:2, overflow:"hidden"}}>
        <div style={{width:`${pct}%`, height:"100%", background:color, borderRadius:2}}/>
      </div>
      <span style={{fontSize:9, color, fontFamily:"'IBM Plex Mono',monospace", minWidth:36}}>
        {value >= 0 ? "+" : ""}{(value*100).toFixed(0)}%
      </span>
    </div>
  );
}

function WeatherBadge({wind, temp, precip, isDome}) {
  if (isDome) return <span style={{fontSize:9, color:"#555", background:"#ffffff08", border:"1px solid #ffffff0a", padding:"2px 6px", borderRadius:3}}>🏟 DOME</span>;
  const flags = [];
  if (wind >= 20) flags.push({icon:"💨", label:`${wind}mph HIGH`, color:"#ff4757"});
  else if (wind >= 12) flags.push({icon:"💨", label:`${wind}mph`, color:"#ffa502"});
  if (temp <= 32) flags.push({icon:"🥶", label:`${temp}°F`, color:"#00e5ff"});
  else if (temp <= 45) flags.push({icon:"❄️", label:`${temp}°F`, color:"#8888ff"});
  if (precip) flags.push({icon:"🌧️", label:"RAIN", color:"#ffa502"});
  if (!flags.length) return null;
  return (
    <div style={{display:"flex", gap:4, flexWrap:"wrap"}}>
      {flags.map((f,i) => (
        <span key={i} style={{fontSize:9, color:f.color, background:f.color+"18",
          border:`1px solid ${f.color}40`, padding:"2px 6px", borderRadius:3, fontFamily:"'IBM Plex Mono',monospace"}}>
          {f.icon} {f.label}
        </span>
      ))}
    </div>
  );
}

function PlayCard({play, expanded, onToggle}) {
  const tier    = TIER_CONFIG[play.tier] || TIER_CONFIG.T2;
  const posColor = POS_COLOR[play.pos] || "#888";
  const allNotes = [...play.gs_notes, ...play.mu_notes, ...play.wx_notes, ...play.rest_notes].filter(Boolean);

  const adjs = [
    {label:"Streak",  val:play.adj_streak},
    {label:"Line",    val:play.adj_line},
    {label:"Script",  val:play.adj_gs},
    {label:"Matchup", val:play.adj_matchup},
    {label:"Weather", val:play.adj_weather},
    {label:"Rest",    val:play.adj_rest},
    {label:"Travel",  val:play.adj_travel},
  ].filter(a => a.val !== 0);

  return (
    <div onClick={onToggle} style={{
      background:"#0d1117", border:`1px solid ${expanded ? tier.color+"60" : "#ffffff0a"}`,
      borderRadius:8, overflow:"hidden", cursor:"pointer",
      transition:"all 0.2s", marginBottom:8,
      boxShadow: expanded ? `0 0 20px ${tier.color}18` : "none",
    }}>
      {/* Header */}
      <div style={{padding:"12px 16px", display:"flex", alignItems:"center", gap:12}}>
        {/* Tier badge */}
        <div style={{
          background:tier.bg, border:`1px solid ${tier.border}`,
          borderRadius:4, padding:"3px 8px", minWidth:60, textAlign:"center",
        }}>
          <div style={{fontSize:8, color:tier.color, fontFamily:"'IBM Plex Mono',monospace",
            letterSpacing:1, fontWeight:700}}>{tier.icon} {tier.label}</div>
        </div>

        {/* Player info */}
        <div style={{flex:1, minWidth:0}}>
          <div style={{display:"flex", alignItems:"center", gap:8, flexWrap:"wrap"}}>
            <span style={{fontSize:14, fontWeight:700, color:"#f0f0f0",
              fontFamily:"'Barlow Condensed',sans-serif", letterSpacing:0.5}}>
              {play.player}
            </span>
            <span style={{fontSize:10, color:posColor, background:posColor+"18",
              border:`1px solid ${posColor}40`, padding:"1px 6px", borderRadius:3,
              fontFamily:"'IBM Plex Mono',monospace", fontWeight:700}}>
              {play.pos}
            </span>
            <span style={{fontSize:10, color:"#555", fontFamily:"'IBM Plex Mono',monospace"}}>
              {play.team} vs {play.opp}
            </span>
            <span style={{fontSize:9, color:"#444", fontFamily:"'IBM Plex Mono',monospace"}}>
              {WINDOW_LABEL[play.game_window] || play.game_window}
            </span>
          </div>
          <div style={{fontSize:12, color:"#888", marginTop:2, fontFamily:"'IBM Plex Mono',monospace"}}>
            {PROP_LABEL[play.prop] || play.prop} OVER {play.posted_line}
          </div>
        </div>

        {/* Key stats */}
        <div style={{display:"flex", gap:16, alignItems:"center"}}>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:18, fontWeight:800, color:tier.color,
              fontFamily:"'Barlow Condensed',sans-serif"}}>
              {(play.model_prob * 100).toFixed(0)}%
            </div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1}}>MODEL</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:14, fontWeight:700, color:"#f0f0f0",
              fontFamily:"'IBM Plex Mono',monospace"}}>
              {play.streak}g
            </div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1}}>STREAK</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:14, fontWeight:700, color:"#f0f0f0",
              fontFamily:"'IBM Plex Mono',monospace"}}>
              {(play.l6 * 100).toFixed(0)}%
            </div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1}}>L6</div>
          </div>
          <div style={{fontSize:16, color:expanded ? tier.color : "#444",
            transition:"transform 0.2s",
            transform: expanded ? "rotate(180deg)" : "none"}}>▾</div>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{borderTop:"1px solid #ffffff08", padding:"16px"}}>
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16}}>

            {/* Left — stats */}
            <div>
              <div style={{fontSize:10, color:"#444", letterSpacing:2,
                fontFamily:"'IBM Plex Mono',monospace", marginBottom:8}}>LINE ANALYSIS</div>

              <div style={{display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:8, marginBottom:12}}>
                {[
                  {label:"WMA (weighted)", val:play.wma},
                  {label:"SMA-4 (recent)", val:play.sma_4},
                  {label:"Gap vs line", val:`+${play.line_vs_wma}`},
                ].map(s => (
                  <div key={s.label} style={{background:"#ffffff06", borderRadius:6, padding:"8px 10px"}}>
                    <div style={{fontSize:16, fontWeight:700, color:"#f0f0f0",
                      fontFamily:"'Barlow Condensed',sans-serif"}}>{s.val}</div>
                    <div style={{fontSize:8, color:"#555", marginTop:2}}>{s.label}</div>
                  </div>
                ))}
              </div>

              <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12}}>
                {[
                  {label:"Spread", val:`${play.spread > 0 ? "+" : ""}${play.spread}`},
                  {label:"Game Total", val:play.total},
                ].map(s => (
                  <div key={s.label} style={{background:"#ffffff06", borderRadius:6, padding:"8px 10px"}}>
                    <div style={{fontSize:14, fontWeight:700, color:"#e0e0e0",
                      fontFamily:"'IBM Plex Mono',monospace"}}>{s.val}</div>
                    <div style={{fontSize:8, color:"#555", marginTop:2}}>{s.label}</div>
                  </div>
                ))}
              </div>

              <WeatherBadge wind={play.wind} temp={play.temp}
                precip={play.precip} isDome={play.is_dome}/>
            </div>

            {/* Right — adjustments + notes */}
            <div>
              <div style={{fontSize:10, color:"#444", letterSpacing:2,
                fontFamily:"'IBM Plex Mono',monospace", marginBottom:8}}>SIGNAL BREAKDOWN</div>

              <div style={{display:"flex", flexDirection:"column", gap:6, marginBottom:12}}>
                {adjs.map(a => (
                  <div key={a.label} style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
                    <span style={{fontSize:10, color:"#666", fontFamily:"'IBM Plex Mono',monospace",
                      minWidth:60}}>{a.label}</span>
                    {adjBar(a.val)}
                  </div>
                ))}
                <div style={{display:"flex", justifyContent:"space-between", alignItems:"center",
                  borderTop:"1px solid #ffffff08", paddingTop:6, marginTop:2}}>
                  <span style={{fontSize:10, color:"#888", fontFamily:"'IBM Plex Mono',monospace",
                    minWidth:60}}>TOTAL</span>
                  {adjBar(play.total_adj, 0.30)}
                </div>
              </div>

              {allNotes.length > 0 && (
                <>
                  <div style={{fontSize:10, color:"#444", letterSpacing:2,
                    fontFamily:"'IBM Plex Mono',monospace", marginBottom:6}}>CONTEXT</div>
                  {allNotes.slice(0,4).map((n,i) => (
                    <div key={i} style={{fontSize:10, color:"#666", marginBottom:4,
                      paddingLeft:8, borderLeft:`2px solid ${tier.color}40`}}>
                      {n}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Alt lines */}
          {play.alt_lines && play.alt_lines.length > 0 && (
            <div style={{marginTop:12, paddingTop:12, borderTop:"1px solid #ffffff08"}}>
              <div style={{fontSize:10, color:"#444", letterSpacing:2,
                fontFamily:"'IBM Plex Mono',monospace", marginBottom:8}}>
                ALT LINES (reduced juice)
              </div>
              <div style={{display:"flex", gap:6, flexWrap:"wrap"}}>
                {play.alt_lines.map(l => (
                  <div key={l} style={{
                    background:"#ffffff06", border:"1px solid #ffffff0f",
                    borderRadius:4, padding:"4px 10px",
                    fontSize:11, color:"#aaa", fontFamily:"'IBM Plex Mono',monospace",
                  }}>
                    {l}+
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ParlayCard({parlay, index}) {
  const [open, setOpen] = useState(false);
  const evColor = parlay.ev >= 2 ? "#00ff88" : parlay.ev >= 1 ? "#f5c518" : "#ffa502";

  return (
    <div onClick={() => setOpen(!open)} style={{
      background:"#0d1117", border:"1px solid #ffffff0f",
      borderRadius:8, overflow:"hidden", cursor:"pointer", marginBottom:8,
      transition:"border-color 0.2s",
    }}
    onMouseEnter={e => e.currentTarget.style.borderColor="#ffffff20"}
    onMouseLeave={e => e.currentTarget.style.borderColor="#ffffff0f"}
    >
      <div style={{padding:"12px 16px", display:"flex", alignItems:"center", gap:12}}>
        <div style={{
          width:28, height:28, borderRadius:6,
          background:"linear-gradient(135deg, #00ff88, #00cc6a)",
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:12, fontWeight:900, color:"#060911", flexShrink:0,
        }}>#{index+1}</div>

        <div style={{flex:1}}>
          <div style={{fontSize:12, color:"#888", fontFamily:"'IBM Plex Mono',monospace"}}>
            {parlay.type} · {parlay.legs.map(l => l.player.split(" ").pop()).join(" + ")}
          </div>
        </div>

        <div style={{display:"flex", gap:16, alignItems:"center"}}>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:18, fontWeight:800, color:"#00ff88",
              fontFamily:"'Barlow Condensed',sans-serif"}}>{parlay.parlay_odds}</div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1}}>ODDS</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:14, fontWeight:700, color:"#f0f0f0",
              fontFamily:"'IBM Plex Mono',monospace"}}>
              {(parlay.hit_prob * 100).toFixed(0)}%
            </div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1}}>HIT PROB</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:14, fontWeight:700, color:evColor,
              fontFamily:"'IBM Plex Mono',monospace"}}>+{parlay.ev.toFixed(2)}</div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1}}>EV/unit</div>
          </div>
        </div>
      </div>

      {open && (
        <div style={{borderTop:"1px solid #ffffff08", padding:"12px 16px"}}>
          {parlay.legs.map((leg, i) => (
            <div key={i} style={{display:"flex", justifyContent:"space-between",
              alignItems:"center", marginBottom:6,
              paddingBottom:6, borderBottom: i < parlay.legs.length-1 ? "1px solid #ffffff06" : "none"}}>
              <div>
                <span style={{fontSize:12, color:"#e0e0e0", fontFamily:"'Barlow Condensed',sans-serif",
                  fontWeight:700}}>{leg.player}</span>
                <span style={{fontSize:10, color:"#666", marginLeft:8,
                  fontFamily:"'IBM Plex Mono',monospace"}}>{leg.prop}</span>
              </div>
              <div style={{display:"flex", gap:12}}>
                <span style={{fontSize:11, color:"#888", fontFamily:"'IBM Plex Mono',monospace"}}>
                  {leg.odds}
                </span>
                <span style={{fontSize:11, color:"#00ff88", fontFamily:"'IBM Plex Mono',monospace"}}>
                  {(leg.prob * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
          <div style={{marginTop:8, fontSize:10, color:"#555", fontFamily:"'IBM Plex Mono',monospace"}}>
            Parlay math: {parlay.legs.map(l => l.odds).join(" × ")} = {parlay.parlay_odds}
          </div>
        </div>
      )}
    </div>
  );
}

export default function PlaybookHub() {
  const [activeTab, setActive] = useState("plays");
  const [activeTier, setTier]  = useState("ALL");
  const [activePos,  setPos]   = useState("ALL");
  const [expanded,   setExp]   = useState(null);

  const week   = 1;
  const season = 2026;

  const tiers = ["ALL","AUTO","T1","T2"];
  const positions = ["ALL","QB","RB","WR","TE"];

  const filtered = SAMPLE_PLAYS.filter(p =>
    (activeTier === "ALL" || p.tier === activeTier) &&
    (activePos  === "ALL" || p.pos  === activePos)
  );

  const autoCount = SAMPLE_PLAYS.filter(p => p.tier === "AUTO").length;
  const t1Count   = SAMPLE_PLAYS.filter(p => p.tier === "T1").length;

  const T = {
    bg:      "#060911",
    surface: "#0d1117",
    card:    "#111820",
    border:  "#ffffff0a",
    accent:  "#00ff88",
    text:    "#f0f0f0",
    muted:   "#555",
    mono:    "'IBM Plex Mono', monospace",
    head:    "'Barlow Condensed', sans-serif",
  };

  return (
    <div style={{background:T.bg, minHeight:"100vh", padding:"0 0 60px"}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #060911; }
        ::-webkit-scrollbar-thumb { background: #ffffff15; border-radius: 2px; }
      `}</style>

      {/* Header */}
      <div style={{background:"#0a0f1a", borderBottom:`1px solid ${T.border}`,
        padding:"20px 24px 0"}}>
        <div style={{display:"flex", alignItems:"flex-start",
          justifyContent:"space-between", marginBottom:16}}>
          <div>
            <div style={{fontSize:11, color:T.muted, letterSpacing:3,
              fontFamily:T.mono, marginBottom:4}}>EDGE INDEX / NFL</div>
            <div style={{fontSize:28, fontWeight:800, color:T.text,
              fontFamily:T.head, letterSpacing:1}}>
              WEEK {week} {season} PLAYBOOK
            </div>
          </div>
          <div style={{display:"flex", gap:12}}>
            {[
              {label:"AUTO PLAYS", val:autoCount, color:"#00ff88"},
              {label:"TIER 1",     val:t1Count,   color:"#f5c518"},
              {label:"PARLAYS",    val:PARLAYS.length, color:"#00e5ff"},
            ].map(s => (
              <div key={s.label} style={{textAlign:"center",
                background:"#ffffff06", border:"1px solid #ffffff0a",
                borderRadius:8, padding:"10px 16px"}}>
                <div style={{fontSize:22, fontWeight:800, color:s.color,
                  fontFamily:T.head}}>{s.val}</div>
                <div style={{fontSize:8, color:T.muted, letterSpacing:2,
                  fontFamily:T.mono}}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div style={{display:"flex", gap:0}}>
          {[{id:"plays",   label:"🎯 Plays"},
            {id:"parlays", label:"⚡ Parlays"},
            {id:"streaks", label:"🔥 Streak Sheet"},
          ].map(t => (
            <button key={t.id} onClick={() => setActive(t.id)}
              style={{padding:"10px 20px", background:"transparent", border:"none",
                borderBottom: activeTab===t.id ? `2px solid ${T.accent}` : "2px solid transparent",
                color: activeTab===t.id ? T.accent : T.muted,
                fontSize:12, fontWeight:600, cursor:"pointer",
                fontFamily:T.mono, transition:"all 0.15s", letterSpacing:0.5}}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{padding:"20px 24px", maxWidth:1280, margin:"0 auto"}}>

        {/* PLAYS TAB */}
        {activeTab === "plays" && (
          <>
            {/* Filters */}
            <div style={{display:"flex", gap:8, marginBottom:16, flexWrap:"wrap"}}>
              <div style={{display:"flex", gap:4}}>
                {tiers.map(t => (
                  <button key={t} onClick={() => setTier(t)}
                    style={{padding:"5px 12px", borderRadius:4,
                      background: activeTier===t ? TIER_CONFIG[t]?.color||T.accent+"22" : "#ffffff08",
                      border: `1px solid ${activeTier===t ? TIER_CONFIG[t]?.color||T.accent : "#ffffff0f"}`,
                      color: activeTier===t ? TIER_CONFIG[t]?.color||T.accent : T.muted,
                      fontSize:10, cursor:"pointer", fontFamily:T.mono,
                      fontWeight:700, letterSpacing:0.5}}>
                    {t}
                  </button>
                ))}
              </div>
              <div style={{display:"flex", gap:4}}>
                {positions.map(p => (
                  <button key={p} onClick={() => setPos(p)}
                    style={{padding:"5px 12px", borderRadius:4,
                      background: activePos===p ? (POS_COLOR[p]||T.accent)+"22" : "#ffffff08",
                      border: `1px solid ${activePos===p ? POS_COLOR[p]||T.accent : "#ffffff0f"}`,
                      color: activePos===p ? POS_COLOR[p]||T.accent : T.muted,
                      fontSize:10, cursor:"pointer", fontFamily:T.mono,
                      fontWeight:700, letterSpacing:0.5}}>
                    {p}
                  </button>
                ))}
              </div>
              <div style={{marginLeft:"auto", fontSize:10, color:T.muted,
                fontFamily:T.mono, alignSelf:"center"}}>
                {filtered.length} plays
              </div>
            </div>

            {filtered.map(p => (
              <PlayCard key={`${p.player}-${p.prop}`} play={p}
                expanded={expanded === `${p.player}-${p.prop}`}
                onToggle={() => setExp(
                  expanded === `${p.player}-${p.prop}`
                    ? null : `${p.player}-${p.prop}`
                )}/>
            ))}
          </>
        )}

        {/* PARLAYS TAB */}
        {activeTab === "parlays" && (
          <>
            <div style={{marginBottom:16, padding:"12px 16px",
              background:"#ffffff06", borderRadius:8, border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:11, color:T.muted, fontFamily:T.mono,
                letterSpacing:1, marginBottom:4}}>PARLAY MATH</div>
              <div style={{fontSize:12, color:"#666", fontFamily:T.mono, lineHeight:1.6}}>
                Combining heavy juice plays (-130 to -200) to reach even money to +300.
                Hit prob = model probs multiplied. EV = hit_prob × (decimal-1) - miss_prob.
              </div>
            </div>
            {PARLAYS.map((p,i) => <ParlayCard key={i} parlay={p} index={i}/>)}
          </>
        )}

        {/* STREAKS TAB */}
        {activeTab === "streaks" && (
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12}}>
            {[
              {pos:"QB", icon:"💪", plays: SAMPLE_PLAYS.filter(p=>p.pos==="QB")},
              {pos:"RB", icon:"🏃", plays: SAMPLE_PLAYS.filter(p=>p.pos==="RB")},
              {pos:"WR", icon:"🏈", plays: SAMPLE_PLAYS.filter(p=>p.pos==="WR")},
              {pos:"TE", icon:"🎯", plays: SAMPLE_PLAYS.filter(p=>p.pos==="TE")},
            ].map(group => (
              <div key={group.pos} style={{background:T.surface,
                border:`1px solid ${T.border}`, borderRadius:8, padding:"16px"}}>
                <div style={{fontSize:13, fontWeight:800, color:POS_COLOR[group.pos],
                  fontFamily:T.head, letterSpacing:1, marginBottom:12}}>
                  {group.icon} {group.pos} STREAKS
                </div>
                {group.plays.length === 0 && (
                  <div style={{fontSize:11, color:T.muted, fontFamily:T.mono}}>
                    No plays this week
                  </div>
                )}
                {group.plays.map(p => (
                  <div key={`${p.player}-${p.prop}`} style={{
                    display:"flex", justifyContent:"space-between",
                    alignItems:"center", marginBottom:8,
                    paddingBottom:8, borderBottom:`1px solid ${T.border}`,
                  }}>
                    <div>
                      <div style={{fontSize:12, color:T.text,
                        fontFamily:T.head, fontWeight:700}}>
                        {p.player.split(" ").map((n,i) =>
                          i===0 ? n[0]+"." : n).join(" ")}
                      </div>
                      <div style={{fontSize:9, color:T.muted, fontFamily:T.mono}}>
                        {PROP_LABEL[p.prop]} OVER {p.posted_line}
                      </div>
                    </div>
                    <div style={{textAlign:"right"}}>
                      <div style={{fontSize:13, fontWeight:700,
                        color: p.l6 >= 0.90 ? "#00ff88" : p.l6 >= 0.75 ? "#f5c518" : "#ffa502",
                        fontFamily:T.mono}}>
                        {p.streak}/{p.streak + Math.round(p.streak * (1/p.l6 - 1))}
                      </div>
                      <div style={{fontSize:8, color:T.muted}}>
                        {(p.l6*100).toFixed(0)}% L6
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
