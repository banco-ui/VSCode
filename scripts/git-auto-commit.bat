@echo off
REM Git Auto Commit & Push - Windows Task Scheduler용 배치 파일
REM 작업 스케줄러에 의해 30분 간격으로 실행됨

cd /d "d:\Data\AI\VSCode"
powershell -ExecutionPolicy Bypass -File "scripts\git-auto-commit.ps1" >> "%USERPROFILE%\git-auto-commit.log" 2>&1
