# Edge Index v2 — Audit Findings & Season Roadmap
*July 8, 2026 — prepared for the 2026 NFL/CFB season and beyond*

## 1. What the audit found (the uncomfortable truths)

**MLB (live record, May 7 – Jul 7, 2026).** Your real graded record is 681-475-170 — a 58.9% hit rate that *lost 62.5 units (-5.4% ROI)*. The hits props are the leak: 60% hit rate at an average price of -174 needs 63.5% to break even, and volume ran ~24 plays/day. The one genuinely profitable market is **pitcher strikeouts: +6.6% ROI over 120 plays at avg -93**. That is a plausible real edge — K props are a known soft market and your Savant-based inputs are the right ones.

**NFL v1 backtest.** The 97% AUTO-tier hit rate was circular: lines were reconstructed as the player's rolling 6-game average, then tiers selected players by their hit rate against that same number. Your own bet slips in `line_estimator.py` show what books actually do — shade the line down and charge -200 to -436. The +15% ROI never existed.

**The buried treasure.** `prop_lines` contains ~458,000 REAL DraftKings/FanDuel/BetMGM lines for 2024–2025, both sides quoted. You do not need to buy historical NFL odds — you already collected them. Caveat: the 2025 rows are contaminated with live in-game snapshots (e.g., Tyreek Hill rec yds 4.5 at -110), so only 2024 is trustworthy.

**The honest v2 baseline.** A leak-free walk-forward model (exp-weighted player baseline, defense adjustment, shrinkage, de-vigged market comparison) run against clean 2024 closing lines is well-calibrated (predicted probs match observed frequencies across every bucket) but produces **-2% to -4% ROI**. That is what closing prop markets are: efficient. Anyone selling "model beats the close" is selling the leak you just fixed.

## 2. Where real, harvestable edges actually live

The model's job is to be a fair-value ruler; the profit comes from where you apply it. Line shopping alone is worth 2-4% — the same prop is regularly priced 15-25 cents apart across DK/FD/MGM, and betting the best price against consensus fair value flips a -2% bettor to roughly breakeven-plus. Timing is the second edge: lines move all week on injury news, weather, and steam; a Tuesday bet graded against the closing number (CLV) is the leading indicator of long-term profit, and the tracker now measures it on every play. Niche and derivative markets are third — pitcher K's (already proven in your own record), alt lines where books lag the mainline move, and low-liquidity CFB spreads, which is why CFBD's free real closing lines make CFB your best model-driven market. Finally, discipline is an edge over the subscriber's alternative: 2-3 plays max, flat 1u or quarter-Kelly, every play graded publicly.

## 3. What was built this session (`engine/`)

| Module | Purpose |
|---|---|
| `engine/core/odds.py` | One source of truth: de-vig, EV, fractional Kelly (capped 2%), parlay math |
| `engine/nfl/props_engine.py` | Leak-free projections: exp-weighted baseline x shrunk defense factor -> P(over) |
| `engine/nfl/backtest.py` | Walk-forward vs real 2024-25 lines, live-snapshot filters, threshold sweep, calibration report |
| `engine/parlay.py` | 2-3 leg hard cap, negative-correlation blocker, EV-ranked; `daily_card()` = max 3 singles + 2 parlays |
| `engine/core/tracking.py` | Unified all-sport plays DB: posted price, closing line, result, ROI + CLV reports |
| `engine/cfb/spreads_backtest.py` | Margin-capped Elo walk-forward vs real CFBD closing spreads (needs free `CFBD_API_KEY`) |

All odds/parlay/tracking math is unit-tested; the NFL backtest ran end-to-end on your database; the CFB harness passed a synthetic-data smoke test.

## 4. Season plan

**Now (July).** Start the timestamped line collector for NFL/MLB: pull odds 2-3x daily *with pull time and kickoff time stored*, never during games. This builds the clean 2026 dataset that 2025 should have been, and feeds CLV grading. Fix MLB per the audit: drop hits props (or require better than -130), keep the K model, cap the card at 2-3 plays via `daily_card()`.

