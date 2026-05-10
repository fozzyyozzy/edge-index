import { useState } from "react";

const POSITIONS = ["QB", "RB", "WR", "TE"];

const PLAYERS = {
  QB: [
    { name: "Lamar Jackson",    team: "BAL", props: { pass_yds: { l6: 94, l10: 91, streak: 8, line: 268.5 }, pass_att: { l6: 100, l10: 97, streak: 12, line: 33.5 }, rush_yds: { l6: 89, l10: 86, streak: 7, line: 48.5 } } },
    { name: "Josh Allen",       team: "BUF", props: { pass_yds: { l6: 83, l10: 81, streak: 5, line: 278.5 }, pass_att: { l6: 88, l10: 86, streak: 7, line: 37.5 }, rush_yds: { l6: 78, l10: 76, streak: 4, line: 38.5 } } },
    { name: "Joe Burrow",       team: "CIN", props: { pass_yds: { l6: 88, l10: 84, streak: 6, line: 271.5 }, pass_att: { l6: 92, l10: 89, streak: 8, line: 38.5 }, rush_yds: { l6: 62, l10: 58, streak: 2, line: 8.5  } } },
    { name: "Jalen Hurts",      team: "PHI", props: { pass_yds: { l6: 79, l10: 77, streak: 4, line: 238.5 }, pass_att: { l6: 84, l10: 81, streak: 6, line: 32.5 }, rush_yds: { l6: 91, l10: 88, streak: 9, line: 58.5 } } },
    { name: "Patrick Mahomes",  team: "KC",  props: { pass_yds: { l6: 86, l10: 83, streak: 6, line: 271.5 }, pass_att: { l6: 90, l10: 88, streak: 8, line: 36.5 }, rush_yds: { l6: 61, l10: 58, streak: 2, line: 14.5 } } },
    { name: "Jared Goff",       team: "DET", props: { pass_yds: { l6: 92, l10: 89, streak: 10, line: 278.5 }, pass_att: { l6: 96, l10: 93, streak: 12, line: 38.5 }, rush_yds: { l6: 48, l10: 44, streak: 1, line: 4.5  } } },
    { name: "Brock Purdy",      team: "SF",  props: { pass_yds: { l6: 83, l10: 80, streak: 5, line: 261.5 }, pass_att: { l6: 88, l10: 85, streak: 7, line: 34.5 }, rush_yds: { l6: 58, l10: 54, streak: 2, line: 12.5 } } },
    { name: "Jayden Daniels",   team: "WAS", props: { pass_yds: { l6: 79, l10: 76, streak: 4, line: 248.5 }, pass_att: { l6: 83, l10: 80, streak: 5, line: 34.5 }, rush_yds: { l6: 84, l10: 81, streak: 6, line: 42.5 } } },
  ],
  RB: [
    { name: "Saquon Barkley",       team: "PHI", props: { rush_yds: { l6: 88, l10: 85, streak: 7, line: 88.5  }, rush_att: { l6: 92, l10: 89, streak: 9, line: 18.5 }, receptions: { l6: 83, l10: 80, streak: 6, line: 4.5  }, rec_yds: { l6: 79, l10: 76, streak: 4, line: 32.5 } } },
    { name: "Derrick Henry",         team: "BAL", props: { rush_yds: { l6: 91, l10: 88, streak: 9, line: 98.5  }, rush_att: { l6: 94, l10: 91, streak: 11, line: 21.5 }, receptions: { l6: 62, l10: 58, streak: 2, line: 1.5  }, rec_yds: { l6: 58, l10: 54, streak: 1, line: 8.5  } } },
    { name: "Christian McCaffrey",   team: "SF",  props: { rush_yds: { l6: 84, l10: 81, streak: 6, line: 78.5  }, rush_att: { l6: 88, l10: 85, streak: 8, line: 15.5 }, receptions: { l6: 91, l10: 88, streak: 10, line: 6.5  }, rec_yds: { l6: 88, l10: 85, streak: 8, line: 58.5 } } },
    { name: "Jahmyr Gibbs",          team: "DET", props: { rush_yds: { l6: 83, l10: 80, streak: 6, line: 72.5  }, rush_att: { l6: 87, l10: 84, streak: 7, line: 13.5 }, receptions: { l6: 78, l10: 75, streak: 4, line: 4.5  }, rec_yds: { l6: 74, l10: 71, streak: 3, line: 38.5 } } },
    { name: "Bijan Robinson",        team: "ATL", props: { rush_yds: { l6: 81, l10: 78, streak: 5, line: 82.5  }, rush_att: { l6: 85, l10: 82, streak: 7, line: 17.5 }, receptions: { l6: 76, l10: 73, streak: 4, line: 4.5  }, rec_yds: { l6: 72, l10: 69, streak: 3, line: 34.5 } } },
    { name: "De'Von Achane",         team: "MIA", props: { rush_yds: { l6: 77, l10: 74, streak: 4, line: 62.5  }, rush_att: { l6: 81, l10: 78, streak: 5, line: 12.5 }, receptions: { l6: 84, l10: 81, streak: 6, line: 5.5  }, rec_yds: { l6: 80, l10: 77, streak: 5, line: 48.5 } } },
    { name: "James Cook",            team: "BUF", props: { rush_yds: { l6: 79, l10: 76, streak: 4, line: 68.5  }, rush_att: { l6: 83, l10: 80, streak: 6, line: 13.5 }, receptions: { l6: 77, l10: 74, streak: 4, line: 3.5  }, rec_yds: { l6: 73, l10: 70, streak: 3, line: 28.5 } } },
    { name: "Josh Jacobs",           team: "GB",  props: { rush_yds: { l6: 82, l10: 79, streak: 5, line: 78.5  }, rush_att: { l6: 86, l10: 83, streak: 7, line: 17.5 }, receptions: { l6: 68, l10: 65, streak: 2, line: 3.5  }, rec_yds: { l6: 64, l10: 61, streak: 2, line: 22.5 } } },
  ],
  WR: [
    { name: "Ja'Marr Chase",         team: "CIN", props: { rec_yds: { l6: 91, l10: 88, streak: 9,  line: 72.5 }, receptions: { l6: 84, l10: 81, streak: 6,  line: 5.5 }, rec_tds: { l6: 72, l10: 69, streak: 3, line: 0.5 } } },
    { name: "CeeDee Lamb",           team: "DAL", props: { rec_yds: { l6: 84, l10: 81, streak: 6,  line: 78.5 }, receptions: { l6: 88, l10: 85, streak: 8,  line: 6.5 }, rec_tds: { l6: 68, l10: 65, streak: 2, line: 0.5 } } },
    { name: "Justin Jefferson",      team: "MIN", props: { rec_yds: { l6: 83, l10: 80, streak: 5,  line: 74.5 }, receptions: { l6: 79, l10: 76, streak: 4,  line: 5.5 }, rec_tds: { l6: 64, l10: 61, streak: 2, line: 0.5 } } },
    { name: "Amon-Ra St. Brown",     team: "DET", props: { rec_yds: { l6: 88, l10: 85, streak: 8,  line: 68.5 }, receptions: { l6: 92, l10: 89, streak: 10, line: 6.5 }, rec_tds: { l6: 66, l10: 63, streak: 2, line: 0.5 } } },
    { name: "Tyreek Hill",           team: "MIA", props: { rec_yds: { l6: 79, l10: 76, streak: 4,  line: 68.5 }, receptions: { l6: 76, l10: 73, streak: 3,  line: 5.5 }, rec_tds: { l6: 61, l10: 58, streak: 1, line: 0.5 } } },
    { name: "Marvin Harrison Jr.",   team: "ARI", props: { rec_yds: { l6: 82, l10: 79, streak: 5,  line: 62.5 }, receptions: { l6: 78, l10: 75, streak: 4,  line: 4.5 }, rec_tds: { l6: 63, l10: 60, streak: 2, line: 0.5 } } },
    { name: "Zay Flowers",           team: "BAL", props: { rec_yds: { l6: 84, l10: 81, streak: 6,  line: 58.5 }, receptions: { l6: 81, l10: 78, streak: 5,  line: 5.5 }, rec_tds: { l6: 60, l10: 57, streak: 1, line: 0.5 } } },
    { name: "Nico Collins",          team: "HOU", props: { rec_yds: { l6: 86, l10: 83, streak: 7,  line: 72.5 }, receptions: { l6: 79, l10: 76, streak: 4,  line: 5.5 }, rec_tds: { l6: 64, l10: 61, streak: 2, line: 0.5 } } },
    { name: "DeVonta Smith",         team: "PHI", props: { rec_yds: { l6: 81, l10: 78, streak: 5,  line: 62.5 }, receptions: { l6: 83, l10: 80, streak: 6,  line: 5.5 }, rec_tds: { l6: 61, l10: 58, streak: 1, line: 0.5 } } },
    { name: "Rashee Rice",           team: "KC",  props: { rec_yds: { l6: 80, l10: 77, streak: 5,  line: 64.5 }, receptions: { l6: 77, l10: 74, streak: 4,  line: 5.5 }, rec_tds: { l6: 60, l10: 57, streak: 1, line: 0.5 } } },
  ],
  TE: [
    { name: "Travis Kelce",      team: "KC",  props: { rec_yds: { l6: 88, l10: 85, streak: 8,  line: 54.5 }, receptions: { l6: 91, l10: 88, streak: 10, line: 5.5 }, rec_tds: { l6: 72, l10: 69, streak: 3, line: 0.5 } } },
    { name: "Trey McBride",      team: "ARI", props: { rec_yds: { l6: 84, l10: 81, streak: 6,  line: 62.5 }, receptions: { l6: 87, l10: 84, streak: 8,  line: 5.5 }, rec_tds: { l6: 68, l10: 65, streak: 2, line: 0.5 } } },
    { name: "Mark Andrews",      team: "BAL", props: { rec_yds: { l6: 86, l10: 83, streak: 7,  line: 58.5 }, receptions: { l6: 83, l10: 80, streak: 5,  line: 5.5 }, rec_tds: { l6: 74, l10: 71, streak: 3, line: 0.5 } } },
    { name: "George Kittle",     team: "SF",  props: { rec_yds: { l6: 83, l10: 80, streak: 6,  line: 58.5 }, receptions: { l6: 80, l10: 77, streak: 5,  line: 5.5 }, rec_tds: { l6: 70, l10: 67, streak: 3, line: 0.5 } } },
    { name: "Brock Bowers",      team: "LV",  props: { rec_yds: { l6: 81, l10: 78, streak: 5,  line: 52.5 }, receptions: { l6: 84, l10: 81, streak: 7,  line: 5.5 }, rec_tds: { l6: 62, l10: 59, streak: 2, line: 0.5 } } },
    { name: "Sam LaPorta",       team: "DET", props: { rec_yds: { l6: 79, l10: 76, streak: 4,  line: 48.5 }, receptions: { l6: 82, l10: 79, streak: 6,  line: 4.5 }, rec_tds: { l6: 64, l10: 61, streak: 2, line: 0.5 } } },
    { name: "Dallas Goedert",    team: "PHI", props: { rec_yds: { l6: 80, l10: 77, streak: 5,  line: 52.5 }, receptions: { l6: 78, l10: 75, streak: 4,  line: 4.5 }, rec_tds: { l6: 65, l10: 62, streak: 2, line: 0.5 } } },
    { name: "Tyler Warren",      team: "IND", props: { rec_yds: { l6: 78, l10: 75, streak: 4,  line: 48.5 }, receptions: { l6: 80, l10: 77, streak: 5,  line: 4.5 }, rec_tds: { l6: 62, l10: 59, streak: 1, line: 0.5 } } },
  ],
};

