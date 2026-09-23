"""
Weekly Performance Tracker for August Paper Trading
Ingests daily tracking CSV and computes aggregate stats
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

class WeeklyPerformanceTracker:
    
    def __init__(self, tracking_csv_path):
        """
        Load paper trading CSV
        Expected columns:
        - Date, Book, Game, Player, Market, Side, Price_Taken, Model_Edge_Pct, 
        - Hours_Before_Kickoff, Result, Units_Returned, Close_Price_Same_Side, 
        - Close_Price_Opp_Side, Actual_CLV_Pct, Tier
        """
        self.df = pd.read_csv(tracking_csv_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Units_Returned'] = pd.to_numeric(self.df['Units_Returned'], errors='coerce')
        self.df['Result'] = self.df['Result'].fillna('pending')
        
        # Assume 1 unit per bet (update if tracking variable bet sizes)
        self.df['Stake'] = 1.0
        self.df['Profit'] = self.df.apply(
            lambda row: row['Units_Returned'] if row['Result'] in ['win', 'loss'] else np.nan,
            axis=1
        )
    
    def aggregate_by_week(self):
        """
        Group by calendar week and compute aggregate stats
        """
        self.df['Week'] = self.df['Date'].dt.isocalendar().week
        
        weekly_stats = []
        
        for week in sorted(self.df['Week'].unique()):
            week_data = self.df[self.df['Week'] == week]
            
            # Skip incomplete/pending week
            if week_data['Result'].eq('pending').any() and week_data['Result'].ne('pending').sum() < 10:
                continue
            
            completed = week_data[week_data['Result'].isin(['win', 'loss'])]
            
            wins = (completed['Result'] == 'win').sum()
            losses = (completed['Result'] == 'loss').sum()
            total = len(completed)
            
            roi = completed['Profit'].sum() / completed['Stake'].sum() if completed['Stake'].sum() > 0 else 0
            win_pct = wins / total if total > 0 else 0
            
            weekly_stats.append({
                'week': week,
                'bets': total,
                'wins': wins,
                'losses': losses,
                'win_pct': win_pct,
                'profit': completed['Profit'].sum(),
                'stake': completed['Stake'].sum(),
                'roi': roi,
                'avg_edge_pct': week_data['Model_Edge_Pct'].mean(),
                'avg_clv': completed['Actual_CLV_Pct'].mean() if 'Actual_CLV_Pct' in completed.columns else np.nan
            })
        
        return pd.DataFrame(weekly_stats)
    
    def analyze_by_market(self):
        """
        Break down performance by market type (rec_yds, pass_yds, spread, etc.)
        """
        completed = self.df[self.df['Result'].isin(['win', 'loss'])]
        
        market_stats = completed.groupby('Market').agg({
            'Result': 'count',
            'Profit': ['sum', 'mean'],
            'Stake': 'sum'
        }).round(4)
        
        market_stats.columns = ['bets', 'profit', 'avg_profit_per_bet', 'total_stake']
        market_stats['win_pct'] = (completed.groupby('Market')['Result'].apply(lambda x: (x == 'win').sum()) / 
                                   completed.groupby('Market')['Result'].count()).values
        market_stats['roi'] = market_stats['profit'] / market_stats['total_stake']
        
        return market_stats.sort_values('roi', ascending=False)
    
    def analyze_by_book(self):
        """
        Which book had the sharpest openers? Which had the best lines for you?
        """
        completed = self.df[self.df['Result'].isin(['win', 'loss'])]
        
        book_stats = completed.groupby('Book').agg({
            'Result': 'count',
            'Profit': 'sum',
            'Stake': 'sum',
            'Price_Taken': 'mean'
        }).round(4)
        
        book_stats.columns = ['bets', 'profit', 'stake', 'avg_price_taken']
        book_stats['win_pct'] = (completed.groupby('Book')['Result'].apply(lambda x: (x == 'win').sum()) / 
                                 completed.groupby('Book')['Result'].count()).values
        book_stats['roi'] = book_stats['profit'] / book_stats['stake']
        
        return book_stats.sort_values('roi', ascending=False)
    
    def analyze_by_timing(self):
        """
        Which placement timing (hours before kickoff) captured the most CLV?
        Critical finding from 2026 audit: 48-96h window was +2.1%, <12h was -6.0%
        """
        completed = self.df[self.df['Result'].isin(['win', 'loss'])].copy()
        
        # Bucket into timing windows
        def timing_bucket(hours):
            if hours < 12:
                return '0-12h'
            elif hours < 24:
                return '12-24h'
            elif hours < 48:
                return '24-48h'
            elif hours < 72:
                return '48-72h'
            elif hours < 96:
                return '72-96h'
            else:
                return '96h+'
        
        completed['timing_bucket'] = completed['Hours_Before_Kickoff'].apply(timing_bucket)
        
        timing_stats = completed.groupby('timing_bucket', sort=False).agg({
            'Result': 'count',
            'Profit': 'sum',
            'Stake': 'sum',
            'Actual_CLV_Pct': 'mean'
        }).round(4)
        
        timing_stats.columns = ['bets', 'profit', 'stake', 'avg_clv_captured']
        timing_stats['win_pct'] = (completed.groupby('timing_bucket', sort=False)['Result'].apply(lambda x: (x == 'win').sum()) / 
                                   completed.groupby('timing_bucket', sort=False)['Result'].count()).values
        timing_stats['roi'] = timing_stats['profit'] / timing_stats['stake']
        
        return timing_stats
    
    def analyze_by_tier(self):
        """
        Did Tier 1 (edge >= +2%) outperform Tier 2 (+1.5-2%) and Tier 3 (+1-1.5%)?
        """
        completed = self.df[self.df['Result'].isin(['win', 'loss'])]
        
        tier_stats = completed.groupby('Tier').agg({
            'Result': 'count',
            'Profit': 'sum',
            'Stake': 'sum'
        }).round(4)
        
        tier_stats.columns = ['bets', 'profit', 'stake']
        tier_stats['win_pct'] = (completed.groupby('Tier')['Result'].apply(lambda x: (x == 'win').sum()) / 
                                completed.groupby('Tier')['Result'].count()).values
        tier_stats['roi'] = tier_stats['profit'] / tier_stats['stake']
        
        return tier_stats
    
    def generate_weekly_report(self, week_number=None):
        """
        Generate a full report for a specific week or most recent completed week
        """
        if week_number is None:
            # Get most recent week with results
            completed = self.df[self.df['Result'].isin(['win', 'loss'])]
            if completed.empty:
                print("No completed bets yet")
                return
            week_number = completed['Date'].dt.isocalendar().week.max()
        
        week_data = self.df[self.df['Date'].dt.isocalendar().week == week_number]
        completed = week_data[week_data['Result'].isin(['win', 'loss'])]
        
        if completed.empty:
            print(f"Week {week_number}: No results yet")
            return
        
        wins = (completed['Result'] == 'win').sum()
        losses = (completed['Result'] == 'loss').sum()
        total = len(completed)
        
        profit = completed['Profit'].sum()
        stake = completed['Stake'].sum()
        roi = profit / stake if stake > 0 else 0
        win_pct = wins / total if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"WEEK {week_number} SUMMARY")
        print(f"{'='*70}")
        print(f"Bets: {total} ({wins}W-{losses}L)")
        print(f"Win%: {win_pct:.2%}")
        print(f"Profit: {profit:+.2f} units on {stake:.2f} wagered")
        print(f"ROI: {roi:+.2%}")
        print(f"Avg model edge: {week_data['Model_Edge_Pct'].mean():+.2f}%")
        print(f"Avg actual CLV: {completed['Actual_CLV_Pct'].mean():+.2f}%")
        
        print(f"\n{'By Market:':<20} {'Bets':<8} {'ROI':<12} {'Win%':<10}")
        market_breakdown = completed.groupby('Market').agg({
            'Result': 'count',
            'Profit': 'sum',
            'Stake': 'sum'
        })
        
        for market, row in market_breakdown.iterrows():
            bets = row['Result']
            wins_m = (completed[completed['Market'] == market]['Result'] == 'win').sum()
            roi_m = row['Profit'] / row['Stake'] if row['Stake'] > 0 else 0
            win_pct_m = wins_m / bets if bets > 0 else 0
            print(f"{market:<20} {bets:<8} {roi_m:+.2%}       {win_pct_m:.2%}")
        
        print(f"\n{'By Book:':<20} {'Bets':<8} {'ROI':<12} {'Win%':<10}")
        book_breakdown = completed.groupby('Book').agg({
            'Result': 'count',
            'Profit': 'sum',
            'Stake': 'sum'
        })
        
        for book, row in book_breakdown.iterrows():
            bets = row['Result']
            wins_b = (completed[completed['Book'] == book]['Result'] == 'win').sum()
            roi_b = row['Profit'] / row['Stake'] if row['Stake'] > 0 else 0
            win_pct_b = wins_b / bets if bets > 0 else 0
            print(f"{book:<20} {bets:<8} {roi_b:+.2%}       {win_pct_b:.2%}")
        
        print(f"\n{'Placement Timing:':<20} {'Bets':<8} {'ROI':<12} {'Avg CLV':<10}")
        
        completed_with_timing = completed.copy()
        def timing_bucket(hours):
            if hours < 12:
                return '0-12h'
            elif hours < 24:
                return '12-24h'
            elif hours < 48:
                return '24-48h'
            elif hours < 72:
                return '48-72h'
            elif hours < 96:
                return '72-96h'
            else:
                return '96h+'
        
        completed_with_timing['timing_bucket'] = completed_with_timing['Hours_Before_Kickoff'].apply(timing_bucket)
        timing_breakdown = completed_with_timing.groupby('timing_bucket', sort=False).agg({
            'Result': 'count',
            'Profit': 'sum',
            'Stake': 'sum',
            'Actual_CLV_Pct': 'mean'
        })
        
        for timing, row in timing_breakdown.iterrows():
            bets = row['Result']
            roi_t = row['Profit'] / row['Stake'] if row['Stake'] > 0 else 0
            avg_clv = row['Actual_CLV_Pct']
            print(f"{timing:<20} {bets:<8} {roi_t:+.2%}       {avg_clv:+.2f}%")
        
        print(f"\n{'='*70}")
    
    def generate_season_summary(self):
        """
        Overall summary across all completed weeks
        """
        weekly = self.aggregate_by_week()
        
        if weekly.empty:
            print("No completed weeks yet")
            return
        
        total_bets = weekly['bets'].sum()
        total_wins = weekly['wins'].sum()
        total_profit = weekly['profit'].sum()
        total_stake = weekly['stake'].sum()
        overall_roi = total_profit / total_stake if total_stake > 0 else 0
        overall_win_pct = total_wins / total_bets if total_bets > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"AUGUST PAPER TRADING SUMMARY")
        print(f"{'='*70}")
        print(f"Total bets: {total_bets}")
        print(f"Total wins: {total_wins} ({overall_win_pct:.2%})")
        print(f"Total profit: {total_profit:+.2f} units on {total_stake:.2f} wagered")
        print(f"Overall ROI: {overall_roi:+.2%}")
        print(f"\nWeekly breakdown:")
        print(weekly[['bets', 'win_pct', 'profit', 'roi']].to_string())
        print(f"\n{'='*70}")


def demo():
    """
    Example usage
    """
    # Create sample tracking data
    dates = pd.date_range('2027-08-01', periods=30, freq='D')
    sample_bets = []
    
    for i, date in enumerate(dates):
        for j in range(3):  # 3 bets per day
            sample_bets.append({
                'Date': date,
                'Book': ['DraftKings', 'FanDuel', 'BetMGM'][j % 3],
                'Game': f'Game_{i}_{j}',
                'Player': f'Player_{i}_{j}',
                'Market': ['rec_yds', 'receptions', 'pass_att', 'pass_yds'][j % 4],
                'Side': 'over' if j % 2 == 0 else 'under',
                'Price_Taken': -110 if j % 2 == 0 else 105,
                'Model_Edge_Pct': np.random.uniform(1.0, 3.0),
                'Hours_Before_Kickoff': np.random.uniform(12, 96),
                'Result': np.random.choice(['win', 'loss'], p=[0.53, 0.47]),
                'Units_Returned': np.random.choice([0.8, 1.05], p=[0.47, 0.53]),
                'Close_Price_Same_Side': -115,
                'Close_Price_Opp_Side': 100,
                'Actual_CLV_Pct': np.random.uniform(-5, 5),
                'Tier': np.random.choice(['Tier1', 'Tier2'], p=[0.6, 0.4])
            })
    
    sample_df = pd.DataFrame(sample_bets)
    sample_df.to_csv('/tmp/sample_paper_trading.csv', index=False)
    
    # Initialize tracker
    tracker = WeeklyPerformanceTracker('/tmp/sample_paper_trading.csv')
    
    # Generate reports
    tracker.generate_season_summary()
    
    # Most recent week
    tracker.generate_weekly_report()
    
    # Detailed breakdowns
    print("\n\nBY MARKET:")
    print(tracker.analyze_by_market())
    
    print("\n\nBY BOOK:")
    print(tracker.analyze_by_book())
    
    print("\n\nBY TIMING:")
    print(tracker.analyze_by_timing())
    
    print("\n\nBY TIER:")
    print(tracker.analyze_by_tier())


if __name__ == '__main__':
    demo()
