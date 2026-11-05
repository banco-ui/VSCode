# HTTP/1.1 강제 + 단일 push 테스트
Set-Location "d:\Data\AI\VSCode"
$shas = @(git rev-list origin/main..main)
[array]::Reverse($shas)
$target = $shas[0]
"TARGET=$target HTTP11" | Out-File "d:\Data\AI\VSCode\.git\push-debug.log" -Encoding utf8
git -c http.version=HTTP/1.1 push origin ("{0}:refs/heads/main" -f $target) 2>&1 | Out-String | Out-File "d:\Data\AI\VSCode\.git\push-debug.log" -Append -Encoding utf8
("EXITCODE=" + $LASTEXITCODE) | Out-File "d:\Data\AI\VSCode\.git\push-debug.log" -Append -Encoding utf8
