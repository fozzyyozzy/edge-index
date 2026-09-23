import { useState } from "react";
// v2026-09-23

const TODAY = "2026-09-23";

// >>> AUTO-GENERATED FREE PICK BEGIN — do not edit between markers
const FREE_PICK = {
  date:       "2026-09-23",
  player:     "Mauricio Dubon",
  prop:       "H OVER 0.5",
  odds:       -200,
  matchup:    "Atlanta Braves vs TBD",
  reason:     "Highest model_prob AUTO — 95.0% model",
  hit_prob:   0.95,
};
// <<< AUTO-GENERATED FREE PICK END

const PITCHER_PLAYS = [
  {pitcher:"George Kirby",team:"None",opp:"Seattle Mariners",home:"Seattle Mariners",
   prop:"strikeouts",line:4.5,odds:-130,tier:"T1",model_prob:0.66,
   streak:3,l5_avg:5.2,k_per_ip:0,opp_k_pct:0.228,
   alt_lines:[3.5,4.0],hand:"R",notes:["L5 avg 5.2 Ks"]},
  {pitcher:"Kevin Gausman",team:"None",opp:"Chicago Cubs",home:"Chicago Cubs",
   prop:"strikeouts",line:5.5,odds:-151,tier:"AUTO",model_prob:0.895,
   streak:5,l5_avg:6.8,k_per_ip:0,opp_k_pct:0.235,
   alt_lines:[4.5,5.0],hand:"R",notes:["L5 avg 6.8 Ks"]},
  {pitcher:"Logan Henderson",team:"None",opp:"Philadelphia Phillies",home:"Philadelphia Phillies",
   prop:"strikeouts",line:5.5,odds:-113,tier:"T1",model_prob:0.758,
   streak:4,l5_avg:6.4,k_per_ip:0,opp_k_pct:0.225,
   alt_lines:[4.5,5.0],hand:"R",notes:["L5 avg 6.4 Ks"]},
  {pitcher:"Sonny Gray",team:"None",opp:"Boston Red Sox",home:"Boston Red Sox",
   prop:"strikeouts",line:4.5,odds:-120,tier:"AUTO",model_prob:0.904,
   streak:6,l5_avg:5.8,k_per_ip:0,opp_k_pct:0.222,
   alt_lines:[3.5,4.0],hand:"R",notes:["L5 avg 5.8 Ks"]},
];

const BATTER_PLAYS = [
  {batter:"Nolan Arenado",team:"Arizona Diamondbacks",opp:"?",home:"Colorado Rockies",
   prop:"hits",line:0.5,odds:175,tier:"T1",model_prob:0.654,
   hit_streak:1,pitcher_hand:"R",
   xba:null,xba_diff:null,xwoba:null,vs_team:null,notes:["1-game hit streak"]},
  {batter:"Nolan Arenado",team:"None",opp:"?",home:"Colorado Rockies",
   prop:"hits",line:0.5,odds:100,tier:"T1",model_prob:0.654,
   hit_streak:1,pitcher_hand:"R",
   xba:null,xba_diff:null,xwoba:null,vs_team:null,notes:["1-game hit streak"]},
  {batter:"Andrew Knizner",team:"Minnesota Twins",opp:"?",home:"San Francisco Giants",
   prop:"hits",line:0.5,odds:-130,tier:"T1",model_prob:0.657,
   hit_streak:2,pitcher_hand:"R",
   xba:null,xba_diff:null,xwoba:null,vs_team:null,notes:["2-game hit streak"]},
  {batter:"Brenton Doyle",team:"Chicago White Sox",opp:"?",home:"Kansas City Royals",
   prop:"hits",line:0.5,odds:-125,tier:"AUTO",model_prob:0.894,
   hit_streak:7,pitcher_hand:"R",
   xba:null,xba_diff:null,xwoba:null,vs_team:null,notes:["7-game hit streak"]},
  {batter:"Dustin Harris",team:"San Diego Padres",opp:"?",home:"Los Angeles Dodgers",
   prop:"hits",line:0.5,odds:-140,tier:"T1",model_prob:0.675,
   hit_streak:0,pitcher_hand:"R",
   xba:null,xba_diff:null,xwoba:null,vs_team:null,notes:["0-game hit streak"]},
];

const SKIP_TODAY = [
  {player:"Keider Montero K UNDER 4.5", reason:"K UNDER dual gate pass (0.52 K/IP, 4/5 UNDER) — +118 OVER — see Parlay tab"},
  {player:"LAD -1.5",                   reason:"Freeland FIP 7.67 is extreme but LAD -1.5 at -110 fails odds gate"},
  {player:"MIL -1.5 +110",              reason:"Exactly at gate — STL cold signal real but +110 marginal value"},
  {player:"Spencer Strider K OVER 6.5", reason:"Only 4 starts returning from injury — insufficient sample, LOW_K ump Baker"},
];

