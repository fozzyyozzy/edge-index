import { useState } from "react";

const TODAY = "2026-05-10";

const PITCHER_PLAYS = [
  {
    pitcher:"Bryce Elder", team:"ATL", opp:"LAD", home:"LAD",
    prop:"strikeouts", line:4.5, odds:-136, tier:"AUTO", model_prob:0.90,
    streak:5, l5_avg:6.4, k_pct:0.268, opp_k_pct:0.235,
    alt_lines:[3.5,4.0], hand:"R", days_rest:5,
    notes:["5-start K streak | L5 avg 6.4 Ks","ATL vs LAD — neutral park","L5: 100% | L10: 70%"],
  },
  {
    pitcher:"Noah Cameron", team:"DET", opp:"KC", home:"KC",
    prop:"strikeouts", line:4.5, odds:-144, tier:"AUTO", model_prob:0.87,
    streak:5, l5_avg:6.2, k_pct:0.252, opp_k_pct:0.228,
    alt_lines:[3.5,4.0], hand:"R", days_rest:5,
    notes:["5-start K streak | L5 avg 6.2 Ks","DET vs KC — neutral park","L5: 100% | L10: 60%"],
  },
  {
    pitcher:"Logan Henderson", team:"MIL", opp:"NYY", home:"MIL",
    prop:"strikeouts", line:5.5, odds:-156, tier:"T2", model_prob:0.57,
    streak:0, l5_avg:6.6, k_pct:0.265, opp_k_pct:0.228,
    alt_lines:[4.5,5.0], hand:"R", days_rest:5,
    notes:["L5 avg 6.6 Ks but 0-start streak","MIL hitter-friendly park","L5: 80% | L10: 57%"],
  },
];

const BATTER_PLAYS = [
  {
    batter:"Colson Montgomery", team:"CWS", opp:"SEA", home:"CWS",
    prop:"hits", line:0.5, odds:-155, tier:"AUTO", model_prob:0.95,
    hit_streak:10, platoon_avg:0.268, batter_avg:0.268, pitcher_hand:"R",
    alt_lines:[0.5], notes:["10-game hit streak","L5: 100% | L10: 100%","CWS vs SEA"],
  },
  {
    batter:"Ernie Clement", team:"TOR", opp:"LAA", home:"TOR",
    prop:"hits", line:0.5, odds:-187, tier:"AUTO", model_prob:0.94,
    hit_streak:13, platoon_avg:0.275, batter_avg:0.275, pitcher_hand:"R",
    alt_lines:[0.5], notes:["13-game hit streak — longest active","L5: 100% | L10: 100%","TOR vs LAA"],
  },
  {
    batter:"Nico Hoerner", team:"CHC", opp:"TEX", home:"TEX",
    prop:"hits", line:0.5, odds:-235, tier:"AUTO", model_prob:0.93,
    hit_streak:9, platoon_avg:0.298, batter_avg:0.298, pitcher_hand:"R",
    alt_lines:[0.5], notes:["9-game hit streak","L5: 100% | L10: 90%","CHC vs TEX"],
  },
  {
    batter:"Brendan Donovan", team:"STL", opp:"SD", home:"SD",
    prop:"hits", line:0.5, odds:-250, tier:"AUTO", model_prob:0.93,
    hit_streak:8, platoon_avg:0.285, batter_avg:0.285, pitcher_hand:"R",
    alt_lines:[0.5], notes:["8-game hit streak","L5: 100% | L10: 90%","STL vs SD"],
  },
  {
    batter:"Miguel Vargas", team:"LAD", opp:"ATL", home:"ATL",
    prop:"hits", line:0.5, odds:-195, tier:"AUTO", model_prob:0.93,
    hit_streak:9, platoon_avg:0.272, batter_avg:0.272, pitcher_hand:"R",
    alt_lines:[0.5], notes:["9-game hit streak","L5: 100% | L10: 90%","LAD vs ATL"],
  },
  {
    batter:"Jonathan Aranda", team:"TB", opp:"BOS", home:"BOS",
    prop:"hits", line:0.5, odds:-200, tier:"AUTO", model_prob:0.92,
    hit_streak:7, platoon_avg:0.288, batter_avg:0.288, pitcher_hand:"R",
    alt_lines:[0.5], notes:["7-game hit streak","L5: 100% | L10: 80%","TB vs BOS"],
  },
  {
    batter:"Xander Bogaerts", team:"SD", opp:"STL", home:"SD",
    prop:"hits", line:0.5, odds:-218, tier:"AUTO", model_prob:0.91,
    hit_streak:7, platoon_avg:0.288, batter_avg:0.288, pitcher_hand:"R",
    alt_lines:[0.5], notes:["7-game hit streak","L5: 100% | L10: 90%","SD vs STL"],
  },
  {
    batter:"Rafael Devers", team:"BOS", opp:"TB", home:"BOS",
    prop:"hits", line:0.5, odds:-162, tier:"AUTO", model_prob:0.88,
    hit_streak:8, platoon_avg:0.295, batter_avg:0.295, pitcher_hand:"R",
    alt_lines:[0.5], notes:["8-game hit streak","L5: 100% | L10: 80%","BOS vs TB"],
  },
  {
    batter:"Addison Barger", team:"TOR", opp:"LAA", home:"TOR",
    prop:"hits", line:0.5, odds:-188, tier:"AUTO", model_prob:0.88,
    hit_streak:5, platoon_avg:0.295, batter_avg:0.295, pitcher_hand:"R",
    alt_lines:[0.5], notes:["5-game hit streak","L5: 100% | L10: 90%","TOR vs LAA"],
  },
  {
    batter:"Addison Barger", team:"TOR", opp:"LAA", home:"TOR",
    prop:"total_bases", line:1.5, odds:144, tier:"AUTO", model_prob:0.83,
    hit_streak:5, platoon_avg:0.295, batter_avg:0.295, pitcher_hand:"R",
    alt_lines:[0.5,1.0], notes:["FREE PICK — +144 plus money","Model: 83% | Market: 41% | Edge: +41.6%","3rd straight day with massive value"],
  },
  {
    batter:"Aaron Judge", team:"NYY", opp:"MIL", home:"MIL",
    prop:"hits", line:0.5, odds:-212, tier:"T1", model_prob:0.77,
    hit_streak:4, platoon_avg:0.312, batter_avg:0.312, pitcher_hand:"R",
    alt_lines:[0.5], notes:["4-game hit streak","L5: 80% | L10: 90%","NOTE: Judge walks a lot — avoid TB props"],
  },
  {
    batter:"Aaron Judge", team:"NYY", opp:"MIL", home:"MIL",
    prop:"total_bases", line:1.5, odds:105, tier:"T1", model_prob:0.72,
    hit_streak:4, platoon_avg:0.312, batter_avg:0.312, pitcher_hand:"R",
    alt_lines:[0.5,1.0], notes:["Plus money TB +105","⚠️ Walk risk — Judge drew 3 walks yesterday","Use as parlay leg only if confident no walk game"],
  },
];