const PROP_LABELS = {
  pass_yds:   "Pass Yds",   pass_att:   "Pass Att",  rush_yds:  "Rush Yds",
  rush_att:   "Rush Att",   receptions: "Recs",       rec_yds:   "Rec Yds",
  rec_tds:    "Rec TDs",
};

const TEAM_COLORS = {
  BAL:"#9E7FD4", BUF:"#00338D", CIN:"#FB4F14", PHI:"#004C54",
  KC:"#E31837",  DET:"#0076B6", SF:"#AA0000",  WAS:"#773141",
  ATL:"#A71930", MIA:"#008E97", GB:"#203731",  ARI:"#97233F",
  LV:"#A5ACAF",  IND:"#002C5F", DAL:"#003594", MIN:"#4F2683",
  HOU:"#03202F", LAR:"#003594",
};

function getTier(rate, streak) {
  if (rate >= 85 && streak >= 6) return "AUTO";
  if (rate >= 70) return "T1";
  if (rate >= 55) return "T2";
  return "T3";
}

function tierColor(tier) {
  return { AUTO:"#00ff88", T1:"#4fc3f7", T2:"#ffd54f", T3:"#ef5350" }[tier] || "#888";
}

function StreakBadge({ streak }) {
  const color = streak >= 10 ? "#00ff88" : streak >= 6 ? "#4fc3f7" : streak >= 3 ? "#ffd54f" : "#888";
  return (
    <span style={{ background: color + "22", color, border: `1px solid ${color}55`,
      borderRadius: 4, padding: "1px 6px", fontSize: 11, fontWeight: 700 }}>
      {streak}🔥
    </span>
  );
}

