"""
Advanced line parsing for DK, FD, BetMGM, theScore, Betr, Sleeper, PrizePicks
Handles prop line extraction and normalization
"""

import re
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# LINE PARSING UTILITIES
# ============================================================================

class LineParser:
    """Parse prop lines from different sportsbooks"""
    
    # Market type mappings
    MARKETS = {
        'rec_yds': ['receiving yards', 'rec yds', 'pass rec yds'],
        'receptions': ['receptions', 'recs', 'rec'],
        'pass_yds': ['passing yards', 'pass yds', 'passing'],
        'pass_cmps': ['pass completions', 'cmps', 'completions'],
        'rush_yds': ['rushing yards', 'rush yds', 'rushing'],
        'rush_att': ['rushing attempts', 'rush attempts', 'rush att'],
        'pass_tds': ['passing touchdowns', 'pass tds'],
        'rush_tds': ['rushing touchdowns', 'rush tds'],
        'anytime_td': ['anytime touchdown', 'any td'],
        'first_td': ['first touchdown'],
        'yds_rec_rec_tds': ['yards + rec + tds', 'rsh rec yds'],
    }
    
    @staticmethod
    def normalize_market(market_text: str) -> Optional[str]:
        """Convert market text to standard format"""
        market_lower = market_text.lower().strip()
        
        for standard, variations in LineParser.MARKETS.items():
            if market_lower in variations:
                return standard
        
        return market_lower  # Return as-is if no match
    
    @staticmethod
    def extract_line_and_odds(text: str) -> Tuple[Optional[float], Optional[int]]:
        """
        Extract line and odds from text
        Examples: "82+ -114", "8.5 -110", "O 45.5 (-115)"
        Returns: (line, odds)
        """
        # Try to find line and odds
        match = re.search(r'(\d+\.?\d*)\s*([+-]\d{3})', text)
        if match:
            line = float(match.group(1))
            odds = int(match.group(2))
            return line, odds
        
        # Try without odds
        match = re.search(r'(\d+\.?\d*)\+', text)
        if match:
            line = float(match.group(1))
            return line, None
        
        return None, None

# ============================================================================
# DRAFTKINGS PARSER
# ============================================================================

class DraftKingsParser(LineParser):
    """Parse DraftKings prop lines from HTML"""
    
    @staticmethod
    def parse_prop_lines(html_content: str) -> Dict[str, Dict]:
        """
        Parse DraftKings HTML and extract player prop lines
        Returns: {
            "PlayerName-Market": {
                "line": 8.5,
                "odds": -110,
                "market": "receptions"
            }
        }
        """
        props = {}
        
        try:
            # DK uses specific class structures for props
            # Pattern: Player Name → Market (e.g., "Receptions") → Line (e.g., "8.5") → Odds (e.g., "-110")
            
            # This is a simplified version - full implementation would need actual HTML parsing
            # Using regex patterns for common DK prop structures
            
            # Pattern: Player name followed by market and line
            pattern = r'(?P<player>[A-Z][a-z\s\.]+?)\s+(?P<market>[\w\s]+?)\s+(?P<line>\d+\.?\d*)\s+(?P<odds>[+-]\d{3})'
            
            matches = re.finditer(pattern, html_content)
            for match in matches:
                player = match.group('player').strip()
                market = DraftKingsParser.normalize_market(match.group('market'))
                line = float(match.group('line'))
                odds = int(match.group('odds'))
                
                key = f"{player}-{market}"
                props[key] = {
                    "line": line,
                    "odds": odds,
                    "market": market,
                    "book": "DK"
                }
        
        except Exception as e:
            logger.error(f"DraftKings parsing error: {e}")
        
        return props

# ============================================================================
# FANDUEL PARSER
# ============================================================================

class FanDuelParser(LineParser):
    """Parse FanDuel prop lines"""
    
    @staticmethod
    def parse_prop_lines(html_content: str) -> Dict[str, Dict]:
        """Parse FanDuel HTML for prop lines"""
        props = {}
        
        try:
            # FanDuel uses different class structure than DK
            # Similar pattern matching but with FD-specific selectors
            
            pattern = r'(?P<player>[A-Z][a-z\s\.]+?)\s+(?P<market>[\w\s]+?)\s+(?P<line>\d+\.?\d*)\s+(?P<odds>[+-]\d{3})'
            
            matches = re.finditer(pattern, html_content)
            for match in matches:
                player = match.group('player').strip()
                market = FanDuelParser.normalize_market(match.group('market'))
                line = float(match.group('line'))
                odds = int(match.group('odds'))
                
                key = f"{player}-{market}"
                props[key] = {
                    "line": line,
                    "odds": odds,
                    "market": market,
                    "book": "FD"
                }
        
        except Exception as e:
            logger.error(f"FanDuel parsing error: {e}")
        
        return props

# ============================================================================
# BETMGM PARSER
# ============================================================================

class BetMGMParser(LineParser):
    """Parse BetMGM prop lines"""
    
    @staticmethod
    def parse_prop_lines(html_content: str) -> Dict[str, Dict]:
        """Parse BetMGM HTML for prop lines"""
        props = {}
        
        try:
            pattern = r'(?P<player>[A-Z][a-z\s\.]+?)\s+(?P<market>[\w\s]+?)\s+(?P<line>\d+\.?\d*)\s+(?P<odds>[+-]\d{3})'
            
            matches = re.finditer(pattern, html_content)
            for match in matches:
                player = match.group('player').strip()
                market = BetMGMParser.normalize_market(match.group('market'))
                line = float(match.group('line'))
                odds = int(match.group('odds'))
                
                key = f"{player}-{market}"
                props[key] = {
                    "line": line,
                    "odds": odds,
                    "market": market,
                    "book": "BetMGM"
                }
        
        except Exception as e:
            logger.error(f"BetMGM parsing error: {e}")
        
        return props

# ============================================================================
# CONSOLIDATE LINES ACROSS BOOKS
# ============================================================================

def consolidate_lines(dk_props: Dict, fd_props: Dict, betmgm_props: Dict,
                      thescore_props: Dict = None, betr_props: Dict = None,
                      sleeper_props: Dict = None, pp_props: Dict = None) -> Dict:
    """
    Consolidate all book lines into single player-market entry
    Returns: {
        "PlayerName-Market": {
            "DK": 8.5,
            "FD": 8.5,
            "BetMGM": 8.0,
            "theScore": 8.5,
            "Betr": 8.5,
            "Sleeper": 8.5,
            "PrizePicks": 8.5
        }
    }
    """
    consolidated = {}
    
    all_props = {
        'DK': dk_props,
        'FD': fd_props,
        'BetMGM': betmgm_props,
        'theScore': thescore_props or {},
        'Betr': betr_props or {},
        'Sleeper': sleeper_props or {},
        'PrizePicks': pp_props or {}
    }
    
    # Collect all unique player-market combos
    all_keys = set()
    for props in all_props.values():
        all_keys.update(props.keys())
    
    # Build consolidated view
    for key in all_keys:
        consolidated[key] = {}
        for book, props in all_props.items():
            if key in props:
                consolidated[key][book] = props[key]['line']
            else:
                consolidated[key][book] = None
    
    return consolidated

if __name__ == "__main__":
    # Test parsing
    test_text = "Travis Kelce Receptions 8.5 -110"
    line, odds = LineParser.extract_line_and_odds(test_text)
    print(f"Line: {line}, Odds: {odds}")
    
    market = LineParser.normalize_market("receiving yards")
    print(f"Normalized: {market}")
