import { useState } from "react";
// v2026-08-20 — NFL weekly card. Paper trial, 2026 season.

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

// BASEMENT = projection sits well above the line, priced heavy.
// PLAY     = ordinary edge.
// REVIEW   = disagreement large enough that we distrust ourselves, not the book.
const VERDICT_CFG = {
  BASEMENT:{color:"#00ff88",bg:"#00ff8818",border:"#00ff8840",icon:"▼"},
  PLAY:    {color:"#00e5ff",bg:"#00e5ff18",border:"#00e5ff40",icon:"◆"},
  REVIEW:  {color:"#f5c518",bg:"#f5c51818",border:"#f5c51840",icon:"?"},
};

// >>> AUTO-GENERATED WEEK BEGIN — do not edit between markers
const WEEK = {
  season: 2026,
  week: 1,
  posted: "2026-09-08",
  clv_avg: null,          // points, filled after closing capture
  legs_logged: 0,
  slope: 1.055,           // held-out 2025 backtest
  stake: 0,
};

const CALIBRATION = [
  { stated: 0.746, actual: 0.758 },
  { stated: 0.851, actual: 0.857 },
  { stated: 0.937, actual: 0.931 },
];

const PICKS = [
  { player:"Garrett Wilson", team:"NYJ", prop:"receptions", line:2.5, side:"over",
    odds:-410, proj:6.23, sd:2.61, model:0.894, implied:0.804, edge:9.0,
    daylight:1.43, verdict:"BASEMENT", need:4.97,
    why:"All 11 first-drive snaps in the preseason opener.",
    flags:[] },
  { player:"Jerry Jeudy", team:"CLE", prop:"receptions", line:3.5, side:"over",
    odds:-160, proj:4.88, sd:2.32, model:0.663, implied:0.615, edge:4.8,
    daylight:0.59, verdict:"PLAY", need:4.49,
    why:"Nominal WR1, grasp tenuous with Concepcion and Boston pushing.",
    flags:["role prior carries 67% of the projection weight"] },
  { player:"Garrett Wilson", team:"NYJ", prop:"receptions", line:4.5, side:"over",
    odds:-180, proj:6.23, sd:2.61, model:0.686, implied:0.643, edge:4.3,
    daylight:0.66, verdict:"PLAY", need:5.87,
    why:"Same projection, longer line. Less room than the 2.5.",
    flags:[] },
  { player:"Kyle Pitts", team:"ATL", prop:"receptions", line:3.5, side:"over",
    odds:-175, proj:4.97, sd:2.34, model:0.675, implied:0.636, edge:3.8,
    daylight:0.63, verdict:"PLAY", need:4.71,
    why:"Targeted on four of Tagovailoa's five attempts in the preseason debut.",
    flags:[] },
  { player:"Breece Hall", team:"NYJ", prop:"rush_attempts", line:10.5, side:"over",
    odds:-260, proj:18.20, sd:6.02, model:0.858, implied:0.722, edge:13.6,
    daylight:1.28, verdict:"REVIEW", need:13.9,
    why:"10 of 11 opening-drive snaps; being featured more prominently.",
    flags:["13.6pt disagreement with a liquid market — held back on purpose"] },
];

const SCREENED = [
  { player:"Breece Hall",    detail:"rush att o13.5 −140 · price outside −150 to −500" },
  { player:"Tony Pollard",   detail:"rush att o12.5 −145 · price outside band; Spears took 12 starter snaps to his 9" },
  { player:"DJ Moore",       detail:"receptions o4.5 −165 · model 23.8pts BELOW the book" },
  { player:"Matthew Golden", detail:"receptions o3.5 −155 · model 12.3pts below the book" },
  { player:"Jeremiyah Love", detail:"ruled out — high ankle sprain, 3-5wk recovery" },
];
// <<< AUTO-GENERATED WEEK END

