import { useEffect, useState } from "react";
import { SLATES, defaultSlate } from "./nflSlates";
import SlateSwitch from "./SlateSwitch";
// Floor lines. Reads /data/nfl_floors_<slate>.json, written by automation/pipeline/floors.py each card run.

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const POS_COLOR = { QB:"#a855f7", RB:"#00c896", WR:"#00e5ff", TE:"#f5c518" };
const oddsStr = o => o == null ? "—" : (o > 0 ? "+" : "") + o;

const POSITIONS = ["ALL", "WR", "TE", "RB", "QB"];

// Prop filter. Ordered so the volume props a floor play usually lives on
// come first, and the QB-only ones sit together at the end.
const PROP_FILTERS = [
  { id:"ALL",        label:"ALL PROPS" },
  { id:"receptions", label:"REC" },
  { id:"rec_yds",    label:"REC YDS" },
  { id:"rush_att",   label:"RUSH ATT" },
  { id:"rush_yds",   label:"RUSH YDS" },
  { id:"pass_cmps",  label:"COMP" },
  { id:"pass_att",   label:"PASS ATT" },
  { id:"pass_yds",   label:"PASS YDS" },
];
const LABEL = { receptions:"Receptions", rec_yds:"Rec Yards", rush_att:"Rush Att", rush_yds:"Rush Yards",
  pass_cmps:"Completions", pass_att:"Pass Att", pass_yds:"Pass Yards" };

