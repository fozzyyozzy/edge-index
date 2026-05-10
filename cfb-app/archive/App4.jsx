import { useState } from "react";

const T = {
  bg:"#0a0a0f",surface:"#12121a",card:"#1a1a26",border:"#2a2a3d",borderHi:"#3d3d5c",
  accent:"#00e5ff",gold:"#f5c518",green:"#00c896",red:"#ff4757",amber:"#ffa502",
  purple:"#a855f7",text:"#e8e8f0",muted:"#8888a8",dim:"#4a4a6a",
};

const css = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Barlow:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0a0a0f;color:#e8e8f0;font-family:'Barlow',sans-serif;font-size:14px;min-height:100vh;}
.mono{font-family:'IBM Plex Mono',monospace;}
.cond{font-family:'Barlow Condensed',sans-serif;}
.cfb-nav{background:#0a0a0fee;border-bottom:1px solid #2a2a3d;display:flex;align-items:center;padding:0 16px;height:50px;gap:6px;position:sticky;top:0;z-index:100;flex-wrap:wrap;}
.cfb-logo{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:800;letter-spacing:.08em;color:#00e5ff;text-transform:uppercase;margin-right:20px;white-space:nowrap;}
.cfb-logo span{color:#f5c518;}
.ntab{height:50px;padding:0 12px;display:flex;align-items:center;font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;cursor:pointer;border-bottom:2px solid transparent;transition:color .15s,border-color .15s;white-space:nowrap;}
.ntab:hover{color:#e8e8f0;}
.ntab.on{color:#00e5ff;border-bottom-color:#00e5ff;}
.pg{max-width:960px;margin:0 auto;padding:20px 16px;}
.pg-title{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;margin-bottom:3px;}
.pg-sub{font-size:12px;color:#8888a8;margin-bottom:18px;}
.card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:16px;margin-bottom:12px;}
.card-hdr{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;padding-bottom:10px;border-bottom:1px solid #2a2a3d;margin-bottom:12px;}
.itabs{display:flex;gap:4px;margin-bottom:14px;flex-wrap:wrap;}
.itab{font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;padding:5px 11px;border-radius:3px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;white-space:nowrap;}
.itab:hover{color:#e8e8f0;}
.itab.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;}
.stat-box{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:12px 14px;}
.stat-lbl{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.stat-val{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;line-height:1;}
.stat-sub{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#8888a8;margin-top:3px;}
.game-card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:6px;margin-bottom:10px;overflow:hidden;cursor:pointer;transition:border-color .15s;}
.game-card:hover{border-color:#3d3d5c;}
.game-card.expanded{border-color:#00e5ff66;}
.game-header{padding:14px 16px;display:grid;grid-template-columns:1fr auto auto;gap:12px;align-items:center;}
.away-team{font-family:'Barlow Condensed',sans-serif;font-size:14px;font-weight:600;color:#8888a8;margin-bottom:2px;}
.home-team{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:800;letter-spacing:.02em;}
.conf-badge{font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid;margin-top:4px;display:inline-block;}
.edge-box{text-align:center;padding:8px 16px;border-radius:4px;}
.edge-val{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:800;line-height:1;}
.edge-lbl{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#8888a8;margin-top:3px;}
.bet-tags{display:flex;flex-direction:column;gap:4px;align-items:flex-end;}
.bet-tag{font-family:'IBM Plex Mono',monospace;font-size:10px;padding:3px 8px;border-radius:3px;border:1px solid;white-space:nowrap;}
.game-body{border-top:1px solid #2a2a3d;padding:16px;}
.model-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px;}
.model-box{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:10px;text-align:center;}
.model-name{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:6px;}
.model-spread{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:800;line-height:1;}
.model-note{font-size:10px;color:#8888a8;margin-top:3px;}
.agree-bar{display:flex;align-items:center;gap:10px;margin-bottom:14px;}
.agree-track{flex:1;height:6px;background:#2a2a3d;border-radius:3px;overflow:hidden;}
.agree-fill{height:100%;border-radius:3px;transition:width .8s;}
.factor-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px;}
.factor-box{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:10px 12px;}
.factor-label{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.factor-val{font-family:'Barlow Condensed',sans-serif;font-size:16px;font-weight:700;}
.play-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #2a2a3d66;font-size:13px;}
.play-row:last-child{border-bottom:none;}
.t1{background:#f5c51822;color:#f5c518;border:1px solid #f5c51844;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.t2{background:#00e5ff18;color:#00e5ff;border:1px solid #00e5ff33;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.filter-row{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;align-items:center;}
.filter-label{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;}
.filter-btn{font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:3px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;}
.filter-btn:hover{color:#e8e8f0;}
.filter-btn.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.power-row{display:grid;grid-template-columns:28px 1fr 60px 60px 60px 60px 80px;gap:8px;align-items:center;padding:10px 12px;border-bottom:1px solid #2a2a3d66;font-size:13px;cursor:pointer;}
.power-row:last-child{border-bottom:none;}
.power-row:hover{background:#12121a;}
.rank-num{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#8888a8;text-align:center;}
.team-name{font-family:'Barlow Condensed',sans-serif;font-size:15px;font-weight:700;}
.rating-val{font-family:'IBM Plex Mono',monospace;font-size:12px;text-align:right;}
.composite-bar{height:4px;background:#2a2a3d;border-radius:2px;margin-top:4px;overflow:hidden;}
.composite-fill{height:100%;border-radius:2px;}
.sit-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;background:#12121a;border:1px solid #2a2a3d;color:#8888a8;padding:2px 6px;border-radius:2px;margin:2px;}
.sit-pos{color:#00c896;background:#00c89612;border-color:#00c89628;}
.sit-neg{color:#ff4757;background:#ff475712;border-color:#ff475728;}
.sit-neu{color:#ffa502;background:#ffa50212;border-color:#ffa50228;}
.prog-t{height:5px;background:#2a2a3d;border-radius:3px;overflow:hidden;}
.prog-f{height:100%;border-radius:3px;}
.disagree-flag{background:#ffa50218;border:1px solid #ffa50233;border-radius:3px;padding:6px 10px;font-size:11px;color:#ffa502;margin-bottom:10px;}
.total-section{border-top:1px solid #2a2a3d;padding-top:12px;margin-top:12px;}
`;

const CONF_COLORS = {
  SEC:"#ff4757",B1G:"#00e5ff",B12:"#f5c518",ACC:"#a855f7",
  MWC:"#ffa502",IND:"#00c896",
};
const confColor = c => CONF_COLORS[c] || "#8888a8";

function computeComposite(models) {
  const vals = Object.values(models);
  const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
  const variance = vals.reduce((s,v)=>s+Math.pow(v-mean,2),0)/vals.length;
  const sigma = Math.sqrt(variance);
  return { composite: parseFloat(mean.toFixed(1)), disagreement: parseFloat(sigma.toFixed(2)) };
}

function edgeVsMarket(composite, marketSpread) {
  return parseFloat((marketSpread - composite).toFixed(1));
}

const GAMES = [
  {
    id:1, away:"Auburn", home:"Alabama", conf:"SEC", time:"Sat 8pm ET",
    market:{ spread:-14.5, total:51.0, fh_spread:-7.5 },
    models:{ "SP+":-8.2, "ESPN FPI":-11.4, "Sagarin":-9.8, "Massey":-10.1, "Connelly":-9.3 },
    situational:{
      nightGame:{ label:"SEC night game", adj:1.5, dir:"home" },
      rivalry:{ label:"Iron Bowl tightens", adj:-1.5, dir:"tightens" },
      recentForm:{ label:"Alabama +2.1 form", adj:1.2, dir:"home" },
      pace:{ label:"Alabama 68 vs 72 pl/g", adj:0.4, dir:"home" },
    },
    efficiency:{
      homeOff:{ label:"Alabama Off SR", val:"48.2%", rank:3 },
      homeDef:{ label:"Alabama Def SR", val:"28.1%", rank:2 },
      awayOff:{ label:"Auburn Off SR", val:"39.4%", rank:28 },
      awayDef:{ label:"Auburn Def SR", val:"35.7%", rank:19 },
    },
    plays:[
      { bet:"Auburn ATS -14.5", type:"spread", tier:1, edge:5.2, prob:62 },
      { bet:"UNDER 51.0", type:"total", tier:2, edge:3.1, prob:55 },
    ]
  },
  {
    id:2, away:"Tennessee", home:"Georgia", conf:"SEC", time:"Sat 3:30pm ET",
    market:{ spread:-10.0, total:48.5, fh_spread:-5.5 },
    models:{ "SP+":-7.1, "ESPN FPI":-8.8, "Sagarin":-7.9, "Massey":-8.4, "Connelly":-7.6 },
    situational:{
      afternoon:{ label:"Afternoon kickoff", adj:-0.3, dir:"away" },
      rivalry:{ label:"SEC East rivalry", adj:-0.8, dir:"tightens" },
      recentForm:{ label:"Tennessee +1.4 form", adj:0.7, dir:"away" },
      pace:{ label:"Tennessee 76 pl/g (fast)", adj:1.1, dir:"total-up" },
    },
    efficiency:{
      homeOff:{ label:"Georgia Off SR", val:"44.1%", rank:8 },
      homeDef:{ label:"Georgia Def SR", val:"30.4%", rank:5 },
      awayOff:{ label:"Tennessee Off SR", val:"46.8%", rank:6 },
      awayDef:{ label:"Tennessee Def SR", val:"33.2%", rank:14 },
    },
    plays:[
      { bet:"Tennessee +10.0", type:"spread", tier:1, edge:2.4, prob:58 },
      { bet:"OVER 48.5", type:"total", tier:1, edge:4.2, prob:63 },
      { bet:"Tennessee +5.5 1H", type:"fh", tier:2, edge:1.8, prob:54 },
    ]
  },
  {
    id:3, away:"Ohio State", home:"Michigan", conf:"B1G", time:"Sat 12pm ET",
    market:{ spread:7.0, total:44.5, fh_spread:3.5 },
    models:{ "SP+":4.1, "ESPN FPI":5.8, "Sagarin":3.9, "Massey":4.7, "Connelly":4.4 },
    situational:{
      noon:{ label:"Noon kickoff road", adj:-0.8, dir:"away" },
      rivalry:{ label:"The Game tightens", adj:-2.0, dir:"tightens" },
      recentForm:{ label:"Ohio St +1.8 form", adj:0.9, dir:"away" },
      pace:{ label:"Michigan 64 pl/g (slow)", adj:-0.6, dir:"total-dn" },
    },
    efficiency:{
      homeOff:{ label:"Michigan Off SR", val:"41.2%", rank:18 },
      homeDef:{ label:"Michigan Def SR", val:"34.8%", rank:11 },
      awayOff:{ label:"Ohio St Off SR", val:"52.1%", rank:1 },
      awayDef:{ label:"Ohio St Def SR", val:"29.3%", rank:4 },
    },
    plays:[
      { bet:"Ohio State -7.0", type:"spread", tier:1, edge:2.9, prob:60 },
      { bet:"UNDER 44.5", type:"total", tier:2, edge:2.1, prob:54 },
    ]
  },
  {
    id:4, away:"Boise State", home:"UNLV", conf:"MWC", time:"Fri 10pm ET",
    market:{ spread:-6.5, total:58.0, fh_spread:-3.5 },
    models:{ "SP+":-9.8, "ESPN FPI":-8.2, "Sagarin":-10.1, "Massey":-9.4, "Connelly":-9.7 },
    situational:{
      nightGame:{ label:"Friday night boost", adj:0.5, dir:"home" },
      travel:{ label:"Boise→Las Vegas altitude", adj:-0.3, dir:"away" },
      pace:{ label:"Both teams 74+ pl/g", adj:1.8, dir:"total-up" },
      recentForm:{ label:"Boise St +0.8 form", adj:0.4, dir:"away" },
    },
    efficiency:{
      homeOff:{ label:"UNLV Off SR", val:"43.1%", rank:12 },
      homeDef:{ label:"UNLV Def SR", val:"36.2%", rank:22 },
      awayOff:{ label:"Boise St Off SR", val:"47.8%", rank:5 },
      awayDef:{ label:"Boise St Def SR", val:"31.1%", rank:9 },
    },
    plays:[
      { bet:"Boise State ATS -6.5", type:"spread", tier:1, edge:3.1, prob:61 },
      { bet:"OVER 58.0", type:"total", tier:1, edge:5.8, prob:67 },
      { bet:"Boise St -3.5 1H", type:"fh", tier:2, edge:2.1, prob:56 },
    ]
  },
];

const POWER_RANKINGS = [
  { rank:1, team:"Georgia",       conf:"SEC", sp:28.4, fpi:96.2, sagarin:88.1, connelly:29.1, composite:91, record:"10-0" },
  { rank:2, team:"Ohio State",    conf:"B1G", sp:26.1, fpi:94.8, sagarin:86.4, connelly:27.3, composite:89, record:"9-1"  },
  { rank:3, team:"Alabama",       conf:"SEC", sp:24.8, fpi:93.1, sagarin:84.2, connelly:25.9, composite:87, record:"9-1"  },
  { rank:4, team:"Oregon",        conf:"B1G", sp:23.2, fpi:91.4, sagarin:82.8, connelly:24.1, composite:85, record:"10-0" },
  { rank:5, team:"Notre Dame",    conf:"IND", sp:21.8, fpi:89.7, sagarin:81.3, connelly:22.4, composite:83, record:"9-1"  },
  { rank:6, team:"Texas",         conf:"SEC", sp:20.4, fpi:88.2, sagarin:79.6, connelly:21.0, composite:81, record:"8-2"  },
  { rank:7, team:"Penn State",    conf:"B1G", sp:19.1, fpi:86.8, sagarin:78.1, connelly:19.8, composite:79, record:"9-1"  },
  { rank:8, team:"Boise State",   conf:"MWC", sp:18.2, fpi:81.4, sagarin:74.9, connelly:18.8, composite:74, record:"10-0" },
  { rank:9, team:"Tennessee",     conf:"SEC", sp:17.4, fpi:84.1, sagarin:76.8, connelly:17.9, composite:77, record:"8-2"  },
  { rank:10,team:"SMU",           conf:"ACC", sp:16.8, fpi:79.3, sagarin:72.4, connelly:17.1, composite:72, record:"9-1"  },
  { rank:11,team:"Indiana",       conf:"B1G", sp:15.9, fpi:78.1, sagarin:71.2, connelly:16.4, composite:71, record:"9-1"  },
  { rank:12,team:"Clemson",       conf:"ACC", sp:14.8, fpi:76.8, sagarin:70.1, connelly:15.2, composite:69, record:"8-2"  },
  { rank:13,team:"Iowa State",    conf:"B12", sp:14.1, fpi:75.4, sagarin:68.9, connelly:14.6, composite:68, record:"8-2"  },
  { rank:14,team:"Arizona State", conf:"B12", sp:13.4, fpi:74.2, sagarin:67.8, connelly:13.8, composite:67, record:"8-2"  },
  { rank:15,team:"UNLV",          conf:"MWC", sp:12.8, fpi:69.1, sagarin:63.4, connelly:13.1, composite:63, record:"9-1"  },
];

function ModelComparison({ models, market }) {
  const { composite, disagreement } = computeComposite(models);
  const edge = edgeVsMarket(composite, market.spread);
  const vals  = Object.values(models);
  const range = Math.abs(Math.max(...vals) - Math.min(...vals));
  const bigDisagree = range >= 4.0;

  return (
    <div>
      {bigDisagree && (
        <div className="disagree-flag">
          ⚡ Model disagreement detected — range of {range.toFixed(1)} pts. High disagreement = potential market mispricing.
        </div>
      )}
      <div className="model-grid">
        {Object.entries(models).map(([name, val]) => {
          const diff = val - composite;
          const isOut = Math.abs(diff) >= 2.0;
          return (
            <div className="model-box" key={name} style={{ borderColor: isOut ? "#ffa50266" : "#2a2a3d" }}>
              <div className="model-name">{name}</div>
              <div className="model-spread" style={{ color: val < 0 ? "#00c896" : "#ff4757" }}>
                {val > 0 ? "+" : ""}{val}
              </div>
              <div className="model-note" style={{ color: isOut ? "#ffa502" : "#8888a8" }}>
                {isOut ? `${diff > 0 ? "+" : ""}${diff.toFixed(1)} outlier` : "in range"}
              </div>
            </div>
          );
        })}
        <div className="model-box" style={{ borderColor: "#00e5ff66" }}>
          <div className="model-name" style={{ color: "#00e5ff" }}>Composite</div>
          <div className="model-spread" style={{ color: "#00e5ff" }}>
            {composite > 0 ? "+" : ""}{composite}
          </div>
          <div className="model-note" style={{ color: "#8888a8" }}>σ = {disagreement.toFixed(1)}</div>
        </div>
      </div>
      <div className="agree-bar">
        <span style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:10, fontWeight:700, letterSpacing:".12em", textTransform:"uppercase", color:"#8888a8", minWidth:90 }}>
          Model agree
        </span>
        <div className="agree-track">
          <div className="agree-fill" style={{
            width: `${Math.max(10, 100 - disagreement * 20)}%`,
            background: disagreement < 2 ? "#00c896" : disagreement < 3.5 ? "#ffa502" : "#ff4757"
          }}/>
        </div>
        <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:10, color:"#8888a8", minWidth:60, textAlign:"right" }}>
          {disagreement < 2 ? "HIGH" : disagreement < 3.5 ? "MEDIUM" : "LOW"}
        </span>
      </div>
      <div style={{ display:"flex", gap:10, alignItems:"center", padding:"10px 12px", background:"#12121a", borderRadius:4, border:"1px solid #2a2a3d" }}>
        <div>
          <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:9, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:"#8888a8", marginBottom:3 }}>Market spread</div>
          <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:20, fontWeight:800 }}>{market.spread > 0 ? "+" : ""}{market.spread}</div>
        </div>
        <div style={{ fontSize:18, color:"#4a4a6a" }}>→</div>
        <div>
          <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:9, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:"#8888a8", marginBottom:3 }}>Composite</div>
          <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:20, fontWeight:800, color:"#00e5ff" }}>{composite > 0 ? "+" : ""}{composite}</div>
        </div>
        <div style={{ fontSize:18, color:"#4a4a6a" }}>→</div>
        <div>
          <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:9, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:"#8888a8", marginBottom:3 }}>Edge</div>
          <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:20, fontWeight:800, color: Math.abs(edge) >= 3 ? "#f5c518" : "#00c896" }}>
            {edge > 0 ? "+" : ""}{edge} pts
          </div>
        </div>
        {Math.abs(edge) >= 3 && <div style={{ marginLeft:"auto" }}><span className="t1">★★★ HIGH EDGE</span></div>}
        {Math.abs(edge) >= 2 && Math.abs(edge) < 3 && <div style={{ marginLeft:"auto" }}><span className="t2">★★ EDGE</span></div>}
      </div>
    </div>
  );
}

function SituationalFactors({ situational, efficiency }) {
  const totalAdj = Object.values(situational).reduce((s,f)=>s+f.adj,0);
  return (
    <div>
      <div style={{ marginBottom:10 }}>
        <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:10, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:"#8888a8", marginBottom:8 }}>
          Situational adjustments
        </div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:0, marginBottom:8 }}>
          {Object.values(situational).map((f,i) => (
            <span key={i} className={`sit-tag ${f.adj > 0.5 ? "sit-pos" : f.adj < -0.5 ? "sit-neg" : "sit-neu"}`}>
              {f.label} ({f.adj > 0 ? "+" : ""}{f.adj})
            </span>
          ))}
        </div>
        <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:11, color:"#e8e8f0" }}>
          Total: <span style={{ color: totalAdj > 0 ? "#00c896" : totalAdj < 0 ? "#ff4757" : "#8888a8", fontWeight:500 }}>
            {totalAdj > 0 ? "+" : ""}{totalAdj.toFixed(1)} pts
          </span>
        </div>
      </div>
      <div style={{ borderTop:"1px solid #2a2a3d", paddingTop:12 }}>
        <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:10, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:"#8888a8", marginBottom:8 }}>
          Efficiency ratings
        </div>
        <div className="factor-grid">
          {Object.entries(efficiency).map(([key,ef]) => (
            <div className="factor-box" key={key}>
              <div className="factor-label">{ef.label}</div>
              <div className="factor-val" style={{ color: ef.rank <= 10 ? "#00c896" : ef.rank <= 20 ? "#ffa502" : "#ff4757" }}>
                {ef.val}
              </div>
              <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:9, color:"#8888a8", marginTop:2 }}>Rank #{ef.rank}</div>
              <div className="prog-t" style={{ marginTop:6 }}>
                <div className="prog-f" style={{ width:`${Math.max(5,100-ef.rank*3)}%`, background: ef.rank <= 10 ? "#00c896" : ef.rank <= 20 ? "#ffa502" : "#ff4757" }}/>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TotalSection({ market, models, situational }) {
  const paceAdj = situational.pace?.adj || 0;
  const modelAvg = Object.values(models).reduce((a,b)=>a+b,0)/Object.values(models).length;
  const projTotal = parseFloat((market.total + Math.abs(modelAvg)*0.4 + paceAdj*1.2).toFixed(1));
  const totalEdge = parseFloat((projTotal - market.total).toFixed(1));
  return (
    <div className="total-section">
      <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:10, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:"#8888a8", marginBottom:10 }}>
        Total analysis
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8 }}>
        {[
          {l:"Market total",v:market.total,c:"#e8e8f0"},
          {l:"Model projection",v:projTotal,c:"#00e5ff"},
          {l:"Edge",v:`${totalEdge>0?"+":""}${totalEdge}`,c:Math.abs(totalEdge)>=3?"#f5c518":"#00c896"},
          {l:"First half",v:market.fh_spread,c:"#8888a8"},
        ].map(s => (
          <div key={s.l} style={{ background:"#12121a", border:"1px solid #2a2a3d", borderRadius:4, padding:"10px 12px" }}>
            <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:9, fontWeight:700, letterSpacing:".12em", textTransform:"uppercase", color:"#8888a8", marginBottom:4 }}>{s.l}</div>
            <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:20, fontWeight:800, color:s.c }}>{s.v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GameCard({ game, betFilter }) {
  const [expanded, setExpanded] = useState(false);
  const [drillTab, setDrillTab] = useState("models");
  const { composite } = computeComposite(game.models);
  const spreadEdge = edgeVsMarket(composite, game.market.spread);
  const filteredPlays = betFilter === "ALL" ? game.plays : game.plays.filter(p=>p.type===betFilter);
  if (betFilter !== "ALL" && filteredPlays.length === 0) return null;
  const edgeColor = Math.abs(spreadEdge) >= 5 ? "#f5c518" : Math.abs(spreadEdge) >= 2.5 ? "#00c896" : "#8888a8";

  return (
    <div className={`game-card${expanded?" expanded":""}`}>
      <div className="game-header" onClick={()=>setExpanded(!expanded)}>
        <div>
          <div className="away-team">{game.away}</div>
          <div className="home-team">{game.home}</div>
          <div style={{ display:"flex", gap:6, marginTop:4, alignItems:"center" }}>
            <span className="conf-badge" style={{ color:confColor(game.conf), borderColor:confColor(game.conf)+"44", background:confColor(game.conf)+"18" }}>
              {game.conf}
            </span>
            <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:9, color:"#8888a8" }}>{game.time}</span>
          </div>
        </div>
        <div className="edge-box" style={{
          background: Math.abs(spreadEdge) >= 3 ? edgeColor+"18" : "#12121a",
          border: `1px solid ${Math.abs(spreadEdge) >= 3 ? edgeColor+"44" : "#2a2a3d"}`
        }}>
          <div className="edge-val" style={{ color:edgeColor }}>{spreadEdge > 0 ? "+" : ""}{spreadEdge}</div>
          <div className="edge-lbl">pts edge</div>
        </div>
        <div className="bet-tags">
          {filteredPlays.slice(0,2).map((p,i) => (
            <span key={i} className="bet-tag" style={{
              color: p.tier===1 ? "#f5c518" : "#00e5ff",
              borderColor: p.tier===1 ? "#f5c51844" : "#00e5ff33",
              background: p.tier===1 ? "#f5c51818" : "#00e5ff15",
            }}>
              {p.bet}
            </span>
          ))}
          <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:9, color:"#4a4a6a", textAlign:"right" }}>
            {expanded ? "▲ collapse" : "▼ expand"}
          </span>
        </div>
      </div>
      {expanded && (
        <div className="game-body">
          <div className="itabs">
            {[{id:"models",l:"Model Comparison"},{id:"situation",l:"Situational"},{id:"efficiency",l:"Efficiency"},{id:"plays",l:"Plays"}].map(t => (
              <button key={t.id} className={`itab${drillTab===t.id?" on":""}`} onClick={()=>setDrillTab(t.id)}>{t.l}</button>
            ))}
          </div>
          {drillTab==="models"    && <ModelComparison models={game.models} market={game.market}/>}
          {drillTab==="situation" && <SituationalFactors situational={game.situational} efficiency={game.efficiency}/>}
          {drillTab==="efficiency"&& (
            <div>
              <SituationalFactors situational={game.situational} efficiency={game.efficiency}/>
              <TotalSection market={game.market} models={game.models} situational={game.situational}/>
            </div>
          )}
          {drillTab==="plays" && (
            <div>
              {game.plays.map((p,i) => (
                <div key={i} className="play-row">
                  <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                    {p.tier===1 ? <span className="t1">★★★ TIER 1</span> : <span className="t2">★★ TIER 2</span>}
                    <span style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:15, fontWeight:700 }}>{p.bet}</span>
                  </div>
                  <div style={{ display:"flex", gap:12, alignItems:"center" }}>
                    <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:12, color:"#00c896" }}>+{p.edge}pts</span>
                    <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:11, color:"#8888a8" }}>{p.prob}% cover</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function GamesPage() {
  const [conf, setConf] = useState("ALL");
  const [bet,  setBet]  = useState("ALL");
  const filtered = GAMES.filter(g => conf === "ALL" || g.conf === conf);
  const tier1Count = GAMES.filter(g => {
    const {composite} = computeComposite(g.models);
    return Math.abs(edgeVsMarket(composite, g.market.spread)) >= 3;
  }).length;
  return (
    <div className="pg">
      <div className="pg-title">CFB Game Analysis — Week 10</div>
      <div className="pg-sub">SP+ · ESPN FPI · Sagarin · Massey · Connelly · Composite · Situational factors</div>
      <div className="stat-grid">
        {[
          {l:"Games analyzed", v:GAMES.length, s:"This week",        c:"#e8e8f0"},
          {l:"Tier 1 edges",   v:tier1Count,   s:"≥3pt model edge",  c:"#f5c518"},
          {l:"Avg disagreement",v:"2.4σ",      s:"Between models",   c:"#ffa502"},
          {l:"High confidence", v:"4",          s:"Models aligned",   c:"#00c896"},
        ].map(s => (
          <div className="stat-box" key={s.l}>
            <div className="stat-lbl">{s.l}</div>
            <div className="stat-val" style={{color:s.c}}>{s.v}</div>
            <div className="stat-sub">{s.s}</div>
          </div>
        ))}
      </div>
      <div className="filter-row">
        <span className="filter-label">Conf:</span>
        {["ALL","SEC","B1G","B12","ACC","MWC","IND"].map(c => (
          <button key={c} className={`filter-btn${conf===c?" on":""}`} onClick={()=>setConf(c)}>{c}</button>
        ))}
        <span className="filter-label" style={{marginLeft:8}}>Bet:</span>
        {[{id:"ALL",l:"All"},{id:"spread",l:"Spreads"},{id:"total",l:"Totals"},{id:"fh",l:"1st Half"}].map(b => (
          <button key={b.id} className={`filter-btn${bet===b.id?" on":""}`} onClick={()=>setBet(b.id)}>{b.l}</button>
        ))}
      </div>
      <div style={{marginBottom:8,fontSize:11,color:"#8888a8"}}>Click any game to drill into models, situational factors, and efficiency.</div>
      {filtered.map(g => <GameCard key={g.id} game={g} betFilter={bet}/>)}
    </div>
  );
}

function RankingsPage() {
  const [sortBy, setSortBy] = useState("composite");
  const [conf,   setConf]   = useState("ALL");
  const [drill,  setDrill]  = useState(null);
  const sorted = [...POWER_RANKINGS]
    .filter(t => conf === "ALL" || t.conf === conf)
    .sort((a,b) => b[sortBy] - a[sortBy]);
  const drillData = drill ? POWER_RANKINGS.find(t=>t.team===drill) : null;
  return (
    <div className="pg">
      <div className="pg-title">Power Rankings</div>
      <div className="pg-sub">SP+ · ESPN FPI · Sagarin · Connelly · Edge Index Composite — All FBS</div>
      <div className="filter-row">
        <span className="filter-label">Sort:</span>
        {[{id:"composite",l:"Composite"},{id:"sp",l:"SP+"},{id:"fpi",l:"FPI"},{id:"sagarin",l:"Sagarin"},{id:"connelly",l:"Connelly"}].map(s => (
          <button key={s.id} className={`filter-btn${sortBy===s.id?" on":""}`} onClick={()=>setSortBy(s.id)}>{s.l}</button>
        ))}
        <span className="filter-label" style={{marginLeft:8}}>Conf:</span>
        {["ALL","SEC","B1G","B12","ACC","MWC","IND"].map(c => (
          <button key={c} className={`filter-btn${conf===c?" on":""}`} onClick={()=>setConf(c)}>{c}</button>
        ))}
      </div>
      {drillData && (
        <div className="card" style={{borderColor:confColor(drillData.conf)+"66",marginBottom:16}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
            <div>
              <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,fontWeight:800}}>{drillData.team}</div>
              <div style={{display:"flex",gap:8,marginTop:4}}>
                <span className="conf-badge" style={{color:confColor(drillData.conf),borderColor:confColor(drillData.conf)+"44",background:confColor(drillData.conf)+"18"}}>{drillData.conf}</span>
                <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:11,color:"#8888a8"}}>{drillData.record}</span>
              </div>
            </div>
            <button className="filter-btn" onClick={()=>setDrill(null)}>✕ Close</button>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8}}>
            {[{l:"SP+",v:drillData.sp,c:"#00c896"},{l:"ESPN FPI",v:drillData.fpi,c:"#00e5ff"},{l:"Sagarin",v:drillData.sagarin,c:"#ffa502"},{l:"Connelly",v:drillData.connelly,c:"#a855f7"}].map(m => (
              <div key={m.l} style={{background:"#12121a",border:"1px solid #2a2a3d",borderRadius:4,padding:"10px 12px"}}>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:4}}>{m.l}</div>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:800,color:m.c}}>{m.v}</div>
              </div>
            ))}
          </div>
          <div style={{marginTop:10}}>
            <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:10,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:6}}>Composite</div>
            <div style={{display:"flex",alignItems:"center",gap:10}}>
              <div className="agree-track" style={{flex:1,height:8}}>
                <div className="agree-fill" style={{width:`${drillData.composite}%`,background:confColor(drillData.conf)}}/>
              </div>
              <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:13,color:"#e8e8f0"}}>{drillData.composite}/100</span>
            </div>
          </div>
        </div>
      )}
      <div className="card">
        <div className="card-hdr">FBS Power Rankings — {conf==="ALL"?"All conferences":conf}</div>
        <div style={{display:"grid",gridTemplateColumns:"28px 1fr 60px 60px 60px 60px 80px",gap:8,padding:"0 0 8px",borderBottom:"1px solid #2a2a3d"}}>
          {["#","Team","SP+","FPI","Sagarin","Connelly","Composite"].map(h => (
            <div key={h} style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8",textAlign:h==="Team"?"left":"right"}}>{h}</div>
          ))}
        </div>
        {sorted.map((t,i) => (
          <div key={t.team} className="power-row" onClick={()=>setDrill(drill===t.team?null:t.team)}>
            <div className="rank-num">{i+1}</div>
            <div>
              <div className="team-name" style={{color:drill===t.team?confColor(t.conf):"#e8e8f0"}}>{t.team}</div>
              <div style={{display:"flex",gap:6,marginTop:2}}>
                <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:9,color:confColor(t.conf)}}>{t.conf}</span>
                <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:9,color:"#8888a8"}}>{t.record}</span>
              </div>
            </div>
            <div className="rating-val" style={{color:"#00c896"}}>{t.sp}</div>
            <div className="rating-val" style={{color:"#00e5ff"}}>{t.fpi}</div>
            <div className="rating-val" style={{color:"#ffa502"}}>{t.sagarin}</div>
            <div className="rating-val" style={{color:"#a855f7"}}>{t.connelly}</div>
            <div style={{textAlign:"right"}}>
              <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700}}>{t.composite}</div>
              <div className="composite-bar">
                <div className="composite-fill" style={{width:`${t.composite}%`,background:confColor(t.conf)}}/>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SituationalPage() {
  const edges = [
    {factor:"SEC night games (home team)",          adj:"+1.5 pts", n:48, hit:61, note:"Death Valley, Swamp, Bryant-Denny — crowd factor is real"},
    {factor:"Noon kickoff road team (east→west)",   adj:"+1.2 pts", n:34, hit:59, note:"West coast teams traveling east for noon games are undervalued"},
    {factor:"Rivalry game spread tightening",       adj:"-1.8 pts", n:92, hit:63, note:"Games between rivals historically come within 1.8 pts of models"},
    {factor:"Altitude advantage (1500m+)",          adj:"+0.8 pts", n:28, hit:54, note:"Colorado, BYU — altitude measurably affects opponents in first half"},
    {factor:"Back-to-back travel weeks",            adj:"+1.4 pts", n:41, hit:58, note:"Third road game in four weeks = significant underdog fade"},
    {factor:"Fast pace vs slow defense (total)",    adj:"+3.2 pts", n:67, hit:64, note:"75+ pl/game offense vs 68+ allowed D = over signal"},
    {factor:"G5 home vs P4 underdog",               adj:"+2.1 pts", n:53, hit:57, note:"P4 teams underestimate G5 home environments"},
    {factor:"Early bye week advantage",             adj:"+0.9 pts", n:39, hit:55, note:"Team coming off bye vs team on short week"},
    {factor:"High SR offense vs bad SR defense",    adj:"+4.1 pts", n:78, hit:67, note:"SR >45% offense vs SR-allowed >38% D = consistent over signal"},
  ];
  return (
    <div className="pg">
      <div className="pg-title">Situational Edge Database</div>
      <div className="pg-sub">Historical factors not captured in power rankings — night games, travel, rivalry tightening, pace matchups</div>
      <div className="stat-grid">
        {[{l:"Tracked factors",v:9,c:"#e8e8f0"},{l:"Avg hit rate",v:"60%",c:"#00c896"},{l:"Best factor",v:"67%",c:"#f5c518"},{l:"Sample size",v:"480+",c:"#00e5ff"}].map(s => (
          <div className="stat-box" key={s.l}><div className="stat-lbl">{s.l}</div><div className="stat-val" style={{color:s.c}}>{s.v}</div></div>
        ))}
      </div>
      <div className="card">
        <div className="card-hdr">Situational factors — empirical adjustments</div>
        {edges.map((e,i) => (
          <div key={i} style={{padding:"12px 0",borderBottom:"1px solid #2a2a3d66"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}>
              <div>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700,marginBottom:3}}>{e.factor}</div>
                <div style={{fontSize:12,color:"#8888a8"}}>{e.note}</div>
              </div>
              <div style={{textAlign:"right",minWidth:80}}>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:18,fontWeight:800,color:"#00c896"}}>{e.adj}</div>
                <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:10,color:"#8888a8"}}>n={e.n}</div>
              </div>
            </div>
            <div style={{display:"flex",alignItems:"center",gap:10}}>
              <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8",minWidth:60}}>Hit rate</span>
              <div className="prog-t" style={{flex:1}}>
                <div className="prog-f" style={{width:`${e.hit}%`,background:e.hit>=63?"#f5c518":e.hit>=58?"#00c896":"#ffa502"}}/>
              </div>
              <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:11,color:"#e8e8f0",minWidth:36}}>{e.hit}%</span>
              {e.hit >= 63 && <span className="t1">★★★</span>}
              {e.hit >= 58 && e.hit < 63 && <span className="t2">★★</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("games");
  const tabs = [
    {id:"games",    l:"Game Analysis"},
    {id:"rankings", l:"Power Rankings"},
    {id:"sit",      l:"Situational Factors"},
  ];
  return (
    <>
      <style>{css}</style>
      <nav className="cfb-nav">
        <div className="cfb-logo">EDGE<span>INDEX</span> <span style={{color:"#8888a8",fontSize:12,fontWeight:400,letterSpacing:".05em"}}>/ CFB</span></div>
        {tabs.map(t => (
          <div key={t.id} className={`ntab${tab===t.id?" on":""}`} onClick={()=>setTab(t.id)}>{t.l}</div>
        ))}
      </nav>
      {tab==="games"    && <GamesPage/>}
      {tab==="rankings" && <RankingsPage/>}
      {tab==="sit"      && <SituationalPage/>}
    </>
  );
}