const FADE_PLAYS = [
  {batter:"Isiah Kiner-Falefa",team:"?",opp:"?",
   l14_avg:".043",l14:"ICE COLD",
   odds_over:-168,odds_under:126,
   reason:"1-for-23 L14 (.043)"}, 
  {batter:"Maikel Garcia",team:"?",opp:"?",
   l14_avg:".056",l14:"ICE COLD",
   odds_over:-235,odds_under:175,
   reason:"1-for-18 L14 (.056)"}, 
  {batter:"Austin Martin",team:"?",opp:"?",
   l14_avg:".062",l14:"ICE COLD",
   odds_over:-220,odds_under:165,
   reason:"1-for-16 L14 (.062)"}, 
  {batter:"Ryan Jeffers",team:"?",opp:"?",
   l14_avg:".071",l14:"ICE COLD",
   odds_over:-220,odds_under:160,
   reason:"2-for-28 L14 (.071)"}, 
];

const PARLAY_POTENTIALS = [
  {
    player:"Keider Montero K UNDER 4.5", team:"DET", opp:"LAA", odds:118,
    streak:0, tier:"T1",
    why_juiced:"K UNDER at +118 — take the UNDER side",
    matchup:"LAA @ DET · Montero 0.52 K/IP · 4/5 UNDER 4.5 · avg 2.8 Ks vs 4.5 line",
    signal:"DUAL GATE PASS: 0.52 K/IP AND 4/5 UNDER · HIGH_K ump Conroy (+0.5) slight negative",
    parlay_with:"Stack with any batter hit OVER (different game)",
  },
  {
    player:"Corbin Carroll H OVER 0.5", team:"ARI", opp:"SF", odds:-210,
    streak:13, tier:"AUTO",
    why_juiced:"-210 eliminates single value",
    matchup:"ARI @ SF · Carroll .341 L14 · 13-game streak — longest active",
    signal:"13-game streak · 93% model prob · .272 xBA hitting BELOW skill",
    parlay_with:"Pair with Burns or Mahle (different game)",
  },
  {
    player:"Willson Contreras H OVER 0.5", team:"ATL", opp:"BOS", odds:-188,
    streak:8, tier:"AUTO",
    why_juiced:"-188 above singles cutoff",
    matchup:"ATL @ BOS · Contreras .320 career vs ATL · 8g streak",
    signal:"8-game streak · 94% model prob · xwOBA .397 strong",
    parlay_with:"Stack with Carroll (different games)",
  },
];

// ── TEAM RUN LINE DATA ──────────────────────────────────────
// Odds lookup pending fix — signals manually entered from mlb_team_rl.py output
const RL_HOT = [
];

const RL_COLD = [
];

const RL_SKIPPED = [
  {team:"LAD -1.5 vs COL",  reason:"LAD power +2.18 ELITE but -110 odds — fails gate, no value"},
  {team:"MIL -1.5 vs STL",  reason:"+110 marginal — Harrison FIP 3.65 strong but MIL power only +1.40"},
  {team:"CIN -1.5 vs NYM",  reason:"+135 qualifies on odds but CIN power -0.77 BELOW AVG — no team strength"},
  {team:"PHI -1.5 vs SD",   reason:"+155 qualifies on odds but PHI power -0.57 — marginal"},
];

const RL_METHODOLOGY = [
  "HOT team -1.5: power score >= +0.5 AND odds <= -150 or plus money",
  "Cold team fade: bet opponent -1.5 when cold team is 0-7/1-6 L7",
  "Gate: -1.5 only at -150 or better (break-even 60%) or plus money",
  "Today: ATL -1.5 +145 (ELITE) · TB -1.5 +140 (STRONG) · PIT -1.5 +150 (fade CHI 0-7)",
];

const TIER_CFG = {
  AUTO:{color:"#00ff88",bg:"#00ff8818",border:"#00ff8840",icon:"⚡"},
  T1:  {color:"#f5c518",bg:"#f5c51818",border:"#f5c51840",icon:"★"},
  T2:  {color:"#00e5ff",bg:"#00e5ff18",border:"#00e5ff40",icon:"◆"},
};

// 2026 MLB Stats API confirmed — from mlb_run_today.py output
const STREAK_BATTERS = [
  {name:"C. Carroll",    team:"ARI", streak:13, rate:0.93},
  {name:"W. Contreras",  team:"ATL", streak:8,  rate:0.94},
  {name:"J. Caminero",   team:"TB",  streak:8,  rate:0.92},
  {name:"K. Marte",      team:"ARI", streak:9,  rate:0.91},
  {name:"E. Clement",    team:"PIT", streak:8,  rate:0.89},
  {name:"T. Hernandez",  team:"LAD", streak:6,  rate:0.88},
  {name:"A. Bregman",    team:"HOU", streak:5,  rate:0.85},
  {name:"C. Smith",      team:"HOU", streak:5,  rate:0.82},
  {name:"N. Schanuel",   team:"LAA", streak:5,  rate:0.83},
];

