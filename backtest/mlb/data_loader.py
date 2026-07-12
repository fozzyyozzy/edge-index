"""
Edge Index — MLB Data Loader (stub)
"""
PARK_FACTORS = {
    "COL":1.18,"CIN":1.08,"PHI":1.06,"BOS":1.05,"HOU":1.04,
    "NYY":1.03,"MIL":1.02,"TEX":1.02,"ATL":1.01,"LAD":1.00,
    "CHC":1.00,"STL":0.99,"MIN":0.98,"DET":0.98,"TOR":0.97,
    "CLE":0.97,"PIT":0.96,"MIA":0.95,"SF":0.94,"SD":0.94,"SEA":0.93,
}
K_ALT_LINES = [3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
UMPIRE_K_ADJ = {
    "Angel Hernandez":+0.08,"CB Bucknor":+0.06,"Laz Diaz":+0.07,
    "Joe West":-0.05,"Bill Miller":-0.04,
}
def get_park_factor(team): return PARK_FACTORS.get(team, 1.00)
def get_umpire_adj(name):  return UMPIRE_K_ADJ.get(name, 0.0)

if __name__ == "__main__":
    print("Park factors:")
    for team, f in sorted(PARK_FACTORS.items(), key=lambda x:-x[1]):
        print(f"  {team}: {f:.2f}")
    print("\nInstall pybaseball to pull real stats: pip install pybaseball")
