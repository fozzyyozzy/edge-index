"""
Edge Index — MLB Streak Sheet Generator
Two modes:
  Daily (fast, ~3 min):  pitchers only + cached batters
  Weekly (slow, ~10 min): full batter refresh

Usage:
  python mlb_streak_sheets.py                    # daily, today
  python mlb_streak_sheets.py --weekly           # full batter refresh
  python mlb_streak_sheets.py --reddit           # reddit format
  python mlb_streak_sheets.py --date 2026-05-09  # specific date
"""
import os, sys, json, argparse
from datetime import date, datetime
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR   = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

PITCHER_CACHE = os.path.join(CACHE_DIR, "pitcher_streaks.json")
BATTER_CACHE  = os.path.join(CACHE_DIR, "batter_streaks.json")
WEEKLY_STAMP  = os.path.join(CACHE_DIR, "weekly_stamp.txt")

# ── PARK FACTORS (K-friendly) ─────────────────────────────────
PARK_K_FACTOR = {
    "San Francisco Giants": 1.06, "Seattle Mariners": 1.05,
    "San Diego Padres": 1.04,     "Oakland Athletics": 1.03,
    "Miami Marlins": 1.02,        "Los Angeles Dodgers": 1.01,
    "Cincinnati Reds": 0.98,      "Colorado Rockies": 0.95,
    "Houston Astros": 0.99,       "New York Yankees": 0.99,
}

# ── STREAK HELPERS ────────────────────────────────────────────
def calc_streak(values, threshold):
    streak = 0
    for v in reversed(values):
        if v >= threshold: streak += 1
        else: break
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

# ── DAILY: PULL TODAY'S PITCHERS ONLY ────────────────────────
def pull_todays_pitchers(game_date, season=2025):
    """
    Pull K logs for only the pitchers starting today.
    Fast — typically 15-20 pitchers max.
    """
    try:
        import pybaseball
        pybaseball.cache.enable()
    except ImportError:
        print("  pybaseball not installed")
        return {}

    # Load today's lines to get today's pitchers
    lines_path = os.path.join(BASE_DIR, f"mlb_lines_{game_date}.json")
    if not os.path.exists(lines_path):
        print(f"  No lines file for {game_date} — run mlb_odds_puller.py first")
        return {}

    with open(lines_path) as f:
        lines_data = json.load(f)

    props = pd.DataFrame(lines_data["props"])
    k_props = props[props["prop"] == "strikeouts"]["player"].unique().tolist()
    print(f"  Today's pitchers: {len(k_props)}")

    import unicodedata
    def normalize(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                      if unicodedata.category(c) != 'Mn').lower()

    pitcher_logs = {}
    for name in k_props:
        parts = name.strip().split()
        if len(parts) < 2:
            continue

        try:
            print(f"    {name}...", end="", flush=True)
            lookup = pybaseball.playerid_lookup(parts[-1], parts[0])
            if lookup.empty:
                lookup = pybaseball.playerid_lookup(
                    normalize(parts[-1]), normalize(parts[0]))
            if lookup.empty:
                print(" no ID")
                continue

            if 'birth_year' in lookup.columns:
                lookup = lookup[lookup['birth_year'] >= 1985]
            if lookup.empty:
                print(" no active player")
                continue

            mlb_id = int(lookup.iloc[0]['key_mlbam'])
            data   = pybaseball.statcast_pitcher(
                f"{season}-03-01", f"{season}-11-01",
                player_id=mlb_id
            )

            if data is None or data.empty:
                print(" no data")
                continue

            data['game_date'] = pd.to_datetime(
                data['game_date']).dt.date.astype(str)
            data = data[data['game_date'] >= f"{season}-01-01"]

            by_game = data.groupby('game_date').apply(
                lambda g: g['events'].isin(
                    ['strikeout','strikeout_double_play']).sum()
            ).reset_index()
            by_game.columns = ['game_date', 'ks']
            by_game = by_game.sort_values('game_date')

            ks = by_game['ks'].tolist()
            print(f" {len(ks)} starts")

            if len(ks) >= 1:
                pitcher_logs[name] = {
                    'ks':    ks,
                    'dates': by_game['game_date'].tolist(),
                    'team':  '',
                    'gs':    len(ks),
                }

        except Exception as e:
            print(f" error: {e}")
            continue

    return pitcher_logs

