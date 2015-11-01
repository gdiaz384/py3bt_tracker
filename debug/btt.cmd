@echo off
taskkill /f /im "python.exe" /t >nul 2>nul
set tempfile=%userprofile%\desktop\bt_tracker.py.log
if exist %tempfile% del %tempfile%
if /i "%~1" neq "l" RunHiddenConsole python C:\Users\User\Documents\GitHub\py3bt_tracker\py3bt_tracker.py
if /i "%~1" equ "l" cmd /c "python C:\Users\User\Documents\GitHub\py3bt_tracker\py3bt_tracker.py" 2>>%tempfile%
