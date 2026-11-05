# 미푸시 커밋(origin/main..main)에서 Electron 빌드 산출물을 히스토리에서 제거
# 사용법: powershell -File scripts\strip-release-history.ps1
$env:FILTER_BRANCH_SQUELCH_WARNING = 1
Set-Location "d:\Data\AI\VSCode"
git filter-branch -f --index-filter "git rm -r --cached --ignore-unmatch --quiet sd-search/release" -- origin/main..main
Write-Output ("EXITCODE=" + $LASTEXITCODE)
