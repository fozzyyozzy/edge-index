"""
Edge Index — Full Platoon Cache Builder
Builds platoon splits for all MLB regulars.
Run once (~30-45 min), then daily update is fast.

Usage:
  python build_platoon_cache.py           # full build
  python build_platoon_cache.py --top200  # top 200 by PA
  python build_platoon_cache.py --summary # show cached splits
"""
import os, sys, json, argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mlb_platoon_splits import get_platoon_splits, PLATOON_CACHE

# ── ALL REGULARS — expand as needed ──────────────────────────
ALL_PLAYERS = [
    # ── CATCHERS ──────────────────────────────────────────────
    ("Shea Langeliers",      669127),
    ("William Contreras",    661388),
    ("Cal Raleigh",          663728),
    ("Adley Rutschman",      668939),
    ("Gabriel Moreno",       672580),
    ("Sean Murphy",          669004),
    ("Tyler Stephenson",     663886),
    ("Willson Contreras",    575929),
    ("Salvador Perez",       521692),
    ("Ryan Jeffers",         680777),
    ("Danny Jansen",         656429),
    ("Austin Wells",         688789),
    ("Patrick Bailey",       686469),
    ("Jake Rogers",          660155),
    ("Nick Fortes",          673237),
    ("Joey Bart",            657557),
    # ── FIRST BASE ────────────────────────────────────────────
    ("Pete Alonso",          624413),
    ("Freddie Freeman",      518692),
    ("Vladimir Guerrero",    665489),
    ("Christian Walker",     572233)  # HOU (was ARI),
    ("Matt Olson",           621566),
    ("Josh Naylor",          669357),
    ("Vinnie Pasquantino",   686469),
    ("Nathaniel Lowe",       663993),
    ("Ryan Mountcastle",     663527),
    ("Rhys Hoskins",         656061),
    ("Spencer Torkelson",    679529),
    ("Dominic Smith",        623993),
    ("Joey Meneses",         650402),
    ("Ji Man Choi",          596748),
    # ── SECOND BASE ───────────────────────────────────────────
    ("Jose Altuve",          514888),
    ("Marcus Semien",        543760),
    ("Ozzie Albies",         645277),
    ("Gleyber Torres",       650402),
    ("Luis Arraez",          650333),
    ("Jeff McNeil",          643446),
    ("Andres Gimenez",       665926),
    ("Nico Hoerner",         663538),
    ("Jorge Polanco",        553869),
    ("Lourdes Gurriel Jr.",  666971),
    ("Jonathan India",       663697),
    ("Ha-Seong Kim",         673237),
    ("DJ LeMahieu",          518934),
    ("Brandon Lowe",         641533),
    ("Brendan Donovan",      680757),
    ("Kolten Wong",          543939),
    ("Adam Frazier",         600303),
    # ── SHORTSTOP ─────────────────────────────────────────────
    ("Corey Seager",         608369),
    ("Trea Turner",          607208),
    ("Xander Bogaerts",      572138),
    ("Francisco Lindor",     596019),
    ("Bo Bichette",          666182),  # NYM (was TOR)
    ("Gunnar Henderson",     683002),
    ("Bobby Witt Jr.",       677951),
    ("CJ Abrams",            682928),
    ("Carlos Correa",        621043),
    ("Willy Adames",         642715),
    ("Anthony Volpe",        694524),
    ("Geraldo Perdomo",      671022),
    ("Dansby Swanson",       621020),
    ("Jeremy Pena",          665874),
    ("Lenyn Sosa",           680543),
    ("Masyn Winn",           694192),
    # ── THIRD BASE ────────────────────────────────────────────
    ("Jose Ramirez",         608070),
    ("Rafael Devers",        646240),
    ("Manny Machado",        592518),
    ("Austin Riley",         663586),
    ("Alec Bohm",            664761),
    ("Nolan Arenado",        571448),
    ("Matt Chapman",         656305),
    ("Ryan McMahon",         641857),
    ("Josh Jung",            677950),
    ("Ke Bryan Hayes",       663855),
    ("Eugenio Suarez",       553993),
    ("Emmanuel Rivera",      681481),
    ("Yoan Moncada",         660162),
    ("Jose Miranda",         668942),
    # ── OUTFIELD ──────────────────────────────────────────────
    ("Aaron Judge",          592450),
    ("Yordan Alvarez",       670541),
    ("Juan Soto",            665742),
    ("Kyle Tucker",          663656),
    ("Julio Rodriguez",      682998),
    ("Mike Trout",           545361),
    ("Mookie Betts",         605141),
    ("Ronald Acuna Jr.",     660670),
    ("Shohei Ohtani",        660271),
    ("Corbin Carroll",       682998),
    ("Jarren Duran",         680776),
    ("Riley Greene",         682985),
    ("Lars Nootbaar",        663527),
    ("Bryan Reynolds",       668804),
    ("Michael Harris II",    671739),
    ("Seiya Suzuki",         673548),
    ("Taylor Ward",          621493),
    ("Cedric Mullins",       656429),
    ("Yordan Alvarez",       670541),
    ("Steven Kwan",          680757),
    ("Lane Thomas",          657277),
    ("Teoscar Hernandez",    606192),
    ("Starling Marte",       516782),
    ("George Springer",      543807),
    ("Cody Bellinger",       641355),
    ("Jackson Merrill",      694192),
    ("Masataka Yoshida",     807799),
    ("Randy Arozarena",      668227),
    ("Tyler O'Neill",        641933),
    ("Kevin Kiermaier",      500779),
    ("Daulton Varsho",       662253),
    ("Brent Rooker",         667731),
    ("Andrew McCutchen",     457705),
    ("Lourdes Gurriel Jr.",  666971),
    ("Byron Buxton",         621439),
    ("Jake Fraley",          668800),
    ("Eddie Rosario",        600466),
    ("Jorge Soler",          578428),
    ("Adolis Garcia",        666969),
    ("Jose Siri",            642772),
    ("Hunter Renfroe",       592669),
    ("Whit Merrifield",      623993),
    # ── DH / UTILITY ──────────────────────────────────────────
    ("Giancarlo Stanton",    519317),
    ("J.D. Martinez",        503908),
    ("Joc Pederson",         592626),
    ("Kyle Schwarber",       656941),
    ("Robbie Grossman",      571771),
    ("Rowdy Tellez",         642708),
    ("Luke Voit",            621433),
    # ── OUR DAILY REGULARS ────────────────────────────────────
    ("Ernie Clement",        666803),
    ("Colson Montgomery",    682998),
    ("Jonathan Aranda",      668939),
    ("Miguel Vargas",        677774),
    ("Junior Caminero",      694192),
    ("Alejandro Osuna",      686575),
    ("Matt Vierling",        666185),
    ("Tyrone Taylor",        621345),
    ("Ildemaro Vargas",      624577),
    ("Josh Lowe",            641933),
    ("Jose Caballero",       672624),
    ("Yandy Diaz",           650490),
    ("Isaac Paredes",        670623),
    ("Brandon Valenzuela",   694192),
    ("Nolan Schanuel",       694192),
    ("Zach Neto",            694192),
    ("Jo Adell",             672515),
    ("Taylor Walls",         669022),
]

