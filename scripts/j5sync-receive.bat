@echo off
chcp 65001 >nul
echo ========================================
echo   [보안 PC] j5Create 에서 파일 수신
echo ========================================
echo.

REM j5Create 드라이브 설정 (드라이브 문자 확인 필요)
set J5DRIVE=E:
set J5_TO=%J5DRIVE%\j5sync\to-security
set J5_FROM=%J5DRIVE%\j5sync\from-security

REM 보안 PC 작업 디렉토리 설정 (수정 필요)
set WORKSPACE=d:\work\usm-automation
set INPUT_DIR=%WORKSPACE%\j5sync-input

echo [작업 디렉토리] %WORKSPACE%
echo [j5Create 드라이브] %J5DRIVE%
echo.

REM j5Create to-security 폴더 확인
if not exist "%J5_TO%" (
    echo [오류] %J5_TO% 폴더가 없습니다.
    echo 무보안 PC 에서 파일을 먼저 넣어주세요.
    echo.
    pause
    exit /b 1
)

REM input 폴더 생성
if not exist "%INPUT_DIR%" (
    echo [생성] %INPUT_DIR%
    mkdir "%INPUT_DIR%"
)

echo ----------------------------------------
echo   파일 복사 중...
echo ----------------------------------------

echo [COPY] %J5_TO% → %INPUT_DIR%
xcopy "%J5_TO%" "%INPUT_DIR%" /Y /Q /S /E /I

REM 복사 후 정리 (선택사항 - 보안상 삭제 권장)
echo [정리] %J5_TO% 폴더 비우기
del /Q "%J5_TO%\*.*"
for /d %%i in ("%J5_TO%\*") do rd /Q /S "%%i"

echo.
echo ----------------------------------------
echo   수신 완료!
echo ----------------------------------------
echo.
echo [입력 폴더] %INPUT_DIR%
echo.
echo ========================================
pause