import { useEffect, useMemo, useRef, useState } from "react";
import { teamColor, normName } from "./nflTeams";
import { SLATES, defaultSlate } from "./nflSlates";
import SlateSwitch from "./SlateSwitch";
// NFL Legs — every graded rung for the slate + a slip builder. Reads /data/nfl_legs_<slate>.json
// (automation/pipeline/grade_legs.py) and /data/nfl_usage.json (automation/pipeline/usage.py). Absorbs the old Usage tab.
// Deep link: #legs?player=<name> opens that player's rows (used by the Matchups tab's Edge Leans).

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  red:"#ff4757", amber:"#f5c518",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const POS_COLOR = { QB:"#a855f7", RB:"#00c896", WR:"#00e5ff", TE:"#f5c518" };
const LETTERS = ["F", "D", "C", "B", "A-", "A", "A+"];
const gi = g => LETTERS.indexOf(g);
const MARKETS = [["ALL","all"],["rec_yds","rec yds"],["receptions","rec"],["rush_yds","rush yds"],
  ["rush_att","rush att"],["pass_yds","pass yds"],["pass_cmps","cmp"],["pass_att","att"]];
const MARKET_LABEL = Object.fromEntries(MARKETS.slice(1));
const ATTEMPT_MARKETS = new Set(["pass_att", "pass_cmps", "rush_att"]);
const CAT = m => ["pass_yds","pass_cmps","pass_att","rec_yds","receptions"].includes(m) ? "pass" : "rush";
// Usage fields per position (per game), carried over from the old Usage tab.
const USAGE_FIELDS = {
  QB: [["att","pass att"],["passyd","pass yds"],["car","rush att"],["rushyd","rush yds"]],
  RB: [["car","carries"],["rushyd","rush yds"],["tgt","targets"],["rec","rec"]],
  WR: [["tgt","targets"],["rec","rec"],["recyd","rec yds"]],
  TE: [["tgt","targets"],["rec","rec"],["recyd","rec yds"]],
};
const USAGE_SHARES = {
  RB: [["car_share","carry share"],["tgt_share","tgt share"]], WR: [["tgt_share","tgt share"]], TE: [["tgt_share","tgt share"]],
};
const TICKETS_KEY = "ei_legs_tickets_v1";

const oddsStr = o => o == null ? "—" : (o > 0 ? "+" : "") + o;
const rungStr = r => Number.isInteger(r) ? `${r}+` : `o${r}`;
const clean = s => String(s || "").trim();
const rowKey = p => `${p.player}|${p.market}`;

// Formulas from LEGS_TAB_SPEC.md
const dec = o => o < 0 ? 1 + 100 / (-o) : 1 + o / 100;
const american = d => d >= 2 ? Math.round((d - 1) * 100) : Math.round(-100 / (d - 1));

function bestRung(p) {
  return p.rungs.reduce((b, r) =>
    !b || gi(r.grade) > gi(b.grade) || (gi(r.grade) === gi(b.grade) && r.rung > b.rung) ? r : b, null);
}

function loadTickets() {
  try { const v = JSON.parse(localStorage.getItem(TICKETS_KEY) || "[]"); return Array.isArray(v) ? v : []; }
  catch { return []; }
}
function storeTickets(t) {
  try { localStorage.setItem(TICKETS_KEY, JSON.stringify(t)); } catch { /* private window etc. — slip still works */ }
}

/* ---------- small pieces ---------- */
function GradePill({ g }) {
  const s = {
    "A+": { color:T.bg,      background:T.accent,        border:T.accent },
    "A":  { color:T.accent,  background:T.accent + "38", border:T.accent + "70" },
    "A-": { color:"#7fe0b0", background:T.accent + "12", border:T.accent + "38" },
    "B":  { color:T.amber,   background:T.amber + "18",  border:T.amber + "40" },
    "C":  { color:"#999",    background:"#ffffff0c",     border:"#ffffff1c" },
    "D":  { color:"#555",    background:"transparent",   border:"#ffffff12" },
    "F":  { color:T.red,     background:"transparent",   border:T.red + "90" },
  }[g] || {};
  return (
    <span style={{display:"inline-block",minWidth:26,textAlign:"center",fontSize:10,fontWeight:800,
      fontFamily:T.mono,borderRadius:3,padding:"2px 5px",color:s.color,background:s.background,
      border:`1px solid ${s.border}`}}>{g}</span>
  );
}

