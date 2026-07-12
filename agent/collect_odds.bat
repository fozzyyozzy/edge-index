@echo off
REM Edge Index — pregame odds collector. Schedule 2-3x daily.
REM One-time setup (run these two lines once in cmd):
REM   setx ODDS_API_KEY your_key_here
REM   schtasks /create /tn "EdgeIndexCollector" /tr "%~dp0collect_odds.bat" /sc daily /st 09:00 /ri 360 /du 18:00
REM (that runs it 9am, 3pm, 9pm daily; adjust /st and /ri as you like)
cd /d %~dp0..
python engine\collector.py --sport americanfootball_nfl >> agent\logs\collector.log 2>&1
python engine\collector.py --sport baseball_mlb >> agent\logs\collector.log 2>&1