function RateBar({ value }) {
  const color = value >= 90 ? "#00ff88" : value >= 75 ? "#4fc3f7" : value >= 60 ? "#ffd54f" : "#ef5350";
  return (
    <div style={{ display:"flex", alignItems:"center", gap: 6 }}>
      <div style={{ flex:1, height: 5, background:"#ffffff11", borderRadius: 3, overflow:"hidden" }}>
        <div style={{ width:`${value}%`, height:"100%", background: color, borderRadius: 3,
          transition:"width 0.6s ease" }} />
      </div>
      <span style={{ fontSize:12, color, fontWeight:700, minWidth:34 }}>{value}%</span>
    </div>
  );
}

function PropRow({ label, data }) {
  if (!data) return null;
  const tier = getTier(data.l6, data.streak);
  return (
    <div style={{ display:"grid", gridTemplateColumns:"90px 1fr 60px 60px 50px",
      alignItems:"center", gap:8, padding:"6px 0",
      borderBottom:"1px solid #ffffff08" }}>
      <span style={{ fontSize:11, color:"#888", fontWeight:600 }}>{label}</span>
      <RateBar value={data.l6} />
      <span style={{ fontSize:11, color:"#aaa", textAlign:"center" }}>{data.l10}%</span>
      <StreakBadge streak={data.streak} />
      <span style={{ fontSize:10, color: tierColor(tier), fontWeight:700,
        background: tierColor(tier)+"18", padding:"1px 5px", borderRadius:3,
        textAlign:"center" }}>{tier}</span>
    </div>
  );
}

