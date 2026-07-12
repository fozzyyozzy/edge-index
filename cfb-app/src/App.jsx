import { useState } from "react";
import KBoard from "./KBoard";
import PropHub from "./PropHub";
import StreakCenter from "./StreakCenter";
import BankrollManager from "./BankrollManager";
import PlayerStatsHub from "./PlayerStatsHub";
import MLBHub from "./MLBHub";
import RecordTracker from "./RecordTracker";
import FAQ from "./FAQ";
import PlaybookHub from "./PlaybookHub";

// Sport section dividers + tabs
const NAV_SECTIONS = [
  {
    sport: "MLB",
    color: "#f5c518",
    tabs: [
      { id: "kboard",   label: "K Board",          component: KBoard },
      { id: "mlb",      label: "Full Card",        component: MLBHub },
      { id: "record",   label: "Record",           component: RecordTracker },
      { id: "faq",      label: "FAQ",              component: FAQ },
    ],
  },
  {
    sport: "NFL",
    color: "#00e5ff",
    tabs: [
      { id: "streaks",  label: "Streak Center",   component: StreakCenter },
      { id: "players",  label: "Player Stats",     component: PlayerStatsHub },
      { id: "props",    label: "Prop Hub",          component: PropHub },
      { id: "playbook", label: "Playbook",          component: PlaybookHub },
      { id: "bankroll", label: "Bankroll",          component: BankrollManager },
    ],
  },
];

const ALL_TABS = NAV_SECTIONS.flatMap(s => s.tabs);

export default function App() {
  const [active, setActive] = useState("kboard");
  const ActiveComponent = ALL_TABS.find(n => n.id === active)?.component;

  return (
    <div style={{ background:"#060911", minHeight:"100vh",
      fontFamily:"'SF Mono','Fira Code',monospace" }}>

      {/* Top nav */}
      <div style={{ background:"#0a0f1a", borderBottom:"1px solid #ffffff0a",
        padding:"0 24px", display:"flex", alignItems:"center",
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
            <div style={{ fontSize:9, color:"#00ff88", letterSpacing:2,
              marginTop:-2 }}>MLB STRIKEOUT EDGE · NFL PROPS</div>
          </div>
        </div>

        {/* Tabs with sport dividers */}
        <div style={{ display:"flex", alignItems:"stretch" }}>
          {NAV_SECTIONS.map((section, si) => (
            <div key={section.sport} style={{ display:"flex", alignItems:"stretch" }}>
              {/* Sport label — non-clickable divider */}
              <div style={{
                padding:"16px 12px",
                fontSize:10, fontWeight:800,
                color: section.color + "60",
                letterSpacing:3,
                fontFamily:"'IBM Plex Mono',monospace",
                display:"flex", alignItems:"center",
                borderLeft: si > 0 ? "1px solid #ffffff08" : "none",
                userSelect:"none",
              }}>
                {section.sport}
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
          <div style={{ width:6, height:6, borderRadius:"50%", background:"#00ff88",
            animation:"pulse 2s infinite" }} />
          <span style={{ fontSize:10, color:"#00ff88", letterSpacing:2,
            fontWeight:700 }}>LIVE</span>
        </div>
      </div>

      <div style={{ minHeight:"calc(100vh - 57px)" }}>
        {ActiveComponent && <ActiveComponent />}
      </div>

      <style>{`
        @keyframes pulse {
          0%,100% { opacity:1; transform:scale(1); }
          50% { opacity:0.4; transform:scale(1.3); }
        }
      `}</style>
    </div>
  );
}
