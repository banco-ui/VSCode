# 프록시 403 대응: 소규모 배치 push + 재시도 자동화
# origin/main..main 을 오래된 커밋부터 5개씩 끊어 push, 배치당 최대 4회 재시도
Set-Location "d:\Data\AI\VSCode"
$shas = @(git rev-list origin/main..main)
[array]::Reverse($shas)   # 오래된 것부터
$batchSize = 5
$i = 0
$log = "d:\Data\AI\VSCode\.git\batch-push.log"
"START " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Encoding utf8

while ($i -lt $shas.Count) {
    $end = [Math]::Min($i + $batchSize - 1, $shas.Count - 1)
    $target = $shas[$end]
    $done = $false
    for ($try = 1; $try -le 4 -and -not $done; $try++) {
        $out = git push origin ("{0}:refs/heads/main" -f $target) 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0 -and $out -notmatch "403") {
            $done = $true
            ("OK   {0}/{1} -> {2}" -f ($end + 1), $shas.Count, $target.Substring(0,7)) | Out-File $log -Append -Encoding utf8
        } else {
            ("FAIL {0}/{1} try={2} {3}" -f ($end + 1), $shas.Count, $try, ($out.Trim() -split "`n" | Select-Object -Last 1)) | Out-File $log -Append -Encoding utf8
            Start-Sleep -Seconds 5
        }
    }
    if (-not $done) { "STOPPED (batch failed 4 times)" | Out-File $log -Append -Encoding utf8; exit 1 }
    $i = $end + 1
    Start-Sleep -Seconds 2
}
"DONE " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Append -Encoding utf8
