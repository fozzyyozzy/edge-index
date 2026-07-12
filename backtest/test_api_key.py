"""
Quick test to verify OddsPapi API key works.
Run this first before the full loader.

  set ODDS_API_KEY=your_key
  python test_api_key.py
"""
import sys, os, requests, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY  = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://v5.oddspapi.io"

if not API_KEY:
    print("ERROR: ODDS_API_KEY not set")
    print("  Windows: set ODDS_API_KEY=your_key")
    sys.exit(1)

print(f"Testing key: {API_KEY[:6]}...{API_KEY[-4:]}")
print()

# Test 4 different auth methods
tests = [
    ("Query param only",
     f"{BASE_URL}/api/sports",
     {"apiKey": API_KEY},
     {}),
    ("Bearer header only",
     f"{BASE_URL}/api/sports",
     {},
     {"Authorization": f"Bearer {API_KEY}"}),
    ("X-Api-Key header",
     f"{BASE_URL}/api/sports",
     {},
     {"X-Api-Key": API_KEY}),
    ("Both query + header",
     f"{BASE_URL}/api/sports",
     {"apiKey": API_KEY},
     {"Authorization": f"Bearer {API_KEY}"}),
]

working_method = None
for name, url, params, headers in tests:
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        status = r.status_code
        if status == 200:
            data = r.json()
            print(f"✓ {name} — WORKS (HTTP {status})")
            print(f"  Response preview: {str(data)[:150]}")
            working_method = name
            break
        else:
            print(f"✗ {name} — HTTP {status}: {r.text[:100]}")
    except Exception as e:
        print(f"✗ {name} — Error: {e}")

print()
if working_method:
    print(f"API key is valid. Working method: {working_method}")
    print("Now run: python propodds_loader.py --seasons 2024 --test")
else:
    print("All auth methods failed. Check:")
    print("  1. Key is correct (copy from dashboard, no spaces)")
    print("  2. Account is activated")
    print("  3. Try pasting this in browser:")
    print(f"     {BASE_URL}/api/sports?apiKey={API_KEY}")
