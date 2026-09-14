<#
.SYNOPSIS
    Windows 작업 스케줄러에 Git Auto Commit 작업 등록
.DESCRIPTION
    30분 간격으로 git-auto-commit.bat를 실행하는 스케줄을 등록합니다.
#>

$taskName = "GitAutoCommit_VSCode"
$batPath = "d:\Data\AI\VSCode\scripts\git-auto-commit.bat"

# 기존 작업 삭제 (있는 경우)
$existingTask = schtasks /query /tn $taskName 2>$null
if ($existingTask) {
    Write-Host "기존 작업 삭제 중: $taskName"
    schtasks /delete /tn $taskName /f
}

# 작업 등록
Write-Host "작업 스케줄러 등록 중: $taskName"
Write-Host "실행 간격: 30분"
Write-Host "배치 파일: $batPath"

schtasks /create /tn $taskName /tr $batPath /sc minute /mo 30 /rl HIGHEST /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 작업 스케줄러 등록 성공!" -ForegroundColor Green
    Write-Host ""
    Write-Host "확인 방법:"
    Write-Host "  schtasks /query /tn $taskName"
    Write-Host ""
    Write-Host "삭제 방법:"
    Write-Host "  schtasks /delete /tn $taskName /f"
} else {
    Write-Host "❌ 작업 스케줄러 등록 실패!" -ForegroundColor Red
}
