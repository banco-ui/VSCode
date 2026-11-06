# api-push 완료 감시 + 최종 검증
# 완료(DONE/ERROR) 감지 후 fetch + 카운트 검증, 결과를 .git\api-push-final.txt 에 기록
Set-Location "d:\Data\AI\VSCode"
$log = "d:\Data\AI\VSCode\.git\api-push.log"
$out = "d:\Data\AI\VSCode\.git\api-push-final.txt"
while ($true) {
    Start-Sleep -Seconds 60
    $tail = Get-Content $log -Tail 3 -ErrorAction SilentlyContinue
    if ($tail -match "REF-UPDATED") { $status = "SUCCESS"; break }
    if ($tail -match "ERROR|FATAL") { $status = "FAILED"; break }
    $nodeAlive = Get-Process -Name node -ErrorAction SilentlyContinue
    if (-not $nodeAlive) { $status = "PROCESS-DIED"; break }
}
"STATUS=$status" | Set-Content $out
Get-Content $log -Tail 5 | Add-Content $out
git fetch upstream 2>&1 | Add-Content $out
$behind = git rev-list --count upstream/main..main 2>&1
"PENDING_AFTER=$behind" | Add-Content $out
git ls-remote upstream refs/heads/main 2>&1 | Add-Content $out
