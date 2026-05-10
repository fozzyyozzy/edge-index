import { useState } from "react";

// ── RESULTS — add one entry per day ──────────────────────────
const RESULTS = [
  {
    date:  "2026-05-08",
    sport: "MLB",
    plays: [
      {player:"Kyle Bradish",   prop:"K OVER 5.5",  odds:-114, tier:"T1",   hit:true,  actual:7},
      {player:"Connelly Early", prop:"K OVER 4.5",  odds:105,  tier:"T1",   hit:true,  actual:6},
      {player:"Jacob Lopez",    prop:"K OVER 4.5",  odds:-135, tier:"T2",   hit:true,  actual:5},
      {player:"Max Fried",      prop:"K OVER 5.5",  odds:-120, tier:"T2",   hit:false, actual:5},
    ],
    parlays: [],
  },
  {
    date:  "2026-05-09",
    sport: "MLB",
    plays: [
      {player:"Colson Montgomery", prop:"H OVER 0.5",  odds:-175, tier:"AUTO", hit:true,   actual:1},
      {player:"Ernie Clement",     prop:"H OVER 0.5",  odds:-235, tier:"AUTO", hit:true,   actual:1},
      {player:"Miguel Vargas",     prop:"H OVER 0.5",  odds:-175, tier:"AUTO", hit:true,   actual:1},
      {player:"Cam Schlittler",    prop:"K OVER 5.5",  odds:100,  tier:"T2",   hit:true,   actual:6},
      {player:"Joe Ryan",          prop:"K OVER 4.5",  odds:-142, tier:"T2",   hit:true,   actual:5},
      {player:"Edward Cabrera",    prop:"K OVER 5.5",  odds:104,  tier:"T2",   hit:true,   actual:6},
      {player:"Ketel Marte",       prop:"H OVER 0.5",  odds:-250, tier:"AUTO", hit:true,   actual:1},
      {player:"Addison Barger",    prop:"TB OVER 1.5", odds:135,  tier:"AUTO", hit:false,  actual:0},
      {player:"Nico Hoerner",      prop:"H OVER 0.5",  odds:-275, tier:"AUTO", hit:false,  actual:0},
      {player:"Aaron Judge",       prop:"TB OVER 1.5", odds:117,  tier:"T1",   hit:false,  actual:0},
      {player:"Xander Bogaerts",   prop:"H OVER 0.5",  odds:-250, tier:"AUTO", hit:false,  actual:0},
      {player:"Jonathan Aranda",   prop:"H OVER 0.5",  odds:-149, tier:"AUTO", hit:"void", actual:null},
      {player:"Brendan Donovan",   prop:"H OVER 0.5",  odds:-190, tier:"AUTO", hit:"void", actual:null},
    ],
    parlays: [
      {id:"P1", legs:"Montgomery + Donovan + Vargas", odds:"+277", hit:true,  pnl:277,  note:"Donovan voided → 2-leg HIT"},
      {id:"P2", legs:"Montgomery + Clement + Aranda", odds:"+274", hit:true,  pnl:274,  note:"Aranda voided → 2-leg HIT"},
      {id:"P3", legs:"Aranda + Barger TB",            odds:"+293", hit:false, pnl:-100, note:"Barger TB missed"},
      {id:"P4", legs:"Clement + Judge TB",            odds:"+240", hit:false, pnl:-100, note:"Judge 3 walks = 0 TB"},
    ],
  },
];

// ── MATH ──────────────────────────────────────────────────────
function calcPnl(plays, stake=100) {
  return plays.reduce((acc, p) => {
    // Skip pending and voided plays
    if (p.hit === null || p.hit === undefined || p.hit === "void") return acc;
    if (p.hit === true) {
      const odds = Number(p.odds);
      const ret  = odds < 0
        ? stake * (100 / Math.abs(odds))
        : stake * (odds / 100);
      return acc + ret;
    }
    // hit === false
    return acc - stake;
  }, 0);
}

