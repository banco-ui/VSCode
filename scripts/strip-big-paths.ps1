# 1) 안전 백업 번들 (repo 밖에 저장)
# 2) filter-repo: 대형 경로 + *.pyc 를 미푸시 히스토리에서 제거
Set-Location "d:\Data\AI\VSCode"
$backupDir = "d:\Data\AI\backup"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$bundle = Join-Path $backupDir ("main-pre-split-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".bundle")
git bundle create $bundle main 2>&1 | Select-Object -Last 1
"BUNDLE=" + $bundle
"BUNDLE_MB=" + [math]::Round((Get-Item $bundle).Length / 1MB, 1)
$env:FILTER_BRANCH_SQUELCH_WARNING = 1
git filter-repo --force --invert-paths --paths-from-file "d:\Data\AI\VSCode\.git\filter-repo-paths.txt" --path-glob "*.pyc" --refs main 2>&1 | Select-Object -Last 2
"FILTER_EXIT=$LASTEXITCODE"
git log --oneline -1
git rev-list --count "upstream/main..main"
