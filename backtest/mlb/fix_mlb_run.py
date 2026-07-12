# Run this from C:\Users\tyose\edge-index\backtest\mlb\
# python fix_mlb_run.py
import os

path = 'mlb_run_today.py'
with open(path, encoding='utf-8') as f:
    c = f.read()

fn = '''
def load_exclusions(game_date):
    import json, os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                      'cache', f'slump_list_{game_date}.json')
    if _os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
        print(f'  Loaded {len(d)} slump exclusions')
        return d
    print('  No slump cache found — run mlb_current_stats.py --update-cache first')
    return {}

'''

if 'def load_exclusions' in c:
    print('Function already exists')
else:
    c = c.replace('EXCLUDE_PLAYERS = {}  # populated at runtime',
                  fn + 'EXCLUDE_PLAYERS = {}  # populated at runtime')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Done — load_exclusions added')
