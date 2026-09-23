@echo off
REM Edge Index — Windows Task Scheduler Setup
REM Run this once to schedule the daily publish (pull -> MLB morning routine -> commit + push;
REM GitHub Actions deploy-site builds and deploys). Re-running replaces the task.

echo Setting up EdgeIndexPublish...

REM Daily at 10:00 AM. Runs as soon as possible after a missed start, and on battery (a missed or
REM refused run means the MLB pages don't update that day). schtasks can't set those two options,
REM so the task is registered through PowerShell.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = New-ScheduledTaskAction -Execute '%~dp0daily_publish.bat' -WorkingDirectory '%~dp0..';" ^
  "$t = New-ScheduledTaskTrigger -Daily -At 10:00am;" ^
  "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries;" ^
  "Register-ScheduledTask -TaskName 'EdgeIndexPublish' -Action $a -Trigger $t -Settings $s -Force | Out-Null"
if errorlevel 1 (
    echo FAILED to create the task.
    pause
    exit /b 1
)

echo.
echo Task created: EdgeIndexPublish
echo Runs: Daily at 10:00 AM (and on the next chance if 10:00 was missed)
echo.
echo To run manually:
echo   %~dp0daily_publish.bat
echo.
pause
