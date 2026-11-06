# 분할 백업된 대형 파일들을 조각에서 원본으로 복원
Set-Location "d:\Data\AI\VSCode"
$ok = 0; $fail = 0
Get-Content ".git\ignore-additions.txt" | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object {
    $r = node "d:\Data\AI\VSCode\scripts\restore-split.js" $_ 2>&1
    if ($LASTEXITCODE -eq 0) { $ok++ } else { $fail++; Write-Output "FAIL: $_ -> $r" }
}
"RESTORED=$ok FAILED=$fail"
