import { useState } from "react";

// ── Data ──────────────────────────────────────────────────────────────────────

const AUTO_PLAYS = [
  {
    player:"Sam Darnold",     team:"MIN", pos:"QB",
    prop:"Pass Att UNDER 31.5", dir:"UNDER",
    streak:10, l15:13, season:13,
    hitRate:87, avgActual:28.1, postedLine:31.5,
    odds:142, lineAdj:false,
    why:"Market pricing this as a coin flip. Data says 87%. Rarest find — auto-play floor AT plus money.",
    gameScript:"MIN run-first, Flores D, quick release system",
    risk:"LOW",
  },
  {
    player:"Zay Flowers",     team:"BAL", pos:"WR",
    prop:"Receptions OVER 3.5", dir:"OVER",
    streak:11, l15:14, season:14,
    hitRate:93, avgActual:5.1, postedLine:3.5,
    odds:-388, lineAdj:false,
    why:"93% hit rate. Line unchanged at 3.5 despite 11 straight. Book cannot move it without creating liability.",
    gameScript:"BAL heavy favorite, pass volume elevated late",
    risk:"LOW",
  },
  {
    player:"Lamar Jackson",   team:"BAL", pos:"QB",
    prop:"Rush Yards OVER 28.5", dir:"OVER",
    streak:8, l15:14, season:14,
    hitRate:91, avgActual:48.2, postedLine:28.5,
    odds:-315, lineAdj:false,
    why:"Automatic floor. Lamar rushes for 28+ in virtually every healthy game. Design runs alone cover this.",
    gameScript:"BAL favored, run game is identity",
    risk:"VERY LOW",
  },
  {
    player:"Trey McBride",    team:"ARI", pos:"TE",
    prop:"Rec Yards OVER 42.5", dir:"OVER",
    streak:8, l15:11, season:12,
    hitRate:88, avgActual:72.4, postedLine:62.5,
    odds:-284, lineAdj:false,
    why:"Floor at 42.5 hits 88%. Posted line at 62.5 is already a different bet. Both worth playing.",
    gameScript:"ARI trailing = elevated pass volume",
    risk:"LOW",
  },
  {
    player:"Saquon Barkley",  team:"PHI", pos:"RB",
    prop:"Rush Yards OVER 58.5", dir:"OVER",
    streak:7, l15:13, season:13,
    hitRate:86, avgActual:102.4, postedLine:88.5,
    odds:-271, lineAdj:false,
    why:"Floor at 58.5 is 44 yards below his average. PHI designs their offense around him.",
    gameScript:"PHI heavy favorite, game script locks in run volume",
    risk:"LOW",
  },
  {
    player:"Josh Allen",      team:"BUF", pos:"QB",
    prop:"Pass Yards OVER 225.5", dir:"OVER",
    streak:7, l15:12, season:12,
    hitRate:86, avgActual:294.2, postedLine:268.5,
    odds:-334, lineAdj:true,
    why:"Line adjusted from 248 to 268.5 but floor at 225.5 still holds. Book chasing his average upward.",
    gameScript:"High-stakes game, BUF pass-first regardless",
    risk:"LOW",
  },
];

const PLAYER_STREAKS = [
  { player:"Zay Flowers",       team:"BAL", pos:"WR", prop:"Receptions OVER 3.5",      dir:"OVER",  streak:11, l15:14, season:14, lineAdj:false, avgActual:5.1,   postedLine:3.5,   optLine:"3.5 (-388)",  odds:-388, note:"Market has NOT adjusted. Line unchanged at 3.5 despite 11 straight.", schemeNote:"CLE slot rank 31st this week" },
  { player:"Sam Darnold",       team:"MIN", pos:"QB", prop:"Pass Att UNDER 31.5",      dir:"UNDER", streak:10, l15:13, season:13, lineAdj:false, avgActual:28.1,  postedLine:31.5,  optLine:"31.5 (+142)", odds:142,  note:"Darnold quick-release system beats UNDER consistently. Market still sleeping.", schemeNote:"MIN run-first, Flores system" },
  { player:"Rashee Rice",       team:"KC",  pos:"WR", prop:"Rec Yards OVER 52.5",      dir:"OVER",  streak:9,  l15:11, season:13, lineAdj:true,  avgActual:76.6,  postedLine:62.5,  optLine:"52.5 (-142)", odds:-142, note:"Line moved from 55.5 to 62.5. Floor at 52.5 still holds at 82%.", schemeNote:"Zone beater vs BUF 71% zone" },
  { player:"Lamar Jackson",     team:"BAL", pos:"QB", prop:"Rush Yards OVER 28.5",     dir:"OVER",  streak:8,  l15:14, season:14, lineAdj:false, avgActual:48.2,  postedLine:28.5,  optLine:"28.5 (-315)", odds:-315, note:"Floor line. Automatic unless injury. Design runs alone cover this.", schemeNote:"CLE new DC Rutenberg" },
  { player:"Trey McBride",      team:"ARI", pos:"TE", prop:"Rec Yards OVER 42.5",      dir:"OVER",  streak:8,  l15:11, season:12, lineAdj:true,  avgActual:72.4,  postedLine:62.5,  optLine:"42.5 (-284)", odds:-284, note:"Line adjusted upward. Floor at 42.5 still hitting 88%+.", schemeNote:"SF zone exposes TE middle" },
  { player:"Amon-Ra St. Brown", team:"DET", pos:"WR", prop:"Rec Yards OVER 57.5",      dir:"OVER",  streak:7,  l15:10, season:12, lineAdj:true,  avgActual:81.2,  postedLine:68.5,  optLine:"57.5 (-140)", odds:-140, note:"Line slowly adjusting. Still 10+ pts below his average.", schemeNote:"DAL zone, Eberflus new DC" },
  { player:"Justin Jefferson",  team:"MIN", pos:"WR", prop:"Rec Yards OVER 48.5",      dir:"OVER",  streak:7,  l15:10, season:11, lineAdj:false, avgActual:74.1,  postedLine:74.5,  optLine:"48.5 (-175)", odds:-175, note:"Floor at 48.5 hitting 86%. Posted line at 74.5 is a different risk level.", schemeNote:"GB Gannon man shift incoming" },
  { player:"Saquon Barkley",    team:"PHI", pos:"RB", prop:"Rush Yards OVER 58.5",     dir:"OVER",  streak:7,  l15:13, season:13, lineAdj:true,  avgActual:102.4, postedLine:88.5,  optLine:"58.5 (-271)", odds:-271, note:"Floor automatic. PHI offense designed around him.", schemeNote:"WAS new DC Jones, run D rank 22nd" },
  { player:"Josh Allen",        team:"BUF", pos:"QB", prop:"Pass Yards OVER 225.5",    dir:"OVER",  streak:7,  l15:12, season:12, lineAdj:true,  avgActual:294.2, postedLine:268.5, optLine:"225.5 (-334)", odds:-334, note:"Floor holds despite line adjustment upward.", schemeNote:"KC blitz 32%, Allen thrives" },
  { player:"Jonathan Taylor",   team:"IND", pos:"RB", prop:"Rush Yards OVER 54.5",     dir:"OVER",  streak:6,  l15:9,  season:11, lineAdj:false, avgActual:94.1,  postedLine:82.5,  optLine:"54.5 (-178)", odds:-178, note:"Line not adjusted to recent form. Floor hitting 88%+.", schemeNote:"TEN new HC scheme installing" },
  { player:"Brock Bowers",      team:"LV",  pos:"TE", prop:"Rec Yards OVER 36.5",      dir:"OVER",  streak:6,  l15:9,  season:10, lineAdj:false, avgActual:64.8,  postedLine:54.5,  optLine:"36.5 (-168)", odds:-168, note:"Floor well below his average. Elite route rate sustains this.", schemeNote:"DEN zone heavy" },
  { player:"Puka Nacua",        team:"LAR", pos:"WR", prop:"Rec Yards OVER 38.5",      dir:"OVER",  streak:6,  l15:8,  season:10, lineAdj:false, avgActual:68.4,  postedLine:54.5,  optLine:"38.5 (-158)", odds:-158, note:"Line set low for injury risk. When active, floor is automatic.", schemeNote:"ARI new DC uncertainty" },
];

