import { useEffect, useState } from "react";
import { teamColor } from "./nflTeams";
import { SLATES, defaultSlate } from "./nflSlates";
import SlateSwitch from "./SlateSwitch";
// NFL Card — the plays. Reads /data/nfl_card_<slate>.json (automation/pipeline/build_card_json.py).

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", nfl:"#00e5ff", text:"#f0f0f0", muted:"#555",
  red:"#ff4757", amber:"#f5c518",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const SINGLE_GAME = new Set(["tnf", "mnf"]);
const MARKET_LABEL = { rec_yds:"rec yds", receptions:"rec", rush_yds:"rush yds", rush_att:"rush att",
  pass_yds:"pass yds", pass_cmps:"cmp", pass_att:"att" };

const oddsStr = o => o == null ? "—" : (o > 0 ? "+" : "") + o;
const rungStr = r => typeof r === "string" ? r : Number.isInteger(r) ? `${r}+` : `o${r}`;
const frac = (v, n) => `${Math.round(v * n)}/${n}`;
// last3 is a list; older cards stored "[np.int64(126), ...]" strings.
const last3Of = v => Array.isArray(v) ? v :
  (String(v || "").replace(/np\.\w+\(/g, "").match(/-?\d+(\.\d+)?/g) || []).map(Number);

// Older cards have no Reasons on held rows; rebuild them from the flags.
function heldReasons(h) {
  if (h.Reasons?.length) return h.Reasons;
  const r = [];
  if (h.TeamChange) r.push("team change");
  if (h.OppD === "TOUGH") r.push("opp D tough");
  if (h.OwnVol === "TOUGH") r.push("own volume low");
  return r;
}

function Tag({ label, v }) {
  // opp_d: SOFT = easy matchup. own_vol: SOFT = high volume, TOUGH = low volume.
  const good = v === "SOFT", bad = v === "TOUGH";
  const text = label === "VOL" ? (good ? "HIGH" : bad ? "LOW" : "—") : (good ? "SOFT" : bad ? "TOUGH" : "—");
  return (
    <span style={{fontSize:9,fontFamily:T.mono,color: good ? T.accent : bad ? T.red : "#444",whiteSpace:"nowrap"}}>
      <span style={{color:"#444"}}>{label} </span>{text}
    </span>
  );
}

const implied = o => o < 0 ? -o / (-o + 100) : 100 / (o + 100);
const when = iso => iso ? new Date(iso).toLocaleString(undefined, { weekday:"short", hour:"numeric", minute:"2-digit" }) : "—";

// Published price (locked) -> current price from the latest refresh. Green = the price shortened after we
// published (the market moved toward us); red = it drifted out.
function Price({ leg }) {
  const real = leg.published_odds != null || leg.odds_real != null;
  const pub = leg.published_odds ?? (leg.odds_real != null ? leg.odds_real : leg.odds_est);
  const cur = leg.current_odds;
  const moved = cur != null && cur !== pub;
  const toward = moved && implied(cur) > implied(pub);
  return (
    <span title={moved ? `published ${oddsStr(pub)} (${when(leg.published_at)}) → now ${oddsStr(cur)} (${when(leg.current_at)})`
                       : leg.current_at ? `unchanged since publish · checked ${when(leg.current_at)}` : ""}
      style={{fontSize:12,fontWeight:700,color:T.text,fontFamily:T.mono,whiteSpace:"nowrap"}}>
      {oddsStr(pub)}
      {!real && <sup style={{fontSize:7,color:T.amber,marginLeft:2,fontWeight:500}}>est</sup>}
      {moved && <>
        <span style={{color:"#555",fontWeight:400,margin:"0 4px"}}>→</span>
        <span style={{color: toward ? T.accent : T.red}}>{oddsStr(cur)}</span>
      </>}
    </span>
  );
}

function Leg({ l, last }) {
  const l3 = last3Of(l.last3);
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap",padding:"9px 12px 9px 10px",
      borderLeft:`3px solid ${teamColor(l.team)}`,borderBottom: last ? "none" : `1px solid ${T.border}`}}>
      <div style={{flex:"1 1 200px",minWidth:0}}>
        <div style={{display:"flex",alignItems:"baseline",gap:8,flexWrap:"wrap"}}>
          <a href={`#legs?player=${encodeURIComponent(l.player)}`} title="open this player's ladder in Legs"
            style={{fontSize:14,fontWeight:700,color:T.text,fontFamily:T.head,textDecoration:"none"}}>{l.player}</a>
          {l.star && <span title="floor star: L10 ≥ 9/10 and L15 ≥ 13/15 — may anchor two tickets"
            style={{fontSize:10,color:T.amber}}>★</span>}
          <span style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>{l.team} v {l.opp}</span>
        </div>
        <div style={{fontSize:11,fontFamily:T.mono,marginTop:2}}>
          <span style={{color:T.accent,fontWeight:700}}>{rungStr(l.rung)}</span>{" "}
          <span style={{color:"#999"}}>{MARKET_LABEL[l.market] || l.market}</span>
        </div>
      </div>
      <div style={{display:"flex",alignItems:"center",gap:14,flexWrap:"wrap",fontFamily:T.mono}}>
        <Price leg={l} />
        {l.l10 != null && <span style={{fontSize:10,color:"#999"}}>{frac(l.l10, 10)} <span style={{color:"#555"}}>{frac(l.l15, 15)}</span></span>}
        {l3.length > 0 && <span style={{fontSize:10,minWidth:66}}>
          {l3.map((v, i) => <span key={i} style={{color: v >= l.rung ? "#7fe0b0" : "#c96b74",marginRight:5}}>{Math.round(v)}</span>)}
        </span>}
        {l.opp_d != null && <span style={{display:"flex",gap:7}}><Tag label="D" v={l.opp_d} /><Tag label="VOL" v={l.own_vol} /></span>}
      </div>
    </div>
  );
}

