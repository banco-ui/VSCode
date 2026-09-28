@echo off
chcp 65001 >nul
echo ========================================
echo   [보안 PC] 작업 결과를 j5Create 로 전송
echo ========================================
echo.

REM j5Create 드라이브 설정 (드라이브 문자 확인 필요)
set J5DRIVE=E:
set J5_FROM=%J5DRIVE%\j5sync\from-security

REM 보안 PC 작업 디렉토리 설정 (수정 필요)
set WORKSPACE=d:\work\usm-automation
set OUTPUT_DIR=%WORKSPACE%\output

echo [작업 디렉토리] %WORKSPACE%
echo [출력 디렉토리] %OUTPUT_DIR%
echo [j5Create 드라이브] %J5DRIVE%
echo.

REM output 폴더 확인
if not exist "%OUTPUT_DIR%" (
    echo [오류] %OUTPUT_DIR% 폴더가 없습니다.
    echo 작업 결과를 먼저 생성해주세요.
    echo.
    pause
    exit /b 1
)

REM j5Create from-security 폴더 생성
if not exist "%J5_FROM%" (
    echo [생성] %J5_FROM%
    mkdir "%J5_FROM%"
)

echo ----------------------------------------
echo   파일 복사 중...
echo ----------------------------------------

REM output 폴더의 모든 파일을 from-security 로 복사
echo [COPY] %OUTPUT_DIR% → %J5_FROM%
xcopy "%OUTPUT_DIR%" "%J5_FROM%" /Y /Q /S /E /I

REM 복사 후 정리 (선택사항)
echo [정리] %OUTPUT_DIR% 폴더 비우기
del /Q "%OUTPUT_DIR%\*.*"
for /d %%i in ("%OUTPUT_DIR%\*") do rd /Q /S "%%i"

echo.
echo ----------------------------------------
echo   전송 완료!
echo ----------------------------------------
echo.
echo [다음 단계]
echo 1. j5Create USB 를 분리하여 무보안 PC 에 연결
echo 2. j5create-from-security.bat 실행
echo.
echo ========================================
pause