const pct  = n => (n*100).toFixed(1) + "%";
const odds = n => (n > 0 ? "+" : "") + n;
const prop = p => p.replace(/_/g, " ");

function VerdictBadge({ verdict }) {
  const c = VERDICT_CFG[verdict] || VERDICT_CFG.PLAY;
  return (
    <span style={{fontSize:9,fontWeight:700,fontFamily:T.mono,color:c.color,
      background:c.bg,border:`1px solid ${c.border}`,borderRadius:3,
      padding:"3px 7px",letterSpacing:1,whiteSpace:"nowrap"}}>
      {c.icon} {verdict}
    </span>
  );
}

/* Signature element: what the model claimed against what happened.
   The filled bar is the claim; the notch is the outcome. */
function CalibrationStrip() {
  return (
    <div style={{borderTop:`1px solid ${T.border}`,marginTop:22,paddingTop:18}}>
      <div style={{fontSize:13,fontWeight:700,color:T.text,fontFamily:T.head,
        letterSpacing:1,marginBottom:3}}>DOES 80% MEAN 80%?</div>
      <div style={{fontSize:10,color:"#666",fontFamily:T.mono,lineHeight:1.6,
        maxWidth:"62ch",marginBottom:14}}>
        Every projection states a probability. These compare what the model said
        against what happened, across 33,237 player-week lines it never saw while
        fitting.
      </div>

      {CALIBRATION.map((c,i) => {
        const gap = (c.actual - c.stated) * 100;
        return (
          <div key={i} style={{display:"grid",
            gridTemplateColumns:"62px 1fr 66px",alignItems:"center",
            gap:10,marginBottom:7}}>
            <div style={{fontSize:10,color:"#666",fontFamily:T.mono,
              textAlign:"right"}}>said {(c.stated*100).toFixed(0)}%</div>
            <div style={{position:"relative",height:20,background:"#ffffff05",
              border:`1px solid ${T.border}`,borderRadius:3,overflow:"hidden"}}>
              <div style={{position:"absolute",inset:0,width:`${c.stated*100}%`,
                background:"#00e5ff1a"}} />
              <div style={{position:"absolute",top:5,bottom:5,left:0,
                width:`${c.actual*100}%`,borderRight:`2px solid ${T.text}`}} />
            </div>
            <div style={{fontSize:10,fontFamily:T.mono,
              color: gap >= 0 ? T.accent : "#ff4757"}}>
              {gap >= 0 ? "+" : ""}{gap.toFixed(1)} pts
            </div>
          </div>
        );
      })}

      <div style={{fontSize:9.5,color:"#444",fontFamily:T.mono,marginTop:12,
        lineHeight:1.7,maxWidth:"66ch"}}>
        Uncorrected, the same model ran ~5.5 points hot above 70% — it said 94% on
        things that happened 89% of the time. Closing that gap is why this page exists.
      </div>
    </div>
  );
}

function Metric({ label, value, sub, color }) {
  return (
    <div style={{minWidth:120}}>
      <div style={{fontSize:8,color:"#444",letterSpacing:2,fontFamily:T.mono,
        marginBottom:5}}>{label}</div>
      <div style={{fontSize:26,fontWeight:800,fontFamily:T.mono,
        color:color||T.text,letterSpacing:-1,lineHeight:1}}>{value}</div>
      <div style={{fontSize:9,color:"#555",fontFamily:T.mono,marginTop:5}}>{sub}</div>
    </div>
  );
}

