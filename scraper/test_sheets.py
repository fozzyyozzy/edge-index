import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1i-1V84KckPMk0wF7coklceT5m4JsO3HP63NMw9OrsrY"
CREDENTIALS_PATH = "edge-index-scraper-9eff2ef43944.json"

try:
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet("Alt_Lines_Live")
    
    print("✅ Connected to Google Sheets")
    print(f"Worksheet: {worksheet.title}")
    print(f"Max rows: {worksheet.row_count}")
    
except Exception as e:
    print(f"❌ Error: {e}")