# ── WEEKLY: FULL BATTER REFRESH ───────────────────────────────
def pull_all_batters_weekly(season=2025, min_games=15):
    """
    Full batter refresh — run Sunday nights.
    Pulls all qualifying batters, saves to weekly cache.
    ~10-15 min runtime.
    """
    try:
        import pybaseball
        pybaseball.cache.enable()
    except ImportError:
        print("  pybaseball not installed")
        return {}

    print(f"  Pulling {season} batter stats list...")
    try:
        stats = pybaseball.batting_stats_bref(season)
    except Exception as e:
        print(f"  Error: {e}")
        return {}

    if stats is None or stats.empty:
        print("  No stats returned")
        return {}

    qualified = stats[stats.get('G', stats.get('AB', 0)/3) >= min_games].copy()
    print(f"  {len(qualified)} qualifying batters — pulling logs...")

    import unicodedata
    def normalize(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                      if unicodedata.category(c) != 'Mn').lower()

    batter_logs = {}
    total = len(qualified)

    for idx, (_, row) in enumerate(qualified.iterrows(), 1):
        name = row.get('Name', '')
        if not name:
            continue

        parts = name.strip().split()
        if len(parts) < 2:
            continue

        try:
            if idx % 25 == 0:
                print(f"  Progress: {idx}/{total} ({idx/total*100:.0f}%)")

            lookup = pybaseball.playerid_lookup(parts[-1], parts[0])
            if lookup.empty:
                lookup = pybaseball.playerid_lookup(
                    normalize(parts[-1]), normalize(parts[0]))
            if lookup.empty:
                continue

            if 'birth_year' in lookup.columns:
                lookup = lookup[lookup['birth_year'] >= 1985]
            if lookup.empty:
                continue

            mlb_id = int(lookup.iloc[0]['key_mlbam'])
            data   = pybaseball.statcast_batter(
                f"{season}-03-01", f"{season}-11-01",
                player_id=mlb_id
            )

            if data is None or data.empty:
                continue

            data['game_date'] = pd.to_datetime(
                data['game_date']).dt.date.astype(str)
            data = data[data['game_date'] >= f"{season}-01-01"]

            by_game = data.groupby('game_date').agg(
                hits=('events', lambda x:
                      x.isin(['single','double','triple','home_run']).sum()),
                tb=('events', lambda x: (
                    x.isin(['single']).sum()    * 1 +
                    x.isin(['double']).sum()    * 2 +
                    x.isin(['triple']).sum()    * 3 +
                    x.isin(['home_run']).sum()  * 4
                )),
                hr=('events', lambda x: (x == 'home_run').sum()),
            ).reset_index().sort_values('game_date')

            # Last 60 games only for streak relevance
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

        except Exception:
            continue

    print(f"  Done — {len(batter_logs)} batters pulled")
    return batter_logs

