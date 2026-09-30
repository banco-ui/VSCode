#!/usr/bin/env node

/**
 * DRM 문서 HTML 저장
 * 
 * Word COM 으로 텍스트를 추출하고, 화면 캡처로 그림/표를 저장한 후
 * 단일 HTML 파일로 통합합니다.
 * 결과물:
 * - output/{문서명}.html (텍스트 + 이미지 모두 포함)
 * 
 * 사용법:
 * node scripts/drm-html-save.js "D:\path\to\document.docx"
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const docPath = process.argv[2];
if (!docPath) {
  console.error('사용법: node drm-html-save.js "문서경로.docx"');
  process.exit(1);
}

if (!fs.existsSync(docPath)) {
  console.error(`파일을 찾을 수 없습니다: ${docPath}`);
  process.exit(1);
}

const outputDir = path.join(__dirname, '../output');
const imagesDir = path.join(outputDir, 'images', path.basename(docPath, '.docx'));
const htmlPath = path.join(outputDir, `${path.basename(docPath, '.docx')}.html`);

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
if (!fs.existsSync(imagesDir)) fs.mkdirSync(imagesDir, { recursive: true });

console.log(`📄 문서: ${path.basename(docPath)}`);
console.log(`📁 HTML 출력: ${htmlPath}`);
console.log(`🖼️  이미지 출력: ${imagesDir}`);
console.log('');

const psScript = `
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$docPath = "${docPath.replace(/\\/g, '\\\\')}"
$outputDir = "${outputDir.replace(/\\/g, '\\\\')}"
$imagesDir = "${imagesDir.replace(/\\/g, '\\\\')}"
$htmlPath = "${htmlPath.replace(/\\/g, '\\\\')}"

Write-Host "🚀 Word COM 객체 생성 중..."
$word = New-Object -ComObject Word.Application
$word.Visible = $true
$word.WindowState = 1

try {
  Write-Host "📖 문서 여는 중..."
  $doc = $word.Documents.Open($docPath, $false, $true)
  $pageCount = $doc.ComputeStatistics(2)
  Write-Host "📊 총 페이지: $pageCount 페이지"
  Write-Host ""
  
  $word.Activate()
  Start-Sleep -Milliseconds 500
  
  $docName = "$(path.basename(docPath, '.docx'))"
  $docBaseName = "$(path.basename(docPath))"
  
  $htmlContent = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$docName</title>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; background: #f5f5f5; }
        .document-container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .page-section { margin: 30px 0; page-break-after: always; }
        .page-header { background: #007bff; color: white; padding: 5px 15px; border-radius: 4px; display: inline-block; margin-bottom: 15px; }
        .text-content { white-space: pre-wrap; font-size: 14px; margin-bottom: 20px; }
        .screenshot { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }
        .info { background: #e7f3ff; padding: 15px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="document-container">
        <h1>$docBaseName</h1>
        <div class="info"><strong>문서 정보:</strong><br>• 추출일: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")<br>• 총 페이지: $pageCount 페이지<br>• 원본: $docPath</div>
"@

  for ($i = 1; $i -le $pageCount; $i++) {
    Write-Host "   페이지 $i/$pageCount 처리 중..."
    $selection = $word.Selection
    $selection.GoTo(-1, 1, $i)
    Start-Sleep -Milliseconds 300
    
    $pageText = ""
    try {
      $startPos = $selection.Start
      $selection.GoTo(-1, 1, $i + 1)
      $endPos = $selection.Start
      $selection.GoTo(-1, 1, $i)
      $pageRange = $doc.Range($startPos, $endPos)
      $pageText = $pageRange.Text
    } catch { $pageText = $selection.Text }
    
    $imagePath = Join-Path $imagesDir "page_$(printf "%03d" $i).jpg"
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Bounds.X, $screen.Bounds.Y, 0, 0, $bitmap.Size)
    $bitmap.Save($imagePath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $graphics.Dispose()
    $bitmap.Dispose()
    
    $relImg = "images/$(Split-Path $imagesDir -Leaf)/page_$(printf "%03d" $i).jpg"
    $htmlContent += @"

        <div class="page-section">
            <div class="page-header">페이지 $i</div>
            <div class="text-content">$pageText</div>
            <img src="$relImg" alt="페이지 $i 캡처" class="screenshot">
        </div>
"@
    Write-Host "   ✅ 페이지 $i 완료"
  }
  
  $htmlContent += @"

    </div>
</body>
</html>
"@

  $utf8BOM = New-Object System.Text.UTF8Encoding $true
  [System.IO.File]::WriteAllText($htmlPath, $htmlContent, $utf8BOM)
  
  Write-Host ""
  Write-Host "✅ 완료!"
  Write-Host "   HTML: $htmlPath"
  Write-Host "   이미지: $imagesDir (총 $pageCount 개)"
} catch {
  Write-Host "❌ 오류: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
} finally {
  if ($doc) { $doc.Close($false) }
  if ($word) {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
  }
  [System.GC]::Collect()
  [System.GC]::WaitForPendingFinalizers()
}
`;

try {
  execSync(`powershell -ExecutionPolicy Bypass -Command "${psScript}"`, { encoding: 'utf8', stdio: 'inherit' });
} catch (error) {
  console.error('실행 중 오류 발생:', error.message);
  process.exit(1);
}