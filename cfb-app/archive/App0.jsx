import { useState } from "react";
import PropHub from "./PropHub";
import StreakCenter from "./StreakCenter";
import BankrollManager from "./BankrollManager";
import PlayerStatsHub from "./PlayerStatsHub";

const NAV = [
  { id: "streaks",  label: "⚡ Streak Center",   component: StreakCenter },
  { id: "players",  label: "📊 Player Stats",     component: PlayerStatsHub },
  { id: "props",    label: "🎯 Prop Hub",          component: PropHub },
  { id: "bankroll", label: "💰 Bankroll Manager",  component: BankrollManager },
];

export default function App() {
  const [active, setActive] = useState("streaks");
  const ActiveComponent = NAV.find(n => n.id === active)?.component;

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
              marginTop:-2 }}>NFL PROP ANALYTICS</div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display:"flex" }}>
          {NAV.map(n => (
            <button key={n.id} onClick={() => setActive(n.id)}
              style={{ padding:"16px 20px", background:"transparent", border:"none",
                borderBottom: active===n.id ? "2px solid #00ff88" : "2px solid transparent",
                color: active===n.id ? "#00ff88" : "#555",
                fontSize:12, fontWeight:600, cursor:"pointer",
                transition:"all 0.15s", whiteSpace:"nowrap" }}>
              {n.label}
            </button>
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
