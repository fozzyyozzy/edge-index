@echo off
REM Edge Index — Windows Task Scheduler Setup
REM Run this once as Administrator to schedule the morning routine

echo Setting up Edge Index Morning Routine...

REM Create the scheduled task — runs daily at 8:00 AM
schtasks /create /tn "EdgeIndex_MorningRoutine" ^
  /tr "python C:\Users\tyose\edge-index\agent\morning_routine.py --build" ^
  /sc daily ^
  /st 08:00 ^
  /ru "%USERNAME%" ^
  /f

echo.
echo Task created: EdgeIndex_MorningRoutine
echo Runs: Daily at 8:00 AM
echo.
echo To run manually:
echo   python C:\Users\tyose\edge-index\agent\morning_routine.py --build
echo.
echo To add auto-deploy to Netlify:
echo   1. npm install -g netlify-cli
echo   2. netlify login
echo   3. Change --build to --deploy in the task
echo.
pause
