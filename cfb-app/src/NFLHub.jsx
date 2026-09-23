import { useEffect, useState } from "react";
import { teamColor } from "./nflTeams";
// NFL Card — the plays. Reads /data/nfl_card_<slate>.json (automation/pipeline/build_card_json.py).
// Paper trial, 2026 season: nothing is bet.

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  red:"#ff4757", amber:"#f5c518",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const SLATES = [["tnf","THU"],["sun","SUN"],["mnf","MON"]];
const SINGLE_GAME = new Set(["tnf", "mnf"]);
const MARKET_LABEL = { rec_yds:"rec yds", receptions:"rec", rush_yds:"rush yds", rush_att:"rush att",
  pass_yds:"pass yds", pass_cmps:"cmp", pass_att:"att" };

const oddsStr = o => o == null ? "—" : (o > 0 ? "+" : "") + o;
const rungStr = r => typeof r === "string" ? r : Number.isInteger(r) ? `${r}+` : `o${r}`;
const frac = (v, n) => `${Math.round(v * n)}/${n}`;
// last3 is a list; older cards stored "[np.int64(126), ...]" strings.
const last3Of = v => Array.isArray(v) ? v :
  (String(v || "").replace(/np\.\w+\(/g, "").match(/-?\d+(\.\d+)?/g) || []).map(Number);

// Wed–Thu -> Thursday card, Fri–Sun -> Sunday, Mon–Tue -> Monday.
function slateForToday() {
  const d = new Date().getDay();
  return d >= 3 && d <= 4 ? "tnf" : d === 1 || d === 2 ? "mnf" : "sun";
}

// Older cards have no Reasons on held rows; rebuild them from the flags.
function heldReasons(h) {
  if (h.Reasons?.length) return h.Reasons;
  const r = [];
  if (h.TeamChange) r.push("team change");
  if (h.OppD === "TOUGH") r.push("opp D tough");
  if (h.OwnVol === "TOUGH") r.push("own volume low");
  return r;
}

function Tag({ label, v }) {
  // opp_d: SOFT = easy matchup. own_vol: SOFT = high volume, TOUGH = low volume.
  const good = v === "SOFT", bad = v === "TOUGH";
  const text = label === "VOL" ? (good ? "HIGH" : bad ? "LOW" : "—") : (good ? "SOFT" : bad ? "TOUGH" : "—");
  return (
    <span style={{fontSize:9,fontFamily:T.mono,color: good ? T.accent : bad ? T.red : "#444",whiteSpace:"nowrap"}}>
      <span style={{color:"#444"}}>{label} </span>{text}
    </span>
  );
}

function Price({ leg }) {
  const real = leg.odds_real != null;
  return (
    <span style={{fontSize:12,fontWeight:700,color:T.text,fontFamily:T.mono}}>
      {oddsStr(real ? leg.odds_real : leg.odds_est)}
      {!real && <sup style={{fontSize:7,color:T.amber,marginLeft:2,fontWeight:500}}>est</sup>}
    </span>
  );
}

function Leg({ l, last }) {
  const l3 = last3Of(l.last3);
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap",padding:"9px 12px 9px 10px",
      borderLeft:`3px solid ${teamColor(l.team)}`,borderBottom: last ? "none" : `1px solid ${T.border}`}}>
      <div style={{flex:"1 1 200px",minWidth:0}}>
        <div style={{display:"flex",alignItems:"baseline",gap:8,flexWrap:"wrap"}}>
          <a href={`#legs?player=${encodeURIComponent(l.player)}`} title="open this player's ladder in Legs"
            style={{fontSize:14,fontWeight:700,color:T.text,fontFamily:T.head,textDecoration:"none"}}>{l.player}</a>
          {l.star && <span title="floor star: L10 ≥ 9/10 and L15 ≥ 13/15 — may anchor two tickets"
            style={{fontSize:10,color:T.amber}}>★</span>}
          <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>{l.team} v {l.opp}</span>
        </div>
        <div style={{fontSize:11,fontFamily:T.mono,marginTop:2}}>
          <span style={{color:T.accent,fontWeight:700}}>{rungStr(l.rung)}</span>{" "}
          <span style={{color:"#999"}}>{MARKET_LABEL[l.market] || l.market}</span>
        </div>
      </div>
      <div style={{display:"flex",alignItems:"center",gap:14,flexWrap:"wrap",fontFamily:T.mono}}>
        <Price leg={l} />
        <span style={{fontSize:10,color:"#999"}}>{frac(l.l10, 10)} <span style={{color:"#555"}}>{frac(l.l15, 15)}</span></span>
        <span style={{fontSize:10,minWidth:66}}>
          {l3.map((v, i) => <span key={i} style={{color: v >= l.rung ? "#7fe0b0" : "#c96b74",marginRight:5}}>{Math.round(v)}</span>)}
        </span>
        <span style={{display:"flex",gap:7}}><Tag label="D" v={l.opp_d} /><Tag label="VOL" v={l.own_vol} /></span>
      </div>
    </div>
  );
}

