import { useState } from "react";

// ── Data ──────────────────────────────────────────────────────────────────────

const DAYS = {
  thu: [
    { player:"Ja'Marr Chase", team:"CIN", opp:"TB", prop:"Rec Yards OVER 72.5", odds:"-115", prob:71, edge:23, tier:1, why:"Zone beater +2.25 yprr vs TB 74% zone. 4 straight OVER. Best play of week." },
    { player:"Sam LaPorta", team:"DET", opp:"DAL", prop:"Receptions OVER 4.5", odds:"-128", prob:68, edge:14, tier:1, why:"DAL weak vs TE middle. Eberflus zone scheme — slot and seam routes exposed." },
    { player:"Caleb Williams", team:"CHI", opp:"DET", prop:"Pass Att OVER 37.5", odds:"-105", prob:61, edge:8, tier:2, why:"CHI 6.5-pt dog. Must-score volume script. Williams averages 39 att/game." },
  ],
  sun1: [
    { player:"Saquon Barkley", team:"PHI", opp:"WAS", prop:"Rush Yards OVER 88.5", odds:"-125", prob:64, edge:16, tier:1, why:"WAS new DC Jones — run D rank 22nd. PHI heavy favorite, game script favors run." },
    { player:"Brock Bowers", team:"LV", opp:"DEN", prop:"Rec Yards OVER 54.5", odds:"-118", prob:62, edge:19, tier:2, why:"DEN zone heavy. Bowers elite route rate. LV dog = elevated pass volume." },
    { player:"Drake London", team:"ATL", opp:"CAR", prop:"Rec Yards OVER 64.5", odds:"-112", prob:61, edge:12, tier:2, why:"CAR bottom-5 defense. London 28%+ target share for 3rd straight season." },
  ],
  sun2: [
    { player:"Jonathan Taylor", team:"IND", opp:"TEN", prop:"Rush Yards OVER 82.5", odds:"-118", prob:62, edge:14, tier:1, why:"TEN new HC Saleh — scheme installation week. Run D rank 18th. Taylor carries this offense." },
    { player:"Trey McBride", team:"ARI", opp:"SF", prop:"Rec Yards OVER 62.5", odds:"-115", prob:64, edge:16, tier:1, why:"SF Morris zone — TE middle of field exposed. McBride league-leading 25.4% TE target share." },
    { player:"Jaxon Smith-Njigba", team:"SEA", opp:"LAR", prop:"Rec Yards OVER 64.5", odds:"-110", prob:63, edge:15, tier:2, why:"33.9% target share — biggest since DeAndre Hopkins 2017. LAR zone coverage." },
  ],
  snf: [
    { player:"Justin Jefferson", team:"MIN", opp:"GB", prop:"Rec Yards OVER 74.5", odds:"-118", prob:65, edge:14, tier:1, why:"GB Gannon man-heavy shift incoming. Jefferson man-beater +2.41 yprr advantage." },
    { player:"Josh Allen", team:"BUF", opp:"KC", prop:"Pass Yards OVER 268.5", odds:"-118", prob:66, edge:10, tier:1, why:"KC blitz 32% — Allen historically elite vs blitz. High-stakes game = pass volume." },
    { player:"Rashee Rice", team:"KC", opp:"BUF", prop:"Rec Yards OVER 62.5", odds:"-112", prob:68, edge:22, tier:1, why:"Zone beater vs BUF Leonhard 71% zone system. 9 of last 10 games OVER this line." },
  ],
  mon: [
    { player:"Lamar Jackson", team:"BAL", opp:"CLE", prop:"Pass Yards OVER 242.5", odds:"-122", prob:64, edge:12, tier:1, why:"CLE Rutenberg — first-year DC, HIGH slot vulnerability. BAL heavy favorite." },
    { player:"Zay Flowers", team:"BAL", opp:"CLE", prop:"Receptions OVER 4.5", odds:"-120", prob:62, edge:13, tier:2, why:"CLE slot coverage rank 31st. Flowers averages 72.4 rec yards — receptions floor is consistent." },
    { player:"Brock Bowers", team:"LV", opp:"DEN", prop:"Rec Yards OVER 54.5", odds:"-118", prob:62, edge:19, tier:2, why:"DEN zone heavy. Bowers elite route rate. Best value in his tier." },
  ],
};

