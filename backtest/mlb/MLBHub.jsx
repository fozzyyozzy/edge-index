import { useState } from "react";

// ── SAMPLE DATA ───────────────────────────────────────────────
const TODAY = "2026-05-08";

const PITCHER_PLAYS = [
  {
    pitcher:"Spencer Strider", team:"ATL", opp:"MIA", home:"ATL",
    prop:"strikeouts", line:8.5, odds:-120, tier:"T1", model_prob:0.80,
    streak:5, l5_avg:9.6, k_pct:0.378, opp_k_pct:0.265,
    alt_lines:[7.5, 8.0], hand:"R", days_rest:5,
    notes:["37.8% K rate vs 26.5% opp K rate","Umpire: Angel Hernandez (+7% K rate)","5-start K streak"],
    result:null,
  },
  {
    pitcher:"Zack Wheeler", team:"PHI", opp:"NYM", home:"PHI",
    prop:"strikeouts", line:6.5, odds:-130, tier:"T1", model_prob:0.80,
    streak:5, l5_avg:7.8, k_pct:0.298, opp_k_pct:0.248,
    alt_lines:[5.5, 6.0], hand:"R", days_rest:5,
    notes:["Park: PHI hitter-friendly (-3% K adj)","Umpire: Laz Diaz (+8% K rate)"],
    result:null,
  },
  {
    pitcher:"Gerrit Cole", team:"NYY", opp:"BOS", home:"NYY",
    prop:"strikeouts", line:7.5, odds:-115, tier:"T2", model_prob:0.63,
    streak:5, l5_avg:8.2, k_pct:0.312, opp_k_pct:0.228,
    alt_lines:[6.5, 7.0], hand:"R", days_rest:4,
    notes:["31.2% K rate vs 22.8% opp K rate","Umpire: Tom Hallion (+5% K rate)"],
    result:null,
  },
  {
    pitcher:"Framber Valdez", team:"HOU", opp:"TEX", home:"HOU",
    prop:"strikeouts", line:5.5, odds:-140, tier:"SKIP", model_prob:0.48,
    streak:2, l5_avg:6.0, k_pct:0.225, opp_k_pct:0.238,
    alt_lines:[4.5, 5.0], hand:"L", days_rest:5,
    notes:["Umpire: Bill Miller (-4% K rate)","Opp K% (23.8%) higher than pitcher K% (22.5%)"],
    result:null,
  },
];

const BATTER_PLAYS = [
  {
    batter:"Juan Soto", team:"NYY", opp:"BOS", home:"NYY",
    prop:"total_bases", line:1.5, odds:-120, tier:"AUTO", model_prob:0.79,
    hit_streak:6, platoon_avg:0.278, batter_avg:0.288, pitcher_hand:"R",
    prior_tb:[3,1,5,0,4,2,3,5,2,4],
    alt_lines:[0.5, 1.0], notes:["Park: NYY hitter-friendly (+3%)","6-game hit streak"],
    result:null,
  },
  {
    batter:"Yordan Alvarez", team:"HOU", opp:"TEX", home:"HOU",
    prop:"hits", line:1.5, odds:-140, tier:"T1", model_prob:0.66,
    hit_streak:10, platoon_avg:0.318, batter_avg:0.302, pitcher_hand:"L",
    prior_tb:[2,2,1,2,1,2,2,1,2,2],
    alt_lines:[0.5, 1.0], notes:["Platoon advantage vs LHP (.318 vs .302 avg)","10-game hit streak","Park: HOU hitter-friendly (+4%)"],
    result:null,
  },
  {
    batter:"Freddie Freeman", team:"LAD", opp:"SD", home:"LAD",
    prop:"hits", line:1.5, odds:-130, tier:"T1", model_prob:0.72,
    hit_streak:7, platoon_avg:0.289, batter_avg:0.298, pitcher_hand:"R",
    prior_tb:[2,1,2,1,2,2,1,2,1,2],
    alt_lines:[0.5, 1.0], notes:["7-game hit streak","LAD neutral park"],
    result:null,
  },
  {
    batter:"Shohei Ohtani", team:"LAD", opp:"SD", home:"LAD",
    prop:"total_bases", line:1.5, odds:-125, tier:"T1", model_prob:0.70,
    hit_streak:4, platoon_avg:0.310, batter_avg:0.305, pitcher_hand:"R",
    prior_tb:[4,0,3,1,2,3,0,4,2,3],
    alt_lines:[0.5, 1.0], notes:["Power hitter vs weak SD bullpen","LAD neutral park"],
    result:null,
  },
];