function Row({ r }) {
  const [open, setOpen] = useState(false);
  const pc = POS_COLOR[r.pos] || T.muted;
  const newTeam = r.team_change && r.prev_team && r.prev_team !== r.team;
  // How far the clear rate sits above what the price asks. Positive = the log clears it more often than the price implies.
  const gap = r.clear_pct - r.implied_pct;
  const hit = Number(r.l10.split("/")[0]);

  return (
    <div onClick={() => setOpen(!open)} style={{background:T.surface,
      border:`1px solid ${open ? pc + "40" : T.border}`, borderRadius:6,
      marginBottom:6, cursor:"pointer"}}>
      <div style={{padding:"11px 14px", display:"flex", alignItems:"center", gap:12, flexWrap:"wrap"}}>
        <span style={{fontSize:9, fontWeight:700, color:pc, background:pc+"18",
          border:`1px solid ${pc}40`, borderRadius:3, padding:"2px 6px",
          fontFamily:T.mono, minWidth:30, textAlign:"center"}}>{r.pos}</span>

        <div style={{flex:"1 1 180px", minWidth:0}}>
          <div style={{display:"flex", alignItems:"baseline", gap:8, flexWrap:"wrap"}}>
            <span style={{fontSize:13, fontWeight:700, color:T.text,
              fontFamily:T.head}}>{r.player}</span>
            <span style={{fontSize:10, color:T.muted, fontFamily:T.mono}}>
              {newTeam ? `${r.prev_team} → ${r.team}` : r.team} · {LABEL[r.market] || r.market}{" "}
              <span style={{color:T.accent, fontWeight:700}}>{r.rung}+</span>
            </span>
            {newTeam && (
              <span style={{fontSize:8, color:"#f5c518", background:"#f5c51818",
                border:"1px solid #f5c51840", borderRadius:3, padding:"1px 5px",
                fontFamily:T.mono, letterSpacing:1}}>NEW TEAM</span>
            )}
          </div>
        </div>

        <div style={{display:"flex", gap:16, alignItems:"center", flexShrink:0}}>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:12, fontWeight:700, color:T.text,
              fontFamily:T.mono}}>{hit}/10</div>
            <div style={{fontSize:8, color:"#444"}}>CLEARED</div>
          </div>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:16, fontWeight:800, color:pc,
              fontFamily:T.mono}}>{r.clear_pct.toFixed(0)}%</div>
            <div style={{fontSize:8, color:"#444"}}>CLEAR RATE</div>
          </div>
          <div style={{textAlign:"center", minWidth:52}}>
            <div style={{fontSize:12, fontWeight:700, color:T.accent,
              fontFamily:T.mono}}>{oddsStr(r.odds)}{!r.real && <sup style={{fontSize:7,color:"#f5c518",marginLeft:2}}>est</sup>}</div>
            <div style={{fontSize:8, color:"#444"}}>DK PRICE</div>
          </div>
          <span style={{fontSize:13, color:open ? pc : "#333"}}>{open ? "−" : "+"}</span>
        </div>
      </div>

      {open && (
        <div style={{borderTop:`1px solid ${T.border}`, padding:"12px 14px",
          display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(220px, 1fr))", gap:14}}>
          <div>
            <div style={{fontSize:9, color:"#444", letterSpacing:2,
              fontFamily:T.mono, marginBottom:7}}>GAME LOG</div>
            {[["Last-10 average", r.avg10],
               ["Cleared", `${r.l10} · ${r.l15} (${r.clear_pct.toFixed(0)}% blended)`],
               ["Last 3", r.last3.join(" · ")],
               ["Current streak", r.streak + (r.streak === 1 ? " game" : " games")],
               ["Games in sample", r.games],
              ].map(([k,v]) => (
              <div key={k} style={{display:"flex", justifyContent:"space-between",
                fontSize:10, fontFamily:T.mono, marginBottom:4}}>
                <span style={{color:"#666"}}>{k}</span>
                <span style={{color:T.text, fontWeight:700}}>{v}</span>
              </div>
            ))}
          </div>
          <div>
            <div style={{fontSize:9, color:"#444", letterSpacing:2,
              fontFamily:T.mono, marginBottom:7}}>PRICE</div>
            {[["DK price" + (r.real ? "" : " (est)"), `${oddsStr(r.odds)} · ${r.implied_pct.toFixed(1)}% implied`],
               ["Longest price worth taking", oddsStr(r.fair_odds)],
               ["Clear rate minus price", (gap >= 0 ? "+" : "") + gap.toFixed(0) + " pts"],
               ["DK main line", `${r.main_line} at ${oddsStr(r.main_odds)}`],
               ["Matchup · volume", `opp D ${r.opp_d} · own ${r.own_vol === "TOUGH" ? "LOW" : r.own_vol === "SOFT" ? "HIGH" : r.own_vol}`],
              ].map(([k,v]) => (
              <div key={k} style={{display:"flex", justifyContent:"space-between", gap:10,
                fontSize:10, fontFamily:T.mono, marginBottom:4}}>
                <span style={{color:"#666"}}>{k}</span>
                <span style={{color:T.text, fontWeight:700, textAlign:"right"}}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function StreakCenter() {
  const [pos, setPos] = useState("ALL");
  const [prop, setProp] = useState("ALL");
  const [files, setFiles] = useState(null);
  const [slate, setSlate] = useState(null);

  useEffect(() => {
    const bust = `?t=${Date.now()}`;
    Promise.all(SLATES.map(([s]) => fetch(`/data/nfl_floors_${s}.json${bust}`)
      .then(r => r.ok ? r.json() : null).catch(() => null)))
      .then(all => {
        const fs = Object.fromEntries(SLATES.map(([s], i) => [s, all[i]?.rows ? all[i] : null]));
        setFiles(fs); setSlate(defaultSlate(fs));
      });
  }, []);

  const data = files && slate ? files[slate] : null;
  const rows = (data?.rows || [])
    .filter(r => pos === "ALL" || r.pos === pos)
    .filter(r => prop === "ALL" || r.market === prop);
  const pulled = data?.meta?.prices_pulled ? new Date(data.meta.prices_pulled).toLocaleString(undefined,
    { weekday:"short", hour:"numeric", minute:"2-digit" }) : null;
  const slateLabel = SLATES.find(([s]) => s === slate)?.[1];

  return (
    <div style={{padding:"28px 16px 80px", maxWidth:1000, margin:"0 auto",
      fontFamily:T.mono}}>

      <div style={{display:"flex", alignItems:"baseline", gap:14,
        flexWrap:"wrap", marginBottom:6}}>
        <div style={{fontSize:22, fontWeight:800, color:T.text,
          fontFamily:T.head, letterSpacing:1}}>FLOOR LINES</div>
        <SlateSwitch files={files} slate={slate} onChange={setSlate} />
        {data && (
          <span style={{fontSize:9, fontWeight:700, color:"#f5c518",
            background:"#f5c51818", border:"1px solid #f5c51840", borderRadius:3,
            padding:"3px 8px", letterSpacing:2}}>
            WK {data.meta.week} {slateLabel}{pulled ? ` · PRICES ${pulled.toUpperCase()}` : ""}
          </span>
        )}
      </div>

      <div style={{fontSize:10, color:"#666", lineHeight:1.7, maxWidth:"72ch",
        marginBottom:18}}>
        For every player with a DK line this slate: the highest alt rung he cleared in at least 8 of his last 10
        and 11 of his last 15, how often, and what DK charges for it. Clear rate blends L10 (60%) and L15 (40%).
      </div>

      <div style={{display:"flex", gap:4, marginBottom:14, flexWrap:"wrap"}}>
        {POSITIONS.map(p => (
          <button key={p} onClick={() => setPos(p)} style={{
            padding:"5px 12px", background: pos===p ? (POS_COLOR[p]||"#333")+"18" : "transparent",
            border:`1px solid ${pos===p ? (POS_COLOR[p]||"#444")+"40" : T.border}`,
            borderRadius:4, color: pos===p ? (POS_COLOR[p]||T.text) : "#555",
            fontSize:10, fontWeight:700, fontFamily:T.mono, cursor:"pointer",
            letterSpacing:1}}>{p}</button>
        ))}
      </div>

      <div style={{display:"flex", gap:4, marginBottom:16, flexWrap:"wrap"}}>
        {PROP_FILTERS.map(f => (
          <button key={f.id} onClick={() => setProp(f.id)} style={{
            padding:"4px 10px", background:"transparent",
            border:`1px solid ${prop===f.id ? T.nfl+"40" : T.border}`,
            borderRadius:4, color: prop===f.id ? T.nfl : "#444",
            fontSize:9, fontWeight:700, fontFamily:T.mono, cursor:"pointer",
            letterSpacing:1}}>{f.label}</button>
        ))}
      </div>

      {!files && <div style={{fontSize:10, color:"#444"}}>loading…</div>}
      {files && !data && (
        <div style={{fontSize:11, color:"#777", background:T.surface, border:`1px solid ${T.border}`,
          borderRadius:6, padding:16}}>No floor scan posted for this slate yet.</div>
      )}
      {data && rows.length === 0 && (
        <div style={{padding:"28px 0", fontSize:11, color:"#444",
          textAlign:"center"}}>
          No floors for that combination.
        </div>
      )}
      {rows.map(r => <Row key={`${r.player}|${r.market}`} r={r} />)}

      <div style={{marginTop:26, paddingTop:16, borderTop:`1px solid ${T.border}`,
        fontSize:10, color:"#555", lineHeight:1.8, maxWidth:"74ch"}}>
        LONGEST PRICE WORTH TAKING is the break-even odds at the clear rate, before vig. Paying longer
        than that is a losing bet however good the log looks. A floor is not a pick: the card adds the
        matchup and volume gates, and the Legs tab grades every rung.
      </div>
    </div>
  );
}