function PlayerCard({ player }) {
  const accent = TEAM_COLORS[player.team] || "#4fc3f7";
  const props = Object.entries(player.props);
  const bestTier = props.some(([,d]) => getTier(d.l6, d.streak) === "AUTO") ? "AUTO"
    : props.some(([,d]) => getTier(d.l6, d.streak) === "T1") ? "T1" : "T2";

  return (
    <div style={{ background:"#0d1117", border:`1px solid ${accent}33`,
      borderLeft:`3px solid ${accent}`, borderRadius:8, padding:"14px 16px",
      transition:"transform 0.15s, box-shadow 0.15s" }}
      onMouseEnter={e => { e.currentTarget.style.transform="translateY(-2px)";
        e.currentTarget.style.boxShadow=`0 8px 24px ${accent}22`; }}
      onMouseLeave={e => { e.currentTarget.style.transform="none";
        e.currentTarget.style.boxShadow="none"; }}>

      <div style={{ display:"flex", justifyContent:"space-between",
        alignItems:"flex-start", marginBottom:10 }}>
        <div>
          <div style={{ fontSize:14, fontWeight:700, color:"#f0f0f0",
            letterSpacing:"-0.3px" }}>{player.name}</div>
          <div style={{ fontSize:11, color: accent, fontWeight:600,
            marginTop:2 }}>{player.team}</div>
        </div>
        <span style={{ fontSize:10, color: tierColor(bestTier), fontWeight:700,
          background: tierColor(bestTier)+"22", padding:"2px 8px",
          borderRadius:12, border:`1px solid ${tierColor(bestTier)}44` }}>
          {bestTier === "AUTO" ? "⚡ AUTO" : bestTier}
        </span>
      </div>

      <div style={{ borderTop:"1px solid #ffffff0a", paddingTop:8 }}>
        <div style={{ display:"grid", gridTemplateColumns:"90px 1fr 60px 60px 50px",
          gap:8, marginBottom:4 }}>
          <span style={{ fontSize:10, color:"#555" }}>PROP</span>
          <span style={{ fontSize:10, color:"#555" }}>L6 RATE</span>
          <span style={{ fontSize:10, color:"#555", textAlign:"center" }}>L10</span>
          <span style={{ fontSize:10, color:"#555", textAlign:"center" }}>STREAK</span>
          <span style={{ fontSize:10, color:"#555", textAlign:"center" }}>TIER</span>
        </div>
        {props.map(([key, data]) => (
          <PropRow key={key} label={PROP_LABELS[key] || key} data={data} />
        ))}
      </div>
    </div>
  );
}

