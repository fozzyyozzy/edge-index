# NFL Main-Line Check: receptions / rec_yds Overs and Unders, DK vs best price (2025)

**Date:** 2026-10-21 · **Type:** descriptive only. No pre-registration, **no new credits.** It uses the 2025 closing prices already pulled from 8 US books (`early_props_2025.parquet`, `CLOSE_ALL` snapshot).

**Rule 5 applies:** anything here that looks profitable is a slice found after looking. It's a **hypothesis** until a pre-registered forward test confirms it.

## Data

- **Lines:** 5,726 DK closing main lines (269 games, regular season), each with both an Over and an Under price at DK.
- **Coverage:** a median of 5 books post the same line.
- **Settlement:**
  - From nflverse.
  - All lines are half-points, so there are no pushes.
  - Players who didn't play are excluded, since DK voids those props.
- **Best price:** the highest payout for that side across the 8 books **at the same line**, never worse than DK's.

## Flat returns (1u on every line, both sides)

| Slice | n | Hit | **ROI at DK price** [95% CI] | **ROI at best price** [95% CI] | Recovered by shopping |
|---|---|---|---|---|---|
| All main lines, both sides | 11,452 | 50.0% | −5.72% [−5.93, −5.51] | −3.96% [−4.19, −3.74] | +1.76 pts |
| Receptions, both sides | 5,584 | 50.0% | −6.10% | −3.15% | +2.95 pts |
| rec_yds, both sides | 5,868 | 50.0% | −5.35% | −4.73% | +0.62 pts |
| **Receptions Overs** | 2,792 | 44.1% | **−15.76%** [−19.55, −12.12] | −12.91% [−16.82, −9.12] | +2.85 |
| **Receptions Unders** | 2,792 | 55.9% | **+3.57%** [−0.06, +7.24] | **+6.60%** [+2.85, +10.37] | +3.03 |
| **rec_yds Overs** | 2,934 | 45.4% | **−14.00%** [−17.60, −10.38] | −13.48% [−17.10, −9.84] | +0.52 |
| **rec_yds Unders** | 2,934 | 54.6% | **+3.29%** [−0.33, +6.88] | **+4.02%** [+0.37, +7.64] | +0.73 |

"Both sides" hits exactly 50% by construction: one side of each line wins.

### Vig by market

| Market | DK hold (mean) | Best-price hold (best Over + best Under, mean) | Lines where best prices form an arb (hold < 0) |
|---|---|---|---|
| Receptions | 6.01% | **2.78%** | 3.5% |
| rec_yds | 5.66% | 4.94% | 0.0% |
| All | 5.83% | 3.89% | 1.7% |

**Shopping recovers about 1.8 points of return overall**: 3 points on receptions, under 1 on rec_yds.
- **Receptions:** books disagree a lot, and shopping cuts the effective vig from about 6% to under 3%.
- **rec_yds:** books are tightly aligned on yardage lines.

### Unders by season half (post-hoc stability check)

| Slice | n | Under hit | ROI at DK [95% CI] | ROI at best [95% CI] |
|---|---|---|---|---|
| Receptions Unders, weeks 1–9 | 1,410 | 55.5% | +3.02% [−2.12, +8.08] | +5.95% [+0.65, +11.18] |
| Receptions Unders, weeks 10–18 | 1,382 | 56.4% | +4.13% [−1.09, +9.12] | +7.26% [+1.89, +12.41] |
| rec_yds Unders, weeks 1–9 | 1,479 | 53.1% | +0.57% [−4.40, +5.51] | +1.28% [−3.73, +6.25] |
| rec_yds Unders, weeks 10–18 | 1,455 | 56.0% | +6.05% [+0.87, +11.22] | +6.81% [+1.59, +12.01] |

- **Better Under elsewhere:** another book beat DK's Under price on **54%** of lines.
- **Who had it:** FanDuel 663, BetMGM 596, BetOnline 583, Caesars 398, Bovada 381, BetRivers 304, Fanatics 174.

## The factor study's combined model (game script + weather) on main lines, weeks 10–18

- **Model:** refit exactly as registered (rows A, weeks 1–9, per market). Applied to main lines with DK's main-line de-vig as the base probability.
- **"Favored"** = EV > 0 at the price. One leg per player-game-market, the higher-EV side.

| Legs | n | Games | Sides | Model p (mean) | Hit | ROI [95% CI] |
|---|---|---|---|---|---|---|
| All main lines, both sides (baseline), DK price | 5,674 | 134 | — | — | 50.0% | −5.70% [−6.01, −5.39] |
| All main lines, both sides (baseline), best price | 5,674 | 134 | — | — | 50.0% | −3.98% [−4.31, −3.64] |
| **Favored at DK price** | 1,486 | 127 | 799 U / 687 O | 55.5% | 52.0% | **−1.17%** [−7.41, +4.78] |
| **Favored at best price** | 1,921 | 134 | 996 U / 925 O | 54.7% | 51.4% | **−0.32%** [−5.96, +5.23] |

| Favored, by market | n | ROI [95% CI] |
|---|---|---|
| Receptions, at DK | 689 | +1.6% [−6.4, +9.5] |
| rec_yds, at DK | 797 | −3.6% [−10.6, +3.4] |
| Receptions, at best | 1,047 | +1.5% [−5.3, +8.3] |
| rec_yds, at best | 874 | −2.5% [−9.2, +4.2] |

- **The model's picks only escape part of the vig.** Its favored legs do better than betting every line (−1.2% vs −5.7%), but the interval spans zero, and its 55% expected hit rate came in at 52%.
- **It underperforms a simple direction.** The plain "all Unders" slice above beat it. About half the model's favored legs are Overs, which lost 13–16% as a group.

## What this says

1. **Main-line Overs on receptions and rec_yds were heavily −EV in 2025:** −14% to −16% at DK, and shopping barely helps.
2. **Main-line Unders were the profitable side in 2025:** +3–4% at DK, and **+4% to +7% at the best of 8 books**, positive in both halves of the season.
   - This fits the widely reported public-Overs bias in player props.
   - But it was **found after looking** and comes from a single season. It's a **hypothesis.**
3. **Line shopping matters on main lines, unlike floors.** It cuts the effective receptions vig from about 6% to under 3% and adds about 3 points of return.
4. **The factor study's combined model adds nothing** beyond what the plain Under side shows.

### If Tim wants to pursue (2), not done

- **Pre-register** "receptions/rec_yds main-line Unders at the best available price" and test it forward on 2026.
- **Free option:** the live pipeline's committed DK two-way pulls (DK only) cover weeks 3–6 already.
- **Costed option:** an all-book version would need a pull with `regions=us`, about 40 credits per game.
- **Questions for a real betting plan:** account limits on Unders, and which books are actually available to Tim (BetOnline and Bovada are offshore).

## Files (branch `nfl-verify`)

| Path | Contents |
|---|---|
| `engine/nfl/main_lines_check.py` | The check |
| `data/nfl/verify/main_lines_check.json` | All numbers above |
| `data/nfl/verify/main_lines_unders_halves.json` | Season-half split |
