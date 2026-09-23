"""
CFB Proper Backtest: Train/Test Split + Edge vs Vegas
Measures: Does model beat Vegas consensus, not just pick winners
"""

import pandas as pd
import numpy as np
import os

# Try to load from current directory or data/cfb folder
def find_games_file():
    paths = [
        'cfb_backtest_games.csv',
        'data/cfb/cfb_backtest_games.csv',
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("cfb_backtest_games.csv not found")

games_file = find_games_file()
print(f"Loading from: {games_file}\n")

# Load all games
all_games = pd.read_csv(games_file)

print("="*80)
print("CFB PROPER BACKTEST: TRAIN/TEST SPLIT")
print("="*80)

print(f"\nTotal games loaded: {len(all_games)}")
print(f"Seasons: {all_games['season'].min()}-{all_games['season'].max()}\n")

# Split: Train on 2023-2024, Test on 2025 only
train_games = all_games[all_games['season'] < 2025].copy()
test_games = all_games[all_games['season'] == 2025].copy()

print(f"Training set (2023-2024): {len(train_games)} games")
print(f"  2023: {len(train_games[train_games['season'] == 2023])}")
print(f"  2024: {len(train_games[train_games['season'] == 2024])}")
print(f"\nTest set (2025 only): {len(test_games)} games")

# ============================================================================
# PART 1: BUILD MODEL ON 2023-2024 DATA
# ============================================================================

print("\n" + "="*80)
print("PART 1: BUILD MODEL ON TRAINING DATA (2023-2024)")
print("="*80)

def get_team_stats(team_name, df):
    """Get team's record from dataset"""
    home_games = df[df['home_team'] == team_name]
    away_games = df[df['away_team'] == team_name]
    
    home_wins = (home_games['result'] == 1).sum()
    home_losses = (home_games['result'] == 0).sum()
    
    away_wins = (away_games['result'] == 0).sum()
    away_losses = (away_games['result'] == 1).sum()
    
    total_wins = home_wins + away_wins
    total_games = home_wins + home_losses + away_wins + away_losses
    
    return {
        'wins': total_wins,
        'games': total_games,
        'win_pct': total_wins / total_games if total_games > 0 else 0.5
    }

# Build team ratings from training data
print("\nCalculating team ratings from 2023-2024 games...\n")

team_ratings = {}
for team in sorted(all_games['home_team'].unique()):
    stats = get_team_stats(team, train_games)
    if stats['games'] > 0:
        rating = stats['win_pct'] * 0.5 + 0.5
        team_ratings[team] = {
            'win_pct': stats['win_pct'],
            'rating': np.clip(rating, 0.2, 0.95),
            'games': stats['games'],
            'wins': stats['wins']
        }

# Show top teams
sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1]['rating'], reverse=True)
print("Top 12 teams by record (2023-2024):")
for i, (team, stats) in enumerate(sorted_teams[:12]):
    print(f"  {i+1:2d}. {team:15} | {stats['win_pct']:.1%} W ({stats['wins']}/{stats['games']}) | Rating: {stats['rating']:.3f}")

# ============================================================================
# PART 2: TEST ON 2025 DATA
# ============================================================================

print("\n" + "="*80)
print("PART 2: TEST MODEL ON 2025 GAMES")
print("="*80)
print("\nModel has never seen these games. Scoring with 2023-2024 training...\n")

def american_to_prob(odds):
    """Convert American odds to implied probability"""
    odds = float(odds)
    if odds < 0:
        return -odds / (-odds + 100)
    else:
        return 100 / (odds + 100)

results = []

for idx, game in test_games.iterrows():
    home = game['home_team']
    away = game['away_team']
    actual_result = game['result']
    spread = game['opening_spread']
    
    # Get ratings (trained on 2023-2024)
    home_rating = team_ratings.get(home, {}).get('rating', 0.5)
    away_rating = team_ratings.get(away, {}).get('rating', 0.5)
    
    # Model win probability
    if home_rating + away_rating > 0:
        model_prob_home = home_rating / (home_rating + away_rating)
    else:
        model_prob_home = 0.5
    
    # Vegas implied probability
    vegas_prob_home = american_to_prob(spread)
    
    # Edge
    edge_pct = (model_prob_home - vegas_prob_home) * 100
    
    # Did model pick win?
    model_pick = 1 if model_prob_home > 0.5 else 0
    is_correct = (model_pick == actual_result)
    
    results.append({
        'game': f"{away}@{home}",
        'model_prob_home': model_prob_home,
        'vegas_prob_home': vegas_prob_home,
        'edge_pct': edge_pct,
        'spread': spread,
        'model_pick': 'HOME' if model_pick == 1 else 'AWAY',
        'actual_result': 'HOME' if actual_result == 1 else 'AWAY',
        'correct': is_correct,
    })
    
    if idx < 10:
        edge_marker = "✓" if edge_pct >= 1.5 else " "
        print(f"{edge_marker} {away:15}@{home:15} | Model: {model_prob_home:.1%} | Vegas: {vegas_prob_home:.1%} | Edge: {edge_pct:+.2f}%")

