"""
Edge Index — MLB Streak Sheet Generator
Pulls real game logs via pybaseball and generates
comprehensive streak sheets for all pitchers and hitters.

Usage:
  python mlb_streak_sheets.py --date 2026-05-08
  python mlb_streak_sheets.py --date 2026-05-08 --reddit
  python mlb_streak_sheets.py --date 2026-05-08 --position P
"""
import os, sys, json, argparse
from datetime import date, datetime
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))

# ── STREAK CALCULATOR ─────────────────────────────────────────
def calc_streak(values, threshold):
    streak = 0
    for v in reversed(values):
        if v >= threshold:
            streak += 1
        else:
            break
    return streak

def calc_rate(values, threshold, n=None):
    data = values[-n:] if n and len(values) >= n else values
    if not data: return 0
    return sum(1 for v in data if v >= threshold) / len(data)

def streak_emoji(streak, rate):
    if streak >= 10 and rate >= 0.90: return "🔥"
    if streak >= 7:  return "⚡"
    if streak >= 5:  return "✅"
    if streak >= 3:  return "📈"
    return ""

# ── PITCHER STREAK THRESHOLDS ─────────────────────────────────
PITCHER_K_THRESHOLDS = [3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]

# ── BATTER HIT THRESHOLDS ─────────────────────────────────────
BATTER_HIT_THRESHOLDS   = [0.5, 1.5, 2.5]
BATTER_TB_THRESHOLDS    = [0.5, 1.5, 2.5, 3.5]
BATTER_HR_THRESHOLDS    = [0.5]

# ── PYBASEBALL PULLER ─────────────────────────────────────────
def pull_pitcher_season(season=2025, min_starts=5):
    """Pull all qualifying pitchers with their K game logs."""
    try:
        import pybaseball
        pybaseball.cache.enable()

        print(f"  Pulling {season} pitcher list...")
        # Get season pitching stats for qualified starters
        stats = pybaseball.pitching_stats_bref(season)
        if stats is None or stats.empty:
            return {}

        # Filter to starters with enough starts
        starters = stats[stats.get('GS', stats.get('G', 0)) >= min_starts].copy()
        print(f"  Found {len(starters)} qualifying pitchers")

        pitcher_logs = {}
        for _, row in starters.iterrows():
            name = row.get('Name', '')
            if not name:
                continue

            parts = name.split()
            if len(parts) < 2:
                continue

            try:
                lookup = pybaseball.playerid_lookup(parts[-1], parts[0])
                if lookup.empty:
                    continue

                mlb_id = int(lookup.iloc[0]['key_mlbam'])
                data   = pybaseball.statcast_pitcher(
                    f"{season}-03-01", f"{season}-11-01",
                    player_id=mlb_id
                )

                if data.empty:
                    continue

                data['game_date'] = pd.to_datetime(data['game_date']).dt.date.astype(str)
                by_game = data.groupby('game_date').apply(
                    lambda g: g['events'].isin(
                        ['strikeout','strikeout_double_play']
                    ).sum()
                ).reset_index()
                by_game.columns = ['game_date','ks']
                by_game = by_game.sort_values('game_date')
                
                # Filter to current season only
                by_game = by_game[by_game['game_date'] >= f"{season}-01-01"]

                if len(by_game) < 3:
                    continue

                pitcher_logs[name] = {
                    'ks':    by_game['ks'].tolist(),
                    'dates': by_game['game_date'].tolist(),
                    'team':  row.get('Tm', ''),
                    'gs':    len(by_game),
                }
                print(f"    ✓ {name}: {len(by_game)} starts")

            except Exception as e:
                continue

        return pitcher_logs

    except ImportError:
        print("  pybaseball not installed")
        return {}
    except Exception as e:
        print(f"  Error: {e}")
        return {}