**August — CFB verdict (negative result, and it's final enough to act on).** Four seasons of real CFBD lines, graded vs both openers and closers, with and without SP+ preseason priors: every configuration is -1% to -6% ROI. The carry-only Elo showed +1-4% vs openers in 2022-2024, but it did not survive 2025 (-8.8%) or the SP+ variant, and CLV never got above ~40% — the market moves away from the model's picks. Conclusion: ratings-based CFB spread picking does not clear the vig, and Edge Index should NOT sell CFB spread picks at launch. This negative result is worth real money — it is the product line that would have quietly eaten the subscribers' bankroll and the brand. Keep the harness (any future idea gets the same trial), and if CFB stays in the product, it must come from information speed (QB status, injuries, G5 news deserts) rather than ratings — a different pipeline, and unproven until backtested. Launch focus: NFL props + MLB strikeouts, with CFB as research. Wire `Tracker` into the site's RecordTracker so the public record is generated from the database, not by hand. Dry-run the NFL pipeline through preseason.

**September (NFL kickoff).** Publish the card: max 3 singles + max 2 parlays across NFL+CFB, every play posted with model prob, price, and book, graded next morning with CLV. Weeks 1-3 are the softest prop markets of the year (books have no current-season data either — your projection variance is their projection variance).

**November (NBA).** Reuse the NFL engine skeleton — `PropsEngine` is sport-agnostic once you feed it game logs (nba_api gives them free). Points/rebounds/assists mainlines, same de-vig discipline, same tracker. Do not launch NBA picks until a 2024-25 backtest with real or forward-collected lines clears breakeven.

## 5. Subscription (Gumroad, unchanged platform)

Sell transparency, not certainty — it is the one thing touts cannot copy. Free tier: yesterday's graded card + running record (this is marketing). Paid (~$15-25/mo): the daily card before lock, the model's fair line vs best available price on each play, and the bankroll rule (flat 1u, never chase). The pitch writes itself from the tracker: "every pick we've ever posted, graded, with closing-line value shown." Do not advertise a win percentage; advertise the audited record and CLV. Under- promise: 2-3 plays a day, some days zero — "no play" days are proof the model isn't a volume mill.

## 6. Alt-line strategy (Tim's bread and butter) — status

The strategy: below-mainline alt overs (receptions, rec/rush/pass yds, QB/RB attempts) at -120 to -500, stacked 2-3 legs. `engine/nfl/alt_backtest.py` tests exactly this. Findings on 2024 data: unfiltered alts run about -2% (the vig); model-filtered (EV>=0) alts ran +1.1% over 2,171 bets — directionally supportive. BUT the stored alt odds are contaminated (e.g., "Jefferson o1.5 rec at -146" — a live snapshot, pregame that's -1200), so the eye-popping parlay ROI in that backtest is an artifact. Verdict: the strategy is plausible and consistent with how Tim has actually profited, but it is UNVALIDATED until we have clean alt prices. Two ways to get them: (1) the timestamped pregame collector, starting immediately — free, answers it by mid-season; (2) spend the "hybrid" odds budget on The Odds API historical snapshots for 3-4 weeks of 2025 NFL alt markets — answers it before kickoff. Recommend (2): this is the single highest-value use of paid data because it validates the core product.

**Floor study — CORRECTED after data-quality audit.** The 2025 game_logs rows are SYNTHETIC (96.7% even values, 18 games/player, no byes — a seeder filled them; 2023-24 are organic) and the first floor study unknowingly included them, inflating everything. On real 2023-24 data only (4,095 obs, deduplicated): at 0.6x expected output, RECEPTIONS floors are real — 88-90% clear (fair price -750 to -900), so a book hanging -175 to -300 on a 0.6x receptions alt is offering serious +EV. YARDAGE floors are much weaker than first reported — rec_yds clears only 65-69% (fair ~-210), rush_yds 72-75% (fair ~-290): a -290 book price on a 0.6x rec-yds alt is roughly fair-to-negative WITHOUT matchup selection. The streak per se adds NOTHING on real data (7/7 -> 67% vs <=4/7 -> 69% for rec_yds) — the 94% streak effect was a synthetic-data artifact. Stability terciles also flatten. ACTION: re-pull real 2025 logs via nflverse_loader.py to double the real sample and re-verify.

**FINAL numbers — three real seasons (2023-25 re-pulled from nflverse, 42k obs, verified organic).** Receptions floors at 0.6x depth: 88.4% (fair -762); at 0.5x: 92.3% (fair -1195). Books hang these at -175 to -300 -> this is THE product edge, confirmed on every clean data source we have. Yardage floors confirmed weak: rec_yds 0.6x -> 67.0% (fair -203), rush_yds -> 71.2% (-247); a -290 yardage alt is -EV without a matchup case. Streaks and role-stability (cv) add ~nothing beyond the trailing average — use streaks as card COPY (subscribers love them), never as selection.

**Matchup gates (2024-25 real, n=4,274):** the blitz split is the star, and it points OPPOSITE directions by stat — high-blitz defenses BOOST WR/TE receptions floors (91.5%/89.7% vs 86.9%/82.8% low-blitz; quick game & hot routes) while CRUSHING RB rush floors (66.3% vs 74-79%). Card rule: vs blitz-heavy DCs take pass-catcher receptions, avoid RB rush yards. Slot corner quality still moves WR yardage floors (74.3% weak vs 66.1% elite — moderated from the 2024-only run) and barely moves receptions. DC tiers are stable across runs: Bowen/Schwartz/Babich toughest (~71-74% floors allowed), Spagnuolo/Austin/Woods softest (87-90%). Fix someday: Rams appear as 'LA' in game logs vs the CSV's code — Rams matchups drop from the join.

**Matchup study results (engine/nfl/matchup_study.py — floor study x NFL_Coaches_Schemes CSV, 4,157 steady-role player-weeks 2024-25).** The card's play/avoid rules, now data-backed at 0.6x depth: (1) WR yardage floors swing 9 points on slot corner quality — 94.2% clear vs weak slot corners, 85.0% vs elite; at a -450 alt price (81.8% implied) that is the difference between a strong play and a pass. (2) High-blitz defenses (>=29%) crush TE yardage floors (80.2% vs 85.8% low-blitz) but NOT TE reception floors (96.0%) — vs blitz-heavy DCs, take the TE receptions alt, never the yards alt. (3) High blitz also cuts RB rush-yds floors (82.7% vs 90.0%). (4) Surprise: zone-vs-man split barely moves WR floors (88.5-89.4% flat) — slot personnel and pressure matter more than shell for FLOOR plays. (5) DC spread is real: Babich/Fangio/Anarumo/Bowen suppress steady-role receiving floors (~86%), Flores/Minter/Shula sides allowed 96-100%. Caveats: full-season scheme values used within-season (deployment uses the CSV's preseason projections instead — keep 2026 rows updated), and some DC spread is roster, not scheme. Weekly human inputs Tim maintains: DC/OC changes, slot corner injuries/signings, OL status (RT out = avoid RB/TE floors), DL form. These feed card notes; the engine prices the rest.

## 7. Known issues / debt

The 2025 prop_lines rows need a cleanup pass (live snapshots); keep them for line-movement research, exclude from backtests. `backtest/nfl` vs `backtest/nfl_fixed` are near-duplicates — consolidate into `engine/`. The repo root has stray files from shell mishaps (`#`, `0.05`, `80%`, `npm`, `findstr` in cfb-app/) — safe to delete. MLBHub.jsx exists in three places; single-source it.
