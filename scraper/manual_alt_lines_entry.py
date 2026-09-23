import gspread
from google.oauth2.service_account import Credentials
import csv
from datetime import datetime

SHEET_ID = "1i-1V84KckPMk0wF7coklceT5m4JsO3HP63NMw9OrsrY"
CREDENTIALS_PATH = "edge-index-scraper-9eff2ef43944.json"

print("=" * 80)
print("🚀 MANUAL ALT-LINES ENTRY TOOL")
print("=" * 80)

# Step 1: Connect
print("\n[1/3] Connecting to Google Sheets...")
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet("Alt_Lines_Live")
    print("✅ Connected")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# Step 2: Ask for filename
print("\n[2/3] Enter CSV filename (e.g., alt_lines.csv):")
filename = input("> ")

print(f"\nLoading {filename}...")
try:
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"✅ Loaded {len(rows)} lines")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# Step 3: Load model projections
print("\n[3/3] Loading model projections...")
try:
    model_sheet = sheet.worksheet("Model_Projections")
    records = model_sheet.get_all_values()
    projections = {}
    for row in records[1:]:
        if len(row) >= 3:
            key = f"{row[0]}-{row[1]}"
            projections[key] = float(row[2])
    print(f"✅ Loaded {len(projections)} projections")
except Exception as e:
    print(f"⚠️ Could not load projections: {e}")
    projections = {}

# Step 4: Process and upload
print("\nProcessing lines...")
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
rows_to_upload = []

for i, line in enumerate(rows):
    player = line.get('Player', '')
    market = line.get('Market', '')
    dk = line.get('DK', '')
    fd = line.get('FD', '')
    betmgm = line.get('BetMGM', '')
    
    # Get model projection
    key = f"{player}-{market}"
    model_proj = projections.get(key, '')
    
    # Calculate deviation
    deviation = ''
    if model_proj and dk:
        try:
            dev = ((float(model_proj) - float(dk)) / float(dk)) * 100
            deviation = f"{round(dev, 1)}%"
        except:
            pass
    
    # Best line (just use DK for now)
    best_line = dk
    best_book = 'DK'
    
    row = [timestamp, player, market, dk, fd, betmgm, '', '', '', '', model_proj, best_line, best_book, deviation]
    rows_to_upload.append(row)
    print(f"✓ {player} - {market}")

# Upload
print(f"\nUploading {len(rows_to_upload)} rows to Google Sheet...")
try:
    worksheet.append_rows(rows_to_upload, value_input_option='RAW')
    print("✅ SUCCESS - Data uploaded to Alt_Lines_Live")
except Exception as e:
    print(f"❌ Error uploading: {e}")

print("\n" + "=" * 80)
print("Done!")
print("=" * 80)