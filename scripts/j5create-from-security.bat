@echo off
chcp 65001 >nul
echo ========================================
echo   j5Create: 보안 PC 로부터 파일 수신
echo ========================================
echo.

REM j5Create 드라이브 설정
set J5DRIVE=E:
set J5_FROM=%J5DRIVE%\j5sync\from-security

REM 작업 디렉토리 설정
cd /d "%~dp0.."
set WORKSPACE=%CD%
set OUTPUT_DIR=%WORKSPACE%\output

echo [작업 디렉토리] %WORKSPACE%
echo [j5Create 드라이브] %J5DRIVE%
echo.

REM j5Create from-security 폴더 확인
if not exist "%J5_FROM%" (
    echo [오류] %J5_FROM% 폴더가 없습니다.
    echo 보안 PC 에서 파일을 먼저 넣어주세요.
    echo.
    pause
    exit /b 1
)

REM output 폴더 생성
if not exist "%OUTPUT_DIR%" (
    echo [생성] %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

echo ----------------------------------------
echo   파일 복사 중...
echo ----------------------------------------

REM from-security 폴더의 모든 파일 복사
echo [COPY] %J5_FROM% → %OUTPUT_DIR%
xcopy "%J5_FROM%" "%OUTPUT_DIR%" /Y /Q /S /E /I

echo.
echo ----------------------------------------
echo   수신 완료!
echo ----------------------------------------
echo.
echo [결과 확인]
echo - %OUTPUT_DIR% 폴더에서 파일 확인 가능
echo.
echo ========================================
pause