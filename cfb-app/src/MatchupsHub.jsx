import { useEffect, useMemo, useState } from "react";
import { teamColor, normName } from "./nflTeams";
// NFL Matchups — defense x slot heat map + this week's edge leans.
// Reads /data/nfl_matchups.json (automation/pipeline/matchups.py). Replaces the old Usage tab.

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  red:"#ff4757",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const SLOTS = ["QB", "RB", "WR1", "WR2", "TE", "RUN", "PASS"];
const DAYS = { Thursday:"Thu", Sunday:"Sun", Monday:"Mon", Saturday:"Sat", Friday:"Fri" };
const LEGS_SLATES = ["tnf", "sun", "mnf"];
const norm = s => String(s || "").trim().toLowerCase();

// Rank 1-8 red (tough for the offense), 9-24 neutral, 25-32 green (soft). Stronger toward the extremes.
function rankColor(rank, n = 32) {
  if (rank == null) return "transparent";
  const hex = a => Math.round(a * 255).toString(16).padStart(2, "0");
  if (rank <= 8)      return T.red    + hex(0.12 + 0.30 * (8 - rank) / 7);
  if (rank >= n - 7)  return T.accent + hex(0.08 + 0.24 * (rank - (n - 7)) / 7);
  return "transparent";
}

// 1 = fewest allowed. Nulls are unranked.
function rankBy(rows, get) {
  const ranked = rows.filter(r => get(r) != null).sort((a, b) => get(a) - get(b));
  const out = new Map();
  ranked.forEach((r, i) => out.set(r.team, i + 1));
  return out;
}

function Toggle({ options, value, onChange, disabled }) {
  return (
    <div style={{display:"inline-flex",border:`1px solid #ffffff14`,borderRadius:4,
      overflow:"hidden",opacity:disabled ? 0.35 : 1}}>
      {options.map(([k, label]) => (
        <button key={k} disabled={disabled} onClick={() => onChange(k)}
          style={{padding:"5px 10px",fontSize:10,fontFamily:T.mono,letterSpacing:1,
            border:"none",cursor:disabled ? "default" : "pointer",
            background: value === k ? T.nfl + "1c" : "transparent",
            color: value === k ? T.nfl : "#666", fontWeight: value === k ? 700 : 500}}>
          {label}
        </button>
      ))}
    </div>
  );
}

function Chip({ active, onClick, children, color = T.nfl }) {
  return (
    <button onClick={onClick}
      style={{padding:"4px 9px",fontSize:10,fontFamily:T.mono,borderRadius:3,cursor:"pointer",
        border:`1px solid ${active ? color + "60" : "#ffffff12"}`,
        background: active ? color + "18" : "transparent",
        color: active ? color : "#666", fontWeight: active ? 700 : 500}}>
      {children}
    </button>
  );
}

function SectionLabel({ children }) {
  return <div style={{fontSize:9,color:"#444",letterSpacing:3,marginBottom:10}}>{children}</div>;
}

