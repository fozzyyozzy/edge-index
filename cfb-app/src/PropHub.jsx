import { useState } from "react";
// v2026-08-20 — Prop browser. Market columns stay empty until the odds pull runs.

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const POS_COLOR = { QB:"#a855f7", RB:"#00c896", WR:"#00e5ff", TE:"#f5c518" };
const oddsStr = o => (o > 0 ? "+" : "") + o;

// >>> AUTO-GENERATED PROPS BEGIN — written by generate_nfl_data.py
// generated 2026-08-20 from 2025 full-season game logs
const PROP_ROWS = [
  {
    "player": "Christian Watson",
    "team": "GB",
    "pos": "WR",
    "prop": "Receptions",
    "line": 1.5,
    "avg": 3.5,
    "rate": 1.0,
    "hit": 10,
    "of": 10,
    "streak": 10,
    "odds": null,
    "model": null
  },
  {
    "player": "Brock Bowers",
    "team": "LV",
    "pos": "TE",
    "prop": "Rec Yards",
    "line": 25.0,
    "avg": 56.7,
    "rate": 1.0,
    "hit": 12,
    "of": 12,
    "streak": 12,
    "odds": null,
    "model": null
  },
  {
    "player": "Kyren Williams",
    "team": "LA",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 40.0,
    "avg": 73.6,
    "rate": 1.0,
    "hit": 17,
    "of": 17,
    "streak": 17,
    "odds": null,
    "model": null
  },
  {
    "player": "J.K. Dobbins",
    "team": "DEN",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 10.5,
    "avg": 15.3,
    "rate": 1.0,
    "hit": 10,
    "of": 10,
    "streak": 10,
    "odds": null,
    "model": null
  },
  {
    "player": "Trevor Lawrence",
    "team": "JAX",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 150.0,
    "avg": 235.7,
    "rate": 1.0,
    "hit": 17,
    "of": 17,
    "streak": 17,
    "odds": null,
    "model": null
  },
  {
    "player": "Caleb Williams",
    "team": "CHI",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 25.0,
    "avg": 33.4,
    "rate": 1.0,
    "hit": 17,
    "of": 17,
    "streak": 17,
    "odds": null,
    "model": null
  },
  {
    "player": "Caleb Williams",
    "team": "CHI",
    "pos": "QB",
    "prop": "Completions",
    "line": 15.0,
    "avg": 19.4,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 11,
    "odds": null,
    "model": null
  },
  {
    "player": "Dillon Gabriel",
    "team": "CLE",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 0.5,
    "avg": 0.2,
    "rate": 0.9,
    "hit": 9,
    "of": 10,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Nico Collins",
    "team": "HOU",
    "pos": "WR",
    "prop": "Receptions",
    "line": 2.5,
    "avg": 4.7,
    "rate": 1.0,
    "hit": 15,
    "of": 15,
    "streak": 15,
    "odds": null,
    "model": null
  },
  {
    "player": "Trey McBride",
    "team": "ARI",
    "pos": "TE",
    "prop": "Rec Yards",
    "line": 40.0,
    "avg": 72.9,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 2,
    "odds": null,
    "model": null
  },
  {
    "player": "Jaylen Warren",
    "team": "PIT",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 30.0,
    "avg": 59.9,
    "rate": 0.938,
    "hit": 15,
    "of": 16,
    "streak": 4,
    "odds": null,
    "model": null
  },
  {
    "player": "Kyren Williams",
    "team": "LA",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 10.5,
    "avg": 15.2,
    "rate": 1.0,
    "hit": 17,
    "of": 17,
    "streak": 17,
    "odds": null,
    "model": null
  },
  {
    "player": "Caleb Williams",
    "team": "CHI",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 150.0,
    "avg": 231.9,
    "rate": 1.0,
    "hit": 17,
    "of": 17,
    "streak": 17,
    "odds": null,
    "model": null
  },
  {
    "player": "Patrick Mahomes",
    "team": "KC",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 27.0,
    "avg": 35.9,
    "rate": 1.0,
    "hit": 14,
    "of": 14,
    "streak": 14,
    "odds": null,
    "model": null
  },
  {
    "player": "Matthew Stafford",
    "team": "LA",
    "pos": "QB",
    "prop": "Completions",
    "line": 17.5,
    "avg": 22.8,
    "rate": 0.882,
    "hit": 15,
    "of": 17,
    "streak": 7,
    "odds": null,
    "model": null
  },
  {
    "player": "Justin Herbert",
    "team": "LAC",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 1.5,
    "avg": 0.8,
    "rate": 0.875,
    "hit": 14,
    "of": 16,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Keon Coleman",
    "team": "BUF",
    "pos": "WR",
    "prop": "Receptions",
    "line": 1.0,
    "avg": 3.2,
    "rate": 1.0,
    "hit": 12,
    "of": 12,
    "streak": 12,
    "odds": null,
    "model": null
  },
  {
    "player": "Jaxon Smith-Njigba",
    "team": "SEA",
    "pos": "WR",
    "prop": "Rec Yards",
    "line": 65.0,
    "avg": 105.5,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 5,
    "odds": null,
    "model": null
  },
  {
    "player": "Zach Charbonnet",
    "team": "SEA",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 20.0,
    "avg": 45.6,
    "rate": 0.938,
    "hit": 15,
    "of": 16,
    "streak": 14,
    "odds": null,
    "model": null
  },
  {
    "player": "Kenneth Walker III",
    "team": "SEA",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 8.5,
    "avg": 13.0,
    "rate": 1.0,
    "hit": 17,
    "of": 17,
    "streak": 17,
    "odds": null,
    "model": null
  },
  {
    "player": "Matthew Stafford",
    "team": "LA",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 175.0,
    "avg": 276.9,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 7,
    "odds": null,
    "model": null
  },
  {
    "player": "Jared Goff",
    "team": "DET",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 25.5,
    "avg": 34.0,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 12,
    "odds": null,
    "model": null
  },
  {
    "player": "Trevor Lawrence",
    "team": "JAX",
    "pos": "QB",
    "prop": "Completions",
    "line": 15.5,
    "avg": 20.1,
    "rate": 0.882,
    "hit": 15,
    "of": 17,
    "streak": 7,
    "odds": null,
    "model": null
  },
  {
    "player": "Sam Darnold",
    "team": "SEA",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 1.5,
    "avg": 0.8,
    "rate": 0.824,
    "hit": 14,
    "of": 17,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Stefon Diggs",
    "team": "NE",
    "pos": "WR",
    "prop": "Receptions",
    "line": 2.5,
    "avg": 5.0,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 5,
    "odds": null,
    "model": null
  },
  {
    "player": "Harold Fannin Jr.",
    "team": "CLE",
    "pos": "TE",
    "prop": "Rec Yards",
    "line": 20.0,
    "avg": 45.7,
    "rate": 0.938,
    "hit": 15,
    "of": 16,
    "streak": 11,
    "odds": null,
    "model": null
  },
  {
    "player": "Bucky Irving",
    "team": "TB",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 30.0,
    "avg": 58.8,
    "rate": 0.9,
    "hit": 9,
    "of": 10,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "Tony Pollard",
    "team": "TEN",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 9.5,
    "avg": 14.2,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 10,
    "odds": null,
    "model": null
  },
  {
    "player": "Jared Goff",
    "team": "DET",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 175.0,
    "avg": 268.5,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 13,
    "odds": null,
    "model": null
  },
  {
    "player": "Dak Prescott",
    "team": "DAL",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 26.5,
    "avg": 35.3,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Dak Prescott",
    "team": "DAL",
    "pos": "QB",
    "prop": "Completions",
    "line": 18.5,
    "avg": 23.8,
    "rate": 0.882,
    "hit": 15,
    "of": 17,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Jalen Hurts",
    "team": "PHI",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 0.5,
    "avg": 0.4,
    "rate": 0.812,
    "hit": 13,
    "of": 16,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Trey McBride",
    "team": "ARI",
    "pos": "TE",
    "prop": "Receptions",
    "line": 4.5,
    "avg": 7.4,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 2,
    "odds": null,
    "model": null
  },
  {
    "player": "Dallas Goedert",
    "team": "PHI",
    "pos": "TE",
    "prop": "Rec Yards",
    "line": 15.0,
    "avg": 39.4,
    "rate": 0.933,
    "hit": 14,
    "of": 15,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "J.K. Dobbins",
    "team": "DEN",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 45.0,
    "avg": 77.2,
    "rate": 0.9,
    "hit": 9,
    "of": 10,
    "streak": 4,
    "odds": null,
    "model": null
  },
  {
    "player": "Travis Etienne",
    "team": "JAX",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 10.5,
    "avg": 15.3,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 10,
    "odds": null,
    "model": null
  },
  {
    "player": "Dak Prescott",
    "team": "DAL",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 175.0,
    "avg": 267.8,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Matthew Stafford",
    "team": "LA",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 26.5,
    "avg": 35.1,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 11,
    "odds": null,
    "model": null
  },
  {
    "player": "Bryce Young",
    "team": "CAR",
    "pos": "QB",
    "prop": "Completions",
    "line": 14.5,
    "avg": 19.0,
    "rate": 0.875,
    "hit": 14,
    "of": 16,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "Aaron Rodgers",
    "team": "PIT",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 1.0,
    "avg": 0.4,
    "rate": 0.75,
    "hit": 12,
    "of": 16,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Tre Tucker",
    "team": "LV",
    "pos": "WR",
    "prop": "Receptions",
    "line": 1.5,
    "avg": 3.4,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 3,
    "odds": null,
    "model": null
  },
  {
    "player": "Davante Adams",
    "team": "LA",
    "pos": "WR",
    "prop": "Rec Yards",
    "line": 25.0,
    "avg": 56.4,
    "rate": 0.929,
    "hit": 13,
    "of": 14,
    "streak": 4,
    "odds": null,
    "model": null
  },
  {
    "player": "Jacory Croskey-Merritt",
    "team": "WAS",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 20.0,
    "avg": 47.4,
    "rate": 0.882,
    "hit": 15,
    "of": 17,
    "streak": 5,
    "odds": null,
    "model": null
  },
  {
    "player": "Jaylen Warren",
    "team": "PIT",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 8.5,
    "avg": 13.2,
    "rate": 0.938,
    "hit": 15,
    "of": 16,
    "streak": 4,
    "odds": null,
    "model": null
  },
  {
    "player": "Drake Maye",
    "team": "NE",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 175.0,
    "avg": 258.5,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 3,
    "odds": null,
    "model": null
  },
  {
    "player": "Daniel Jones",
    "team": "IND",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 22.5,
    "avg": 29.5,
    "rate": 0.923,
    "hit": 12,
    "of": 13,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Daniel Jones",
    "team": "IND",
    "pos": "QB",
    "prop": "Completions",
    "line": 15.5,
    "avg": 20.1,
    "rate": 0.846,
    "hit": 11,
    "of": 13,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Geno Smith",
    "team": "LV",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 2.0,
    "avg": 1.1,
    "rate": 0.733,
    "hit": 11,
    "of": 15,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Tyler Warren",
    "team": "IND",
    "pos": "TE",
    "prop": "Receptions",
    "line": 2.5,
    "avg": 4.5,
    "rate": 0.941,
    "hit": 16,
    "of": 17,
    "streak": 4,
    "odds": null,
    "model": null
  },
  {
    "player": "CeeDee Lamb",
    "team": "DAL",
    "pos": "WR",
    "prop": "Rec Yards",
    "line": 45.0,
    "avg": 82.8,
    "rate": 0.923,
    "hit": 12,
    "of": 13,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Jordan Mason",
    "team": "MIN",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 20.0,
    "avg": 47.4,
    "rate": 0.875,
    "hit": 14,
    "of": 16,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "Rhamondre Stevenson",
    "team": "NE",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 5.0,
    "avg": 9.3,
    "rate": 0.929,
    "hit": 13,
    "of": 14,
    "streak": 11,
    "odds": null,
    "model": null
  },
  {
    "player": "Patrick Mahomes",
    "team": "KC",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 175.0,
    "avg": 256.2,
    "rate": 0.929,
    "hit": 13,
    "of": 14,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "Trevor Lawrence",
    "team": "JAX",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 24.5,
    "avg": 32.9,
    "rate": 0.882,
    "hit": 15,
    "of": 17,
    "streak": 7,
    "odds": null,
    "model": null
  },
  {
    "player": "Sam Darnold",
    "team": "SEA",
    "pos": "QB",
    "prop": "Completions",
    "line": 14.5,
    "avg": 19.0,
    "rate": 0.824,
    "hit": 14,
    "of": 17,
    "streak": 5,
    "odds": null,
    "model": null
  },
  {
    "player": "Tua Tagovailoa",
    "team": "MIA",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 1.5,
    "avg": 1.1,
    "rate": 0.714,
    "hit": 10,
    "of": 14,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Josh Downs",
    "team": "IND",
    "pos": "WR",
    "prop": "Receptions",
    "line": 1.0,
    "avg": 3.6,
    "rate": 0.938,
    "hit": 15,
    "of": 16,
    "streak": 7,
    "odds": null,
    "model": null
  },
  {
    "player": "Dalton Kincaid",
    "team": "BUF",
    "pos": "TE",
    "prop": "Rec Yards",
    "line": 20.0,
    "avg": 47.6,
    "rate": 0.917,
    "hit": 11,
    "of": 12,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "Javonte Williams",
    "team": "DAL",
    "pos": "RB",
    "prop": "Rush Yards",
    "line": 40.0,
    "avg": 75.1,
    "rate": 0.875,
    "hit": 14,
    "of": 16,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "Bucky Irving",
    "team": "TB",
    "pos": "RB",
    "prop": "Rush Att",
    "line": 12.5,
    "avg": 17.3,
    "rate": 0.9,
    "hit": 9,
    "of": 10,
    "streak": 1,
    "odds": null,
    "model": null
  },
  {
    "player": "C.J. Stroud",
    "team": "HOU",
    "pos": "QB",
    "prop": "Pass Yards",
    "line": 150.0,
    "avg": 217.2,
    "rate": 0.929,
    "hit": 13,
    "of": 14,
    "streak": 6,
    "odds": null,
    "model": null
  },
  {
    "player": "Sam Darnold",
    "team": "SEA",
    "pos": "QB",
    "prop": "Pass Att",
    "line": 21.5,
    "avg": 28.1,
    "rate": 0.882,
    "hit": 15,
    "of": 17,
    "streak": 8,
    "odds": null,
    "model": null
  },
  {
    "player": "Bo Nix",
    "team": "DEN",
    "pos": "QB",
    "prop": "Completions",
    "line": 17.5,
    "avg": 22.8,
    "rate": 0.824,
    "hit": 14,
    "of": 17,
    "streak": 0,
    "odds": null,
    "model": null
  },
  {
    "player": "Jaxson Dart",
    "team": "NYG",
    "pos": "QB",
    "prop": "Interceptions",
    "line": 0.5,
    "avg": 0.4,
    "rate": 0.714,
    "hit": 10,
    "of": 14,
    "streak": 0,
    "odds": null,
    "model": null
  }
];
// <<< AUTO-GENERATED PROPS END