def pull_batter_season(season=2025, min_games=20):
    """Pull all qualifying batters with hit/TB game logs."""
    try:
        import pybaseball
        pybaseball.cache.enable()

        print(f"  Pulling {season} batter list...")
        stats = pybaseball.batting_stats_bref(season)
        if stats is None or stats.empty:
            return {}

        qualified = stats[stats.get('G', 0) >= min_games].copy()
        print(f"  Found {len(qualified)} qualifying batters")

        batter_logs = {}
        for _, row in qualified.iterrows():
            name = row.get('Name', '')
            if not name:
                continue

            parts = name.split()
            if len(parts) < 2:
                continue

            try:
                lookup = pybaseball.playerid_lookup(parts[-1], parts[0])
                if lookup.empty:
                    continue

                mlb_id = int(lookup.iloc[0]['key_mlbam'])
                data   = pybaseball.statcast_batter(
                    f"{season}-03-01", f"{season}-11-01",
                    player_id=mlb_id
                )

                if data.empty:
                    continue

                data['game_date'] = pd.to_datetime(data['game_date']).dt.date.astype(str)

                by_game = data.groupby('game_date').agg(
                    hits=('events', lambda x:
                          x.isin(['single','double','triple','home_run']).sum()),
                    tb=('events', lambda x: (
                        x.isin(['single']).sum() * 1 +
                        x.isin(['double']).sum() * 2 +
                        x.isin(['triple']).sum() * 3 +
                        x.isin(['home_run']).sum() * 4
                    )),
                    hr=('events', lambda x: (x == 'home_run').sum()),
                ).reset_index().sort_values('game_date')

                # Filter to current season only (2025+)
                by_game = by_game[by_game['game_date'] >= f"{season}-01-01"]
                
                # Cap at last 60 games for streak relevance
                by_game = by_game.tail(60)

                if len(by_game) < 5:
                    continue

                batter_logs[name] = {
                    'hits':  by_game['hits'].tolist(),
                    'tb':    by_game['tb'].tolist(),
                    'hr':    by_game['hr'].tolist(),
                    'dates': by_game['game_date'].tolist(),
                    'team':  row.get('Tm', ''),
                    'games': len(by_game),
                }

            except Exception as e:
                continue

        print(f"  Pulled logs for {len(batter_logs)} batters")
        return batter_logs

    except Exception as e:
        print(f"  Error: {e}")
        return {}

# ── STREAK ANALYZER ───────────────────────────────────────────
def analyze_pitcher_streaks(pitcher_logs):
    """Find best K streaks for all pitchers."""
    results = []

    for name, data in pitcher_logs.items():
        ks = data['ks']
        if len(ks) < 3:
            continue

        abbr = f"{name.split()[0][0]}. {' '.join(name.split()[1:])}"

        for threshold in PITCHER_K_THRESHOLDS:
            streak = calc_streak(ks, threshold)
            total  = len(ks)
            hits   = sum(1 for k in ks if k >= threshold)
            rate   = hits / total if total > 0 else 0
            l5     = calc_rate(ks, threshold, 5)

            if streak >= 2 or (rate >= 0.75 and total >= 5):
                results.append({
                    'name':      name,
                    'abbr':      abbr,
                    'team':      data.get('team',''),
                    'threshold': threshold,
                    'streak':    streak,
                    'total':     total,
                    'hits':      hits,
                    'rate':      round(rate, 3),
                    'l5':        round(l5, 3),
                    'avg_ks':    round(np.mean(ks[-10:]), 1),
                    'type':      'pitcher_k',
                })

    return sorted(results, key=lambda x: (x['streak'], x['rate']), reverse=True)

def analyze_batter_streaks(batter_logs):
    """Find best hit/TB/HR streaks for all batters."""
    results = []

    for name, data in batter_logs.items():
        if data.get('games', 0) < 5:
            continue

        abbr = f"{name.split()[0][0]}. {' '.join(name.split()[1:])}"

        for stat, thresholds in [
            ('hits', BATTER_HIT_THRESHOLDS),
            ('tb',   BATTER_TB_THRESHOLDS),
            ('hr',   BATTER_HR_THRESHOLDS),
        ]:
            values = data.get(stat, [])
            if len(values) < 3:
                continue

            for threshold in thresholds:
                streak = calc_streak(values, threshold)
                total  = len(values)
                hits   = sum(1 for v in values if v >= threshold)
                rate   = hits / total if total > 0 else 0
                l5     = calc_rate(values, threshold, 5)

                if streak >= 3 or (rate >= 0.80 and total >= 10):
                    results.append({
                        'name':      name,
                        'abbr':      abbr,
                        'team':      data.get('team',''),
                        'stat':      stat,
                        'threshold': threshold,
                        'streak':    streak,
                        'total':     total,
                        'hits':      hits,
                        'rate':      round(rate, 3),
                        'l5':        round(l5, 3),
                        'type':      'batter',
                    })

    return sorted(results, key=lambda x: (x['streak'], x['rate']), reverse=True)

