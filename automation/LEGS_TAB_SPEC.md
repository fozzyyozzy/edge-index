# Legs tab + slip builder — spec for Claude Code (React, cfb-app/src)

New nav item **Legs** between Floor Lines and Props. Reads `public/data/nfl_legs_<slate>.json` (slate = tnf | sun | mnf; a
segmented control at the top switches files). Each player carries `prices: "real" | "estimated"` — show a small "est" tag on
estimated prices only; real DK prices are the default now that the fetch step exists. Match the existing dark UI, mono labels, and the row style of Floor Lines.

## Data shape (from pipeline/grade_legs.py)
The file only contains rungs graded C or better. Players on a hard hold (team change, blowout, <10 games) keep their 3 rungs
nearest the DK line, all graded F, with `held: true` — render those greyed with the reason.
    { meta: { season, week, slate, generated, grade_key, rules[] },
      players: [ { player, team, opp, game, market, main_line, main_odds, opp_d, own_vol, spread, games, last3[],
                   rungs: [ { rung, est_odds, implied_pct, l10, l15, clear_pct, grade, reasons[] } ] } ] }

## Layout
Left (≈65%): the table.  Right (≈35%, sticky): the slip.

### Header
One line, always visible, from `meta.grade_key`:
"Grade = how often this rung hits. It says nothing about whether the price is good."  Then the slate control and the
posted time (`meta.generated`).

### Filters (chips, like Floor Lines)
Grade ≥ [A+ | A | A− | B | C]  · Market [all | rec yds | rec | rush yds | rush att | pass yds | cmp | att] · Team · Game ·
☐ hide holds (F)  · Search player.
Default: Grade ≥ A−, hide holds OFF (holds are shown greyed with their reason — the reason is content).

### Row (collapsed) = one player/market at its **best graded rung** (highest rung with the best letter; ties → higher rung)
    [POS] Player  TEAM · market · game            Grade   Rung   Est price   L10 / L15   Last 3   Opp D · Vol   [+]
Grade pill colors: A+ / A / A− in the site's green range (three shades), B amber, C grey, D dark grey, F red outline.
If `reasons` non-empty, show the first as a muted subline (e.g. "blowout risk (fav by 12.5)", "team change (PHI->NE)").

### Row (expanded) = the ladder
Every rung as a compact table: Rung · Est price · Implied % · Clear % · L10 · L15 · Grade · Reasons.  The main line row is
marked "DK line". Tapping any rung's [+] adds THAT rung to the slip (so a user can take 60+ instead of 70+).
Under the ladder: last-3 results, `games` in sample, spread, and matchup tags spelled out ("Opp run D: SOFT").

### Slip (right panel)
- Legs list: player · rung · market · est price · grade · [x]. User can overtype est price with the real DK price.
- Live math (from the ladder engine, reimplemented in JS — formulas below): parlay decimal + American, **hit % = product of
  clear_pct/100**, breakeven % = 1/decimal, EV per unit = hit*(dec-1) - (1-hit).
- Rule checks, shown as warnings (never blocking except where noted):
  · "Same game: these legs rise and fall together" when two legs share `game`.
  · "This leg is already on Ticket N" when a saved ticket has the same player+market — BLOCK unless grade is A+, and
    even then allow at most one repeated A+ leg per ticket.
  · "3–4 legs" — warn under 3 or over 4.
  · "Price worse than −400" per leg.
  · Attempt props with F/blowout: allowed to add, shown red, warning text from `reasons`.
- Save ticket (name auto: SUN-1, SUN-2 …) → localStorage (try/catch). Saved tickets list under the slip with a "copy legs"
  button (plain text: "Player rung+ market @ price, …").
- Footer line: "Flat units. Card tickets are graded Tuesday; your saved slips are yours and are not graded."

### Formulas (JS)
    dec(o) = o < 0 ? 1 + 100/(-o) : 1 + o/100
    parlay_dec = Π dec(o_i);  american = parlay_dec >= 2 ? round((parlay_dec-1)*100) : round(-100/(parlay_dec-1))
    hit = Π (clear_pct_i/100);  breakeven = 1/parlay_dec;  ev = hit*(parlay_dec-1) - (1-hit)

### Record tab addition (small)
A "Grade receipts" table: for each week, A+ / A / A− / B legs that were on published cards — n, hit %, expected (avg clear %).
Source: `receipts/season_ledger.csv` once `grade` is added to card legs (build_card_json already has l10/l15; add letter).

## Out of scope for v1
Correlation math (just the warning), injury feed, live odds. Keep it static-JSON like the rest of the site.