const PLUS_PLAYS = {
  single: [
    { player:"Puka Nacua", team:"LAR", opp:"ARI", prop:"Rec Yards OVER 54.5", odds:"+118", prob:58, edge:14, why:"Line set low due to ARI DC uncertainty. Nacua averaging ~10 targets/game in appearances. Model projects 68.4 yards vs 54.5 line." },
    { player:"Garrett Wilson", team:"NYJ", opp:"NE", prop:"Receptions OVER 5.5", odds:"+105", prob:57, edge:11, why:"NE new DC Kuhr — first year. Wilson 30.4% target share. Jets dog so pass volume elevated." },
    { player:"Breece Hall", team:"NYJ", opp:"NE", prop:"Rush+Rec OVER 74.5", odds:"+112", prob:56, edge:10, why:"NE run D rank 28th. Hall dual-threat floor. Glenn scheme prioritizes RB usage." },
  ],
  parlay: [
    { player:"Josh Allen", team:"BUF", opp:"KC", prop:"Pass Yards OVER 248.5", odds:"+102", prob:55, edge:9, why:"Reduced line from posted 268.5. Excellent parlay leg — correlated with BUF WR props. Pair with Diggs or Shakir." },
    { player:"Rashee Rice", team:"KC", opp:"BUF", prop:"Rec Yards OVER 52.5", odds:"+108", prob:56, edge:16, why:"Floor line. 9 of last 10 games hit 50+ yards. Combine with Chase for AFC Thursday parlay at +280." },
    { player:"Lamar Jackson", team:"BAL", opp:"CLE", prop:"Rush Yards OVER 28.5", odds:"+115", prob:58, edge:12, why:"Lamar's rushing floor is essentially automatic. Pairs with pass yards for correlated MNF parlay." },
  ],
  long: [
    { player:"Amon-Ra St. Brown", team:"DET", opp:"DAL", prop:"Rec Yards OVER 84.5", odds:"+202", prob:52, edge:18, why:"Model projects 81.2 avg — 84.5 barely above average. Boom rate 24%. High ceiling matchup vs DAL zone. DAL run D rank 12th means game stays passing." },
    { player:"Jonathan Taylor", team:"IND", opp:"TEN", prop:"Rush Yards OVER 114.5", odds:"+248", prob:48, edge:14, why:"Hit 100+ yards in 7 of last 10 games. TEN scheme installation week = exploit period. 114.5 hits ~48% in favorable matchups." },
    { player:"Trey McBride", team:"ARI", opp:"SF", prop:"Rec Yards OVER 84.5", odds:"+235", prob:46, edge:19, why:"McBride ceiling is 108 yards. SF Morris zone exposes TE middle. ARI will be trailing — pass volume spikes." },
  ],
};