function Chip({ active, onClick, children, color = T.nfl }) {
  return (
    <button onClick={onClick} style={{padding:"4px 10px",background: active ? color + "14" : "transparent",
      border:`1px solid ${active ? color + "40" : T.border}`,borderRadius:4,
      color: active ? color : "#555",fontSize:9,fontWeight:700,fontFamily:T.mono,cursor:"pointer",
      letterSpacing:1,whiteSpace:"nowrap"}}>{children}</button>
  );
}

const selectStyle = {background:T.surface,border:`1px solid #ffffff14`,borderRadius:4,color:"#aaa",
  fontSize:10,fontFamily:T.mono,padding:"4px 6px",outline:"none"};

function Tag({ label, v }) {
  // opp_d: SOFT = easy matchup. own_vol: SOFT = high volume, TOUGH = low volume.
  const good = v === "SOFT", bad = v === "TOUGH";
  const text = label === "VOL" ? (good ? "HIGH" : bad ? "LOW" : "—") : (good ? "SOFT" : bad ? "TOUGH" : "—");
  return (
    <span style={{fontSize:9,fontFamily:T.mono,color: good ? T.accent : bad ? T.red : "#444"}}>
      <span style={{color:"#444"}}>{label} </span>{text}
    </span>
  );
}

function Last3({ vals, rung }) {
  return (
    <span style={{fontFamily:T.mono,fontSize:10,letterSpacing:-0.2}}>
      {vals.map((v, i) => (
        <span key={i} style={{color: v >= rung ? "#7fe0b0" : "#c96b74",marginRight: i < vals.length - 1 ? 5 : 0}}>
          {Math.round(v)}
        </span>
      ))}
    </span>
  );
}

function AddBtn({ onClick, on, title }) {
  return (
    <button title={title} onClick={e => { e.stopPropagation(); onClick(); }}
      style={{width:24,height:22,borderRadius:3,cursor:"pointer",fontFamily:T.mono,fontSize:13,lineHeight:1,
        border:`1px solid ${on ? T.nfl + "80" : "#ffffff1c"}`,background: on ? T.nfl + "22" : "transparent",
        color: on ? T.nfl : "#888"}}>{on ? "✓" : "+"}</button>
  );
}

/* ---------- one player/market row ---------- */
const STAT_COLS = "40px 48px 64px 70px 74px 118px 26px";

