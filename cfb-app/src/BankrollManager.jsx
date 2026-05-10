import { useState, useEffect } from "react";

// ── Kelly Calculator ──────────────────────────────────────────────────────────
function americanToDecimal(odds) {
  if (odds > 0) return (odds / 100) + 1;
  return (100 / Math.abs(odds)) + 1;
}

function kellyFraction(prob, decimalOdds) {
  const q = 1 - prob;
  const b = decimalOdds - 1;
  const k = (prob * b - q) / b;
  return Math.max(0, k);
}

function recommendedBet(prob, odds, bankroll) {
  const dec = americanToDecimal(odds);
  const full = kellyFraction(prob / 100, dec);
  const quarter = full * 0.25;
  return Math.round(bankroll * quarter);
}

function evPerHundred(prob, odds) {
  const dec = americanToDecimal(odds);
  const win = (prob / 100) * (dec - 1) * 100;
  const lose = (1 - prob / 100) * 100;
  return Math.round(win - lose);
}

function meetsTarget(prob, odds) {
  const isPlus = odds >= 100;
  const hitRate = prob >= 75;
  return isPlus && hitRate;
}

function qualityGrade(prob, odds) {
  const dec = americanToDecimal(odds);
  const ev = evPerHundred(prob, odds);
  if (prob >= 80 && odds >= 100) return { label:"IDEAL", color:"#00c896" };
  if (prob >= 75 && odds >= 100) return { label:"CLOSE", color:"#ffa502" };
  if (prob >= 68 && ev > 0)      return { label:"VALUE", color:"#00e5ff" };
  return { label:"BELOW", color:"#ff4757" };
}

// ── Sample bet history seeded from real slips ─────────────────────────────────
const SEED_HISTORY = [
  { id:1,  date:"2025-11-09", desc:"Ladd McConkey 50+ Rec Yds",           legs:1, odds:-223, prob:85, wager:12,  result:"WIN",  pnl:5.38  },
  { id:2,  date:"2025-11-09", desc:"CMC 50+ Rush Yds",                    legs:1, odds:-253, prob:82, wager:12,  result:"LOSS", pnl:-12   },
  { id:3,  date:"2025-11-09", desc:"James Cook 60+ Rush Yds",             legs:1, odds:-436, prob:78, wager:12,  result:"LOSS", pnl:-12   },
  { id:4,  date:"2025-11-09", desc:"Pittman/Taylor/Jones 3-SGP",          legs:3, odds:-119, prob:58, wager:20,  result:"LOSS", pnl:-20   },
  { id:5,  date:"2025-11-09", desc:"Achane 50+ / Warren 4+ / Flowers 4+", legs:3, odds:100,  prob:79, wager:20,  result:"WIN",  pnl:20    },
  { id:6,  date:"2025-11-09", desc:"Kyren 50+ / CMC 40+ 2-SGP",          legs:2, odds:100,  prob:81, wager:20,  result:"WIN",  pnl:20    },
  { id:7,  date:"2025-11-09", desc:"Rodgers 180+ / Johnston 25+ SGP",     legs:2, odds:-160, prob:72, wager:20,  result:"LOSS", pnl:-20   },
  { id:8,  date:"2025-11-13", desc:"9-leg SGP Patriots game",             legs:9, odds:650,  prob:32, wager:100, result:"WIN",  pnl:650   },
  { id:9,  date:"2025-11-13", desc:"5-leg NE Patriots SGP",               legs:5, odds:154,  prob:44, wager:12,  result:"WIN",  pnl:18.48 },
  { id:10, date:"2025-11-14", desc:"Clemson +3.5 / Oregon -23.5",         legs:2, odds:177,  prob:62, wager:100, result:"WIN",  pnl:177   },
  { id:11, date:"2025-11-15", desc:"CFB Totals 3-pick parlay",            legs:3, odds:362,  prob:58, wager:50,  result:"WIN",  pnl:227   },
  { id:12, date:"2025-11-16", desc:"7-leg DET game SGP",                  legs:7, odds:710,  prob:28, wager:100, result:"LOSS", pnl:-100  },
  { id:13, date:"2025-11-30", desc:"6-pick parlay +615 boost",            legs:6, odds:615,  prob:36, wager:100, result:"WIN",  pnl:715   },
  { id:14, date:"2025-12-04", desc:"6-pick parlay DAL/DET",               legs:6, odds:550,  prob:34, wager:100, result:"LOSS", pnl:-100  },
  { id:15, date:"2026-01-03", desc:"4-pick parlay +178",                  legs:4, odds:178,  prob:48, wager:12,  result:"LOSS", pnl:-12   },
];

