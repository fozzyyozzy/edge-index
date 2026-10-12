# CFB betting splits: research only (Phase 4 brief §6)

Researched 2026-10-12. **No scraper built.** robots.txt files were fetched directly; terms
were read where they could be found.

## Sources

| Source | What it shows | Updates | History | Cost | Automated access allowed? |
|---|---|---|---|---|---|
| **VSiN: DraftKings splits** (data.vsin.com/college-football/betting-splits/, `?bookid=dk`) | **DK-specific** % of bets (tickets) vs % of handle, for spread, total and ML. Circa splits also offered. | Every **5 minutes** (VSiN) | No archive found. VSiN's own analysis covers 2022-24 (2,365 games), so data exists internally. | **VSiN Pro** membership (price not verified) | **Unclear → treat as no.** robots.txt allows `/betting-splits/` for general crawlers (it only blocks Baidu, PetalBot and Semrush). But I found no terms of use (the privacy page has no body, and the /terms URLs 404), the DK splits are a Pro (logged-in, paid) feature, and the data is DraftKings' under license to VSiN. |
| **Action Network** (actionnetwork.com/ncaaf/public-betting) | Aggregated % bets / % money, plus PRO "sharp" reports | Live | Not public | Free view; PRO paywalled | **No.** Terms §2 bar any "page-scrape, robot, spider or other automatic device" and any commercial use without written consent, and list "betting percentages" as protected content. robots.txt disallows all query-string URLs. Third-party Apify scrapers exist; using them would breach the terms. |
| **ScoresAndOdds** consensus (scoresandodds.com/ncaaf/consensus-picks) | Consensus % picks/money aggregated from several books (**not DK-specific**) | Daily+ | No | Free | robots.txt only disallows `/app`; terms not reviewed. Aggregated, not DK-specific, so a weaker signal. |
| **Sports Insights** (sportsinsights.com) | Historically offered public % data | n/a | Unknown | Unknown | robots.txt permissive; no current CFB splits product found. |
| Others (SportsBettingDime, CleatZ, BetQL, TheSpread) | Weekly public % pages, mostly aggregated | Weekly | No | Free/paywalled | Not DK-specific; no programmatic access offered. |

## Evidence on value (published, not ours)

VSiN's own 2022-24 CFB tracking (Makinen): majority **handle** on spreads went 48.7% ATS,
majority **tickets** 49.9%. On totals, majority handle went 51.4%. Raw majorities show no
edge. VSiN's pitch is the **ticket-vs-handle discrepancy** (≥10 points), which it states for
NFL more than CFB. Treat that as unverified for CFB.

## Recommendation

**None viable for automated collection today.** The one DK-specific source (VSiN) is a paid,
logged-in product, with DraftKings-licensed data and no published terms permitting automation.
Options, in order:

1. **Ask VSiN in writing** whether a licensed feed or API exists for DK CFB splits, at what
   price, and whether storing snapshots for internal modeling is permitted. This is the only
   route to a lawful, DK-specific historical series.
2. Meanwhile, if useful, Tim can **read VSiN Pro manually** for flagged games. That's human
   use, nothing stored automatically.
3. Revisit in Phase 5 only if a forward bar passes **and** (1) produces a permitted feed.

Sources: [VSiN DK splits](https://data.vsin.com/draftkings/betting-splits/),
[VSiN CFB splits](https://data.vsin.com/college-football/betting-splits/),
[VSiN CFB splits systems 2025](https://vsin.com/college-football/college-football-betting-splits-systems-update-for-the-2025-season/),
[VSiN: how to use DK/Circa splits](https://vsin.com/nfl/how-to-be-a-winning-football-bettor-using-draftkings-and-circa-nfl-betting-splits/),
[Action Network terms](https://www.actionnetwork.com/terms),
[Action Network NCAAF public betting](https://www.actionnetwork.com/ncaaf/public-betting),
[Apify Action Network scraper (not used)](https://apify.com/zen-studio/action-network-odds),
[ScoresAndOdds consensus](https://www.scoresandodds.com/ncaaf/consensus-picks).
