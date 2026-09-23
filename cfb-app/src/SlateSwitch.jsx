import { SLATES } from "./nflSlates";

// Segmented control. Slates without a file are greyed and not clickable.
export default function SlateSwitch({ files, slate, onChange }) {
  return (
    <div style={{display:"inline-flex",border:"1px solid #ffffff14",borderRadius:4,overflow:"hidden"}}>
      {SLATES.map(([s, label]) => {
        const has = !!files?.[s], on = has && slate === s;
        return (
          <button key={s} disabled={!has} onClick={() => onChange(s)} title={has ? "" : "not posted yet"}
            style={{padding:"5px 12px",fontSize:10,fontFamily:"'IBM Plex Mono',monospace",letterSpacing:1,border:"none",
              cursor: has ? "pointer" : "default",background: on ? "#00e5ff1c" : "transparent",
              color: on ? "#00e5ff" : has ? "#777" : "#333",fontWeight: on ? 700 : 500}}>{label}</button>
        );
      })}
    </div>
  );
}