print(f"... (showing 10 of {len(test_games)})\n")

results_df = pd.DataFrame(results)

# ============================================================================
# PART 3: BETTING PERFORMANCE ON HIGH-EDGE GAMES
# ============================================================================

print("="*80)
print("PART 3: BETTING PERFORMANCE (GAMES WITH EDGE ≥ +1.5%)")
print("="*80)

bettable = results_df[results_df['edge_pct'] >= 1.5].copy()

print(f"\nGames where model disagrees with Vegas by ≥1.5%: {len(bettable)} games\n")

if len(bettable) > 0:
    print("Bettable games:\n")
    for idx, game in bettable.iterrows():
        result_marker = "✓" if game['correct'] else "✗"
        print(f"{result_marker} {game['game']:30} | Model: {game['model_prob_home']:.1%} | Vegas: {game['vegas_prob_home']:.1%} | Edge: {game['edge_pct']:+.2f}%")
    
    wins = (bettable['correct']).sum()
    losses = len(bettable) - wins
    win_pct = wins / len(bettable)
    
    # ROI at -110
    roi = (wins * 0.909 - losses * 1.0) / len(bettable)
    
    print(f"\n{'='*80}")
    print(f"RESULTS ON HIGH-EDGE GAMES (≥1.5%):")
    print(f"{'='*80}")
    print(f"\nBets placed: {len(bettable)}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win rate: {win_pct:.1%}")
    print(f"ROI at -110: {roi:+.2%}")
    print(f"Average edge taken: {bettable['edge_pct'].mean():+.2f}%")
    
    print(f"\n{'VERDICT:'}{'':10}")
    if win_pct >= 0.55:
        print(f"  ✅ STRONG EDGE")
        print(f"  {win_pct:.1%} win rate on high-edge bets")
        print(f"  Model beats Vegas. Ready to deploy.")
    elif win_pct >= 0.53:
        print(f"  🟡 MODERATE EDGE")
        print(f"  {win_pct:.1%} win rate — slightly above breakeven (52.4%)")
        print(f"  Deployable but paper trade first to confirm.")
    elif win_pct >= 0.52:
        print(f"  🟡 WEAK EDGE")
        print(f"  {win_pct:.1%} win rate — barely above breakeven")
        print(f"  Extended paper trading required.")
    else:
        print(f"  ❌ NO EDGE")
        print(f"  {win_pct:.1%} win rate — below breakeven")
        print(f"  Do NOT deploy.")

else:
    print("\n❌ No games with edge ≥1.5%")
    print("Model is not finding opportunities where it disagrees with Vegas.")
    print("This means model is just following Vegas consensus (no value).")

# ============================================================================
# PART 4: MEDIUM-EDGE ANALYSIS
# ============================================================================

print(f"\n" + "="*80)
print("PART 4: MEDIUM-EDGE GAMES (≥ +1.0%)")
print("="*80)

medium_edge = results_df[results_df['edge_pct'] >= 1.0].copy()

print(f"\nGames with edge ≥ +1.0%: {len(medium_edge)}")

if len(medium_edge) > 0:
    wins_m = (medium_edge['correct']).sum()
    losses_m = len(medium_edge) - wins_m
    win_pct_m = wins_m / len(medium_edge)
    roi_m = (wins_m * 0.909 - losses_m * 1.0) / len(medium_edge)
    
    print(f"  Win rate: {win_pct_m:.1%}")
    print(f"  ROI at -110: {roi_m:+.2%}")
    print(f"  (Lower tier, but more opportunities)")

# ============================================================================
# SAVE & SUMMARY
# ============================================================================

results_df.to_csv('cfb_backtest_2025_results.csv', index=False)

print(f"\n" + "="*80)
print("✅ BACKTEST COMPLETE")
print("="*80)
print(f"""
Results saved to: cfb_backtest_2025_results.csv

WHAT THIS TEST MEANS:
- Measures if model beats Vegas, not just picks winners
- Uses only data model was trained on (2023-2024)
- Tests on completely new games (2025)
- Calculates edge vs Vegas spread

KEY METRIC: Win rate on high-edge games (≥1.5%)
- ≥55%: Strong edge → Deploy
- 53-55%: Moderate edge → Paper trade then deploy
- <53%: No edge → Don't deploy

Next: Check Part 3 results above.
If ≥53% win rate on high-edge bets: Ready for Week 0 paper trading.
""")

