# Edge-Index Alt-Lines Scraper: Setup Guide

**Status:** Code complete, ready to deploy

**Deployment Options:**
- Option A: Run locally on your machine
- Option B: Deploy to Heroku (free tier, automatic scheduling)

---

## Option A: Local Setup (Simplest for Testing)

### Step 1: Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Place credentials file
Make sure `edge-index-scraper-9eff2ef43944.json` is in the same directory as the scraper

### Step 3: Run scraper once (test)
```bash
python alt_lines_scraper.py
```

You should see:
```
🚀 SCRAPER STARTED: 2025-09-01 10:00:00
✅ Google Sheets API initialized
✅ Chrome driver initialized
🔄 Scraping DraftKings...
✅ DraftKings scrape complete
...
✅ SCRAPER COMPLETE
```

### Step 4: Set up automatic scheduling

**Option A1: Manual (you run it 3x per day)**
- 10 AM: `python alt_lines_scraper.py`
- 2 PM: `python alt_lines_scraper.py`
- 6 PM: `python alt_lines_scraper.py`

**Option A2: Automated with APScheduler**
```bash
python scheduler.py
```
(Runs in background, auto-schedules based on game days)

---

## Option B: Deploy to Heroku (Fully Automated, Free Tier)

### Step 1: Install Heroku CLI
- Mac: `brew tap heroku/brew && brew install heroku`
- Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
- Linux: `curl https://cli.heroku.com/install.sh | sh`

### Step 2: Login to Heroku
```bash
heroku login
```
(Opens browser, authenticate with GitHub or create Heroku account)

### Step 3: Create Heroku app
```bash
heroku create edge-index-scraper-live
```

### Step 4: Set environment variables
```bash
heroku config:set SHEET_ID="1i-1V84KckPMk0wF7coklceT5m4JsO3HP63NMw9OrsrY"
heroku config:set CREDENTIALS_JSON=$(cat edge-index-scraper-9eff2ef43944.json | base64)
```

### Step 5: Initialize Git repo (if not already)
```bash
git init
git add .
git commit -m "Initial commit: Alt-lines scraper"
```

### Step 6: Deploy to Heroku
```bash
git push heroku main
```

### Step 7: View live logs
```bash
heroku logs --tail
```

### Step 8: Check if it's running
```bash
heroku ps:scale worker=1
```

---

## What the Scraper Does

1. **Scrapes 7 sportsbooks:**
   - DraftKings
   - FanDuel
   - BetMGM
   - theScore
   - Betr
   - Sleeper
   - PrizePicks

2. **Pulls all markets:**
   - Receiving Yards
   - Receptions
   - Pass Yards
   - Pass Completions
   - Rush Yards
   - Rush Attempts
   - Anytime TD
   - And more

3. **Compares to your model:**
   - Reads your daily projections from "Model_Projections" sheet tab
   - Calculates deviation % for each book
   - Identifies "best line" (biggest edge)

4. **Logs to Google Sheet:**
   - Timestamp
   - Player name
   - Market
   - Lines from all books
   - Your model projection
   - Best line & book
   - Deviation %

5. **Scheduling:**
   - Weekdays (Mon-Wed): 10 AM, 2 PM, 6 PM ET
   - TNF/SNF/MNF: Every hour during game windows

---

## Your Google Sheet Setup

### Tab 1: "Alt_Lines_Live" (Auto-populated by scraper)
Headers:
```
Timestamp | Player | Market | DK | FD | BetMGM | theScore | Betr | Sleeper | PrizePicks | Your_Model | Best_Line | Best_Book | Deviation_%
```

**Example row (auto-filled by scraper):**
```
2025-09-01 10:15 | Travis Kelce | Receptions | 8.5 | 8.5 | 8.0 | 8.5 | 8.5 | 8.5 | 8.5 | 9.1 | 8.0 | BetMGM | +13.8%
```

### Tab 2: "Model_Projections" (YOU FILL THIS DAILY)
Headers:
```
Player | Market | Projection
```

**Example rows (you enter these each morning):**
```
Travis Kelce | Receptions | 9.1
Davante Adams | Receptions | 4.1
Drake Maye | Pass_Cmps | 20.3
```

**How to fill it:**
1. Run your model in the morning
2. Get projections for each player-market
3. Paste into "Model_Projections" tab
4. Scraper reads it automatically

---

## Troubleshooting

**Problem:** Chrome driver not found
**Solution:** Run `pip install webdriver-manager` (already in requirements.txt)

**Problem:** Google Sheets API not authorized
**Solution:** Make sure you shared your Google Sheet with: `edge-index-scraper@edge-index-scraper.iam.gserviceaccount.com`

**Problem:** Scraper times out
**Solution:** Increase timeout in code from 10 to 15 seconds (line: `WebDriverWait(driver, 10)`)

**Problem:** Heroku app sleeping
**Solution:** Use free-tier scheduler to keep it warm, or manually trigger with: `heroku run python alt_lines_scraper.py`

---

## Next Steps

### Monday Sept 1 @ 10 AM:

1. **Create "Model_Projections" sheet tab** (if not already)
2. **Enter your daily projections** from your model
3. **Start scraper** (locally or on Heroku)
4. **Watch Google Sheet auto-populate** with lines from all books

### Throughout Week:

1. **Update "Model_Projections"** each morning with fresh projections
2. **Check "Alt_Lines_Live"** sheet for best lines
3. **Log to your betting tracker** when you place bets

### Sept 8 Decision:

- If alt-line strategy works (high deviations found) → Keep running
- If not useful → Disable scraper, continue with manual approach

---

## File Structure

```
edge-index-scraper/
├── alt_lines_scraper.py          # Main scraper
├── line_parsers.py               # Line extraction logic
├── scheduler.py                  # APScheduler for automation
├── requirements.txt              # Python dependencies
├── Procfile                       # Heroku config
├── runtime.txt                   # Python version
├── edge-index-scraper-9eff2ef43944.json  # Google Sheets credentials
└── scraper.log                   # Log file (auto-created)
```

---

## API Costs

✅ **Google Sheets API:** FREE (included in Google Cloud free tier)
✅ **Heroku:** FREE (free dyno, 5 dyno hours/month = more than enough)
✅ **Web scraping libraries:** FREE (open source)

**Total cost:** $0/month

---

## Support

If anything breaks:
1. Check `scraper.log` for error messages
2. Run locally first to debug: `python alt_lines_scraper.py`
3. Check Heroku logs: `heroku logs --tail`
4. Make sure "Model_Projections" sheet exists and has data

Good luck! 🚀

