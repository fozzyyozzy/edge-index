import { useEffect, useState } from "react";
import CalibrationPanel from "./CalibrationPanel";
// NFL Record — calibration, then the card record. Reads /data/nfl_record.json
// (automation/pipeline/grade.py -> receipts/record_<season>.json, copied by tuesday.yml).

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555", red:"#ff4757", amber:"#f5c518",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};
const MARKET_LABEL = { rec_yds:"rec yds", receptions:"rec", rush_yds:"rush yds", rush_att:"rush att",
  pass_yds:"pass yds", pass_cmps:"cmp", pass_att:"att" };
const oddsStr = o => o == null ? "—" : (o > 0 ? "+" : "") + o;
const implied = o => o < 0 ? -o / (-o + 100) : 100 / (o + 100);
const pct = (a, b) => b ? `${(100 * a / b).toFixed(1)}%` : "—";
const unitStr = u => u == null ? "—" : `${u > 0 ? "+" : ""}${u.toFixed(2)}u`;
// CLV in implied-probability points: positive = the price shortened between posting and kickoff (we beat the close)
const clvCell = v => v == null ? "—" :
  <span style={{color: v > 0 ? T.accent : v < 0 ? T.red : "#999"}}>{v > 0 ? "+" : ""}{v.toFixed(2)}</span>;

// Tickets published by hand, outside the pipeline (receipts carry their "flag"). Counted in W-L, never in grade stats.
function FlagBadge({ children }) {
  return (
    <span style={{fontSize:8.5,letterSpacing:1,color:T.amber,border:`1px solid ${T.amber}50`,background:T.amber + "12",
      borderRadius:3,padding:"2px 6px",whiteSpace:"nowrap"}}>{children}</span>
  );
}

function Label({ children }) {
  return <div style={{fontSize:9,color:"#444",letterSpacing:3,margin:"28px 0 10px"}}>{children}</div>;
}

