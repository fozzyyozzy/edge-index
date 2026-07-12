import { useState } from "react";

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", gold:"#f5c518", cyan:"#00e5ff",
  text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

const FAQS = [
  {
    category: "METHODOLOGY",
    color: "#00ff88",
    items: [
      {
        q: "What model do you use to generate picks?",
        a: "A 7-layer signal stack combining: (1) streak momentum from pybaseball game logs, (2) current form via MLB Stats API L14 batting average, (3) LHP/RHP platoon splits from Statcast p_throws data, (4) park factors across all 30 stadiums, (5) opposing lineup strikeout rate, (6) trade detection via daily 40-man roster diffs, and (7) xBA regression signals from Baseball Savant. Each layer contributes an additive probability adjustment. Every play shows its full signal stack in the dropdown.",
      },
      {
        q: "What were your coefficients on the regression analysis?",
        a: "The model uses a weighted signal stack rather than traditional OLS regression. Primary weights: L5 hit rate at 60% of base probability, L10 rate at 25%. Platoon splits apply a +/-8-15% multiplicative adjustment, park factors +/-3-5%, and xBA regression +/-2-8%. Slump detection is binary — players below .150 L14 with 10+ AB are excluded entirely from OVER plays. Tier thresholds: AUTO at model prob >= 88% with streak >= 7 and 100% L5; T1 at 75-87%; T2 at 65-74%.",
      },
      {
        q: "What is xBA and why does it matter?",
        a: "xBA (expected batting average) uses Statcast exit velocity and launch angle to calculate hit probability on each batted ball, independent of defense. If a player's xBA is .040 above their actual BA, they're hitting below their true skill — a positive regression signal shown as 'DUE UP' on the card. If actual BA exceeds xBA by .040+, they're getting lucky — shown as 'LUCKY', a caution flag.",
      },
      {
        q: "How does the fade model work?",
        a: "Players below .150 batting average over the last 14 days (minimum 10 AB) are excluded from OVER plays and added to the fade list. When books still price their hit OVER at -180 to -250, the UNDER becomes plus money (+100 to +175). The model hit 15-4 (78.9%) on fades in the first week of live operation — it's our biggest edge.",
      },
      {
        q: "Why 2-3 leg parlays instead of singles on juiced plays?",
        a: "For plays priced at -200 to -280, the juice consumes most of the edge on a straight single. Pairing two -220 plays produces roughly +120 to +140 odds at about 80% combined hit probability — better risk-adjusted return. The paired-by-juice system ensures no player appears in more than 2 parlays per slate, preventing cascade failures.",
      },
      {
        q: "How do you handle mid-season trades?",
        a: "The trade tracker pulls all 30 MLB 40-man rosters daily and diffs against the previous day. Any player changing teams is flagged immediately with a NEW TEAM indicator. This prevents using stale park factors or platoon data for a player now in a different division.",
      },
    ],
  },
  {
    category: "PERFORMANCE",
    color: "#f5c518",
    items: [
      {
        q: "What is your verified track record?",
        a: "Live MLB operations launched May 8, 2026. Through May 13: Singles 39-23 (62.9%) +$211, Fades 15-4 (78.9%) +$1,477, Parlays 5-12 +$344, Combined +$1,680 (+16.8 units) at $100/play flat betting. Profitable every single day across 6 days. Full day-by-day record is in the Record tab.",
      },
      {
        q: "Why do fades outperform singles?",
        a: "Sportsbooks adjust OVER pricing slowly on cold bats because their algorithms weight season-long reputation heavily. A player hitting .094 L14 priced at -200 OVER implies 67% probability — when true probability is closer to 35-45%. That mispricing creates plus money UNDER value. At +120 average odds you only need 45.5% to break even. The model hits 78.9%.",
      },
      {
        q: "What is your biggest known weakness?",
        a: "Three documented weaknesses: (1) Lineup confirmation — the model uses prop line availability as a proxy for starting status, but players can appear in markets while listed as bench. We are adding lineup verification. (2) Blowout risk — when a team falls behind 5+ runs early, starters get pulled with fewer AB. (3) 2026 Statcast data lag — pybaseball game logs are from 2025; current season bridges via MLB Stats API but lacks pitch-level granularity.",
      },
      {
        q: "How do you define a unit?",
        a: "1 unit = $100 at our standard flat-bet tracking rate. Quarter Kelly criterion sizing is recommended for actual bankroll management. AUTO tier singles: 1.0-1.5 units. T1 singles: 0.75-1.0 units. Parlays: 0.5 units. Fades: 0.5-1.0 units.",
      },
    ],
  },
  {
    category: "PRODUCT",
    color: "#00e5ff",
    items: [
      {
        q: "What is included in the free tier?",
        a: "One play per day — the model's highest-confidence FREE PICK, typically an AUTO tier play with significant plus money value or a strong cold streak fade. The free pick is posted by 9:00 AM ET and available at edge-index.com with no signup required.",
      },
      {
        q: "When are plays posted each day?",
        a: "By approximately 9:00 AM ET. The morning routine pulls live lines from DraftKings, FanDuel, and BetMGM, runs slump detection, platoon adjustments, xBA signals, and pitcher K analysis before publishing. Lines are real — directly from the books, not estimated.",
      },
      {
        q: "Do you cover NFL?",
        a: "NFL is in development. The model was backtested on 37,777 NFL prop plays with the AUTO tier hitting 97.2% on 6,799 plays. Full NFL launch is planned for September 2026 preseason. MLB is the current live product.",
      },
      {
        q: "How is this different from other pick services?",
        a: "Three things: (1) Full transparency — every play shows its signal stack, model probability, market implied probability, and edge calculation. No black box. (2) We track UNDERS alongside OVERs — the cold streak fade model is our biggest edge and most services ignore it entirely. (3) Discipline over volume — 2-3 leg SGPs on floor lines, not 8-leg parlays. Backtesting proves 2-3 leg correlated SGPs dramatically outperform 4+ leg parlays.",
      },
      {
        q: "Do you guarantee results?",
        a: "No. Edge Index provides sports analytics for entertainment and informational purposes only. This is not financial advice. Sports betting involves risk. The model identifies statistical edges — it does not predict individual outcomes with certainty. A 90% model probability means the play hits approximately 90% of the time over a large sample. Please gamble responsibly. Must be 21+. If you have a gambling problem call 1-800-GAMBLER.",
      },
    ],
  },
];

