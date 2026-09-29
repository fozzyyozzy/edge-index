import { useState } from "react";

const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", gold:"#f5c518", cyan:"#00e5ff",
  text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

// Answers may be JSX so they can link. stopPropagation keeps the click from also collapsing the answer.
function Link({ href, children }) {
  const external = href.startsWith("http");
  return (
    <a href={href} onClick={e => e.stopPropagation()} {...(external ? { target:"_blank", rel:"noopener noreferrer" } : {})}
      style={{color:"#00e5ff",textDecoration:"none",borderBottom:"1px dotted #00e5ff80"}}>{children}</a>
  );
}
const RecordLink = () => <Link href="#record">Record tab</Link>;

const FAQS = [
  {
    category: "METHODOLOGY",
    color: "#00ff88",
    items: [
      {
        q: "How is the card built?",
        a: "From DraftKings alternate ladders. For every player with a DK line on the slate, the floor rung is the highest rung he cleared in at least 8 of his last 10 games and 11 of his last 15. Floors then pass gates: no tough opposing defense or low team volume, no team change this season, no attempt props when his team is favored by 7+, no price worse than −450, and at least +2 points of edge at DK's price. Tickets are 3–4 legs (2 allowed on a single-game Thursday or Monday slate), aiming for +200 by adding a fourth floor leg, never by stepping a rung up.",
      },
      {
        q: "What does a leg's grade mean?",
        a: "Grade = our estimated hit probability after blending with DK's price. Edge is shown separately. A+ is 85% and up, A 80%, A− 75%, B 68%, C 60%; form, price, matchup and new target competition move a grade one step. F is a hard hold (team change, likely blowout on an attempt prop, or fewer than 10 games).",
      },
      {
        q: "How is the probability estimated?",
        a: "Take the player's clear rate at that rung over his last 10 and last 15 games, smoothed as (hits + 1) / (games + 2), and use the lower of the two. Then blend it toward DK's no-vig price as if the market were 10 more games, and cap it at 90%. The fair price is the odds that probability implies; edge is our probability minus the one DK's price implies.",
      },
      {
        q: "Why parlays of short-priced legs?",
        a: "Floor legs are priced heavily (often −200 to −450), so a single returns little. Three or four of them from different games make a ticket near +200. No player appears on more than one ticket, except a floor star (9 of his last 10 and 13 of his last 15) on at most two.",
      },
    ],
  },
  {
    category: "PERFORMANCE",
    color: "#f5c518",
    items: [
      {
        q: "Where is the track record?",
        a: <>Every card ticket as published, graded each Tuesday against nflverse box scores, is on the <RecordLink />. Tickets are graded as settled at DraftKings, where Early Exit protection applies. Tickets published by hand before the pipeline existed are flagged and left out of the grade statistics.</>,
      },
      {
        q: "What is CLV?",
        a: "Closing line value: the price each leg was published at against the last price pulled before its game kicked off, in implied-probability points. Positive means the market moved toward the card after it posted. Published prices are locked; the Card tab shows published → current.",
      },
      {
        q: "What are the known weaknesses?",
        a: "Samples are small: a season is a few dozen tickets. DK posts alternate ladders one-sided, so the no-vig price uses the hold on the player's main line, which understates the hold on alt rungs. Clear rates look back 10–15 games, so a role change shows up late; the target-competition rule catches only new teammates with 8+ targets.",
      },
      {
        q: "How do you define a unit?",
        a: "Flat: every card ticket is 1 unit.",
      },
    ],
  },
  {
    category: "PRODUCT",
    color: "#00e5ff",
    items: [
      {
        q: "When is the card posted?",
        a: <>Wednesday (Thursday game), Friday (Sunday slate) and Monday (Monday game), and receipts grading every card leg post Tuesday, at <Link href="https://fozzyyozzy.substack.com">fozzyyozzy.substack.com</Link>. Prices on the site refresh through the week until each game kicks off.</>,
      },
      {
        q: "How is this different from other pick services?",
        a: "Every leg shows its rung, DK's price, our fair price, the edge, its grade, its last 10/15 clear rates and its matchup tags. Every ticket is graded in public, misses included, and nothing is removed after it posts.",
      },
      {
        q: "Do you guarantee results?",
        a: <>No. Edge Index provides sports analytics for entertainment and informational purposes only. This is not financial advice. Sports betting involves risk. A stated probability is an estimate; the <RecordLink /> shows how each grade has actually hit. Please gamble responsibly. Must be 21+. If you have a gambling problem call 1-800-GAMBLER.</>,
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
