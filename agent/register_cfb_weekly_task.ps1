# Registers the Tuesday CFB weekly run (Tim, 2026-10-23): Tue 10:20 AM ET, wake-to-run, runs whether
# the user is signed in or not (S4U). Runs:  python -m engine.cfb.weekly_task
# (wait for the tue10 bet snapshot -> update_week -> project_week -> DRAFT card -> commit + push the
# week's targets and the forward log). Publishing stays manual. Output: %USERPROFILE%\.edge-index\weekly.log
# Must be run from an ELEVATED PowerShell (S4U). Remove with:
#   Unregister-ScheduledTask -TaskPath "\EdgeIndex\" -TaskName "CFB weekly" -Confirm:$false

$ErrorActionPreference = "Stop"
$Repo   = Split-Path -Parent $PSScriptRoot
$Python = (Get-Command python).Source
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
$Action  = New-ScheduledTaskAction -Execute $Python -Argument "-m engine.cfb.weekly_task" -WorkingDirectory $Repo
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At "10:20"
Register-ScheduledTask -TaskName "CFB weekly" -TaskPath "\EdgeIndex\" -Action $Action -Trigger $Trigger `
    -Settings $Settings -Principal $Principal -Description "CFB weekly: update, project (forward log), draft card, push targets + log" -Force | Out-Null
Write-Output "registered CFB weekly: Tuesday 10:20 ET"