function FAQItem({ q, a, color }) {
  const [open, setOpen] = useState(false);
  return (
    <div onClick={() => setOpen(!open)}
      style={{background:open?"#ffffff08":"#0d1117",
        border:"1px solid "+(open?color+"40":"#ffffff0a"),
        borderRadius:8, marginBottom:6, cursor:"pointer",
        transition:"all 0.2s", overflow:"hidden"}}>
      <div style={{padding:"14px 18px",display:"flex",
        justifyContent:"space-between",alignItems:"center",gap:16}}>
        <div style={{fontSize:13,fontWeight:700,color:open?color:"#f0f0f0",
          fontFamily:"'Barlow Condensed',sans-serif",lineHeight:1.4,flex:1}}>{q}</div>
        <span style={{fontSize:20,color:open?color:"#555",flexShrink:0,
          transition:"transform 0.2s",
          display:"inline-block",
          transform:open?"rotate(45deg)":"none"}}>+</span>
      </div>
      {open && (
        <div style={{padding:"0 18px 16px",borderTop:"1px solid #ffffff08"}}>
          <div style={{fontSize:12,color:"#888",
            fontFamily:"'IBM Plex Mono',monospace",
            lineHeight:1.8,marginTop:12,paddingLeft:12,
            borderLeft:"2px solid "+color+"40"}}>{a}</div>
        </div>
      )}
    </div>
  );
}