/* ---------- Section 1: heat map ---------- */
function HeatMap({ data }) {
  const [basis, setBasis] = useState("blend");      // blend | cur
  const [venue, setVenue] = useState("all");        // all | home | away
  const [sort, setSort] = useState({ key:"PASS", dir:"desc" });
  const [q, setQ] = useState("");

  const valueOf = (d, s) => {
    const c = d.slots[s];
    if (!c) return null;
    if (venue === "home") return c.home_pg;
    if (venue === "away") return c.away_pg;
    return basis === "cur" ? c.cur_pg : c.yds_pg;
  };

  // Re-rank per view so color always matches the numbers on screen (Blend reproduces the pipeline's ranks).
  const ranks = useMemo(() => Object.fromEntries(
    SLOTS.map(s => [s, rankBy(data.defenses, d => valueOf(d, s))])
  ), [data, basis, venue]); // eslint-disable-line react-hooks/exhaustive-deps

  const rows = useMemo(() => {
    const f = data.defenses.filter(d => !q || norm(d.team).includes(norm(q)));
    const sign = sort.dir === "asc" ? 1 : -1;
    return [...f].sort((a, b) => {
      if (sort.key === "team") return sign * a.team.localeCompare(b.team);
      const va = valueOf(a, sort.key), vb = valueOf(b, sort.key);
      if (va == null) return 1;
      if (vb == null) return -1;
      return sign * (va - vb);
    });
  }, [data, q, sort, basis, venue]); // eslint-disable-line react-hooks/exhaustive-deps

  const clickSort = key => setSort(s => s.key === key
    ? { key, dir: s.dir === "asc" ? "desc" : "asc" }
    : { key, dir: key === "team" ? "asc" : "desc" });

  const n = data.defenses.length;
  const arrow = key => sort.key === key ? (sort.dir === "asc" ? " ▲" : " ▼") : "";
  const th = {position:"sticky",top:0,background:"#0a0f1a",zIndex:2,padding:"8px 6px",
    fontSize:10,fontWeight:700,letterSpacing:1,cursor:"pointer",userSelect:"none",
    borderBottom:"1px solid #ffffff14",whiteSpace:"nowrap"};
  const venueLabel = venue === "home" ? "defense at home, 2025–26" : venue === "away" ? "defense on the road, 2025–26" : null;

  return (
    <div style={{marginBottom:34}}>
      {/* controls */}
      <div style={{display:"flex",gap:10,flexWrap:"wrap",alignItems:"center",marginBottom:10}}>
        <Toggle value={basis} onChange={setBasis} disabled={venue !== "all"}
          options={[["blend","BLEND"],[ "cur", `${data.meta.season} ONLY`]]} />
        <Toggle value={venue} onChange={setVenue}
          options={[["all","ALL"],["home","HOME"],["away","AWAY"]]} />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="search team"
          style={{background:"transparent",border:"1px solid #ffffff14",borderRadius:4,
            padding:"5px 9px",fontSize:10,fontFamily:T.mono,color:T.text,width:110,outline:"none"}} />
        <div style={{marginLeft:"auto",fontSize:9,color:"#666",fontFamily:T.mono,textAlign:"right",lineHeight:1.5}}>
          {venueLabel
            ? <>{venueLabel.toUpperCase()}<br /><span style={{color:"#444"}}>not blended</span></>
            : basis === "cur"
              ? <>{data.meta.season} ONLY<br /><span style={{color:"#444"}}>{data.meta.blend.match(/\(.*\)/)?.[0] || ""}</span></>
              : <>BLEND<br /><span style={{color:T.nfl}}>{data.meta.blend}</span></>}
        </div>
      </div>

      {/* grid */}
      <div style={{overflow:"auto",maxHeight:"72vh",border:`1px solid ${T.border}`,borderRadius:6,
        background:T.surface}}>
        <table style={{borderCollapse:"separate",borderSpacing:0,width:"100%",minWidth:520,
          fontFamily:T.mono,fontSize:11}}>
          <thead>
            <tr>
              <th onClick={() => clickSort("team")}
                style={{...th,left:0,zIndex:3,textAlign:"left",paddingLeft:12,
                  color: sort.key === "team" ? T.nfl : "#666"}}>DEF{arrow("team")}</th>
              {SLOTS.map(s => (
                <th key={s} onClick={() => clickSort(s)}
                  style={{...th,textAlign:"right",paddingRight:10,
                    color: sort.key === s ? T.nfl : "#888"}}>{s}{arrow(s)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(d => (
              <tr key={d.team}>
                <td style={{position:"sticky",left:0,zIndex:1,background:T.surface,
                  borderLeft:`3px solid ${teamColor(d.team)}`,borderBottom:`1px solid ${T.border}`,
                  padding:"5px 10px 5px 9px",fontWeight:700,color:T.text,letterSpacing:1}}>
                  {d.team}
                </td>
                {SLOTS.map(s => {
                  const v = valueOf(d, s), rk = ranks[s].get(d.team), c = d.slots[s];
                  const tip = v == null ? "no games" :
                    `${d.team} vs ${s}: rank ${rk} of ${n}\n` +
                    `blend ${c.yds_pg} · ${data.meta.season - 1} ${c.prev_pg ?? "—"} · ` +
                    `${data.meta.season} ${c.cur_pg ?? "—"} (${c.n_cur} g)\nhome ${c.home_pg ?? "—"} · away ${c.away_pg ?? "—"}`;
                  return (
                    <td key={s} title={tip}
                      style={{textAlign:"right",padding:"5px 10px 5px 6px",whiteSpace:"nowrap",
                        background:rankColor(rk, n),borderBottom:`1px solid ${T.border}`,
                        color: v == null ? "#444" : sort.key === s ? T.text : "#ccc",
                        fontWeight: sort.key === s ? 700 : 400}}>
                      {v == null ? "—" : v.toFixed(1)}
                      <sup style={{fontSize:8,color:"#ffffff55",marginLeft:3,
                        display:"inline-block",minWidth:12,textAlign:"left"}}>{rk ?? ""}</sup>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* legend */}
      <div style={{display:"flex",gap:14,flexWrap:"wrap",marginTop:8,fontSize:9,color:"#555",fontFamily:T.mono}}>
        <span><span style={{display:"inline-block",width:10,height:10,background:rankColor(1),
          verticalAlign:"middle",marginRight:5,borderRadius:2}} />1–8 tough</span>
        <span><span style={{display:"inline-block",width:10,height:10,border:"1px solid #ffffff14",
          verticalAlign:"middle",marginRight:5,borderRadius:2}} />9–24</span>
        <span><span style={{display:"inline-block",width:10,height:10,background:rankColor(32),
          verticalAlign:"middle",marginRight:5,borderRadius:2}} />25–32 soft</span>
        <span style={{color:"#444"}}>yards allowed per game · superscript = rank · hover for splits · WR1/WR2 = most/second-most targeted WR that game</span>
      </div>
    </div>
  );
}

/* ---------- Section 2: edge leans ---------- */
function LeanRow({ l, graded, last }) {
  const outdoors = l.roof === "outdoors";
  const soft = l.tag === "SOFT";
  const name = graded
    ? <a href={`#legs?player=${encodeURIComponent(l.player)}`}
        style={{color:T.text,textDecoration:"none",borderBottom:`1px dotted ${T.nfl}80`}}>{l.player}</a>
    : <span style={{color:T.text}}>{l.player}</span>;
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap",
      padding:"8px 12px 8px 10px",borderLeft:`3px solid ${teamColor(l.team)}`,
      borderBottom: last ? "none" : `1px solid ${T.border}`,fontSize:11,fontFamily:T.mono}}>
      <span style={{fontWeight:700,fontFamily:T.head,fontSize:14,letterSpacing:0.3,minWidth:150}}>{name}</span>
      <span style={{color:T.nfl,fontWeight:700,minWidth:36}}>{l.slot}</span>
      <span style={{color:"#888",minWidth:92}}>
        {l.team} <span style={{color:"#555"}}>{l.home ? "vs" : "@"}</span> {l.opp}
      </span>
      <span style={{color: soft ? T.accent : T.red,fontWeight:700,minWidth:120}}>
        #{l.opp_rank} <span style={{color:"#666",fontWeight:400}}>({l.opp_yds_pg} allowed)</span>
      </span>
      <span style={{color:"#666"}}>{DAYS[l.day] || l.day}</span>
      {outdoors && (
        <span style={{fontSize:8.5,letterSpacing:1.5,color:"#f5c518",border:"1px solid #f5c51840",
          background:"#f5c51812",borderRadius:3,padding:"2px 6px"}}>OUTDOORS</span>
      )}
    </div>
  );
}

function EdgeLeans({ data, graded }) {
  const [slot, setSlot] = useState("ALL");
  const [day, setDay] = useState("ALL");
  const [tag, setTag] = useState("ALL");

  const days = [...new Set(data.edge_leans.map(l => l.day))]
    .sort((a, b) => ["Thursday","Friday","Saturday","Sunday","Monday"].indexOf(a) -
                    ["Thursday","Friday","Saturday","Sunday","Monday"].indexOf(b));
  const f = data.edge_leans.filter(l =>
    (slot === "ALL" || l.slot === slot) && (day === "ALL" || l.day === day) && (tag === "ALL" || l.tag === tag));
  const soft  = f.filter(l => l.tag === "SOFT").sort((a, b) => b.opp_rank - a.opp_rank);
  const tough = f.filter(l => l.tag === "TOUGH").sort((a, b) => a.opp_rank - b.opp_rank);

  const list = (label, rows, color) => rows.length > 0 && (
    <div style={{marginBottom:20}}>
      <div style={{fontSize:9,letterSpacing:3,marginBottom:8,color}}>{label} · {rows.length}</div>
      <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:6,overflow:"hidden"}}>
        {rows.map((l, i) => (
          <LeanRow key={`${l.player}-${l.slot}`} l={l} last={i === rows.length - 1}
            graded={graded.has(normName(l.player))} />
        ))}
      </div>
    </div>
  );

  return (
    <div>
      <div style={{display:"flex",alignItems:"baseline",gap:12,flexWrap:"wrap",marginBottom:4}}>
        <div style={{fontSize:18,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>
          EDGE LEANS · WEEK {data.meta.week}
        </div>
      </div>
      <div style={{fontSize:10,color:"#777",marginBottom:14,maxWidth:"72ch",lineHeight:1.6}}>
        Leans are matchup only. A soft matchup with no volume is not a floor — check the Legs tab.
      </div>

      <div style={{display:"flex",flexDirection:"column",gap:7,marginBottom:18}}>
        <div style={{display:"flex",gap:5,flexWrap:"wrap"}}>
          {["ALL", ...SLOTS].map(s => <Chip key={s} active={slot === s} onClick={() => setSlot(s)}>{s}</Chip>)}
        </div>
        <div style={{display:"flex",gap:5,flexWrap:"wrap"}}>
          {["ALL", ...days].map(d => <Chip key={d} active={day === d} onClick={() => setDay(d)}>
            {d === "ALL" ? "ALL DAYS" : (DAYS[d] || d).toUpperCase()}</Chip>)}
          <span style={{width:10}} />
          <Chip active={tag === "ALL"} onClick={() => setTag("ALL")}>BOTH</Chip>
          <Chip active={tag === "SOFT"} onClick={() => setTag("SOFT")} color={T.accent}>SOFT</Chip>
          <Chip active={tag === "TOUGH"} onClick={() => setTag("TOUGH")} color={T.red}>TOUGH</Chip>
        </div>
      </div>

      {list("SOFT · WORST DEFENSE FIRST", soft, T.accent)}
      {list("TOUGH · BEST DEFENSE FIRST", tough, T.red)}
      {soft.length + tough.length === 0 && (
        <div style={{fontSize:10,color:"#555",padding:"12px 0"}}>No leans match these filters.</div>
      )}
    </div>
  );
}

export default function MatchupsHub() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(false);
  const [graded, setGraded] = useState(new Set());

  useEffect(() => {
    const bust = `?t=${Date.now()}`;
    fetch(`/data/nfl_matchups.json${bust}`).then(r => r.ok ? r.json() : Promise.reject())
      .then(setData).catch(() => setErr(true));
    // Players with graded rungs on any slate get a link into the Legs tab.
    Promise.all(LEGS_SLATES.map(s =>
      fetch(`/data/nfl_legs_${s}.json${bust}`).then(r => r.ok ? r.json() : null).catch(() => null)))
      .then(all => setGraded(new Set(all.flatMap(d =>
        (d?.players || []).filter(p => p.rungs?.length).map(p => normName(p.player))))));
  }, []);

  return (
    <div style={{padding:"28px 16px 80px",maxWidth:1000,margin:"0 auto",fontFamily:T.mono}}>
      <div style={{display:"flex",alignItems:"baseline",gap:14,flexWrap:"wrap",marginBottom:4}}>
        <div style={{fontSize:22,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>
          MATCHUPS{data ? ` · WEEK ${data.meta.week}` : ""}
        </div>
        {data && <div style={{fontSize:10,color:T.muted}}>{data.meta.season} · defense vs position</div>}
      </div>
      <div style={{fontSize:10,color:"#777",marginBottom:20,maxWidth:"72ch",lineHeight:1.6}}>
        1 = fewest yards allowed to that position (tough). 32 = most (soft). Blend shown in the corner.
      </div>

      {err && <div style={{fontSize:11,color:"#777",background:T.surface,border:`1px solid ${T.border}`,
        borderRadius:6,padding:16}}>Matchup data isn't posted yet for this week.</div>}
      {!data && !err && <div style={{fontSize:10,color:"#444"}}>loading…</div>}

      {data && <>
        <SectionLabel>HEAT MAP · {data.defenses.length} DEFENSES × {SLOTS.length} SLOTS</SectionLabel>
        <HeatMap data={data} />
        <EdgeLeans data={data} graded={graded} />
      </>}
    </div>
  );
}