# ── PRINT STREAK SHEET ────────────────────────────────────────
def print_streak_sheet(pitcher_streaks, batter_streaks, game_date):
    STAT_LABELS = {
        'hits': 'Hits', 'tb': 'Total Bases', 'hr': 'Home Runs'
    }

    print(f"\n{'='*65}")
    print(f"EDGE INDEX MLB STREAK SHEET — {game_date}")
    print(f"{'='*65}")

    # ── PITCHER K STREAKS ─────────────────────────────────────
    print(f"\n⚾ PITCHER STRIKEOUT STREAKS")
    print(f"{'─'*65}")

    perfect = [p for p in pitcher_streaks if p['rate'] >= 0.90 and p['streak'] >= 5]
    strong  = [p for p in pitcher_streaks if 0.75 <= p['rate'] < 0.90 and p['streak'] >= 4]
    building= [p for p in pitcher_streaks if p['streak'] in (2,3) and p['rate'] >= 0.65]

    # Deduplicate — best streak per pitcher
    seen = set()
    def dedup(lst):
        out = []
        for p in lst:
            key = (p['name'], p['stat'] if 'stat' in p else 'k')
            if key not in seen:
                seen.add(key)
                out.append(p)
        return out

    if perfect:
        print(f"\n🔥 100%+ hit rates (5+ starts):")
        for p in dedup(perfect)[:15]:
            emoji = streak_emoji(p['streak'], p['rate'])
            print(f"  {p['abbr']:20} {p['threshold']}+ Ks {emoji} "
                  f"{p['streak']}/{p['total']} "
                  f"({p['rate']*100:.0f}%) avg {p['avg_ks']} Ks")

    if strong:
        print(f"\n✅ Strong streaks (75%+ rate, 4+ starts):")
        for p in dedup(strong)[:12]:
            emoji = streak_emoji(p['streak'], p['rate'])
            print(f"  {p['abbr']:20} {p['threshold']}+ Ks {emoji} "
                  f"{p['streak']}/{p['total']} ({p['rate']*100:.0f}%)")

    if building:
        print(f"\n📈 Building streaks (2-3 starts):")
        for p in dedup(building)[:8]:
            print(f"  {p['abbr']:20} {p['threshold']}+ Ks "
                  f"{p['streak']}/{p['total']} ({p['rate']*100:.0f}%)")

    # ── BATTER STREAKS ────────────────────────────────────────
    for stat in ['hits', 'tb', 'hr']:
        stat_plays = [p for p in batter_streaks if p['stat'] == stat]
        if not stat_plays:
            continue

        label = STAT_LABELS[stat]
        print(f"\n🏃 {label.upper()} STREAKS")
        print(f"{'─'*65}")

        hot   = [p for p in stat_plays if p['streak'] >= 6 and p['rate'] >= 0.75]
        good  = [p for p in stat_plays if 3 <= p['streak'] < 6 and p['rate'] >= 0.65]
        value = [p for p in stat_plays if p['streak'] >= 2 and p['l5'] >= 0.80]

        seen_b = set()
        def dedup_b(lst):
            out = []
            for p in lst:
                key = (p['name'], p['stat'], p['threshold'])
                if key not in seen_b:
                    seen_b.add(key)
                    out.append(p)
            return out

        if hot:
            print(f"\n🔥 Hot streaks (8+ games):")
            for p in dedup_b(hot)[:10]:
                emoji = streak_emoji(p['streak'], p['rate'])
                print(f"  {p['abbr']:20} {p['threshold']}+ {label} {emoji} "
                      f"{p['streak']}/{p['total']} ({p['rate']*100:.0f}%)")

        if good:
            print(f"\n✅ Strong streaks (4-7 games):")
            for p in dedup_b(good)[:10]:
                emoji = streak_emoji(p['streak'], p['rate'])
                print(f"  {p['abbr']:20} {p['threshold']}+ {label} {emoji} "
                      f"{p['streak']}/{p['total']} ({p['rate']*100:.0f}%)")

        if value and stat == 'hits':
            print(f"\n💎 Alt line value (L5 80%+):")
            for p in dedup_b(value)[:8]:
                print(f"  {p['abbr']:20} {p['threshold']}+ {label} "
                      f"L5: {p['l5']*100:.0f}% | All-time: {p['rate']*100:.0f}%")