// 2026 MLB Stats API confirmed — min 3/5 starts over line
// 2026 MLB Stats API confirmed
const STREAK_PITCHERS = [
  {name:"T. Mahle",    team:"ARI", line:"4.5+", streak:4, note:"4/5 OVER — TODAY +110"},
  {name:"C. Burns",    team:"CIN", line:"6.5+", streak:4, note:"4/5 OVER — TODAY"},
  {name:"B. Ashcraft", team:"PIT", line:"5.5+", streak:4, note:"4/5 OVER"},
  {name:"K. Montero",  team:"DET", line:"4.5 UNDER", streak:4, note:"4/5 UNDER — K UNDER play"},
];
const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

function tierBadge(tier) {
  const c = TIER_CFG[tier]||TIER_CFG.T2;
  return (
    <span style={{fontSize:9,fontWeight:700,fontFamily:T.mono,
      color:c.color,background:c.bg,border:"1px solid "+c.border,
      padding:"2px 7px",borderRadius:3,letterSpacing:1}}>
      {c.icon} {tier}
    </span>
  );
}

function xbaBadge(diff) {
  if (!diff) return null;
  const color = diff>0.030?"#00ff88":diff<-0.030?"#ff4757":"#888";
  const label = diff>0.030?"DUE UP":diff<-0.030?"LUCKY":"NEUTRAL";
  return (
    <span style={{fontSize:8,fontWeight:700,fontFamily:T.mono,color,
      background:color+"15",border:"1px solid "+color+"30",
      padding:"2px 5px",borderRadius:3,marginLeft:4}}>{label}</span>
  );
}