function amToDec(o) { return o < 0 ? 1+(100/Math.abs(o)) : 1+(o/100); }
function decToAm(d) { return d >= 2.0 ? `+${Math.round((d-1)*100)}` : `${Math.round(-100/(d-1))}`; }

const PARLAYS_DATA = [
  {
    label:"Best EV — 3-leg",
    legs:[
      {player:"C. Montgomery", prop:"H OVER 0.5", odds:-155, model:0.95},
      {player:"E. Clement",    prop:"H OVER 0.5", odds:-187, model:0.94},
      {player:"M. Vargas",     prop:"H OVER 0.5", odds:-195, model:0.93},
    ],
  },
  {
    label:"Hits +300 — 3-leg",
    legs:[
      {player:"C. Montgomery", prop:"H OVER 0.5", odds:-155, model:0.95},
      {player:"B. Donovan",    prop:"H OVER 0.5", odds:-250, model:0.93},
      {player:"B. Elder",      prop:"K OVER 4.5", odds:-136, model:0.90},
    ],
  },
  {
    label:"Strong Value — 3-leg",
    legs:[
      {player:"C. Montgomery", prop:"H OVER 0.5", odds:-155, model:0.95},
      {player:"E. Clement",    prop:"H OVER 0.5", odds:-187, model:0.94},
      {player:"J. Aranda",     prop:"H OVER 0.5", odds:-200, model:0.92},
    ],
  },
  {
    label:"K + Hits — 3-leg",
    legs:[
      {player:"E. Clement",  prop:"H OVER 0.5", odds:-187, model:0.94},
      {player:"J. Aranda",   prop:"H OVER 0.5", odds:-200, model:0.92},
      {player:"B. Elder",    prop:"K OVER 4.5", odds:-136, model:0.90},
    ],
  },
  {
    label:"Plus Money Mix — 2-leg",
    legs:[
      {player:"J. Aranda",  prop:"H OVER 0.5",  odds:-200, model:0.92},
      {player:"A. Barger",  prop:"TB OVER 1.5", odds:144,  model:0.83},
    ],
  },
].map(p => {
  const dec      = p.legs.reduce((acc,l) => acc * amToDec(l.odds), 1.0);
  const hit_prob = p.legs.reduce((acc,l) => acc * l.model, 1.0);
  const ev       = hit_prob * (dec-1) - (1-hit_prob);
  return {...p, odds:decToAm(dec), dec:Math.round(dec*1000)/1000,
          hit_prob:Math.round(hit_prob*1000)/1000,
          ev:Math.round(ev*1000)/1000};
});