// hand = a ticket published by hand before the automated card (nfl_handbuilt_<slate>.json): amber flag instead of the
// Bloom/Reduced label, no model hit (it has no pipeline numbers), payout as published.
function Ticket({ t, hand }) {
  const color = hand || t.reduced ? T.amber : T.accent;
  const payoutX = t.est_payout ?? (t.est_american != null ? (t.est_american > 0 ? 1 + t.est_american / 100 : 1 + 100 / -t.est_american) : null);
  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,marginBottom:14,overflow:"hidden"}}>
      <div style={{display:"flex",alignItems:"center",gap:14,flexWrap:"wrap",padding:"12px 14px",
        borderBottom:`1px solid ${T.border}`}}>
        <div style={{fontSize:18,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>{t.name}</div>
        <span style={{fontSize:9.5,fontFamily:T.mono,color,background:color + "14",border:`1px solid ${color}40`,
          borderRadius:3,padding:"3px 8px",lineHeight:1.4,letterSpacing: hand ? 1 : 0}}>{hand ? (t.flag || "hand-built").toUpperCase() : t.label}</span>
        {t.correlated && <span style={{fontSize:9,fontFamily:T.mono,color:"#888",border:"1px solid #ffffff18",
          borderRadius:3,padding:"3px 7px"}}>single game · legs correlated</span>}
        <span style={{flex:1}} />
        <div style={{display:"flex",gap:18,fontFamily:T.mono}}>
          <div style={{textAlign:"right"}}>
            <div style={{fontSize:20,fontWeight:800,color:T.nfl,letterSpacing:-0.5,lineHeight:1}}>{oddsStr(t.est_american)}</div>
            <div style={{fontSize:8,color:"#444",letterSpacing:1.5,marginTop:3}}>PAYOUT{payoutX != null ? ` · ${payoutX.toFixed(2)}x` : ""}</div>
          </div>
          {!hand && <div style={{textAlign:"right"}}>
            <div style={{fontSize:20,fontWeight:800,color:T.text,letterSpacing:-0.5,lineHeight:1}}>{(t.model_hit * 100).toFixed(1)}%</div>
            <div style={{fontSize:8,color:"#444",letterSpacing:1.5,marginTop:3}}>MODEL HIT</div>
          </div>}
        </div>
      </div>
      {hand && <div style={{fontSize:10,color:"#999",padding:"8px 14px",borderBottom:`1px solid ${T.border}`,lineHeight:1.6}}>
        Published in the newsletter before the automated card; graded Tuesday, excluded from grade stats.</div>}
      {t.legs.map((l, i) => <Leg key={`${l.player}|${l.market}`} l={l} last={i === t.legs.length - 1} />)}
    </div>
  );
}

function Label({ children }) {
  return <div style={{fontSize:9,color:"#444",letterSpacing:3,margin:"26px 0 10px"}}>{children}</div>;
}