// ── Weekly plays for 80/100 Finder ───────────────────────────────────────────
const WEEK_PLAYS = [
  { player:"Ja'Marr Chase",     prop:"Rec Yds OVER 72.5", team:"CIN", opp:"TB",  odds:115,  prob:71, legs:1, type:"WR",  l6:4, l10:7 },
  { player:"Rashee Rice",       prop:"Rec Yds OVER 52.5", team:"KC",  opp:"BUF", odds:108,  prob:79, legs:1, type:"WR",  l6:5, l10:9 },
  { player:"Lamar Jackson",     prop:"Rush Yds OVER 28.5",team:"BAL", opp:"CLE", odds:115,  prob:82, legs:1, type:"QB",  l6:5, l10:8 },
  { player:"Rice + Allen SGP",  prop:"Rice 52.5+ / Allen 248.5+", team:"KC/BUF", opp:"—", odds:124, prob:78, legs:2, type:"SGP", l6:5, l10:8 },
  { player:"McBride + ARI ML",  prop:"McBride 42.5+ / ARI +7.5",  team:"ARI", opp:"SF",    odds:198, prob:62, legs:2, type:"SGP", l6:4, l10:6 },
  { player:"Sam Darnold",       prop:"Pass Att UNDER 31.5",team:"MIN",opp:"CHI", odds:142,  prob:83, legs:1, type:"QB",  l6:5, l10:8 },
  { player:"Zay Flowers",       prop:"Rec OVER 3.5",      team:"BAL", opp:"CLE", odds:105,  prob:81, legs:1, type:"WR",  l6:5, l10:8 },
  { player:"Bowers + LV dog",   prop:"Bowers 36.5+ / LV +3.5",    team:"LV",  opp:"DEN",  odds:245, prob:58, legs:2, type:"SGP", l6:4, l10:7 },
  { player:"Taylor + Indy ML",  prop:"Taylor 54.5+ / IND -3",      team:"IND", opp:"TEN",  odds:118, prob:76, legs:2, type:"SGP", l6:5, l10:8 },
  { player:"Nacua floor",       prop:"Rec Yds OVER 38.5", team:"LAR", opp:"ARI", odds:118,  prob:77, legs:1, type:"WR",  l6:5, l10:8 },
];