function dayStats(day) {
  const settled = day.plays.filter(p =>
    p.hit !== null && p.hit !== undefined && p.hit !== "void");
  const hits   = settled.filter(p => p.hit === true).length;
  const misses = settled.filter(p => p.hit === false).length;
  const voids  = day.plays.filter(p => p.hit === "void").length;
  const pnl    = calcPnl(day.plays);
  const rate   = settled.length > 0 ? hits / settled.length : 0;
  const pending= day.plays.filter(p =>
    p.hit === null || p.hit === undefined).length;

  const parlays    = day.parlays || [];
  const p_settled  = parlays.filter(p => p.hit !== null && p.hit !== "void");
  const p_hits     = p_settled.filter(p => p.hit === true).length;
  const p_pnl      = p_settled.reduce((a,p) =>
    a + (p.hit === true ? p.pnl : -100), 0);

  return {hits, misses, voids, total:settled.length, pnl, rate, pending,
          p_hits, p_total:p_settled.length, p_pnl};
}

function allStats(results) {
  const all    = results.flatMap(d =>
    d.plays.filter(p =>
      p.hit !== null && p.hit !== undefined && p.hit !== "void"));
  const hits   = all.filter(p => p.hit === true).length;
  const pnl    = calcPnl(all);
  const rate   = all.length > 0 ? hits / all.length : 0;

  const byTier = {};
  all.forEach(p => {
    if (!byTier[p.tier]) byTier[p.tier] = {hits:0,total:0,pnl:0};
    byTier[p.tier].total++;
    if (p.hit === true) byTier[p.tier].hits++;
    byTier[p.tier].pnl += p.hit === true
      ? (p.odds < 0 ? 100*(100/Math.abs(p.odds)) : 100*(p.odds/100))
      : -100;
  });

  const bySport = {};
  results.forEach(d => {
    if (!bySport[d.sport]) bySport[d.sport] = {hits:0,total:0,pnl:0};
    d.plays.filter(p =>
      p.hit !== null && p.hit !== undefined && p.hit !== "void"
    ).forEach(p => {
      bySport[d.sport].total++;
      if (p.hit === true) bySport[d.sport].hits++;
      bySport[d.sport].pnl += p.hit === true
        ? (p.odds < 0 ? 100*(100/Math.abs(p.odds)) : 100*(p.odds/100))
        : -100;
    });
  });

  const allParlays = results.flatMap(d => d.parlays||[])
    .filter(p => p.hit !== null && p.hit !== "void");
  const p_hits = allParlays.filter(p => p.hit === true).length;
  const p_pnl  = allParlays.reduce((a,p) =>
    a + (p.hit === true ? p.pnl : -100), 0);

  return {hits, total:all.length, pnl, rate, byTier, bySport,
          p_hits, p_total:allParlays.length, p_pnl};
}

// ── STYLES ────────────────────────────────────────────────────
const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

function StatBox({label, value, color, sub}) {
  return (
    <div style={{textAlign:"center",background:"#ffffff06",
      border:"1px solid #ffffff0a",borderRadius:8,
      padding:"12px 16px",minWidth:80}}>
      <div style={{fontSize:22,fontWeight:800,color:color||T.text,
        fontFamily:T.head}}>{value}</div>
      <div style={{fontSize:8,color:T.muted,letterSpacing:2,
        fontFamily:T.mono,marginTop:2}}>{label}</div>
      {sub && <div style={{fontSize:9,color:T.muted,
        fontFamily:T.mono,marginTop:2}}>{sub}</div>}
    </div>
  );
}

