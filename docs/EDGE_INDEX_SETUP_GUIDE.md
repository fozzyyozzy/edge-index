# Edge Index — Complete Deployment Guide
### From zero to automated weekly pick sheet

---

## PHASE 1 — Prerequisites (~20 min)

### Step 1 — Check Python version
You likely have this from your portal tracker. Confirm 3.11+.

```bash
python3 --version
```
Need 3.11 or higher. If older: python.org/downloads

---

### Step 2 — Confirm Git is installed

```bash
git --version
```

If missing on Mac:
```bash
xcode-select --install
```
If missing on Windows:
```bash
winget install Git.Git
```

---

### Step 3 — Create a GitHub account (if needed)
Go to **github.com → Sign up**. Use a professional email.
If you already have one from your portal tracker, reuse it.

---

### Step 4 — Create a Gumroad account
Go to **gumroad.com → Start selling**.
Connect your bank account in Settings so payouts work immediately.
Free to create — Gumroad takes 10% per sale, no monthly fee.

---

## PHASE 2 — GitHub Repo (~15 min)

### Step 5 — Create a new private repo
On GitHub: **+ (top right) → New repository**
- Name: `edge-index`
- Visibility: **Private** (your model logic is your edge)
- Check "Initialize with README"
- Click **Create repository**

---

### Step 6 — Clone the repo to your machine

```bash
git clone https://github.com/YOUR_USERNAME/edge-index.git
cd edge-index
```
Replace YOUR_USERNAME with your actual GitHub username.

---

### Step 7 — Copy Edge Index files into the repo
Unzip `edge_index_complete.zip` (the file you downloaded from Claude).
Copy everything **inside** the `edge_index/` folder into your cloned repo.

Your folder structure should look exactly like this:
```
edge-index/
  models/
    nfl_props_model.py
    cfb_model.py
  scrapers/
    pfr_scraper.py
  scripts/
    generate_pick_sheet.py
    update_results.py
  .github/
    workflows/
      weekly_update.yml
  players.json
  requirements.txt
  results/
  data/
  outputs/
```

Create any empty folders that don't exist yet:
```bash
mkdir -p data/cache data/processed data/logs results outputs
```

---

### Step 8 — Create a .gitignore file
Create a file called `.gitignore` in the repo root with this content:
```
data/cache/
__pycache__/
*.pyc
.env
.DS_Store
```

> **Important:** Do NOT add `data/processed/` to .gitignore.
> GitHub Actions needs to commit parquet files from that folder.

---

### Step 9 — Push everything to GitHub

```bash
git add .
git commit -m "initial: Edge Index setup"
git push origin main
```

After pushing: go to **github.com/YOUR_USERNAME/edge-index → Actions tab**.
You should see "Edge Index Weekly Update" listed in the left sidebar.
If it's there — the workflow file was recognized successfully.

---

## PHASE 3 — Local Python Environment (~20 min)

### Step 10 — Create a virtual environment

```bash
cd edge-index
python3 -m venv venv
source venv/bin/activate        # Mac / Linux
# OR:
venv\Scripts\activate           # Windows
```

> You'll run the activate command every time you open a new terminal
> window for Edge Index work.

---

### Step 11 — Install Python dependencies

```bash
pip install -r requirements.txt
```

If pyarrow fails (common on newer Python):
```bash
pip install pyarrow --pre
```

---

### Step 12 — Install Playwright browser
Playwright needs to download Chromium separately from the pip package.
This is a one-time download (~150MB) — identical to your portal tracker setup.

```bash
playwright install chromium
```

---

### Step 13 — Run the model smoke test
Confirm the models work before adding scraper complexity.

```bash
python3 models/nfl_props_model.py
python3 models/cfb_model.py
```

**You should see:**
- "PROJECTION: Tyreek Hill (WR)" with rec yards, targets, receptions
- A formatted pick sheet with Tier 1 / Tier 2 plays
- "PROJECTION: Auburn @ Alabama" with spread and total edges

If both print cleanly — your models are working perfectly.

---

## PHASE 4 — GitHub Actions Secrets (~10 min)

### Step 14 — Enable Actions write permissions
By default Actions can't commit files back to your repo.
You need to grant write access so it can save the parquet data files.

**GitHub repo → Settings → Actions → General**
→ Scroll to "Workflow permissions"
→ Select **"Read and write permissions"**
→ Save

---

### Step 15 — Add Discord webhook (optional, recommended)
When a run completes, Actions pings your Discord so subscribers know
the sheet is ready. This is your automated subscriber notification.

**Step A — Get the webhook URL:**
Discord → your server → channel settings → Integrations → Webhooks → New Webhook → copy URL

**Step B — Add it as a GitHub secret:**
GitHub repo → Settings → Secrets and variables → Actions
→ New repository secret
→ Name: `DISCORD_WEBHOOK`
→ Paste the URL
→ Add secret

---

### Step 16 — Verify workflow appears in Actions tab
Go to **github.com/YOUR_USERNAME/edge-index → Actions tab**

"Edge Index Weekly Update" should appear in the left sidebar.

If it's missing:
- Confirm `weekly_update.yml` is in `.github/workflows/`
- Confirm you ran `git push` after adding the file
- Check the file has no YAML syntax errors (indentation matters)

---

## PHASE 5 — First Manual Run (~30 min)

### Step 17 — Trim players.json for your test run
Smaller list = faster first run. Edit players.json to 6–8 players:

```json
{
  "Tyreek Hill":   "HillTy00",
  "CeeDee Lamb":   "LambCe00",
  "Travis Kelce":  "KelcTr00",
  "Lamar Jackson": "JackLa02",
  "Josh Allen":    "AlleJo02",
  "Breece Hall":   "HallBr01"
}
```
You can expand back to the full 22-player roster after you confirm it works.