export default function PlayerStatsHub() {
  const [activePos, setActivePos] = useState("QB");
  const [sortBy, setSortBy]       = useState("streak");
  const [filterTier, setFilter]   = useState("ALL");
  const [search, setSearch]       = useState("");

  const players = PLAYERS[activePos] || [];

  const filtered = players
    .filter(p => {
      if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
      if (filterTier === "ALL") return true;
      const props = Object.values(p.props);
      return props.some(d => getTier(d.l6, d.streak) === filterTier);
    })
    .sort((a, b) => {
      const aProps = Object.values(a.props);
      const bProps = Object.values(b.props);
      if (sortBy === "streak")  return Math.max(...bProps.map(d=>d.streak)) - Math.max(...aProps.map(d=>d.streak));
      if (sortBy === "l6")      return Math.max(...bProps.map(d=>d.l6))     - Math.max(...aProps.map(d=>d.l6));
      if (sortBy === "name")    return a.name.localeCompare(b.name);
      return 0;
    });

  return (
    <div style={{ background:"#060911", minHeight:"100vh", fontFamily:"'SF Mono', 'Fira Code', monospace",
      padding:"0 0 40px" }}>

      {/* Header */}
      <div style={{ background:"linear-gradient(135deg, #060911 0%, #0d1a2d 100%)",
        borderBottom:"1px solid #ffffff0a", padding:"24px 24px 0" }}>
        <div style={{ display:"flex", alignItems:"baseline", gap:12, marginBottom:4 }}>
          <span style={{ fontSize:11, color:"#00ff88", fontWeight:700,
            letterSpacing:3 }}>EDGE INDEX</span>
          <span style={{ fontSize:11, color:"#333" }}>///</span>
          <span style={{ fontSize:11, color:"#555", letterSpacing:2 }}>PLAYER STATS HUB</span>
        </div>
        <h1 style={{ fontSize:22, fontWeight:700, color:"#f0f0f0", margin:"0 0 20px",
          letterSpacing:"-0.5px" }}>Streak & Hit Rate Tracker</h1>

        {/* Position tabs */}
        <div style={{ display:"flex", gap:0 }}>
          {POSITIONS.map(pos => (
            <button key={pos} onClick={() => setActivePos(pos)}
              style={{ padding:"10px 24px", background: activePos===pos
                ? "#00ff8822" : "transparent",
                border:"none", borderBottom: activePos===pos
                ? "2px solid #00ff88" : "2px solid transparent",
                color: activePos===pos ? "#00ff88" : "#555",
                fontSize:13, fontWeight:700, cursor:"pointer",
                transition:"all 0.15s", letterSpacing:1 }}>
              {pos}
            </button>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display:"flex", gap:12, padding:"16px 24px",
        flexWrap:"wrap", alignItems:"center" }}>
        <input
          placeholder="Search player..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ background:"#0d1117", border:"1px solid #ffffff15", borderRadius:6,
            padding:"7px 12px", color:"#f0f0f0", fontSize:12, outline:"none",
            fontFamily:"inherit", width:160 }} />

        <div style={{ display:"flex", gap:6 }}>
          {["ALL","AUTO","T1","T2"].map(t => (
            <button key={t} onClick={() => setFilter(t)}
              style={{ padding:"6px 12px", borderRadius:6, cursor:"pointer",
                fontSize:11, fontWeight:700, transition:"all 0.15s",
                background: filterTier===t ? tierColor(t==="ALL"?"T1":t)+"22" : "#0d1117",
                color: filterTier===t ? tierColor(t==="ALL"?"T1":t) : "#555",
                border:`1px solid ${filterTier===t ? tierColor(t==="ALL"?"T1":t)+"55" : "#ffffff0f"}` }}>
              {t === "AUTO" ? "⚡ AUTO" : t}
            </button>
          ))}
        </div>

        <div style={{ display:"flex", gap:6, marginLeft:"auto" }}>
          <span style={{ fontSize:11, color:"#555", alignSelf:"center" }}>SORT:</span>
          {[["streak","🔥 Streak"],["l6","L6 Rate"],["name","Name"]].map(([val,label]) => (
            <button key={val} onClick={() => setSortBy(val)}
              style={{ padding:"6px 10px", borderRadius:6, cursor:"pointer",
                fontSize:11, fontWeight:600, transition:"all 0.15s",
                background: sortBy===val ? "#4fc3f722" : "#0d1117",
                color: sortBy===val ? "#4fc3f7" : "#555",
                border:`1px solid ${sortBy===val ? "#4fc3f744" : "#ffffff0f"}` }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display:"flex", gap:16, padding:"0 24px 16px",
        flexWrap:"wrap" }}>
        {[["AUTO","⚡ 85%+ L6 + 6+ streak"],["T1","70%+ hit rate"],
          ["T2","55-70% hit rate"],["T3","Below 55%"]].map(([tier,desc]) => (
          <div key={tier} style={{ display:"flex", alignItems:"center", gap:6 }}>
            <div style={{ width:8, height:8, borderRadius:"50%",
              background: tierColor(tier) }} />
            <span style={{ fontSize:10, color:"#555" }}>
              <span style={{ color: tierColor(tier), fontWeight:700 }}>{tier}</span>
              {" "}{desc}
            </span>
          </div>
        ))}
      </div>

      {/* Grid */}
      <div style={{ display:"grid",
        gridTemplateColumns:"repeat(auto-fill, minmax(340px, 1fr))",
        gap:12, padding:"0 24px" }}>
        {filtered.map(player => (
          <PlayerCard key={player.name} player={player} />
        ))}
        {filtered.length === 0 && (
          <div style={{ color:"#333", padding:40, textAlign:"center",
            gridColumn:"1/-1" }}>No players match filters</div>
        )}
      </div>

      {/* Summary bar */}
      <div style={{ display:"flex", gap:24, padding:"20px 24px 0",
        borderTop:"1px solid #ffffff08", marginTop:20, flexWrap:"wrap" }}>
        {[
          ["AUTO PLAYS", players.filter(p => Object.values(p.props).some(d => getTier(d.l6,d.streak)==="AUTO")).length],
          ["AVG L6 RATE", Math.round(players.flatMap(p => Object.values(p.props)).reduce((s,d) => s+d.l6,0) / players.flatMap(p=>Object.values(p.props)).length) + "%"],
          ["ACTIVE STREAKS 6+", players.flatMap(p=>Object.values(p.props)).filter(d=>d.streak>=6).length],
          ["PLAYERS TRACKED", players.length],
        ].map(([label, val]) => (
          <div key={label}>
            <div style={{ fontSize:10, color:"#444", letterSpacing:2 }}>{label}</div>
            <div style={{ fontSize:20, fontWeight:700, color:"#00ff88",
              fontFamily:"'SF Mono', monospace" }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
