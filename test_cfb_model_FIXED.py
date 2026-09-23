"""
Test CFB Power Ranking Model
Fixed import path for Windows
"""

import sys
import os

# Add models folder to path
sys.path.insert(0, os.path.join(os.getcwd(), 'models'))

# Now import
from cfb_spreads_2027 import CFBPowerRankingModel

print("="*70)
print("CFB POWER RANKING MODEL TEST")
print("="*70)

# Initialize model
model = CFBPowerRankingModel()

# Load data - use relative paths
data_path = os.path.join('data', 'cfb', 'team_historical.csv')
recruit_path = os.path.join('data', 'cfb', 'recruiting_ranks.csv')

print(f"\nLoading data from:")
print(f"  {data_path}")
print(f"  {recruit_path}")

try:
    model.load_data(data_path, recruit_path)
    print("✅ Data loaded successfully\n")
except FileNotFoundError as e:
    print(f"❌ ERROR: {e}")
    print("\nMake sure you have:")
    print("  edge-index/data/cfb/team_historical.csv")
    print("  edge-index/data/cfb/recruiting_ranks.csv")
    sys.exit(1)

# Test 1: Team ratings
print("="*70)
print("TEST 1: Individual Team Ratings")
print("="*70)

teams_to_test = ['Alabama', 'Georgia', 'Texas', 'Ohio State', 'Oregon', 'Notre Dame']

for team in teams_to_test:
    try:
        rating = model.calculate_team_rating(team)
        print(f"{team:15} | Rating: {rating:.4f}")
    except Exception as e:
        print(f"{team:15} | ERROR: {e}")

# Test 2: Matchup predictions
print("\n" + "="*70)
print("TEST 2: Head-to-Head Matchup Predictions")
print("="*70)

matchups = [
    ('Alabama', 'Texas'),
    ('Georgia', 'Ohio State'),
    ('Oregon', 'Notre Dame'),
]

for away, home in matchups:
    try:
        p_home, r_home, r_away = model.calculate_win_probability(home, away)
        print(f"{away:15} @ {home:15} | {home} wins: {p_home:.1%}")
    except Exception as e:
        print(f"{away:15} @ {home:15} | ERROR: {e}")

# Test 3: Edge detection
print("\n" + "="*70)
print("TEST 3: Finding Edges in Sample Spreads")
print("="*70)

sample_games = [
    {'home_team': 'Alabama', 'away_team': 'Texas', 'spread': -3.5, 'book': 'DK'},
    {'home_team': 'Georgia', 'away_team': 'Ohio State', 'spread': -2.0, 'book': 'FanDuel'},
    {'home_team': 'Oregon', 'away_team': 'Notre Dame', 'spread': 2.5, 'book': 'BetMGM'},
]

try:
    edges = model.find_edges(sample_games, min_edge_pct=1.0)
    if not edges.empty:
        print("\nEdges found (min 1.0%):")
        print(edges[['game', 'side', 'model_prob', 'market_prob', 'edge_pct']].to_string())
    else:
        print("No edges found (this is normal for sample spreads)")
except Exception as e:
    print(f"ERROR in edge detection: {e}")

print("\n" + "="*70)
print("✅ MODEL TESTS COMPLETE")
print("="*70)
print("""
If all tests passed:
- Model is ready for production
- You can start scoring CFB games

Next step:
- Pull real opening spreads for Week 0 CFB (Labor Day weekend)
- Run model.find_edges() to identify opportunities
- Log to your Google Sheet
""")

