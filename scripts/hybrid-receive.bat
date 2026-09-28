@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo   Hybrid Receive: Security PC
echo ========================================
echo.

REM ========================================
REM CONFIG: Edit for your Security PC
REM ========================================
set J5DRIVE=E:
set WORKSPACE=d:\work\usm-automation
set J5_INPUT=%J5DRIVE%\j5sync\to-security
set J5_OUTPUT=%J5DRIVE%\j5sync\from-security

echo [WORKSPACE] %WORKSPACE%
echo [J5DRIVE] %J5DRIVE%
echo.

echo ----------------------------------------
echo   Step 1/3: Receive from j5Create
echo ----------------------------------------

if not exist "%J5_INPUT%" (
    echo [INFO] No incoming files (%J5_INPUT% not found)
    goto :github
)

dir "%J5_INPUT%" /s /b >nul 2>&1
if errorlevel 1 (
    echo [INFO] No incoming files
    goto :github
)

echo [COPY] %J5_INPUT% -> %WORKSPACE%\j5-input\
echo.

if not exist "%WORKSPACE%\j5-input" mkdir "%WORKSPACE%\j5-input"
xcopy "%J5_INPUT%\*" "%WORKSPACE%\j5-input\" /Y /Q /S /E /I

REM Clean up after copy (security)
echo [CLEAN] Removing j5Create transfer folder
del /Q "%J5_INPUT%\*.*" >nul 2>&1
for /d %%i in ("%J5_INPUT%\*") do rd /Q /S "%%i" >nul 2>&1

echo.
echo [DONE] Check: %WORKSPACE%\j5-input\

:github
echo.
echo ----------------------------------------
echo   Step 2/3: GitHub Status
echo ----------------------------------------

cd /d "%WORKSPACE%"

git status >nul 2>&1
if errorlevel 1 (
    echo [WARN] Not a Git repository
    goto :output
)

echo [GitHub] Current branch:
git branch --show-current
echo.

git status --short
echo.

echo [ACTION] If changes, run:
echo   git add .
echo   git commit -m "message"
echo   git push origin main
echo.

:output
echo ----------------------------------------
echo   Step 3/3: Send Results to j5Create
echo ----------------------------------------

set OUTPUT_DIR=%WORKSPACE%\output

if not exist "%OUTPUT_DIR%" (
    echo [INFO] No output folder
    goto :end
)

dir "%OUTPUT_DIR%" /s /b >nul 2>&1
if errorlevel 1 (
    echo [INFO] Output folder is empty
    goto :end
)

if not exist "%J5_OUTPUT%" mkdir "%J5_OUTPUT%"

echo [COPY] %OUTPUT_DIR% -> %J5_OUTPUT%
xcopy "%OUTPUT_DIR%\*" "%J5_OUTPUT%\" /Y /Q /S /E /I

echo.
echo [DONE] Files ready in j5Create
echo [NEXT] Run hybrid-sync.bat on insecure PC

:end
echo.
echo ========================================
pause
