@echo off
chcp 65001 >nul
echo ========================================
echo   Hybrid Receive: 보안 PC 용 수신 스크립트
echo ========================================
echo.

REM ========================================
REM 설정 (보안 PC 환경에 맞게 수정)
REM ========================================
set J5DRIVE=E:
set WORKSPACE=d:\work\usm-automation
set J5_INPUT=%J5DRIVE%\j5sync\to-security
set J5_OUTPUT=%J5DRIVE%\j5sync\from-security

echo [작업 디렉토리] %WORKSPACE%
echo [j5Create 드라이브] %J5DRIVE%
echo.

REM ========================================
REM 1 단계: j5Create 에서 파일 수신
REM ========================================
echo ----------------------------------------
echo   [1/3] j5Create 에서 파일 수신
echo ----------------------------------------

if not exist "%J5_INPUT%" (
    echo [결과] 전달할 파일 없음 (E:\j5sync\to-security\ 없음)
    goto :github
)

dir "%J5_INPUT%" /s /b >nul 2>&1
if errorlevel 1 (
    echo [결과] 전달할 파일 없음
    goto :github
)

echo [복사] %J5_INPUT% → %WORKSPACE%\j5-input\
echo.

if not exist "%WORKSPACE%\j5-input" mkdir "%WORKSPACE%\j5-input"
xcopy "%J5_INPUT%\*" "%WORKSPACE%\j5-input\" /Y /Q /S /E /I

REM 복사 후 정리 (보안상 삭제 권장)
echo [정리] j5Create 전달 폴더 삭제
del /Q "%J5_INPUT%\*.*" >nul 2>&1
for /d %%i in ("%J5_INPUT%\*") do rd /Q /S "%%i" >nul 2>&1

echo.
echo [완료] %WORKSPACE%\j5-input\ 에서 확인하세요

:github
REM ========================================
REM 2 단계: GitHub 동기화
REM ========================================
echo.
echo ----------------------------------------
echo   [2/3] GitHub 상태 확인
echo ----------------------------------------

cd /d "%WORKSPACE%"

git status >nul 2>&1
if errorlevel 1 (
    echo [경고] 이 폴더는 Git 저장소가 아닙니다.
    goto :output
)

echo [GitHub] 현재 브랜치:
git branch --show-current
echo.

git status --short
echo.

echo [안내] 변경사항이 있으면 다음 명령 실행:
echo   git add .
echo   git commit -m "작업 내용"
echo   git push origin main
echo.

:output
REM ========================================
REM 3 단계: Cline SR 작업 결과 보내기
REM ========================================
echo ----------------------------------------
echo   [3/3] 작업 결과를 j5Create 로 보내기
echo ----------------------------------------

set OUTPUT_DIR=%WORKSPACE%\output

if not exist "%OUTPUT_DIR%" (
    echo [결과] output 폴더 없음 - 작업 결과 없음
    goto :end
)

dir "%OUTPUT_DIR%" /s /b >nul 2>&1
if errorlevel 1 (
    echo [결과] output 폴더에 파일 없음
    goto :end
)

if not exist "%J5_OUTPUT%" mkdir "%J5_OUTPUT%"

echo [복사] %OUTPUT_DIR% → %J5_OUTPUT%
xcopy "%OUTPUT_DIR%\*" "%J5_OUTPUT%\" /Y /Q /S /E /I

echo.
echo [완료] j5Create 에 결과 파일이 준비되었습니다.
echo [다음] 무보안 PC 에서 j5create-from-security.bat 실행

:end
echo.
echo ========================================
pause
