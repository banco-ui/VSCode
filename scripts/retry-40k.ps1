# 40KB POST 재시도 (간헐성 확인)
Set-Location "d:\Data\AI\VSCode"
$bytes = New-Object byte[] (40 * 1024)
(New-Object Random 1).NextBytes($bytes)
$b64 = [Convert]::ToBase64String($bytes)
$json = '{"content":"' + $b64 + '","encoding":"base64"}'
$tmp = "$env:TEMP\s40.json"
[IO.File]::WriteAllText($tmp, $json)
foreach ($i in 1..3) {
    $null = gh api repos/banco-ui/VSCode/git/blobs --input $tmp -X POST 2>&1
    "40KB try=$i EXIT=$LASTEXITCODE" | Add-Content "d:\Data\AI\VSCode\.git\size-test.out" -Encoding utf8
    Start-Sleep -Seconds 2
}
Remove-Item $tmp -Force
"DONE" | Add-Content "d:\Data\AI\VSCode\.git\size-test.out" -Encoding utf8
