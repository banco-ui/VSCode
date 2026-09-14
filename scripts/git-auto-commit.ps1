<#
.SYNOPSIS
    Git Auto Commit & Push Script
.DESCRIPTION
    변경사항을 감지하여 자동으로 git add, commit, push를 수행합니다.
    Windows 작업 스케줄러에 의해 주기적으로 실행됩니다.
#>

param(
    [string]$RepoPath = "d:\Data\AI\VSCode",
    [string]$LogFile = "$env:USERPROFILE\git-auto-commit.log"
)

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
}

# 로그 시작
Write-Log "========== Git Auto Commit Started =========="

# 저장소 디렉토리로 이동
if (-not (Test-Path $RepoPath)) {
    Write-Log "ERROR: Repository path not found: $RepoPath"
    exit 1
}

Set-Location $RepoPath

# Git 저장소 확인
$gitDir = git rev-parse --git-dir 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: Not a git repository: $RepoPath"
    exit 1
}

# 변경사항 확인
$status = git status --porcelain 2>&1
if (-not $status) {
    Write-Log "No changes detected. Skipping commit."
    exit 0
}

Write-Log "Changes detected. Proceeding with commit..."

# Git add
git add . 2>&1 | ForEach-Object { Write-Log "ADD: $_" }

# 커밋 메시지 생성
$commitMsg = "Auto commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$coAuthor = "Co-Authored-By: Cline SR"

# Git commit
git commit -m $commitMsg -m $coAuthor 2>&1 | ForEach-Object { Write-Log "COMMIT: $_" }

if ($LASTEXITCODE -ne 0) {
    Write-Log "WARNING: Commit failed or nothing to commit."
    exit 0
}

Write-Log "Commit successful."

# Git push (실패해도 커밋은 유지)
Write-Log "Attempting push..."
$pushResult = git push origin main 2>&1
$pushResult | ForEach-Object { Write-Log "PUSH: $_" }

if ($LASTEXITCODE -eq 0) {
    Write-Log "Push successful!"
} else {
    Write-Log "WARNING: Push failed (network/proxy issue?). Commit is saved locally. Will push next time."
}

Write-Log "========== Git Auto Commit Finished =========="
