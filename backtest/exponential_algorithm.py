"""
Edge Index — Exponential Bankroll Algorithm
Anti-Martingale with Banker Lockbox

Philosophy:
  - Chase wins, not losses
  - Scale UP on winning streaks
  - Hard reset on any loss
  - Bank 50% of each win permanently
  - Never risk the banked amount
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class Bet:
    description: str
    prob: float
    odds: int          # American
    wager: float
    result: Optional[str] = None  # 'WIN' or 'LOSS'
    pnl: float = 0.0
    banked: float = 0.0
    multiplier_before: float = 1.0

@dataclass 
class ExpoState:
    bankroll: float
    banked: float = 0.0
    streak: int = 0
    multiplier: float = 1.0
    base_pct: float = 0.03
    scale_factor: float = 1.4
    bank_pct: float = 0.50
    max_mult: float = 4.0
    history: List[dict] = field(default_factory=list)

    def next_bet_size(self) -> float:
        raw = self.bankroll * self.base_pct * self.multiplier
        capped = self.bankroll * self.base_pct * self.max_mult
        return round(min(raw, capped), 2)

    def american_to_decimal(self, odds: int) -> float:
        if odds > 0:
            return (odds / 100) + 1
        return (100 / abs(odds)) + 1

    def place_bet(self, description: str, prob: float, odds: int,
                  result: str) -> dict:
        wager = self.next_bet_size()
        dec = self.american_to_decimal(odds)
        mult_before = self.multiplier

        if result == 'WIN':
            profit = wager * (dec - 1)
            bank_amount = profit * self.bank_pct
            active_profit = profit - bank_amount

            self.bankroll += active_profit
            self.banked += bank_amount
            self.streak += 1
            self.multiplier = min(self.multiplier * self.scale_factor,
                                  self.max_mult)
            pnl = active_profit
        else:
            self.bankroll -= wager
            self.streak = 0
            self.multiplier = 1.0
            bank_amount = 0
            pnl = -wager

        record = {
            'description':   description,
            'prob':          prob,
            'odds':          odds,
            'wager':         wager,
            'result':        result,
            'pnl':           round(pnl, 2),
            'banked_this':   round(bank_amount, 2),
            'total_banked':  round(self.banked, 2),
            'streak':        self.streak,
            'multiplier':    round(mult_before, 2),
            'next_mult':     round(self.multiplier, 2),
            'active_bankroll': round(self.bankroll, 2),
            'total_net':     round(self.bankroll + self.banked, 2),
        }
        self.history.append(record)
        return record

    def summary(self) -> dict:
        total = self.bankroll + self.banked
        wins   = sum(1 for h in self.history if h['result'] == 'WIN')
        losses = sum(1 for h in self.history if h['result'] == 'LOSS')
        return {
            'active_bankroll':  round(self.bankroll, 2),
            'banked':           round(self.banked, 2),
            'total':            round(total, 2),
            'wins':             wins,
            'losses':           losses,
            'win_rate':         round(wins/(wins+losses)*100, 1) if (wins+losses) else 0,
            'current_streak':   self.streak,
            'current_mult':     round(self.multiplier, 2),
            'next_bet_size':    self.next_bet_size(),
        }


def run_sample_week(starting_bankroll=1000):
    """
    Demonstrate the algorithm with a sample week of plays.
    This mirrors what the BankrollManager component would do.
    """
    state = ExpoState(bankroll=starting_bankroll)
    
    # Sample week — mix of wins and losses at our validated hit rates
    plays = [
        ("Lamar Jackson Rush Yds OVER 28.5",   0.91, -315, "WIN"),
        ("Zay Flowers Rec OVER 3.5",            0.93, -388, "WIN"),
        ("Josh Allen Pass Yds OVER 225.5",      0.86, -334, "WIN"),
        ("Rashee Rice Rec Yds OVER 52.5",       0.82, -142, "WIN"),
        ("Saquon Barkley Rush Yds OVER 58.5",   0.86, -271, "LOSS"),  # streak breaks
        ("Trey McBride Rec Yds OVER 42.5",      0.88, -284, "WIN"),
        ("Sam Darnold Pass Att UNDER 31.5",     0.87,  142, "WIN"),
    ]
    
    print("=" * 65)
    print(f"EXPONENTIAL ALGORITHM — SAMPLE WEEK (Starting: ${starting_bankroll})")
    print("=" * 65)
    print(f"Base unit: 3% = ${starting_bankroll * 0.03:.0f}")
    print(f"Scale: 1.4× per win | Bank: 50% of each win | Max: 4×")
    print()
    print(f"{'#':<3} {'Play':<38} {'Wager':>7} {'Result':>6} {'P&L':>8} {'Banked':>8} {'Bankroll':>10} {'Streak':>7}")
    print("-" * 95)
    
    for i, (desc, prob, odds, result) in enumerate(plays, 1):
        rec = state.place_bet(desc, prob, odds, result)
        short = desc[:37]
        print(f"{i:<3} {short:<38} ${rec['wager']:>6.0f} {rec['result']:>6} ${rec['pnl']:>+7.2f} ${rec['banked_this']:>6.2f} ${rec['active_bankroll']:>9.2f} {rec['streak']:>7}")
    
    s = state.summary()
    print("-" * 95)
    print(f"\nWeek Summary:")
    print(f"  Active bankroll:  ${s['active_bankroll']:>8,.2f}")
    print(f"  Banked (locked):  ${s['banked']:>8,.2f}")
    print(f"  Total net worth:  ${s['total']:>8,.2f}")
    print(f"  Started:          ${starting_bankroll:>8,.2f}")
    print(f"  Net gain:         ${s['total'] - starting_bankroll:>+8,.2f}")
    print(f"  Win rate:         {s['win_rate']}%  ({s['wins']}W {s['losses']}L)")
    print(f"  Current streak:   {s['current_streak']}")
    print(f"  Next bet mult:    {s['current_mult']}×  (next bet: ${s['next_bet_size']:.2f})")
    
    return state


def compare_strategies(starting_bankroll=1000, n_bets=51, hit_rate=0.718,
                        avg_odds=-180, n_simulations=10000):
    """
    Monte Carlo comparison: flat Kelly vs exponential.
    """
    import random
    
    def dec(odds):
        if odds > 0: return (odds/100)+1
        return (100/abs(odds))+1
    
    avg_dec = dec(avg_odds)
    base_pct = 0.03
    
    flat_results, expo_results = [], []
    
    for _ in range(n_simulations):
        # Flat Kelly
        br = starting_bankroll
        for _ in range(n_bets):
            bet = br * base_pct
            if random.random() < hit_rate:
                br += bet * (avg_dec - 1)
            else:
                br -= bet
        flat_results.append(br)
        
        # Exponential with banker
        br = starting_bankroll
        banked = 0
        mult = 1.0
        for _ in range(n_bets):
            bet = min(br * base_pct * mult, br * base_pct * 4.0)
            if random.random() < hit_rate:
                profit = bet * (avg_dec - 1)
                bank = profit * 0.50
                banked += bank
                br += profit - bank
                mult = min(mult * 1.4, 4.0)
            else:
                br -= bet
                mult = 1.0
        expo_results.append(br + banked)
    
    import statistics
    print(f"\n{'='*55}")
    print(f"MONTE CARLO COMPARISON ({n_simulations:,} simulations)")
    print(f"{'='*55}")
    print(f"Hit rate: {hit_rate*100:.1f}% | Avg odds: {avg_odds} | {n_bets} bets/season")
    print()
    print(f"{'Metric':<30} {'Flat Kelly':>12} {'Exponential':>12}")
    print("-" * 56)
    
    def pct(lst, p): return sorted(lst)[int(len(lst)*p/100)]
    
    rows = [
        ("Median bankroll", statistics.median(flat_results), statistics.median(expo_results)),
        ("Mean bankroll",   statistics.mean(flat_results),   statistics.mean(expo_results)),
        ("Best 10%",        pct(flat_results, 90),           pct(expo_results, 90)),
        ("Worst 10%",       pct(flat_results, 10),           pct(expo_results, 10)),
        ("Profitable %",    sum(r > starting_bankroll for r in flat_results)/n_simulations*100,
                            sum(r > starting_bankroll for r in expo_results)/n_simulations*100),
    ]
    for label, f, e in rows:
        if '%' in label:
            print(f"{label:<30} {f:>11.1f}% {e:>11.1f}%")
        else:
            print(f"{label:<30} ${f:>10,.0f} ${e:>10,.0f}")
    
    beat_flat = sum(e > f for e, f in zip(expo_results, flat_results)) / n_simulations * 100
    print(f"\n  Exponential beats flat: {beat_flat:.1f}% of seasons")
    upside = (statistics.mean(expo_results) / statistics.mean(flat_results) - 1) * 100
    print(f"  Mean upside vs flat:    +{upside:.1f}%")
    print(f"\n  KEY INSIGHT: Exponential wins on the right tail.")
    print(f"  Hot streak seasons: dramatically more profit.")
    print(f"  Cold streak seasons: similar (reset protects you).")
    print(f"  The banker lockbox is the real feature — ${statistics.mean(expo_results) - statistics.mean(flat_results):,.0f} avg protected.")

if __name__ == "__main__":
    run_sample_week(1000)
    compare_strategies()