function LegRow({ p, usage, open, onToggle, onAdd, inSlip, focused }) {
  const b = bestRung(p);
  const pc = POS_COLOR[p.pos] || T.muted;
  const held = !!p.held;
  const est = p.prices === "estimated";
  const sub = clean(b.reasons?.[0]);
  const hasMain = p.rungs.some(r => r.rung === p.main_line);
  const cat = CAT(p.market);
  const u = usage.get(normName(p.player));

  return (
    <div id={`leg-${rowKey(p)}`} onClick={onToggle}
      style={{background:T.surface,borderRadius:6,marginBottom:6,cursor:"pointer",
        // longhands only: mixing `border` with `borderLeft` loses the team accent when React updates the shorthand
        borderStyle:"solid",borderWidth:"1px 1px 1px 3px",
        borderColor:`${Array(3).fill(focused ? T.nfl + "90" : open ? pc + "40" : T.border).join(" ")} ${teamColor(p.team)}`,
        opacity: held ? 0.55 : 1,
        boxShadow: focused ? `0 0 0 2px ${T.nfl}22` : "none",transition:"border-color .2s"}}>
      <div className="legs-row" style={{padding:"9px 12px",display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
        <span style={{fontSize:9,fontWeight:700,color:pc,background:pc + "18",border:`1px solid ${pc}40`,
          borderRadius:3,padding:"2px 6px",fontFamily:T.mono,minWidth:30,textAlign:"center"}}>{p.pos || "—"}</span>

        <div style={{flex:"1 1 180px",minWidth:0}}>
          <div style={{display:"flex",alignItems:"baseline",gap:8,flexWrap:"wrap"}}>
            <span style={{fontSize:14,fontWeight:700,color:T.text,fontFamily:T.head}}>{p.player}</span>
            <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>
              {p.team} · <span style={{color:"#999"}}>{MARKET_LABEL[p.market] || p.market}</span> · {p.game}
            </span>
          </div>
          {sub && <div style={{fontSize:9.5,fontFamily:T.mono,marginTop:2,
            color: held ? "#d0707a" : "#666"}}>{held ? "HOLD · " : ""}{sub}</div>}
        </div>

        <div className="legs-stats" style={{display:"grid",gridTemplateColumns:STAT_COLS,alignItems:"center",gap:8,flexShrink:0}}>
          <GradePill g={b.grade} />
          <span style={{fontSize:12,fontWeight:700,color:T.text,fontFamily:T.mono}}>{rungStr(b.rung)}</span>
          <span style={{fontSize:11,color:T.text,fontFamily:T.mono}}>
            {oddsStr(b.est_odds)}{est && <sup style={{fontSize:7,color:T.amber,marginLeft:2}}>est</sup>}
          </span>
          <span style={{fontSize:10,color:"#999",fontFamily:T.mono}}>{b.l10 ?? "—"} <span style={{color:"#555"}}>{b.l15 ?? ""}</span></span>
          <Last3 vals={p.last3} rung={b.rung} />
          <span style={{display:"flex",gap:7}}><Tag label="D" v={p.opp_d} /><Tag label="VOL" v={p.own_vol} /></span>
          <AddBtn on={inSlip(p, b)} title={`add ${rungStr(b.rung)} to slip`} onClick={() => onAdd(p, b)} />
        </div>
      </div>

      {open && (
        <div onClick={e => e.stopPropagation()} style={{borderTop:`1px solid ${T.border}`,padding:"10px 12px 12px",cursor:"default"}}>
          <div style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontFamily:T.mono,fontSize:10,minWidth:560}}>
              <thead>
                <tr style={{color:"#444",fontSize:8.5,letterSpacing:1.5,textAlign:"right"}}>
                  {["RUNG","PRICE","IMPLIED","CLEAR","L10","L15","GRADE"].map(h =>
                    <th key={h} style={{fontWeight:600,padding:"3px 8px",textAlign: h === "RUNG" ? "left" : "right"}}>{h}</th>)}
                  <th style={{fontWeight:600,padding:"3px 8px",textAlign:"left"}}>REASONS</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {p.rungs.map(r => {
                  const main = r.rung === p.main_line;
                  return (
                    <tr key={r.rung} style={{borderTop:`1px solid ${T.border}`,background: main ? "#ffffff05" : "transparent"}}>
                      <td style={{padding:"5px 8px",color:T.text,fontWeight:700,whiteSpace:"nowrap"}}>
                        {rungStr(r.rung)}
                        {main && <span style={{marginLeft:6,fontSize:8,letterSpacing:1,color:T.nfl,fontWeight:600}}>DK LINE</span>}
                      </td>
                      <td style={{padding:"5px 8px",textAlign:"right",color:T.text}}>
                        {oddsStr(r.est_odds)}{est && <sup style={{fontSize:7,color:T.amber,marginLeft:2}}>est</sup>}</td>
                      <td style={{padding:"5px 8px",textAlign:"right",color:"#888"}}>{r.implied_pct != null ? r.implied_pct.toFixed(1) + "%" : "—"}</td>
                      <td style={{padding:"5px 8px",textAlign:"right",color:T.text,fontWeight:700}}>{r.clear_pct != null ? r.clear_pct.toFixed(1) + "%" : "—"}</td>
                      <td style={{padding:"5px 8px",textAlign:"right",color:"#999"}}>{r.l10 ?? "—"}</td>
                      <td style={{padding:"5px 8px",textAlign:"right",color:"#999"}}>{r.l15 ?? "—"}</td>
                      <td style={{padding:"5px 8px",textAlign:"right"}}><GradePill g={r.grade} /></td>
                      <td style={{padding:"5px 8px",color: r.grade === "F" ? "#d0707a" : "#666",fontSize:9.5}}>
                        {r.reasons.map(clean).filter(Boolean).join(" · ") || ""}</td>
                      <td style={{padding:"5px 0 5px 8px",textAlign:"right"}}>
                        <AddBtn on={inSlip(p, r)} title={`add ${rungStr(r.rung)} to slip`} onClick={() => onAdd(p, r)} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {!hasMain && (
            <div style={{fontSize:9.5,color:"#555",fontFamily:T.mono,marginTop:6}}>
              DK line {rungStr(p.main_line)} {oddsStr(p.main_odds)} graded below C — not listed.
            </div>
          )}

          <div style={{display:"flex",gap:18,flexWrap:"wrap",marginTop:12,paddingTop:10,
            borderTop:`1px solid ${T.border}`,fontSize:10,fontFamily:T.mono,color:"#777"}}>
            <span>Last 3: <span style={{color:T.text}}>{p.last3.map(v => Math.round(v)).join(" · ")}</span></span>
            <span>Games in sample: <span style={{color:T.text}}>{p.games}</span></span>
            <span>Spread: <span style={{color:T.text}}>
              {p.spread == null ? "—" : `${p.team} ${p.spread > 0 ? "+" : ""}${p.spread}`}</span></span>
            <span>Opp {cat} D: <span style={{color: p.opp_d === "SOFT" ? T.accent : p.opp_d === "TOUGH" ? T.red : T.text}}>
              {p.opp_d}</span></span>
            <span>Own {cat} volume: <span style={{color: p.own_vol === "SOFT" ? T.accent : p.own_vol === "TOUGH" ? T.red : T.text}}>
              {p.own_vol === "SOFT" ? "HIGH" : p.own_vol === "TOUGH" ? "LOW" : p.own_vol}</span></span>
          </div>

          {/* usage (automation/pipeline/usage.py) — this season, then last season */}
          <div style={{marginTop:10,fontSize:10,fontFamily:T.mono,color:"#777"}}>
            <div style={{fontSize:8.5,letterSpacing:2,color:"#444",marginBottom:4}}>USAGE / GM</div>
            {!u && <span style={{color:"#444"}}>no usage row for this player</span>}
            {u && [["cur", usage.windows?.cur], ["prev", usage.windows?.prev]].map(([w, label]) => {
              const x = u[w];
              if (!x) return null;
              return (
                <div key={w} style={{display:"flex",gap:14,flexWrap:"wrap",alignItems:"baseline",marginBottom:3,
                  color: w === "prev" ? "#5c5c5c" : "#777"}}>
                  <span style={{minWidth:92,color:"#555"}}>
                    {label} · {x.games} g{x.team !== p.team ? ` · ${x.team}` : ""}</span>
                  {(USAGE_FIELDS[u.pos] || []).map(([k, name]) => (
                    <span key={k}><span style={{color: w === "cur" ? T.text : "#aaa",fontWeight:700}}>{x[k] ?? "—"}</span> {name}</span>
                  ))}
                  {(USAGE_SHARES[u.pos] || []).map(([k, name]) => x[k] != null && (
                    <span key={k}><span style={{color: w === "cur" ? T.nfl : "#6a9fa6",fontWeight:700}}>{x[k]}%</span> {name}</span>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- slip ---------- */
function Slip({ slip, setSlip, notice, tickets, setTickets, meta, slate, onSave }) {
  const setOdds = (i, text) => setSlip(s => s.map((l, j) => {
    if (j !== i) return l;
    const n = parseInt(text.replace(/[−–]/g, "-"), 10);
    const ok = /^[+-]?\d+$/.test(text.trim().replace(/[−–]/g, "-")) && Math.abs(n) >= 100;
    return { ...l, oddsText: text, odds: ok ? n : l.odds, oddsBad: !ok };
  }));
  const remove = i => setSlip(s => s.filter((_, j) => j !== i));

  const pd = slip.reduce((a, l) => a * dec(l.odds), 1);
  const hitKnown = slip.every(l => l.clear_pct != null);
  const hit = slip.reduce((a, l) => a * (l.clear_pct ?? 0) / 100, 1);
  const be = 1 / pd;
  const ev = hit * (pd - 1) - (1 - hit);

  // Warnings (never blocking — blocking happens on add)
  const warns = [];
  const byGame = {};
  slip.forEach(l => { (byGame[l.game] = byGame[l.game] || []).push(l); });
  Object.entries(byGame).forEach(([g, ls]) => { if (ls.length > 1)
    warns.push({ t:`Same game (${g}): these legs rise and fall together.`, c:T.amber }); });
  const minLegs = slate === "tnf" || slate === "mnf" ? 2 : 3;          // single-game slates allow a 2-leg ticket
  if (slip.length && (slip.length < minLegs || slip.length > 4))
    warns.push({ t:`${minLegs}–4 legs per ticket — this one has ${slip.length}.`, c:T.amber });
  if (slip.length === 2 && minLegs === 2)
    warns.push({ t:"2-leg ticket: reduced payout.", c:"#888" });
  slip.forEach(l => {
    if (l.odds < -400) warns.push({ t:`Price worse than −400: ${l.player} ${rungStr(l.rung)}.`, c:T.amber });
    if (l.danger) warns.push({ t:`${l.player} ${MARKET_LABEL[l.market]}: ${l.reasons.map(clean).filter(Boolean).join("; ") || "hard hold"}.`, c:T.red });
    if (l.repeatOf) warns.push({ t:`${l.player} is already on Ticket ${l.repeatOf} (A+ may anchor two).`, c:"#888" });
  });

  const slateTickets = tickets.filter(t => t.season === meta.season && t.week === meta.week);
  const copy = t => {
    const text = t.legs.map(l => `${l.player} ${rungStr(l.rung)} ${MARKET_LABEL[l.market] || l.market} @ ${oddsStr(l.odds)}`).join(", ");
    try { navigator.clipboard.writeText(text); } catch { window.prompt("Copy legs", text); }
  };
  const del = id => { const next = tickets.filter(t => t.id !== id); setTickets(next); storeTickets(next); };

  const stat = (label, value, color = T.text) => (
    <div>
      <div style={{fontSize:8,color:"#444",letterSpacing:2,marginBottom:3}}>{label}</div>
      <div style={{fontSize:15,fontWeight:800,color,fontFamily:T.mono,letterSpacing:-0.5}}>{value}</div>
    </div>
  );

  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:14,fontFamily:T.mono}}>
      <div style={{display:"flex",alignItems:"baseline",justifyContent:"space-between",marginBottom:10}}>
        <div style={{fontSize:15,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>SLIP</div>
        <div style={{fontSize:9,color:"#555"}}>{slip.length} leg{slip.length === 1 ? "" : "s"}</div>
      </div>

      {slip.length === 0 && <div style={{fontSize:10,color:"#555",lineHeight:1.6,padding:"4px 0 10px"}}>
        Tap + on a row for its best rung, or open a ladder to take a different one.</div>}

      {slip.map((l, i) => (
        <div key={`${l.player}|${l.market}`} style={{display:"flex",alignItems:"center",gap:8,padding:"7px 0",
          borderTop: i ? `1px solid ${T.border}` : "none"}}>
          <div style={{flex:1,minWidth:0}}>
            <div style={{fontSize:12,fontWeight:700,fontFamily:T.head,color: l.danger ? T.red : T.text,
              whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{l.player}</div>
            <div style={{fontSize:9.5,color:"#777"}}>{rungStr(l.rung)} {MARKET_LABEL[l.market]}</div>
          </div>
          <input value={l.oddsText} onChange={e => setOdds(i, e.target.value)} title="overtype with the real DK price"
            style={{width:54,background:"transparent",border:`1px solid ${l.oddsBad ? T.red : "#ffffff18"}`,borderRadius:3,
              color: l.odds < -400 ? T.amber : T.text,fontFamily:T.mono,fontSize:11,padding:"3px 5px",textAlign:"right",outline:"none"}} />
          <GradePill g={l.grade} />
          <button onClick={() => remove(i)} title="remove"
            style={{background:"transparent",border:"none",color:"#555",cursor:"pointer",fontSize:13,padding:"0 2px"}}>×</button>
        </div>
      ))}

      {notice && <div style={{fontSize:10,color:T.red,background:T.red + "10",border:`1px solid ${T.red}40`,
        borderRadius:4,padding:"6px 8px",margin:"8px 0",lineHeight:1.5}}>{notice}</div>}

      {slip.length > 0 && <>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"12px 10px",margin:"12px 0 10px",
          paddingTop:12,borderTop:`1px solid ${T.border}`}}>
          {stat("PAYOUT", oddsStr(american(pd)), T.nfl)}
          {stat("DECIMAL", pd.toFixed(2))}
          {stat("HIT %", hitKnown ? (hit * 100).toFixed(1) + "%" : "—")}
          {stat("BREAKEVEN", (be * 100).toFixed(1) + "%")}
          {stat("EV / UNIT", hitKnown ? `${ev >= 0 ? "+" : ""}${ev.toFixed(2)}u` : "—",
            !hitKnown ? T.text : ev >= 0 ? T.accent : T.red)}
        </div>
        {warns.map((w, i) => <div key={i} style={{fontSize:9.5,color:w.c,lineHeight:1.5,marginBottom:4}}>! {w.t}</div>)}
        <button onClick={onSave} style={{width:"100%",marginTop:8,padding:"8px 0",borderRadius:4,cursor:"pointer",
          background:T.nfl + "18",border:`1px solid ${T.nfl}50`,color:T.nfl,fontFamily:T.mono,fontSize:10,
          fontWeight:700,letterSpacing:2}}>SAVE TICKET</button>
      </>}

      {slateTickets.length > 0 && (
        <div style={{marginTop:16,paddingTop:12,borderTop:`1px solid ${T.border}`}}>
          <div style={{fontSize:8.5,color:"#444",letterSpacing:2,marginBottom:8}}>SAVED · WEEK {meta.week}</div>
          {slateTickets.map(t => (
            <div key={t.id} style={{marginBottom:10,opacity: t.slate === slate ? 1 : 0.6}}>
              <div style={{display:"flex",alignItems:"center",gap:8}}>
                <span style={{fontSize:11,fontWeight:700,color:T.text}}>{t.name}</span>
                <span style={{fontSize:9.5,color:T.nfl}}>{oddsStr(american(t.legs.reduce((a, l) => a * dec(l.odds), 1)))}</span>
                <span style={{flex:1}} />
                <button onClick={() => copy(t)} style={{fontSize:8.5,letterSpacing:1,fontFamily:T.mono,cursor:"pointer",
                  background:"transparent",border:"1px solid #ffffff18",borderRadius:3,color:"#888",padding:"2px 6px"}}>COPY LEGS</button>
                <button onClick={() => del(t.id)} title="remove ticket" style={{background:"transparent",border:"none",
                  color:"#444",cursor:"pointer",fontSize:12}}>×</button>
              </div>
              <div style={{fontSize:9.5,color:"#666",lineHeight:1.5,marginTop:2}}>
                {t.legs.map(l => `${l.player} ${rungStr(l.rung)} ${MARKET_LABEL[l.market] || l.market}`).join(" · ")}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{marginTop:14,paddingTop:10,borderTop:`1px solid ${T.border}`,fontSize:9,color:"#555",lineHeight:1.6}}>
        Flat units. Card tickets are graded Tuesday; your saved slips are yours and are not graded.
      </div>
    </div>
  );
}

/* ---------- tab ---------- */
function readHashPlayer() {
  const h = window.location.hash;
  const i = h.indexOf("?");
  return i < 0 ? null : new URLSearchParams(h.slice(i + 1)).get("player");
}

export default function LegsHub() {
  const [files, setFiles] = useState({});          // slate -> data | null (missing)
  const [slate, setSlate] = useState(null);
  const [usageRows, setUsageRows] = useState(null);
  const [minGrade, setMinGrade] = useState("A-");
  const [market, setMarket] = useState("ALL");
  const [team, setTeam] = useState("ALL");
  const [game, setGame] = useState("ALL");
  const [hideHolds, setHideHolds] = useState(false);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(() => new Set());
  const [slip, setSlip] = useState([]);
  const [notice, setNotice] = useState(null);
  const [tickets, setTickets] = useState(loadTickets);
  const [focus, setFocus] = useState(null);               // deep-linked row: { key } or { missing }
  const filesRef = useRef({});

  // #legs?player=X -> open that player's rows on whichever slate has them, loosening filters so they show.
  // Returns false when no posted slate has the player.
  const applyDeepLink = (name, fs) => {
    const n = normName(name);
    const order = ["sun", "tnf", "mnf"].filter(s => fs[s]);   // a player is on one slate a week
    const hit = order.find(s => fs[s].players.some(p => normName(p.player) === n));
    try { history.replaceState(null, "", "#legs"); } catch { /* the same link can then fire again */ }
    if (!hit) { setFocus({ missing: name }); return false; }
    const rows = fs[hit].players.filter(p => normName(p.player) === n);
    setSlate(hit); setMinGrade("C"); setMarket("ALL"); setTeam("ALL"); setGame("ALL");
    setHideHolds(false); setQ(rows[0].player);
    setOpen(new Set(rows.map(rowKey)));
    setFocus({ key: rowKey(rows[0]) });
    return true;
  };

  useEffect(() => {
    const bust = `?t=${Date.now()}`;
    Promise.all(SLATES.map(([s]) => fetch(`/data/nfl_legs_${s}.json${bust}`)
      .then(r => r.ok ? r.json() : null).catch(() => null)))
      .then(all => {
        const fs = Object.fromEntries(SLATES.map(([s], i) => [s, all[i]?.players ? all[i] : null]));
        filesRef.current = fs; setFiles(fs);
        const want = readHashPlayer();
        if (!want || !applyDeepLink(want, fs)) setSlate(defaultSlate(fs));
      });
    fetch(`/data/nfl_usage.json${bust}`).then(r => r.ok ? r.json() : null).then(setUsageRows).catch(() => setUsageRows(null));
    const onHash = () => { const p = readHashPlayer(); if (p && Object.keys(filesRef.current).length) applyDeepLink(p, filesRef.current); };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const loaded = Object.keys(files).length > 0;
  const available = SLATES.map(([s]) => s).filter(s => files[s]);

  // Scroll the deep-linked row into view once it renders.
  useEffect(() => {
    if (!focus?.key) return;
    const el = document.getElementById(`leg-${focus.key}`);
    if (el) el.scrollIntoView({ behavior:"smooth", block:"center" });
    const t = setTimeout(() => setFocus(null), 2600);
    return () => clearTimeout(t);
  }, [focus, slate]);

  const data = slate ? files[slate] : null;
  const usage = useMemo(() => {
    const m = new Map((usageRows?.players || []).map(u => [normName(u.player), u]));
    m.windows = usageRows?.meta?.windows;
    return m;
  }, [usageRows]);

  const players = useMemo(() => data?.players || [], [data]);
  const teams = useMemo(() => [...new Set(players.map(p => p.team))].sort(), [players]);
  const games = useMemo(() => [...new Set(players.map(p => p.game))].sort(), [players]);

  const rows = useMemo(() => {
    const nq = normName(q);
    return players
      .filter(p => p.rungs?.length)
      .filter(p => p.held ? !hideHolds : gi(bestRung(p).grade) >= gi(minGrade))
      .filter(p => market === "ALL" || p.market === market)
      .filter(p => team === "ALL" || p.team === team)
      .filter(p => game === "ALL" || p.game === game)
      .filter(p => !nq || normName(p.player).includes(nq))
      .map(p => ({ p, b: bestRung(p) }))
      .sort((x, y) => (!!x.p.held - !!y.p.held) || (gi(y.b.grade) - gi(x.b.grade)) ||
        ((y.b.clear_pct ?? 0) - (x.b.clear_pct ?? 0)) || x.p.player.localeCompare(y.p.player))
      .map(x => x.p);
  }, [players, minGrade, market, team, game, hideHolds, q]);

  const toggle = k => setOpen(s => { const n = new Set(s); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const inSlip = (p, r) => slip.some(l => l.player === p.player && l.market === p.market && l.rung === r.rung);

  const addLeg = (p, r) => {
    setNotice(null);
    const same = l => l.player === p.player && l.market === p.market;
    if (slip.some(l => same(l) && l.rung === r.rung)) { setSlip(s => s.filter(l => !same(l))); return; }  // tap again = remove
    const saved = tickets.find(t => t.season === data.meta.season && t.week === data.meta.week &&
      t.legs.some(same));
    if (saved) {
      if (r.grade !== "A+") { setNotice(`This leg is already on Ticket ${saved.name}. Only an A+ rung may anchor two tickets.`); return; }
      if (slip.some(l => l.repeatOf && !same(l))) { setNotice(`This leg is already on Ticket ${saved.name}, and this ticket already repeats one A+ leg.`); return; }
    }
    const leg = { player:p.player, market:p.market, team:p.team, game:p.game, rung:r.rung, odds:r.est_odds,
      oddsText:oddsStr(r.est_odds), grade:r.grade, clear_pct:r.clear_pct ?? null, reasons:r.reasons || [],
      danger: r.grade === "F" || (ATTEMPT_MARKETS.has(p.market) && r.reasons?.some(x => /blowout/.test(x))),
      repeatOf: saved ? saved.name : null };
    // Another rung of the same player/market replaces the one in the slip.
    setSlip(s => s.some(same) ? s.map(l => same(l) ? leg : l) : [...s, leg]);
  };

  const saveTicket = () => {
    if (!slip.length || !data) return;
    const prefix = slate.toUpperCase();
    const nums = tickets.filter(t => t.season === data.meta.season && t.week === data.meta.week && t.slate === slate)
      .map(t => parseInt(t.name.split("-")[1], 10) || 0);
    const t = { id:`${Date.now()}`, name:`${prefix}-${Math.max(0, ...nums) + 1}`, season:data.meta.season,
      week:data.meta.week, slate, saved:new Date().toISOString(),
      legs: slip.map(({ player, market, rung, odds, grade, clear_pct, game }) => ({ player, market, rung, odds, grade, clear_pct, game })) };
    const next = [...tickets, t];
    setTickets(next); storeTickets(next); setSlip([]); setNotice(null);
  };

  const posted = data?.meta?.generated ? new Date(data.meta.generated).toLocaleString(undefined,
    { weekday:"short", month:"short", day:"numeric", hour:"numeric", minute:"2-digit" }) : null;

  return (
    <div style={{padding:"28px 16px 80px",maxWidth:1240,margin:"0 auto",fontFamily:T.mono}}>
      <style>{`
        .legs-grid { display:grid; grid-template-columns:minmax(0,65fr) minmax(300px,35fr); gap:20px; align-items:start; }
        .legs-slip { position:sticky; top:72px; max-height:calc(100vh - 90px); overflow-y:auto; }
        .legs-colhead { display:grid; }
        /* a row needs ~740px on one line; below that width its stats wrap and the column header can't align */
        @media (max-width: 1180px) {
          .legs-grid { grid-template-columns:1fr; }
          .legs-slip { position:static; max-height:none; order:-1; }
        }
        @media (max-width: 800px) {
          .legs-colhead { display:none; }
          .legs-stats { display:flex !important; flex-wrap:wrap; gap:8px 12px !important; flex-shrink:1 !important; }
        }
      `}</style>

      {/* header */}
      <div style={{display:"flex",alignItems:"baseline",gap:14,flexWrap:"wrap",marginBottom:4}}>
        <div style={{fontSize:22,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>
          LEGS{data ? ` · WEEK ${data.meta.week}` : ""}
        </div>
        <SlateSwitch files={files} slate={slate} onChange={s => { setSlate(s); setOpen(new Set()); }} />
        {posted && <div style={{fontSize:10,color:T.muted}}>posted {posted}</div>}
      </div>
      <div title={data?.meta?.grade_key} style={{fontSize:10,color:"#777",marginBottom:18,maxWidth:"72ch",lineHeight:1.6}}>
        Grade = how often this rung hits. It says nothing about whether the price is good.
      </div>

      {!loaded && <div style={{fontSize:10,color:"#444"}}>loading…</div>}
      {loaded && !available.length && <div style={{fontSize:11,color:"#777",background:T.surface,
        border:`1px solid ${T.border}`,borderRadius:6,padding:16}}>No slate is posted yet this week.</div>}

      {data && (
        <div className="legs-grid">
          <div>
            {/* filters */}
            <div style={{display:"flex",flexDirection:"column",gap:7,marginBottom:14}}>
              <div style={{display:"flex",gap:4,flexWrap:"wrap",alignItems:"center"}}>
                <span style={{fontSize:9,color:"#444",letterSpacing:2,marginRight:4}}>GRADE ≥</span>
                {["A+","A","A-","B","C"].map(g => <Chip key={g} active={minGrade === g} onClick={() => setMinGrade(g)}
                  color={g === "B" ? T.amber : g === "C" ? "#aaa" : T.accent}>{g.replace("-", "−")}</Chip>)}
                <span style={{width:10}} />
                <label style={{display:"inline-flex",alignItems:"center",gap:5,fontSize:9,color:"#666",letterSpacing:1,cursor:"pointer"}}>
                  <input type="checkbox" checked={hideHolds} onChange={e => setHideHolds(e.target.checked)}
                    style={{accentColor:T.nfl,margin:0}} /> HIDE HOLDS (F)
                </label>
              </div>
              <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
                {MARKETS.map(([k, label]) => <Chip key={k} active={market === k} onClick={() => setMarket(k)}>{label.toUpperCase()}</Chip>)}
              </div>
              <div style={{display:"flex",gap:6,flexWrap:"wrap",alignItems:"center"}}>
                <select value={team} onChange={e => setTeam(e.target.value)} style={selectStyle}>
                  <option value="ALL">all teams</option>{teams.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <select value={game} onChange={e => setGame(e.target.value)} style={selectStyle}>
                  <option value="ALL">all games</option>{games.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
                <input value={q} onChange={e => setQ(e.target.value)} placeholder="search player"
                  style={{...selectStyle,color:T.text,padding:"5px 8px",width:150}} />
                {q && <button onClick={() => setQ("")} style={{...selectStyle,cursor:"pointer",color:"#666"}}>clear</button>}
              </div>
            </div>

            {focus?.missing && (
              <div style={{fontSize:10,color:"#888",background:T.surface,border:`1px solid ${T.border}`,borderRadius:6,
                padding:"8px 12px",marginBottom:10}}>{focus.missing} has no graded rungs on the posted slates.</div>
            )}

            {/* column header */}
            <div className="legs-colhead" style={{gridTemplateColumns:`1fr ${STAT_COLS}`,gap:8,padding:"0 15px 6px 55px",
              fontSize:8,color:"#444",letterSpacing:1.5}}>
              <span />
              <span>GRADE</span><span>RUNG</span><span>PRICE</span><span>L10 / 15</span><span>LAST 3</span><span>OPP D · VOL</span><span />
            </div>

            {rows.length === 0 && <div style={{padding:"28px 0",fontSize:11,color:"#444",textAlign:"center"}}>
              No legs at that grade for this filter.</div>}
            {rows.map(p => (
              <LegRow key={rowKey(p)} p={p} usage={usage} open={open.has(rowKey(p))} onToggle={() => toggle(rowKey(p))}
                onAdd={addLeg} inSlip={inSlip} focused={focus?.key === rowKey(p)} />
            ))}
            <div style={{marginTop:10,fontSize:9,color:"#444"}}>{rows.length} of {players.length} player/markets shown</div>
          </div>

          <div className="legs-slip">
            <Slip slip={slip} setSlip={setSlip} notice={notice} tickets={tickets} setTickets={setTickets}
              meta={data.meta} slate={slate} onSave={saveTicket} />
            {data.meta.rules?.length > 0 && (
              <div style={{fontSize:9,color:"#444",lineHeight:1.7,marginTop:10,padding:"0 4px"}}>
                <span style={{letterSpacing:2}}>CARD RULES · </span>{data.meta.rules.join(" · ")}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
