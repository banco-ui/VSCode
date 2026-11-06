# 조각 크기 임계값 확인 (22KB / 26KB raw)
Set-Location "d:\Data\AI\VSCode"
foreach ($kb in @(22, 26)) {
    $bytes = New-Object byte[] ($kb * 1024)
    (New-Object Random 1).NextBytes($bytes)
    $b64 = [Convert]::ToBase64String($bytes)
    $json = '{"content":"' + $b64 + '","encoding":"base64"}'
    $tmp = "$env:TEMP\sz.json"
    [IO.File]::WriteAllText($tmp, $json)
    $null = gh api repos/banco-ui/VSCode/git/blobs --input $tmp -X POST 2>&1
    "${kb}KB -> EXIT=$LASTEXITCODE"
    Start-Sleep -Seconds 1
}
