import { useState } from "react";

const T = {
  bg:"#0a0a0f",surface:"#12121a",card:"#1a1a26",border:"#2a2a3d",borderHi:"#3d3d5c",
  accent:"#00e5ff",gold:"#f5c518",green:"#00c896",red:"#ff4757",amber:"#ffa502",
  purple:"#a855f7",text:"#e8e8f0",muted:"#8888a8",dim:"#4a4a6a",
};

const css = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=Barlow:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0a0a0f;color:#e8e8f0;font-family:'Barlow',sans-serif;font-size:14px;min-height:100vh;}
::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-track{background:#0a0a0f;} ::-webkit-scrollbar-thumb{background:#2a2a3d;border-radius:2px;}
.mono{font-family:'IBM Plex Mono',monospace;} .cond{font-family:'Barlow Condensed',sans-serif;}
.nav{background:#0a0a0fee;backdrop-filter:blur(12px);border-bottom:1px solid #2a2a3d;display:flex;align-items:center;padding:0 20px;height:52px;gap:0;position:sticky;top:0;z-index:200;overflow-x:auto;}
.nav-logo{font-family:'Barlow Condensed',sans-serif;font-size:21px;font-weight:800;letter-spacing:.08em;color:#00e5ff;text-transform:uppercase;margin-right:24px;cursor:pointer;white-space:nowrap;flex-shrink:0;}
.nav-logo span{color:#f5c518;}
.nav-tab{height:52px;padding:0 13px;display:flex;align-items:center;font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;cursor:pointer;border-bottom:2px solid transparent;transition:color .15s,border-color .15s;white-space:nowrap;flex-shrink:0;}
.nav-tab:hover{color:#e8e8f0;} .nav-tab.on{color:#00e5ff;border-bottom-color:#00e5ff;}
.nav-div{width:1px;height:22px;background:#2a2a3d;margin:0 6px;flex-shrink:0;}
.nav-sec{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#4a4a6a;padding:0 6px;flex-shrink:0;}
.nav-right{margin-left:auto;display:flex;align-items:center;gap:10px;flex-shrink:0;padding-left:12px;}
.nav-badge{font-family:'IBM Plex Mono',monospace;font-size:10px;background:#00e5ff22;color:#00e5ff;border:1px solid #00e5ff44;padding:2px 7px;border-radius:3px;}
.btn-unlock{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;background:#00e5ff;color:#0a0a0f;border:none;border-radius:3px;padding:6px 14px;cursor:pointer;}
.btn-unlock:hover{opacity:.85;}
.pg{max-width:960px;margin:0 auto;padding:20px 16px;}
.pg-title{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;margin-bottom:3px;}
.pg-sub{font-size:12px;color:#8888a8;margin-bottom:18px;}
.card{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:16px;margin-bottom:12px;}
.card-hdr{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;padding-bottom:10px;border-bottom:1px solid #2a2a3d;margin-bottom:12px;}
.sg{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;}
.sb{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:12px 14px;}
.sl{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.sv{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;line-height:1;}
.ss{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#8888a8;margin-top:3px;}
.itabs{display:flex;gap:4px;margin-bottom:14px;flex-wrap:wrap;}
.itab{font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;padding:5px 11px;border-radius:3px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;white-space:nowrap;}
.itab:hover{color:#e8e8f0;} .itab.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.fr{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;align-items:center;}
.fl{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;}
.fb{font-family:'Barlow Condensed',sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:3px;border:1px solid #2a2a3d;color:#8888a8;cursor:pointer;background:transparent;}
.fb:hover{color:#e8e8f0;} .fb.on{background:#00e5ff22;color:#00e5ff;border-color:#00e5ff44;}
.dt{width:100%;border-collapse:collapse;}
.dt th{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;text-align:left;padding:6px 8px;border-bottom:1px solid #2a2a3d;}
.dt td{padding:10px 8px;border-bottom:1px solid #2a2a3d66;font-size:13px;}
.dt tr:last-child td{border-bottom:none;} .dt tr:hover td{background:#12121a;}
.pt{height:5px;background:#2a2a3d;border-radius:3px;overflow:hidden;}
.pf{height:100%;border-radius:3px;}
.sl2{font-family:'Barlow Condensed',sans-serif;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#8888a8;display:flex;align-items:center;gap:10px;margin-bottom:12px;}
.sl2::after{content:'';flex:1;height:1px;background:#2a2a3d;}
.t1{background:#f5c51822;color:#f5c518;border:1px solid #f5c51844;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;white-space:nowrap;}
.t2{background:#00e5ff18;color:#00e5ff;border:1px solid #00e5ff33;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;white-space:nowrap;}
.rw{background:#00c89622;color:#00c896;border:1px solid #00c89644;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.rl{background:#ff475722;color:#ff4757;border:1px solid #ff475744;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;}
.lock{position:relative;overflow:hidden;min-height:240px;}
.lock-blur{filter:blur(5px);pointer-events:none;user-select:none;opacity:.35;}
.lock-gate{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0a0a0fcc;backdrop-filter:blur(4px);gap:10px;z-index:10;}
.lock-t{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:800;text-transform:uppercase;}
.lock-s{font-size:12px;color:#8888a8;text-align:center;max-width:240px;}
.bp{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:#00e5ff;color:#0a0a0f;border:none;border-radius:3px;padding:8px 20px;cursor:pointer;}
.bs{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;background:transparent;color:#8888a8;border:1px solid #2a2a3d;border-radius:3px;padding:7px 16px;cursor:pointer;}
.pr{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-bottom:8px;display:grid;grid-template-columns:auto 1fr auto auto;gap:12px;align-items:center;transition:border-color .15s;}
.pr:hover{border-color:#3d3d5c;} .t1r{border-left:3px solid #f5c518;} .t2r{border-left:3px solid #00e5ff;}
.sig{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;background:#12121a;border:1px solid #2a2a3d;color:#8888a8;padding:1px 5px;border-radius:2px;margin:1px;}
.sz{color:#00e5ff;background:#00e5ff12;border-color:#00e5ff28;} .ss2{color:#00c896;background:#00c89612;border-color:#00c89628;} .sv2{color:#ff4757;background:#ff475712;border-color:#ff475728;}
.pc{background:#12121a;border:1px solid #2a2a3d;border-radius:5px;padding:14px 16px;margin-bottom:8px;}
.po{font-family:'Barlow Condensed',sans-serif;font-size:30px;font-weight:800;color:#00c896;line-height:1;}
.pl{font-size:12px;color:#8888a8;margin-top:3px;display:flex;align-items:center;gap:5px;}
.pl::before{content:'+';font-family:'IBM Plex Mono',monospace;color:#4a4a6a;font-size:10px;}
.gc{background:#1a1a26;border:1px solid #2a2a3d;border-radius:6px;margin-bottom:10px;overflow:hidden;cursor:pointer;transition:border-color .15s;}
.gc:hover{border-color:#3d3d5c;} .gc.ex{border-color:#00e5ff66;}
.gh{padding:14px 16px;display:grid;grid-template-columns:1fr auto auto;gap:12px;align-items:center;}
.at{font-family:'Barlow Condensed',sans-serif;font-size:14px;font-weight:600;color:#8888a8;margin-bottom:2px;}
.ht{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:800;}
.cb{font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid;margin-top:4px;display:inline-block;}
.eb{text-align:center;padding:8px 14px;border-radius:4px;}
.ev{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:800;line-height:1;}
.el{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#8888a8;margin-top:3px;}
.bt-tags{display:flex;flex-direction:column;gap:4px;align-items:flex-end;}
.bt{font-family:'IBM Plex Mono',monospace;font-size:10px;padding:3px 8px;border-radius:3px;border:1px solid;white-space:nowrap;}
.gb{border-top:1px solid #2a2a3d;padding:16px;}
.mg{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px;}
.mb{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:10px;text-align:center;}
.mn{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:6px;}
.ms{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:800;line-height:1;}
.ab{display:flex;align-items:center;gap:10px;margin-bottom:14px;}
.at2{flex:1;height:6px;background:#2a2a3d;border-radius:3px;overflow:hidden;}
.af{height:100%;border-radius:3px;}
.fg{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px;}
.fb2{background:#12121a;border:1px solid #2a2a3d;border-radius:4px;padding:10px 12px;}
.fl2{font-family:'Barlow Condensed',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8888a8;margin-bottom:5px;}
.df{background:#ffa50218;border:1px solid #ffa50233;border-radius:3px;padding:6px 10px;font-size:11px;color:#ffa502;margin-bottom:10px;}
.st{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;background:#12121a;border:1px solid #2a2a3d;color:#8888a8;padding:2px 6px;border-radius:2px;margin:2px;}
.sp{color:#00c896;background:#00c89612;border-color:#00c89628;} .sn{color:#ff4757;background:#ff475712;border-color:#ff475728;} .su{color:#ffa502;background:#ffa50212;border-color:#ffa50228;}
.prow{display:grid;grid-template-columns:28px 1fr 60px 60px 60px 60px 80px;gap:8px;align-items:center;padding:10px 12px;border-bottom:1px solid #2a2a3d66;font-size:13px;cursor:pointer;}
.prow:last-child{border-bottom:none;} .prow:hover{background:#12121a;}
.cpb{height:4px;background:#2a2a3d;border-radius:2px;margin-top:4px;overflow:hidden;}
.cpf{height:100%;border-radius:2px;}
.vb{height:4px;border-radius:2px;background:#2a2a3d;overflow:hidden;margin-top:4px;}
.vf{height:100%;border-radius:2px;}
.ch{color:#ff4757;font-weight:700;} .cm{color:#ffa502;font-weight:700;} .cl{color:#00c896;font-weight:700;}
.dc-c{color:#ffa502;font-size:11px;} .dc-r{color:#00c896;font-size:11px;}
.hero{text-align:center;padding:56px 16px 40px;}
.hre{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#00e5ff;margin-bottom:18px;opacity:.8;}
.hrh{font-family:'Barlow Condensed',sans-serif;font-size:clamp(44px,7vw,84px);font-weight:800;letter-spacing:-.01em;line-height:.95;text-transform:uppercase;margin-bottom:20px;}
.hrh span{color:#00e5ff;}
.hrs{font-size:14px;color:#8888a8;max-width:480px;margin:0 auto 28px;line-height:1.7;}
.hrc{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;}
.feg{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;max-width:820px;margin:0 0 24px;}
.feb{background:#1a1a26;border:1px solid #2a2a3d;border-radius:5px;padding:16px;}
.fei{font-size:16px;color:#00e5ff;margin-bottom:8px;font-family:'IBM Plex Mono',monospace;}
.fet{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;margin-bottom:4px;}
.fed{font-size:12px;color:#8888a8;line-height:1.5;}
.modal-bg{position:fixed;inset:0;background:#000c;display:flex;align-items:center;justify-content:center;z-index:1000;backdrop-filter:blur(8px);}
.modal{background:#1a1a26;border:1px solid #2a2a3d;border-radius:7px;padding:32px 28px;max-width:360px;width:calc(100% - 32px);}
.ki{background:#12121a;border:1px solid #2a2a3d;border-radius:3px;color:#e8e8f0;font-family:'IBM Plex Mono',monospace;font-size:12px;padding:7px 12px;width:100%;outline:none;}
.ki:focus{border-color:#00e5ff;} .ki::placeholder{color:#4a4a6a;}
.es{text-align:center;padding:60px 24px;}
.ei2{font-size:40px;margin-bottom:16px;opacity:.4;}
.et{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:800;text-transform:uppercase;margin-bottom:8px;}
.ed{font-size:13px;color:#8888a8;line-height:1.7;max-width:340px;margin:0 auto;}
`;

// ── Data ──────────────────────────────────────────────────────────────────────
const NFL_PICKS=[
  {player:"Rashee Rice",team:"KC",opp:"TB",prop:"Receptions",dir:"OVER",line:5.5,proj:6.5,edge:18.0,prob:67,tier:1,scheme:"ZONE",sigs:["Zone beater +2.25 yprr","TB 74% zone","Slot rank #4 vuln"]},
  {player:"Rashee Rice",team:"KC",opp:"TB",prop:"Rec Yards",dir:"OVER",line:62.5,proj:76.6,edge:22.5,prob:71,tier:1,scheme:"ZONE",sigs:["Zone beater +2.25 yprr","TB 74% zone","Total 51.5"]},
  {player:"Amon-Ra St. Brown",team:"DET",opp:"DAL",prop:"Receptions",dir:"OVER",line:6.5,proj:7.4,edge:13.8,prob:64,tier:1,scheme:"ZONE",sigs:["Zone beater","DAL 77% zone","Slot 55.7%"]},
  {player:"Khalil Shakir",team:"BUF",opp:"MIA",prop:"Rec Yards",dir:"OVER",line:58.5,proj:63.9,edge:9.2,prob:58,tier:2,scheme:"SLOT",sigs:["Slot 68% rate","MIA 8.5 yds/tgt slot"]},
  {player:"Caleb Williams",team:"CHI",opp:"DET",prop:"Pass Attempts",dir:"OVER",line:37.5,proj:41.2,edge:9.9,prob:61,tier:2,scheme:"VOL",sigs:["CHI 6.5-pt dog","Must-score volume"]},
];
const PARLAYS=[
  {legs:["Rashee Rice: Rec Yards OVER 62.5","Caleb Williams: Pass Att OVER 37.5"],odds:"+170",prob:37,tier:1},
  {legs:["Rashee Rice: Rec OVER 5.5","Khalil Shakir: Rec Yards OVER 58.5"],odds:"+175",prob:36,tier:2},
  {legs:["Amon-Ra: Rec OVER 6.5","Rashee Rice: Rec Yards OVER 62.5","Williams: Pass Att OVER 37.5"],odds:"+285",prob:28,tier:2},
];
const COVERAGE=[
  {team:"LV",man:18.3,zone:81.7,vuln:"HIGH",dc:"Rob Leonard",chg:true,blitz:22},
  {team:"DAL",man:22.8,zone:77.2,vuln:"HIGH",dc:"Eberflus",chg:true,blitz:20},
  {team:"TB",man:25.7,zone:74.3,vuln:"HIGH",dc:"TBD",chg:true,blitz:20},
  {team:"MIA",man:25.8,zone:74.2,vuln:"MEDIUM",dc:"B. Duker",chg:true,blitz:20},
  {team:"GB",man:32.7,zone:67.3,vuln:"LOW",dc:"J. Gannon",chg:true,blitz:26},
  {team:"BUF",man:28.9,zone:71.1,vuln:"LOW",dc:"Jim Leonhard",chg:true,blitz:30},
  {team:"BAL",man:42.0,zone:58.0,vuln:"LOW",dc:"Minter/HC",chg:true,blitz:30},
  {team:"DET",man:38.2,zone:61.8,vuln:"LOW",dc:"K. Sheppard",chg:true,blitz:28},
  {team:"KC",man:28.4,zone:71.6,vuln:"LOW",dc:"Spagnuolo",chg:false,blitz:32},
  {team:"MIN",man:23.7,zone:76.3,vuln:"LOW",dc:"B. Flores",chg:false,blitz:30},
  {team:"CIN",man:32.5,zone:67.5,vuln:"MEDIUM",dc:"Anarumo",chg:false,blitz:24},
  {team:"PHI",man:37.4,zone:62.6,vuln:"LOW",dc:"C. Parker",chg:false,blitz:28},
];
const CFB_GAMES=[
  {id:1,away:"Auburn",home:"Alabama",conf:"SEC",time:"Sat 8pm ET",market:{spread:-14.5,total:51.0,fh:-7.5},models:{"SP+":-8.2,"FPI":-11.4,"Sagarin":-9.8,"Massey":-10.1,"Connelly":-9.3},sit:{nightGame:{label:"SEC night game",adj:1.5},rivalry:{label:"Iron Bowl tightens",adj:-1.5},form:{label:"Bama +2.1 form",adj:1.2},pace:{label:"68 vs 72 pl/g",adj:0.4}},eff:{homeOff:{label:"Bama Off SR",val:"48.2%",rank:3},homeDef:{label:"Bama Def SR",val:"28.1%",rank:2},awayOff:{label:"Auburn Off SR",val:"39.4%",rank:28},awayDef:{label:"Auburn Def SR",val:"35.7%",rank:19}},plays:[{bet:"Auburn ATS -14.5",type:"spread",tier:1,edge:5.2,prob:62},{bet:"UNDER 51.0",type:"total",tier:2,edge:3.1,prob:55}]},
  {id:2,away:"Tennessee",home:"Georgia",conf:"SEC",time:"Sat 3:30pm ET",market:{spread:-10.0,total:48.5,fh:-5.5},models:{"SP+":-7.1,"FPI":-8.8,"Sagarin":-7.9,"Massey":-8.4,"Connelly":-7.6},sit:{afternoon:{label:"Afternoon kickoff",adj:-0.3},rivalry:{label:"SEC East rivalry",adj:-0.8},form:{label:"Tennessee +1.4",adj:0.7},pace:{label:"TN 76 pl/g fast",adj:1.1}},eff:{homeOff:{label:"Georgia Off SR",val:"44.1%",rank:8},homeDef:{label:"Georgia Def SR",val:"30.4%",rank:5},awayOff:{label:"Tennessee Off SR",val:"46.8%",rank:6},awayDef:{label:"Tennessee Def SR",val:"33.2%",rank:14}},plays:[{bet:"Tennessee +10.0",type:"spread",tier:1,edge:2.4,prob:58},{bet:"OVER 48.5",type:"total",tier:1,edge:4.2,prob:63},{bet:"Tennessee +5.5 1H",type:"fh",tier:2,edge:1.8,prob:54}]},
  {id:3,away:"Ohio State",home:"Michigan",conf:"B1G",time:"Sat 12pm ET",market:{spread:7.0,total:44.5,fh:3.5},models:{"SP+":4.1,"FPI":5.8,"Sagarin":3.9,"Massey":4.7,"Connelly":4.4},sit:{noon:{label:"Noon kickoff road",adj:-0.8},rivalry:{label:"The Game tightens",adj:-2.0},form:{label:"Ohio St +1.8 form",adj:0.9},pace:{label:"Michigan 64 pl/g",adj:-0.6}},eff:{homeOff:{label:"Michigan Off SR",val:"41.2%",rank:18},homeDef:{label:"Michigan Def SR",val:"34.8%",rank:11},awayOff:{label:"Ohio St Off SR",val:"52.1%",rank:1},awayDef:{label:"Ohio St Def SR",val:"29.3%",rank:4}},plays:[{bet:"Ohio State -7.0",type:"spread",tier:1,edge:2.9,prob:60},{bet:"UNDER 44.5",type:"total",tier:2,edge:2.1,prob:54}]},
  {id:4,away:"Boise State",home:"UNLV",conf:"MWC",time:"Fri 10pm ET",market:{spread:-6.5,total:58.0,fh:-3.5},models:{"SP+":-9.8,"FPI":-8.2,"Sagarin":-10.1,"Massey":-9.4,"Connelly":-9.7},sit:{night:{label:"Friday night boost",adj:0.5},travel:{label:"Boise→LV altitude",adj:-0.3},pace:{label:"Both 74+ pl/g",adj:1.8},form:{label:"Boise +0.8 form",adj:0.4}},eff:{homeOff:{label:"UNLV Off SR",val:"43.1%",rank:12},homeDef:{label:"UNLV Def SR",val:"36.2%",rank:22},awayOff:{label:"Boise St Off SR",val:"47.8%",rank:5},awayDef:{label:"Boise St Def SR",val:"31.1%",rank:9}},plays:[{bet:"Boise State ATS -6.5",type:"spread",tier:1,edge:3.1,prob:61},{bet:"OVER 58.0",type:"total",tier:1,edge:5.8,prob:67},{bet:"Boise St -3.5 1H",type:"fh",tier:2,edge:2.1,prob:56}]},
];
const PWR=[
  {rank:1,team:"Georgia",conf:"SEC",sp:28.4,fpi:96.2,sagarin:88.1,connelly:29.1,composite:91,record:"10-0"},
  {rank:2,team:"Ohio State",conf:"B1G",sp:26.1,fpi:94.8,sagarin:86.4,connelly:27.3,composite:89,record:"9-1"},
  {rank:3,team:"Alabama",conf:"SEC",sp:24.8,fpi:93.1,sagarin:84.2,connelly:25.9,composite:87,record:"9-1"},
  {rank:4,team:"Oregon",conf:"B1G",sp:23.2,fpi:91.4,sagarin:82.8,connelly:24.1,composite:85,record:"10-0"},
  {rank:5,team:"Notre Dame",conf:"IND",sp:21.8,fpi:89.7,sagarin:81.3,connelly:22.4,composite:83,record:"9-1"},
  {rank:6,team:"Texas",conf:"SEC",sp:20.4,fpi:88.2,sagarin:79.6,connelly:21.0,composite:81,record:"8-2"},
  {rank:7,team:"Penn State",conf:"B1G",sp:19.1,fpi:86.8,sagarin:78.1,connelly:19.8,composite:79,record:"9-1"},
  {rank:8,team:"Boise State",conf:"MWC",sp:18.2,fpi:81.4,sagarin:74.9,connelly:18.8,composite:74,record:"10-0"},
  {rank:9,team:"Tennessee",conf:"SEC",sp:17.4,fpi:84.1,sagarin:76.8,connelly:17.9,composite:77,record:"8-2"},
  {rank:10,team:"SMU",conf:"ACC",sp:16.8,fpi:79.3,sagarin:72.4,connelly:17.1,composite:72,record:"9-1"},
  {rank:11,team:"Indiana",conf:"B1G",sp:15.9,fpi:78.1,sagarin:71.2,connelly:16.4,composite:71,record:"9-1"},
  {rank:12,team:"Clemson",conf:"ACC",sp:14.8,fpi:76.8,sagarin:70.1,connelly:15.2,composite:69,record:"8-2"},
  {rank:13,team:"Iowa State",conf:"B12",sp:14.1,fpi:75.4,sagarin:68.9,connelly:14.6,composite:68,record:"8-2"},
  {rank:14,team:"Arizona State",conf:"B12",sp:13.4,fpi:74.2,sagarin:67.8,connelly:13.8,composite:67,record:"8-2"},
  {rank:15,team:"UNLV",conf:"MWC",sp:12.8,fpi:69.1,sagarin:63.4,connelly:13.1,composite:63,record:"9-1"},
];
const SIT=[
  {factor:"SEC night games (home team)",adj:"+1.5 pts",n:48,hit:61,note:"Death Valley, Swamp, Bryant-Denny — crowd factor is real"},
  {factor:"Noon kickoff road team (east→west)",adj:"+1.2 pts",n:34,hit:59,note:"West coast teams traveling east for noon games undervalued"},
  {factor:"Rivalry game spread tightening",adj:"-1.8 pts",n:92,hit:63,note:"Rivals historically come within 1.8 pts of models"},
  {factor:"Altitude advantage (1500m+)",adj:"+0.8 pts",n:28,hit:54,note:"Colorado, BYU — affects opponents in first half"},
  {factor:"Back-to-back travel weeks",adj:"+1.4 pts",n:41,hit:58,note:"Third road game in four weeks = underdog fade"},
  {factor:"Fast pace vs slow defense (total)",adj:"+3.2 pts",n:67,hit:64,note:"75+ pl/game offense vs 68+ allowed D = over signal"},
  {factor:"G5 home vs P4 underdog",adj:"+2.1 pts",n:53,hit:57,note:"P4 teams underestimate G5 home environments"},
  {factor:"Early bye week advantage",adj:"+0.9 pts",n:39,hit:55,note:"Team coming off bye vs team on short week"},
  {factor:"High SR offense vs bad SR defense",adj:"+4.1 pts",n:78,hit:67,note:"SR >45% off vs SR-allowed >38% D = over signal"},
];

// ── Helpers ───────────────────────────────────────────────────────────────────
const vc=v=>v==="HIGH"?"ch":v==="MEDIUM"?"cm":"cl";
const vp=v=>v==="HIGH"?85:v==="MEDIUM"?50:20;
const vf=v=>v==="HIGH"?"#ff4757":v==="MEDIUM"?"#ffa502":"#00c896";
const sb2=s=>({ZONE:"sz",SLOT:"ss2",VOL:"sv2"})[s]||"";
const CC={SEC:"#ff4757",B1G:"#00e5ff",B12:"#f5c518",ACC:"#a855f7",MWC:"#ffa502",IND:"#00c896"};
const cc=c=>CC[c]||"#8888a8";
function cmp(m){const v=Object.values(m);const mean=v.reduce((a,b)=>a+b,0)/v.length;const vr=v.reduce((s,x)=>s+Math.pow(x-mean,2),0)/v.length;return{composite:parseFloat(mean.toFixed(1)),disagreement:parseFloat(Math.sqrt(vr).toFixed(2))};}
function evm(c,s){return parseFloat((s-c).toFixed(1));}

// ── Components ────────────────────────────────────────────────────────────────
function Gate({children,unlocked}){
  if(unlocked)return children;
  return(<div className="lock"><div className="lock-blur">{children}</div><div className="lock-gate"><div style={{fontSize:28}}>🔒</div><div className="lock-t">Members Only</div><div className="lock-s">Subscribe for full access to picks, model data, and parlays.</div><a href="https://gumroad.com" target="_blank" rel="noreferrer"><button className="bp">Get Access →</button></a></div></div>);
}
function Modal({onUnlock,onClose}){
  const[k,setK]=useState("");const[e,setE]=useState("");
  const go=()=>{if(k.trim().length>5)onUnlock();else setE("Invalid key. Check your Gumroad email.");};
  return(<div className="modal-bg" onClick={onClose}><div className="modal" onClick={ev=>ev.stopPropagation()}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:10,fontWeight:700,letterSpacing:".2em",textTransform:"uppercase",color:"#00e5ff",marginBottom:12}}>Member Access</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:800,textTransform:"uppercase",marginBottom:6}}>Enter License Key</div><div style={{fontSize:12,color:"#8888a8",marginBottom:18,lineHeight:1.6}}>Find your key in your Gumroad purchase email.</div><input className="ki" style={{marginBottom:10}} placeholder="XXXX-XXXX-XXXX-XXXX" value={k} onChange={ev=>setK(ev.target.value)} onKeyDown={ev=>ev.key==="Enter"&&go()}/>{e&&<div style={{fontSize:11,color:"#ff4757",marginBottom:10}}>{e}</div>}<div style={{display:"flex",gap:8}}><button className="bp" style={{flex:1}} onClick={go}>Unlock</button><button className="bs" onClick={onClose}>Cancel</button></div><div style={{marginTop:16,fontSize:11,color:"#8888a8",textAlign:"center"}}>No account? <a href="https://gumroad.com" target="_blank" rel="noreferrer" style={{color:"#00e5ff"}}>Subscribe on Gumroad →</a></div></div></div>);
}

function HomePage({setTab,setShow}){
  return(<div>
    <div className="hero">
      <div className="hre">Data-driven · Process-first · Results posted weekly</div>
      <div className="hrh">The picks sheet<br/>built by a<br/><span>data engineer</span></div>
      <div className="hrs">Model-driven NFL props and CFB spreads. Powered by PFF scheme splits, original efficiency ratings, and situational analysis. Not a tout. A process.</div>
      <div className="hrc"><button className="bp" onClick={()=>setShow(true)}>Get Member Access</button><button className="bs" onClick={()=>setTab("results")}>View Public Record</button></div>
    </div>
    <div style={{maxWidth:820,margin:"0 auto",padding:"0 16px 32px"}}>
      <div className="sl2">Season record</div>
      <div className="sg" style={{marginBottom:24}}>
        {[{l:"Overall",v:"—",s:"Season starts Week 1",c:"#8888a8"},{l:"Tier 1 ★★★",v:"—",s:"Awaiting results",c:"#8888a8"},{l:"Win rate",v:"—",s:"Check back Week 1",c:"#8888a8"},{l:"Net units",v:"—",s:"Updated Mondays",c:"#8888a8"}].map(s=>(<div className="sb" key={s.l}><div className="sl">{s.l}</div><div className="sv" style={{color:s.c}}>{s.v}</div><div className="ss">{s.s}</div></div>))}
      </div>
      <div className="sl2">What you get</div>
      <div className="feg">
        {[{i:"◈",t:"NFL Props",d:"Scheme-adjusted props with PFF coverage splits, man/zone edges, and confidence tiers."},{i:"◉",t:"CFB Spreads",d:"Original EI power rating + SP+ blend × pace × HFA × situational factors."},{i:"⊕",t:"Parlays",d:"2-3 leg combinations auto-built from top edges. Target +100 to +300."},{i:"◎",t:"EI Power Ratings",d:"Our original efficiency model. Pass ypp, success rate, EPA. No black boxes."},{i:"⊗",t:"Model Ratings",d:"PFF coverage profiles for all 32 NFL teams adjusted for 2026 DC changes."},{i:"◌",t:"Results",d:"Every play posted publicly. Wins and losses. No hiding bad weeks. Ever."}].map(f=>(<div className="feb" key={f.t}><div className="fei">{f.i}</div><div className="fet">{f.t}</div><div className="fed">{f.d}</div></div>))}
      </div>
      <div style={{background:"#1a1a26",border:"1px solid #2a2a3d",borderRadius:5,padding:"20px 24px",display:"flex",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:16}}>
        <div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800,textTransform:"uppercase",marginBottom:4}}>Ready for the 2026 season?</div><div style={{fontSize:12,color:"#8888a8"}}>NFL props Thursday · CFB plays Friday · Results every Monday</div></div>
        <div style={{display:"flex",gap:8}}><button className="bp" onClick={()=>setShow(true)}>$20/week</button><button className="bs" onClick={()=>setShow(true)}>$49/month</button></div>
      </div>
    </div>
  </div>);
}

function NFLPage({unlocked}){
  const[f,setF]=useState("ALL");
  const picks=NFL_PICKS.filter(p=>f==="ALL"||p.tier===Number(f));
  return(<div className="pg">
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:16,flexWrap:"wrap",gap:10}}>
      <div><div className="pg-title">NFL Props — Week 10</div><div className="pg-sub">PFF scheme splits · Coverage tendencies · Game script · 2026 DC adjustments</div></div>
      <div className="itabs">{["ALL","1","2"].map(v=>(<button key={v} className={`itab${f===v?" on":""}`} onClick={()=>setF(v)}>{v==="ALL"?"All":v==="1"?"★★★ T1":"★★ T2"}</button>))}</div>
    </div>
    <Gate unlocked={unlocked}>
      <div>{picks.map((p,i)=>(<div key={i} className={`pr t${p.tier}r`}><div>{p.tier===1?<span className="t1">★★★ T1</span>:<span className="t2">★★ T2</span>}<div style={{marginTop:6}}><span className={`sig ${sb2(p.scheme)}`}>{p.scheme}</span></div></div><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:16,fontWeight:700,marginBottom:2}}>{p.player}<span style={{fontWeight:400,color:"#8888a8",fontSize:13,marginLeft:6}}>{p.team} vs {p.opp}</span></div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:14,marginBottom:6}}>{p.prop} <span style={{color:"#00c896",fontWeight:700}}>{p.dir}</span>{" "}<span className="mono" style={{color:"#00e5ff"}}>{p.line}</span></div><div>{p.sigs.map((s,j)=><span className="sig" key={j}>{s}</span>)}</div></div><div style={{textAlign:"right"}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,fontWeight:800,color:p.tier===1?"#f5c518":"#00e5ff",lineHeight:1}}>{p.proj}</div><div style={{fontSize:10,color:"#8888a8",marginTop:2}}>proj</div></div><div style={{textAlign:"right",minWidth:68}}><div className="mono" style={{fontSize:13,color:"#00c896",fontWeight:500}}>+{p.edge}%</div><div style={{fontSize:10,color:"#8888a8"}}>edge</div><div className="mono" style={{fontSize:10,color:"#8888a8",marginTop:3}}>{p.prob}% prob</div></div></div>))}</div>
    </Gate>
  </div>);
}

function ParlaysPage({unlocked}){
  return(<div className="pg">
    <div className="pg-title">Parlay Builder — Week 10</div>
    <div className="pg-sub">2–3 legs · Target +100 to +300 · Correlated legs excluded automatically</div>
    <Gate unlocked={unlocked}>
      <div>{PARLAYS.map((p,i)=>(<div key={i} className="pc"><div style={{display:"flex",alignItems:"flex-start",justifyContent:"space-between",marginBottom:10}}><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:10,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8"}}>Parlay {i+1}</div><div className="po" style={{marginTop:4}}>{p.odds}</div></div><div style={{textAlign:"right"}}>{p.tier===1?<span className="t1">★★★ TIER 1</span>:<span className="t2">★★ TIER 2</span>}<div className="mono" style={{fontSize:11,color:"#8888a8",marginTop:5}}>{p.prob}% win prob</div></div></div><div style={{height:1,background:"#2a2a3d",marginBottom:10}}/>{p.legs.map((l,j)=><div key={j} className="pl">{l}</div>)}</div>))}</div>
    </Gate>
  </div>);
}

function ResultsPage(){
  return(<div className="pg">
    <div className="pg-title">Public Results Tracker</div>
    <div className="pg-sub">Every play posted. Wins and losses. No cherry-picking. Ever.</div>
    <div className="es"><div className="ei2">📋</div><div className="et">Season Hasn't Started Yet</div><div className="ed">Results will be posted here every Monday during the season. Every pick — wins and losses — tracked publicly. No hiding bad weeks.</div><div style={{marginTop:24,fontFamily:"'IBM Plex Mono',monospace",fontSize:11,color:"#4a4a6a"}}>First picks post · Week 1 · September 2026</div></div>
  </div>);
}

function ModelPage({unlocked}){
  const[it,setIt]=useState("coverage");
  return(<div className="pg">
    <div className="pg-title">NFL Model Ratings</div>
    <div className="pg-sub">PFF-powered team profiles · Adjusted for 2026 coordinator changes</div>
    <div className="itabs">{[{id:"coverage",l:"Coverage"},{id:"slot",l:"Slot Vuln"},{id:"dc",l:"DC Changes"}].map(t=>(<button key={t.id} className={`itab${it===t.id?" on":""}`} onClick={()=>setIt(t.id)}>{t.l}</button>))}</div>
    <Gate unlocked={unlocked}>
      {it==="coverage"&&(<div className="card"><div className="card-hdr">Defensive coverage tendencies — 2026 adjusted</div><table className="dt"><thead><tr><th>Team</th><th>Man%</th><th>Zone%</th><th>Slot</th><th>Blitz%</th><th>DC</th></tr></thead><tbody>{COVERAGE.map((c,i)=>(<tr key={i}><td style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700}}>{c.team}</td><td className="mono">{c.man}%</td><td className="mono">{c.zone}%</td><td><span className={vc(c.vuln)}>{c.vuln}</span></td><td className="mono">{c.blitz}%</td><td>{c.chg?<span className="dc-c">⚠ {c.dc}</span>:<span className="dc-r">✓ {c.dc}</span>}</td></tr>))}</tbody></table></div>)}
      {it==="slot"&&(<div className="card"><div className="card-hdr">Slot vulnerability</div>{[...COVERAGE].sort((a,b)=>vp(b.vuln)-vp(a.vuln)).map((c,i)=>(<div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"8px 0",borderBottom:"1px solid #2a2a3d66"}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700,minWidth:36}}>{c.team}</div><div style={{flex:1}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}><span className={vc(c.vuln)} style={{fontSize:12}}>{c.vuln}</span><span style={{fontSize:10,color:"#8888a8"}}>{c.chg?"⚠ Changed":"✓ Retained"}</span></div><div className="pt"><div className="pf" style={{width:`${vp(c.vuln)}%`,background:vf(c.vuln)}}/></div></div><div style={{fontSize:10,color:"#8888a8",minWidth:80,textAlign:"right"}}>{c.dc}</div></div>))}</div>)}
      {it==="dc"&&(<div><div style={{background:"#ffa50218",border:"1px solid #ffa50233",borderRadius:4,padding:"10px 14px",marginBottom:12,fontSize:12,color:"#ffa502"}}>14 teams have new DCs for 2026. Profiles blend DC historical tendencies with 2025 PFF data.</div><div className="card"><div className="card-hdr">2026 DC changes</div>{COVERAGE.filter(c=>c.chg).map((c,i)=>(<div key={i} style={{background:"#12121a",border:"1px solid #2a2a3d",borderRadius:4,padding:"12px 14px",marginBottom:8}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:16,fontWeight:700}}>{c.team} <span style={{fontWeight:400,color:"#8888a8",fontSize:13}}>{c.dc}</span></div><span className="dc-c">⚠ Changed</span></div><div style={{display:"flex",gap:16,fontSize:12,color:"#8888a8"}}><span>Man: <span style={{color:"#e8e8f0"}} className="mono">{c.man}%</span></span><span>Zone: <span style={{color:"#e8e8f0"}} className="mono">{c.zone}%</span></span><span>Blitz: <span style={{color:"#e8e8f0"}} className="mono">{c.blitz}%</span></span><span>Slot: <span className={vc(c.vuln)}>{c.vuln}</span></span></div></div>))}</div></div>)}
    </Gate>
  </div>);
}

function GameCard({game,betFilter}){
  const[ex,setEx]=useState(false);const[dt,setDt]=useState("models");
  const{composite,disagreement}=cmp(game.models);
  const se=evm(composite,game.market.spread);
  const fp=betFilter==="ALL"?game.plays:game.plays.filter(p=>p.type===betFilter);
  if(betFilter!=="ALL"&&fp.length===0)return null;
  const ec=Math.abs(se)>=5?"#f5c518":Math.abs(se)>=2.5?"#00c896":"#8888a8";
  const vals=Object.values(game.models);const rng=Math.abs(Math.max(...vals)-Math.min(...vals));
  return(<div className={`gc${ex?" ex":""}`}><div className="gh" onClick={()=>setEx(!ex)}><div><div className="at">{game.away}</div><div className="ht">{game.home}</div><div style={{display:"flex",gap:6,marginTop:4,alignItems:"center"}}><span className="cb" style={{color:cc(game.conf),borderColor:cc(game.conf)+"44",background:cc(game.conf)+"18"}}>{game.conf}</span><span className="mono" style={{fontSize:9,color:"#8888a8"}}>{game.time}</span></div></div><div className="eb" style={{background:Math.abs(se)>=3?ec+"18":"#12121a",border:`1px solid ${Math.abs(se)>=3?ec+"44":"#2a2a3d"}`}}><div className="ev" style={{color:ec}}>{se>0?"+":""}{se}</div><div className="el">pts edge</div></div><div className="bt-tags">{fp.slice(0,2).map((p,i)=>(<span key={i} className="bt" style={{color:p.tier===1?"#f5c518":"#00e5ff",borderColor:p.tier===1?"#f5c51844":"#00e5ff33",background:p.tier===1?"#f5c51818":"#00e5ff15"}}>{p.bet}</span>))}<span className="mono" style={{fontSize:9,color:"#4a4a6a"}}>{ex?"▲ collapse":"▼ expand"}</span></div></div>
  {ex&&(<div className="gb"><div className="itabs">{[{id:"models",l:"Models"},{id:"situation",l:"Situational"},{id:"efficiency",l:"Efficiency"},{id:"plays",l:"Plays"}].map(t=>(<button key={t.id} className={`itab${dt===t.id?" on":""}`} onClick={()=>setDt(t.id)}>{t.l}</button>))}</div>
  {dt==="models"&&(<div>{rng>=4&&<div className="df">⚡ Model disagreement {rng.toFixed(1)}pts — potential mispricing</div>}<div className="mg">{Object.entries(game.models).map(([n,v])=>{const d=v-composite;const o=Math.abs(d)>=2;return(<div className="mb" key={n} style={{borderColor:o?"#ffa50266":"#2a2a3d"}}><div className="mn">{n}</div><div className="ms" style={{color:v<0?"#00c896":"#ff4757"}}>{v>0?"+":""}{v}</div><div style={{fontSize:10,color:o?"#ffa502":"#8888a8"}}>{o?`${d>0?"+":""}${d.toFixed(1)} out`:"ok"}</div></div>);}}<div className="mb" style={{borderColor:"#00e5ff66"}}><div className="mn" style={{color:"#00e5ff"}}>Composite</div><div className="ms" style={{color:"#00e5ff"}}>{composite>0?"+":""}{composite}</div><div style={{fontSize:10,color:"#8888a8"}}>σ={disagreement}</div></div></div><div className="ab"><span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8",minWidth:80}}>Model agree</span><div className="at2"><div className="af" style={{width:`${Math.max(10,100-disagreement*20)}%`,background:disagreement<2?"#00c896":disagreement<3.5?"#ffa502":"#ff4757"}}/></div><span className="mono" style={{fontSize:10,color:"#8888a8",minWidth:50,textAlign:"right"}}>{disagreement<2?"HIGH":disagreement<3.5?"MED":"LOW"}</span></div><div style={{display:"flex",gap:10,alignItems:"center",padding:"10px 12px",background:"#12121a",borderRadius:4,border:"1px solid #2a2a3d"}}><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:3}}>Market</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800}}>{game.market.spread>0?"+":""}{game.market.spread}</div></div><div style={{fontSize:16,color:"#4a4a6a"}}>→</div><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:3}}>Composite</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800,color:"#00e5ff"}}>{composite>0?"+":""}{composite}</div></div><div style={{fontSize:16,color:"#4a4a6a"}}>→</div><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:3}}>Edge</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800,color:Math.abs(se)>=3?"#f5c518":"#00c896"}}>{se>0?"+":""}{se}pts</div></div>{Math.abs(se)>=3&&<div style={{marginLeft:"auto"}}><span className="t1">★★★ HIGH EDGE</span></div>}</div></div>)}
  {dt==="situation"&&(<div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:10,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:8}}>Adjustments</div><div style={{display:"flex",flexWrap:"wrap",marginBottom:10}}>{Object.values(game.sit).map((f,i)=><span key={i} className={`st ${f.adj>0.5?"sp":f.adj<-0.5?"sn":"su"}`}>{f.label} ({f.adj>0?"+":""}{f.adj})</span>)}</div><div className="fg">{Object.entries(game.eff).map(([k,ef])=>(<div className="fb2" key={k}><div className="fl2">{ef.label}</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:16,fontWeight:700,color:ef.rank<=10?"#00c896":ef.rank<=20?"#ffa502":"#ff4757"}}>{ef.val}</div><div style={{fontSize:9,color:"#8888a8"}}>#{ef.rank}</div><div className="pt" style={{marginTop:5}}><div className="pf" style={{width:`${Math.max(5,100-ef.rank*3)}%`,background:ef.rank<=10?"#00c896":ef.rank<=20?"#ffa502":"#ff4757"}}/></div></div>))}</div></div>)}
  {dt==="efficiency"&&(<div><div className="fg">{Object.entries(game.eff).map(([k,ef])=>(<div className="fb2" key={k}><div className="fl2">{ef.label}</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:16,fontWeight:700,color:ef.rank<=10?"#00c896":ef.rank<=20?"#ffa502":"#ff4757"}}>{ef.val}</div><div style={{fontSize:9,color:"#8888a8"}}>#{ef.rank}</div><div className="pt" style={{marginTop:5}}><div className="pf" style={{width:`${Math.max(5,100-ef.rank*3)}%`,background:ef.rank<=10?"#00c896":ef.rank<=20?"#ffa502":"#ff4757"}}/></div></div>))}</div><div style={{borderTop:"1px solid #2a2a3d",paddingTop:12,marginTop:4}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:10,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:10}}>Total analysis</div><div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8}}>{[{l:"Market total",v:game.market.total,c:"#e8e8f0"},{l:"First half",v:game.market.fh,c:"#8888a8"},{l:"Pace adj",v:parseFloat((game.market.total+(game.sit.pace?.adj||0)*1.2).toFixed(1)),c:"#00e5ff"}].map(s=>(<div key={s.l} style={{background:"#12121a",border:"1px solid #2a2a3d",borderRadius:4,padding:"10px 12px"}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8",marginBottom:4}}>{s.l}</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:20,fontWeight:800,color:s.c}}>{s.v}</div></div>))}</div></div></div>)}
  {dt==="plays"&&(<div>{game.plays.map((p,i)=>(<div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"8px 0",borderBottom:"1px solid #2a2a3d66"}}><div style={{display:"flex",alignItems:"center",gap:8}}>{p.tier===1?<span className="t1">★★★ T1</span>:<span className="t2">★★ T2</span>}<span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700}}>{p.bet}</span></div><div style={{display:"flex",gap:12}}><span className="mono" style={{fontSize:12,color:"#00c896"}}>+{p.edge}pts</span><span className="mono" style={{fontSize:11,color:"#8888a8"}}>{p.prob}% cover</span></div></div>))}</div>)}
  </div>)}
  </div>);
}

function CFBGamesPage(){
  const[conf,setConf]=useState("ALL");const[bet,setBet]=useState("ALL");
  const filtered=CFB_GAMES.filter(g=>conf==="ALL"||g.conf===conf);
  const t1c=CFB_GAMES.filter(g=>{const{composite}=cmp(g.models);return Math.abs(evm(composite,g.market.spread))>=3;}).length;
  return(<div className="pg"><div className="pg-title">CFB Game Analysis — Week 10</div><div className="pg-sub">SP+ · ESPN FPI · Sagarin · Massey · Connelly · EI Composite · Situational</div>
  <div className="sg">{[{l:"Games",v:CFB_GAMES.length,s:"This week",c:"#e8e8f0"},{l:"Tier 1 edges",v:t1c,s:"≥3pt model edge",c:"#f5c518"},{l:"Avg disagreement",v:"2.4σ",s:"Between models",c:"#ffa502"},{l:"High confidence",v:"4",s:"Models aligned",c:"#00c896"}].map(s=>(<div className="sb" key={s.l}><div className="sl">{s.l}</div><div className="sv" style={{color:s.c}}>{s.v}</div><div className="ss">{s.s}</div></div>))}</div>
  <div className="fr"><span className="fl">Conf:</span>{["ALL","SEC","B1G","B12","ACC","MWC","IND"].map(c=>(<button key={c} className={`fb${conf===c?" on":""}`} onClick={()=>setConf(c)}>{c}</button>))}<span className="fl" style={{marginLeft:8}}>Bet:</span>{[{id:"ALL",l:"All"},{id:"spread",l:"Spreads"},{id:"total",l:"Totals"},{id:"fh",l:"1st Half"}].map(b=>(<button key={b.id} className={`fb${bet===b.id?" on":""}`} onClick={()=>setBet(b.id)}>{b.l}</button>))}</div>
  <div style={{marginBottom:8,fontSize:11,color:"#8888a8"}}>Click any game to drill into model comparison, situational factors, and efficiency.</div>
  {filtered.map(g=><GameCard key={g.id} game={g} betFilter={bet}/>)}</div>);
}

function CFBRankingsPage(){
  const[sb,setSb]=useState("composite");const[conf,setConf]=useState("ALL");const[drill,setDrill]=useState(null);
  const sorted=[...PWR].filter(t=>conf==="ALL"||t.conf===conf).sort((a,b)=>b[sb]-a[sb]);
  const dd=drill?PWR.find(t=>t.team===drill):null;
  return(<div className="pg"><div className="pg-title">CFB Power Rankings</div><div className="pg-sub">SP+ · ESPN FPI · Sagarin · Connelly · EI Composite — All FBS</div>
  <div className="fr"><span className="fl">Sort:</span>{[{id:"composite",l:"Composite"},{id:"sp",l:"SP+"},{id:"fpi",l:"FPI"},{id:"sagarin",l:"Sagarin"},{id:"connelly",l:"Connelly"}].map(s=>(<button key={s.id} className={`fb${sb===s.id?" on":""}`} onClick={()=>setSb(s.id)}>{s.l}</button>))}<span className="fl" style={{marginLeft:8}}>Conf:</span>{["ALL","SEC","B1G","B12","ACC","MWC","IND"].map(c=>(<button key={c} className={`fb${conf===c?" on":""}`} onClick={()=>setConf(c)}>{c}</button>))}</div>
  {dd&&(<div className="card" style={{borderColor:cc(dd.conf)+"66",marginBottom:16}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:24,fontWeight:800}}>{dd.team}</div><div style={{display:"flex",gap:8,marginTop:4}}><span className="cb" style={{color:cc(dd.conf),borderColor:cc(dd.conf)+"44",background:cc(dd.conf)+"18"}}>{dd.conf}</span><span className="mono" style={{fontSize:11,color:"#8888a8"}}>{dd.record}</span></div></div><button className="fb" onClick={()=>setDrill(null)}>✕ Close</button></div><div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8}}>{[{l:"SP+",v:dd.sp,c:"#00c896"},{l:"ESPN FPI",v:dd.fpi,c:"#00e5ff"},{l:"Sagarin",v:dd.sagarin,c:"#ffa502"},{l:"Connelly",v:dd.connelly,c:"#a855f7"}].map(m=>(<div key={m.l} style={{background:"#12121a",border:"1px solid #2a2a3d",borderRadius:4,padding:"10px 12px"}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:4}}>{m.l}</div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:800,color:m.c}}>{m.v}</div></div>))}</div><div style={{marginTop:10}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".15em",textTransform:"uppercase",color:"#8888a8",marginBottom:6}}>Composite</div><div style={{display:"flex",alignItems:"center",gap:10}}><div className="at2" style={{flex:1,height:8}}><div className="af" style={{width:`${dd.composite}%`,background:cc(dd.conf)}}/></div><span className="mono" style={{fontSize:13,color:"#e8e8f0"}}>{dd.composite}/100</span></div></div></div>)}
  <div className="card"><div className="card-hdr">FBS Power Rankings — {conf==="ALL"?"All conferences":conf}</div><div style={{display:"grid",gridTemplateColumns:"28px 1fr 60px 60px 60px 60px 80px",gap:8,padding:"0 0 8px",borderBottom:"1px solid #2a2a3d"}}>{["#","Team","SP+","FPI","Sagarin","Connelly","Composite"].map(h=>(<div key={h} style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8",textAlign:h==="Team"?"left":"right"}}>{h}</div>))}</div>{sorted.map((t,i)=>(<div key={t.team} className="prow" onClick={()=>setDrill(drill===t.team?null:t.team)}><div className="mono" style={{fontSize:11,color:"#8888a8",textAlign:"center"}}>{i+1}</div><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700,color:drill===t.team?cc(t.conf):"#e8e8f0"}}>{t.team}</div><div style={{display:"flex",gap:6,marginTop:2}}><span className="mono" style={{fontSize:9,color:cc(t.conf)}}>{t.conf}</span><span className="mono" style={{fontSize:9,color:"#8888a8"}}>{t.record}</span></div></div><div className="mono" style={{fontSize:12,textAlign:"right",color:"#00c896"}}>{t.sp}</div><div className="mono" style={{fontSize:12,textAlign:"right",color:"#00e5ff"}}>{t.fpi}</div><div className="mono" style={{fontSize:12,textAlign:"right",color:"#ffa502"}}>{t.sagarin}</div><div className="mono" style={{fontSize:12,textAlign:"right",color:"#a855f7"}}>{t.connelly}</div><div style={{textAlign:"right"}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700}}>{t.composite}</div><div className="cpb"><div className="cpf" style={{width:`${t.composite}%`,background:cc(t.conf)}}/></div></div></div>))}</div></div>);
}

function CFBSituationalPage(){
  return(<div className="pg"><div className="pg-title">Situational Edge Database</div><div className="pg-sub">Historical factors not in power rankings — night games, travel, rivalry, pace matchups</div>
  <div className="sg">{[{l:"Tracked factors",v:9,c:"#e8e8f0"},{l:"Avg hit rate",v:"60%",c:"#00c896"},{l:"Best factor",v:"67%",c:"#f5c518"},{l:"Sample size",v:"480+",c:"#00e5ff"}].map(s=>(<div className="sb" key={s.l}><div className="sl">{s.l}</div><div className="sv" style={{color:s.c}}>{s.v}</div></div>))}</div>
  <div className="card"><div className="card-hdr">Situational factors — empirical adjustments</div>{SIT.map((e,i)=>(<div key={i} style={{padding:"12px 0",borderBottom:"1px solid #2a2a3d66"}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}><div><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:15,fontWeight:700,marginBottom:3}}>{e.factor}</div><div style={{fontSize:12,color:"#8888a8"}}>{e.note}</div></div><div style={{textAlign:"right",minWidth:80}}><div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:18,fontWeight:800,color:"#00c896"}}>{e.adj}</div><div className="mono" style={{fontSize:10,color:"#8888a8"}}>n={e.n}</div></div></div><div style={{display:"flex",alignItems:"center",gap:10}}><span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:9,fontWeight:700,letterSpacing:".12em",textTransform:"uppercase",color:"#8888a8",minWidth:56}}>Hit rate</span><div className="pt" style={{flex:1}}><div className="pf" style={{width:`${e.hit}%`,background:e.hit>=63?"#f5c518":e.hit>=58?"#00c896":"#ffa502"}}/></div><span className="mono" style={{fontSize:11,color:"#e8e8f0",minWidth:34}}>{e.hit}%</span>{e.hit>=63&&<span className="t1">★★★</span>}{e.hit>=58&&e.hit<63&&<span className="t2">★★</span>}</div></div>))}</div></div>);
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App(){
  const[tab,setTab]=useState("home");
  const[unlocked,setUnlocked]=useState(false);
  const[showM,setShowM]=useState(false);
  const NAV=[
    {id:"home",l:"Home"},
    {type:"div"},{type:"label",l:"NFL"},
    {id:"nfl",l:"Props"},{id:"parlays",l:"Parlays"},{id:"results",l:"Results"},{id:"model",l:"Model"},
    {type:"div"},{type:"label",l:"CFB"},
    {id:"cfb-games",l:"Game Analysis"},{id:"cfb-rankings",l:"Power Rankings"},{id:"cfb-sit",l:"Situational"},
  ];
  return(<>
    <style>{css}</style>
    <nav className="nav">
      <div className="nav-logo" onClick={()=>setTab("home")}>EDGE<span>INDEX</span></div>
      {NAV.map((t,i)=>{
        if(t.type==="div") return <div key={i} className="nav-div"/>;
        if(t.type==="label") return <span key={i} className="nav-sec">{t.l}</span>;
        return <div key={t.id} className={`nav-tab${tab===t.id?" on":""}`} onClick={()=>setTab(t.id)}>{t.l}</div>;
      })}
      <div className="nav-right">{unlocked?<span className="nav-badge">MEMBER</span>:<button className="btn-unlock" onClick={()=>setShowM(true)}>Unlock</button>}</div>
    </nav>
    {tab==="home"         &&<HomePage setTab={setTab} setShow={setShowM}/>}
    {tab==="nfl"          &&<NFLPage unlocked={unlocked}/>}
    {tab==="parlays"      &&<ParlaysPage unlocked={unlocked}/>}
    {tab==="results"      &&<ResultsPage/>}
    {tab==="model"        &&<ModelPage unlocked={unlocked}/>}
    {tab==="cfb-games"    &&<CFBGamesPage/>}
    {tab==="cfb-rankings" &&<CFBRankingsPage/>}
    {tab==="cfb-sit"      &&<CFBSituationalPage/>}
    {showM&&<Modal onUnlock={()=>{setUnlocked(true);setShowM(false);}} onClose={()=>setShowM(false)}/>}
  </>);
}
