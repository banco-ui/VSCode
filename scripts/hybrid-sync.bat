@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo   Hybrid Sync: GitHub + j5Create
echo ========================================
echo.

cd /d "%~dp0.."
set WORKSPACE=%CD%

echo [WORKSPACE] %WORKSPACE%
echo.

echo ----------------------------------------
echo   Step 1/3: GitHub Sync Check
echo ----------------------------------------

git status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Not a Git repository.
    echo Run: git init ^&^& git remote add origin URL
    goto :j5create
)

git status --short > "%TEMP%\git-status.txt"
findstr /C:"modified" /C:"new file" /C:"deleted" "%TEMP%\git-status.txt" >nul
if errorlevel 1 (
    echo [GitHub] No changes - skip
    goto :j5create
)

echo [GitHub] Changes detected!
echo [ACTION] Run manually:
echo   git add .
echo   git commit -m "message"
echo   git push origin main
echo.

:j5create
echo ----------------------------------------
echo   Step 2/3: j5Create Large Files
echo ----------------------------------------

set J5DRIVE=E:

if not exist "%J5DRIVE%\" (
    echo [WARN] j5Create drive not found: %J5DRIVE%
    goto :summary
)

echo [SEARCH] Files over 10MB...
echo.

powershell -Command "Get-ChildItem -Path '%WORKSPACE%' -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 10MB } | Select-Object -First 20 FullName | Format-Table -HideTableHeaders"

echo.
echo [ACTION] Copy above files to: D:\j5sync\to-security\
echo.

:summary
echo ----------------------------------------
echo   Step 3/3: Summary
echo ----------------------------------------
echo.
echo [GitHub] Code/Config files (*.js, *.md, *.json)
echo [j5Create] Large files (10MB+) - manual copy
echo.
echo ========================================
pause
