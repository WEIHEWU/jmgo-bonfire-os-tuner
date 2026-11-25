@echo off
setlocal

:: Bonfire OS Tuning Tool N5/N5S - Windows launcher
:: All logic lives in bonfire_tuner_full.py (cross-platform).

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%bonfire_tuner_full.py"

if not exist "%PY_SCRIPT%" (
    echo [ERROR] bonfire_tuner_full.py not found in script folder.
    pause
    exit /b 1
)

:: Find Python (prefer 3.x via py launcher, then python3, then python)
set "PY_CMD="
where py >nul 2>&1
if %errorlevel%==0 (
    set "PY_CMD=py -3"
) else (
    where python3 >nul 2>&1
    if %errorlevel%==0 (
        set "PY_CMD=python3"
    ) else (
        where python >nul 2>&1
        if %errorlevel%==0 (
            set "PY_CMD=python"
        )
    )
)

if "%PY_CMD%"=="" (
    echo [ERROR] Python 3 not found in PATH.
    echo Please install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)

%PY_CMD% "%PY_SCRIPT%" %*
exit /b %errorlevel%
