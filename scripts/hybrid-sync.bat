@echo off
chcp 65001 >nul
echo ========================================
echo   Hybrid Sync: GitHub + j5Create
echo ========================================
echo.

cd /d "%~dp0.."
set WORKSPACE=%CD%

echo [작업 디렉토리] %WORKSPACE%
echo.

REM ========================================
REM 1 단계: GitHub 동기화 (코드/설정)
REM ========================================
echo ----------------------------------------
echo   [1/3] GitHub 동기화 중...
echo ----------------------------------------

git status >nul 2>&1
if errorlevel 1 (
    echo [오류] 이 폴더는 Git 저장소가 아닙니다.
    echo git init 또는 git clone 을 먼저 실행하세요.
    goto :j5create
)

REM 변경사항 확인
git status --short > "%TEMP%\git-status.txt"
findstr /C:"modified" /C:"new file" /C:"deleted" "%TEMP%\git-status.txt" >nul
if errorlevel 1 (
    echo [GitHub] 변경사항 없음 - 스킵
    goto :j5create
)

echo [GitHub] 변경사항 발견 - 동기화 시작
echo.

REM 자동 커밋 (선택사항 - 주석 해제하면 자동 실행)
REM git add .
REM git commit -m "Auto: %date% %time%"
REM git push origin main

echo [안내] 다음 명령을 수동으로 실행하세요:
echo   git add .
echo   git commit -m "작업 내용"
echo   git push origin main
echo.

:j5create
REM ========================================
REM 2 단계: j5Create 대용량 파일 확인
REM ========================================
echo ----------------------------------------
echo   [2/3] j5Create 전달 파일 확인 중...
echo ----------------------------------------

REM j5Create 드라이브 확인 (E:)
set J5DRIVE=E:

if not exist "%J5DRIVE%\\" (
    echo [경고] j5Create 드라이브 (%J5DRIVE%) 를 찾을 수 없습니다.
    echo USB 연결을 확인하세요.
    goto :summary
)

REM 대용량 파일 찾기 (10MB 이상)
echo [검색] 10MB 이상 파일 검색 중...
echo.

set FOUND=0
for /f "tokens=*" %%i in ('
    powershell -Command "Get-ChildItem -Path '%WORKSPACE%' -Recurse -File | Where-Object { $_.Length -gt 10MB } | Select-Object -First 20 FullName"
') do (
    echo   %%i
    set FOUND=1
)

if %FOUND%==0 (
    echo [결과] 대용량 파일 없음 - j5Create 전달 불필요
) else (
    echo.
    echo [안내] 위 파일들은 j5Create 로 수동 복사하세요:
    echo   1. 탐색기에서 위 파일들 선택
    echo   2. Ctrl+C 복사
    echo   3. E:\j5sync\to-security\ 에 붙여넣기
)

:summary
echo.
echo ----------------------------------------
echo   [3/3] 요약
echo ----------------------------------------
echo.
echo [GitHub] 코드/설정 파일 동기화
echo   - *.js, *.md, *.json, *.py 등
echo   - git push 로 전송
echo.
echo [j5Create] 대용량 파일 수동 전달
echo   - 10MB 이상 파일
echo   - 빌드 결과물, 모델 파일 등
echo   - 탐색기에서 Ctrl+C/V
echo.
echo ========================================
pause
