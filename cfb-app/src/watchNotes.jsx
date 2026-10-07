import { useState } from "react";

// Watch flags (automation/pipeline/availability.py): "injury watch: ..." per player, "QB change: ..." per team.
// Display only. Each list (Legs table, Card tickets, Floors as singles) numbers its notes in order of first appearance;
// the chip carries the marker, the note sits in a footnote block under the list, and tapping/hovering the chip shows the
// same note inline (phones have no hover).

const AMBER = "#f5c518";
const SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹";
export const sup = n => String(n).split("").map(d => SUP[+d]).join("");

const isWatch = f => f.startsWith("injury watch") || f.startsWith("QB change");
export const watchFlags = fs => (fs || []).filter(isWatch);

export const watchLabel = fs => fs.every(f => f.startsWith("injury watch")) ? "INJURY WATCH"
  : fs.every(f => f.startsWith("QB change")) ? "QB CHANGE" : "WATCH";

const QB = /\((.+?) led the team's last game, \d{4} wk (\d+); (.+?) led (\d+) of its last (\d+)\)/;

function noteFor(flag, player, team) {
  if (flag.startsWith("QB change")) {
    const m = flag.match(QB);
    return {
      key: `QB|${team}`,
      text: m ? `${team}: QB change. ${m[1]} started the team's last game (wk ${m[2]}); ${m[3]} started ${m[4]} of its last ${m[5]}. ` +
                "Receiving and passing history may not reflect the new QB."
              : `${team}: ${flag}.`,
    };
  }
  const t = flag.replace(/^injury watch:\s*/, "");
  return { key: `INJ|${player}`, text: `${player}: injury watch. ${t.charAt(0).toUpperCase()}${t.slice(1)}.` };
}

// items: [{ player, team, flags }] in display order -> { notes: [{n, text}], marks(player, team, flags) -> [{n, text}] }
export function buildNotes(items) {
  const byKey = new Map();
  for (const it of items)
    for (const f of watchFlags(it.flags)) {
      const { key, text } = noteFor(f, it.player, it.team);
      if (!byKey.has(key)) byKey.set(key, { n: byKey.size + 1, text });
    }
  const marks = (player, team, flags) => {
    const seen = new Set();
    return watchFlags(flags).map(f => byKey.get(noteFor(f, player, team).key)).filter(m => m && !seen.has(m.n) && seen.add(m.n));
  };
  return { notes: [...byKey.values()], marks };
}

// The chip, plus its inline note when tapped (pinned) or hovered. Clicks don't reach the row (Legs rows toggle open).
export function WatchChip({ flags, marks, mono }) {
  const [pinned, setPinned] = useState(false);
  const [hover, setHover] = useState(false);
  const fs = watchFlags(flags);
  if (!fs.length) return null;
  const text = marks.map(m => `${sup(m.n)} ${m.text}`).join("\n");
  return (
    <>
      <button type="button" aria-expanded={pinned} title={text}
        onClick={e => { e.stopPropagation(); setPinned(!pinned); setHover(false); }}
        onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
        style={{fontSize:8,color:AMBER,background:"transparent",border:`1px solid ${AMBER}55`,borderRadius:3,
          padding:"1px 5px",fontFamily:mono,letterSpacing:1,whiteSpace:"nowrap",cursor:"pointer",lineHeight:1.5}}>
        {watchLabel(fs)}{marks.length > 0 && <span style={{marginLeft:3,letterSpacing:0}}>{marks.map(m => sup(m.n)).join("")}</span>}
      </button>
      {(pinned || hover) && (
        <div onClick={e => e.stopPropagation()}
          style={{flexBasis:"100%",fontSize:9.5,color:"#9a9a9a",fontFamily:mono,lineHeight:1.5,margin:"2px 0 1px",
            whiteSpace:"pre-line"}}>{text}</div>
      )}
    </>
  );
}

export function Footnotes({ notes, mono, style }) {
  if (!notes.length) return null;
  return (
    <div style={{fontSize:9,color:"#666",fontFamily:mono,lineHeight:1.6,marginTop:8,...style}}>
      {notes.map(n => <div key={n.n}><span style={{color:AMBER}}>{sup(n.n)}</span> {n.text}</div>)}
    </div>
  );
}
