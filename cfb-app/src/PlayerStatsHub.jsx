import { useState } from "react";
// v2026-08-20 — Per-position usage. Absorbs the old Playbook breakdowns.

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const POS_COLOR = { QB:"#a855f7", RB:"#00c896", WR:"#00e5ff", TE:"#f5c518" };
const oddsStr = o => (o > 0 ? "+" : "") + o;

// >>> AUTO-GENERATED PLAYERS BEGIN — written by generate_nfl_data.py
// generated 2026-08-20 from 2025 full-season game logs
const PLAYER_ROWS = [
  {
    "player": "Matthew Stafford",
    "team": "LA",
    "pos": "QB",
    "games": 17,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 1.7,
    "rushyd": 0.1,
    "att": 35.1,
    "passyd": 276.9
  },
  {
    "player": "Jared Goff",
    "team": "DET",
    "pos": "QB",
    "games": 17,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 1.1,
    "rushyd": 2.6,
    "att": 34.0,
    "passyd": 268.5
  },
  {
    "player": "Dak Prescott",
    "team": "DAL",
    "pos": "QB",
    "games": 17,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 3.1,
    "rushyd": 10.4,
    "att": 35.3,
    "passyd": 267.8
  },
  {
    "player": "Drake Maye",
    "team": "NE",
    "pos": "QB",
    "games": 17,
    "tgt": 0.1,
    "rec": 0.1,
    "recyd": 0.1,
    "car": 6.1,
    "rushyd": 26.5,
    "att": 28.9,
    "passyd": 258.5
  },
  {
    "player": "Patrick Mahomes",
    "team": "KC",
    "pos": "QB",
    "games": 14,
    "tgt": 0.1,
    "rec": 0.1,
    "recyd": -0.7,
    "car": 4.6,
    "rushyd": 30.1,
    "att": 35.9,
    "passyd": 256.2
  },
  {
    "player": "Brock Purdy",
    "team": "SF",
    "pos": "QB",
    "games": 9,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 3.7,
    "rushyd": 16.3,
    "att": 31.6,
    "passyd": 240.8
  },
  {
    "player": "Jacoby Brissett",
    "team": "ARI",
    "pos": "QB",
    "games": 14,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 2.7,
    "rushyd": 12.0,
    "att": 34.6,
    "passyd": 240.4
  },
  {
    "player": "Daniel Jones",
    "team": "IND",
    "pos": "QB",
    "games": 13,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 3.5,
    "rushyd": 12.6,
    "att": 29.5,
    "passyd": 238.5
  },
  {
    "player": "Sam Darnold",
    "team": "SEA",
    "pos": "QB",
    "games": 17,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 2.1,
    "rushyd": 5.6,
    "att": 28.1,
    "passyd": 238.1
  },
  {
    "player": "Trevor Lawrence",
    "team": "JAX",
    "pos": "QB",
    "games": 17,
    "tgt": 0.0,
    "rec": 0.0,
    "recyd": 0.0,
    "car": 4.8,
    "rushyd": 21.1,
    "att": 32.9,
    "passyd": 235.7
  },
  {
    "player": "James Cook",
    "team": "BUF",
    "pos": "RB",
    "games": 17,
    "tgt": 2.4,
    "rec": 1.9,
    "recyd": 17.1,
    "car": 18.2,
    "rushyd": 95.4,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Derrick Henry",
    "team": "BAL",
    "pos": "RB",
    "games": 17,
    "tgt": 1.2,
    "rec": 0.9,
    "recyd": 8.8,
    "car": 18.1,
    "rushyd": 93.8,
    "att": 0.1,
    "passyd": 0.0
  },
  {
    "player": "Jonathan Taylor",
    "team": "IND",
    "pos": "RB",
    "games": 17,
    "tgt": 3.2,
    "rec": 2.7,
    "recyd": 22.2,
    "car": 19.0,
    "rushyd": 93.2,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Bijan Robinson",
    "team": "ATL",
    "pos": "RB",
    "games": 17,
    "tgt": 6.1,
    "rec": 4.6,
    "recyd": 48.2,
    "car": 16.9,
    "rushyd": 86.9,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "De'Von Achane",
    "team": "MIA",
    "pos": "RB",
    "games": 16,
    "tgt": 5.3,
    "rec": 4.2,
    "recyd": 30.5,
    "car": 14.9,
    "rushyd": 84.4,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "J.K. Dobbins",
    "team": "DEN",
    "pos": "RB",
    "games": 10,
    "tgt": 1.4,
    "rec": 1.1,
    "recyd": 3.7,
    "car": 15.3,
    "rushyd": 77.2,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Javonte Williams",
    "team": "DAL",
    "pos": "RB",
    "games": 16,
    "tgt": 3.2,
    "rec": 2.2,
    "recyd": 8.6,
    "car": 15.8,
    "rushyd": 75.1,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Kyren Williams",
    "team": "LA",
    "pos": "RB",
    "games": 17,
    "tgt": 2.9,
    "rec": 2.1,
    "recyd": 16.5,
    "car": 15.2,
    "rushyd": 73.6,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Jahmyr Gibbs",
    "team": "DET",
    "pos": "RB",
    "games": 17,
    "tgt": 5.5,
    "rec": 4.5,
    "recyd": 36.2,
    "car": 14.3,
    "rushyd": 71.9,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Saquon Barkley",
    "team": "PHI",
    "pos": "RB",
    "games": 16,
    "tgt": 3.1,
    "rec": 2.3,
    "recyd": 17.1,
    "car": 17.5,
    "rushyd": 71.2,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Puka Nacua",
    "team": "LA",
    "pos": "WR",
    "games": 16,
    "tgt": 10.4,
    "rec": 8.1,
    "recyd": 107.2,
    "car": 0.6,
    "rushyd": 6.6,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Jaxon Smith-Njigba",
    "team": "SEA",
    "pos": "WR",
    "games": 17,
    "tgt": 9.6,
    "rec": 7.0,
    "recyd": 105.5,
    "car": 0.4,
    "rushyd": 2.1,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Ja'Marr Chase",
    "team": "CIN",
    "pos": "WR",
    "games": 16,
    "tgt": 11.6,
    "rec": 7.8,
    "recyd": 88.2,
    "car": 0.2,
    "rushyd": 0.9,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "George Pickens",
    "team": "DAL",
    "pos": "WR",
    "games": 17,
    "tgt": 8.1,
    "rec": 5.5,
    "recyd": 84.1,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "CeeDee Lamb",
    "team": "DAL",
    "pos": "WR",
    "games": 13,
    "tgt": 9.0,
    "rec": 5.8,
    "recyd": 82.8,
    "car": 0.1,
    "rushyd": 0.2,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Amon-Ra St. Brown",
    "team": "DET",
    "pos": "WR",
    "games": 17,
    "tgt": 10.1,
    "rec": 6.9,
    "recyd": 82.4,
    "car": 0.2,
    "rushyd": 0.5,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Drake London",
    "team": "ATL",
    "pos": "WR",
    "games": 12,
    "tgt": 9.3,
    "rec": 5.7,
    "recyd": 76.6,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Nico Collins",
    "team": "HOU",
    "pos": "WR",
    "games": 15,
    "tgt": 8.0,
    "rec": 4.7,
    "recyd": 74.5,
    "car": 0.1,
    "rushyd": 1.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Chris Olave",
    "team": "NO",
    "pos": "WR",
    "games": 16,
    "tgt": 9.8,
    "rec": 6.2,
    "recyd": 72.7,
    "car": 0.1,
    "rushyd": -0.2,
    "att": 0.1,
    "passyd": 0.0
  },
  {
    "player": "Rashee Rice",
    "team": "KC",
    "pos": "WR",
    "games": 8,
    "tgt": 9.8,
    "rec": 6.6,
    "recyd": 71.4,
    "car": 0.6,
    "rushyd": 2.5,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Trey McBride",
    "team": "ARI",
    "pos": "TE",
    "games": 17,
    "tgt": 9.9,
    "rec": 7.4,
    "recyd": 72.9,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Tucker Kraft",
    "team": "GB",
    "pos": "TE",
    "games": 8,
    "tgt": 5.5,
    "rec": 4.0,
    "recyd": 61.1,
    "car": 0.1,
    "rushyd": 0.4,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "George Kittle",
    "team": "SF",
    "pos": "TE",
    "games": 11,
    "tgt": 6.3,
    "rec": 5.2,
    "recyd": 57.1,
    "car": 0.1,
    "rushyd": -0.3,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Brock Bowers",
    "team": "LV",
    "pos": "TE",
    "games": 12,
    "tgt": 7.2,
    "rec": 5.3,
    "recyd": 56.7,
    "car": 0.2,
    "rushyd": 0.2,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Kyle Pitts",
    "team": "ATL",
    "pos": "TE",
    "games": 17,
    "tgt": 6.9,
    "rec": 5.2,
    "recyd": 54.6,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Sam LaPorta",
    "team": "DET",
    "pos": "TE",
    "games": 9,
    "tgt": 5.4,
    "rec": 4.4,
    "recyd": 54.3,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Juwan Johnson",
    "team": "NO",
    "pos": "TE",
    "games": 17,
    "tgt": 6.0,
    "rec": 4.5,
    "recyd": 52.3,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Travis Kelce",
    "team": "KC",
    "pos": "TE",
    "games": 17,
    "tgt": 6.4,
    "rec": 4.5,
    "recyd": 50.1,
    "car": 0.1,
    "rushyd": 0.1,
    "att": 0.0,
    "passyd": 0.0
  },
  {
    "player": "Tyler Warren",
    "team": "IND",
    "pos": "TE",
    "games": 17,
    "tgt": 6.6,
    "rec": 4.5,
    "recyd": 48.1,
    "car": 0.4,
    "rushyd": 0.5,
    "att": 0.1,
    "passyd": 0.0
  },
  {
    "player": "Dalton Kincaid",
    "team": "BUF",
    "pos": "TE",
    "games": 12,
    "tgt": 4.1,
    "rec": 3.2,
    "recyd": 47.6,
    "car": 0.0,
    "rushyd": 0.0,
    "att": 0.0,
    "passyd": 0.0
  }
];
// <<< AUTO-GENERATED PLAYERS END