function Ticket({ t }) {
  const color = t.reduced ? T.amber : T.accent;
  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,marginBottom:14,overflow:"hidden"}}>
      <div style={{display:"flex",alignItems:"center",gap:14,flexWrap:"wrap",padding:"12px 14px",
        borderBottom:`1px solid ${T.border}`}}>
        <div style={{fontSize:18,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>{t.name}</div>
        <span style={{fontSize:9.5,fontFamily:T.mono,color,background:color + "14",border:`1px solid ${color}40`,
          borderRadius:3,padding:"3px 8px",lineHeight:1.4}}>{t.label}</span>
        {t.correlated && <span style={{fontSize:9,fontFamily:T.mono,color:"#888",border:"1px solid #ffffff18",
          borderRadius:3,padding:"3px 7px"}}>single game · legs correlated</span>}
        <span style={{flex:1}} />
        <div style={{display:"flex",gap:18,fontFamily:T.mono}}>
          <div style={{textAlign:"right"}}>
            <div style={{fontSize:20,fontWeight:800,color:T.nfl,letterSpacing:-0.5,lineHeight:1}}>{oddsStr(t.est_american)}</div>
            <div style={{fontSize:8,color:"#444",letterSpacing:1.5,marginTop:3}}>PAYOUT · {t.est_payout.toFixed(2)}x</div>
          </div>
          <div style={{textAlign:"right"}}>
            <div style={{fontSize:20,fontWeight:800,color:T.text,letterSpacing:-0.5,lineHeight:1}}>{(t.model_hit * 100).toFixed(1)}%</div>
            <div style={{fontSize:8,color:"#444",letterSpacing:1.5,marginTop:3}}>MODEL HIT</div>
          </div>
        </div>
      </div>
      {t.legs.map((l, i) => <Leg key={`${l.player}|${l.market}`} l={l} last={i === t.legs.length - 1} />)}
    </div>
  );
}

function Label({ children }) {
  return <div style={{fontSize:9,color:"#444",letterSpacing:3,margin:"26px 0 10px"}}>{children}</div>;
}

