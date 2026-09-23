import { useState, useEffect } from "react";

/* ============================================================
   K BOARD — pitcher strikeout props, graded in public. The tiles
   show the live record (record.json); the heading makes no claim.
   Data: fetched at runtime from /data/daily_card.json and
   /data/record.json (written by the morning routine).
   ============================================================ */

const C = {
  bg: "#060911", panel: "#0a0f1a", border: "#ffffff0f",
  text: "#e8eaf0", muted: "#7a8494", gold: "#f5c518",
  green: "#00ff88", red: "#ff4d5a", cyan: "#00e5ff",
};

const impliedProb = odds => odds < 0 ? -odds / (-odds + 100) : 100 / (odds + 100);
const fairAmerican = p => p >= 0.5 ? Math.round(-100 * p / (1 - p)) : Math.round(100 * (1 - p) / p);
const evPerUnit = (p, odds) => {
  const dec = odds < 0 ? 1 + 100 / -odds : 1 + odds / 100;
  return p * (dec - 1) - (1 - p);
};
const fmtOdds = o => (o > 0 ? `+${o}` : `${o}`);
const unitsFromPlay = pl => {
  if (pl.hit === null || pl.hit === undefined) return 0;
  if (pl.hit === true) return pl.odds < 0 ? 100 / -pl.odds : pl.odds / 100;
  return -1;
};
const isKProp = prop => /k\b|strikeout/i.test(prop || "");

function recordSummary(days, filter) {
  let w = 0, l = 0, p = 0, units = 0, n = 0;
  for (const d of days || []) {
    for (const pl of d.plays || []) {
      if (filter && !filter(pl)) continue;
      if (pl.hit === true) w++; else if (pl.hit === false) l++; else p++;
      units += unitsFromPlay(pl);
      if (pl.hit !== null && pl.hit !== undefined) n++;
    }
  }
  return { w, l, p, units, roi: n ? (units / n) * 100 : 0, n };
}

const Stat = ({ label, value, color }) => (
  <div style={{ textAlign: "center", padding: "0 18px" }}>
    <div style={{ fontSize: 10, color: C.muted, letterSpacing: 1.5, textTransform: "uppercase" }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 800, color: color || C.text, marginTop: 2 }}>{value}</div>
  </div>
);

const TierBadge = ({ tier }) => (
  <span style={{
    fontSize: 9, fontWeight: 900, letterSpacing: 1, padding: "3px 8px", borderRadius: 4,
    background: tier === "AUTO" ? "#00ff8822" : "#f5c51822",
    color: tier === "AUTO" ? C.green : C.gold,
    border: `1px solid ${tier === "AUTO" ? C.green : C.gold}44`,
  }}>{tier}</span>
);