# Deduplicate by player_id
seen_ids = set()
PLAYERS  = []
for name, pid in ALL_PLAYERS:
    if pid not in seen_ids:
        seen_ids.add(pid)
        PLAYERS.append((name, pid))

def build_cache(players, season=2025):
    cache = {}
    if os.path.exists(PLATOON_CACHE):
        with open(PLATOON_CACHE) as f:
            cache = json.load(f)

    total   = len(players)
    new_cnt = 0
    print(f"Building platoon cache — {total} players ({season} data)")
    print(f"Already cached: {len(cache)}")
    print(f"To fetch: {sum(1 for n,_ in players if n not in cache)}")
    print(f"{'─'*65}\n")

    for i, (name, pid) in enumerate(players, 1):
        if name in cache:
            continue

        print(f"  [{i:3}/{total}] {name:28}...", end="", flush=True)
        splits = get_platoon_splits(pid, season=season)

        if splits:
            overall = splits.get("overall", {})
            vs_lhp  = splits.get("vs_lhp", {})
            vs_rhp  = splits.get("vs_rhp", {})
            diff    = vs_lhp.get("avg", 0) - vs_rhp.get("avg", 0)
            flag    = " ⚠️ PLATOON" if abs(diff) > 0.050 else ""

            print(f" .{int(overall.get('avg',0)*1000):03d} | "
                  f"L:.{int(vs_lhp.get('avg',0)*1000):03d} "
                  f"R:.{int(vs_rhp.get('avg',0)*1000):03d}"
                  f"{flag}")

            cache[name] = {
                "player_id": pid,
                "splits":    splits,
                "updated":   date.today().isoformat(),
            }
            new_cnt += 1
        else:
            print(" no data")

    with open(PLATOON_CACHE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\n{'='*65}")
    print(f"✓ Cache saved — {len(cache)} total players ({new_cnt} new)")
    print(f"\n  SIGNIFICANT PLATOON SPLITS (>50 pts):")
    print(f"  {'─'*60}")

    platoon_players = []
    for name, data in cache.items():
        splits = data.get("splits", {})
        lhp    = splits.get("vs_lhp", {})
        rhp    = splits.get("vs_rhp", {})
        if lhp.get("reliable") and rhp.get("reliable"):
            diff = lhp.get("avg", 0) - rhp.get("avg", 0)
            if abs(diff) > 0.050:
                platoon_players.append((name, diff,
                    lhp.get("avg",0), rhp.get("avg",0)))

    platoon_players.sort(key=lambda x: x[1], reverse=True)

    print(f"  {'PLAYER':28} {'vs LHP':8} {'vs RHP':8} {'DIFF':8} EDGE")
    print(f"  {'─'*60}")
    for name, diff, lhp_avg, rhp_avg in platoon_players:
        direction = "BOOST vs LHP" if diff > 0 else "FADE vs LHP"
        print(f"  {name:28} "
              f".{int(lhp_avg*1000):03d}     "
              f".{int(rhp_avg*1000):03d}     "
              f"{diff:+.3f}   {direction}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--season",  type=int, default=2025)
    args = parser.parse_args()

    if args.summary:
        if not os.path.exists(PLATOON_CACHE):
            print("No cache — run without --summary first")
        else:
            with open(PLATOON_CACHE) as f:
                cache = json.load(f)
            build_cache([], args.season)
    else:
        build_cache(PLAYERS, args.season)