export default function NFLHub() {
  const [files, setFiles] = useState(null);     // slate -> card | null
  const [slate, setSlate] = useState(null);

  useEffect(() => {
    const bust = `?t=${Date.now()}`;
    Promise.all(SLATES.map(([s]) => fetch(`/data/nfl_card_${s}.json${bust}`)
      .then(r => r.ok ? r.json() : null).catch(() => null)))
      .then(all => {
        const fs = Object.fromEntries(SLATES.map(([s], i) => [s, all[i]?.tickets ? all[i] : null]));
        setFiles(fs);
        const want = slateForToday();
        setSlate(fs[want] ? want : ["sun", "tnf", "mnf"].find(s => fs[s]) || want);
      });
  }, []);

  const card = files && slate ? files[slate] : null;
  const pulled = card?.prices_pulled ? new Date(card.prices_pulled).toLocaleString(undefined,
    { weekday:"short", month:"short", day:"numeric", hour:"numeric", minute:"2-digit" }) : null;

  return (
    <div style={{padding:"28px 16px 80px",maxWidth:1000,margin:"0 auto",fontFamily:T.mono}}>
      <div style={{display:"flex",alignItems:"baseline",gap:14,flexWrap:"wrap",marginBottom:4}}>
        <div style={{fontSize:22,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>
          CARD{card ? ` · WEEK ${card.week}` : ""}
        </div>
        <div style={{display:"inline-flex",border:"1px solid #ffffff14",borderRadius:4,overflow:"hidden"}}>
          {SLATES.map(([s, label]) => {
            const has = !!files?.[s];
            return (
              <button key={s} disabled={!has} onClick={() => setSlate(s)} title={has ? "" : "not posted"}
                style={{padding:"5px 12px",fontSize:10,fontFamily:T.mono,letterSpacing:1,border:"none",
                  cursor: has ? "pointer" : "default",background: slate === s && has ? T.nfl + "1c" : "transparent",
                  color: slate === s && has ? T.nfl : has ? "#777" : "#333",fontWeight: slate === s ? 700 : 500}}>{label}</button>
            );
          })}
        </div>
        <span style={{fontSize:9,fontWeight:700,color:T.amber,background:T.amber + "18",border:`1px solid ${T.amber}40`,
          borderRadius:3,padding:"3px 8px",letterSpacing:2}}>PAPER · NOTHING IS BET</span>
      </div>
      <div style={{fontSize:10,color:"#777",marginBottom:20,maxWidth:"72ch",lineHeight:1.6}}>
        Card tickets are graded Tuesday. Personal slips are not the card.
      </div>

      {!files && <div style={{fontSize:10,color:"#444"}}>loading…</div>}
      {files && !card && (
        <div style={{fontSize:11,color:"#777",background:T.surface,border:`1px solid ${T.border}`,borderRadius:6,padding:16}}>
          No card posted for this slate yet.
        </div>
      )}

      {card && <>
        <Label>TICKETS · {card.tickets.length}</Label>
        {card.tickets.length === 0 && <div style={{fontSize:10,color:"#555"}}>
          No ticket cleared the rules this slate — see what was held back below.</div>}
        {card.tickets.map(t => <Ticket key={t.name} t={t} />)}

        {SINGLE_GAME.has(slate) && card.floors_singles?.length > 0 && <>
          <Label>FLOORS AS SINGLES · {card.floors_singles.length}</Label>
          <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,overflow:"hidden"}}>
            {card.floors_singles.map((l, i) => <Leg key={`${l.player}|${l.market}`} l={l} last={i === card.floors_singles.length - 1} />)}
          </div>
        </>}

        {card.notes?.trim() && <>
          <Label>AUTHOR NOTES</Label>
          <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"12px 14px",
            fontSize:11,color:"#aaa",lineHeight:1.7,whiteSpace:"pre-wrap"}}>{card.notes.trim()}</div>
        </>}

        {card.held?.length > 0 && <>
          <Label>HELD BACK · {card.held.length}</Label>
          <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"2px 14px"}}>
            {card.held.map((h, i) => (
              <div key={`${h.Player}|${h.Market}`} style={{display:"flex",gap:10,flexWrap:"wrap",alignItems:"baseline",
                padding:"8px 0",fontSize:10,borderBottom: i < card.held.length - 1 ? `1px solid ${T.border}` : "none"}}>
                <span style={{color:"#999",fontWeight:700,minWidth:150}}>{h.Player}</span>
                <span style={{color:"#666",minWidth:130}}>
                  {h.Rung} {MARKET_LABEL[h.Market] || h.Market} · {oddsStr(h.EstOdds)}</span>
                <span style={{color:"#555",minWidth:70}}>{h.L10} {h.L15}</span>
                <span style={{color:"#c96b74",flex:"1 1 200px"}}>{heldReasons(h).join("; ")}</span>
              </div>
            ))}
          </div>
        </>}

        <div style={{marginTop:28,fontSize:10,color:"#555",fontStyle:"italic"}}>
          ({pulled ? `Prices as pulled ${pulled}` : "Prices as pulled — time not recorded"})
        </div>
      </>}
    </div>
  );
}
