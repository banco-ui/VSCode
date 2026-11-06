# 프록시 POST 크기 임계값 탐색 (정밀)
Set-Location "d:\Data\AI\VSCode"
foreach ($kb in @(5, 10, 20, 40, 64, 80)) {
    $bytes = New-Object byte[] ($kb * 1024)
    (New-Object Random 1).NextBytes($bytes)
    $b64 = [Convert]::ToBase64String($bytes)
    $json = '{"content":"' + $b64 + '","encoding":"base64"}'
    $tmp = "$env:TEMP\size-test.json"
    [IO.File]::WriteAllText($tmp, $json)
    $null = gh api repos/banco-ui/VSCode/git/blobs --input $tmp -X POST 2>&1
    "${kb}KB -> EXIT=$LASTEXITCODE"
    Remove-Item $tmp -Force
    Start-Sleep -Seconds 1
}