// ── DAY CARD ──────────────────────────────────────────────────
function DayCard({day, expanded, onToggle}) {
  const s = dayStats(day);
  const rateColor = s.total===0 ? "#555"
    : s.rate>=0.75 ? "#00ff88"
    : s.rate>=0.50 ? "#f5c518" : "#ff4757";
  const pnlColor = s.pnl >= 0 ? "#00ff88" : "#ff4757";
  const dateStr  = new Date(day.date+"T12:00:00")
    .toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric"});
  const tierIcon = {AUTO:"⚡",T1:"★",T2:"◆",T3:"·"};

  return (
    <div onClick={onToggle} style={{background:T.surface,
      border:`1px solid ${expanded?"#ffffff18":T.border}`,
      borderRadius:8,marginBottom:6,overflow:"hidden",
      cursor:"pointer",transition:"all 0.15s"}}>
      <div style={{padding:"12px 16px",display:"flex",
        alignItems:"center",gap:12}}>
        <div style={{minWidth:120}}>
          <div style={{fontSize:13,fontWeight:700,color:T.text,
            fontFamily:T.head}}>{dateStr}</div>
          <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
            letterSpacing:1,marginTop:2}}>{day.sport}</div>
        </div>
        <div style={{flex:1,display:"flex",gap:8,alignItems:"center"}}>
          {s.total > 0 ? (
            <>
              <div style={{fontSize:22,fontWeight:800,color:rateColor,
                fontFamily:T.head}}>{s.hits}-{s.misses}</div>
              <div style={{fontSize:11,color:T.muted,fontFamily:T.mono}}>
                ({(s.rate*100).toFixed(0)}%)
                {s.voids > 0 && ` · ${s.voids} void`}
              </div>
            </>
          ) : (
            <div style={{fontSize:13,color:T.muted,fontFamily:T.mono}}>
              {s.pending > 0 ? `${s.pending} pending` : "no results"}
            </div>
          )}
          {s.p_total > 0 && (
            <div style={{fontSize:10,color:"#f5c518",fontFamily:T.mono,
              background:"#f5c51815",border:"1px solid #f5c51830",
              padding:"2px 8px",borderRadius:4}}>
              🎯 {s.p_hits}-{s.p_total-s.p_hits} parlays
            </div>
          )}
        </div>
        <div style={{textAlign:"right"}}>
          {s.total > 0 && (
            <>
              <div style={{fontSize:16,fontWeight:700,color:pnlColor,
                fontFamily:T.mono}}>
                {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
              </div>
              <div style={{fontSize:8,color:T.muted,fontFamily:T.mono}}>
                singles @$100
              </div>
            </>
          )}
          {s.p_total > 0 && (
            <div style={{fontSize:11,fontWeight:700,
              color:s.p_pnl>=0?"#00ff88":"#ff4757",
              fontFamily:T.mono}}>
              {s.p_pnl>=0?"+":""}${s.p_pnl.toFixed(0)} parlays
            </div>
          )}
        </div>
        <div style={{fontSize:14,
          color:expanded?"#fff":"#333",
          transform:expanded?"rotate(180deg)":"none",
          transition:"transform 0.2s"}}>▾</div>
      </div>

      {expanded && (
        <div style={{borderTop:`1px solid ${T.border}`,padding:"12px 16px"}}>
          {/* Parlays section */}
          {day.parlays && day.parlays.length > 0 && (
            <div style={{marginBottom:12,padding:"10px 12px",
              background:"#f5c51810",border:"1px solid #f5c51830",
              borderRadius:6}}>
              <div style={{fontSize:9,color:"#f5c518",letterSpacing:2,
                fontFamily:T.mono,marginBottom:8}}>🎯 PARLAYS</div>
              {day.parlays.map((p,i) => (
                <div key={i} style={{display:"flex",
                  justifyContent:"space-between",alignItems:"flex-start",
                  fontSize:10,marginBottom:6,paddingBottom:6,
                  borderBottom:i<day.parlays.length-1
                    ?`1px solid #ffffff06`:"none"}}>
                  <div>
                    <span style={{color:"#888",fontFamily:T.mono,
                      fontWeight:700}}>{p.id}: </span>
                    <span style={{color:"#666",fontFamily:T.mono}}>
                      {p.legs}
                    </span>
                    {p.note && (
                      <div style={{fontSize:9,color:"#444",
                        fontFamily:T.mono,marginTop:2}}>{p.note}</div>
                    )}
                  </div>
                  <div style={{display:"flex",gap:10,flexShrink:0,
                    marginLeft:12}}>
                    <span style={{color:"#666",fontFamily:T.mono}}>
                      {p.odds}
                    </span>
                    <span style={{fontWeight:700,fontFamily:T.mono,
                      color:p.hit==="void"?"#555"
                        :p.hit===true?"#00ff88":"#ff4757"}}>
                      {p.hit==="void" ? "— VOID"
                        :p.hit===true ? `✓ +$${p.pnl}`
                        : "✗ -$100"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Singles */}
          {day.plays.map((p,i) => (
            <div key={i} style={{display:"flex",
              justifyContent:"space-between",alignItems:"center",
              padding:"7px 0",
              borderBottom:i<day.plays.length-1
                ?`1px solid ${T.border}`:"none"}}>
              <div style={{display:"flex",alignItems:"center",gap:8}}>
                <span style={{fontSize:9,fontWeight:700,
                  fontFamily:T.mono,
                  color:p.tier==="AUTO"?"#00ff88"
                    :p.tier==="T1"?"#f5c518":"#00e5ff"}}>
                  {tierIcon[p.tier]}{p.tier}
                </span>
                <span style={{fontSize:12,color:T.text,
                  fontWeight:600,fontFamily:T.head}}>{p.player}</span>
                <span style={{fontSize:10,color:T.muted,
                  fontFamily:T.mono}}>{p.prop}</span>
              </div>
              <div style={{display:"flex",gap:12,alignItems:"center"}}>
                <span style={{fontSize:10,color:"#888",fontFamily:T.mono}}>
                  {p.odds>0?"+":""}{p.odds}
                </span>
                {p.actual !== null && p.actual !== undefined && (
                  <span style={{fontSize:10,color:"#666",
                    fontFamily:T.mono}}>→ {p.actual}</span>
                )}
                <span style={{fontSize:11,fontWeight:700,fontFamily:T.mono,
                  color:p.hit===null?"#555"
                    :p.hit==="void"?"#888"
                    :p.hit===true?"#00ff88":"#ff4757"}}>
                  {p.hit===null?"PENDING"
                    :p.hit==="void"?"— VOID"
                    :p.hit===true?"✓ HIT":"✗ MISS"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── DUAL CALENDAR ─────────────────────────────────────────────
function CalendarView({results}) {
  const now     = new Date();
  const year    = now.getFullYear();
  const month   = now.getMonth();
  const first   = new Date(year,month,1).getDay();
  const daysInM = new Date(year,month+1,0).getDate();
  const monthNm = now.toLocaleDateString("en-US",
    {month:"long",year:"numeric"});

  const rMap = {};
  results.forEach(d => { rMap[d.date] = dayStats(d); });

  function DayCell({day, s, isToday}) {
    return (
      <div style={{background: s && s.total>0
          ? s.rate>=0.75?"#00ff8818":s.rate>=0.50?"#f5c51818":"#ff475718"
          : "transparent",
        border:`1px solid ${isToday?"#00e5ff"
          :s&&s.total>0
          ?s.pnl>=0?"#00ff8840":"#ff475740"
          :T.border}`,
        borderRadius:5,padding:"4px 3px",minHeight:58,
        textAlign:"center"}}>
        <div style={{fontSize:9,
          color:isToday?"#00e5ff":T.muted,
          fontFamily:T.mono,
          fontWeight:isToday?700:400}}>{day}</div>
        {s && s.total > 0 && (
          <>
            <div style={{fontSize:11,fontWeight:800,
              color:s.rate>=0.75?"#00ff88"
                :s.rate>=0.50?"#f5c518":"#ff4757",
              fontFamily:T.head,marginTop:1}}>
              {s.hits}-{s.misses}
            </div>
            <div style={{fontSize:8,
              color:s.pnl>=0?"#00ff88":"#ff4757",
              fontFamily:T.mono}}>
              {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
            </div>
          </>
        )}
        {s && s.p_total > 0 && (
          <div style={{fontSize:8,
            color:s.p_pnl>=0?"#f5c518":"#ff6b35",
            fontFamily:T.mono,marginTop:1}}>
            🎯{s.p_hits}-{s.p_total-s.p_hits}
          </div>
        )}
        {s && s.pending > 0 && s.total === 0 && (
          <div style={{fontSize:8,color:"#555",
            fontFamily:T.mono,marginTop:4}}>{s.pending}p</div>
        )}
      </div>
    );
  }

  const todayStr = now.toISOString().split("T")[0];

  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,
      borderRadius:8,padding:16,maxWidth:520}}>
      <div style={{fontSize:14,fontWeight:800,color:T.text,
        fontFamily:T.head,marginBottom:12}}>{monthNm}</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(7,1fr)",
        gap:3,marginBottom:3}}>
        {["Su","Mo","Tu","We","Th","Fr","Sa"].map(d=>(
          <div key={d} style={{textAlign:"center",fontSize:9,
            color:T.muted,fontFamily:T.mono,padding:"3px 0"}}>{d}</div>
        ))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(7,1fr)",gap:3}}>
        {Array(first).fill(null).map((_,i)=><div key={"e"+i}/>)}
        {Array(daysInM).fill(null).map((_,i)=>{
          const day = i+1;
          const ds  = `${year}-${String(month+1).padStart(2,"0")}-${String(day).padStart(2,"0")}`;
          return <DayCell key={day} day={day}
            s={rMap[ds]} isToday={ds===todayStr}/>;
        })}
      </div>
      <div style={{marginTop:10,display:"flex",gap:8,flexWrap:"wrap"}}>
        {[
          {color:"#00ff8818",border:"#00ff8840",label:"75%+ singles"},
          {color:"#f5c51818",border:"#f5c51840",label:"50-74%"},
          {color:"#ff475718",border:"#ff475740",label:"Under 50%"},
        ].map(l=>(
          <div key={l.label} style={{display:"flex",alignItems:"center",gap:5}}>
            <div style={{width:10,height:10,background:l.color,
              border:`1px solid ${l.border}`,borderRadius:2}}/>
            <span style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>
              {l.label}
            </span>
          </div>
        ))}
        <div style={{display:"flex",alignItems:"center",gap:5}}>
          <span style={{fontSize:10}}>🎯</span>
          <span style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>
            parlay W-L
          </span>
        </div>
      </div>
    </div>
  );
}

// ── MAIN ──────────────────────────────────────────────────────
export default function RecordTracker() {
  const [tab,      setTab]      = useState("overview");
  const [expanded, setExpanded] = useState(null);

  const stats    = allStats(RESULTS);
  const TIER_ORD = ["AUTO","T1","T2","T3"];
  const TABS     = [
    {id:"overview", label:"📊 Overview"},
    {id:"calendar", label:"📅 Calendar"},
    {id:"parlays",  label:"🎯 Parlays"},
    {id:"log",      label:"📋 Day Log"},
  ];

  // All parlays across all days
  const allParlays = RESULTS.flatMap(d =>
    (d.parlays||[]).map(p => ({...p, date:d.date, sport:d.sport}))
  );

  return (
    <div style={{background:T.bg,minHeight:"100vh",paddingBottom:60}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        * { box-sizing:border-box; }
      `}</style>

      {/* Header */}
      <div style={{background:"#0a0f1a",
        borderBottom:`1px solid ${T.border}`,padding:"20px 24px 0"}}>
        <div style={{maxWidth:1280,margin:"0 auto"}}>
          <div style={{display:"flex",justifyContent:"space-between",
            alignItems:"flex-start",marginBottom:16,
            flexWrap:"wrap",gap:12}}>
            <div>
              <div style={{fontSize:11,color:T.muted,letterSpacing:3,
                fontFamily:T.mono,marginBottom:4}}>EDGE INDEX / RECORD</div>
              <div style={{fontSize:26,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1}}>
                PERFORMANCE TRACKER
              </div>
              <div style={{fontSize:11,color:T.muted,
                fontFamily:T.mono,marginTop:2}}>
                MLB · NFL · Singles + Parlays · Daily P&L
              </div>
            </div>
            <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
              <StatBox label="SINGLES"
                value={`${stats.hits}-${stats.total-stats.hits}`}
                color={stats.rate>=0.65?"#00ff88":"#f5c518"}
                sub={`${stats.total>0?(stats.rate*100).toFixed(0):"-"}%`}/>
              <StatBox label="SINGLES P&L"
                value={`${stats.pnl>=0?"+":""}$${stats.pnl.toFixed(0)}`}
                color={stats.pnl>=0?"#00ff88":"#ff4757"}
                sub={`${stats.pnl>=0?"+":""}${(stats.pnl/100).toFixed(2)}u`}/>
              <StatBox label="PARLAYS"
                value={`${stats.p_hits}-${stats.p_total-stats.p_hits}`}
                color={stats.p_hits>=(stats.p_total-stats.p_hits)
                  ?"#f5c518":"#ff4757"}
                sub={`${stats.p_total>0
                  ?((stats.p_hits/stats.p_total)*100).toFixed(0):"-"}%`}/>
              <StatBox label="PARLAY P&L"
                value={`${stats.p_pnl>=0?"+":""}$${stats.p_pnl.toFixed(0)}`}
                color={stats.p_pnl>=0?"#00ff88":"#ff4757"}
                sub={`${stats.p_pnl>=0?"+":""}${(stats.p_pnl/100).toFixed(2)}u`}/>
              <StatBox label="COMBINED"
                value={`${stats.pnl+stats.p_pnl>=0?"+":""}$${(stats.pnl+stats.p_pnl).toFixed(0)}`}
                color={(stats.pnl+stats.p_pnl)>=0?"#00ff88":"#ff4757"}
                sub={`${(stats.pnl+stats.p_pnl)>=0?"+":""}${((stats.pnl+stats.p_pnl)/100).toFixed(2)}u`}/>
              <StatBox label="DAYS"
                value={RESULTS.length} color="#00e5ff"/>
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
                  fontFamily:T.mono,transition:"all 0.15s"}}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{padding:"20px 24px",maxWidth:1280,margin:"0 auto"}}>

        {/* OVERVIEW */}
        {tab==="overview" && (
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            {/* By Tier */}
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
              <div style={{fontSize:13,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                SINGLES BY TIER
              </div>
              {TIER_ORD.filter(t=>stats.byTier[t]).map(tier=>{
                const s = stats.byTier[tier];
                const rate = s.total>0?s.hits/s.total:0;
                const color = tier==="AUTO"?"#00ff88"
                  :tier==="T1"?"#f5c518"
                  :tier==="T2"?"#00e5ff":"#888";
                return (
                  <div key={tier} style={{display:"flex",
                    justifyContent:"space-between",alignItems:"center",
                    padding:"8px 0",borderBottom:`1px solid ${T.border}`}}>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontSize:10,color,fontWeight:700,
                        fontFamily:T.mono,minWidth:45}}>{tier}</span>
                      <span style={{fontSize:13,color:T.text,
                        fontFamily:T.head,fontWeight:700}}>
                        {s.hits}-{s.total-s.hits}
                      </span>
                    </div>
                    <div style={{display:"flex",gap:16}}>
                      <span style={{fontSize:11,color,fontFamily:T.mono}}>
                        {(rate*100).toFixed(0)}%
                      </span>
                      <span style={{fontSize:11,fontFamily:T.mono,
                        color:s.pnl>=0?"#00ff88":"#ff4757"}}>
                        {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* By Sport */}
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
              <div style={{fontSize:13,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                BY SPORT
              </div>
              {Object.entries(stats.bySport).map(([sport,s])=>{
                const rate = s.total>0?s.hits/s.total:0;
                const color = sport==="NFL"?"#00e5ff":"#f5c518";
                return (
                  <div key={sport} style={{display:"flex",
                    justifyContent:"space-between",alignItems:"center",
                    padding:"8px 0",borderBottom:`1px solid ${T.border}`}}>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontSize:13,color,fontWeight:700,
                        fontFamily:T.head,minWidth:50}}>{sport}</span>
                      <span style={{fontSize:13,color:T.text,
                        fontFamily:T.head,fontWeight:700}}>
                        {s.hits}-{s.total-s.hits}
                      </span>
                    </div>
                    <div style={{display:"flex",gap:16}}>
                      <span style={{fontSize:11,color,fontFamily:T.mono}}>
                        {(rate*100).toFixed(0)}%
                      </span>
                      <span style={{fontSize:11,fontFamily:T.mono,
                        color:s.pnl>=0?"#00ff88":"#ff4757"}}>
                        {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                      </span>
                    </div>
                  </div>
                );
              })}
              <div style={{marginTop:10,padding:"8px 10px",
                background:"#ffffff06",borderRadius:6}}>
                <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
                  letterSpacing:1}}>BREAK-EVEN REFERENCE</div>
                <div style={{fontSize:10,color:"#666",fontFamily:T.mono,
                  marginTop:4,lineHeight:1.6}}>
                  -110: 52.4% · -130: 56.5% · -150: 60.0%
                </div>
              </div>
            </div>

            {/* Recent form */}
            <div style={{gridColumn:"1/-1",background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
              <div style={{fontSize:13,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                RECENT FORM
              </div>
              <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                {[...RESULTS].reverse().slice(0,14).map((d,i)=>{
                  const s = dayStats(d);
                  const color = s.total===0?"#555"
                    :s.rate>=0.75?"#00ff88"
                    :s.rate>=0.50?"#f5c518":"#ff4757";
                  const label = new Date(d.date+"T12:00:00")
                    .toLocaleDateString("en-US",
                      {month:"numeric",day:"numeric"});
                  return (
                    <div key={i} style={{textAlign:"center",
                      background:color+"18",
                      border:`1px solid ${color}40`,
                      borderRadius:6,padding:"8px 10px",minWidth:72}}>
                      <div style={{fontSize:9,color:T.muted,
                        fontFamily:T.mono,marginBottom:4}}>{label}</div>
                      {s.total > 0 ? (
                        <>
                          <div style={{fontSize:15,fontWeight:800,
                            color,fontFamily:T.head}}>
                            {s.hits}-{s.misses}
                          </div>
                          <div style={{fontSize:9,
                            color:s.pnl>=0?"#00ff88":"#ff4757",
                            fontFamily:T.mono}}>
                            {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                          </div>
                          {s.p_total>0 && (
                            <div style={{fontSize:9,
                              color:s.p_pnl>=0?"#f5c518":"#ff6b35",
                              fontFamily:T.mono}}>
                              🎯{s.p_hits}-{s.p_total-s.p_hits}
                            </div>
                          )}
                        </>
                      ) : (
                        <div style={{fontSize:11,color:"#555",
                          fontFamily:T.mono}}>
                          {s.pending}p
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* CALENDAR */}
        {tab==="calendar" && <CalendarView results={RESULTS}/>}

        {/* PARLAYS TAB */}
        {tab==="parlays" && (
          <div>
            {/* Parlay summary */}
            <div style={{display:"flex",gap:12,marginBottom:16,
              flexWrap:"wrap"}}>
              {[
                {label:"PARLAY RECORD",
                 val:`${stats.p_hits}-${stats.p_total-stats.p_hits}`,
                 color:"#f5c518"},
                {label:"HIT RATE",
                 val:`${stats.p_total>0?((stats.p_hits/stats.p_total)*100).toFixed(0):"-"}%`,
                 color:"#f5c518"},
                {label:"P&L @$100",
                 val:`${stats.p_pnl>=0?"+":""}$${stats.p_pnl.toFixed(0)}`,
                 color:stats.p_pnl>=0?"#00ff88":"#ff4757"},
                {label:"AVG ODDS",
                 val: allParlays.filter(p=>p.hit!==null).length > 0
                   ? allParlays.filter(p=>p.odds).slice(-1)[0]?.odds||"-"
                   : "-",
                 color:"#888"},
              ].map(s=>(
                <div key={s.label} style={{textAlign:"center",
                  background:"#ffffff06",border:"1px solid #ffffff0a",
                  borderRadius:8,padding:"12px 20px",minWidth:100}}>
                  <div style={{fontSize:22,fontWeight:800,color:s.color,
                    fontFamily:T.head}}>{s.val}</div>
                  <div style={{fontSize:8,color:T.muted,letterSpacing:2,
                    fontFamily:T.mono,marginTop:2}}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Parlay history */}
            <div style={{background:T.surface,
              border:`1px solid ${T.border}`,borderRadius:8,
              overflow:"hidden"}}>
              <div style={{display:"grid",
                gridTemplateColumns:"60px 80px 1fr 80px 80px 90px",
                gap:8,padding:"8px 16px",
                borderBottom:`1px solid ${T.border}`}}>
                {["DATE","ID","LEGS","ODDS","HIT PROB","RESULT"].map(h=>(
                  <div key={h} style={{fontSize:8,color:T.muted,
                    fontFamily:T.mono,letterSpacing:2}}>{h}</div>
                ))}
              </div>
              {allParlays.length === 0 && (
                <div style={{padding:24,textAlign:"center",
                  color:T.muted,fontFamily:T.mono,fontSize:11}}>
                  No parlays logged yet
                </div>
              )}
              {[...allParlays].reverse().map((p,i)=>(
                <div key={i} style={{display:"grid",
                  gridTemplateColumns:"60px 80px 1fr 80px 80px 90px",
                  gap:8,padding:"10px 16px",
                  borderBottom:`1px solid ${T.border}`,
                  background:i%2===0?"transparent":"#ffffff03"}}>
                  <div style={{fontSize:10,color:T.muted,
                    fontFamily:T.mono}}>{p.date.slice(5)}</div>
                  <div style={{fontSize:10,color:"#888",
                    fontFamily:T.mono,fontWeight:700}}>{p.id}</div>
                  <div style={{fontSize:10,color:"#666",
                    fontFamily:T.mono,overflow:"hidden",
                    textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                    {p.legs}
                  </div>
                  <div style={{fontSize:11,color:"#00ff88",
                    fontFamily:T.mono,fontWeight:700}}>{p.odds}</div>
                  <div style={{fontSize:10,color:T.muted,
                    fontFamily:T.mono}}>
                    {p.hit_prob ? `${(p.hit_prob*100).toFixed(0)}%` : "—"}
                  </div>
                  <div style={{fontSize:11,fontWeight:700,
                    fontFamily:T.mono,
                    color:p.hit===true?"#00ff88"
                      :p.hit===false?"#ff4757":"#555"}}>
                    {p.hit===true?`✓ +$${p.pnl}`
                      :p.hit===false?"✗ -$100"
                      :p.hit==="void"?"— VOID":"PENDING"}
                  </div>
                </div>
              ))}
            </div>

            {allParlays.length > 0 && (
              <div style={{marginTop:12,padding:"10px 16px",
                background:stats.p_pnl>=0?"#00ff8810":"#ff475710",
                border:`1px solid ${stats.p_pnl>=0?"#00ff8830":"#ff475730"}`,
                borderRadius:8}}>
                <div style={{fontSize:13,fontWeight:800,
                  color:stats.p_pnl>=0?"#00ff88":"#ff4757",
                  fontFamily:T.head}}>
                  {stats.p_hits}-{stats.p_total-stats.p_hits} PARLAYS ·{" "}
                  {stats.p_total>0?((stats.p_hits/stats.p_total)*100).toFixed(0):0}% HIT RATE ·{" "}
                  {stats.p_pnl>=0?"+":""}${stats.p_pnl.toFixed(0)} P&L
                </div>
                <div style={{fontSize:10,color:T.muted,
                  fontFamily:T.mono,marginTop:4}}>
                  Flat $100/parlay · Combined: {(stats.pnl+stats.p_pnl)>=0?"+":""}
                  ${(stats.pnl+stats.p_pnl).toFixed(0)} ·{" "}
                  {(stats.pnl+stats.p_pnl)>=0?"+":""}
                  {((stats.pnl+stats.p_pnl)/100).toFixed(2)}u total
                </div>
              </div>
            )}
          </div>
        )}

        {/* DAY LOG */}
        {tab==="log" && (
          <>
            <div style={{marginBottom:12,fontSize:11,
              color:T.muted,fontFamily:T.mono}}>
              {RESULTS.length} days · click to expand
            </div>
            {[...RESULTS].reverse().map(d=>(
              <DayCard key={d.date} day={d}
                expanded={expanded===d.date}
                onToggle={()=>setExpanded(
                  expanded===d.date?null:d.date)}/>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