const STREAK_DATA = {
  pitchers:[
    {name:"B. Elder",     team:"ATL", prop:"4.5+ Ks", streak:5, total:31, rate:0.77},
    {name:"N. Cameron",   team:"DET", prop:"4.5+ Ks", streak:5, total:26, rate:0.73},
    {name:"G. Williams",  team:"PIT", prop:"3.5+ Ks", streak:4, total:36, rate:0.75},
    {name:"J. deGrom",    team:"TEX", prop:"3.5+ Ks", streak:2, total:33, rate:0.79},
    {name:"L. Henderson", team:"MIL", prop:"5.5+ Ks", streak:0, total:7,  rate:0.80},
  ],
  batters:[
    {name:"E. Clement",   team:"TOR", prop:"1+ Hits", streak:13, total:60, rate:0.68},
    {name:"C. Montgomery",team:"CWS", prop:"1+ Hits", streak:10, total:60, rate:0.68},
    {name:"N. Hoerner",   team:"CHC", prop:"1+ Hits", streak:9,  total:60, rate:0.75},
    {name:"M. Vargas",    team:"LAD", prop:"1+ Hits", streak:9,  total:60, rate:0.58},
    {name:"R. Devers",    team:"BOS", prop:"1+ Hits", streak:8,  total:60, rate:0.67},
    {name:"K. Marte",     team:"ARI", prop:"1+ Hits", streak:8,  total:60, rate:0.68},
    {name:"B. Donovan",   team:"STL", prop:"1+ Hits", streak:8,  total:60, rate:0.67},
    {name:"G. Urshela",   team:"OAK", prop:"1+ Hits", streak:8,  total:60, rate:0.60},
    {name:"J. Aranda",    team:"TB",  prop:"1+ Hits", streak:7,  total:60, rate:0.75},
    {name:"X. Bogaerts",  team:"SD",  prop:"1+ Hits", streak:7,  total:60, rate:0.75},
    {name:"B. Bichette",  team:"TOR", prop:"1+ Hits", streak:5,  total:60, rate:0.88},
    {name:"A. Barger",    team:"TOR", prop:"1.5+ TB",  streak:5,  total:60, rate:0.70},
  ],
};

// ── FADE PLAYS (cold bats from slump list) ───────────────────
const FADE_PLAYS = [
  {batter:"Addison Barger",  team:"TOR", opp:"LAA", l14_avg:".045", l14:"1-for-22",  reason:"Season slump — 1 hit in 22 AB"},
  {batter:"Ketel Marte",     team:"ARI", opp:"NYM", l14_avg:".140", l14:"6-for-43",  reason:"Cold L14 — below .150 threshold"},
  {batter:"Corey Seager",    team:"TEX", opp:"CHC", l14_avg:".128", l14:"6-for-47",  reason:"Ice cold — .128 L14"},
  {batter:"Matt Chapman",    team:"SF",  opp:"PIT", l14_avg:".077", l14:"3-for-39",  reason:"Extreme slump — .077 L14"},
  {batter:"Cal Raleigh",     team:"SEA", opp:"CWS", l14_avg:".054", l14:"2-for-37",  reason:"Near hitless — .054 L14"},
  {batter:"Royce Lewis",     team:"MIN", opp:"CLE", l14_avg:".094", l14:"3-for-32",  reason:"Deep slump — .094 L14"},
  {batter:"Evan Carter",     team:"TEX", opp:"CHC", l14_avg:".086", l14:"3-for-35",  reason:"Cold bat — .086 L14"},
  {batter:"Taylor Ward",     team:"LAA", opp:"TOR", l14_avg:".091", l14:"3-for-33",  reason:"Struggling — .091 L14"},
];

const TRACKING_INIT = [
  {id:1,  player:"Bryce Elder",      prop:"K OVER 4.5",  odds:-136, model:0.90, tier:"AUTO", actual:null, hit:null},
  {id:2,  player:"Noah Cameron",     prop:"K OVER 4.5",  odds:-144, model:0.87, tier:"AUTO", actual:null, hit:null},
  {id:3,  player:"Colson Montgomery",prop:"H OVER 0.5",  odds:-155, model:0.95, tier:"AUTO", actual:null, hit:null},
  {id:4,  player:"Ernie Clement",    prop:"H OVER 0.5",  odds:-187, model:0.94, tier:"AUTO", actual:null, hit:null},
  {id:5,  player:"Miguel Vargas",    prop:"H OVER 0.5",  odds:-195, model:0.93, tier:"AUTO", actual:null, hit:null},
  {id:6,  player:"Brendan Donovan",  prop:"H OVER 0.5",  odds:-250, model:0.93, tier:"AUTO", actual:null, hit:null},
  {id:7,  player:"Jonathan Aranda",  prop:"H OVER 0.5",  odds:-200, model:0.92, tier:"AUTO", actual:null, hit:null},
  {id:8,  player:"Xander Bogaerts",  prop:"H OVER 0.5",  odds:-218, model:0.91, tier:"AUTO", actual:null, hit:null},
  {id:9,  player:"Rafael Devers",    prop:"H OVER 0.5",  odds:-162, model:0.88, tier:"AUTO", actual:null, hit:null},
  {id:10, player:"Addison Barger",   prop:"TB OVER 1.5", odds:144,  model:0.83, tier:"AUTO", actual:null, hit:null},
];

const TIER_CFG = {
  AUTO:{color:"#00ff88",bg:"#00ff8818",border:"#00ff8840",icon:"⚡"},
  T1:  {color:"#f5c518",bg:"#f5c51818",border:"#f5c51840",icon:"★"},
  T2:  {color:"#00e5ff",bg:"#00e5ff18",border:"#00e5ff40",icon:"◆"},
};

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

function tierBadge(tier) {
  const c = TIER_CFG[tier]||TIER_CFG.T2;
  return (
    <span style={{fontSize:9,fontWeight:700,fontFamily:T.mono,
      color:c.color,background:c.bg,border:`1px solid ${c.border}`,
      padding:"2px 7px",borderRadius:3,letterSpacing:1}}>
      {c.icon} {tier}
    </span>
  );
}