const STREAK_DATA = {
  pitchers: [
    {name:"S. Strider",  team:"ATL", prop:"5+ Ks",  streak:10, total:10, rate:1.00},
    {name:"Z. Wheeler",  team:"PHI", prop:"5+ Ks",  streak:8,  total:10, rate:0.90},
    {name:"G. Cole",     team:"NYY", prop:"6+ Ks",  streak:7,  total:10, rate:0.80},
    {name:"K. Gausman",  team:"TOR", prop:"5+ Ks",  streak:6,  total:9,  rate:0.89},
    {name:"C. Burnes",   team:"BAL", prop:"5+ Ks",  streak:5,  total:8,  rate:0.88},
    {name:"P. Corbin",   team:"WAS", prop:"4+ Ks",  streak:5,  total:10, rate:0.80},
    {name:"F. Valdez",   team:"HOU", prop:"4+ Ks",  streak:4,  total:8,  rate:0.75},
    {name:"L. Gilbert",  team:"SEA", prop:"5+ Ks",  streak:4,  total:7,  rate:0.86},
  ],
  batters: [
    {name:"Y. Alvarez",  team:"HOU", prop:"1+ Hits", streak:10, total:12, rate:0.92},
    {name:"F. Freeman",  team:"LAD", prop:"1+ Hits", streak:7,  total:10, rate:0.90},
    {name:"J. Soto",     team:"NYY", prop:"1+ Hits", streak:6,  total:9,  rate:0.89},
    {name:"M. Betts",    team:"LAD", prop:"1+ Hits", streak:6,  total:10, rate:0.80},
    {name:"S. Ohtani",   team:"LAD", prop:"1+ TB",   streak:5,  total:8,  rate:0.88},
    {name:"R. Devers",   team:"BOS", prop:"1+ Hits", streak:5,  total:9,  rate:0.78},
    {name:"B. Harper",   team:"PHI", prop:"1+ Hits", streak:5,  total:10, rate:0.80},
    {name:"T. Turner",   team:"PHI", prop:"1+ Hits", streak:4,  total:8,  rate:0.88},
  ],
};

// Today's tracking results — 2026-05-08 REAL PLAYS
// Source: Real DK/FD/BetMGM lines + pybaseball 2025 game logs
const TRACKING = [
  {id:1, player:"Kyle Bradish",    prop:"K OVER 5.5",  odds:-114, model:0.75, actual:null, hit:null, tier:"T1", game:"ATL @ BAL",   note:"6 starts, L5 avg 7.4 Ks, 4-start streak"},
  {id:2, player:"Connelly Early",  prop:"K OVER 4.5",  odds:+105, model:0.68, actual:null, hit:null, tier:"T1", game:"COL @ PHI",   note:"5 starts, L5 avg 7.0 Ks, plus money edge"},
  {id:3, player:"Max Fried",       prop:"K OVER 5.5",  odds:-120, model:0.60, actual:null, hit:null, tier:"T2", game:"NYY @ MIL",   note:"38 starts, L5 avg 6.6 Ks, 0-start streak"},
  {id:4, player:"Jacob Lopez",     prop:"K OVER 4.5",  odds:-135, model:0.60, actual:null, hit:null, tier:"T2", game:"ATL @ BAL",   note:"22 starts, L5 avg 6.8 Ks, 0-start streak"},
];

// ── HELPERS ──────────────────────────────────────────────────
const TIER_CFG = {
  AUTO: {color:"#00ff88", bg:"#00ff8818", border:"#00ff8840", icon:"⚡"},
  T1:   {color:"#f5c518", bg:"#f5c51818", border:"#f5c51840", icon:"★"},
  T2:   {color:"#00e5ff", bg:"#00e5ff18", border:"#00e5ff40", icon:"◆"},
  SKIP: {color:"#555",    bg:"#55555518", border:"#55555540", icon:"✗"},
};

function tierBadge(tier) {
  const cfg = TIER_CFG[tier] || TIER_CFG.T2;
  return (
    <span style={{
      fontSize:9, fontWeight:700, fontFamily:"'IBM Plex Mono',monospace",
      color:cfg.color, background:cfg.bg, border:`1px solid ${cfg.border}`,
      padding:"2px 7px", borderRadius:3, letterSpacing:1,
    }}>{cfg.icon} {tier}</span>
  );
}