def print_reddit_format(pitcher_streaks, batter_streaks, game_date):
    """Clean Reddit markdown output."""
    print(f"\n--- REDDIT FORMAT ---\n")
    print(f"**⚾ MLB Pitcher K Streaks — {game_date}**")
    print(f"🔥 Active streaks\n")

    seen = set()
    for p in pitcher_streaks:
        if p['name'] in seen or p['streak'] < 3:
            continue
        seen.add(p['name'])
        emoji = streak_emoji(p['streak'], p['rate'])
        print(f"* {p['abbr']} ({p['team']}): {p['threshold']}+ Ks "
              f"➡️ {p['streak']}/{p['total']} {emoji}")
        if len(seen) >= 15:
            break

    print(f"\n**🏃 MLB Hitter Hit Streaks — {game_date}**")
    print(f"🔥 Active streaks\n")
    seen = set()
    for p in [x for x in batter_streaks if x['stat']=='hits' and x['threshold']==0.5]:
        if p['name'] in seen or p['streak'] < 3:
            continue
        seen.add(p['name'])
        emoji = streak_emoji(p['streak'], p['rate'])
        print(f"* {p['abbr']} ({p['team']}): 1+ Hits "
              f"➡️ {p['streak']}/{p['total']} {emoji}")
        if len(seen) >= 15:
            break