const VIEWS = ["ALL", "WR", "TE", "RB", "QB"];
const SORTS = [
  { id:"rate",  label:"CLEAR RATE", get:r => r.rate },
  { id:"line",  label:"LINE",       get:r => r.line },
  { id:"avg",   label:"AVERAGE",    get:r => r.avg },
  { id:"streak",label:"STREAK",     get:r => r.streak },
];

export default function PropHub() {
  const [view, setView] = useState("ALL");
  const [sort, setSort] = useState("rate");

  const cfg = SORTS.find(s => s.id === sort);
  const rows = (view === "ALL" ? PROP_ROWS : PROP_ROWS.filter(r => r.pos === view))
    .slice().sort((a,b) => cfg.get(b) - cfg.get(a));

  return (
    <div style={{padding:"28px 24px 80px", maxWidth:1000, margin:"0 auto",
      fontFamily:T.mono}}>

      <div style={{fontSize:22, fontWeight:800, color:T.text, fontFamily:T.head,
        letterSpacing:1, marginBottom:6}}>PROP BROWSER</div>
      <div style={{fontSize:10, color:"#666", lineHeight:1.7, maxWidth:"72ch",
        marginBottom:18}}>
        Every prop the floor-line search found, with the measured clear rate
        beside it. Odds and edge fill in when the weekly odds pull runs — they
        are left blank rather than estimated.
      </div>

      <div style={{display:"flex", gap:4, marginBottom:8, flexWrap:"wrap"}}>
        {VIEWS.map(p => (
          <button key={p} onClick={() => setView(p)} style={{
            padding:"5px 12px",
            background: view===p ? (POS_COLOR[p]||"#333")+"18" : "transparent",
            border:`1px solid ${view===p ? (POS_COLOR[p]||"#444")+"40" : T.border}`,
            borderRadius:4, color: view===p ? (POS_COLOR[p]||T.text) : "#555",
            fontSize:10, fontWeight:700, fontFamily:T.mono, cursor:"pointer",
            letterSpacing:1}}>{p}</button>
        ))}
      </div>
      <div style={{display:"flex", gap:4, marginBottom:14, flexWrap:"wrap"}}>
        {SORTS.map(s => (
          <button key={s.id} onClick={() => setSort(s.id)} style={{
            padding:"4px 10px", background:"transparent",
            border:`1px solid ${sort===s.id ? T.nfl+"40" : T.border}`,
            borderRadius:4, color: sort===s.id ? T.nfl : "#444",
            fontSize:9, fontWeight:700, fontFamily:T.mono, cursor:"pointer",
            letterSpacing:1}}>{s.label}</button>
        ))}
      </div>

      <div style={{background:T.surface, border:`1px solid ${T.border}`,
        borderRadius:6, overflow:"hidden"}}>
        <div style={{display:"grid",
          gridTemplateColumns:"38px 1fr 92px 58px 62px 58px 62px",
          gap:8, padding:"9px 14px", borderBottom:`1px solid ${T.border}`,
          fontSize:8, color:"#444", letterSpacing:1.5}}>
          <div>POS</div><div>PLAYER</div><div>PROP</div>
          <div style={{textAlign:"right"}}>LINE</div>
          <div style={{textAlign:"right"}}>CLEARED</div>
          <div style={{textAlign:"right"}}>AVG</div>
          <div style={{textAlign:"right"}}>ODDS</div>
        </div>
        {rows.map((r,i) => {
          const pc = POS_COLOR[r.pos] || T.muted;
          return (
            <div key={i} style={{display:"grid",
              gridTemplateColumns:"38px 1fr 92px 58px 62px 58px 62px", gap:8,
              padding:"10px 14px", alignItems:"center", fontSize:11,
              borderBottom: i < rows.length-1 ? `1px solid ${T.border}` : "none"}}>
              <div style={{fontSize:9, fontWeight:700, color:pc}}>{r.pos}</div>
              <div style={{color:T.text, fontWeight:600, fontFamily:T.head,
                fontSize:13, overflow:"hidden", textOverflow:"ellipsis",
                whiteSpace:"nowrap"}}>{r.player}</div>
              <div style={{color:"#666", fontSize:10}}>{r.prop}</div>
              <div style={{textAlign:"right", color:T.text}}>o{r.line}</div>
              <div style={{textAlign:"right", color:T.accent}}>{r.hit}/{r.of}</div>
              <div style={{textAlign:"right", color:"#888"}}>{r.avg}</div>
              <div style={{textAlign:"right", color: r.odds ? T.text : "#333"}}>
                {r.odds ? oddsStr(r.odds) : "—"}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{marginTop:20, fontSize:10, color:"#555", lineHeight:1.8,
        maxWidth:"74ch"}}>
        Showing {rows.length} of {PROP_ROWS.length} rows. A dash in the odds
        column means no price has been pulled for that line yet.
      </div>
    </div>
  );
}