export default function KBoard() {
  const [card, setCard] = useState(null);
  const [record, setRecord] = useState(null);
  const [lineShop, setLineShop] = useState(null);
  const [showResearch, setShowResearch] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const bust = `?t=${Date.now()}`;
    fetch(`/data/daily_card.json${bust}`).then(r => r.ok ? r.json() : null)
      .then(setCard).catch(() => setErr("card"));
    fetch(`/data/record.json${bust}`).then(r => r.ok ? r.json() : null)
      .then(setRecord).catch(() => {});
    fetch(`/data/line_shop.json${bust}`).then(r => r.ok ? r.json() : null)
      .then(setLineShop).catch(() => {});
  }, []);

  const kPlays = (card?.pitcher_plays || []).filter(
    p => (p.prop === "strikeouts" || isKProp(p.prop)) && ["AUTO", "T1"].includes(p.tier));
  const research = (card?.batter_plays || []);

  const all = record ? recordSummary(record.results) : null;
  const kOnly = record ? recordSummary(record.results, pl => isKProp(pl.prop)) : null;

  const shopFor = name => {
    if (!lineShop?.pitchers) return null;
    return lineShop.pitchers.find(x => x.pitcher?.toLowerCase() === name?.toLowerCase());
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px", color: C.text }}>

      {/* Hero */}
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <div style={{ fontSize: 26, fontWeight: 900, letterSpacing: 3 }}>
          <span style={{ color: C.gold }}>K</span> BOARD
        </div>
        <div style={{ fontSize: 11, color: C.muted, letterSpacing: 1.5, marginTop: 4 }}>
          PITCHER STRIKEOUT PROPS · GRADED IN PUBLIC
        </div>
      </div>

      {/* Honest record banner */}
      {all && kOnly && (
        <div style={{
          display: "flex", justifyContent: "center", flexWrap: "wrap", gap: 8,
          background: C.panel, border: `1px solid ${C.border}`, borderRadius: 10,
          padding: "14px 8px", marginBottom: 20,
        }}>
          <Stat label="K Props Record" value={`${kOnly.w}-${kOnly.l}${kOnly.p ? `-${kOnly.p}` : ""}`} color={C.gold} />
          <Stat label="K Props Units" value={`${kOnly.units >= 0 ? "+" : ""}${kOnly.units.toFixed(1)}u`}
            color={kOnly.units >= 0 ? C.green : C.red} />
          <Stat label="K Props ROI" value={`${kOnly.roi >= 0 ? "+" : ""}${kOnly.roi.toFixed(1)}%`}
            color={kOnly.roi >= 0 ? C.green : C.red} />
          <div style={{ width: 1, background: C.border, margin: "0 6px" }} />
          <Stat label="All Props (honesty)" value={`${all.w}-${all.l}-${all.p}`} />
          <Stat label="All Props Units" value={`${all.units >= 0 ? "+" : ""}${all.units.toFixed(1)}u`}
            color={all.units >= 0 ? C.green : C.red} />
        </div>
      )}

      {/* Today's card */}
      <div style={{ fontSize: 12, color: C.muted, letterSpacing: 2, margin: "6px 2px" }}>
        TODAY'S CARD {card?.date ? `— ${card.date}` : ""}
      </div>

      {!card && !err && <div style={{ color: C.muted, padding: 30, textAlign: "center" }}>loading…</div>}
      {(err === "card" || (card && kPlays.length === 0)) && (
        <div style={{
          background: C.panel, border: `1px solid ${C.border}`, borderRadius: 10,
          padding: 30, textAlign: "center", color: C.muted, fontSize: 13, lineHeight: 1.8,
        }}>
          No qualifying K plays posted{card?.date ? ` for ${card.date}` : " yet"}.<br />
          <span style={{ color: C.green }}>“No play” days are proof the model isn't a volume mill.</span>
        </div>
      )}

      {kPlays.map((p, i) => {
        const imp = impliedProb(p.odds);
        const edge = p.model_prob - imp;
        const ev = evPerUnit(p.model_prob, p.odds);
        const shop = shopFor(p.pitcher || p.player);
        return (
          <div key={i} style={{
            background: C.panel, border: `1px solid ${edge > 0.04 ? C.green + "33" : C.border}`,
            borderRadius: 10, padding: "14px 16px", marginBottom: 10,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <TierBadge tier={p.tier} />
              <span style={{ fontWeight: 800, fontSize: 15 }}>{p.pitcher || p.player}</span>
              <span style={{ color: C.muted, fontSize: 12 }}>vs {p.opp}</span>
              <span style={{ marginLeft: "auto", fontWeight: 800, color: C.gold, fontSize: 15 }}>
                O {p.line} Ks <span style={{ color: C.text }}>{fmtOdds(p.odds)}</span>
              </span>
            </div>
            <div style={{
              display: "flex", gap: 18, marginTop: 10, fontSize: 11.5,
              color: C.muted, flexWrap: "wrap",
            }}>
              <span>model <b style={{ color: C.text }}>{(p.model_prob * 100).toFixed(0)}%</b></span>
              <span>book implied <b style={{ color: C.text }}>{(imp * 100).toFixed(0)}%</b></span>
              <span>edge <b style={{ color: edge > 0 ? C.green : C.red }}>
                {edge > 0 ? "+" : ""}{(edge * 100).toFixed(1)} pts</b></span>
              <span>fair <b style={{ color: C.text }}>{fmtOdds(fairAmerican(p.model_prob))}</b></span>
              <span>EV <b style={{ color: ev > 0 ? C.green : C.red }}>
                {ev > 0 ? "+" : ""}{(ev * 100).toFixed(1)}%</b></span>
              {p.l5_avg ? <span>L5 avg <b style={{ color: C.text }}>{p.l5_avg} Ks</b></span> : null}
            </div>
            {shop && shop.books?.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 11, color: C.muted }}>
                <span style={{ color: C.cyan, letterSpacing: 1 }}>LINE SHOP </span>
                {shop.books.map((b, j) => (
                  <span key={j} style={{
                    marginRight: 10,
                    color: b.best ? C.green : C.muted, fontWeight: b.best ? 800 : 400,
                  }}>{b.book} {b.line} {fmtOdds(b.over)}</span>
                ))}
              </div>
            )}
            {p.notes?.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 11, color: C.muted, fontStyle: "italic" }}>
                {p.notes.slice(0, 3).join(" · ")}
              </div>
            )}
          </div>
        );
      })}

      {/* Demoted research section — per the audit, hits props lost money */}
      {research.length > 0 && (
        <div style={{ marginTop: 26 }}>
          <button onClick={() => setShowResearch(!showResearch)} style={{
            background: "none", border: `1px solid ${C.border}`, color: C.muted,
            borderRadius: 6, padding: "6px 12px", fontSize: 11, cursor: "pointer",
            fontFamily: "inherit", letterSpacing: 1,
          }}>
            {showResearch ? "▾" : "▸"} RESEARCH — batter props (NOT on card; hits props ran −ROI in our audit)
          </button>
          {showResearch && research.map((b, i) => (
            <div key={i} style={{
              background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8,
              padding: "8px 14px", marginTop: 6, fontSize: 12, color: C.muted,
              display: "flex", gap: 12, flexWrap: "wrap",
            }}>
              <span style={{ color: C.text }}>{b.batter || b.player}</span>
              <span>{b.prop} {b.line}</span>
              <span>{fmtOdds(b.odds)}</span>
              <span>model {(b.model_prob * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 30, fontSize: 10.5, color: C.muted, textAlign: "center", lineHeight: 1.7 }}>
        Max 2-3 plays. Flat 1u. Every play graded next morning — full history in the Record tab.<br />
        Model probabilities vs your book's price; bet only when the edge is real. Not financial advice.
      </div>
    </div>
  );
}
