# 고유 blob 크기 분포 (빠른 버전: batch-check 사용)
Set-Location "d:\Data\AI\VSCode"
$out = "d:\Data\AI\VSCode\.git\blob-analysis.txt"
Set-Content -Path $out -Value "START" -Encoding utf8
$lines = git rev-list --objects upstream/main..main | git cat-file --batch-check="%(objectname) %(objecttype) %(objectsize) %(rest)"
$set = @{}
foreach ($line in $lines) {
    $p = $line -split " ", 4
    if ($p[1] -eq "blob") { $set[$p[0]] = $p[3] }
}
Add-Content $out ("UNIQUE_BLOBS=" + $set.Count) -Encoding utf8
$big = @()
foreach ($k in $set.Keys) {
    $sz = [long]($lines | Where-Object { $_.StartsWith($k) } | Select-Object -First 1 | ForEach-Object { ($_ -split " ")[2] })
    if ($sz -gt 17000) { $big += [PSCustomObject]@{ Sha = $k; SizeKB = [math]::Round($sz / 1KB, 1); Path = $set[$k] } }
}
Add-Content $out ("BIG_BLOBS=" + $big.Count) -Encoding utf8
$big | Sort-Object SizeKB -Descending | ForEach-Object {
    Add-Content $out ("{0}`t{1}KB`t{2}" -f $_.Sha.Substring(0, 8), $_.SizeKB, $_.Path) -Encoding utf8
}
Add-Content $out "END" -Encoding utf8
