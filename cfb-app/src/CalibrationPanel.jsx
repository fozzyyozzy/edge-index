// "Does 80% mean 80%?" — NFL model calibration on held-out lines. Moved from the old Card tab to Record.
// Signature element: what the model claimed against what happened. The filled bar is the claim; the notch is the outcome.

const T = {
  surface:"#0d1117", border:"#ffffff0a", accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const CALIBRATION = [
  { stated: 0.746, actual: 0.758 },
  { stated: 0.851, actual: 0.857 },
  { stated: 0.937, actual: 0.931 },
];

export default function CalibrationPanel() {
  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"18px 20px"}}>
      <div style={{fontSize:9,color:T.nfl,letterSpacing:3,fontFamily:T.mono,marginBottom:6}}>NFL MODEL</div>
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
        things that happened 89% of the time. Closing that gap is why the NFL card exists.
      </div>
    </div>
  );
}