# ── STREAK ANALYZERS ──────────────────────────────────────────
PITCHER_THRESHOLDS = [3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
BATTER_HIT_THRESH  = [0.5, 1.5, 2.5]
BATTER_TB_THRESH   = [1.5, 2.5, 3.5]

def analyze_pitcher_streaks(pitcher_logs):
    results = []
    for name, data in pitcher_logs.items():
        ks = data['ks']
        if len(ks) < 2:
            continue
        abbr = f"{name.split()[0][0]}. {' '.join(name.split()[1:])}"
        for thresh in PITCHER_THRESHOLDS:
            streak = calc_streak(ks, thresh)
            total  = len(ks)
            hits   = sum(1 for k in ks if k >= thresh)
            rate   = hits / total
            l5     = calc_rate(ks, thresh, 5)
            l5_avg = round(np.mean(ks[-5:]), 1) if len(ks) >= 5 else round(np.mean(ks), 1)
            avg_ks = round(np.mean(ks[-10:]), 1)

            if streak >= 2 or (rate >= 0.70 and total >= 5):
                results.append({
                    'name':      name,
                    'abbr':      abbr,
                    'team':      data.get('team',''),
                    'threshold': thresh,
                    'streak':    streak,
                    'total':     total,
                    'hits':      hits,
                    'rate':      round(rate, 3),
                    'l5':        round(l5, 3),
                    'l5_avg':    l5_avg,
                    'avg_ks':    avg_ks,
                })
    return sorted(results,
                  key=lambda x: (x['streak'], x['rate']), reverse=True)

def analyze_batter_streaks(batter_logs):
    results = []
    for name, data in batter_logs.items():
        if data.get('games', 0) < 5:
            continue
        abbr = f"{name.split()[0][0]}. {' '.join(name.split()[1:])}"
        for stat, thresholds in [
            ('hits', BATTER_HIT_THRESH),
            ('tb',   BATTER_TB_THRESH),
            ('hr',   [0.5]),
        ]:
            values = data.get(stat, [])
            if len(values) < 3:
                continue
            for thresh in thresholds:
                streak = calc_streak(values, thresh)
                total  = len(values)
                hits   = sum(1 for v in values if v >= thresh)
                rate   = hits / total
                l5     = calc_rate(values, thresh, 5)
                if streak >= 3 or (rate >= 0.75 and total >= 10 and l5 >= 0.80):
                    results.append({
                        'name':      name,
                        'abbr':      abbr,
                        'team':      data.get('team',''),
                        'stat':      stat,
                        'threshold': thresh,
                        'streak':    streak,
                        'total':     total,
                        'hits':      hits,
                        'rate':      round(rate, 3),
                        'l5':        round(l5, 3),
                    })
    return sorted(results,
                  key=lambda x: (x['streak'], x['rate']), reverse=True)

# ── PRINT SHEET ───────────────────────────────────────────────
STAT_LABELS = {'hits':'Hits','tb':'Total Bases','hr':'Home Runs'}

def print_sheet(pitcher_streaks, batter_streaks, game_date):
    print(f"\n{'='*65}")
    print(f"EDGE INDEX MLB STREAK SHEET — {game_date}")
    print(f"{'='*65}")

    # ── PITCHERS ──────────────────────────────────────────────
    print(f"\n⚾ PITCHER K STREAKS")
    print(f"{'─'*65}")

    seen = set()
    tiers = [
        ("🔥 Elite (8+ streak OR 95%+ rate):",
         lambda p: p['streak'] >= 8 or p['rate'] >= 0.95),
        ("⚡ Strong (5-7 streak, 80%+ rate):",
         lambda p: 4 <= p['streak'] < 8 and p['rate'] >= 0.80),
        ("✅ Building (2-4 streak, 70%+ rate):",
         lambda p: 2 <= p['streak'] < 5 and p['rate'] >= 0.70),
    ]

    for label, fn in tiers:
        matches = [p for p in pitcher_streaks
                   if fn(p) and p['name'] not in seen]
        # Deduplicate — best threshold per pitcher
        deduped = {}
        for p in matches:
            if p['name'] not in deduped or p['streak'] > deduped[p['name']]['streak']:
                deduped[p['name']] = p
        matches = sorted(deduped.values(),
                         key=lambda x: (x['streak'], x['rate']), reverse=True)
        if not matches:
            continue
        print(f"\n{label}")
        for p in matches[:12]:
            seen.add(p['name'])
            emoji = streak_emoji(p['streak'], p['rate'])
            sample = f"L{p['total']}" if p['total'] < 30 else "season"
            print(f"  {p['abbr']:22} {p['threshold']}+ Ks {emoji} "
                  f"{p['streak']}-start streak | "
                  f"{sample}: {p['rate']*100:.0f}% | "
                  f"avg {p['avg_ks']} Ks")

    # ── BATTERS ───────────────────────────────────────────────
    for stat in ['hits', 'tb', 'hr']:
        plays = [p for p in batter_streaks if p['stat'] == stat]
        if not plays:
            continue
        label = STAT_LABELS[stat]
        print(f"\n🏃 {label.upper()} STREAKS")
        print(f"{'─'*65}")

        seen_b = set()
        # For hits: show both 0.5 (parlay) and 1.5 (meaningful singles)
        # For TB: start at 1.5 — 0.5 TB = same as 1 hit, redundant
        min_thresh = 0.5 if stat == 'hits' else 1.5
        plays = [p for p in plays if p['threshold'] >= min_thresh]

        hot  = [p for p in plays if p['streak'] >= 6]
        good = [p for p in plays if 3 <= p['streak'] < 6 and p['rate'] >= 0.65]
        val  = [p for p in plays if p['l5'] >= 0.80 and p['streak'] >= 2]

        def dedup_b(lst):
            d = {}
            for p in lst:
                key = (p['name'], p['stat'], p['threshold'])
                if key not in d:
                    d[key] = p
            return sorted(d.values(),
                          key=lambda x: (x['streak'], x['rate']), reverse=True)

        if hot:
            print(f"\n🔥 Hot (6+ games):")
            for p in dedup_b(hot)[:10]:
                seen_b.add(p['name'])
                emoji = streak_emoji(p['streak'], p['rate'])
                sample = f"L{p['total']}" if p['total'] < 60 else "L60"
                print(f"  {p['abbr']:22} {p['threshold']}+ {label} {emoji} "
                      f"{p['streak']}-game streak | {sample}: {p['rate']*100:.0f}%")
        if good:
            print(f"\n✅ Strong (3-5 games):")
            for p in dedup_b(good)[:10]:
                emoji = streak_emoji(p['streak'], p['rate'])
                sample = f"L{p['total']}" if p['total'] < 60 else "L60"
                print(f"  {p['abbr']:22} {p['threshold']}+ {label} {emoji} "
                      f"{p['streak']}-game streak | {sample}: {p['rate']*100:.0f}%")
        if stat == 'hits' and val:
            print(f"\n💎 Alt line value (L5 80%+):")
            for p in dedup_b(val)[:8]:
                sample = f"L{p['total']}" if p['total'] < 60 else "L60"
                print(f"  {p['abbr']:22} {p['threshold']}+ {label} "
                      f"L5:{p['l5']*100:.0f}% | {sample}: {p['rate']*100:.0f}%")

def print_reddit(pitcher_streaks, batter_streaks, game_date):
    print(f"\n--- REDDIT FORMAT ---\n")
    print(f"**⚾ Edge Index MLB Streak Sheet — {game_date}**\n")
    print(f"*Pitcher K Streaks*\n")
    seen = set()
    for p in pitcher_streaks:
        if p['name'] in seen or p['streak'] < 3:
            continue
        seen.add(p['name'])
        emoji = streak_emoji(p['streak'], p['rate'])
        print(f"* {p['abbr']} ({p['team']}): "
              f"{p['threshold']}+ Ks ➡️ {p['streak']}-start streak "
              f"({p['rate']*100:.0f}% season) {emoji}")
        if len(seen) >= 15:
            break

    print(f"\n*Hitter Streaks*\n")
    seen = set()
    for p in [x for x in batter_streaks
              if x['stat'] == 'hits' and x['threshold'] == 0.5
              and x['streak'] >= 4]:
        if p['name'] in seen:
            continue
        seen.add(p['name'])
        emoji = streak_emoji(p['streak'], p['rate'])
        print(f"* {p['abbr']} ({p['team']}): "
              f"1+ Hits ➡️ {p['streak']}-game streak "
              f"(L60: {p['rate']*100:.0f}%) {emoji}")
        if len(seen) >= 15:
            break

# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",    default=date.today().isoformat())
    parser.add_argument("--season",  type=int, default=2025)
    parser.add_argument("--weekly",  action="store_true",
                        help="Run full batter refresh (Sunday nights)")
    parser.add_argument("--reddit",  action="store_true")
    args = parser.parse_args()

    print(f"Edge Index MLB Streak Sheet — {args.date}")
    print(f"{'─'*65}")

    # ── WEEKLY MODE ───────────────────────────────────────────
    if args.weekly:
        print("WEEKLY BATTER REFRESH — grab a coffee ☕")
        print("Run Sunday nights, cache lasts all week\n")

        batter_logs = pull_all_batters_weekly(args.season)
        batter_streaks = analyze_batter_streaks(batter_logs)

        with open(BATTER_CACHE, 'w') as f:
            json.dump({
                "updated":        args.date,
                "batter_streaks": batter_streaks,
            }, f, indent=2)

        with open(WEEKLY_STAMP, 'w') as f:
            f.write(args.date)

        print(f"\n✓ Batter cache saved ({len(batter_streaks)} streaks)")
        print(f"  Valid until next Sunday")

    # ── DAILY MODE ────────────────────────────────────────────
    else:
        print("DAILY MODE — today's pitchers + cached batters\n")

        # Today's pitchers (fast)
        print(f"[1] Pulling today's pitchers...")
        pitcher_logs    = pull_todays_pitchers(args.date, args.season)
        pitcher_streaks = analyze_pitcher_streaks(pitcher_logs)

        # Save pitcher cache
        with open(PITCHER_CACHE, 'w') as f:
            json.dump({
                "date":            args.date,
                "pitcher_streaks": pitcher_streaks,
            }, f, indent=2)
        print(f"    {len(pitcher_streaks)} pitcher streaks found")

        # Load batter cache
        print(f"\n[2] Loading batter cache...")
        batter_streaks = []
        if os.path.exists(BATTER_CACHE):
            cache = json.load(open(BATTER_CACHE))
            batter_streaks = cache.get("batter_streaks", [])
            updated = cache.get("updated", "unknown")
            print(f"    {len(batter_streaks)} batter streaks (cache from {updated})")
        else:
            print(f"    No batter cache — run with --weekly first")
            print(f"    (Sunday nights, ~10-15 min)")

    # Ensure both vars defined regardless of mode
    if 'pitcher_streaks' not in dir():
        pitcher_streaks = []
    if 'batter_streaks' not in dir():
        batter_streaks = []

    # Print output
    print_sheet(pitcher_streaks, batter_streaks, args.date)

    if args.reddit:
        print_reddit(pitcher_streaks, batter_streaks, args.date)

    # Save combined output
    out_path = os.path.join(BASE_DIR, f"mlb_streaks_{args.date}.json")
    with open(out_path, 'w') as f:
        json.dump({
            "date":            args.date,
            "pitcher_streaks": pitcher_streaks,
            "batter_streaks":  batter_streaks,
        }, f, indent=2)
    print(f"\nSaved to mlb_streaks_{args.date}.json")