function PlayCard({play, type}) {
  const [open, setOpen] = useState(false);
  const cfg    = TIER_CFG[play.tier]||TIER_CFG.T2;
  const isPlus = play.odds > 0;
  const oddsStr= isPlus?"+"+play.odds:""+play.odds;
  const streak = type==="pitcher"?play.streak:play.hit_streak;
  const streakColor = streak>=10?"#00ff88":streak>=7?"#f5c518":streak>=5?"#ffa502":"#888";
  return (
    <div onClick={()=>setOpen(!open)} style={{background:T.surface,
      border:"1px solid "+(open?cfg.color+"50":isPlus?"#00ff8830":T.border),
      borderRadius:8,marginBottom:8,overflow:"hidden",cursor:"pointer",
      transition:"all 0.2s"}}>
      <div style={{padding:"12px 16px",display:"flex",alignItems:"center",gap:12}}>
        <div style={{flexShrink:0}}>{tierBadge(play.tier)}</div>
        <div style={{flex:1,minWidth:0}}>
          <div style={{display:"flex",alignItems:"center",gap:6,flexWrap:"wrap"}}>
            <span style={{fontSize:14,fontWeight:700,color:T.text,fontFamily:T.head}}>
              {type==="pitcher"?play.pitcher:play.batter}
            </span>
            <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>
              {play.team} vs {type==="pitcher"?play.opp:play.opp.split(" ").slice(-1)[0]}
            </span>
            {isPlus&&(
              <span style={{fontSize:9,color:"#00ff88",fontFamily:T.mono,
                background:"#00ff8815",padding:"2px 6px",borderRadius:3}}>
                PLUS MONEY
              </span>
            )}
            {type==="batter"&&xbaBadge(play.xba_diff)}
          </div>
          <div style={{fontSize:11,color:"#777",fontFamily:T.mono,marginTop:2}}>
            {play.prop.toUpperCase().replace("_"," ")} OVER {play.line}
            {type==="pitcher"&&" · "+play.hand+"HP · "+play.k_per_ip+" K/IP"}
          </div>
        </div>
        <div style={{display:"flex",gap:12,alignItems:"center",flexShrink:0}}>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:13,fontWeight:700,color:streakColor,
              fontFamily:T.mono}}>{streak}g</div>
            <div style={{fontSize:8,color:"#444"}}>
              {type==="pitcher"?"K STK":"STREAK"}
            </div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:18,fontWeight:800,color:cfg.color,
              fontFamily:T.head}}>{(play.model_prob*100).toFixed(0)}%</div>
            <div style={{fontSize:8,color:"#444"}}>MODEL</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:13,fontWeight:700,
              color:isPlus?"#00ff88":"#888",fontFamily:T.mono}}>{oddsStr}</div>
            <div style={{fontSize:8,color:"#444"}}>ODDS</div>
          </div>
          <span style={{fontSize:14,color:open?cfg.color:"#333"}}>
            {open?"▴":"▾"}
          </span>
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
                  paddingLeft:8,borderLeft:"2px solid "+cfg.color+"40"}}>{n}</div>
              ))}
            </div>
            <div>
              {type==="batter"&&play.xba&&(
                <>
                  <div style={{fontSize:9,color:"#444",letterSpacing:2,
                    fontFamily:T.mono,marginBottom:8}}>ADVANCED</div>
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6}}>
                    {[
                      {label:"xBA",      val:play.xba},
                      {label:"xwOBA",    val:play.xwoba},
                      {label:"xBA diff", val:play.xba_diff
                        ?(play.xba_diff>0?"+":"")+play.xba_diff.toFixed(3):"N/A"},
                    ].map(s=>(
                      <div key={s.label} style={{background:"#ffffff06",
                        borderRadius:4,padding:"6px 8px"}}>
                        <div style={{fontSize:12,fontWeight:700,color:T.text,
                          fontFamily:T.mono}}>{s.val}</div>
                        <div style={{fontSize:8,color:T.muted,
                          fontFamily:T.mono}}>{s.label}</div>
                      </div>
                    ))}
                    {play.vs_team&&(
                      <div style={{background:"#ffffff06",borderRadius:4,
                        padding:"6px 8px",gridColumn:"1 / -1"}}>
                        <div style={{fontSize:11,fontWeight:700,color:T.text,
                          fontFamily:T.mono}}>
                          vs {play.opp.split(" ").pop()}: .{(play.vs_team.avg*1000).toFixed(0).padStart(3,"0")} ({play.vs_team.hits}-for-{play.vs_team.ab}) OPS {play.vs_team.ops}
                        </div>
                        <div style={{fontSize:8,color:T.muted,
                          fontFamily:T.mono}}>career vs team</div>
                      </div>
                    )}
                  </div>
                </>
              )}
              {type==="pitcher"&&(
                <>
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
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MLBHub() {
  const [tab, setTab] = useState("plays");

  const TABS = [
    {id:"plays",   label:"⚾ Today's Plays"},
    {id:"fades",   label:"📉 Fade Plays"},
    {id:"rl",      label:"🏟️ Run Lines"},
    {id:"parlay",  label:"🎯 Parlay Potentials"},
    {id:"streaks", label:"🔥 Streaks"},
  ];

  const totalPlays = PITCHER_PLAYS.length + BATTER_PLAYS.length;

  return (
    <div style={{background:T.bg,minHeight:"100vh",paddingBottom:60}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        *{box-sizing:border-box;}
      `}</style>

      <div style={{background:"#0a0f1a",borderBottom:"1px solid "+T.border,
        padding:"20px 24px 0"}}>
        <div style={{maxWidth:1100,margin:"0 auto"}}>
          <div style={{display:"flex",justifyContent:"space-between",
            alignItems:"flex-start",marginBottom:16,flexWrap:"wrap",gap:12}}>
            <div>
              <div style={{fontSize:11,color:T.muted,letterSpacing:3,
                fontFamily:T.mono,marginBottom:4}}>EDGE INDEX / MLB</div>
              <div style={{fontSize:26,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1}}>MLB PROP TRACKER</div>
              <div style={{fontSize:12,color:T.muted,fontFamily:T.mono,marginTop:2}}>
                {TODAY} · 15 games · {totalPlays} plays · NO PARLAYS · discipline mode
              </div>
            </div>
            <div style={{display:"flex",gap:8}}>
              <div style={{background:"#00ff8815",border:"1px solid #00ff8830",
                borderRadius:6,padding:"10px 16px",textAlign:"center"}}>
                <div style={{fontSize:22,fontWeight:800,color:"#00ff88",
                  fontFamily:T.head}}>{totalPlays}</div>
                <div style={{fontSize:8,color:T.muted,fontFamily:T.mono,
                  letterSpacing:2}}>PLAYS</div>
              </div>
              <div style={{background:"#ff475715",border:"1px solid #ff475730",
                borderRadius:6,padding:"10px 16px",textAlign:"center"}}>
                <div style={{fontSize:22,fontWeight:800,color:"#ff4757",
                  fontFamily:T.head}}>{FADE_PLAYS.length}</div>
                <div style={{fontSize:8,color:T.muted,fontFamily:T.mono,
                  letterSpacing:2}}>FADES</div>
              </div>
            </div>
          </div>
          <div style={{display:"flex",overflowX:"auto"}}>
            {TABS.map(t=>(
              <button key={t.id} onClick={()=>setTab(t.id)}
                style={{padding:"10px 18px",background:"transparent",border:"none",
                  borderBottom:tab===t.id?"2px solid "+T.accent:"2px solid transparent",
                  color:tab===t.id?T.accent:T.muted,fontSize:12,fontWeight:600,
                  cursor:"pointer",fontFamily:T.mono,transition:"all 0.15s",
                  whiteSpace:"nowrap"}}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{padding:"20px 24px",maxWidth:1100,margin:"0 auto"}}>

        {tab==="plays"&&(
          <>
            {FREE_PICK && (
              <div style={{marginBottom:12,padding:"12px 16px",
                background:"#00ff8810",border:"1px solid #00ff8830",borderRadius:8}}>
                <div style={{fontSize:11,color:"#00ff88",fontFamily:T.mono,
                  letterSpacing:1,marginBottom:4}}>🎁 FREE PICK</div>
                <div style={{fontSize:14,color:T.text,fontFamily:T.head,fontWeight:700}}>
                  {FREE_PICK.player} · {FREE_PICK.prop} · {FREE_PICK.odds>0?"+":""}{FREE_PICK.odds} · {FREE_PICK.matchup}
                </div>
                <div style={{fontSize:10,color:"#888",fontFamily:T.mono,marginTop:4}}>
                  {FREE_PICK.reason}
                </div>
              </div>
            )}

            <div style={{fontSize:10,color:T.muted,letterSpacing:2,
              fontFamily:T.mono,marginBottom:8}}>⚾ PITCHER K PLAYS</div>
            {PITCHER_PLAYS.map((p,i)=><PlayCard key={i} play={p} type="pitcher"/>)}

            <div style={{fontSize:10,color:T.muted,letterSpacing:2,
              fontFamily:T.mono,marginBottom:8,marginTop:20}}>🏃 BATTER PLAYS</div>
            {BATTER_PLAYS.map((p,i)=><PlayCard key={i} play={p} type="batter"/>)}

            <div style={{marginTop:16,padding:"12px 16px",background:"#ffffff04",
              border:"1px solid #ffffff08",borderRadius:8}}>
              <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
                letterSpacing:2,marginBottom:8}}>DISCIPLINE RULES — TODAY</div>
              {[
                "Max 8 plays — only what is listed above",
                "No parlays — singles only this week",
                "Only bet plays shown here — nothing from the full model output",
                "Results tracked from this card only — keeps P&L accurate",
              ].map((r,i)=>(
                <div key={i} style={{fontSize:10,color:"#555",fontFamily:T.mono,
                  marginBottom:4,paddingLeft:8,
                  borderLeft:"2px solid #ffffff10"}}>✓ {r}</div>
              ))}
            </div>
          </>
        )}

        {tab==="fades"&&(
          <div>
            <div style={{marginBottom:12,padding:"12px 16px",
              background:"#ff475710",border:"1px solid #ff475730",borderRadius:8}}>
              <div style={{fontSize:11,color:"#ff4757",fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>
                📉 FADE PLAYS — COLD BATS + xBA FLAGS + K UNDERS
              </div>
              <div style={{fontSize:11,color:"#888",fontFamily:T.mono,lineHeight:1.6}}>
                53% hit rate (29-26) season to date. Tier 1 (.100 and below) is the strongest signal.
                Umpire-adjusted K UNDERs added as additional fade layer.
              </div>
            </div>
            <div style={{background:T.surface,border:"1px solid "+T.border,
              borderRadius:8,overflow:"hidden"}}>
              <div style={{display:"grid",
                gridTemplateColumns:"1fr 100px 70px 70px 1fr",
                gap:8,padding:"8px 16px",
                borderBottom:"1px solid "+T.border}}>
                {["PLAYER","SIGNAL","OVER","UNDER","REASON"].map(h=>(
                  <div key={h} style={{fontSize:8,color:T.muted,
                    fontFamily:T.mono,letterSpacing:2}}>{h}</div>
                ))}
              </div>
              {FADE_PLAYS.map((p,i)=>{
                const isSpecial = p.l14_avg==="K"||p.l14_avg==="xBA";
                const avgNum    = parseFloat("0"+p.l14_avg.replace(/[^0-9.]/g,""));
                const color     = isSpecial?"#f5c518":
                                  avgNum<0.080?"#ff4757":
                                  avgNum<0.120?"#ff6b35":"#ffa502";
                const underClr  = p.odds_under>0?"#00ff88":"#888";
                return (
                  <div key={i} style={{display:"grid",
                    gridTemplateColumns:"1fr 100px 70px 70px 1fr",
                    gap:8,padding:"10px 16px",
                    borderBottom:i<FADE_PLAYS.length-1
                      ?"1px solid "+T.border:"none",
                    background:i%2===0?"transparent":"#ffffff02"}}>
                    <div>
                      <div style={{fontSize:13,color:T.text,fontWeight:700,
                        fontFamily:T.head}}>{p.batter}</div>
                      <div style={{fontSize:9,color:T.muted,
                        fontFamily:T.mono}}>{p.team} vs {p.opp}</div>
                    </div>
                    <div>
                      <div style={{fontSize:11,fontWeight:700,color,
                        fontFamily:T.mono}}>{p.l14_avg}</div>
                      <div style={{fontSize:9,color:"#555",
                        fontFamily:T.mono}}>{p.l14}</div>
                    </div>
                    <div style={{fontSize:12,color:"#888",fontFamily:T.mono,
                      alignSelf:"center"}}>
                      {p.odds_over>0?"+":""}{p.odds_over}
                    </div>
                    <div style={{fontSize:13,fontWeight:800,color:underClr,
                      fontFamily:T.head,alignSelf:"center"}}>
                      {p.odds_under>0?"+":""}{p.odds_under}
                    </div>
                    <div style={{fontSize:10,color:"#666",fontFamily:T.mono,
                      alignSelf:"center"}}>{p.reason}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab==="parlay"&&(
          <div>
            <div style={{marginBottom:12,padding:"12px 16px",
              background:"#f5c51810",border:"1px solid #f5c51830",borderRadius:8}}>
              <div style={{fontSize:11,color:"#f5c518",fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>
                🎯 PARLAY POTENTIALS — Great signal, too juiced for singles
              </div>
              <div style={{fontSize:11,color:"#888",fontFamily:T.mono,lineHeight:1.6}}>
                These players have real momentum and favorable matchups but odds
                eliminate single value. Use as parlay legs with other confirmed plays.
              </div>
            </div>
            {PARLAY_POTENTIALS.map((p,i)=>(
              <div key={i} style={{background:T.surface,
                border:"1px solid "+T.border,borderRadius:8,
                marginBottom:10,overflow:"hidden"}}>
                <div style={{padding:"12px 16px",
                  borderBottom:"1px solid "+T.border,
                  display:"flex",justifyContent:"space-between",
                  alignItems:"center"}}>
                  <div style={{display:"flex",gap:10,alignItems:"center"}}>
                    <span style={{fontSize:9,fontWeight:700,
                      color:"#f5c518",background:"#f5c51818",
                      border:"1px solid #f5c51840",padding:"2px 7px",
                      borderRadius:3,fontFamily:T.mono}}>PARLAY</span>
                    <div>
                      <div style={{fontSize:15,fontWeight:800,color:T.text,
                        fontFamily:T.head}}>{p.player}</div>
                      <div style={{fontSize:9,color:T.muted,
                        fontFamily:T.mono}}>{p.team} vs {p.opp}</div>
                    </div>
                  </div>
                  <div style={{textAlign:"right"}}>
                    <div style={{fontSize:15,fontWeight:800,
                      color:"#ff4757",fontFamily:T.head}}>{p.odds}</div>
                    <div style={{fontSize:9,color:"#f5c518",
                      fontFamily:T.mono}}>{p.streak}g streak</div>
                  </div>
                </div>
                <div style={{padding:"10px 16px",display:"grid",
                  gridTemplateColumns:"1fr 1fr",gap:10}}>
                  <div>
                    <div style={{fontSize:8,color:T.muted,fontFamily:T.mono,
                      letterSpacing:2,marginBottom:4}}>MATCHUP</div>
                    <div style={{fontSize:11,color:"#00ff88",
                      fontFamily:T.mono,lineHeight:1.5}}>{p.matchup}</div>
                  </div>
                  <div>
                    <div style={{fontSize:8,color:T.muted,fontFamily:T.mono,
                      letterSpacing:2,marginBottom:4}}>SIGNAL</div>
                    <div style={{fontSize:11,color:T.text,
                      fontFamily:T.mono,lineHeight:1.5}}>{p.signal}</div>
                  </div>
                </div>
                <div style={{padding:"8px 16px",
                  background:"#f5c51808",
                  borderTop:"1px solid "+T.border}}>
                  <div style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>
                    <span style={{color:"#f5c518",fontWeight:700}}>WHY JUICED: </span>
                    {p.why_juiced}
                  </div>
                  <div style={{fontSize:9,color:"#00e5ff",
                    fontFamily:T.mono,marginTop:3}}>
                    <span style={{fontWeight:700}}>PAIR WITH: </span>
                    {p.parlay_with}
                  </div>
                </div>
              </div>
            ))}
            <div style={{marginTop:8,padding:"10px 14px",
              background:"#ffffff06",borderRadius:8,
              border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:10,color:T.muted,fontFamily:T.mono,
                lineHeight:1.6}}>
                <strong style={{color:"#f5c518"}}>Parlay discipline:</strong>
                {" "}Max 2-3 legs. Only pair plays from different games.
                Avoid stacking same lineup with itself more than twice.
                Target combined hit prob above 60%.
              </div>
            </div>
          </div>
        )}

        {tab==="rl"&&(
          <div>
            <div style={{marginBottom:12,padding:"12px 16px",
              background:"#00e5ff10",border:"1px solid #00e5ff30",borderRadius:8}}>
              <div style={{fontSize:11,color:"#00e5ff",fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>
                🏟️ TEAM RUN LINE PLAYS
              </div>
            </div>

            {RL_HOT.length>0&&(
              <>
                <div style={{fontSize:10,color:T.muted,letterSpacing:2,
                  fontFamily:T.mono,marginBottom:8}}>🔥 HOT TEAM -1.5</div>
                {RL_HOT.map((p,i)=>(
                  <div key={i} style={{background:T.surface,
                    border:"1px solid #00ff8830",borderRadius:8,
                    marginBottom:10,padding:"14px 16px"}}>
                    <div style={{display:"flex",justifyContent:"space-between",
                      alignItems:"flex-start"}}>
                      <div>
                        <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
                          <span style={{fontSize:9,fontWeight:700,color:"#00ff88",
                            background:"#00ff8818",border:"1px solid #00ff8840",
                            padding:"2px 7px",borderRadius:3,fontFamily:T.mono}}>
                            {p.tier}
                          </span>
                          <span style={{fontSize:15,fontWeight:800,color:T.text,
                            fontFamily:T.head}}>{p.team}</span>
                          <span style={{fontSize:10,color:T.muted,
                            fontFamily:T.mono}}>{p.is_home?"vs":"@"} {p.opp}</span>
                        </div>
                        <div style={{fontSize:11,color:"#777",fontFamily:T.mono,marginTop:4}}>
                          {p.team} -1.5 · {p.record.wins}-{p.record.losses} L7 · {p.record.avg_scored} RS/g
                        </div>
                        <div style={{fontSize:10,color:"#555",fontFamily:T.mono,marginTop:4}}>
                          {p.reason}
                        </div>
                      </div>
                      <div style={{textAlign:"center",flexShrink:0}}>
                        <div style={{fontSize:20,fontWeight:800,color:"#00ff88",
                          fontFamily:T.head}}>{p.odds}</div>
                        <div style={{fontSize:8,color:"#444",fontFamily:T.mono}}>-1.5 RL</div>
                        <div style={{fontSize:11,color:"#00e5ff",fontFamily:T.mono,
                          marginTop:4}}>{p.score>0?"+":""}{p.score} sig</div>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}

            {RL_COLD.length>0&&(
              <>
                <div style={{fontSize:10,color:T.muted,letterSpacing:2,
                  fontFamily:T.mono,marginBottom:8,marginTop:16}}>❄️ COLD TEAM +1.5</div>
                {RL_COLD.map((p,i)=>(
                  <div key={i} style={{background:T.surface,
                    border:"1px solid #00e5ff30",borderRadius:8,
                    marginBottom:10,padding:"14px 16px"}}>
                    <div style={{display:"flex",justifyContent:"space-between",
                      alignItems:"flex-start"}}>
                      <div>
                        <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
                          <span style={{fontSize:9,fontWeight:700,color:"#00e5ff",
                            background:"#00e5ff18",border:"1px solid #00e5ff40",
                            padding:"2px 7px",borderRadius:3,fontFamily:T.mono}}>
                            {p.tier}
                          </span>
                          <span style={{fontSize:15,fontWeight:800,color:T.text,
                            fontFamily:T.head}}>{p.team}</span>
                          <span style={{fontSize:10,color:T.muted,
                            fontFamily:T.mono}}>{p.is_home?"vs":"@"} {p.opp}</span>
                        </div>
                        <div style={{fontSize:11,color:"#777",fontFamily:T.mono,marginTop:4}}>
                          {p.team} +1.5 · {p.record.wins}-{p.record.losses} L7 · {p.record.avg_scored} RS/g
                        </div>
                        <div style={{fontSize:10,color:"#555",fontFamily:T.mono,marginTop:4}}>
                          {p.reason}
                        </div>
                      </div>
                      <div style={{textAlign:"center",flexShrink:0}}>
                        <div style={{fontSize:20,fontWeight:800,color:"#00e5ff",
                          fontFamily:T.head}}>+{p.odds}</div>
                        <div style={{fontSize:8,color:"#444",fontFamily:T.mono}}>+1.5 RL</div>
                        <div style={{fontSize:11,color:"#ff4757",fontFamily:T.mono,
                          marginTop:4}}>{p.score} sig</div>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}

            {RL_SKIPPED.length>0&&(
              <div style={{marginTop:16,background:T.surface,
                border:"1px solid "+T.border,borderRadius:8,padding:"12px 16px"}}>
                <div style={{fontSize:9,color:T.muted,letterSpacing:2,
                  fontFamily:T.mono,marginBottom:8}}>SKIPPED / PENDING</div>
                {RL_SKIPPED.map((s,i)=>(
                  <div key={i} style={{fontSize:10,color:"#555",fontFamily:T.mono,
                    marginBottom:4,paddingLeft:8,borderLeft:"2px solid #ffffff10"}}>
                    {s.team} — {s.reason}
                  </div>
                ))}
              </div>
            )}

            <div style={{marginTop:16,padding:"12px 16px",
              background:"#ffffff04",border:"1px solid #ffffff08",borderRadius:8}}>
              <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
                letterSpacing:2,marginBottom:8}}>METHODOLOGY</div>
              {RL_METHODOLOGY.map((m,i)=>(
                <div key={i} style={{fontSize:10,color:"#555",fontFamily:T.mono,
                  marginBottom:4,paddingLeft:8,borderLeft:"2px solid #00e5ff20"}}>
                  {m}
                </div>
              ))}
            </div>
          </div>
        )}

        {tab==="streaks"&&(
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            <div style={{background:T.surface,border:"1px solid "+T.border,
              borderRadius:8,padding:16}}>
              <div style={{fontSize:14,fontWeight:800,color:"#f5c518",
                fontFamily:T.head,letterSpacing:1,marginBottom:14}}>
                🏃 BATTER HIT STREAKS
              </div>
              {STREAK_BATTERS.map((p,i)=>{
                const color = p.streak>=10?"#00ff88":p.streak>=7?"#f5c518":"#ffa502";
                const emoji = p.streak>=10?"🔥":p.streak>=7?"⚡":"✅";
                return (
                  <div key={i} style={{display:"flex",justifyContent:"space-between",
                    alignItems:"center",marginBottom:8,paddingBottom:8,
                    borderBottom:i<STREAK_BATTERS.length-1
                      ?"1px solid "+T.border:"none"}}>
                    <div>
                      <div style={{fontSize:13,color:T.text,fontFamily:T.head,
                        fontWeight:700}}>{p.name}</div>
                      <div style={{fontSize:9,color:T.muted,
                        fontFamily:T.mono}}>{p.team}</div>
                    </div>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontSize:14}}>{emoji}</span>
                      <div style={{textAlign:"right"}}>
                        <div style={{fontSize:14,fontWeight:800,color,
                          fontFamily:T.head}}>{p.streak}g</div>
                        <div style={{fontSize:9,color:T.muted,
                          fontFamily:T.mono}}>{(p.rate*100).toFixed(0)}% L60</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div style={{background:T.surface,border:"1px solid "+T.border,
              borderRadius:8,padding:16}}>
              <div style={{fontSize:14,fontWeight:800,color:"#00e5ff",
                fontFamily:T.head,letterSpacing:1,marginBottom:14}}>
                ⚾ PITCHER K STREAKS
              </div>
              {STREAK_PITCHERS.map((p,i)=>(
                <div key={i} style={{display:"flex",justifyContent:"space-between",
                  alignItems:"center",marginBottom:10,paddingBottom:10,
                  borderBottom:i<STREAK_PITCHERS.length-1
                    ?"1px solid "+T.border:"none"}}>
                  <div>
                    <div style={{fontSize:13,color:T.text,fontFamily:T.head,
                      fontWeight:700}}>{p.name}</div>
                    <div style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>
                      {p.team} · K OVER {p.line} · {p.note}
                    </div>
                  </div>
                  <div style={{textAlign:"right"}}>
                    <div style={{fontSize:14,fontWeight:800,
                      color:p.streak>=5?"#00ff88":"#f5c518",
                      fontFamily:T.head}}>{p.streak}/5</div>
                    <div style={{fontSize:9,color:T.muted,
                      fontFamily:T.mono}}>OVER streak</div>
                  </div>
                </div>
              ))}
              <div style={{marginTop:12,padding:"10px 12px",
                background:"#ff475710",borderRadius:6,
                border:"1px solid #ff475730"}}>
                <div style={{fontSize:10,color:"#ff4757",fontFamily:T.mono,
                  lineHeight:1.6}}>
                  <strong>K UNDER TODAY:</strong> Patrick Corbin 5/5 UNDER 4.5 · 0.56 K/IP · avg 2.6 Ks · PIT @ TOR. Dual gate pass. +110 OVER = take the UNDER.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={{margin:"20px 24px 0",padding:"12px 16px",
        background:"#ffffff04",border:"1px solid #ffffff08",borderRadius:8,
        maxWidth:1100,marginLeft:"auto",marginRight:"auto"}}>
        <div style={{fontSize:9,color:"#444",
          fontFamily:"'IBM Plex Mono',monospace",
          lineHeight:1.6,textAlign:"center"}}>
          ⚠️ ENTERTAINMENT PURPOSES ONLY — Not financial advice.
          Sports betting involves risk. Must be 21+. 1-800-GAMBLER.
        </div>
      </div>
    </div>
  );
}
