import { useEffect, useState } from "react";
import KBoard from "./KBoard";
import StreakCenter from "./StreakCenter";
import MatchupsHub from "./MatchupsHub";
import LegsHub from "./LegsHub";
import MLBHub from "./MLBHub";
import NFLHub from "./NFLHub";
import RecordTracker from "./RecordTracker";
import NFLRecord from "./NFLRecord";
import FAQ from "./FAQ";


// NFL leads — it's the product. MLB was the offseason trial and is
// labelled as one rather than presented as a parallel offering.
const NAV_SECTIONS = [
  {
    sport: "NFL",
    note: "2026 · GRADED",
    color: "#00e5ff",
    tabs: [
      { id: "nflcard",  label: "Card",         component: NFLHub },
      { id: "legs",     label: "Legs",         component: LegsHub },
      { id: "streaks",  label: "Floor Lines",  component: StreakCenter },
      { id: "matchups", label: "Matchups",     component: MatchupsHub },
      { id: "record",   label: "Record",       component: NFLRecord },
      { id: "faq",      label: "FAQ",          component: FAQ },
    ],
  },
  {
    sport: "MLB",
    note: "OFFSEASON TEST",
    color: "#f5c518",
    tabs: [
      { id: "kboard",   label: "K Board",        component: KBoard },
      { id: "mlb",      label: "Full Card",      component: MLBHub },
      { id: "mlbrecord",label: "MLB Record",     component: RecordTracker },
    ],
  },
];

const ALL_TABS = NAV_SECTIONS.flatMap(s => s.tabs);

export default function App() {
  // "#matchups" or "#legs?player=X" opens that tab; unknown ids are ignored.
  const tabFromHash = () => {
    const id = window.location.hash.slice(1).split("?")[0];
    return ALL_TABS.some(t => t.id === id) ? id : null;
  };
  const [active, setActive] = useState(() => tabFromHash() || "nflcard");
  useEffect(() => {
    const onHash = () => { const id = tabFromHash(); if (id) setActive(id); };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const ActiveComponent = ALL_TABS.find(n => n.id === active)?.component;

  return (
    <div style={{ background:"#060911", minHeight:"100vh",
      fontFamily:"'SF Mono','Fira Code',monospace" }}>

      {/* Top nav */}
      <div className="topnav" style={{ background:"#0a0f1a", borderBottom:"1px solid #ffffff0a",
        padding:"0 24px", display:"flex", alignItems:"center", flexWrap:"wrap", columnGap:16,
        justifyContent:"space-between", position:"sticky", top:0, zIndex:100 }}>

        {/* Logo */}
        <div style={{ display:"flex", alignItems:"center", gap:10, padding:"14px 0" }}>
          <div style={{ width:28, height:28, borderRadius:6,
            background:"linear-gradient(135deg,#00ff88,#00cc6a)",
            display:"flex", alignItems:"center", justifyContent:"center",
            fontSize:12, fontWeight:900, color:"#060911" }}>EI</div>
          <div>
            <div style={{ fontSize:13, fontWeight:700, color:"#f0f0f0",
              letterSpacing:1 }}>EDGE INDEX</div>
            <div className="topnav-sub" style={{ fontSize:9, color:"#00e5ff", letterSpacing:2,
              marginTop:-2 }}>NFL PROP MODEL · CALIBRATED · GRADED IN PUBLIC</div>
          </div>
        </div>

        {/* Tabs with sport dividers */}
        <div className="topnav-tabs" style={{ display:"flex", alignItems:"stretch", minWidth:0, overflowX:"auto" }}>
          {NAV_SECTIONS.map((section, si) => (
            <div key={section.sport} style={{ display:"flex", alignItems:"stretch" }}>
              {/* Sport label — non-clickable divider */}
              <div style={{
                padding:"12px 12px",
                letterSpacing:3,
                fontFamily:"'IBM Plex Mono',monospace",
                display:"flex", flexDirection:"column", justifyContent:"center",
                borderLeft: si > 0 ? "1px solid #ffffff08" : "none",
                userSelect:"none",
              }}>
                <div style={{ fontSize:10, fontWeight:800,
                  color: section.color + "60" }}>{section.sport}</div>
                <div style={{ fontSize:7, color:"#3a3a3a", letterSpacing:1.5,
                  marginTop:2, whiteSpace:"nowrap" }}>{section.note}</div>
              </div>
              {/* Tabs for this sport */}
              {section.tabs.map(n => (
                <button key={n.id} onClick={() => setActive(n.id)}
                  style={{ padding:"16px 14px", background:"transparent", border:"none",
                    borderBottom: active===n.id
                      ? `2px solid ${section.color}`
                      : "2px solid transparent",
                    color: active===n.id ? section.color : "#555",
                    fontSize:11, fontWeight:600, cursor:"pointer",
                    transition:"all 0.15s", whiteSpace:"nowrap",
                    fontFamily:"'IBM Plex Mono',monospace",
                  }}>
                  {n.label}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Live indicator */}
        <div style={{ display:"flex", alignItems:"center", gap:6 }}>
          <div style={{ width:6, height:6, borderRadius:"50%", background:"#f5c518",
            animation:"pulse 2s infinite" }} />
          <span style={{ fontSize:10, color:"#f5c518", letterSpacing:2,
            fontWeight:700 }}>LIVE</span>
        </div>
      </div>

      <div style={{ minHeight:"calc(100vh - 57px)" }}>
        {ActiveComponent && <ActiveComponent />}
      </div>

      <style>{`
        .topnav-tabs { scrollbar-width:none; }
        .topnav-tabs::-webkit-scrollbar { display:none; }
        /* phones: logo + LIVE on the first row, the tab strip on its own row, scrolling sideways inside itself */
        @media (max-width: 760px) {
          .topnav { padding:0 12px !important; }
          .topnav-sub { display:none; }
          .topnav-tabs { order:3; flex:1 0 100%; margin:0 -12px; padding:0 4px; border-top:1px solid #ffffff08; }
          .topnav-tabs button { padding:12px 11px !important; }
        }
        @keyframes pulse {
          0%,100% { opacity:1; transform:scale(1); }
          50% { opacity:0.4; transform:scale(1.3); }
        }
      `}</style>
    </div>
  );
}
