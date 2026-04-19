# Edge Index Analytics — Master README

## What's in this package

```
edge_index/
├── models/
│   ├── nfl_props_model.py     # NFL passing/rushing/receiving props engine
│   └── cfb_model.py           # CFB spread + totals prediction engine
└── GUMROAD_COPY_AND_TEMPLATE.md  # Product copy, weekly template, launch post
```

---

## QUICK START — NFL Props

```python
from models.nfl_props_model import PropModel, PlayerGame, MatchupData, PickSheetGenerator

model = PropModel()

# 1. Build game logs for your player (most recent last)
games = [
    PlayerGame(week=1, opponent="KC", home_away="home", snap_pct=0.88,
               targets=9, receptions=7, rec_yards=94,
               team_pass_att=38, vegas_total=47, team_spread=-3),
    # ... add more weeks
]

# 2. Set up this week's matchup
matchup = MatchupData(
    opponent="DAL",
    def_rec_yards_allowed_rank=28,   # 28th = bad vs receivers = good for over
    def_targets_allowed_rank=24,
    def_td_rate_rank=20,
    game_total=51.5,
    team_spread=-6.5,
    is_home=True,
    implied_team_total=29.0,
    pace_rank=8,
)

# 3. Project + find edges vs. market lines
proj = model.project_player("Player Name", "WR", games, matchup)
edges = model.find_edge(proj, {
    "rec_yards":   82.5,
    "targets":     8.5,
    "receptions":  6.5,
})

# 4. Generate pick sheet text
gen = PickSheetGenerator()
sheet = gen.generate(week=10, season=2025, player_edges=[(proj, edges)])
print(sheet)
```

---

## QUICK START — CFB

```python
from models.cfb_model import CFBModel, TeamData, GameContext, CFBPickSheetGenerator

model = CFBModel()

# 1. Build team profiles (update weekly with current SP+ ratings)
home = TeamData(
    name="Georgia", conference="SEC",
    off_efficiency=18.2, def_efficiency=-20.1, st_efficiency=1.8,
    points_per_game=36.4, points_allowed=14.2,
    plays_per_game=71, recent_form_delta=0.8
)
away = TeamData(
    name="Tennessee", conference="SEC",
    off_efficiency=12.4, def_efficiency=-9.3, st_efficiency=0.5,
    points_per_game=31.1, points_allowed=19.8,
    plays_per_game=74, recent_form_delta=1.2
)

# 2. Game context
ctx = GameContext(
    home_team="Georgia", away_team="Tennessee",
    night_game=True, conference_game=True, rivalry_game=False,
    open_spread=-10.0, current_spread=-11.5,
    open_total=50.5,   current_total=51.5,
    spread_moved_toward_home=True,
)

# 3. Project + find edges
proj         = model.project_game(home, away, ctx)
spread_edge  = model.find_spread_edge(proj, ctx.current_spread)
total_edge   = model.find_total_edge(proj,  ctx.current_total)
line_signals = model.line_movement_signal(ctx)

print(f"Proj: {proj.proj_home_score} – {proj.proj_away_score}")
print(f"Spread edge: {spread_edge}")
print(f"Total edge:  {total_edge}")
print(f"Line signals: {line_signals}")
```

---

## WHERE TO GET FREE DATA (no API key needed to start)

| Source | What you get | How to use |
|--------|-------------|------------|
| Pro Football Reference | Game logs, snap %, targets | Export CSV manually each week |
| SP+ ratings (ESPN) | CFB efficiency ratings | Scrape or copy weekly |
| The Action Network | Market lines + line movement | Check manually before posting |
| KenPom (CBB, $20/yr) | You already have this from portal app | Direct integration |
| FantasyPros / RotoWire | Injury + snap % updates | Free tier weekly |

**Automation roadmap (Phase 2):**
- GitHub Actions scraper for PFR game logs (same pattern as your portal scraper)
- Playwright for line movement from Action Network
- Parquet caching for historical game logs (same as portal tracker)

---

## WEEKLY WORKFLOW (estimated: 2–3 hours/week)

**Thursday morning:**
1. Pull latest snap % / injury reports from FantasyPros
2. Update game logs for featured players (5–8 players)
3. Run nfl_props_model.py with this week's matchups + market lines
4. Paste Tier 1 + Tier 2 edges into the pick sheet template
5. Export PDF → upload to Gumroad

**Friday morning:**
1. Pull latest SP+ from ESPN
2. Update team profiles for featured games (4–6 games)
3. Run cfb_model.py for each game
4. Add CFB plays to same PDF
5. Post Reddit / Discord launch thread with 2–3 sample plays

**Monday:**
1. Record results in public tracker
2. Post results to all channels

---

## PRICING STRATEGY REMINDER

| Tier | Price | Target | Revenue |
|------|-------|--------|---------|
| Weekly | $20/wk | 15 subscribers | $300/wk |
| Monthly founding | $39/mo | 10 subscribers | $390/mo |
| Monthly standard | $69/mo | Future | — |
| Dashboard (Phase 2) | +$20/mo add-on | — | — |

**$1,000 milestone:** 20 weekly subs × $20 × 3 weeks = $1,200 ✓

---

*Edge Index — process over picks. Build the model, post the results, let the work speak.*
