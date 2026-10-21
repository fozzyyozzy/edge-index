"""Team codes. Everything downstream uses NBA.com tricodes; ESPN and The Odds API names map onto them."""
ESPN_TO_NBA = {"GS": "GSW", "NY": "NYK", "NO": "NOP", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}

NBA_TEAMS = {
    "ATL": "Atlanta Hawks", "BKN": "Brooklyn Nets", "BOS": "Boston Celtics", "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers", "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons", "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies", "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves", "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}
NAME_TO_NBA = {v: k for k, v in NBA_TEAMS.items()} | {"LA Clippers": "LAC"}   # Odds API uses full names


def from_espn(abbr: str) -> str:
    code = ESPN_TO_NBA.get(abbr, abbr)
    if code not in NBA_TEAMS:
        raise KeyError(f"unknown ESPN team code {abbr!r}")
    return code


def from_name(name: str) -> str:
    return NAME_TO_NBA[name]