const TEAM_STREAKS = [
  { team:"DET Lions",     trend:"OVER team total 27",      dir:"OVER",  streak:8, context:"home", note:"DET home scoring machine. 8 straight home games OVER 27 pts.", impact:"WR/TE OVERs, Goff pass yards" },
  { team:"BAL Ravens",    trend:"UNDER first half total",  dir:"UNDER", streak:6, context:"road", note:"BAL runs heavily in first halves on road. Second half opens up.", impact:"First half UNDER, Lamar rush yards" },
  { team:"KC Chiefs",     trend:"OVER team total 23",      dir:"OVER",  streak:7, context:"all",  note:"KC offensive consistency. 7 straight scoring 23+.", impact:"Rice rec yards, Kelce recs" },
  { team:"MIN Vikings",   trend:"UNDER team total 24",     dir:"UNDER", streak:5, context:"road", note:"Darnold conservative on road. Game managed.", impact:"Darnold UNDER att, Jefferson floor plays" },
  { team:"SF 49ers",      trend:"UNDER game total",        dir:"UNDER", streak:5, context:"home", note:"SF home games consistently low scoring. Purdy efficient but low volume.", impact:"Game UNDER, Purdy att UNDER" },
  { team:"PHI Eagles",    trend:"OVER first half total",   dir:"OVER",  streak:6, context:"all",  note:"PHI fast starters. 6 straight first halves scoring 17+.", impact:"First half OVER, Barkley rush yards" },
  { team:"CIN Bengals",   trend:"OVER game total",         dir:"OVER",  streak:7, context:"all",  note:"Burrow + Chase = fireworks. 7 straight games OVER 47.", impact:"Chase rec yards, Burrow pass yards" },
  { team:"NYJ Jets",      trend:"OVER pass attempts",      dir:"OVER",  streak:6, context:"all",  note:"Jets always trailing, always passing. Wilson volume elevated.", impact:"Wilson rec yards, Garrett Wilson recs" },
];