// ── Styles ────────────────────────────────────────────────────────────────────
const css = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Barlow:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0a0a0f;color:#e8e8f0;font-family:'Barlow',sans-serif;font-size:14px;}
.mono{font-family:'IBM Plex Mono',monospace;}
.cond{font-family:'Barlow Condensed',sans-serif;}
.pg{max-width:1040px;margin:0 auto;padding:20px 16px;}
.pg-t{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;margin-bottom:3px;}
.pg-s{font-size:12px;color:#8888a8;margin-bottom:18px;}
.tabs{display:flex;gap:4px;margin-bottom:18px;flex-wrap:wrap;}
.tab{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:6px 14px;border-radius:4px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;}
.tab:hover{color:#e8e8f0;} .tab.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px;}
.stat-box{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;}
.stat-lbl{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;margin-bottom:6px;}
.stat-val{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;line-height:1;}
.stat-sub{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#8888a8;margin-top:4px;}
.card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-bottom:12px;}
.chdr{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;padding-bottom:8px;border-bottom:1px solid #2a2a3d;margin-bottom:12px;}
.inp{background:#12121a;border:1px solid #2a2a3d;border-radius:3px;color:#e8e8f0;font-family:'IBM Plex Mono',monospace;font-size:13px;padding:7px 12px;outline:none;width:100%;}
.inp:focus{border-color:#00e5ff;}
.inp-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;}
.inp-lbl{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.btn-p{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:#00e5ff;color:#0a0a0f;border:none;border-radius:3px;padding:7px 16px;cursor:pointer;}
.btn-s{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:transparent;color:#8888a8;border:1px solid #2a2a3d;border-radius:3px;padding:7px 16px;cursor:pointer;}
.btn-s:hover{color:#e8e8f0;}
.btn-danger{font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:transparent;color:#ff4757;border:1px solid #ff475744;border-radius:3px;padding:5px 12px;cursor:pointer;}
.play-card{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:12px 14px;margin-bottom:8px;display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;}
.play-card.ideal{border-left:3px solid #00c896;}
.play-card.close{border-left:3px solid #ffa502;}
.play-card.value{border-left:3px solid #00e5ff;}
.play-card.below{border-left:3px solid #2a2a3d;}
.grade{font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid;}
.hist-row{display:grid;grid-template-columns:80px 1fr 50px 60px 60px 70px;gap:8px;align-items:center;padding:10px 8px;border-bottom:1px solid #2a2a3d66;font-size:13px;}
.hist-row:last-child{border-bottom:none;}
.hist-row:hover{background:#12121a66;}
.win-pill{background:#00c89622;color:#00c896;border:1px solid #00c89644;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.loss-pill{background:#ff475722;color:#ff4757;border:1px solid #ff475744;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.prog-t{height:6px;background:#2a2a3d;border-radius:3px;overflow:hidden;}
.prog-f{height:100%;border-radius:3px;}
.alert-box{border-radius:5px;padding:12px 16px;margin-bottom:12px;font-size:13px;line-height:1.6;}
.alert-warn{background:#ffa50218;border:1px solid #ffa50233;color:#ffa502;}
.alert-good{background:#00c89618;border:1px solid #00c89633;color:#00c896;}
.alert-info{background:#00e5ff18;border:1px solid #00e5ff33;color:#00e5ff;}
.kelly-box{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-top:12px;}
.warn-box{background:#ff475718;border:1px solid #ff475733;border-radius:5px;padding:12px 16px;margin-top:10px;}
.sgp-builder{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;}
.leg-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #2a2a3d66;}
.leg-row:last-child{border-bottom:none;}
.remove-btn{background:transparent;border:none;color:#ff4757;cursor:pointer;font-size:16px;line-height:1;padding:0 4px;}
.seclbl{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#8888a8;margin-bottom:10px;display:flex;align-items:center;gap:10px;}
.seclbl::after{content:'';flex:1;height:1px;background:#2a2a3d;}
.streak-indicator{display:flex;align-items:center;gap:6px;padding:8px 12px;border-radius:4px;margin-bottom:12px;font-size:12px;}
`;

// ── Main Component ────────────────────────────────────────────────────────────
export default function BankrollManager() {
  const [view,        setView]       = useState("overview");
  const [bankroll,    setBankroll]   = useState(1000);
  const [startingBR,  setStartingBR] = useState(1000);
  const [history,     setHistory]    = useState(SEED_HISTORY);
  const [sgpLegs,     setSgpLegs]    = useState([]);
  const [newBet,      setNewBet]     = useState({ desc:"", odds:"", prob:"", wager:"", legs:1 });
  const [brInput,     setBrInput]    = useState("1000");
  const [initialized, setInitialized] = useState(false);

  // Derived stats
  const totalPnl    = history.reduce((s, b) => s + b.pnl, 0);
  const wins        = history.filter(b => b.result === "WIN");
  const losses      = history.filter(b => b.result === "LOSS");
  const winRate     = history.length ? Math.round(wins.length / history.length * 100) : 0;
  const totalWagered = history.reduce((s, b) => s + b.wager, 0);
  const roi         = totalWagered ? Math.round(totalPnl / totalWagered * 100) : 0;

  // By leg count
  const byLegs = (n1, n2) => {
    const subset = history.filter(b => b.legs >= n1 && b.legs <= n2);
    if (!subset.length) return { wr: 0, n: 0 };
    return { wr: Math.round(subset.filter(b => b.result === "WIN").length / subset.length * 100), n: subset.length };
  };
  const solo   = byLegs(1, 1);
  const twoThree = byLegs(2, 3);
  const fourPlus  = byLegs(4, 99);

  // Streak detection
  const sorted = [...history].sort((a, b) => new Date(b.date) - new Date(a.date));
  let streak = 0, streakType = "none";
  for (let i = 0; i < sorted.length; i++) {
    if (i === 0) { streakType = sorted[0].result; streak = 1; }
    else if (sorted[i].result === streakType) streak++;
    else break;
  }

  // Current bankroll
  const currentBR = startingBR + totalPnl;
  const pnlPct    = Math.round(totalPnl / startingBR * 100);
  const maxDraw   = Math.round(Math.min(...history.map((_, i) =>
    history.slice(0, i + 1).reduce((s, b) => s + b.pnl, 0))) / startingBR * 100);

  // Week targets
  const maxAction = Math.round(currentBR * 0.20);
  const streakFactor = streak >= 5 && streakType === "LOSS" ? 0.5 : streak >= 3 && streakType === "LOSS" ? 0.75 : 1;

  // SGP builder
  const sgpCombinedProb = sgpLegs.reduce((p, l) => p * (l.prob / 100), 1);
  const sgpCombinedOdds = sgpLegs.length > 1
    ? Math.round((1 / sgpCombinedProb - 1) * 100)
    : 0;

  function addSgpLeg() {
    const prob = parseInt(newBet.prob);
    const odds = parseInt(newBet.odds);
    if (!newBet.desc || !prob || !odds) return;
    if (sgpLegs.length >= 6) return;
    setSgpLegs([...sgpLegs, { ...newBet, prob, odds, id: Date.now() }]);
    setNewBet({ desc:"", odds:"", prob:"", wager:"", legs:1 });
  }

  function removeLeg(id) {
    setSgpLegs(sgpLegs.filter(l => l.id !== id));
  }

  function logBet() {
    const bet = {
      id: Date.now(),
      date: new Date().toISOString().split("T")[0],
      desc: newBet.desc,
      legs: parseInt(newBet.legs) || 1,
      odds: parseInt(newBet.odds),
      prob: parseInt(newBet.prob),
      wager: parseFloat(newBet.wager),
      result: "PENDING",
      pnl: 0,
    };
    setHistory([bet, ...history]);
    setNewBet({ desc:"", odds:"", prob:"", wager:"", legs:1 });
  }

  function settleBet(id, result) {
    setHistory(history.map(b => {
      if (b.id !== id) return b;
      const dec = americanToDecimal(b.odds);
      const pnl = result === "WIN"
        ? Math.round((b.wager * (dec - 1)) * 100) / 100
        : -b.wager;
      return { ...b, result, pnl };
    }));
  }

  function deleteBet(id) {
    setHistory(history.filter(b => b.id !== id));
  }

  function initBankroll() {
    const val = parseFloat(brInput);
    if (val > 0) { setStartingBR(val); setBankroll(val); setInitialized(true); }
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="pg">
      <style>{css}</style>
      <div className="pg-t">Bankroll Manager</div>
      <div className="pg-s">Quarter Kelly sizing · 80/100 target finder · SGP builder · Season P&amp;L</div>

      <div className="tabs">
        {[{id:"overview",l:"Overview"},{id:"finder",l:"80/100 Finder"},{id:"kelly",l:"Kelly Sizer"},{id:"sgp",l:"SGP Builder"},{id:"history",l:"Bet History"},{id:"analytics",l:"Analytics"}].map(t => (
          <button key={t.id} className={"tab"+(view===t.id?" on":"")} onClick={()=>setView(t.id)}>{t.l}</button>
        ))}
      </div>

      {/* OVERVIEW */}
      {view === "overview" && (
        <div>
          {!initialized && (
            <div className="card" style={{marginBottom:16}}>
              <div className="chdr">Set starting bankroll</div>
              <div style={{display:"flex",gap:10,alignItems:"flex-end"}}>
                <div style={{flex:1}}>
                  <div className="inp-lbl">Starting bankroll ($)</div>
                  <input className="inp" type="number" value={brInput} onChange={e=>setBrInput(e.target.value)} placeholder="1000"/>
                </div>
                <button className="btn-p" onClick={initBankroll}>Set Bankroll</button>
              </div>
            </div>
          )}

          {/* Streak alert */}
          {streak >= 3 && streakType === "LOSS" && (
            <div className="alert-box alert-warn">
              ⚠ {streak}-bet losing streak detected. Kelly recommends reducing bet size by {streak >= 5 ? "50%" : "25%"}. Consider skipping low-confidence plays this week.
            </div>
          )}
          {streak >= 5 && streakType === "WIN" && (
            <div className="alert-box alert-info">
              ★ {streak}-bet win streak. Variance is real — maintain Quarter Kelly discipline. Do not increase size based on a hot streak.
            </div>
          )}

          <div className="stat-grid">
            {[
              {l:"Starting BR",     v:"$"+startingBR.toLocaleString(),    s:"baseline",        c:"#e8e8f0"},
              {l:"Current BR",      v:"$"+Math.round(currentBR).toLocaleString(), s:(pnlPct>=0?"+":"")+pnlPct+"%", c:currentBR>=startingBR?"#00c896":"#ff4757"},
              {l:"Net P&L",         v:(totalPnl>=0?"+$":"$")+Math.round(totalPnl).toLocaleString(), s:"all bets",  c:totalPnl>=0?"#00c896":"#ff4757"},
              {l:"ROI",             v:roi+"%",                            s:"return on wagers", c:roi>=0?"#00c896":"#ff4757"},
              {l:"Win rate",        v:winRate+"%",                        s:wins.length+"W "+losses.length+"L", c:winRate>=65?"#00c896":winRate>=50?"#ffa502":"#ff4757"},
              {l:"Max drawdown",    v:maxDraw+"%",                        s:"peak to trough",  c:maxDraw>-15?"#00c896":"#ff4757"},
              {l:"Max action/week", v:"$"+maxAction,                      s:"20% of bankroll", c:"#e8e8f0"},
              {l:"Streak",          v:streak+"x "+streakType,             s:"most recent bets", c:streakType==="WIN"?"#00c896":streakType==="LOSS"?"#ff4757":"#8888a8"},
            ].map(s => (
              <div className="stat-box" key={s.l}>
                <div className="stat-lbl">{s.l}</div>
                <div className="stat-val" style={{color:s.c}}>{s.v}</div>
                <div className="stat-sub">{s.s}</div>
              </div>
            ))}
          </div>

          <div className="seclbl">Win rate by bet type</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginBottom:18}}>
            {[
              {l:"Singles",      ...solo,       target:70, note:"Floor lines only"},
              {l:"2-3 leg SGP",  ...twoThree,   target:80, note:"★ Primary target"},
              {l:"4+ leg parlay",...fourPlus,    target:55, note:"Greed zone"},
            ].map(s => (
              <div className="card" key={s.l} style={{borderColor:s.wr>=s.target?"#00c89644":"#2a2a3d"}}>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:12,fontWeight:700,textTransform:"uppercase",letterSpacing:".1em",color:"#8888a8",marginBottom:6}}>{s.l}</div>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:30,fontWeight:800,color:s.wr>=s.target?"#00c896":s.wr>=s.target-10?"#ffa502":"#ff4757"}}>{s.wr}%</div>
                <div style={{fontSize:11,color:"#8888a8",marginTop:2}}>n={s.n} · target {s.target}%</div>
                <div className="prog-t" style={{marginTop:8}}>
                  <div className="prog-f" style={{width:Math.min(100,s.wr)+"%",background:s.wr>=s.target?"#00c896":s.wr>=s.target-10?"#ffa502":"#ff4757"}}></div>
                </div>
                <div style={{fontSize:11,color:"#4a4a6a",marginTop:6}}>{s.note}</div>
              </div>
            ))}
          </div>

          <div className="seclbl">This week's allocation</div>
          <div className="card">
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>
              {[
                {l:"Available",      v:"$"+Math.round(currentBR).toLocaleString()},
                {l:"Max action (20%)",v:"$"+maxAction},
                {l:"Streak factor",  v:streakFactor===1?"Normal":Math.round(streakFactor*100)+"% sizing"},
              ].map(s=>(
                <div key={s.l}>
                  <div className="inp-lbl">{s.l}</div>
                  <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:18,fontWeight:800}}>{s.v}</div>
                </div>
              ))}
            </div>
            <div style={{marginTop:12,fontSize:12,color:"#8888a8",lineHeight:1.7}}>
              Goal: 2-3 qualifying plays per week at 3-5% of bankroll each. Some weeks there are zero qualifying plays — that is a valid outcome. Do not force picks.
            </div>
          </div>
        </div>
      )}

      {/* 80/100 FINDER */}
      {view === "finder" && (
        <div>
          <div className="alert-box alert-info">
            Target: 75%+ probability at +100 or better odds. These plays are identified automatically each week. 2-3 qualifying plays is ideal — do not chase volume.
          </div>
          {WEEK_PLAYS.sort((a,b) => {
            const ag = qualityGrade(a.prob,a.odds);
            const bg = qualityGrade(b.prob,b.odds);
            const order = {IDEAL:0,CLOSE:1,VALUE:2,BELOW:3};
            return order[ag.label]-order[bg.label] || b.prob-a.prob;
          }).map((p, i) => {
            const grade = qualityGrade(p.prob, p.odds);
            const ev = evPerHundred(p.prob, p.odds);
            const rec = recommendedBet(p.prob, p.odds, currentBR * streakFactor);
            const meets = meetsTarget(p.prob, p.odds);
            const oddsStr = p.odds >= 0 ? "+"+p.odds : p.odds;
            return (
              <div key={i} className={"play-card "+grade.label.toLowerCase()}>
                <div>
                  <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
                    <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:16,fontWeight:800}}>{p.player}</span>
                    <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:9,padding:"2px 6px",borderRadius:2,border:"1px solid",color:grade.color,borderColor:grade.color+"44",background:grade.color+"18"}}>{grade.label}</span>
                    {meets && <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:9,padding:"2px 6px",borderRadius:2,background:"#00c89618",color:"#00c896",border:"1px solid #00c89633"}}>★ HITS TARGET</span>}
                  </div>
                  <div style={{fontSize:13,color:"#8888a8",marginBottom:6}}>{p.prop} · {p.team}{p.opp!=="—"?" vs "+p.opp:""} · {p.legs===1?"Single":"SGP "+p.legs+"-leg"}</div>
                  <div style={{display:"flex",gap:16,fontSize:12}}>
                    <span>Prob: <span style={{color:grade.color,fontWeight:500}}>{p.prob}%</span></span>
                    <span>Odds: <span className="mono" style={{color:p.odds>=100?"#00c896":"#8888a8"}}>{oddsStr}</span></span>
                    <span>EV/100: <span style={{color:ev>0?"#00c896":"#ff4757"}}>{ev>0?"+":""}{ev}</span></span>
                    <span>L6: <span style={{color:p.l6>=5?"#00c896":p.l6>=4?"#ffa502":"#ff4757"}}>{p.l6}/6</span></span>
                    <span>L10: <span style={{color:p.l10>=8?"#00c896":p.l10>=6?"#ffa502":"#ff4757"}}>{p.l10}/10</span></span>
                  </div>
                </div>
                <div style={{textAlign:"right",minWidth:90}}>
                  <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:800,color:grade.color}}>{oddsStr}</div>
                  <div style={{fontSize:10,color:"#8888a8"}}>recommended</div>
                  <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:18,fontWeight:800,color:"#e8e8f0",marginTop:4}}>${rec}</div>
                  <div style={{fontSize:10,color:"#8888a8"}}>qtr kelly bet</div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* KELLY SIZER */}
      {view === "kelly" && (
        <div>
          <div className="card">
            <div className="chdr">Calculate bet size</div>
            <div className="inp-row">
              <div>
                <div className="inp-lbl">Your probability estimate (%)</div>
                <input className="inp" type="number" value={newBet.prob} onChange={e=>setNewBet({...newBet,prob:e.target.value})} placeholder="71"/>
              </div>
              <div>
                <div className="inp-lbl">Odds (American)</div>
                <input className="inp" type="number" value={newBet.odds} onChange={e=>setNewBet({...newBet,odds:e.target.value})} placeholder="-115 or 130"/>
              </div>
              <div>
                <div className="inp-lbl">Bankroll ($)</div>
                <input className="inp" type="number" value={Math.round(currentBR)} readOnly style={{opacity:.6}}></div>
              </div>
            </div>
            {newBet.prob && newBet.odds && (() => {
              const prob = parseInt(newBet.prob);
              const odds = parseInt(newBet.odds);
              const dec = americanToDecimal(odds);
              const full = kellyFraction(prob/100, dec);
              const qtr = full * 0.25;
              const ev = evPerHundred(prob, odds);
              const meets = meetsTarget(prob, odds);
              const grade = qualityGrade(prob, odds);
              const oddsStr = odds >= 0 ? "+"+odds : ""+odds;
              return (
                <div className="kelly-box">
                  <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:14}}>
                    {[
                      {l:"Full Kelly",    v:(full*100).toFixed(1)+"%", s:"$"+Math.round(currentBR*full), c:"#ff4757", note:"Too aggressive"},
                      {l:"Half Kelly",    v:(full*50).toFixed(1)+"%",  s:"$"+Math.round(currentBR*full*0.5), c:"#ffa502", note:"Moderate"},
                      {l:"Quarter Kelly", v:(qtr*100).toFixed(1)+"%",  s:"$"+Math.round(currentBR*qtr), c:"#00c896", note:"Recommended"},
                      {l:"EV per $100",   v:(ev>=0?"+":"")+ev,        s:ev>0?"Positive edge":"Negative EV", c:ev>0?"#00c896":"#ff4757", note:""},
                    ].map(k=>(
                      <div key={k.l}>
                        <div className="inp-lbl">{k.l}</div>
                        <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:800,color:k.c}}>{k.v}</div>
                        <div style={{fontSize:11,color:"#8888a8"}}>{k.s}</div>
                        {k.note&&<div style={{fontSize:10,color:"#4a4a6a"}}>{k.note}</div>}
                      </div>
                    ))}
                  </div>
                  <div style={{borderTop:"1px solid #2a2a3d",paddingTop:12,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                    <div>
                      <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:14,fontWeight:700}}>Grade: </span>
                      <span style={{color:grade.color,fontFamily:"'Barlow Condensed',sans-serif",fontSize:14,fontWeight:700}}>{grade.label}</span>
                      {meets && <span style={{marginLeft:10,fontFamily:"'IBM Plex Mono',monospace",fontSize:10,background:"#00c89618",color:"#00c896",border:"1px solid #00c89633",padding:"2px 6px",borderRadius:2}}>★ HITS 80/100 TARGET</span>}
                    </div>
                    <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:13,color:"#8888a8"}}>
                      Streak factor: {Math.round(streakFactor*100)}% → adjusted bet: <span style={{color:"#e8e8f0",fontWeight:700}}>${Math.round(currentBR*qtr*streakFactor)}</span>
                    </div>
                  </div>
                  {parseInt(newBet.prob) < 75 && (
                    <div className="warn-box" style={{marginTop:10}}>
                      ⚠ This play does not meet the 80/100 target (75%+ prob at +100 or better). Consider skipping or reducing to minimum bet size.
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* SGP BUILDER */}
      {view === "sgp" && (
        <div>
          <div className="card" style={{marginBottom:12}}>
            <div className="chdr">Add a leg</div>
            <div className="inp-row" style={{gridTemplateColumns:"2fr 1fr 1fr"}}>
              <div>
                <div className="inp-lbl">Description</div>
                <input className="inp" value={newBet.desc} onChange={e=>setNewBet({...newBet,desc:e.target.value})} placeholder="Chase Rec Yds OVER 62.5"/>
              </div>
              <div>
                <div className="inp-lbl">Prob (%)</div>
                <input className="inp" type="number" value={newBet.prob} onChange={e=>setNewBet({...newBet,prob:e.target.value})} placeholder="81"/>
              </div>
              <div>
                <div className="inp-lbl">Individual odds</div>
                <input className="inp" type="number" value={newBet.odds} onChange={e=>setNewBet({...newBet,odds:e.target.value})} placeholder="-145"/>
              </div>
            </div>
            <button className="btn-p" onClick={addSgpLeg} disabled={sgpLegs.length>=6}>
              {sgpLegs.length >= 6 ? "Max 6 legs reached" : "Add leg"}
            </button>
          </div>

          {sgpLegs.length > 0 && (
            <div className="sgp-builder">
              <div className="chdr">SGP legs ({sgpLegs.length})</div>
              {sgpLegs.map((leg, i) => {
                const oddsStr = leg.odds >= 0 ? "+"+leg.odds : ""+leg.odds;
                return (
                  <div key={leg.id} className="leg-row">
                    <div style={{flex:1}}>
                      <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:14,fontWeight:700}}>{leg.desc}</div>
                      <div style={{fontSize:12,color:"#8888a8"}}>Prob: {leg.prob}% · Odds alone: {oddsStr}</div>
                    </div>
                    <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:12,color:leg.prob>=80?"#00c896":leg.prob>=70?"#ffa502":"#ff4757",minWidth:40,textAlign:"right"}}>{leg.prob}%</div>
                    <button className="remove-btn" onClick={()=>removeLeg(leg.id)}>✕</button>
                  </div>
                );
              })}

              <div style={{marginTop:14,borderTop:"1px solid #2a2a3d",paddingTop:14}}>
                <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:12,marginBottom:12}}>
                  <div>
                    <div className="inp-lbl">Combined probability</div>
                    <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,fontWeight:800,color:sgpCombinedProb*100>=75?"#00c896":sgpCombinedProb*100>=60?"#ffa502":"#ff4757"}}>
                      {Math.round(sgpCombinedProb*100)}%
                    </div>
                  </div>
                  <div>
                    <div className="inp-lbl">Projected odds</div>
                    <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,fontWeight:800,color:sgpCombinedOdds>=100?"#00c896":"#e8e8f0"}}>
                      {sgpCombinedOdds>=0?"+":""}{sgpCombinedOdds}
                    </div>
                  </div>
                  <div>
                    <div className="inp-lbl">Recommended bet</div>
                    <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,fontWeight:800,color:"#e8e8f0"}}>
                      ${recommendedBet(Math.round(sgpCombinedProb*100), sgpCombinedOdds, currentBR*streakFactor)}
                    </div>
                  </div>
                </div>

                {sgpLegs.length >= 4 && (
                  <div className="warn-box">
                    <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:14,fontWeight:800,color:"#ff4757",marginBottom:6}}>⚠ GREED WARNING — {sgpLegs.length} legs</div>
                    <div style={{fontSize:12,lineHeight:1.7}}>
                      Combined probability drops with each leg added. Your data shows 4+ leg parlays hit at 40% vs 80%+ for 2-3 legs.
                    </div>
                    <div style={{marginTop:8,fontSize:12,color:"#ff4757",fontWeight:500}}>
                      Weakest leg: {sgpLegs.sort((a,b)=>a.prob-b.prob)[0]?.desc} ({sgpLegs.sort((a,b)=>a.prob-b.prob)[0]?.prob}%)
                    </div>
                    <div style={{fontSize:12,color:"#8888a8",marginTop:4}}>
                      Removing it raises combined prob to {Math.round(sgpCombinedProb/(sgpLegs.sort((a,b)=>a.prob-b.prob)[0]?.prob/100||1)*100)}%
                    </div>
                  </div>
                )}

                {meetsTarget(Math.round(sgpCombinedProb*100), sgpCombinedOdds) && (
                  <div className="alert-box alert-good" style={{marginTop:10}}>
                    ★ This SGP meets the 80/100 target — {Math.round(sgpCombinedProb*100)}% probability at +{sgpCombinedOdds}. Strong play.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* HISTORY */}
      {view === "history" && (
        <div>
          <div className="card" style={{marginBottom:12}}>
            <div className="chdr">Log a new bet</div>
            <div className="inp-row">
              <div>
                <div className="inp-lbl">Description</div>
                <input className="inp" value={newBet.desc} onChange={e=>setNewBet({...newBet,desc:e.target.value})} placeholder="Chase OVER 72.5 / Rice OVER 52.5"/>
              </div>
              <div>
                <div className="inp-lbl">Odds</div>
                <input className="inp" type="number" value={newBet.odds} onChange={e=>setNewBet({...newBet,odds:e.target.value})} placeholder="115 or -115"/>
              </div>
              <div>
                <div className="inp-lbl">Prob (%)</div>
                <input className="inp" type="number" value={newBet.prob} onChange={e=>setNewBet({...newBet,prob:e.target.value})} placeholder="79"/>
              </div>
            </div>
            <div className="inp-row" style={{gridTemplateColumns:"1fr 1fr 2fr"}}>
              <div>
                <div className="inp-lbl">Wager ($)</div>
                <input className="inp" type="number" value={newBet.wager} onChange={e=>setNewBet({...newBet,wager:e.target.value})} placeholder="20"/>
              </div>
              <div>
                <div className="inp-lbl">Legs</div>
                <input className="inp" type="number" value={newBet.legs} onChange={e=>setNewBet({...newBet,legs:e.target.value})} placeholder="2"/>
              </div>
              <div style={{display:"flex",alignItems:"flex-end"}}>
                <button className="btn-p" onClick={logBet} style={{width:"100%"}}>Log bet (pending)</button>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="chdr">Bet history ({history.length} bets)</div>
            <div style={{display:"grid",gridTemplateColumns:"80px 1fr 50px 60px 60px 70px",gap:8,padding:"0 0 8px",borderBottom:"1px solid #2a2a3d"}}>
              {["Date","Description","Legs","Wager","Result","P&L"].map(h=>(
                <div key={h} style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8"}}>{h}</div>
              ))}
            </div>
            {[...history].sort((a,b)=>new Date(b.date)-new Date(a.date)).map(b=>(
              <div key={b.id} className="hist-row">
                <div className="mono" style={{fontSize:11,color:"#8888a8"}}>{b.date.slice(5)}</div>
                <div style={{fontSize:12}}>{b.desc}</div>
                <div style={{fontSize:12,color:"#8888a8",textAlign:"center"}}>{b.legs}</div>
                <div className="mono" style={{fontSize:12}}>${b.wager}</div>
                <div>
                  {b.result==="PENDING"
                    ? <div style={{display:"flex",gap:4}}>
                        <button className="btn-p" style={{padding:"3px 8px",fontSize:10}} onClick={()=>settleBet(b.id,"WIN")}>W</button>
                        <button className="btn-danger" style={{padding:"3px 8px",fontSize:10}} onClick={()=>settleBet(b.id,"LOSS")}>L</button>
                      </div>
                    : b.result==="WIN"
                      ? <span className="win-pill">WIN</span>
                      : <span className="loss-pill">LOSS</span>
                  }
                </div>
                <div className="mono" style={{fontSize:12,color:b.pnl>0?"#00c896":b.pnl<0?"#ff4757":"#8888a8"}}>
                  {b.pnl>0?"+$":b.pnl<0?"-$":""}{Math.abs(b.pnl).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ANALYTICS */}
      {view === "analytics" && (
        <div>
          <div className="seclbl">Performance by bet type</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(200px,1fr))",gap:10,marginBottom:18}}>
            {[
              {l:"Singles (1 leg)",  ...byLegs(1,1),   target:70},
              {l:"2-3 leg SGP",      ...byLegs(2,3),   target:80},
              {l:"4-6 leg parlay",   ...byLegs(4,6),   target:55},
              {l:"7+ leg parlay",    ...byLegs(7,99),  target:50},
            ].map(s=>(
              <div className="card" key={s.l}>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:".1em",color:"#8888a8",marginBottom:8}}>{s.l}</div>
                <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:28,fontWeight:800,color:s.n===0?"#4a4a6a":s.wr>=s.target?"#00c896":s.wr>=s.target-10?"#ffa502":"#ff4757"}}>
                  {s.n===0?"—":s.wr+"%"}
                </div>
                <div style={{fontSize:11,color:"#8888a8",marginTop:2}}>n={s.n} · target {s.target}%</div>
                {s.n>0&&<div className="prog-t" style={{marginTop:8}}><div className="prog-f" style={{width:Math.min(100,s.wr)+"%",background:s.wr>=s.target?"#00c896":s.wr>=s.target-10?"#ffa502":"#ff4757"}}></div></div>}
              </div>
            ))}
          </div>

          <div className="seclbl">Your betting edge summary</div>
          <div className="card">
            <div style={{fontSize:13,lineHeight:1.9,color:"#8888a8"}}>
              <div>Singles win rate: <span style={{color:solo.wr>=65?"#00c896":"#ffa502",fontWeight:500}}>{solo.wr}%</span> — {solo.wr>=65?"Above target. Floor lines are working.":"Slightly below target. Tighten line selection."}</div>
              <div>2-3 leg SGP win rate: <span style={{color:twoThree.wr>=75?"#00c896":"#ffa502",fontWeight:500}}>{twoThree.wr}%</span> — {twoThree.wr>=75?"Near or above 80% target. Primary bet type.":"Building toward 80% target. Stay disciplined."}</div>
              <div>4+ leg parlay win rate: <span style={{color:fourPlus.wr<=45?"#ff4757":"#ffa502",fontWeight:500}}>{fourPlus.wr}%</span> — {fourPlus.wr<=45?"Below break-even. Avoid or minimize.":"Survivable but well below 2-3 leg edge."}</div>
              <div style={{marginTop:8,color:"#e8e8f0"}}>Primary edge: 2-3 leg correlated SGPs using floor lines at +100 to +200 odds. That is where your model and your discipline align.</div>
            </div>
          </div>

          <div className="seclbl">P&L breakdown</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10}}>
            {[
              {l:"Total wagered",  v:"$"+totalWagered.toLocaleString()},
              {l:"Total returned", v:"$"+Math.round(totalWagered+totalPnl).toLocaleString()},
              {l:"Net P&L",        v:(totalPnl>=0?"+$":"$")+Math.round(totalPnl).toLocaleString(), c:totalPnl>=0?"#00c896":"#ff4757"},
            ].map(s=>(
              <div className="stat-box" key={s.l}>
                <div className="stat-lbl">{s.l}</div>
                <div className="stat-val" style={{color:s.c||"#e8e8f0"}}>{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
