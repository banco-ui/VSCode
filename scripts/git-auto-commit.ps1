<#
.SYNOPSIS
    Git Auto Commit & Push Script (사내망 대응)
.DESCRIPTION
    변경사항을 감지하여 자동으로 git add, commit을 수행합니다.
    push는 사내망 프록시 제한으로 인해 실패할 수 있으며, 
    실패해도 커밋은 로컬에 저장됩니다.
    외부망(테더링/VPN/집)에서 수동으로 push하면 됩니다.
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

Write-Log "========== Git Auto Commit Started =========="

Set-Location $RepoPath

# 변경사항 확인
$status = git status --porcelain 2>&1
if (-not $status) {
    Write-Log "No changes detected. Skipping."
    exit 0
}

Write-Log "Changes detected. Committing..."

# Git add
git add . 2>&1 | Out-Null

# 커밋
$commitMsg = "Auto commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git commit -m $commitMsg -m "Co-Authored-By: Cline SR" 2>&1 | ForEach-Object { Write-Log "COMMIT: $_" }

if ($LASTEXITCODE -eq 0) {
    Write-Log "Commit successful."
} else {
    Write-Log "Nothing to commit."
    exit 0
}

# Push 시도 (토큰 URL 방식)
Write-Log "Attempting push (token URL method)..."
$token = gh auth token 2>$null
if ($token) {
    git remote set-url origin "https://shoutsky0705:${token}@github.com/shoutsky0705/VSCode.git"
    $pushResult = git push origin main 2>&1
    git remote set-url origin "https://github.com/shoutsky0705/VSCode.git"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Push successful!"
    } else {
        Write-Log "Push failed (proxy). Commit saved locally. Push manually from external network."
    }
} else {
    Write-Log "No gh token. Push skipped. Commit saved locally."
}

Write-Log "========== Git Auto Commit Finished =========="
