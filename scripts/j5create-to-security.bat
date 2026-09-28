@echo off
chcp 65001 >nul
echo ========================================
echo   j5Create: 보안 PC 로 파일 전달
echo ========================================
echo.

REM j5Create 드라이브 설정
set J5DRIVE=E:
set J5_TO=%J5DRIVE%\j5sync\to-security
set J5_FROM=%J5DRIVE%\j5sync\from-security

REM 작업 디렉토리 설정 (현재 스크립트 기준 상위 폴더)
cd /d "%~dp0.."
set WORKSPACE=%CD%

echo [작업 디렉토리] %WORKSPACE%
echo [j5Create 드라이브] %J5DRIVE%
echo.

REM j5Create 폴더 생성
if not exist "%J5_TO%" (
    echo [생성] %J5_TO%
    mkdir "%J5_TO%"
)
if not exist "%J5_FROM%" (
    echo [생성] %J5_FROM%
    mkdir "%J5_FROM%"
)

echo ----------------------------------------
echo   파일 복사 중...
echo ----------------------------------------

REM JavaScript 파일 복사
if exist "%WORKSPACE%\*.js" (
    echo [JS] *.js
    xcopy "%WORKSPACE%\*.js" "%J5_TO%\" /Y /Q
)

REM Markdown 파일 복사
if exist "%WORKSPACE%\*.md" (
    echo [MD] *.md
    xcopy "%WORKSPACE%\*.md" "%J5_TO%\" /Y /Q
)

REM JSON 설정 파일 복사
if exist "%WORKSPACE%\*.json" (
    echo [JSON] *.json
    xcopy "%WORKSPACE%\*.json" "%J5_TO%\" /Y /Q
)

REM usm-automation 폴더 전체 복사
if exist "%WORKSPACE%\usm-automation" (
    echo [DIR] usm-automation\
    xcopy "%WORKSPACE%\usm-automation" "%J5_TO%\usm-automation" /Y /Q /S /E /I
)

echo.
echo ----------------------------------------
echo   복사 완료!
echo ----------------------------------------
echo.
echo [보안 PC 에서 할 일]
echo 1. j5Create 드라이브 (%J5DRIVE%) 에서 파일 확인
echo 2. %J5_TO% 폴더의 파일을 보안 PC 작업폴더로 복사
echo 3. 작업 완료 후 %J5_FROM% 에 결과 파일 넣기
echo.
echo ========================================
pause