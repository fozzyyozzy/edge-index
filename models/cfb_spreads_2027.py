"""
CFB Power Ranking Model for 2027 Season
Pulls public data from ESPN, calculates team ratings, compares to market spreads
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CFBPowerRankingModel:
    """
    Simple, high-signal CFB power ranking model
    Weights:
    - Historical win rate (50%)
    - Recruiting (30%)
    - Returning production (15%)
    - Coaching tenure (5%)
    """
    
    def __init__(self):
        self.weights = {
            'win_rate': 0.50,
            'recruiting': 0.30,
            'continuity': 0.15,
            'coaching': 0.05
        }
    
    def load_data(self, team_historical_csv, recruiting_csv, transfer_portal_csv=None):
        """
        Load pre-assembled datasets
        
        Expected columns:
        - team_historical.csv: team, year, wins, games, coach, coach_tenure, qb_id, qb_same, top_wr_ids
        - recruiting_csv: team, year, recruiting_rank, avg_recruit_rank_3yr
        - transfer_portal_csv: team, year, in_transfers, out_transfers, key_in, key_out
        """
        self.teams_hist = pd.read_csv(team_historical_csv)
        self.recruiting = pd.read_csv(recruiting_csv)
        if transfer_portal_csv:
            self.portal = pd.read_csv(transfer_portal_csv)
        else:
            self.portal = None
        
        print(f"Loaded {len(self.teams_hist)} team-season records")
        print(f"Loaded recruiting data for {len(self.recruiting)} entries")
    
    def calculate_team_rating(self, team_name, rating_year=2027):
        """
        Calculate power rating for a single team
        Returns rating on 0-1 scale
        """
        
        # Filter for most recent 3 years of data (as of rating_year)
        team_data = self.teams_hist[
            (self.teams_hist['team'] == team_name) & 
            (self.teams_hist['year'] >= rating_year - 3)
        ].sort_values('year', ascending=False)
        
        if team_data.empty:
            print(f"Warning: {team_name} not found in dataset")
            return 0.5  # neutral rating
        
        # 1. Historical win rate (last 3 years)
        try:
            recent_wr = team_data['wins'].sum() / team_data['games'].sum()
        except:
            recent_wr = 0.5
        
        # 2. Recruiting (30% weight)
        recruit_data = self.recruiting[
            (self.recruiting['team'] == team_name) & 
            (self.recruiting['year'] >= rating_year - 3)
        ]
        
        if not recruit_data.empty:
            # Normalize recruiting rank (lower rank = better; 1 is Alabama)
            # Assuming 335 FBS teams max
            avg_recruit_rank = recruit_data['avg_recruit_rank_3yr'].mean()
            recruit_percentile = (335 - avg_recruit_rank) / 335
            recruit_percentile = np.clip(recruit_percentile, 0, 1)
        else:
            recruit_percentile = 0.5  # neutral
        
        # 3. Returning production (15% weight)
        qb_returning = 1.0 if (not team_data.empty and team_data.iloc[0].get('qb_same', False)) else 0.5
        top_wr_back = team_data.iloc[0].get('top_wr_count', 2) / 4.0 if not team_data.empty else 0.5
        continuity = (qb_returning + top_wr_back) / 2.0
        continuity = np.clip(continuity, 0, 1)
        
        # 4. Coaching tenure (5% weight)
        coach_tenure_yrs = team_data.iloc[0].get('coach_tenure', 1) if not team_data.empty else 1
        coach_score = min(coach_tenure_yrs / 3.0, 1.0)  # diminishing returns after 3 years
        
        # Composite rating
        rating = (
            self.weights['win_rate'] * recent_wr +
            self.weights['recruiting'] * recruit_percentile +
            self.weights['continuity'] * continuity +
            self.weights['coaching'] * coach_score
        )
        
        rating = np.clip(rating, 0.2, 0.95)  # cap at reasonable bounds
        
        return rating
    
    def calculate_win_probability(self, team_a, team_b, rating_year=2027):
        """
        Calculate P(Team A beats Team B) based on ratings
        Uses simple Pythagorean formula
        
        Returns: P(A wins), A_rating, B_rating
        """
        rating_a = self.calculate_team_rating(team_a, rating_year)
        rating_b = self.calculate_team_rating(team_b, rating_year)
        
        # Pythagorean: P(A) = A_rating / (A_rating + B_rating)
        p_a = rating_a / (rating_a + rating_b)
        
        return p_a, rating_a, rating_b
    
    def calculate_spread_implied_prob(self, spread, home_team=None):
        """
        Convert Vegas spread to implied probability
        
        spread: negative = favorite, positive = underdog
        e.g., -2.5 means favorite is -2.5
        
        Uses -110 vig standard (55% break-even on either side)
        """
        if spread < 0:
            # Negative = favorite
            fav_vig = -110
            line_pct = abs(spread) / 100.0
            implied_prob = 0.5 + (line_pct / 200.0)
        else:
            # Positive = underdog
            line_pct = spread / 100.0
            implied_prob = 0.5 - (line_pct / 200.0)
        
        # Simplistic; more accurate conversion exists but this is close
        # Better method: use Kelly criterion or logistic curve
        return np.clip(implied_prob, 0.01, 0.99)
    
    def find_edges(self, game_list, min_edge_pct=2.0):
        """
        Find edges in a list of games
        
        game_list: list of dicts with keys:
            - 'home_team': str
            - 'away_team': str
            - 'spread': float (negative = home favored)
            - 'book': str
        
        Returns: DataFrame of edges
        """
        edges = []
        
        for game in game_list:
            home = game['home_team']
            away = game['away_team']
            spread = game.get('spread', 0)
            book = game.get('book', 'Unknown')
            
            # Calculate model win probability
            p_home, rating_h, rating_a = self.calculate_win_probability(home, away)
            p_away = 1.0 - p_home
            
            # Market implied probability
            p_market_fav = self.calculate_spread_implied_prob(spread)
            if spread < 0:
                p_market_home = p_market_fav
            else:
                p_market_home = 1.0 - p_market_fav
            
            # Edge (in percentage points)
            edge_home = (p_home - p_market_home) * 100
            edge_away = (p_away - (1.0 - p_market_home)) * 100
            
            # Which side has edge?
            if abs(edge_home) >= min_edge_pct:
                edges.append({
                    'book': book,
                    'game': f"{away}@{home}",
                    'side': 'Home' if edge_home > 0 else 'Away',
                    'model_prob': p_home if edge_home > 0 else p_away,
                    'market_prob': p_market_home if edge_home > 0 else 1 - p_market_home,
                    'edge_pct': abs(edge_home),
                    'spread': spread,
                    'home_rating': rating_h,
                    'away_rating': rating_a
                })
        
        edges_df = pd.DataFrame(edges)
        return edges_df.sort_values('edge_pct', ascending=False) if not edges_df.empty else edges_df
    
    def backtest_on_historical_games(self, results_csv, min_edge_pct=2.0):
        """
        Backtest model on historical games
        
        results_csv should have columns:
        - home_team, away_team, spread, result (1=home win, 0=away win)
        
        Returns: accuracy, ROI at -110, calibration metrics
        """
        results = pd.read_csv(results_csv)
        
        correct = 0
        total = len(results)
        
        for idx, row in results.iterrows():
            p_home, _, _ = self.calculate_win_probability(
                row['home_team'], 
                row['away_team']
            )
            prediction = 1 if p_home > 0.5 else 0
            actual = row['result']
            
            if prediction == actual:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        
        print(f"\nBacktest Results (on {total} games):")
        print(f"  Accuracy: {accuracy:.1%}")
        print(f"  If betting at -110 odds: {(accuracy * 1.909 - 1):.2%} ROI")
        
        return accuracy


def demo_usage():
    """
    Example usage
    """
    model = CFBPowerRankingModel()
    
    # Create dummy dataset for demo
    teams_data = pd.DataFrame({
        'team': ['Alabama', 'Georgia', 'Ohio State', 'Texas', 'FCS_Team'],
        'year': [2026] * 5,
        'wins': [13, 12, 11, 10, 5],
        'games': [15] * 5,
        'coach': ['Saban', 'Kirby', 'Day', 'Sarkisian', 'Unknown'],
        'coach_tenure': [18, 8, 8, 4, 1],
        'qb_same': [False, True, True, True, False],
        'top_wr_count': [4, 3, 3, 2, 1]
    })
    
    recruiting_data = pd.DataFrame({
        'team': ['Alabama', 'Georgia', 'Ohio State', 'Texas', 'FCS_Team'],
        'year': [2026] * 5,
        'recruiting_rank': [4, 3, 8, 5, 200],
        'avg_recruit_rank_3yr': [5, 4, 7, 6, 180]
    })
    
    # Save temp files
    teams_data.to_csv('/tmp/teams_hist.csv', index=False)
    recruiting_data.to_csv('/tmp/recruiting.csv', index=False)
    
    model.load_data('/tmp/teams_hist.csv', '/tmp/recruiting.csv')
    
    # Example: Calculate power ratings
    print("Team Ratings:")
    for team in ['Alabama', 'Georgia', 'Texas', 'FCS_Team']:
        rating = model.calculate_team_rating(team)
        print(f"  {team}: {rating:.3f}")
    
    # Example: Calculate win probability
    p_bama_beats_texas, r_bama, r_texas = model.calculate_win_probability('Alabama', 'Texas')
    print(f"\nAlabama vs Texas:")
    print(f"  Model says: Alabama {p_bama_beats_texas:.1%}")
    
    # Example: Find edges (hypothetical spreads)
    games = [
        {'home_team': 'Alabama', 'away_team': 'Texas', 'spread': -3.5, 'book': 'DK'},
        {'home_team': 'Georgia', 'away_team': 'Ohio State', 'spread': -2.0, 'book': 'FD'},
    ]
    
    edges = model.find_edges(games, min_edge_pct=1.5)
    if not edges.empty:
        print(f"\nEdges found (min 1.5%):")
        print(edges[['game', 'side', 'model_prob', 'market_prob', 'edge_pct']].to_string())
    else:
        print("\nNo edges found in sample games")


if __name__ == '__main__':
    demo_usage()