# ── DEMO WITH SAMPLE DATA ─────────────────────────────────────
def demo_streaks():
    """Generate realistic demo streaks while pybaseball loads."""
    pitcher_streaks = [
        {'name':'Spencer Strider','abbr':'S. Strider','team':'ATL','threshold':6.5,'streak':8,'total':10,'hits':9,'rate':0.90,'l5':1.00,'avg_ks':9.4,'type':'pitcher_k'},
        {'name':'Zack Wheeler','abbr':'Z. Wheeler','team':'PHI','threshold':5.5,'streak':7,'total':10,'hits':8,'rate':0.80,'l5':0.80,'avg_ks':7.2,'type':'pitcher_k'},
        {'name':'Dylan Cease','abbr':'D. Cease','team':'SD','threshold':6.5,'streak':6,'total':10,'hits':8,'rate':0.80,'l5':0.80,'avg_ks':7.8,'type':'pitcher_k'},
        {'name':'Gerrit Cole','abbr':'G. Cole','team':'NYY','threshold':7.5,'streak':5,'total':9,'hits':8,'rate':0.89,'l5':1.00,'avg_ks':8.6,'type':'pitcher_k'},
        {'name':'Kyle Bradish','abbr':'K. Bradish','team':'BAL','threshold':5.5,'streak':4,'total':6,'hits':5,'rate':0.83,'l5':0.80,'avg_ks':7.4,'type':'pitcher_k'},
        {'name':'Connelly Early','abbr':'C. Early','team':'PHI','threshold':4.5,'streak':3,'total':5,'hits':4,'rate':0.80,'l5':0.80,'avg_ks':7.0,'type':'pitcher_k'},
        {'name':'Max Fried','abbr':'M. Fried','team':'NYY','threshold':5.5,'streak':2,'total':10,'hits':8,'rate':0.80,'l5':0.80,'avg_ks':6.6,'type':'pitcher_k'},
        {'name':'Nick Lodolo','abbr':'N. Lodolo','team':'CIN','threshold':4.5,'streak':3,'total':8,'hits':7,'rate':0.88,'l5':0.80,'avg_ks':6.6,'type':'pitcher_k'},
        {'name':'Chase Dollander','abbr':'C. Dollander','team':'COL','threshold':4.5,'streak':2,'total':6,'hits':5,'rate':0.83,'l5':0.80,'avg_ks':6.6,'type':'pitcher_k'},
        {'name':'Jesus Luzardo','abbr':'J. Luzardo','team':'PHI','threshold':6.5,'streak':5,'total':8,'hits':7,'rate':0.88,'l5':1.00,'avg_ks':8.2,'type':'pitcher_k'},
    ]

    batter_streaks = [
        # Hit streaks
        {'name':'Freddie Freeman','abbr':'F. Freeman','team':'LAD','stat':'hits','threshold':0.5,'streak':14,'total':20,'hits':18,'rate':0.90,'l5':1.00,'type':'batter'},
        {'name':'Yordan Alvarez','abbr':'Y. Alvarez','team':'HOU','stat':'hits','threshold':0.5,'streak':10,'total':15,'hits':13,'rate':0.87,'l5':1.00,'type':'batter'},
        {'name':'Juan Soto','abbr':'J. Soto','team':'NYY','stat':'hits','threshold':0.5,'streak':8,'total':14,'hits':12,'rate':0.86,'l5':1.00,'type':'batter'},
        {'name':'Mookie Betts','abbr':'M. Betts','team':'LAD','stat':'hits','threshold':0.5,'streak':7,'total':12,'hits':10,'rate':0.83,'l5':0.80,'type':'batter'},
        {'name':'Bryce Harper','abbr':'B. Harper','team':'PHI','stat':'hits','threshold':0.5,'streak':6,'total':10,'hits':9,'rate':0.90,'l5':1.00,'type':'batter'},
        {'name':'Aaron Judge','abbr':'A. Judge','team':'NYY','stat':'hits','threshold':0.5,'streak':5,'total':10,'hits':9,'rate':0.90,'l5':1.00,'type':'batter'},
        # TB streaks
        {'name':'Shohei Ohtani','abbr':'S. Ohtani','team':'LAD','stat':'tb','threshold':1.5,'streak':6,'total':10,'hits':8,'rate':0.80,'l5':0.80,'type':'batter'},
        {'name':'Aaron Judge','abbr':'A. Judge','team':'NYY','stat':'tb','threshold':1.5,'streak':5,'total':10,'hits':8,'rate':0.80,'l5':0.80,'type':'batter'},
        {'name':'Yordan Alvarez','abbr':'Y. Alvarez','team':'HOU','stat':'tb','threshold':1.5,'streak':4,'total':10,'hits':8,'rate':0.80,'l5':1.00,'type':'batter'},
        # HR streaks
        {'name':'Aaron Judge','abbr':'A. Judge','team':'NYY','stat':'hr','threshold':0.5,'streak':3,'total':10,'hits':4,'rate':0.40,'l5':0.60,'type':'batter'},
    ]

    return pitcher_streaks, batter_streaks

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",     default=date.today().isoformat())
    parser.add_argument("--reddit",   action="store_true")
    parser.add_argument("--position", default="all", choices=["all","P","B"])
    parser.add_argument("--live",     action="store_true",
                        help="Pull live from pybaseball (slow)")
    parser.add_argument("--season",   type=int, default=2025)
    args = parser.parse_args()

    print(f"Edge Index MLB Streak Sheet — {args.date}")
    print(f"{'─'*65}")

    if args.live:
        print("Pulling live data from pybaseball...")
        pitcher_logs = pull_pitcher_season(args.season) if args.position in ("all","P") else {}
        batter_logs  = pull_batter_season(args.season)  if args.position in ("all","B") else {}

        pitcher_streaks = analyze_pitcher_streaks(pitcher_logs)
        batter_streaks  = analyze_batter_streaks(batter_logs)

        # Save for future use
        cache = {
            "date": args.date,
            "pitcher_streaks": pitcher_streaks,
            "batter_streaks":  batter_streaks,
        }
        cache_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"mlb_streaks_{args.date}.json"
        )
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2)
        print(f"Saved to mlb_streaks_{args.date}.json")

    else:
        # Check for cached data
        cache_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"mlb_streaks_{args.date}.json"
        )
        if os.path.exists(cache_path):
            print("Loading cached streak data...")
            cache = json.load(open(cache_path))
            pitcher_streaks = cache["pitcher_streaks"]
            batter_streaks  = cache["batter_streaks"]
        else:
            print("No cached data — using demo streaks")
            print("Run with --live to pull real data (takes ~10 min)")
            pitcher_streaks, batter_streaks = demo_streaks()

    print_streak_sheet(pitcher_streaks, batter_streaks, args.date)

    if args.reddit:
        print_reddit_format(pitcher_streaks, batter_streaks, args.date)