const POSITION_STREAKS = [
  { pos:"WR", vs:"CLE Browns",     defRank:31, streak:6, stat:"WR1 opponents hit OVER rec yards line", avgYds:84.2, avgPostedLine:67.8, gap:16.4, players:["A.Cooper","S.Diggs","D.Adams","Chase","T.Hill","R.Rice"], results:[1,1,1,1,1,1], note:"CLE secondary torched by every WR1 for 6 straight. New DC Rutenberg still installing.", thisWeek:"Zay Flowers · BAL @ CLE · OVER 4.5 recs" },
  { pos:"TE", vs:"SF 49ers",       defRank:9,  streak:5, stat:"TE opponents hit OVER rec yards line",  avgYds:71.2, avgPostedLine:58.4, gap:12.8, players:["D.Goedert","E.Engram","S.LaPorta","C.Kmet","T.McBride"], results:[1,1,1,1,1], note:"SF Morris zone — new DC — consistently surrenders TE middle routes.", thisWeek:"Trey McBride · ARI vs SF · OVER 62.5 rec yds" },
  { pos:"RB", vs:"WAS Commanders", defRank:22, streak:5, stat:"RB opponents hit OVER rush yards line", avgYds:96.4, avgPostedLine:81.2, gap:15.2, players:["Barkley","D.Henry","J.Taylor","D.Achane","A.Jones"], results:[1,1,1,0,1], note:"WAS new DC Jones — run D trending worse. 4 of 5 opposing RBs hit OVER.", thisWeek:"Saquon Barkley · PHI vs WAS · OVER 88.5 rush yds" },
  { pos:"WR", vs:"DAL Cowboys",    defRank:5,  streak:4, stat:"WR2 opponents hit OVER rec yards line", avgYds:58.4, avgPostedLine:48.2, gap:10.2, players:["K.Shakir","T.Lockett","R.Doubs","M.Harrison"], results:[1,1,1,1], note:"DAL focuses coverage on WR1. WR2 slot getting open consistently under Eberflus zone.", thisWeek:"Slot WR vs DAL — check weekly lineup" },
  { pos:"QB", vs:"NYJ Jets",       defRank:28, streak:5, stat:"QB opponents hit OVER pass yards line",  avgYds:284.2, avgPostedLine:251.6, gap:32.6, players:["L.Jackson","J.Allen","J.Goff","D.Maye","B.Purdy"], results:[1,1,1,1,1], note:"NYJ pass rush collapsed after injuries. Opposing QBs averaging 284 yards vs posted 251.", thisWeek:"Check QB opponent vs NYJ this week" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
function americanToDecimal(odds) {
  if (odds > 0) return (odds / 100) + 1;
  return (100 / Math.abs(odds)) + 1;
}
function evPer100(hitRate, odds) {
  const dec  = americanToDecimal(odds);
  const prob = hitRate / 100;
  return Math.round((prob * (dec - 1) * 100) - ((1 - prob) * 100));
}
function quarterKelly(hitRate, odds, bankroll) {
  const dec = americanToDecimal(odds);
  const p   = hitRate / 100;
  const q   = 1 - p;
  const b   = dec - 1;
  const k   = Math.max(0, (p * b - q) / b);
  return Math.round(bankroll * k * 0.25);
}
function oddsStr(o) { return o >= 0 ? "+" + o : "" + o; }
const streakColor = (n) => n >= 10 ? "#f5c518" : n >= 7 ? "#00c896" : "#ffa502";
const streakLabel = (n) => n >= 10 ? "BANNER" : n >= 7 ? "HOT" : "WARM";
const dirColor    = (d) => d === "OVER" ? "#00c896" : "#00e5ff";
const riskColor   = (r) => r === "VERY LOW" ? "#00c896" : r === "LOW" ? "#00e5ff" : "#ffa502";

// ── CSS ───────────────────────────────────────────────────────────────────────
const css = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Barlow:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0a0a0f;color:#e8e8f0;font-family:'Barlow',sans-serif;font-size:14px;}
.mono{font-family:'IBM Plex Mono',monospace;}
.pg{max-width:1040px;margin:0 auto;padding:20px 16px;}
.pg-t{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;margin-bottom:3px;}
.pg-s{font-size:12px;color:#8888a8;margin-bottom:18px;}
.tabs{display:flex;gap:4px;margin-bottom:18px;flex-wrap:wrap;}
.tab{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:6px 14px;border-radius:4px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;}
.tab:hover{color:#e8e8f0;} .tab.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.seclbl{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#8888a8;margin:16px 0 10px;display:flex;align-items:center;gap:10px;}
.seclbl::after{content:'';flex:1;height:1px;background:#2a2a3d;}
.card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-bottom:10px;}
.auto-card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:6px;padding:16px 18px;margin-bottom:10px;}
.auto-card.gold{border:2px solid #f5c51844;background:#f5c51808;}
.auto-card.green{border-left:3px solid #00c896;}
.auto-card.blue{border-left:3px solid #00e5ff;}
.auto-badge{display:inline-flex;align-items:center;gap:5px;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:3px 8px;border-radius:2px;letter-spacing:.04em;margin-bottom:8px;}
.badge-auto{background:#f5c51822;color:#f5c518;border:1px solid #f5c51844;}
.badge-floor{background:#00c89622;color:#00c896;border:1px solid #00c89644;}
.badge-plus{background:#a855f722;color:#a855f7;border:1px solid #a855f744;}
.ev-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0;}
.ev-box{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:10px 12px;}
.ev-lbl{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.ev-val{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:800;line-height:1;}
.ev-sub{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#8888a8;margin-top:3px;}
.cmp-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;}
.cmp-box{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:12px 14px;}
.cmp-title{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:8px;}
.streak-card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-bottom:8px;cursor:pointer;transition:border-color .15s;}
.streak-card:hover{border-color:#3d3d5c;}
.streak-card.banner{border-left:3px solid #f5c518;}
.streak-card.hot{border-left:3px solid #00c896;}
.streak-card.warm{border-left:3px solid #ffa502;}
.dot-row{display:flex;gap:3px;margin-top:6px;}
.dot{width:9px;height:9px;border-radius:50%;}
.dh{background:#00c896;} .dm{background:#ff4757;}
.tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid;margin:2px;}
.tag-g{color:#00c896;background:#00c89612;border-color:#00c89628;}
.tag-a{color:#ffa502;background:#ffa50212;border-color:#ffa50228;}
.tag-b{color:#00e5ff;background:#00e5ff12;border-color:#00e5ff28;}
.tag-p{color:#a855f7;background:#a855f712;border-color:#a855f728;}
.prog-t{height:5px;background:#2a2a3d;border-radius:3px;overflow:hidden;margin-top:4px;}
.prog-f{height:100%;border-radius:3px;}
.risk-pill{font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 7px;border-radius:2px;border:1px solid;}
.sort-row{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center;}
.srt{font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:3px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;}
.srt:hover{color:#e8e8f0;} .srt.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.fsel{padding:5px 10px;border-radius:3px;border:1px solid #2a2a3d;background:#12121a;color:#8888a8;font-size:12px;}
.team-card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-bottom:8px;}
.pos-card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:16px 18px;margin-bottom:12px;}
.pos-card.six{border-left:3px solid #f5c518;}
.pos-card.five{border-left:3px solid #00c896;}
.pos-card.four{border-left:3px solid #ffa502;}
.this-week{background:#00c89618;border:1px solid #00c89633;border-radius:4px;padding:10px 14px;margin-top:10px;font-size:12px;color:#00c896;line-height:1.6;}
.sm-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:10px;}
.sm-box{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:8px 10px;}
.sm-lbl{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:4px;}
.sm-val{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:800;}
.ev-calc-wrap{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-top:12px;}
.inp{background:#0a0a0f;border:1px solid #2a2a3d;border-radius:3px;color:#e8e8f0;font-family:'IBM Plex Mono',monospace;font-size:13px;padding:7px 12px;outline:none;width:100%;}
.inp:focus{border-color:#00e5ff;}
.inp-lbl{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.inp-row{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-bottom:12px;}
.alert-gold{background:#f5c51812;border:1px solid #f5c51833;border-radius:4px;padding:10px 14px;font-size:12px;color:#f5c518;margin-bottom:12px;line-height:1.6;}
.alert-green{background:#00c89612;border:1px solid #00c89633;border-radius:4px;padding:10px 14px;font-size:12px;color:#00c896;margin-bottom:12px;line-height:1.6;}
.var-warn{background:#ff475712;border:1px solid #ff475733;border-radius:4px;padding:10px 14px;font-size:12px;color:#ff4757;margin-top:8px;line-height:1.6;}
`;

// ── Floor EV Calculator ───────────────────────────────────────────────────────
function FloorEVCalc() {
  const [floorOdds,  setFloorOdds]  = useState("-280");
  const [floorHit,   setFloorHit]   = useState("86");
  const [plusOdds,   setPlusOdds]   = useState("150");
  const [plusHit,    setPlusHit]    = useState("58");
  const [bankroll,   setBankroll]   = useState("1000");

  const fo  = parseInt(floorOdds)  || -280;
  const fh  = parseInt(floorHit)   || 86;
  const po  = parseInt(plusOdds)   || 150;
  const ph  = parseInt(plusHit)    || 58;
  const br  = parseInt(bankroll)   || 1000;

  const fEV   = evPer100(fh, fo);
  const pEV   = evPer100(ph, po);
  const fKelly = quarterKelly(fh, fo, br);
  const pKelly = quarterKelly(ph, po, br);

  const fDec   = americanToDecimal(fo);
  const pDec   = americanToDecimal(po);
  const fWin   = (fh/100) * (fDec-1) * 100;
  const fLoss  = (1-fh/100) * 100;
  const pWin   = (ph/100) * (pDec-1) * 100;
  const pLoss  = (1-ph/100) * 100;

  const bust3Floor = Math.pow(1-fh/100, 3) * 100;
  const bust3Plus  = Math.pow(1-ph/100, 3) * 100;

  return (
    <div>
      <div style={{fontSize:13,color:"#8888a8",marginBottom:16,lineHeight:1.7}}>
        Compare a floor play at heavy juice vs a plus-money play at lower probability.
        The math often surprises people — consistent floors compound faster than chasing plus-money.
      </div>

      <div className="inp-row">
        <div>
          <div className="inp-lbl">Floor odds (American)</div>
          <input className="inp" value={floorOdds} onChange={e=>setFloorOdds(e.target.value)} placeholder="-280"/>
        </div>
        <div>
          <div className="inp-lbl">Floor hit rate (%)</div>
          <input className="inp" value={floorHit} onChange={e=>setFloorHit(e.target.value)} placeholder="86"/>
        </div>
        <div>
          <div className="inp-lbl">Plus-money odds</div>
          <input className="inp" value={plusOdds} onChange={e=>setPlusOdds(e.target.value)} placeholder="150"/>
        </div>
        <div>
          <div className="inp-lbl">Plus-money hit rate (%)</div>
          <input className="inp" value={plusHit} onChange={e=>setPlusHit(e.target.value)} placeholder="58"/>
        </div>
      </div>

      <div style={{marginBottom:12}}>
        <div className="inp-lbl">Bankroll ($)</div>
        <input className="inp" style={{maxWidth:200}} value={bankroll} onChange={e=>setBankroll(e.target.value)} placeholder="1000"/>
      </div>

      <div className="cmp-grid">
        <div className="cmp-box" style={{borderColor:"#00e5ff44"}}>
          <div className="cmp-title" style={{color:"#00e5ff"}}>Floor play — {oddsStr(fo)}</div>
          <div className="ev-grid" style={{margin:"0 0 10px"}}>
            {[
              {l:"Hit rate",    v:fh+"%",            c:fh>=85?"#00c896":"#ffa502"},
              {l:"EV / $100",   v:(fEV>=0?"+":"")+fEV, c:fEV>0?"#00c896":"#ff4757"},
              {l:"Qtr Kelly",  v:"$"+fKelly,         c:"#e8e8f0"},
              {l:"3-loss prob", v:bust3Floor.toFixed(1)+"%", c:bust3Floor<5?"#00c896":"#ffa502"},
            ].map(s=>(
              <div className="ev-box" key={s.l}>
                <div className="ev-lbl">{s.l}</div>
                <div className="ev-val" style={{color:s.c,fontSize:16}}>{s.v}</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:12,color:"#8888a8",lineHeight:1.7}}>
            <div>Win: {fh}% × <span style={{color:"#00c896"}}>${fWin.toFixed(2)}</span> = <span style={{color:"#00c896"}}>+${(fh/100*fWin).toFixed(2)}</span></div>
            <div>Loss: {100-fh}% × <span style={{color:"#ff4757"}}>-$100</span> = <span style={{color:"#ff4757"}}>-${((100-fh)/100*100).toFixed(2)}</span></div>
            <div style={{marginTop:4,fontWeight:500,color:fEV>0?"#00c896":"#ff4757"}}>Net EV: {fEV>=0?"+":""}{fEV} per $100 wagered</div>
          </div>
          <div style={{marginTop:8,fontSize:11,color:"#8888a8"}}>
            3 straight losses probability: <span style={{color:bust3Floor<5?"#00c896":"#ffa502"}}>{bust3Floor.toFixed(2)}%</span>
            {bust3Floor < 5 && " — nearly impossible at floor level"}
          </div>
        </div>

        <div className="cmp-box" style={{borderColor:"#a855f744"}}>
          <div className="cmp-title" style={{color:"#a855f7"}}>Plus-money play — +{po}</div>
          <div className="ev-grid" style={{margin:"0 0 10px"}}>
            {[
              {l:"Hit rate",    v:ph+"%",            c:ph>=75?"#00c896":ph>=60?"#ffa502":"#ff4757"},
              {l:"EV / $100",   v:(pEV>=0?"+":"")+pEV, c:pEV>0?"#00c896":"#ff4757"},
              {l:"Qtr Kelly",  v:"$"+pKelly,         c:"#e8e8f0"},
              {l:"3-loss prob", v:bust3Plus.toFixed(1)+"%", c:bust3Plus<15?"#ffa502":"#ff4757"},
            ].map(s=>(
              <div className="ev-box" key={s.l}>
                <div className="ev-lbl">{s.l}</div>
                <div className="ev-val" style={{color:s.c,fontSize:16}}>{s.v}</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:12,color:"#8888a8",lineHeight:1.7}}>
            <div>Win: {ph}% × <span style={{color:"#00c896"}}>${pWin.toFixed(2)}</span> = <span style={{color:"#00c896"}}>+${(ph/100*pWin).toFixed(2)}</span></div>
            <div>Loss: {100-ph}% × <span style={{color:"#ff4757"}}>-$100</span> = <span style={{color:"#ff4757"}}>-${((100-ph)/100*100).toFixed(2)}</span></div>
            <div style={{marginTop:4,fontWeight:500,color:pEV>0?"#00c896":"#ff4757"}}>Net EV: {pEV>=0?"+":""}{pEV} per $100 wagered</div>
          </div>
          <div style={{marginTop:8,fontSize:11,color:"#8888a8"}}>
            3 straight losses probability: <span style={{color:bust3Plus<15?"#ffa502":"#ff4757"}}>{bust3Plus.toFixed(1)}%</span>
            {bust3Plus > 20 && " — real variance risk"}
          </div>
        </div>
      </div>

      <div style={{background:"#12121a",border:"1px solid #2a2a3d",borderRadius:4,padding:"12px 14px",marginTop:12,fontSize:12,lineHeight:1.8}}>
        <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:13,fontWeight:700,textTransform:"uppercase",letterSpacing:".08em",color:"#e8e8f0",marginBottom:6}}>
          What this means
        </div>
        {fEV > 0 && pEV > 0 ? (
          <div style={{color:"#8888a8"}}>
            Both plays are profitable long-term. The floor play ({oddsStr(fo)}) has{" "}
            <span style={{color:"#00e5ff"}}>{fEV > pEV ? "higher" : "lower"}</span> EV per $100 but{" "}
            <span style={{color:"#00c896"}}>dramatically less variance</span>. The floor is your bankroll foundation.
            The plus-money play is your growth layer on top. Use both — size the floor at{" "}
            <span style={{color:"#e8e8f0"}}>${fKelly}</span> and the plus-money at{" "}
            <span style={{color:"#e8e8f0"}}>${pKelly}</span> from a ${br.toLocaleString()} bankroll.
          </div>
        ) : fEV > 0 ? (
          <div style={{color:"#8888a8"}}>
            Only the floor play is EV positive at these numbers. Skip the plus-money play or find one with a higher hit rate.
          </div>
        ) : (
          <div style={{color:"#ff4757"}}>
            Neither play is EV positive at these numbers. Adjust inputs — hit rate may need to be higher or odds better.
          </div>
        )}
      </div>

      <div style={{background:"#12121a",border:"1px solid #2a2a3d",borderRadius:4,padding:"12px 14px",marginTop:10}}>
        <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:".12em",color:"#8888a8",marginBottom:8}}>
          17-week season projection — $100 flat betting
        </div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,fontSize:12}}>
          {[
            {label:"Floor plays (2/week × 17 weeks = 34 bets)", ev:fEV, hit:fh, col:"#00e5ff"},
            {label:"Plus-money plays (1/week × 17 weeks = 17 bets)", ev:pEV, hit:ph, col:"#a855f7"},
          ].map(s=>(
            <div key={s.label}>
              <div style={{fontSize:11,color:"#8888a8",marginBottom:4}}>{s.label}</div>
              <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800,color:s.ev>0?"#00c896":"#ff4757"}}>
                {s.ev>0?"+$":"-$"}{Math.abs(Math.round(s.ev * (s.label.includes("34")?34:17) / 100 * 100))}
              </div>
              <div style={{fontSize:11,color:"#4a4a6a"}}>projected net on $100/bet flat</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Auto-Play Card ────────────────────────────────────────────────────────────
function AutoPlayCard({ p, bankroll }) {
  const [exp, setExp] = useState(false);
  const ev    = evPer100(p.hitRate, p.odds);
  const kelly = quarterKelly(p.hitRate, p.odds, bankroll);
  const isGold = p.odds >= 0;
  const rc     = riskColor(p.risk);

  return (
    <div className={"auto-card " + (isGold ? "gold" : "green")} onClick={()=>setExp(!exp)}>
      {isGold && <div className="auto-badge badge-plus">★ PLUS-MONEY FLOOR — PREMIUM FIND</div>}
      {!isGold && p.streak >= 10 && <div className="auto-badge badge-auto">★ AUTO-PLAY · 10+ GAME STREAK</div>}
      {!isGold && p.streak < 10  && <div className="auto-badge badge-floor">✓ FLOOR PLAY · {p.streak}-GAME STREAK</div>}

      <div style={{display:"grid",gridTemplateColumns:"1fr auto",gap:14,alignItems:"start"}}>
        <div>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4,flexWrap:"wrap"}}>
            <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:18,fontWeight:800}}>{p.player}</span>
            <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:12,color:"#8888a8"}}>{p.team} · {p.pos}</span>
            <span className="risk-pill" style={{color:rc,borderColor:rc+"44",background:rc+"12"}}>Risk: {p.risk}</span>
          </div>
          <div style={{fontSize:14,marginBottom:8}}>
            <span style={{color:dirColor(p.dir),fontWeight:500}}>{p.dir}</span>{" "}
            <span style={{fontFamily:"'IBM Plex Mono',monospace"}}>{p.prop.replace(/OVER |UNDER /,"")}</span>
          </div>
          <div style={{display:"flex",gap:8,flexWrap:"wrap",marginBottom:8}}>
            <span className={"tag "+(p.odds>=0?"tag-p":"tag-g")}>odds: {oddsStr(p.odds)}</span>
            <span className="tag tag-b">hit rate: {p.hitRate}%</span>
            <span className="tag tag-g">ev: {ev>=0?"+":""}{ev} per $100</span>
            <span className="tag tag-a">{p.lineAdj?"line adjusted":"line unchanged ✓"}</span>
          </div>
          <div className="prog-t">
            <div className="prog-f" style={{width:p.hitRate+"%",background:p.hitRate>=90?"#f5c518":p.hitRate>=85?"#00c896":"#ffa502"}}></div>
          </div>
          <div style={{fontSize:10,color:"#8888a8",marginTop:3}}>{p.hitRate}% hit rate · {p.l15}/15 recent · {p.streak} straight</div>
        </div>
        <div style={{textAlign:"right",minWidth:80}}>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:26,fontWeight:800,color:p.odds>=0?"#a855f7":"#00c896"}}>{oddsStr(p.odds)}</div>
          <div style={{fontSize:10,color:"#8888a8"}}>recommended</div>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800,color:"#e8e8f0",marginTop:4}}>${kelly}</div>
          <div style={{fontSize:10,color:"#8888a8"}}>qtr kelly / $1k</div>
          <div style={{fontSize:10,color:"#4a4a6a",marginTop:6}}>{exp?"▲ collapse":"▼ expand"}</div>
        </div>
      </div>

      {exp && (
        <div style={{marginTop:12,borderTop:"1px solid #2a2a3d",paddingTop:12}}>
          <div className="ev-grid">
            {[
              {l:"Avg actual",   v:p.avgActual,   c:"#00c896"},
              {l:"Posted line",  v:p.postedLine,  c:"#e8e8f0"},
              {l:"Floor gap",    v:"+"+(p.avgActual-p.postedLine).toFixed(1), c:"#f5c518"},
              {l:"EV / $100",    v:(ev>=0?"+":"")+ev, c:ev>0?"#00c896":"#ff4757"},
            ].map(s=>(
              <div className="ev-box" key={s.l}>
                <div className="ev-lbl">{s.l}</div>
                <div className="ev-val" style={{color:s.c}}>{s.v}</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:12,color:"#8888a8",lineHeight:1.7,marginBottom:8}}>{p.why}</div>
          <div style={{fontSize:12,color:"#ffa502"}}>{p.gameScript}</div>
        </div>
      )}
    </div>
  );
}

// ── Player Streak Card ────────────────────────────────────────────────────────
function StreakCard({ p, expanded, onToggle }) {
  const sc  = streakColor(p.streak);
  const sl  = streakLabel(p.streak);
  const cls = "streak-card " + (p.streak>=10?"banner":p.streak>=7?"hot":"warm");

  return (
    <div className={cls} onClick={onToggle}>
      <div style={{display:"grid",gridTemplateColumns:"56px 1fr auto",gap:12,alignItems:"start"}}>
        <div style={{textAlign:"center"}}>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:34,fontWeight:800,lineHeight:1,color:sc}}>{p.streak}</div>
          <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:8,color:sc}}>{sl}</div>
        </div>
        <div>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:3,flexWrap:"wrap"}}>
            <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:16,fontWeight:800}}>{p.player}</span>
            <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:11,color:"#8888a8"}}>{p.team} · {p.pos}</span>
          </div>
          <div style={{fontSize:13,marginBottom:6}}>
            <span style={{color:dirColor(p.dir),fontWeight:500}}>{p.dir}</span>{" "}
            <span style={{fontFamily:"'IBM Plex Mono',monospace"}}>{p.prop.replace(/OVER |UNDER /,"")}</span>{" "}
            <span style={{fontSize:11,color:"#8888a8"}}>{oddsStr(p.odds)}</span>
          </div>
          <div className="dot-row">
            {Array.from({length:15},(_,i)=>i<p.l15?1:0).reverse().map((d,i)=>(
              <div key={i} className={"dot "+(d?"dh":"dm")}/>
            ))}
            <span style={{fontSize:10,color:"#8888a8",marginLeft:6}}>{p.l15}/15</span>
          </div>
          {expanded && (
            <div style={{marginTop:10}}>
              <div className="sm-grid">
                {[
                  {l:"Avg actual",  v:p.avgActual,  c:"#00c896"},
                  {l:"Posted line", v:p.postedLine, c:"#e8e8f0"},
                  {l:"Optimal",     v:p.optLine,    c:"#00e5ff"},
                ].map(s=>(
                  <div className="sm-box" key={s.l}>
                    <div className="sm-lbl">{s.l}</div>
                    <div className="sm-val" style={{color:s.c,fontSize:15}}>{s.v}</div>
                  </div>
                ))}
              </div>
              <div style={{fontSize:12,color:"#8888a8",lineHeight:1.7,marginBottom:6}}>{p.note}</div>
              <div style={{fontSize:12,color:"#ffa502"}}>{p.schemeNote}</div>
            </div>
          )}
        </div>
        <div style={{textAlign:"right"}}>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:12,fontWeight:700,color:p.lineAdj?"#ffa502":"#00c896"}}>
            {p.lineAdj?"ADJUSTED":"UNCHANGED"}
          </div>
          <div style={{fontSize:10,color:"#4a4a6a",marginTop:2}}>market line</div>
          <div style={{fontSize:10,color:"#8888a8",marginTop:8}}>{expanded?"▲":"▼"}</div>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function StreakCenter() {
  const [view,      setView]      = useState("auto");
  const [expanded,  setExpanded]  = useState(new Set());
  const [posFilter, setPosFilter] = useState("ALL");
  const [dirFilter, setDirFilter] = useState("ALL");
  const [sortBy,    setSortBy]    = useState("streak");
  const [calcView,  setCalcView]  = useState(false);
  const bankroll = 1000;

  function toggle(key) {
    const n = new Set(expanded);
    Array.from(n).includes(key) ? n.delete(key) : n.add(key);
    setExpanded(n);
  }

  const filtered = PLAYER_STREAKS
    .filter(p => posFilter==="ALL" || p.pos===posFilter)
    .filter(p => dirFilter==="ALL" || p.dir===dirFilter)
    .sort((a,b) =>
      sortBy==="streak" ? b.streak-a.streak :
      sortBy==="l15"    ? b.l15-a.l15 :
      sortBy==="gap"    ? (b.avgActual-b.postedLine)-(a.avgActual-a.postedLine) :
      (a.lineAdj?1:0)-(b.lineAdj?1:0)
    );

  return (
    <div className="pg">
      <style>{css}</style>
      <div className="pg-t">Streak Intelligence Center</div>
      <div className="pg-s">Auto-play floors · Floor EV calculator · Player streaks · Team trends · Position vulnerability</div>

      <div className="tabs">
        {[
          {id:"auto",     l:"Auto-Play Tier"},
          {id:"calc",     l:"Floor EV Calculator"},
          {id:"player",   l:"Player Streaks"},
          {id:"team",     l:"Team Trends"},
          {id:"position", l:"Position Vulnerability"},
        ].map(t=>(
          <button key={t.id} className={"tab"+(view===t.id?" on":"")} onClick={()=>setView(t.id)}>{t.l}</button>
        ))}
      </div>

      {/* AUTO-PLAY TIER */}
      {view==="auto" && (
        <div>
          <div className="alert-gold">
            ★ Auto-play floors meet all 4 criteria: 85%+ hit rate · 8+ game streak · line unadjusted or soft · game script neutral to favorable.
            These are your foundation plays. Size them with Quarter Kelly and let them compound.
          </div>

          {AUTO_PLAYS.filter(p=>p.odds>=0).length > 0 && (
            <>
              <div className="seclbl" style={{color:"#a855f7"}}>Plus-money floors — automatic AND plus odds</div>
              {AUTO_PLAYS.filter(p=>p.odds>=0).map(p=>(
                <AutoPlayCard key={p.player} p={p} bankroll={bankroll}/>
              ))}
            </>
          )}

          <div className="seclbl">Heavy juice floors — auto-play at -200 to -400</div>
          <div className="alert-green">
            These pay less per bet but variance is minimal. 3 straight losses on an 87% play happens{" "}
            {(Math.pow(0.13,3)*100).toFixed(3)}% of the time. Use as your bankroll foundation,
            stack on top of them with plus-money SGPs.
          </div>
          {AUTO_PLAYS.filter(p=>p.odds<0).map(p=>(
            <AutoPlayCard key={p.player} p={p} bankroll={bankroll}/>
          ))}
        </div>
      )}

      {/* FLOOR EV CALCULATOR */}
      {view==="calc" && <FloorEVCalc/>}

      {/* PLAYER STREAKS */}
      {view==="player" && (
        <div>
          {PLAYER_STREAKS.filter(p=>p.streak>=10).length > 0 && (
            <>
              <div className="seclbl" style={{color:"#f5c518"}}>★ Banner alerts — 10+ consecutive</div>
              <div className="alert-gold">
                {PLAYER_STREAKS.filter(p=>p.streak>=10).length} player(s) have hit 10+ straight.
                Market unadjusted on {PLAYER_STREAKS.filter(p=>p.streak>=10&&!p.lineAdj).length} of them.
                Highest-confidence floor plays of the week.
              </div>
              {PLAYER_STREAKS.filter(p=>p.streak>=10).map(p=>(
                <StreakCard key={p.player} p={p} expanded={Array.from(expanded).includes(p.player) === true} onToggle={()=>toggle(p.player)}/>
              ))}
            </>
          )}

          <div className="seclbl" style={{marginTop:20}}>Hot streaks — 6 to 9 consecutive</div>
          <div className="sort-row">
            <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:10,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8"}}>Sort:</span>
            {[{id:"streak",l:"Streak"},{id:"l15",l:"L15 rate"},{id:"gap",l:"Line gap"},{id:"adj",l:"Unadjusted first"}].map(s=>(
              <button key={s.id} className={"srt"+(sortBy===s.id?" on":"")} onClick={()=>setSortBy(s.id)}>{s.l}</button>
            ))}
            <select className="fsel" value={posFilter} onChange={e=>setPosFilter(e.target.value)}>
              <option value="ALL">All positions</option>
              <option value="WR">WR</option><option value="QB">QB</option>
              <option value="RB">RB</option><option value="TE">TE</option>
            </select>
            <select className="fsel" value={dirFilter} onChange={e=>setDirFilter(e.target.value)}>
              <option value="ALL">OVER + UNDER</option>
              <option value="OVER">OVER only</option>
              <option value="UNDER">UNDER only</option>
            </select>
          </div>
          {filtered.filter(p=>p.streak<10).map(p=>(
            <StreakCard key={p.player} p={p} expanded={Array.from(expanded).includes(p.player) === true} onToggle={()=>toggle(p.player)}/>
          ))}
        </div>
      )}

      {/* TEAM TRENDS */}
      {view==="team" && (
        <div>
          <div style={{fontSize:13,color:"#8888a8",marginBottom:16,lineHeight:1.7}}>
            Team-level trends that directly affect player prop opportunities this week.
          </div>
          {["OVER","UNDER"].map(dir=>(
            <div key={dir}>
              <div className="seclbl">{dir} trends</div>
              {TEAM_STREAKS.filter(t=>t.dir===dir).map((t,i)=>(
                <div key={i} className="team-card" style={{borderLeft:"3px solid "+(t.streak>=7?"#00c896":"#ffa502")}}>
                  <div style={{display:"grid",gridTemplateColumns:"48px 1fr auto",gap:12,alignItems:"start"}}>
                    <div style={{textAlign:"center"}}>
                      <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:28,fontWeight:800,color:streakColor(t.streak)}}>{t.streak}</div>
                      <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:8,color:streakColor(t.streak)}}>straight</div>
                    </div>
                    <div>
                      <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:800,marginBottom:3}}>{t.team}</div>
                      <div style={{fontSize:13,marginBottom:6}}>
                        <span style={{color:dirColor(t.dir),fontWeight:500}}>{t.dir}</span>{" "}{t.trend}
                        <span style={{fontSize:11,color:"#8888a8",marginLeft:8}}>({t.context})</span>
                      </div>
                      <div style={{fontSize:12,color:"#8888a8",lineHeight:1.6,marginBottom:8}}>{t.note}</div>
                      <div>
                        {t.impact.split(", ").map(tag=>(
                          <span key={tag} className="tag tag-g">{tag}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      {t.streak>=7
                        ? <span style={{background:"#00c89622",color:"#00c896",border:"1px solid #00c89644",fontFamily:"'IBM Plex Mono',monospace",fontSize:9,padding:"2px 6px",borderRadius:2}}>HOT</span>
                        : <span style={{background:"#ffa50222",color:"#ffa502",border:"1px solid #ffa50244",fontFamily:"'IBM Plex Mono',monospace",fontSize:9,padding:"2px 6px",borderRadius:2}}>WARM</span>
                      }
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* POSITION VULNERABILITY */}
      {view==="position" && (
        <div>
          <div style={{fontSize:13,color:"#8888a8",marginBottom:16,lineHeight:1.7}}>
            When a defense allows the same position group to hit their prop line 4+ straight games,
            every upcoming opponent at that position is a potential edge play.
          </div>
          {POSITION_STREAKS.sort((a,b)=>b.streak-a.streak).map((p,i)=>{
            const cls = "pos-card "+(p.streak>=6?"six":p.streak>=5?"five":"four");
            return (
              <div key={i} className={cls}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
                  <div>
                    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:4,flexWrap:"wrap"}}>
                      <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:18,fontWeight:800}}>{p.pos}</span>
                      <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:14,fontWeight:700,color:"#8888a8"}}>vs {p.vs}</span>
                      <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:10,color:"#ff4757",background:"#ff475718",border:"1px solid #ff475733",padding:"2px 6px",borderRadius:2}}>Def rank #{p.defRank}</span>
                    </div>
                    <div style={{fontSize:13,color:"#8888a8"}}>{p.stat}</div>
                  </div>
                  <div style={{textAlign:"center",minWidth:56}}>
                    <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:30,fontWeight:800,color:streakColor(p.streak)}}>{p.streak}</div>
                    <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:8,color:streakColor(p.streak)}}>straight</div>
                  </div>
                </div>
                <div className="sm-grid">
                  {[
                    {l:"Avg yards allowed", v:p.avgYds,        c:"#ff4757"},
                    {l:"Avg posted line",   v:p.avgPostedLine, c:"#8888a8"},
                    {l:"Market gap",        v:"+"+p.gap.toFixed(1), c:"#f5c518"},
                  ].map(s=>(
                    <div className="sm-box" key={s.l}>
                      <div className="sm-lbl">{s.l}</div>
                      <div className="sm-val" style={{color:s.c}}>{s.v}</div>
                    </div>
                  ))}
                </div>
                <div style={{marginBottom:10}}>
                  <div style={{fontSize:10,color:"#4a4a6a",fontFamily:"'Barlow Condensed',sans-serif",fontWeight:700,letterSpacing:".1em",textTransform:"uppercase",marginBottom:6}}>Recent opponents</div>
                  <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                    {p.players.map((pl,j)=>(
                      <span key={j} style={{fontSize:12,padding:"3px 10px",borderRadius:3,background:p.results[j]?"#00c89618":"#ff475718",border:"1px solid "+(p.results[j]?"#00c89633":"#ff475733"),color:p.results[j]?"#00c896":"#ff4757"}}>
                        {pl}
                      </span>
                    ))}
                  </div>
                </div>
                <div style={{fontSize:12,color:"#8888a8",lineHeight:1.7,marginBottom:10}}>{p.note}</div>
                <div className="this-week">★ This week: {p.thisWeek}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