// Dense table in the site's mono style. cols: [header, align]; rows: arrays of cells.
function Table({ cols, rows, foot }) {
  const cell = (align, extra = {}) => ({padding:"7px 10px",textAlign:align,whiteSpace:"nowrap",...extra});
  return (
    <div style={{overflowX:"auto",background:T.surface,border:`1px solid ${T.border}`,borderRadius:8}}>
      <table style={{width:"100%",borderCollapse:"collapse",fontFamily:T.mono,fontSize:11,minWidth:420}}>
        <thead>
          <tr>{cols.map(([h, a]) => <th key={h} style={cell(a, {fontSize:8.5,letterSpacing:1.5,color:"#444",fontWeight:600,
            borderBottom:`1px solid ${T.border}`})}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} style={{borderTop: i ? `1px solid ${T.border}` : "none"}}>
              {r.map((v, j) => <td key={j} style={cell(cols[j][1], {color:"#bbb"})}>{v}</td>)}
            </tr>
          ))}
        </tbody>
        {foot && (
          <tfoot>
            <tr style={{borderTop:`1px solid #ffffff18`}}>
              {foot.map((v, j) => <td key={j} style={cell(cols[j][1], {color:T.text,fontWeight:700})}>{v}</td>)}
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}

export default function NFLRecord() {
  const [rec, setRec] = useState(undefined);   // undefined = loading, null = none yet

  useEffect(() => {
    fetch(`/data/nfl_record.json?t=${Date.now()}`).then(r => r.ok ? r.json() : null)
      .then(d => setRec(d?.weeks ? d : null)).catch(() => setRec(null));
  }, []);

  const weeks = rec?.weeks || [];
  const tot = weeks.reduce((a, w) => ({ W: a.W + w.ticket_record.WIN, L: a.L + w.ticket_record.LOSS,
    V: a.V + w.ticket_record.VOID, hit: a.hit + w.legs_hit, n: a.n + w.legs_graded }), { W:0, L:0, V:0, hit:0, n:0 });
  const grades = (rec?.by_grade || []).filter(g => g.n > 0);
  // as settled at DraftKings (Early Exit voids a leg). grade.py also computes standard settlement; not displayed.
  const units = weeks.reduce((a, w) => a + (w.units || 0), 0);
  const clvN = weeks.reduce((a, w) => a + (w.clv?.n || 0), 0);
  const clvSeason = clvN ? weeks.reduce((a, w) => a + (w.clv?.n ? w.clv.avg_leg_pts * w.clv.n : 0), 0) / clvN : null;
  const flagged = weeks.flatMap(w => (w.tickets || []).filter(t => t.flag).map(t => ({ ...t, week: w.week })));
  const evr = rec?.est_vs_real || [];

  return (
    <div style={{padding:"28px 16px 80px",maxWidth:1000,margin:"0 auto",fontFamily:T.mono}}>
      <div style={{fontSize:22,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1,marginBottom:4}}>RECORD</div>
      <div style={{fontSize:10,color:"#777",marginBottom:20,maxWidth:"72ch",lineHeight:1.6}}>
        Every card ticket as published, graded Tuesday against the box scores. Personal slips are not the card.
      </div>

      <CalibrationPanel />

      {rec === undefined && <div style={{fontSize:10,color:"#444",marginTop:24}}>loading…</div>}
      {rec === null || (rec && weeks.length === 0) ? (
        <div style={{marginTop:28,fontSize:12,color:"#999",background:T.surface,border:`1px solid ${T.border}`,
          borderRadius:8,padding:"18px 20px"}}>
          Week 3 is the first graded card. Receipts post Tuesday.
        </div>
      ) : rec && <>
        <Label>TICKETS BY WEEK</Label>
        <Table cols={[["WEEK","left"],["W","right"],["L","right"],["VOID","right"],["LEGS HIT","right"],["UNITS","right"],["LEG HIT %","right"],["AVG CLV","right"]]}
          rows={weeks.map(w => [<>{w.week}{(w.tickets || []).some(t => t.flag) &&
            <span title="includes a flagged ticket — see below" style={{color:T.amber,marginLeft:4}}>†</span>}</>, w.ticket_record.WIN, w.ticket_record.LOSS, w.ticket_record.VOID,
            `${w.legs_hit}/${w.legs_graded}`, unitStr(w.units), pct(w.legs_hit, w.legs_graded), clvCell(w.clv?.avg_leg_pts)])}
          foot={["SEASON", tot.W, tot.L, tot.V, `${tot.hit}/${tot.n}`, unitStr(units), pct(tot.hit, tot.n), clvCell(clvSeason)]} />
        <div style={{fontSize:10,color:"#999",marginTop:8,lineHeight:1.6,maxWidth:"80ch"}}>
          Tickets are graded as settled at DraftKings, where Early Exit protection applies.
        </div>
        <div style={{fontSize:9.5,color:"#555",marginTop:8,lineHeight:1.6,maxWidth:"72ch"}}>
          CLV = closing line value, per card leg, in implied-probability points: the published price against the last
          price pulled before that game kicked off. Positive = the market moved toward the card. Hand-built tickets have no
          price history, so they have no CLV.
        </div>
        {flagged.length > 0 && (
          <div style={{marginTop:10,background:T.surface,border:`1px solid ${T.amber}30`,borderRadius:8,padding:"4px 14px"}}>
            {flagged.map((t, i) => (
              <div key={`${t.week}-${t.name}`} style={{display:"flex",gap:10,flexWrap:"wrap",alignItems:"baseline",padding:"9px 0",
                fontSize:10.5,borderTop: i ? `1px solid ${T.border}` : "none"}}>
                <span style={{color:T.amber}}>†</span>
                <span style={{color:T.text,fontWeight:700}}>Wk {t.week} {t.name}</span>
                <FlagBadge>{t.flag.toUpperCase()}</FlagBadge>
                <span style={{color:"#999",flex:"1 1 260px"}}>{(t.leg_text || []).join(" · ")}{t.est_american != null ? ` · pays ${oddsStr(t.est_american)}` : ""}</span>
                {t.clv_pts != null && <span style={{fontSize:10}}>CLV {clvCell(t.clv_pts)}</span>}
                {t.early_exit?.length > 0 && <span style={{fontSize:9.5,color:"#888"}}>
                  early exit: {t.early_exit.join(", ")}</span>}
                {t.units != null && <span style={{fontSize:10,color:"#999"}}>{unitStr(t.units)}</span>}
                <span style={{color: t.result === "WIN" ? T.accent : t.result === "LOSS" ? T.red : "#888",fontWeight:700}}>{t.result}</span>
              </div>
            ))}
            <div style={{fontSize:9.5,color:"#555",padding:"2px 0 10px",lineHeight:1.6}}>
              Published as a card ticket but built by hand, not by the pipeline. Counted in the W-L above; left out of grade-by-letter, since it has no pipeline grade.
            </div>
          </div>
        )}

        <Label>LEG HIT RATE BY GRADE</Label>
        {grades.length === 0
          ? <div style={{fontSize:10,color:"#555"}}>No graded legs carry a letter yet.</div>
          : <Table cols={[["GRADE","left"],["LEGS","right"],["HIT %","right"],["AVG PROB","right"],["DK IMPLIED","right"],["HIT − PROB","right"]]}
              rows={grades.map(g => {
                const prob = g.avg_prob ?? g.expected;                  // older weeks: the clear % shown at the time
                const diff = prob == null ? null : 100 * g.hits / g.n - prob;
                return [g.grade.replace("-", "−"), g.n, `${pct(g.hits, g.n)} (${g.hits})`,
                  prob == null ? "—" : `${prob.toFixed(1)}%`, g.avg_implied == null ? "—" : `${g.avg_implied.toFixed(1)}%`,
                  diff == null ? "—" : <span style={{color: diff >= 0 ? T.accent : T.red}}>{diff >= 0 ? "+" : ""}{diff.toFixed(1)} pts</span>];
              })} />}
        <div style={{fontSize:9.5,color:"#555",marginTop:8,lineHeight:1.6,maxWidth:"72ch"}}>
          AVG PROB = our blended probability for those legs when the card posted (clear rates pulled toward DK's no-vig
          price). DK IMPLIED = what DK's price implied, vig included. Small samples swing hard.
        </div>

        <Label>ESTIMATED VS REAL PRICE</Label>
        {evr.length === 0
          ? <div style={{fontSize:10,color:"#555"}}>No legs with both an estimated and a real DK price yet.</div>
          : <Table cols={[["WK","left"],["LEG","left"],["EST","right"],["REAL","right"],["IMPLIED Δ","right"],["RESULT","right"]]}
              rows={evr.map(r => {
                const d = 100 * (implied(r.real) - implied(r.est));
                return [r.week, `${r.player} ${r.rung}+ ${MARKET_LABEL[r.market] || r.market}`, oddsStr(r.est), oddsStr(r.real),
                  <span style={{color: d > 0 ? T.red : T.accent}}>{d >= 0 ? "+" : ""}{d.toFixed(1)} pts</span>,
                  r.hit == null ? "void" : r.hit ? <span style={{color:T.accent}}>hit</span> : <span style={{color:T.red}}>miss</span>];
              })} />}
        <div style={{fontSize:9.5,color:"#555",marginTop:8,lineHeight:1.6,maxWidth:"72ch"}}>
          EST is what the ladder estimator priced the rung from the main line alone; REAL is the DK alt price the card used.
          Positive Δ = DK charged more than the estimate.
        </div>
      </>}
    </div>
  );
}