export default function FAQ() {
  const [activeCategory, setActiveCategory] = useState("ALL");
  const categories = ["ALL", ...FAQS.map(f => f.category)];
  const filtered   = activeCategory === "ALL" ? FAQS : FAQS.filter(f => f.category === activeCategory);
  const totalQ     = FAQS.reduce((acc,f) => acc + f.items.length, 0);

  return (
    <div style={{background:"#060911",minHeight:"100vh",paddingBottom:80}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        *{box-sizing:border-box;}
      `}</style>

      <div style={{background:"#0a0f1a",borderBottom:"1px solid #ffffff0a",padding:"40px 24px 32px"}}>
        <div style={{maxWidth:860,margin:"0 auto"}}>
          <div style={{fontSize:11,color:"#555",letterSpacing:3,
            fontFamily:"'IBM Plex Mono',monospace",marginBottom:8}}>EDGE INDEX / FAQ</div>
          <div style={{fontSize:36,fontWeight:800,color:"#f0f0f0",
            fontFamily:"'Barlow Condensed',sans-serif",letterSpacing:1,marginBottom:8}}>
            FREQUENTLY ASKED QUESTIONS
          </div>
          <div style={{fontSize:12,color:"#555",
            fontFamily:"'IBM Plex Mono',monospace",marginBottom:24}}>
            {totalQ} questions covering methodology, performance, and product
          </div>
          <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
            {categories.map(cat => {
              const catData = FAQS.find(f => f.category === cat);
              const color   = catData ? catData.color : "#00ff88";
              const active  = activeCategory === cat;
              return (
                <button key={cat} onClick={() => setActiveCategory(cat)}
                  style={{padding:"6px 16px",borderRadius:4,border:"none",
                    background:active?color+"20":"#ffffff08",
                    color:active?color:"#555",
                    fontSize:10,fontWeight:700,cursor:"pointer",
                    fontFamily:"'IBM Plex Mono',monospace",letterSpacing:2,
                    outline:active?"1px solid "+color+"40":"none",
                    transition:"all 0.15s"}}>
                  {cat}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div style={{maxWidth:860,margin:"0 auto",padding:"32px 24px"}}>
        {filtered.map((section, si) => (
          <div key={si} style={{marginBottom:40}}>
            <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:16}}>
              <div style={{width:3,height:24,background:section.color,borderRadius:2}}/>
              <div style={{fontSize:11,fontWeight:800,color:section.color,
                fontFamily:"'IBM Plex Mono',monospace",letterSpacing:3}}>
                {section.category}
              </div>
              <div style={{fontSize:10,color:"#555",
                fontFamily:"'IBM Plex Mono',monospace"}}>
                {section.items.length} questions
              </div>
            </div>
            {section.items.map((item, ii) => (
              <FAQItem key={ii} q={item.q} a={item.a} color={section.color}/>
            ))}
          </div>
        ))}

        <div style={{marginTop:40,padding:"20px 24px",
          background:"#ffffff04",border:"1px solid #ffffff08",borderRadius:8}}>
          <div style={{fontSize:11,color:"#555",
            fontFamily:"'IBM Plex Mono',monospace",marginBottom:8}}>
            STILL HAVE QUESTIONS?
          </div>
          <div style={{fontSize:14,color:"#f0f0f0",
            fontFamily:"'Barlow Condensed',sans-serif",marginBottom:12}}>
            Reach out at picks@edge-index.com
          </div>
          <div style={{fontSize:9,color:"#444",
            fontFamily:"'IBM Plex Mono',monospace",lineHeight:1.6}}>
            Edge Index provides sports analytics for entertainment and informational purposes only.
            Not financial advice. Sports betting involves risk. Must be 21+.
            If you have a gambling problem call 1-800-GAMBLER.
          </div>
        </div>
      </div>
    </div>
  );
}
