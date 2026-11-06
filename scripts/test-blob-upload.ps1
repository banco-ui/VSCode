# 대용량 blob API 업로드 테스트 (--input 파일 방식, Content-Length 보장)
$s = "1bab625b81e2c6104ca0e8710f6b60657360cb98"
Set-Location "d:\Data\AI\VSCode"
$content = git cat-file blob $s
$b64 = [Convert]::ToBase64String($content)
$json = '{"content":"' + $b64 + '","encoding":"base64"}'
$tmp = "$env:TEMP\blob-test.json"
[IO.File]::WriteAllText($tmp, $json)
"BODY_KB=" + [math]::Round((Get-Item $tmp).Length / 1KB, 1)
$r = gh api repos/banco-ui/VSCode/git/blobs --input $tmp -X POST 2>&1
"EXIT=$LASTEXITCODE"
$r | Select-Object -First 2
Remove-Item $tmp -Force