function streakBar(streak, total, rate) {
  const color = rate>=0.85?"#00ff88":rate>=0.70?"#f5c518":"#ffa502";
  const emoji = streak>=10?"🔥":streak>=7?"⚡":streak>=5?"✅":"📈";
  return (
    <div style={{display:"flex",alignItems:"center",gap:8}}>
      <span style={{fontSize:14}}>{emoji}</span>
      <div>
        <div style={{fontSize:12,fontWeight:700,color,
          fontFamily:T.mono}}>{streak}g</div>
        <div style={{width:60,height:3,background:"#ffffff12",
          borderRadius:2,marginTop:2}}>
          <div style={{width:`${Math.min(rate*100,100)}%`,height:"100%",
            background:color,borderRadius:2}}/>
        </div>
      </div>
      <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>
        L60:{(rate*100).toFixed(0)}%
      </span>
    </div>
  );
}

function PlayCard({play, type}) {
  const [open, setOpen] = useState(false);
  const cfg = TIER_CFG[play.tier]||TIER_CFG.T2;
  const oddsStr = play.odds > 0 ? `+${play.odds}` : `${play.odds}`;
  return (
    <div onClick={() => setOpen(!open)} style={{
      background:T.surface,
      border:`1px solid ${open?cfg.color+"50":T.border}`,
      borderRadius:8,marginBottom:8,overflow:"hidden",
      cursor:"pointer",transition:"all 0.2s"}}>
      <div style={{padding:"12px 16px",display:"flex",
        alignItems:"center",gap:12}}>
        <div style={{flexShrink:0}}>{tierBadge(play.tier)}</div>
        <div style={{flex:1,minWidth:0}}>
          <div style={{display:"flex",alignItems:"center",
            gap:8,flexWrap:"wrap"}}>
            <span style={{fontSize:14,fontWeight:700,color:T.text,
              fontFamily:T.head}}>
              {type==="pitcher"?play.pitcher:play.batter}
            </span>
            <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>
              {play.team} vs {play.opp}
            </span>
          </div>
          <div style={{fontSize:11,color:"#777",
            fontFamily:T.mono,marginTop:2}}>
            {play.prop.toUpperCase()} OVER {play.line}
            {type==="pitcher"&&` · ${play.hand}HP · ${play.days_rest}d rest`}
          </div>
        </div>
        <div style={{display:"flex",gap:14,alignItems:"center",flexShrink:0}}>
          {type==="pitcher"&&(
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:13,fontWeight:700,color:T.text,
                fontFamily:T.mono}}>{play.l5_avg}</div>
              <div style={{fontSize:8,color:"#444"}}>L5 AVG Ks</div>
            </div>
          )}
          {type==="batter"&&(
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:13,fontWeight:700,color:T.text,
                fontFamily:T.mono}}>{play.hit_streak}g</div>
              <div style={{fontSize:8,color:"#444"}}>STREAK</div>
            </div>
          )}
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:18,fontWeight:800,color:cfg.color,
              fontFamily:T.head}}>{(play.model_prob*100).toFixed(0)}%</div>
            <div style={{fontSize:8,color:"#444"}}>MODEL</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:13,fontWeight:700,color:"#888",
              fontFamily:T.mono}}>{oddsStr}</div>
            <div style={{fontSize:8,color:"#444"}}>ODDS</div>
          </div>
          <span style={{fontSize:14,color:open?cfg.color:"#333",
            transition:"transform 0.2s",
            transform:open?"rotate(180deg)":"none"}}>▾</span>
        </div>
      </div>
      {open&&(
        <div style={{borderTop:"1px solid #ffffff08",padding:"14px 16px"}}>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
            <div>
              <div style={{fontSize:9,color:"#444",letterSpacing:2,
                fontFamily:T.mono,marginBottom:8}}>ANALYSIS</div>
              {play.notes.map((n,i)=>(
                <div key={i} style={{fontSize:10,color:"#666",marginBottom:5,
                  paddingLeft:8,borderLeft:`2px solid ${cfg.color}40`}}>{n}</div>
              ))}
            </div>
            <div>
              <div style={{fontSize:9,color:"#444",letterSpacing:2,
                fontFamily:T.mono,marginBottom:8}}>ALT LINES</div>
              <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                {play.alt_lines.map(l=>(
                  <div key={l} style={{background:"#ffffff06",
                    border:"1px solid #ffffff0f",borderRadius:4,
                    padding:"4px 10px",fontSize:11,color:"#aaa",
                    fontFamily:T.mono}}>{l}+ OVER</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TrackerRow({play, onUpdate}) {
  const hitColor = play.hit===true?"#00ff88"
    :play.hit===false?"#ff4757"
    :play.hit==="void"?"#888":"#444";
  const hitLabel = play.hit===true?"✓ HIT"
    :play.hit===false?"✗ MISS"
    :play.hit==="void"?"— VOID":"PENDING";
  const oddsStr = play.odds>0?`+${play.odds}`:`${play.odds}`;
  return (
    <div style={{display:"grid",
      gridTemplateColumns:"1fr 70px 60px 60px 90px 80px",
      gap:8,alignItems:"center",padding:"10px 16px",
      borderBottom:"1px solid #ffffff06"}}>
      <div>
        <div style={{color:T.text,fontWeight:600,
          fontFamily:T.head,fontSize:13}}>{play.player}</div>
        <div style={{color:"#555",fontFamily:T.mono,fontSize:9}}>
          {play.prop}
        </div>
      </div>
      <div style={{color:"#888",fontFamily:T.mono,fontSize:11}}>
        {oddsStr}
      </div>
      <div style={{color:"#00e5ff",fontFamily:T.mono,fontSize:11}}>
        {(play.model*100).toFixed(0)}%
      </div>
      <input type="number" placeholder="—" value={play.actual??''}
        onClick={e=>e.stopPropagation()}
        onChange={e=>onUpdate(play.id,"actual",e.target.value)}
        style={{background:"#ffffff08",border:"1px solid #ffffff15",
          borderRadius:4,color:T.text,padding:"4px 6px",fontSize:11,
          width:"100%",fontFamily:T.mono,outline:"none"}}/>
      <div style={{display:"flex",gap:3}}>
        {["✓","✗","V"].map((btn,i)=>{
          const val = i===0?true:i===1?false:"void";
          const active = play.hit===val;
          const bg = active?(i===0?"#00ff88":i===1?"#ff4757":"#666"):"#ffffff10";
          const color = active?(i<2?"#000":"#fff"):"#555";
          return (
            <button key={btn}
              onClick={e=>{e.stopPropagation();onUpdate(play.id,"hit",val)}}
              style={{flex:1,padding:"4px 2px",borderRadius:3,border:"none",
                background:bg,color,cursor:"pointer",
                fontSize:10,fontWeight:700}}>{btn}</button>
          );
        })}
      </div>
      <div style={{color:hitColor,fontFamily:T.mono,
        fontSize:10,fontWeight:700}}>{hitLabel}</div>
    </div>
  );
}

export default function MLBHub() {
  const [tab,      setTab]      = useState("plays");
  const [tracking, setTracking] = useState(TRACKING_INIT);

  const updateTrack = (id,field,val) => {
    setTracking(prev=>prev.map(p=>
      p.id===id?{...p,[field]:field==="hit"?val:Number(val)}:p
    ));
  };

  const settled = tracking.filter(p=>p.hit!==null&&p.hit!=="void");
  const hits    = tracking.filter(p=>p.hit===true).length;
  const misses  = tracking.filter(p=>p.hit===false).length;
  const voids   = tracking.filter(p=>p.hit==="void").length;
  const pnl     = tracking.reduce((acc,p)=>{
    if(p.hit===true) return acc+(p.odds<0?100*(100/Math.abs(p.odds)):100*(p.odds/100));
    if(p.hit===false) return acc-100;
    return acc;
  },0);

  const TABS = [
    {id:"plays",   label:"⚾ Today's Plays"},
    {id:"streaks", label:"🔥 Streaks"},
    {id:"parlays", label:"🎯 Parlays"},
    {id:"fades",   label:"📉 Fade Plays"},
    {id:"tracker", label:"📊 Live Tracker"},
  ];

  return (
    <div style={{background:T.bg,minHeight:"100vh",paddingBottom:60}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        *{box-sizing:border-box;}
        input[type=number]::-webkit-outer-spin-button,
        input[type=number]::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
      `}</style>

      <div style={{background:"#0a0f1a",
        borderBottom:`1px solid ${T.border}`,padding:"20px 24px 0"}}>
        <div style={{maxWidth:1280,margin:"0 auto"}}>
          <div style={{display:"flex",justifyContent:"space-between",
            alignItems:"flex-start",marginBottom:16,flexWrap:"wrap",gap:12}}>
            <div>
              <div style={{fontSize:11,color:T.muted,letterSpacing:3,
                fontFamily:T.mono,marginBottom:4}}>EDGE INDEX / MLB</div>
              <div style={{fontSize:26,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1}}>MLB PROP TRACKER</div>
              <div style={{fontSize:12,color:T.muted,
                fontFamily:T.mono,marginTop:2}}>
                {TODAY} · 15 games · Real DK/FD/BetMGM lines
              </div>
            </div>
            <div style={{display:"flex",gap:8}}>
              {[
                {label:"PLAYS",  val:tracking.length,       color:T.accent},
                {label:"HITS",   val:hits,                  color:"#00ff88"},
                {label:"MISSES", val:misses,                color:"#ff4757"},
                {label:"VOIDS",  val:voids,                 color:"#888"},
                {label:"P&L",
                 val:`${pnl>=0?"+":""}$${pnl.toFixed(0)}`,
                 color:pnl>=0?"#00ff88":"#ff4757"},
              ].map(s=>(
                <div key={s.label} style={{textAlign:"center",
                  background:"#ffffff06",border:"1px solid #ffffff0a",
                  borderRadius:8,padding:"10px 12px",minWidth:56}}>
                  <div style={{fontSize:18,fontWeight:800,color:s.color,
                    fontFamily:T.head}}>{s.val}</div>
                  <div style={{fontSize:7,color:T.muted,letterSpacing:2,
                    fontFamily:T.mono}}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
          <div style={{display:"flex"}}>
            {TABS.map(t=>(
              <button key={t.id} onClick={()=>setTab(t.id)}
                style={{padding:"10px 18px",background:"transparent",
                  border:"none",
                  borderBottom:tab===t.id
                    ?`2px solid ${T.accent}`:"2px solid transparent",
                  color:tab===t.id?T.accent:T.muted,
                  fontSize:12,fontWeight:600,cursor:"pointer",
                  fontFamily:T.mono,transition:"all 0.15s",
                  whiteSpace:"nowrap"}}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{padding:"20px 24px",maxWidth:1280,margin:"0 auto"}}>

        {tab==="plays"&&(
          <>
            <div style={{marginBottom:16,padding:"12px 16px",
              background:"#00ff8810",border:"1px solid #00ff8830",
              borderRadius:8}}>
              <div style={{fontSize:11,color:"#00ff88",fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>🎁 FREE PICK TODAY — May 10</div>
              <div style={{fontSize:13,color:T.text,fontFamily:T.head,
                fontWeight:700}}>
                Aaron Judge · TB OVER 1.5 · +105
              </div>
              <div style={{fontSize:10,color:"#888",fontFamily:T.mono,
                marginTop:4}}>
                Model: 72% | Market: 49% | Edge: +23% — plus money value
                · Note: walk risk, use as parlay leg
              </div>
            </div>
            <div style={{fontSize:10,color:T.muted,letterSpacing:2,
              fontFamily:T.mono,marginBottom:8}}>⚾ PITCHER K PROPS</div>
            {PITCHER_PLAYS.map((p,i)=>(
              <PlayCard key={i} play={p} type="pitcher"/>
            ))}
            <div style={{fontSize:10,color:T.muted,letterSpacing:2,
              fontFamily:T.mono,marginBottom:8,marginTop:20}}>
              🏃 BATTER HIT / TOTAL BASE PROPS
            </div>
            {BATTER_PLAYS.map((p,i)=>(
              <PlayCard key={i} play={p} type="batter"/>
            ))}
          </>
        )}

        {tab==="streaks"&&(
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
              <div style={{fontSize:14,fontWeight:800,color:"#00e5ff",
                fontFamily:T.head,letterSpacing:1,marginBottom:14}}>
                ⚾ PITCHER K STREAKS
              </div>
              {STREAK_DATA.pitchers.map((p,i)=>(
                <div key={i} style={{display:"flex",
                  justifyContent:"space-between",alignItems:"center",
                  marginBottom:12,paddingBottom:12,
                  borderBottom:`1px solid ${T.border}`}}>
                  <div>
                    <div style={{fontSize:13,color:T.text,
                      fontFamily:T.head,fontWeight:700}}>{p.name}</div>
                    <div style={{fontSize:9,color:T.muted,
                      fontFamily:T.mono}}>{p.team} · {p.prop}</div>
                  </div>
                  {streakBar(p.streak,p.total,p.rate)}
                </div>
              ))}
            </div>
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
              <div style={{fontSize:14,fontWeight:800,color:"#f5c518",
                fontFamily:T.head,letterSpacing:1,marginBottom:14}}>
                🏃 BATTER HIT STREAKS
              </div>
              {STREAK_DATA.batters.map((p,i)=>(
                <div key={i} style={{display:"flex",
                  justifyContent:"space-between",alignItems:"center",
                  marginBottom:10,paddingBottom:10,
                  borderBottom:`1px solid ${T.border}`}}>
                  <div>
                    <div style={{fontSize:13,color:T.text,
                      fontFamily:T.head,fontWeight:700}}>{p.name}</div>
                    <div style={{fontSize:9,color:T.muted,
                      fontFamily:T.mono}}>{p.team} · {p.prop}</div>
                  </div>
                  {streakBar(p.streak,p.total,p.rate)}
                </div>
              ))}
            </div>
            <div style={{gridColumn:"1/-1",background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
              <div style={{fontSize:14,fontWeight:800,color:"#00ff88",
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                🎯 ALT LINE VALUE TODAY
              </div>
              <div style={{display:"grid",
                gridTemplateColumns:"repeat(3,1fr)",gap:8}}>
                {[
                  {player:"A. Barger",    line:"TB 1.5+",  note:"+144 plus money, 41% edge", color:"#00ff88"},
                  {player:"B. Elder",     line:"K 4.5+",   note:"-136 AUTO pitcher, 5-start streak", color:"#00ff88"},
                  {player:"N. Cameron",   line:"K 4.5+",   note:"-144 AUTO pitcher, 5-start streak", color:"#00ff88"},
                  {player:"R. Devers",    line:"H 0.5+",   note:"-162 best juice value, 26% edge", color:"#f5c518"},
                  {player:"C. Montgomery",line:"H 0.5+",   note:"-155 lowest juice on the board", color:"#f5c518"},
                  {player:"A. Judge",     line:"TB 1.5+",  note:"+105 but walk risk — use carefully", color:"#888"},
                ].map((a,i)=>(
                  <div key={i} style={{background:"#ffffff06",
                    border:`1px solid ${a.color}25`,
                    borderRadius:6,padding:"10px 12px"}}>
                    <div style={{fontSize:13,color:a.color,fontWeight:700,
                      fontFamily:T.head}}>{a.player}</div>
                    <div style={{fontSize:11,color:T.text,
                      fontFamily:T.mono,marginTop:2}}>{a.line}</div>
                    <div style={{fontSize:9,color:T.muted,
                      marginTop:4}}>{a.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab==="parlays"&&(
          <div>
            <div style={{marginBottom:16,padding:"12px 16px",
              background:"#ffffff06",borderRadius:8,
              border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:11,color:T.muted,fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>TODAY'S PARLAY MO</div>
              <div style={{fontSize:11,color:"#666",fontFamily:T.mono,
                lineHeight:1.6}}>
                Parlay #2 hits exactly +300. All 5 parlays positive EV.
                Best single edge: Barger TB +144 at 41% over market.
              </div>
            </div>
            {PARLAYS_DATA.map((p,i)=>(
              <div key={i} style={{background:T.surface,
                border:"1px solid #ffffff0f",borderRadius:8,
                marginBottom:8,padding:"14px 16px"}}>
                <div style={{display:"flex",justifyContent:"space-between",
                  alignItems:"center",marginBottom:12}}>
                  <div style={{fontSize:11,color:T.muted,fontFamily:T.mono}}>
                    #{i+1} · {p.label}
                  </div>
                  <div style={{display:"flex",gap:16}}>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontSize:20,fontWeight:800,
                        color:"#00ff88",fontFamily:T.head}}>{p.odds}</div>
                      <div style={{fontSize:8,color:T.muted}}>ODDS</div>
                    </div>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontSize:14,fontWeight:700,color:T.text,
                        fontFamily:T.mono}}>
                        {(p.hit_prob*100).toFixed(0)}%
                      </div>
                      <div style={{fontSize:8,color:T.muted}}>HIT PROB</div>
                    </div>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontSize:14,fontWeight:700,
                        color:p.ev>=0?"#00ff88":"#ff4757",
                        fontFamily:T.mono}}>+{p.ev.toFixed(2)}</div>
                      <div style={{fontSize:8,color:T.muted}}>EV/unit</div>
                    </div>
                  </div>
                </div>
                {p.legs.map((leg,j)=>(
                  <div key={j} style={{display:"flex",
                    justifyContent:"space-between",padding:"6px 0",
                    borderTop:"1px solid #ffffff06"}}>
                    <div>
                      <span style={{fontSize:13,color:T.text,fontWeight:700,
                        fontFamily:T.head}}>{leg.player}</span>
                      <span style={{fontSize:10,color:"#666",marginLeft:8,
                        fontFamily:T.mono}}>{leg.prop}</span>
                    </div>
                    <div style={{display:"flex",gap:12}}>
                      <span style={{fontSize:11,color:"#888",fontFamily:T.mono}}>
                        {leg.odds>0?"+":""}{leg.odds}
                      </span>
                      <span style={{fontSize:11,color:"#00ff88",
                        fontFamily:T.mono}}>
                        {(leg.model*100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
                <div style={{marginTop:8,fontSize:9,color:"#444",
                  fontFamily:T.mono}}>
                  {p.legs.map(l=>amToDec(l.odds).toFixed(3)).join(" × ")} = {p.dec} → {p.odds}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab==="fades"&&(
          <div>
            <div style={{marginBottom:16,padding:"12px 16px",
              background:"#ff475710",border:"1px solid #ff475730",
              borderRadius:8}}>
              <div style={{fontSize:11,color:"#ff4757",fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>📉 FADE PLAYS — COLD BATS</div>
              <div style={{fontSize:11,color:"#888",fontFamily:T.mono,
                lineHeight:1.6}}>
                These players are excluded from OVER plays due to cold L14 form.
                Consider betting the UNDER on their hit props, or combining
                cold bats into UNDER parlays targeting even money to +200.
              </div>
            </div>

            {/* Fade parlay suggestion */}
            <div style={{marginBottom:16,padding:"14px 16px",
              background:"#ffffff06",border:"1px solid #ffffff0a",
              borderRadius:8}}>
              <div style={{fontSize:11,color:"#f5c518",fontFamily:T.mono,
                letterSpacing:1,marginBottom:8}}>🎯 SUGGESTED UNDER PARLAY</div>
              <div style={{fontSize:13,color:T.text,fontFamily:T.head,
                fontWeight:700,marginBottom:4}}>
                Chapman + Cal Raleigh + Royce Lewis UNDER 0.5 Hits
              </div>
              <div style={{fontSize:10,color:"#888",fontFamily:T.mono}}>
                Three extreme cold bats combined → targets +150 to +200
                Same logic as OVER parlays but fading slumps
              </div>
            </div>

            {/* Fade plays list */}
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,
              overflow:"hidden"}}>
              <div style={{display:"grid",
                gridTemplateColumns:"1fr 80px 80px 1fr",
                gap:8,padding:"8px 16px",
                borderBottom:`1px solid ${T.border}`}}>
                {["PLAYER","L14 AVG","L14 AB","REASON"].map(h=>(
                  <div key={h} style={{fontSize:8,color:T.muted,
                    fontFamily:T.mono,letterSpacing:2}}>{h}</div>
                ))}
              </div>
              {FADE_PLAYS.map((p,i)=>{
                const avgNum = parseFloat(p.l14_avg.replace('.','0.'));
                const color = avgNum < 0.080 ? "#ff4757"
                  : avgNum < 0.120 ? "#ff6b35" : "#ffa502";
                return (
                  <div key={i} style={{display:"grid",
                    gridTemplateColumns:"1fr 80px 80px 1fr",
                    gap:8,padding:"10px 16px",
                    borderBottom:i<FADE_PLAYS.length-1
                      ?`1px solid ${T.border}`:"none",
                    background:i%2===0?"transparent":"#ffffff02"}}>
                    <div>
                      <div style={{fontSize:13,color:T.text,
                        fontWeight:700,fontFamily:T.head}}>
                        {p.batter}
                      </div>
                      <div style={{fontSize:9,color:T.muted,
                        fontFamily:T.mono}}>{p.team} vs {p.opp}</div>
                    </div>
                    <div style={{fontSize:14,fontWeight:800,
                      color,fontFamily:T.head,alignSelf:"center"}}>
                      {p.l14_avg}
                    </div>
                    <div style={{fontSize:12,color:"#888",
                      fontFamily:T.mono,alignSelf:"center"}}>
                      {p.l14}
                    </div>
                    <div style={{fontSize:10,color:"#666",
                      fontFamily:T.mono,alignSelf:"center"}}>
                      {p.reason}
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{marginTop:12,padding:"10px 16px",
              background:"#ffffff06",borderRadius:8,
              border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:10,color:T.muted,fontFamily:T.mono,
                lineHeight:1.6}}>
                <strong style={{color:"#f5c518"}}>How to use fade plays:</strong>
                {" "}Books post H UNDER 0.5 at roughly -115 to -135 for most players.
                Cold bats hitting .077-.140 give you real edge on the under.
                Combine 2-3 cold bats into a parlay targeting +150 to +250.
                Same math as OVER parlays — just the other direction.
              </div>
            </div>
          </div>
        )}

        {tab==="tracker"&&(
          <>
            <div style={{marginBottom:12,padding:"12px 16px",
              background:"#ffffff06",borderRadius:8,
              border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:11,color:T.muted,fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>HOW TO USE</div>
              <div style={{fontSize:11,color:"#666",fontFamily:T.mono,
                lineHeight:1.6}}>
                ✓ = Hit · ✗ = Miss · V = Void/Postponed · Enter actual result.
                P&L at $100/play flat bet.
              </div>
            </div>
            <div style={{display:"grid",
              gridTemplateColumns:"1fr 70px 60px 60px 90px 80px",
              gap:8,padding:"8px 16px",marginBottom:4}}>
              {["PLAYER/PROP","ODDS","MODEL","ACTUAL","RESULT","STATUS"].map(h=>(
                <div key={h} style={{fontSize:8,color:T.muted,
                  fontFamily:T.mono,letterSpacing:2}}>{h}</div>
              ))}
            </div>
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,overflow:"hidden"}}>
              {tracking.map(p=>(
                <TrackerRow key={p.id} play={p} onUpdate={updateTrack}/>
              ))}
            </div>
            {settled.length>0&&(
              <div style={{marginTop:16,padding:"14px 16px",
                background:pnl>=0?"#00ff8810":"#ff475710",
                border:`1px solid ${pnl>=0?"#00ff8830":"#ff475730"}`,
                borderRadius:8}}>
                <div style={{display:"flex",justifyContent:"space-between",
                  alignItems:"flex-start",flexWrap:"wrap",gap:12}}>
                  <div>
                    <div style={{fontSize:14,fontWeight:800,
                      color:pnl>=0?"#00ff88":"#ff4757",fontFamily:T.head}}>
                      {hits}-{misses}{voids>0?` · ${voids}v`:""} · {settled.length>0?((hits/settled.length)*100).toFixed(0):0}% HIT RATE
                    </div>
                    <div style={{fontSize:10,color:T.muted,
                      fontFamily:T.mono,marginTop:4}}>
                      Break-even on -110: 52.4% · -130: 56.5%
                    </div>
                  </div>
                  <div style={{display:"flex",gap:12}}>
                    <div style={{textAlign:"center",
                      background:"#ffffff08",borderRadius:6,
                      padding:"8px 14px"}}>
                      <div style={{fontSize:18,fontWeight:800,
                        color:pnl>=0?"#00ff88":"#ff4757",
                        fontFamily:T.head}}>
                        {pnl>=0?"+":""}${pnl.toFixed(0)}
                      </div>
                      <div style={{fontSize:8,color:T.muted,
                        fontFamily:T.mono,letterSpacing:1}}>
                        P&L ($100/play)
                      </div>
                    </div>
                    <div style={{textAlign:"center",
                      background:"#ffffff08",borderRadius:6,
                      padding:"8px 14px"}}>
                      <div style={{fontSize:18,fontWeight:800,
                        color:pnl>=0?"#00ff88":"#ff4757",
                        fontFamily:T.head}}>
                        {pnl>=0?"+":""}
                        {(pnl/100).toFixed(2)}u
                      </div>
                      <div style={{fontSize:8,color:T.muted,
                        fontFamily:T.mono,letterSpacing:1}}>
                        UNITS (1u=$100)
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