const POSITIONS = ["QB", "RB", "WR", "TE"];

// Which usage figures matter per position, and the scale each bar is drawn
// against so a bar length means the same thing down a column.
const FIELDS = {
  QB: [["att","Pass Att",45],["passyd","Pass Yds",320],["car","Rush Att",10],["rushyd","Rush Yds",60]],
  RB: [["car","Carries",22],["rushyd","Rush Yds",120],["tgt","Targets",7],["rec","Rec",6]],
  WR: [["tgt","Targets",12],["rec","Rec",8],["recyd","Rec Yds",110]],
  TE: [["tgt","Targets",10],["rec","Rec",7],["recyd","Rec Yds",85]],
};

function Bar({ value, max, color }) {
  const w = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div style={{height:4, background:"#ffffff08", borderRadius:2,
      overflow:"hidden", marginTop:4}}>
      <div style={{height:"100%", width:`${w}%`, background:color,
        opacity:.75}} />
    </div>
  );
}

function PlayerCard({ p }) {
  const pc = POS_COLOR[p.pos] || T.muted;
  const fields = FIELDS[p.pos] || [];
  return (
    <div style={{background:T.surface, border:`1px solid ${T.border}`,
      borderRadius:6, padding:"14px 16px", marginBottom:8}}>
      <div style={{display:"flex", alignItems:"baseline", gap:9,
        marginBottom:12, flexWrap:"wrap"}}>
        <span style={{fontSize:15, fontWeight:700, color:T.text,
          fontFamily:T.head}}>{p.player}</span>
        <span style={{fontSize:10, color:pc, fontFamily:T.mono}}>{p.team}</span>
        <span style={{fontSize:9, color:"#444", fontFamily:T.mono}}>
          {p.games} games
        </span>
      </div>
      <div style={{display:"grid",
        gridTemplateColumns:`repeat(${fields.length},1fr)`, gap:14}}>
        {fields.map(([k,label,max]) => (
          <div key={k}>
            <div style={{fontSize:16, fontWeight:800, color:T.text,
              fontFamily:T.mono, lineHeight:1}}>
              {p[k] === null || p[k] === undefined ? "—" : p[k]}
            </div>
            <div style={{fontSize:8, color:"#444", letterSpacing:1,
              marginTop:3}}>{label} / GM</div>
            <Bar value={p[k] || 0} max={max} color={pc} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PlayerStatsHub() {
  const [pos, setPos] = useState("WR");
  const rows = PLAYER_ROWS.filter(p => p.pos === pos);

  return (
    <div style={{padding:"28px 24px 80px", maxWidth:1000, margin:"0 auto",
      fontFamily:T.mono}}>

      <div style={{fontSize:22, fontWeight:800, color:T.text, fontFamily:T.head,
        letterSpacing:1, marginBottom:6}}>PLAYER USAGE</div>
      <div style={{fontSize:10, color:"#666", lineHeight:1.7, maxWidth:"72ch",
        marginBottom:18}}>
        Per-game usage from 2025 logs. Volume is the input the model leans on
        hardest — everything else we tested added little or nothing.
      </div>

      <div style={{display:"flex", gap:4, marginBottom:14}}>
        {POSITIONS.map(p => (
          <button key={p} onClick={() => setPos(p)} style={{
            padding:"5px 14px",
            background: pos===p ? POS_COLOR[p]+"18" : "transparent",
            border:`1px solid ${pos===p ? POS_COLOR[p]+"40" : T.border}`,
            borderRadius:4, color: pos===p ? POS_COLOR[p] : "#555",
            fontSize:11, fontWeight:700, fontFamily:T.mono, cursor:"pointer",
            letterSpacing:1}}>{p}</button>
        ))}
      </div>

      {rows.map((p,i) => <PlayerCard key={i} p={p} />)}

      <div style={{marginTop:20, fontSize:10, color:"#555", lineHeight:1.8,
        maxWidth:"74ch"}}>
        Ranked by primary volume for the position. Rates are per game across
        the games a player actually appeared in, not per 17.
      </div>
    </div>
  );
}
