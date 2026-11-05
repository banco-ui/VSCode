# 프록시 403 대응: 1커밋 단위 배치 push + 무한 재시도 루프 (v5)
# - 주 백업 저장소: upstream (banco-ui/VSCode) — 유일한 push 대상
# - origin(shoutsky0705, 개인 계정)은 회사 정책상 사내망에서 push하지 않음
# - 인증: gh CLI 토큰(banco-ui 계정)을 upstream URL에 임시 적용 후 복원
# - 라운드마다 미푸시 커밋 재계산, 1커밋씩 10회 재시도, 실패 시 60초 대기 재라운드
# - 중단 방법: .git\batch-push.stop 파일 생성 / 최대 실행 4시간
# 사용법: powershell -File scripts\batch-push.ps1
Set-Location "d:\Data\AI\VSCode"
$log = "d:\Data\AI\VSCode\.git\batch-push.log"
$stopFlag = "d:\Data\AI\VSCode\.git\batch-push.stop"
if (Test-Path $stopFlag) { Remove-Item $stopFlag -Force }
"START v5 " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Encoding utf8

$remote = "upstream"
$plainUrl = "https://github.com/banco-ui/VSCode.git"
$t = gh auth token
if (-not $t) { "NO_TOKEN - gh auth login 필요" | Out-File $log -Append -Encoding utf8; exit 1 }
git remote set-url $remote ("https://banco-ui:" + $t + "@github.com/banco-ui/VSCode.git")

$deadline = (Get-Date).AddHours(4)
$stoppedByUser = $false
try {
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $stopFlag) { $stoppedByUser = $true; break }

        $shas = @(git rev-list ("{0}..main" -f $remote))
        [array]::Reverse($shas)
        $pending = $shas.Count
        if ($pending -eq 0) {
            ("ALL-SYNCED {0} upstream 최신 상태" -f (Get-Date -Format "HH:mm:ss")) | Out-File $log -Append -Encoding utf8
            break
        }
        ("ROUND {0} upstream PENDING={1}" -f (Get-Date -Format "HH:mm:ss"), $pending) | Out-File $log -Append -Encoding utf8

        # 이 라운드에서는 맨 앞 1커밋만 반복 시도 (성공 시 다음 라운드에서 진행)
        $target = $shas[0]
        for ($try = 1; $try -le 10 -and -not (Test-Path $stopFlag); $try++) {
            $out = git push $remote ("{0}:refs/heads/main" -f $target) 2>&1 | Out-String
            $code = $LASTEXITCODE
            if ($code -eq 0 -and $out -notmatch "403|hung up|rejected") {
                ("OK   upstream {1}/{2} -> {3}" -f $remote, ($pending - 1), $pending, $target.Substring(0,7)) | Out-File $log -Append -Encoding utf8
                break
            }
            ("FAIL upstream 1/{0} try={1}" -f $pending, $try) | Out-File $log -Append -Encoding utf8
            Start-Sleep -Seconds 6
        }
        if (Test-Path $stopFlag) { $stoppedByUser = $true; break }
        Start-Sleep -Seconds 2
    }
}
finally {
    git remote set-url $remote $plainUrl   # 토큰 URL 복원 (보안)
}

if ($stoppedByUser) { "STOPPED-BY-USER " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Append -Encoding utf8 }
else { "TIME-LIMIT " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File $log -Append -Encoding utf8 }