---

### Step 18 — Add this week's market lines
Open `scripts/generate_pick_sheet.py`.
Find the `get_this_weeks_matchups()` function and update it.
This is the **only file you edit each week** — takes 10–15 minutes.

Pull lines from Action Network, DraftKings, or FanDuel.

```python
nfl_targets = [
    {
        "player":   "Tyreek Hill",
        "position": "WR",
        "opponent_abbr": "NE",        # this week's opponent (PFR 2-3 letter abbr)
        "market_lines": {
            "rec_yards":   72.5,      # from your sportsbook
            "targets":     7.5,
            "receptions":  5.5,
        },
        "matchup_overrides": {
            "game_total":  48.5,      # total from the sportsbook
            "team_spread": -9.5,      # MIA is 9.5-point favorite
            "is_home":     True,
        }
    },
    # add 4-7 more players
]
```

**Focus on:** bad defenses (rank 25–32), high game totals (50+),
lopsided spreads (strong favorite = good pass game script).

---

### Step 19 — Push and trigger a manual run

```bash
git add .
git commit -m "w10 matchups"
git push origin main
```

Then trigger manually:
**GitHub repo → Actions tab → "Edge Index Weekly Update"**
→ "Run workflow" button (top right of runs list)
→ Enter the current week number
→ Click **Run workflow**

The run takes 5–10 minutes. Click into it to watch live —
each step shows a green checkmark as it completes.

---

### Step 20 — Pull the output and check your pick sheet

```bash
git pull
cat outputs/pick_sheet_2025_w*.md
```

You should see a fully formatted pick sheet with:
- NFL props: Tier 1 (★★★) and Tier 2 (★★) plays with projections, edge %, win prob
- CFB: spread and total plays with model spread vs. market

**To deliver to subscribers:**
1. Copy the markdown content
2. Paste into Google Docs
3. File → Download → PDF
4. Upload to Gumroad as your weekly product update

---

## PHASE 6 — Weekly Rhythm (ongoing)

### Every Thursday (15 min) — NFL sheet

```bash
# 1. Check FantasyPros for injury updates (5 min)
# 2. Update generate_pick_sheet.py with this week's lines (10 min)

git add .
git commit -m "w11 matchups"
git push origin main

# Actions fires automatically at 6am ET Thursday
# OR trigger manually from the Actions tab anytime after you push
```

After the run completes:
```bash
git pull
# Copy outputs/pick_sheet_*.md → Google Doc → export PDF → upload to Gumroad
```

---

### Every Friday (10 min) — CFB update
Same process — update the `cfb_games` section in `get_this_weeks_matchups()`
with the latest SP+ ratings from ESPN and current spreads/totals.

---

### Every Monday (15 min) — Results update
Add a row to `results/results_tracker.csv` for each play from the weekend:

```
week, season, date, type, player_or_game, stat_or_side, direction, line,
projection, edge_pct, tier, actual, result, units, notes
```

Example row:
```
10,2025,2025-11-10,nfl,Tyreek Hill,rec_yards,OVER,72.5,89.7,23.7,1,94.0,W,0.909,hit per model
```

Then generate the public record:
```bash
python3 scripts/update_results.py
```

Paste `results/public_record.md` into your Reddit + Discord posts.
**This Monday transparency post is what builds trust and sells subscriptions.**

---

## QUICK REFERENCE — PFR Team Abbreviations

| Team | Abbr | Team | Abbr |
|------|------|------|------|
| Miami Dolphins | MIA | Kansas City Chiefs | KAN |
| Buffalo Bills | BUF | Las Vegas Raiders | LVR |
| New England Patriots | NWE | Denver Broncos | DEN |
| New York Jets | NYJ | Los Angeles Chargers | LAC |
| Baltimore Ravens | BAL | Dallas Cowboys | DAL |
| Pittsburgh Steelers | PIT | Philadelphia Eagles | PHI |
| Cincinnati Bengals | CIN | New York Giants | NYG |
| Cleveland Browns | CLE | Washington Commanders | WAS |
| San Francisco 49ers | SFO | Chicago Bears | CHI |
| Seattle Seahawks | SEA | Green Bay Packers | GNB |
| Los Angeles Rams | LAR | Minnesota Vikings | MIN |
| Arizona Cardinals | ARI | Detroit Lions | DET |

---

## TROUBLESHOOTING

**"playwright install chromium" fails:**
```bash
pip install playwright --upgrade
playwright install chromium --with-deps
```

**pyarrow import error:**
```bash
pip install pyarrow --pre --force-reinstall
```

**GitHub Actions run fails on "git push" step:**
→ Check that you enabled "Read and write permissions" in Step 14

**No edges found in pick sheet:**
→ The model threshold is 8% by default. Lower it temporarily for testing:
  In `nfl_props_model.py`, find `find_edge()` and change `min_edge_pct=0.08` to `min_edge_pct=0.05`

**PFR scraper returns empty data:**
→ PFR occasionally changes their HTML structure. Check the URL manually in a browser first.
→ Try running with `--refresh` flag to bypass cache

---

## TOTAL TIME INVESTMENT

| Phase | One-time setup | Recurring |
|-------|---------------|-----------|
| Prerequisites + repo | ~35 min | — |
| Local setup + smoke test | ~20 min | — |
| Actions config | ~10 min | — |
| First manual run | ~30 min | — |
| **Weekly Thursday** | — | 15 min |
| **Weekly Friday** | — | 10 min |
| **Weekly Monday** | — | 15 min |
| **Total recurring** | — | **~40 min/week** |

---

*Edge Index — process over picks. Build the model, post the results, let the work speak.*
