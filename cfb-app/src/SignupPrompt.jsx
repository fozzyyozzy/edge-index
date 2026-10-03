import { useEffect, useState } from "react";

// Small, dismissible newsletter prompt (bottom corner). Shown to a visitor until they close it or click Subscribe;
// either is remembered in localStorage, so it never comes back. Storage can be blocked (private mode, site data
// cleared): then it simply shows again next visit — never an error.
const KEY = "ei_signup_prompt";
const URL = "https://theedgeindex.substack.com/subscribe";
const DELAY_MS = 6000;   // let the card load and be read first

const read = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
const remember = v => { try { localStorage.setItem(KEY, v); } catch { /* storage blocked: nothing to remember */ } };

export default function SignupPrompt() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (read()) return;
    const t = setTimeout(() => setOpen(true), DELAY_MS);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = e => { if (e.key === "Escape") close("dismissed"); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const close = why => { remember(why); setOpen(false); };
  if (!open) return null;

  return (
    <aside className="signup-prompt" aria-label="Newsletter signup"
      style={{ position:"fixed", right:16, bottom:16, zIndex:200, width:300, maxWidth:"calc(100vw - 32px)",
        background:"#0d1117", border:"1px solid #00ff8833", borderLeft:"3px solid #00ff88", borderRadius:8,
        padding:"14px 16px 14px 14px", boxShadow:"0 8px 30px #00000080", fontFamily:"'IBM Plex Mono',monospace",
        animation:"signup-in .25s ease-out" }}>
      <button onClick={() => close("dismissed")} aria-label="Close"
        style={{ position:"absolute", top:6, right:8, background:"transparent", border:"none", color:"#666",
          fontSize:16, lineHeight:1, cursor:"pointer", padding:4 }}>×</button>
      <div style={{ fontSize:10, color:"#00e5ff", letterSpacing:2, fontWeight:700 }}>THE CARD, BY EMAIL</div>
      <div style={{ fontSize:12.5, color:"#f0f0f0", margin:"6px 18px 10px 0", lineHeight:1.45 }}>
        Each slate's card in your inbox before kickoff, and Tuesday receipts on every ticket, wins and losses.
      </div>
      <a href={URL} target="_blank" rel="noopener noreferrer" onClick={() => close("subscribed")}
        style={{ display:"inline-block", background:"#00ff88", color:"#060911", fontSize:11, fontWeight:800,
          letterSpacing:1, padding:"7px 12px", borderRadius:4, textDecoration:"none" }}>SUBSCRIBE, IT'S FREE</a>
      <style>{`
        @keyframes signup-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
        @media (prefers-reduced-motion: reduce) { .signup-prompt { animation:none !important; } }
      `}</style>
    </aside>
  );
}