function PickCard({ p }) {
  const [open, setOpen] = useState(false);
  const cfg = VERDICT_CFG[p.verdict] || VERDICT_CFG.PLAY;
  const side = p.side === "over" ? "o" : "u";

  return (
    <div onClick={() => setOpen(!open)} style={{background:T.surface,
      border:`1px solid ${open ? cfg.border : T.border}`,borderRadius:6,
      marginBottom:8,cursor:"pointer",transition:"border-color .15s"}}>

      <div style={{padding:"12px 16px",display:"flex",alignItems:"center",gap:12}}>
        <div style={{flexShrink:0}}><VerdictBadge verdict={p.verdict} /></div>

        <div style={{flex:1,minWidth:0}}>
          <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
            <span style={{fontSize:14,fontWeight:700,color:T.text,
              fontFamily:T.head}}>{p.player}</span>
            <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>
              {prop(p.prop)} {side}{p.line} · {p.team}
            </span>
          </div>
          <div style={{fontSize:11,color:"#777",fontFamily:T.mono,marginTop:2}}>
            {p.why}
          </div>
        </div>

        <div style={{display:"flex",gap:14,alignItems:"center",flexShrink:0}}>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:13,fontWeight:700,color:T.text,
              fontFamily:T.mono}}>{p.proj.toFixed(2)}</div>
            <div style={{fontSize:8,color:"#444"}}>PROJ</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:18,fontWeight:800,color:cfg.color,
              fontFamily:T.mono}}>{pct(p.model)}</div>
            <div style={{fontSize:8,color:"#444"}}>MODEL</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:13,fontWeight:700,color:T.text,
              fontFamily:T.mono}}>{odds(p.odds)}</div>
            <div style={{fontSize:8,color:"#444"}}>ODDS</div>
          </div>
          <span style={{fontSize:14,color:open?cfg.color:"#333"}}>
            {open ? "−" : "+"}
          </span>
        </div>
      </div>

      {open && (
        <div style={{borderTop:`1px solid ${T.border}`,padding:"14px 16px"}}>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
            <div>
              <div style={{fontSize:9,color:"#444",letterSpacing:2,
                fontFamily:T.mono,marginBottom:8}}>THE NUMBER</div>
              {[
                ["Projection", `${p.proj.toFixed(2)} ± ${p.sd.toFixed(2)}`],
                ["Break-even needs", p.need.toFixed(2)],
                ["Room over the line", `${p.daylight.toFixed(2)} sd`],
              ].map(([k,v]) => (
                <div key={k} style={{display:"flex",justifyContent:"space-between",
                  fontSize:10,fontFamily:T.mono,marginBottom:5}}>
                  <span style={{color:"#666"}}>{k}</span>
                  <span style={{color:T.text,fontWeight:700}}>{v}</span>
                </div>
              ))}
            </div>
            <div>
              <div style={{fontSize:9,color:"#444",letterSpacing:2,
                fontFamily:T.mono,marginBottom:8}}>PRICE</div>
              {[
                ["Model", pct(p.model)],
                ["Book implied", pct(p.implied)],
                ["Edge", `${p.edge > 0 ? "+" : ""}${p.edge.toFixed(1)} pts`],
              ].map(([k,v],i) => (
                <div key={k} style={{display:"flex",justifyContent:"space-between",
                  fontSize:10,fontFamily:T.mono,marginBottom:5}}>
                  <span style={{color:"#666"}}>{k}</span>
                  <span style={{color:i===2?cfg.color:T.text,fontWeight:700}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {p.flags.length > 0 && (
            <div style={{marginTop:12,paddingTop:12,
              borderTop:`1px solid ${T.border}`}}>
              {p.flags.map((f,i) => (
                <div key={i} style={{fontSize:10,color:"#f5c518",
                  fontFamily:T.mono,lineHeight:1.6}}>! {f}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function NFLHub() {
  const card = PICKS.filter(p => p.verdict !== "REVIEW");
  const held = PICKS.filter(p => p.verdict === "REVIEW");

  return (
    <div style={{padding:"28px 24px 80px",maxWidth:1000,margin:"0 auto",
      fontFamily:T.mono}}>

      {/* header */}
      <div style={{display:"flex",alignItems:"baseline",gap:14,flexWrap:"wrap",
        marginBottom:20}}>
        <div style={{fontSize:22,fontWeight:800,color:T.text,fontFamily:T.head,
          letterSpacing:1}}>WEEK {WEEK.week}</div>
        <div style={{fontSize:10,color:T.muted}}>posted {WEEK.posted}</div>
        <span style={{fontSize:9,fontWeight:700,color:"#f5c518",
          background:"#f5c51818",border:"1px solid #f5c51840",borderRadius:3,
          padding:"3px 8px",letterSpacing:2}}>PAPER · NOTHING IS BET</span>
      </div>

      {/* hero: the question the season is built to answer */}
      <div style={{background:T.surface,border:`1px solid ${T.border}`,
        borderRadius:8,padding:22,marginBottom:26}}>
        <div style={{display:"flex",gap:34,flexWrap:"wrap"}}>
          <Metric label="CLOSING LINE VALUE"
            value={WEEK.clv_avg === null ? "—" : `${WEEK.clv_avg > 0 ? "+" : ""}${WEEK.clv_avg.toFixed(2)}`}
            sub="points per leg · logs at kickoff"
            color={WEEK.clv_avg > 0 ? T.accent : T.text} />
          <Metric label="LEGS LOGGED" value={WEEK.legs_logged}
            sub="season target near 300" />
          <Metric label="CALIBRATION SLOPE" value={WEEK.slope.toFixed(3)}
            sub="held-out 2025 · 1.0 is perfect" color={T.nfl} />
          <Metric label="STAKE" value={`$${WEEK.stake}`}
            sub="paper trial, all season" />
        </div>
        <CalibrationStrip />
      </div>

      {/* the card */}
      <div style={{fontSize:9,color:"#444",letterSpacing:3,marginBottom:10}}>
        CARD · {card.length} PLAYS
      </div>
      {card.map((p,i) => <PickCard key={i} p={p} />)}

      {/* held back — showing what we didn't take is the point */}
      {held.length > 0 && (
        <>
          <div style={{fontSize:9,color:"#444",letterSpacing:3,
            margin:"26px 0 10px"}}>HELD BACK</div>
          {held.map((p,i) => <PickCard key={i} p={p} />)}
        </>
      )}

      {/* screened */}
      <div style={{fontSize:9,color:"#444",letterSpacing:3,
        margin:"26px 0 10px"}}>SCREENED OUT · {SCREENED.length}</div>
      <div style={{background:T.surface,border:`1px solid ${T.border}`,
        borderRadius:6,padding:"4px 16px"}}>
        {SCREENED.map((s,i) => (
          <div key={i} style={{padding:"9px 0",fontSize:10,fontFamily:T.mono,
            borderBottom: i < SCREENED.length-1 ? `1px solid ${T.border}` : "none",
            display:"flex",gap:10,flexWrap:"wrap"}}>
            <span style={{color:"#777",fontWeight:700,minWidth:130}}>{s.player}</span>
            <span style={{color:"#555",flex:1}}>{s.detail}</span>
          </div>
        ))}
      </div>

      {/* what this is not */}
      <div style={{marginTop:32,paddingTop:18,borderTop:`1px solid ${T.border}`,
        fontSize:10,color:"#555",lineHeight:1.8,maxWidth:"74ch"}}>
        <div style={{fontSize:9,color:"#444",letterSpacing:3,marginBottom:8}}>
          WHAT THIS PAGE IS NOT
        </div>
        Nothing here is bet. A 17-week season cannot produce enough graded plays to
        prove an edge before it ends — closing line value can, per leg, months
        earlier. The model's aggregate probabilities are honest and validated out of
        sample. Its individual projections are noisy, and for the players covered
        best by reporting they lean heavily on positional priors. A well-formatted
        card is not evidence.
        <div style={{marginTop:12,color:"#444"}}>
          Projections from trailing usage, team pace and game script, shrunk to
          fitted depth-chart priors, converted through a fitted variance curve and
          calibrated on held-out seasons. Defensive matchup adjustments were built,
          tested, and cut — they did not improve accuracy. Data via nflverse.
        </div>
      </div>

    </div>
  );
}