export default function NFLHub() {
  const [files, setFiles] = useState(null);     // slate -> card | null
  const [hands, setHands] = useState({});       // slate -> hand-built tickets file | null
  const [slate, setSlate] = useState(null);

  useEffect(() => {
    const bust = `?t=${Date.now()}`;
    const get = name => fetch(`/data/${name}.json${bust}`).then(r => r.ok ? r.json() : null).catch(() => null);
    Promise.all(SLATES.flatMap(([s]) => [get(`nfl_card_${s}`), get(`nfl_handbuilt_${s}`)]))
      .then(all => {
        const fs = Object.fromEntries(SLATES.map(([s], i) => [s, all[2 * i]?.tickets ? all[2 * i] : null]));
        const hb = Object.fromEntries(SLATES.map(([s], i) => [s, all[2 * i + 1]?.tickets?.length ? all[2 * i + 1] : null]));
        setFiles(fs); setHands(hb);
        setSlate(defaultSlate(Object.fromEntries(SLATES.map(([s]) => [s, fs[s] || hb[s]]))));
      });
  }, []);

  const card = files && slate ? files[slate] : null;
  // a hand-built file only shows with the same week's card (or alone, before the card posts)
  const hand = slate && hands[slate] && (!card || hands[slate].week === card.week) ? hands[slate] : null;
  const available = files ? Object.fromEntries(SLATES.map(([s]) => [s, files[s] || hands[s]])) : null;
  const pulled = card?.prices_pulled ? new Date(card.prices_pulled).toLocaleString(undefined,
    { weekday:"short", month:"short", day:"numeric", hour:"numeric", minute:"2-digit" }) : null;

  return (
    <div style={{padding:"28px 16px 80px",maxWidth:1000,margin:"0 auto",fontFamily:T.mono}}>
      <div style={{display:"flex",alignItems:"baseline",gap:14,flexWrap:"wrap",marginBottom:4}}>
        <div style={{fontSize:22,fontWeight:800,color:T.text,fontFamily:T.head,letterSpacing:1}}>
          CARD{card || hand ? ` · WEEK ${(card || hand).week}` : ""}
        </div>
        <SlateSwitch files={available} slate={slate} onChange={setSlate} />
        <span style={{fontSize:9,fontWeight:700,color:T.amber,background:T.amber + "18",border:`1px solid ${T.amber}40`,
          borderRadius:3,padding:"3px 8px",letterSpacing:2}}>GRADED IN PUBLIC</span>
      </div>
      <div style={{fontSize:10,color:"#777",marginBottom:20,maxWidth:"72ch",lineHeight:1.6}}>
        Card tickets are graded Tuesday. Personal slips are not the card.
      </div>

      {!files && <div style={{fontSize:10,color:"#444"}}>loading…</div>}
      {hand && <>
        <Label>PUBLISHED IN THE NEWSLETTER · {hand.tickets.length}</Label>
        {hand.tickets.map(t => <Ticket key={t.name} t={t} hand />)}
      </>}

      {files && !card && (
        <div style={{fontSize:11,color:"#777",background:T.surface,border:`1px solid ${T.border}`,borderRadius:6,padding:16}}>
          {hand ? "No automated card posted for this slate yet." : "No card posted for this slate yet."}
        </div>
      )}

      {card && <>
        <Label>{hand ? "AUTOMATED TICKETS" : "TICKETS"} · {card.tickets.length}</Label>
        {card.tickets.some(t => t.legs.some(l => l.current_odds != null && l.current_odds !== l.published_odds)) && (
          <div style={{fontSize:9.5,color:"#555",margin:"-4px 0 10px"}}>
            Prices: published → current. <span style={{color:T.accent}}>Green</span> = shortened since we posted (the market
            moved toward the card); <span style={{color:T.red}}>red</span> = drifted out. Tickets never change after posting.
          </div>
        )}
        {card.tickets.length === 0 && <div style={{fontSize:10,color:"#555"}}>
          No ticket cleared the rules this slate — see what was held back below.</div>}
        {card.tickets.map(t => <Ticket key={t.name} t={t} />)}

        {SINGLE_GAME.has(slate) && card.floors_singles?.length > 0 && <>
          <Label>FLOORS AS SINGLES · {card.floors_singles.length}</Label>
          <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,overflow:"hidden"}}>
            {card.floors_singles.map((l, i) => <Leg key={`${l.player}|${l.market}`} l={l} last={i === card.floors_singles.length - 1} />)}
          </div>
        </>}

        {card.notes?.trim() && <>
          <Label>AUTHOR NOTES</Label>
          <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"12px 14px",
            fontSize:11,color:"#aaa",lineHeight:1.7,whiteSpace:"pre-wrap"}}>{card.notes.trim()}</div>
        </>}

        {card.held?.length > 0 && <>
          <Label>HELD BACK · {card.held.length}</Label>
          <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"2px 14px"}}>
            {card.held.map((h, i) => (
              <div key={`${h.Player}|${h.Market}`} style={{display:"flex",gap:10,flexWrap:"wrap",alignItems:"baseline",
                padding:"8px 0",fontSize:10,borderBottom: i < card.held.length - 1 ? `1px solid ${T.border}` : "none"}}>
                <span style={{color:"#999",fontWeight:700,minWidth:150}}>{h.Player}</span>
                <span style={{color:"#666",minWidth:130}}>
                  {h.Rung} {MARKET_LABEL[h.Market] || h.Market} · {oddsStr(h.EstOdds)}</span>
                <span style={{color:"#555",minWidth:70}}>{h.L10} {h.L15}</span>
                <span style={{color:"#c96b74",flex:"1 1 200px"}}>{heldReasons(h).join("; ")}</span>
              </div>
            ))}
          </div>
        </>}

        <div style={{marginTop:28,fontSize:10,color:"#555",fontStyle:"italic"}}>
          ({pulled ? `Prices as pulled ${pulled}` : "Prices as pulled — time not recorded"})
          {card.current_at && card.current_at !== card.prices_pulled && (
            <div style={{marginTop:4}}>(Current prices as of {new Date(card.current_at).toLocaleString(undefined,
              { weekday:"short", month:"short", day:"numeric", hour:"numeric", minute:"2-digit" })})</div>
          )}
        </div>
      </>}
    </div>
  );
}
