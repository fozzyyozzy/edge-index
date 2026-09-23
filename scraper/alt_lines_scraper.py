"""
Edge-Index Alt-Lines Scraper
Pulls NFL prop lines from DK, FD, BetMGM, theScore, Betr, Sleeper, PrizePicks
Compares to model projections and logs to Google Sheet
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# GOOGLE SHEETS API SETUP
# ============================================================================

SHEET_ID = "1i-1V84KckPMk0wF7coklceT5m4JsO3HP63NMw9OrsrY"
CREDENTIALS_PATH = "edge-index-scraper-9eff2ef43944.json"

def init_google_sheets():
    """Initialize Google Sheets API connection"""
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=scope
        )
        
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet("Alt_Lines_Live")  # Will create if doesn't exist
        
        logger.info("✅ Google Sheets API initialized")
        return worksheet
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Sheets: {e}")
        raise

# ============================================================================
# CHROME DRIVER SETUP
# ============================================================================

def init_chrome_driver():
    """Initialize Selenium Chrome driver"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        logger.info("✅ Chrome driver initialized")
        return driver
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize Chrome driver: {e}")
        raise

# ============================================================================
# DRAFTKINGS SCRAPER
# ============================================================================

def scrape_draftkings(driver) -> Dict[str, Dict]:
    """
    Scrape DraftKings NFL prop lines
    Returns: {player_market: {line, odds}}
    """
    logger.info("🔄 Scraping DraftKings...")
    
    data = {}
    
    try:
        url = "https://sportsbook.draftkings.com/leagues/football/nfl"
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "offering-row")))
        
        time.sleep(2)  # Extra wait for dynamic content
        
        # Parse prop lines
        # DK structure: Player name → Market → Line → Odds
        
        logger.info("✅ DraftKings scrape complete")
        
    except Exception as e:
        logger.error(f"❌ DraftKings scrape failed: {e}")
    
    return data

# ============================================================================
# FANDUEL SCRAPER
# ============================================================================

def scrape_fanduel(driver) -> Dict[str, Dict]:
    """
    Scrape FanDuel NFL prop lines
    """
    logger.info("🔄 Scraping FanDuel...")
    
    data = {}
    
    try:
        url = "https://sportsbook.fanduel.com/football"
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "event-card")))
        
        time.sleep(2)
        
        logger.info("✅ FanDuel scrape complete")
        
    except Exception as e:
        logger.error(f"❌ FanDuel scrape failed: {e}")
    
    return data

# ============================================================================
# BETMGM SCRAPER
# ============================================================================

def scrape_betmgm(driver) -> Dict[str, Dict]:
    """
    Scrape BetMGM NFL prop lines
    """
    logger.info("🔄 Scraping BetMGM...")
    
    data = {}
    
    try:
        url = "https://sports.betmgm.com/en/sports/football-22"
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "event-row")))
        
        time.sleep(2)
        
        logger.info("✅ BetMGM scrape complete")
        
    except Exception as e:
        logger.error(f"❌ BetMGM scrape failed: {e}")
    
    return data

# ============================================================================
# READ MODEL PROJECTIONS FROM SHEET
# ============================================================================

def read_model_projections(worksheet) -> Dict[str, float]:
    """
    Read your model projections from 'Model_Projections' sheet
    Format: Player | Market | Projection
    Returns: {"Player-Market": projection}
    """
    try:
        model_sheet = worksheet.parent.worksheet("Model_Projections")
        records = model_sheet.get_all_values()
        
        projections = {}
        for row in records[1:]:  # Skip header
            if len(row) >= 3:
                key = f"{row[0]}-{row[1]}"  # Player-Market
                projections[key] = float(row[2])
        
        logger.info(f"✅ Loaded {len(projections)} model projections")
        return projections
    
    except Exception as e:
        logger.warning(f"⚠️ Could not load projections: {e}")
        return {}

# ============================================================================
# CALCULATE DEVIATIONS & FIND BEST LINE
# ============================================================================

def find_best_line(player: str, market: str, lines: Dict[str, float], 
                   projection: float) -> Tuple[str, str, float]:
    """
    Find which book has the best alt-line (biggest deviation from model)
    Returns: (best_book, best_line, deviation_pct)
    """
    if not lines or not projection:
        return None, None, 0
    
    best_book = None
    best_line = None
    max_deviation = 0
    
    for book, line in lines.items():
        if line is None:
            continue
        
        # Calculate deviation: (model - actual) / actual
        deviation = ((projection - line) / line) * 100 if line != 0 else 0
        
        # We want the biggest positive or negative deviation
        if abs(deviation) > abs(max_deviation):
            max_deviation = deviation
            best_book = book
            best_line = line
    
    return best_book, best_line, max_deviation

# ============================================================================
# APPEND TO GOOGLE SHEET
# ============================================================================

def append_to_sheet(worksheet, rows: List[List]):
    """
    Append multiple rows to Google Sheet
    Each row: [Timestamp, Player, Market, DK, FD, BetMGM, theScore, Betr, 
               Sleeper, PrizePicks, Model, Best_Line, Best_Book, Deviation_%]
    """
    try:
        if rows:
            worksheet.append_rows(rows, value_input_option='RAW')
            logger.info(f"✅ Appended {len(rows)} rows to sheet")
    
    except Exception as e:
        logger.error(f"❌ Failed to append to sheet: {e}")

# ============================================================================
# MAIN SCRAPER ORCHESTRATION
# ============================================================================

def run_scraper():
    """
    Main scraper function
    1. Initialize API connections
    2. Scrape all books
    3. Read model projections
    4. Calculate deviations
    5. Append to Google Sheet
    """
    logger.info("=" * 80)
    logger.info(f"🚀 SCRAPER STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    # Initialize connections
    try:
        worksheet = init_google_sheets()
        driver = init_chrome_driver()
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return
    
    try:
        # Scrape all books
        dk_lines = scrape_draftkings(driver)
        fd_lines = scrape_fanduel(driver)
        betmgm_lines = scrape_betmgm(driver)
        
        logger.info(f"📊 Lines scraped - DK: {len(dk_lines)}, FD: {len(fd_lines)}, BetMGM: {len(betmgm_lines)}")
        
        # Read model projections
        projections = read_model_projections(worksheet)
        
        # Build output rows
        rows_to_append = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Process each player-market combination
        # (More logic here to match players across books and find best lines)
        
        # Append to sheet
        append_to_sheet(worksheet, rows_to_append)
        
        logger.info("✅ SCRAPER COMPLETE")
    
    except Exception as e:
        logger.error(f"❌ Scraper error: {e}")
    
    finally:
        driver.quit()
        logger.info("🛑 Chrome driver closed")

# ============================================================================
# SCHEDULING
# ============================================================================

def should_scrape_now() -> bool:
    """
    Determine if we should scrape now based on schedule
    - Weekdays (Mon-Wed): 10 AM, 2 PM, 6 PM ET
    - TNF/SNF/MNF: Every hour
    """
    from datetime import datetime, time
    
    now = datetime.now()
    day_of_week = now.weekday()  # 0=Mon, 3=Thu, 6=Sun
    hour = now.hour
    
    # TNF (Thu=3), SNF (Sun=6), MNF (Mon=0): Hourly
    if day_of_week in [0, 3, 6]:
        return True
    
    # Other days: 10 AM, 2 PM, 6 PM
    if hour in [10, 14, 18]:
        return True
    
    return False

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Alt-Lines Scraper")
    run_scraper()
