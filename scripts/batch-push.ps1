# 프록시 403 대응: 1커밋 단위 배치 push + 무한 재시도 루프 (v4)
# - 예전에 성공했던 "작게 잘라서 push" 방식: 1커밋씩, 프록시의 간헐적 허용 창을 노림
# - origin(개인 백업)과 upstream(연계) 둘 다 처리
# - 라운드마다 전체 미푸시 커밋을 재계산하여 성공한 만큼 앞으로 진행
# - 중단 방법: .git\batch-push.stop 파일 생성
# - 최대 실행: 4시간 (이후 자동 종료)
# 사용법: powershell -File scripts\batch-push.ps1
Set-Location "d:\Data\AI\VSCode"
$log = "d:\Data\AI\VSCode\.git\batch-push.log"
$stopFlag = "d:\Data\AI\VSCode\.git\batch-push.stop"
if (Test-Path $stopFlag) { Remove-Item $stopFlag -Force }
"START v4 " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Encoding utf8

$deadline = (Get-Date).AddHours(4)
$remotes = @("origin", "upstream")
$stoppedByUser = $false

while ((Get-Date) -lt $deadline) {
    if (Test-Path $stopFlag) { $stoppedByUser = $true; break }

    $anyProgress = $false
    foreach ($remote in $remotes) {
        if (Test-Path $stopFlag) { $stoppedByUser = $true; break }

        $shas = @(git rev-list ("{0}..main" -f $remote))
        [array]::Reverse($shas)
        $pending = $shas.Count
        if ($pending -eq 0) { continue }
        ("ROUND {0} {1} PENDING={2}" -f (Get-Date -Format "HH:mm:ss"), $remote, $pending) | Out-File $log -Append -Encoding utf8

        # 이 라운드에서는 맨 앞 1커밋만 반복 시도 (성공 시 다음 라운드에서 진행)
        $target = $shas[0]
        for ($try = 1; $try -le 10 -and -not (Test-Path $stopFlag); $try++) {
            $out = git push $remote ("{0}:refs/heads/main" -f $target) 2>&1 | Out-String
            $code = $LASTEXITCODE
            if ($code -eq 0 -and $out -notmatch "403|hung up|rejected") {
                ("OK   {0} {1}/{2} -> {3}" -f $remote, ($pending - 1), $pending, $target.Substring(0,7)) | Out-File $log -Append -Encoding utf8
                $anyProgress = $true
                break
            }
            ("FAIL {0} 1/{1} try={2}" -f $remote, $pending, $try) | Out-File $log -Append -Encoding utf8
            Start-Sleep -Seconds 6
        }
        Start-Sleep -Seconds 2
    }
    if ($stoppedByUser) { break }
    if (-not $anyProgress) { Start-Sleep -Seconds 60 }   # 프록시 창이 열릴 때까지 대기 후 재라운드
}

if ($stoppedByUser) { "STOPPED-BY-USER " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Append -Encoding utf8 }
else { "TIME-LIMIT " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Append -Encoding utf8 }