function streakBar(streak, total, rate) {
  const color = rate >= 0.90 ? "#00ff88" : rate >= 0.75 ? "#f5c518" : "#ffa502";
  const emoji  = rate >= 0.95 ? "🔥" : rate >= 0.80 ? "✅" : "📈";
  return (
    <div style={{display:"flex", alignItems:"center", gap:8}}>
      <span style={{fontSize:16}}>{emoji}</span>
      <div>
        <div style={{fontSize:12, fontWeight:700, color, fontFamily:"'IBM Plex Mono',monospace"}}>
          {streak}/{total}
        </div>
        <div style={{width:60, height:3, background:"#ffffff12", borderRadius:2, marginTop:2}}>
          <div style={{width:`${rate*100}%`, height:"100%", background:color, borderRadius:2}}/>
        </div>
      </div>
      <span style={{fontSize:10, color:"#555", fontFamily:"'IBM Plex Mono',monospace"}}>
        {(rate*100).toFixed(0)}%
      </span>
    </div>
  );
}

// ── PLAY CARD ─────────────────────────────────────────────────
function PlayCard({play, type}) {
  const [open, setOpen] = useState(false);
  const cfg = TIER_CFG[play.tier] || TIER_CFG.T2;
  const isSkip = play.tier === "SKIP";

  return (
    <div onClick={() => !isSkip && setOpen(!open)} style={{
      background:"#0d1117",
      border:`1px solid ${open ? cfg.color+"50" : "#ffffff0a"}`,
      borderRadius:8, marginBottom:8, overflow:"hidden",
      cursor: isSkip ? "default" : "pointer",
      opacity: isSkip ? 0.5 : 1,
      transition:"all 0.2s",
    }}>
      <div style={{padding:"12px 16px", display:"flex", alignItems:"center", gap:12}}>
        {/* Tier */}
        <div style={{flexShrink:0}}>{tierBadge(play.tier)}</div>

        {/* Info */}
        <div style={{flex:1, minWidth:0}}>
          <div style={{display:"flex", alignItems:"center", gap:8, flexWrap:"wrap"}}>
            <span style={{fontSize:14, fontWeight:700, color:"#f0f0f0",
              fontFamily:"'Barlow Condensed',sans-serif"}}>
              {type === "pitcher" ? play.pitcher : play.batter}
            </span>
            <span style={{fontSize:10, color:"#555", fontFamily:"'IBM Plex Mono',monospace"}}>
              {play.team} vs {play.opp}
            </span>
          </div>
          <div style={{fontSize:11, color:"#777", fontFamily:"'IBM Plex Mono',monospace", marginTop:2}}>
            {play.prop.toUpperCase()} OVER {play.line}
            {type === "pitcher" && ` | ${play.hand}HP | ${play.days_rest}d rest`}
            {type === "batter"  && ` | vs ${play.pitcher_hand}HP`}
          </div>
        </div>

        {/* Stats */}
        <div style={{display:"flex", gap:14, alignItems:"center", flexShrink:0}}>
          {type === "pitcher" && (
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:13, fontWeight:700, color:"#e0e0e0",
                fontFamily:"'IBM Plex Mono',monospace"}}>{play.l5_avg}</div>
              <div style={{fontSize:8, color:"#444"}}>L5 AVG Ks</div>
            </div>
          )}
          {type === "batter" && (
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:13, fontWeight:700, color:"#e0e0e0",
                fontFamily:"'IBM Plex Mono',monospace"}}>{play.hit_streak}g</div>
              <div style={{fontSize:8, color:"#444"}}>STREAK</div>
            </div>
          )}
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:18, fontWeight:800, color:cfg.color,
              fontFamily:"'Barlow Condensed',sans-serif"}}>
              {(play.model_prob*100).toFixed(0)}%
            </div>
            <div style={{fontSize:8, color:"#444"}}>MODEL</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:13, fontWeight:700, color:"#888",
              fontFamily:"'IBM Plex Mono',monospace"}}>{play.odds}</div>
            <div style={{fontSize:8, color:"#444"}}>ODDS</div>
          </div>
          {!isSkip && (
            <span style={{fontSize:14, color: open ? cfg.color : "#333",
              transition:"transform 0.2s", display:"block",
              transform: open ? "rotate(180deg)" : "none"}}>▾</span>
          )}
        </div>
      </div>

      {/* Expanded */}
      {open && !isSkip && (
        <div style={{borderTop:"1px solid #ffffff08", padding:"14px 16px"}}>
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12}}>
            <div>
              <div style={{fontSize:9, color:"#444", letterSpacing:2,
                fontFamily:"'IBM Plex Mono',monospace", marginBottom:8}}>ANALYSIS</div>
              {play.notes.map((n,i) => (
                <div key={i} style={{fontSize:10, color:"#666", marginBottom:5,
                  paddingLeft:8, borderLeft:`2px solid ${cfg.color}40`}}>{n}</div>
              ))}
            </div>
            <div>
              <div style={{fontSize:9, color:"#444", letterSpacing:2,
                fontFamily:"'IBM Plex Mono',monospace", marginBottom:8}}>ALT LINES</div>
              <div style={{display:"flex", gap:6, flexWrap:"wrap"}}>
                {play.alt_lines.map(l => (
                  <div key={l} style={{
                    background:"#ffffff06", border:"1px solid #ffffff0f",
                    borderRadius:4, padding:"4px 10px",
                    fontSize:11, color:"#aaa", fontFamily:"'IBM Plex Mono',monospace",
                  }}>{l}+ OVER</div>
                ))}
              </div>
              {type === "pitcher" && (
                <div style={{marginTop:10}}>
                  <div style={{fontSize:9, color:"#444", letterSpacing:2,
                    fontFamily:"'IBM Plex Mono',monospace", marginBottom:6}}>K RATE MATCHUP</div>
                  <div style={{fontSize:11, color:"#888", fontFamily:"'IBM Plex Mono',monospace"}}>
                    {(play.k_pct*100).toFixed(1)}% K rate vs {(play.opp_k_pct*100).toFixed(1)}% opp K%
                    {play.k_pct > play.opp_k_pct
                      ? <span style={{color:"#00ff88"}}> ✓ Edge</span>
                      : <span style={{color:"#ff4757"}}> ✗ Fade</span>
                    }
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── TRACKER ROW ───────────────────────────────────────────────
function TrackerRow({play, onUpdate}) {
  const hitColor   = play.hit === true ? "#00ff88" : play.hit === false ? "#ff4757" : "#444";
  const hitLabel   = play.hit === true ? "✓ HIT" : play.hit === false ? "✗ MISS" : "PENDING";

  return (
    <div style={{
      display:"grid", gridTemplateColumns:"1fr 120px 70px 70px 80px 90px",
      gap:8, alignItems:"center", padding:"10px 16px",
      borderBottom:"1px solid #ffffff06", fontSize:11,
    }}>
      <div>
        <div style={{color:"#e0e0e0", fontWeight:600,
          fontFamily:"'Barlow Condensed',sans-serif", fontSize:13}}>
          {play.player}
        </div>
        <div style={{color:"#555", fontFamily:"'IBM Plex Mono',monospace", fontSize:9}}>
          {play.prop}
        </div>
      </div>
      <div style={{color:"#888", fontFamily:"'IBM Plex Mono',monospace"}}>{play.odds}</div>
      <div style={{color:"#00e5ff", fontFamily:"'IBM Plex Mono',monospace"}}>
        {(play.model*100).toFixed(0)}%
      </div>
      <input
        type="number" placeholder="—" value={play.actual ?? ""}
        onClick={e => e.stopPropagation()}
        onChange={e => onUpdate(play.id, "actual", e.target.value)}
        style={{
          background:"#ffffff08", border:"1px solid #ffffff15", borderRadius:4,
          color:"#f0f0f0", padding:"4px 8px", fontSize:11, width:"100%",
          fontFamily:"'IBM Plex Mono',monospace", outline:"none",
        }}
      />
      <div style={{display:"flex", gap:4}}>
        <button onClick={e => {e.stopPropagation(); onUpdate(play.id,"hit",true)}}
          style={{flex:1, padding:"4px", borderRadius:3, border:"none",
            background: play.hit===true ? "#00ff88" : "#ffffff10",
            color: play.hit===true ? "#000" : "#555",
            cursor:"pointer", fontSize:10, fontWeight:700}}>✓</button>
        <button onClick={e => {e.stopPropagation(); onUpdate(play.id,"hit",false)}}
          style={{flex:1, padding:"4px", borderRadius:3, border:"none",
            background: play.hit===false ? "#ff4757" : "#ffffff10",
            color: play.hit===false ? "#fff" : "#555",
            cursor:"pointer", fontSize:10, fontWeight:700}}>✗</button>
      </div>
      <div style={{color:hitColor, fontFamily:"'IBM Plex Mono',monospace",
        fontSize:10, fontWeight:700}}>{hitLabel}</div>
    </div>
  );
}

// ── PARLAY CANDIDATES ────────────────────────────────────────
const PARLAY_PLAYS = [
  {player:"Kyle Bradish",   prop:"K OVER 5.5",  odds:-114, model:0.75, tier:"T1", game:"ATL @ BAL"},
  {player:"Connelly Early", prop:"K OVER 4.5",  odds:+105, model:0.68, tier:"T1", game:"COL @ PHI"},
  {player:"F. Freeman",     prop:"H OVER 0.5",  odds:-175, model:0.87, tier:"AUTO", game:"LAD vs SD"},
  {player:"A. Judge",       prop:"H OVER 0.5",  odds:-185, model:0.88, tier:"AUTO", game:"NYY @ MIL"},
  {player:"Y. Alvarez",     prop:"H OVER 0.5",  odds:-196, model:0.85, tier:"AUTO", game:"HOU vs TEX"},
  {player:"J. Soto",        prop:"TB OVER 0.5", odds:-165, model:0.83, tier:"AUTO", game:"NYY @ MIL"},
];

function am_to_dec(o) { return o < 0 ? 1 + (100/Math.abs(o)) : 1 + (o/100); }
function dec_to_am(d) { return d >= 2.0 ? `+${Math.round((d-1)*100)}` : `${Math.round(-100/(d-1))}`; }
function parlay_odds(odds_list) {
  const dec = odds_list.reduce((acc, o) => acc * am_to_dec(o), 1.0);
  return {odds: dec_to_am(dec), dec, hit_prob: null};
}

const PARLAYS_DATA = [
  {
    legs: [
      {player:"A. Judge",    prop:"H OVER 0.5",  odds:-185, model:0.88},
      {player:"F. Freeman",  prop:"H OVER 0.5",  odds:-175, model:0.87},
      {player:"K. Bradish",  prop:"K OVER 5.5",  odds:-114, model:0.75},
    ],
  },
  {
    legs: [
      {player:"Y. Alvarez",  prop:"H OVER 0.5",  odds:-196, model:0.85},
      {player:"J. Soto",     prop:"TB OVER 0.5", odds:-165, model:0.83},
      {player:"C. Early",    prop:"K OVER 4.5",  odds:+105, model:0.68},
    ],
  },
  {
    legs: [
      {player:"A. Judge",    prop:"H OVER 0.5",  odds:-185, model:0.88},
      {player:"F. Freeman",  prop:"H OVER 0.5",  odds:-175, model:0.87},
    ],
  },
].map(p => {
  const odds_list = p.legs.map(l => l.odds);
  const dec = odds_list.reduce((acc, o) => acc * am_to_dec(o), 1.0);
  const hit_prob = p.legs.reduce((acc, l) => acc * l.model, 1.0);
  const ev = hit_prob * (dec - 1) - (1 - hit_prob);
  return {...p, odds: dec_to_am(dec), dec: Math.round(dec*1000)/1000,
          hit_prob: Math.round(hit_prob*1000)/1000,
          ev: Math.round(ev*1000)/1000};
});

// ── MAIN COMPONENT ────────────────────────────────────────────
export default function MLBHub() {
  const [tab,      setTab]      = useState("plays");
  const [tracking, setTracking] = useState(TRACKING);

  const updateTrack = (id, field, val) => {
    setTracking(prev => prev.map(p =>
      p.id === id ? {...p, [field]: field==="hit" ? val : Number(val)} : p
    ));
  };

  const hits   = tracking.filter(p => p.hit === true).length;
  const misses = tracking.filter(p => p.hit === false).length;
  const pnl    = tracking.reduce((acc, p) => {
    if (p.hit === true)  return acc + (p.odds < 0 ? 100/Math.abs(p.odds)*100 : p.odds);
    if (p.hit === false) return acc - 100;
    return acc;
  }, 0);

  const T = {
    bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
    accent:"#00ff88", text:"#f0f0f0", muted:"#555",
    mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
  };

  const TABS = [
    {id:"plays",   label:"⚾ Today's Plays"},
    {id:"streaks", label:"🔥 Streaks"},
    {id:"parlays", label:"🎯 Parlays"},
    {id:"tracker", label:"📊 Live Tracker"},
  ];

  return (
    <div style={{background:T.bg, minHeight:"100vh", paddingBottom:60}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        * { box-sizing:border-box; }
        input[type=number]::-webkit-outer-spin-button,
        input[type=number]::-webkit-inner-spin-button { -webkit-appearance:none; margin:0; }
      `}</style>

      {/* Header */}
      <div style={{background:"#0a0f1a", borderBottom:`1px solid ${T.border}`,
        padding:"20px 24px 0"}}>
        <div style={{display:"flex", justifyContent:"space-between",
          alignItems:"flex-start", marginBottom:16, flexWrap:"wrap", gap:12}}>
          <div>
            <div style={{fontSize:11, color:T.muted, letterSpacing:3,
              fontFamily:T.mono, marginBottom:4}}>EDGE INDEX / MLB</div>
            <div style={{fontSize:26, fontWeight:800, color:T.text,
              fontFamily:T.head, letterSpacing:1}}>MLB PROP TRACKER</div>
            <div style={{fontSize:12, color:T.muted, fontFamily:T.mono, marginTop:2}}>
              {TODAY} · Daily plays, streaks & live results
            </div>
          </div>

          {/* Live scoreboard */}
          <div style={{display:"flex", gap:8}}>
            {[
              {label:"PLAYS",  val:tracking.length,  color:T.accent},
              {label:"HITS",   val:hits,              color:"#00ff88"},
              {label:"MISSES", val:misses,            color:"#ff4757"},
              {label:"P&L",    val:`${pnl>=0?"+":""}$${pnl.toFixed(0)}`,
               color: pnl >= 0 ? "#00ff88" : "#ff4757"},
            ].map(s => (
              <div key={s.label} style={{textAlign:"center",
                background:"#ffffff06", border:"1px solid #ffffff0a",
                borderRadius:8, padding:"10px 14px", minWidth:64}}>
                <div style={{fontSize:20, fontWeight:800, color:s.color,
                  fontFamily:T.head}}>{s.val}</div>
                <div style={{fontSize:8, color:T.muted, letterSpacing:2,
                  fontFamily:T.mono}}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div style={{display:"flex"}}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{padding:"10px 18px", background:"transparent", border:"none",
                borderBottom: tab===t.id ? `2px solid ${T.accent}` : "2px solid transparent",
                color: tab===t.id ? T.accent : T.muted,
                fontSize:12, fontWeight:600, cursor:"pointer",
                fontFamily:T.mono, transition:"all 0.15s", whiteSpace:"nowrap"}}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{padding:"20px 24px", maxWidth:1280, margin:"0 auto"}}>

        {/* PLAYS TAB */}
        {tab === "plays" && (
          <>
            <div style={{marginBottom:16, display:"flex", gap:8, alignItems:"center"}}>
              <div style={{fontSize:11, color:T.muted, fontFamily:T.mono}}>
                {PITCHER_PLAYS.filter(p=>p.tier!=="SKIP").length + BATTER_PLAYS.filter(p=>p.tier!=="SKIP").length} actionable plays today
              </div>
            </div>

            <div style={{fontSize:10, color:T.muted, letterSpacing:2,
              fontFamily:T.mono, marginBottom:8}}>⚾ PITCHER K PROPS</div>
            {PITCHER_PLAYS.map((p,i) => (
              <PlayCard key={i} play={p} type="pitcher"/>
            ))}

            <div style={{fontSize:10, color:T.muted, letterSpacing:2,
              fontFamily:T.mono, marginBottom:8, marginTop:20}}>🏃 BATTER HIT / TOTAL BASE PROPS</div>
            {BATTER_PLAYS.map((p,i) => (
              <PlayCard key={i} play={p} type="batter"/>
            ))}
          </>
        )}

        {/* STREAKS TAB */}
        {tab === "streaks" && (
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16}}>
            {/* Pitcher streaks */}
            <div style={{background:T.surface, border:`1px solid ${T.border}`,
              borderRadius:8, padding:16}}>
              <div style={{fontSize:14, fontWeight:800, color:"#00e5ff",
                fontFamily:T.head, letterSpacing:1, marginBottom:14}}>
                ⚾ PITCHER K STREAKS
              </div>
              {STREAK_DATA.pitchers.map((p,i) => (
                <div key={i} style={{display:"flex", justifyContent:"space-between",
                  alignItems:"center", marginBottom:12,
                  paddingBottom:12, borderBottom:`1px solid ${T.border}`}}>
                  <div>
                    <div style={{fontSize:13, color:T.text,
                      fontFamily:T.head, fontWeight:700}}>{p.name}</div>
                    <div style={{fontSize:9, color:T.muted, fontFamily:T.mono}}>
                      {p.team} · {p.prop}
                    </div>
                  </div>
                  {streakBar(p.streak, p.total, p.rate)}
                </div>
              ))}
            </div>

            {/* Batter streaks */}
            <div style={{background:T.surface, border:`1px solid ${T.border}`,
              borderRadius:8, padding:16}}>
              <div style={{fontSize:14, fontWeight:800, color:"#f5c518",
                fontFamily:T.head, letterSpacing:1, marginBottom:14}}>
                🏃 BATTER HIT STREAKS
              </div>
              {STREAK_DATA.batters.map((p,i) => (
                <div key={i} style={{display:"flex", justifyContent:"space-between",
                  alignItems:"center", marginBottom:12,
                  paddingBottom:12, borderBottom:`1px solid ${T.border}`}}>
                  <div>
                    <div style={{fontSize:13, color:T.text,
                      fontFamily:T.head, fontWeight:700}}>{p.name}</div>
                    <div style={{fontSize:9, color:T.muted, fontFamily:T.mono}}>
                      {p.team} · {p.prop}
                    </div>
                  </div>
                  {streakBar(p.streak, p.total, p.rate)}
                </div>
              ))}
            </div>

            {/* Alt line value section */}
            <div style={{gridColumn:"1/-1", background:T.surface,
              border:`1px solid ${T.border}`, borderRadius:8, padding:16}}>
              <div style={{fontSize:14, fontWeight:800, color:"#00ff88",
                fontFamily:T.head, letterSpacing:1, marginBottom:12}}>
                🎯 ALT LINE VALUE PLAYS
              </div>
              <div style={{display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8}}>
                {[
                  {player:"S. Strider", line:"7.5+ Ks",   note:"Below avg line — high value", color:"#00ff88"},
                  {player:"Y. Alvarez", line:"0.5+ Hits",  note:"Alt line at juice — easy cover", color:"#00ff88"},
                  {player:"G. Cole",    line:"6.5+ Ks",    note:"Step down for better odds", color:"#f5c518"},
                  {player:"J. Soto",    line:"1.0+ TB",    note:"Easier threshold vs 1.5", color:"#f5c518"},
                  {player:"Z. Wheeler", line:"5.5+ Ks",    note:"Conservative play", color:"#f5c518"},
                  {player:"F. Freeman", line:"0.5+ Hits",  note:"Near lock alt line", color:"#00ff88"},
                ].map((a,i) => (
                  <div key={i} style={{background:"#ffffff06",
                    border:`1px solid ${a.color}25`, borderRadius:6, padding:"10px 12px"}}>
                    <div style={{fontSize:12, color:a.color, fontWeight:700,
                      fontFamily:T.head}}>{a.player}</div>
                    <div style={{fontSize:11, color:"#e0e0e0", fontFamily:T.mono,
                      marginTop:2}}>{a.line}</div>
                    <div style={{fontSize:9, color:T.muted, marginTop:4}}>{a.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* PARLAYS TAB */}
        {tab === "parlays" && (
          <div>
            <div style={{marginBottom:16, padding:"12px 16px",
              background:"#ffffff06", borderRadius:8, border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:11, color:T.muted, fontFamily:T.mono,
                letterSpacing:1, marginBottom:4}}>PARLAY MATH</div>
              <div style={{fontSize:11, color:"#666", fontFamily:T.mono, lineHeight:1.6}}>
                Heavy juice plays (-175 to -220) combined into even money to +300.
                Hit prob = model probs multiplied. EV shown per $1 wagered.
              </div>
            </div>
            {PARLAYS_DATA.map((p,i) => (
              <div key={i} style={{background:"#0d1117",
                border:"1px solid #ffffff0f", borderRadius:8,
                marginBottom:8, padding:"14px 16px"}}>
                <div style={{display:"flex", justifyContent:"space-between",
                  alignItems:"center", marginBottom:12}}>
                  <div style={{fontSize:11, color:T.muted, fontFamily:T.mono}}>
                    {p.legs.length}-leg parlay
                  </div>
                  <div style={{display:"flex", gap:16}}>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontSize:20, fontWeight:800, color:"#00ff88",
                        fontFamily:"'Barlow Condensed',sans-serif"}}>{p.odds}</div>
                      <div style={{fontSize:8, color:T.muted}}>ODDS</div>
                    </div>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontSize:14, fontWeight:700, color:"#f0f0f0",
                        fontFamily:T.mono}}>{(p.hit_prob*100).toFixed(0)}%</div>
                      <div style={{fontSize:8, color:T.muted}}>HIT PROB</div>
                    </div>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontSize:14, fontWeight:700,
                        color: p.ev >= 0 ? "#00ff88" : "#ff4757",
                        fontFamily:T.mono}}>{p.ev >= 0 ? "+" : ""}{p.ev.toFixed(2)}</div>
                      <div style={{fontSize:8, color:T.muted}}>EV/unit</div>
                    </div>
                  </div>
                </div>
                {p.legs.map((leg,j) => (
                  <div key={j} style={{display:"flex", justifyContent:"space-between",
                    padding:"6px 0", borderTop:"1px solid #ffffff06"}}>
                    <div>
                      <span style={{fontSize:13, color:"#e0e0e0", fontWeight:700,
                        fontFamily:"'Barlow Condensed',sans-serif"}}>{leg.player}</span>
                      <span style={{fontSize:10, color:"#666", marginLeft:8,
                        fontFamily:T.mono}}>{leg.prop}</span>
                    </div>
                    <div style={{display:"flex", gap:12}}>
                      <span style={{fontSize:11, color:"#888",
                        fontFamily:T.mono}}>{leg.odds > 0 ? "+" : ""}{leg.odds}</span>
                      <span style={{fontSize:11, color:"#00ff88",
                        fontFamily:T.mono}}>{(leg.model*100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
                <div style={{marginTop:8, fontSize:9, color:"#444",
                  fontFamily:T.mono}}>
                  Math: {p.legs.map(l => am_to_dec(l.odds).toFixed(3)).join(" × ")} = {p.dec} → {p.odds}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TRACKER TAB */}
        {tab === "tracker" && (
          <>
            <div style={{marginBottom:12, padding:"12px 16px",
              background:"#ffffff06", borderRadius:8,
              border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:11, color:T.muted, fontFamily:T.mono,
                marginBottom:4, letterSpacing:1}}>HOW TO USE</div>
              <div style={{fontSize:11, color:"#666", fontFamily:T.mono, lineHeight:1.6}}>
                Enter actual results as they come in. Click ✓ or ✗ to mark hit/miss.
                P&L calculated at $100/play flat bet.
              </div>
            </div>

            {/* Table header */}
            <div style={{display:"grid",
              gridTemplateColumns:"1fr 120px 70px 70px 80px 90px",
              gap:8, padding:"8px 16px", marginBottom:4}}>
              {["PLAYER/PROP","ODDS","MODEL","ACTUAL","RESULT","STATUS"].map(h => (
                <div key={h} style={{fontSize:8, color:T.muted,
                  fontFamily:T.mono, letterSpacing:2}}>{h}</div>
              ))}
            </div>

            <div style={{background:T.surface, border:`1px solid ${T.border}`,
              borderRadius:8, overflow:"hidden"}}>
              {tracking.map(p => (
                <TrackerRow key={p.id} play={p} onUpdate={updateTrack}/>
              ))}
            </div>

            {/* Daily summary */}
            {(hits + misses) > 0 && (
              <div style={{marginTop:16, padding:"14px 16px",
                background: pnl >= 0 ? "#00ff8810" : "#ff475710",
                border:`1px solid ${pnl >= 0 ? "#00ff8830" : "#ff475730"}`,
                borderRadius:8}}>
                <div style={{fontSize:14, fontWeight:800,
                  color: pnl >= 0 ? "#00ff88" : "#ff4757",
                  fontFamily:T.head}}>
                  {hits}-{misses} TODAY · {hits > 0 ? ((hits/(hits+misses))*100).toFixed(0) : 0}% HIT RATE · {pnl >= 0 ? "+" : ""}${pnl.toFixed(0)} P&L
                </div>
                <div style={{fontSize:10, color:T.muted, fontFamily:T.mono, marginTop:4}}>
                  Flat $100/play · Break-even on -110: 52.4%
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
