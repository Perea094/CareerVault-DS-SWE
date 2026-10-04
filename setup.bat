@echo off
setlocal
echo ========================================================
echo   Career Vault - Setup & Dependency Bootstrapper
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
    goto RUN_SETUP
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=py -3"
    goto RUN_SETUP
)

echo [ERROR] Python was not found in your PATH.
echo Please install Python 3.11+ from https://www.python.org/ or via winget:
echo     winget install Python.Python.3.11
pause
exit /b 1

:RUN_SETUP
%PY_CMD% setup_vault.py --interactive --install-deps %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Setup encountered an issue.
    pause
    exit /b %ERRORLEVEL%
)

pause
