import sys
sys.path.insert(0, 'edge-index/models')
from cfb_spreads_2027 import CFBPowerRankingModel

model = CFBPowerRankingModel()
model.load_data('edge-index/data/cfb/team_historical.csv', 
                'edge-index/data/cfb/recruiting_ranks.csv')

# Quick test
for team in ['Alabama', 'Georgia', 'Texas', 'Ohio State']:
    rating = model.calculate_team_rating(team)
    print(f"{team}: {rating:.3f}")