const ALL_PROPS = [
  { player:"Ja'Marr Chase",         team:"CIN", opp:"TB",  pos:"WR", prop:"Rec Yards",  ptype:"yards", line:72.5,  odds:"-115",  prob:71, edge:23, streak:[1,1,1,1,0], safe:"50.5 (-185)", best:"62.5 (-145)", tier:1 },
  { player:"Rashee Rice",            team:"KC",  opp:"BUF", pos:"WR", prop:"Rec Yards",  ptype:"yards", line:62.5,  odds:"-112",  prob:68, edge:22, streak:[1,1,1,1,1], safe:"42.5 (-178)", best:"52.5 (-142)", tier:1 },
  { player:"Amon-Ra St. Brown",      team:"DET", opp:"DAL", pos:"WR", prop:"Rec Yards",  ptype:"yards", line:68.5,  odds:"-120",  prob:67, edge:18, streak:[1,1,0,1,1], safe:"45.5 (-175)", best:"57.5 (-140)", tier:1 },
  { player:"Josh Allen",             team:"BUF", opp:"KC",  pos:"QB", prop:"Pass Yards", ptype:"pass",  line:268.5, odds:"-118",  prob:66, edge:10, streak:[1,1,0,1,1], safe:"225.5 (-188)", best:"248.5 (-148)", tier:1 },
  { player:"Justin Jefferson",       team:"MIN", opp:"GB",  pos:"WR", prop:"Rec Yards",  ptype:"yards", line:74.5,  odds:"-118",  prob:65, edge:14, streak:[0,1,1,1,1], safe:"48.5 (-175)", best:"62.5 (-138)", tier:1 },
  { player:"Trey McBride",           team:"ARI", opp:"SF",  pos:"TE", prop:"Rec Yards",  ptype:"yards", line:62.5,  odds:"-115",  prob:64, edge:16, streak:[1,1,1,0,1], safe:"42.5 (-172)", best:"52.5 (-138)", tier:1 },
  { player:"Saquon Barkley",         team:"PHI", opp:"WAS", pos:"RB", prop:"Rush Yards", ptype:"rush",  line:88.5,  odds:"-125",  prob:64, edge:16, streak:[1,1,1,0,1], safe:"58.5 (-182)", best:"74.5 (-144)", tier:1 },
  { player:"Lamar Jackson",          team:"BAL", opp:"CLE", pos:"QB", prop:"Pass Yards", ptype:"pass",  line:242.5, odds:"-122",  prob:64, edge:12, streak:[1,1,1,1,0], safe:"195.5 (-182)", best:"224.5 (-144)", tier:1 },
  { player:"Jaxon Smith-Njigba",     team:"SEA", opp:"LAR", pos:"WR", prop:"Rec Yards",  ptype:"yards", line:64.5,  odds:"-110",  prob:63, edge:15, streak:[1,1,1,1,0], safe:"42.5 (-168)", best:"54.5 (-132)", tier:2 },
  { player:"Jonathan Taylor",        team:"IND", opp:"TEN", pos:"RB", prop:"Rush Yards", ptype:"rush",  line:82.5,  odds:"-118",  prob:62, edge:14, streak:[1,0,1,1,1], safe:"54.5 (-178)", best:"68.5 (-141)", tier:2 },
  { player:"Brock Bowers",           team:"LV",  opp:"DEN", pos:"TE", prop:"Rec Yards",  ptype:"yards", line:54.5,  odds:"-118",  prob:62, edge:19, streak:[1,0,1,1,1], safe:"36.5 (-168)", best:"46.5 (-132)", tier:2 },
  { player:"Caleb Williams",         team:"CHI", opp:"DET", pos:"QB", prop:"Pass Att",   ptype:"pass",  line:37.5,  odds:"-105",  prob:61, edge:8,  streak:[1,0,1,1,1], safe:"28.5 (-172)", best:"33.5 (-135)", tier:2 },
  { player:"CeeDee Lamb",            team:"DAL", opp:"DET", pos:"WR", prop:"Rec Yards",  ptype:"yards", line:74.5,  odds:"-118",  prob:62, edge:12, streak:[1,0,0,1,1], safe:"50.5 (-172)", best:"62.5 (-138)", tier:2 },
  { player:"Puka Nacua",             team:"LAR", opp:"ARI", pos:"WR", prop:"Rec Yards",  ptype:"yards", line:54.5,  odds:"+118",  prob:58, edge:14, streak:[1,1,0,1,1], safe:"38.5 (-158)", best:"48.5 (-118)", tier:2 },
  { player:"Khalil Shakir",          team:"BUF", opp:"KC",  pos:"WR", prop:"Rec Yards",  ptype:"yards", line:58.5,  odds:"-108",  prob:58, edge:9,  streak:[0,1,1,0,1], safe:"38.5 (-165)", best:"48.5 (-128)", tier:2 },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
const probColor = (p) => p >= 68 ? "#00c896" : p >= 58 ? "#ffa502" : "#8888a8";
const T = {
  bg:"#0a0a0f", surface:"#12121a", card:"#1a1a26", border:"#2a2a3d",
  accent:"#00e5ff", gold:"#f5c518", green:"#00c896", red:"#ff4757",
  amber:"#ffa502", text:"#e8e8f0", muted:"#8888a8", dim:"#4a4a6a",
};

const DAY_LABELS = {
  thu: "Thursday Night",
  sun1: "Sunday Early",
  sun2: "Sunday Afternoon",
  snf: "Sunday Night Football",
  mon: "Monday Night Football",
};

const DAY_COLORS = {
  thu: T.amber, sun1: T.accent, sun2: T.accent, snf: T.accent, mon: T.green,
};

// ── CSS ───────────────────────────────────────────────────────────────────────
const css = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Barlow:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0a0a0f;color:#e8e8f0;font-family:'Barlow',sans-serif;font-size:14px;min-height:100vh;}
.mono{font-family:'IBM Plex Mono',monospace;}
.pg{max-width:1040px;margin:0 auto;padding:20px 16px;}
.pg-t{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;margin-bottom:3px;}
.pg-s{font-size:12px;color:#8888a8;margin-bottom:18px;}
.tabs{display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap;}
.tab{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:6px 14px;border-radius:4px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;}
.tab:hover{color:#e8e8f0;} .tab.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.day-strip{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap;}
.day-btn{padding:6px 14px;border-radius:4px;border:1px solid #2a2a3d;font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;background:transparent;color:#8888a8;}
.day-btn:hover{color:#e8e8f0;}
.day-btn.thu-on{background:#ffa50222;color:#ffa502;border-color:#ffa50244;}
.day-btn.sun-on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.day-btn.mon-on{background:#00c89622;color:#00c896;border-color:#00c89644;}
.potd{background:#1a1a26;border:2px solid #f5c51844;border-radius:6px;padding:16px 20px;margin-bottom:16px;}
.potd-badge{display:inline-flex;align-items:center;gap:5px;background:#f5c51822;color:#f5c518;font-size:11px;font-weight:700;padding:3px 10px;border-radius:3px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px;}
.potd-body{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:center;}
.potd-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;}
.ptag{font-size:11px;padding:2px 8px;border-radius:3px;border:1px solid #2a2a3d;color:#8888a8;background:#12121a;}
.ptag-g{color:#00c896;background:#00c89612;border-color:#00c89628;}
.card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;}
.card-hdr{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;padding-bottom:8px;border-bottom:1px solid #2a2a3d;margin-bottom:12px;}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px;margin-bottom:16px;}
.fcard{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;}
.t1b{background:#f5c51822;color:#f5c518;border:1px solid #f5c51844;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.t2b{background:#00e5ff18;color:#00e5ff;border:1px solid #00e5ff33;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.seclbl{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#8888a8;margin-bottom:10px;}
.pb-s{background:#00c89622;color:#00c896;border:1px solid #00c89644;font-size:11px;padding:2px 8px;border-radius:3px;font-weight:500;}
.pb-p{background:#00e5ff18;color:#00e5ff;border:1px solid #00e5ff33;font-size:11px;padding:2px 8px;border-radius:3px;font-weight:500;}
.pb-l{background:#ffa50218;color:#ffa502;border:1px solid #ffa50233;font-size:11px;padding:2px 8px;border-radius:3px;font-weight:500;}
.pbar{height:5px;background:#2a2a3d;border-radius:3px;overflow:hidden;margin:6px 0 4px;}
.pbfill{height:100%;border-radius:3px;background:#00c896;}
.pwhy{font-size:11px;color:#8888a8;margin-top:8px;line-height:1.6;border-top:1px solid #2a2a3d;padding-top:8px;}
.sinp{flex:1;min-width:150px;padding:7px 12px;border-radius:4px;border:1px solid #2a2a3d;background:#12121a;color:#e8e8f0;font-size:13px;outline:none;}
.sinp:focus{border-color:#00e5ff;}
.fsel{padding:6px 10px;border-radius:4px;border:1px solid #2a2a3d;background:#12121a;color:#8888a8;font-size:12px;}
.srow{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center;}
.btbl{width:100%;border-collapse:collapse;}
.btbl th{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;text-align:left;padding:6px 8px;border-bottom:1px solid #2a2a3d;}
.btbl td{padding:10px 8px;border-bottom:1px solid #2a2a3d66;font-size:13px;vertical-align:middle;}
.btbl tr:last-child td{border-bottom:none;}
.btbl tr:hover td{background:#12121a;}
.sdots{display:flex;gap:2px;}
.sd{width:8px;height:8px;border-radius:50%;}
.sh{background:#00c896;} .sm{background:#ff4757;}
.btn-full{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:transparent;color:#00e5ff;border:1px solid #00e5ff44;border-radius:3px;padding:7px 16px;cursor:pointer;width:100%;margin-top:10px;}
.btn-full:hover{background:#00e5ff18;}
`;

// ── Components ────────────────────────────────────────────────────────────────

function FeaturedView() {
  const [day, setDay] = useState("thu");
  const plays = DAYS[day] || [];
  const dayColor = DAY_COLORS[day];
  const onClass = (d) => {
    const map = { thu:"thu-on", sun1:"sun-on", sun2:"sun-on", snf:"sun-on", mon:"mon-on" };
    return day === d ? map[d] || "" : "";
  };

  return (
    <div>
      <div className="day-strip">
        {Object.entries(DAY_LABELS).map(([d, lbl]) => (
          <button key={d} className={"day-btn " + onClass(d)} onClick={() => setDay(d)}>
            {lbl.split(" ").slice(-1)[0] === "Football" ? "Mon Night" : lbl.split(" ").slice(0, 2).join(" ")}
          </button>
        ))}
      </div>

      <div className="potd">
        <div className="potd-badge">★ Prop of the Day — Week 10</div>
        <div className="potd-body">
          <div>
            <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:20, fontWeight:800 }}>
              Ja'Marr Chase
            </div>
            <div style={{ fontSize:12, color:T.muted, marginTop:2 }}>CIN @ TB · Wide Receiver</div>
            <div style={{ fontSize:16, fontWeight:500, marginTop:6 }}>
              Rec Yards OVER 72.5{" "}
              <span style={{ fontSize:13, color:T.muted, fontWeight:400 }}>-115</span>
            </div>
            <div style={{ fontSize:12, color:T.muted, marginTop:3 }}>
              Optimal line: OVER 62.5 at -145 · 81% hit rate · Best value tier
            </div>
          </div>
          <div style={{ textAlign:"right" }}>
            <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:32, fontWeight:800, color:T.green }}>71%</div>
            <div style={{ fontSize:11, color:T.muted }}>win prob</div>
            <div style={{ fontSize:13, fontWeight:500, color:T.green, marginTop:4 }}>+23% edge</div>
          </div>
        </div>
        <div className="potd-tags">
          {["Zone beater +2.25 yprr","TB 74% zone","4 straight OVER","Slot rank #4 vuln"].map(t => (
            <span key={t} className="ptag ptag-g">{t}</span>
          ))}
          <span className="ptag">CIN -3.5 · Total 48.5</span>
          <span className="ptag">DC changed ⚠</span>
        </div>
      </div>

      <div style={{ fontSize:11, fontWeight:700, letterSpacing:".15em", textTransform:"uppercase", color:dayColor, marginBottom:12, fontFamily:"'Barlow Condensed',sans-serif" }}>
        {DAY_LABELS[day]} · Week 10
      </div>

      <div className="grid3">
        {plays.map((p, i) => (
          <div key={i} className="fcard">
            <div style={{ fontSize:10, fontWeight:700, letterSpacing:".12em", textTransform:"uppercase", color:dayColor, marginBottom:6, fontFamily:"'Barlow Condensed',sans-serif" }}>
              {DAY_LABELS[day]} · {p.team} vs {p.opp}
            </div>
            <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:17, fontWeight:800, marginBottom:2 }}>{p.player}</div>
            <div style={{ fontSize:12, color:T.muted, marginBottom:10 }}>{p.team}</div>
            <div style={{ background:T.surface, borderRadius:4, padding:"8px 10px", marginBottom:8 }}>
              <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:14, fontWeight:700 }}>{p.prop}</div>
              <div style={{ fontSize:11, color:T.muted, marginTop:3, lineHeight:1.5 }}>{p.why}</div>
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:16, fontWeight:800, color:probColor(p.prob) }}>{p.prob}% prob</div>
              <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:12, color:T.muted }}>{p.odds}</div>
              {p.tier === 1 ? <span className="t1b">★★★ T1</span> : <span className="t2b">★★ T2</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PlusMoneyView() {
  const sections = [
    { key:"single", label:"Single-leg plays · +100 to +175", cls:"pb-s", badge:"Single leg" },
    { key:"parlay", label:"Best parlay legs · combine for +200 to +350", cls:"pb-p", badge:"Parlay leg" },
    { key:"long",   label:"Value plays · +200 to +300 · model vs market", cls:"pb-l", badge:"Value play" },
  ];
  return (
    <div>
      <div style={{ fontSize:13, color:T.muted, marginBottom:16, lineHeight:1.7 }}>
        Model-identified edges at plus-money odds. Each play has 55%+ estimated probability.
        The chalk market is efficient — these are where real value hides.
      </div>
      {sections.map(({ key, label, cls, badge }) => (
        <div key={key}>
          <div className="seclbl">{label}</div>
          <div className="grid3" style={{ marginBottom:20 }}>
            {(PLUS_PLAYS[key] || []).map((p, i) => (
              <div key={i} className="card">
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
                  <span className={cls}>{badge}</span>
                  <span style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:24, fontWeight:800, color:T.green }}>{p.odds}</span>
                </div>
                <div style={{ fontFamily:"'Barlow Condensed',sans-serif", fontSize:16, fontWeight:700, marginBottom:2 }}>{p.player}</div>
                <div style={{ fontSize:13, color:T.muted, marginBottom:6 }}>{p.prop} · {p.team} vs {p.opp}</div>
                <div className="pbar"><div className="pbfill" style={{ width:p.prob+"%" }} /></div>
                <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:T.muted }}>
                  <span>{p.prob}% win prob</span>
                  <span>+{p.edge}% edge</span>
                </div>
                <div className="pwhy">{p.why}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function BrowseView() {
  const [search, setSearch] = useState("");
  const [pos,    setPos]    = useState("ALL");
  const [ptype,  setPtype]  = useState("ALL");
  const [odds,   setOdds]   = useState("ALL");
  const [sort,   setSort]   = useState("prob");

  const filtered = ALL_PROPS
    .filter(r => {
      const s = search.toLowerCase();
      if (s && !r.player.toLowerCase().includes(s) && !r.team.toLowerCase().includes(s) && !r.opp.toLowerCase().includes(s)) return false;
      if (pos   !== "ALL" && r.pos   !== pos)   return false;
      if (ptype !== "ALL" && r.ptype !== ptype)  return false;
      if (odds  === "plus" && !r.odds.startsWith("+")) return false;
      if (odds  === "fav"  &&  r.odds.startsWith("+")) return false;
      return true;
    })
    .sort((a, b) =>
      sort === "prob"   ? b.prob - a.prob :
      sort === "edge"   ? b.edge - a.edge :
      b.streak.filter(x=>x).length - a.streak.filter(x=>x).length
    );

  return (
    <div>
      <div className="srow">
        <input
          className="sinp"
          type="text"
          placeholder="Search player, team, or opponent..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select className="fsel" value={pos}   onChange={e => setPos(e.target.value)}>
          <option value="ALL">All positions</option>
          <option value="WR">WR</option><option value="QB">QB</option>
          <option value="RB">RB</option><option value="TE">TE</option>
        </select>
        <select className="fsel" value={ptype} onChange={e => setPtype(e.target.value)}>
          <option value="ALL">All prop types</option>
          <option value="yards">Rec yards</option>
          <option value="rush">Rush yards</option>
          <option value="pass">Pass yards / att</option>
        </select>
        <select className="fsel" value={odds}  onChange={e => setOdds(e.target.value)}>
          <option value="ALL">All odds</option>
          <option value="plus">Plus-money only</option>
          <option value="fav">Favored only</option>
        </select>
        <select className="fsel" value={sort}  onChange={e => setSort(e.target.value)}>
          <option value="prob">Sort: probability</option>
          <option value="edge">Sort: edge %</option>
          <option value="streak">Sort: streak</option>
        </select>
      </div>
      <div style={{ fontSize:12, color:T.muted, marginBottom:10 }}>
        {filtered.length} props matching filters
      </div>
      <div style={{ overflowX:"auto" }}>
        <table className="btbl">
          <thead>
            <tr>
              <th>Player</th>
              <th>Prop</th>
              <th>Posted line</th>
              <th>Prob</th>
              <th>Last 5</th>
              <th>Safe line</th>
              <th>Best value</th>
              <th>Tier</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={i}>
                <td>
                  <div style={{ fontWeight:500, color:T.text }}>{r.player}</div>
                  <div style={{ fontSize:11, color:T.muted }}>{r.team} vs {r.opp} · {r.pos}</div>
                </td>
                <td style={{ color:T.muted, fontSize:13 }}>{r.prop}</td>
                <td>
                  <div style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:12 }}>{r.line} OVER</div>
                  <div style={{ fontSize:11, color:T.muted }}>{r.odds}</div>
                </td>
                <td>
                  <div style={{ fontSize:14, fontWeight:500, color:probColor(r.prob) }}>{r.prob}%</div>
                  <div style={{ fontSize:11, color:T.green }}>+{r.edge}%</div>
                </td>
                <td>
                  <div className="sdots">
                    {r.streak.map((d, j) => (
                      <div key={j} className={"sd " + (d ? "sh" : "sm")} />
                    ))}
                  </div>
                </td>
                <td style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:12, color:T.accent }}>{r.safe}</td>
                <td style={{ fontFamily:"'IBM Plex Mono',monospace", fontSize:12, color:T.green }}>{r.best}</td>
                <td>{r.tier === 1 ? <span className="t1b">★★★</span> : <span className="t2b">★★</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function PropHub() {
  const [view, setView] = useState("featured");
  const tabs = [
    { id:"featured", l:"Featured" },
    { id:"plus",     l:"+ Money Plays" },
    { id:"browse",   l:"Browse All Props" },
  ];
  return (
    <div className="pg">
      <style>{css}</style>
      <div className="pg-t">NFL Prop Intelligence — Week 10</div>
      <div className="pg-s">Featured matchups · Plus-money edges · Full searchable prop database · Optimal line analysis</div>
      <div className="tabs">
        {tabs.map(t => (
          <button key={t.id} className={"tab " + (view === t.id ? "on" : "")} onClick={() => setView(t.id)}>
            {t.l}
          </button>
        ))}
      </div>
      {view === "featured" && <FeaturedView />}
      {view === "plus"     && <PlusMoneyView />}
      {view === "browse"   && <BrowseView />}
    </div>
  );
}
