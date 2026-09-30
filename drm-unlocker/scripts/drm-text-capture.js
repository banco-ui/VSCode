#!/usr/bin/env node

/**
 * DRM 문서 텍스트 + 캡처 추출
 * 
 * Word COM 으로 텍스트를 추출하고, 화면 캡처로 그림/표를 저장합니다.
 * 결과물:
 * - 텍스트: output/{문서명}-text.txt
 * - 캡처: output/screenshots/{문서명}/page_XXX.jpg
 * 
 * 사용법:
 * node scripts/drm-text-capture.js "D:\path\to\document.docx"
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 인자 확인
const docPath = process.argv[2];
if (!docPath) {
  console.error('사용법: node drm-text-capture.js "문서경로.docx"');
  process.exit(1);
}

if (!fs.existsSync(docPath)) {
  console.error(`파일을 찾을 수 없습니다: ${docPath}`);
  process.exit(1);
}

// 출력 디렉토리 설정
const outputDir = path.join(__dirname, '../output');
const screenshotDir = path.join(outputDir, 'screenshots', path.basename(docPath, '.docx'));

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

console.log(`📄 문서: ${path.basename(docPath)}`);
console.log(`📁 텍스트 출력: ${outputDir}`);
console.log(`📸 캡처 출력: ${screenshotDir}`);
console.log('');

// PowerShell 스크립트: Word COM 으로 텍스트 추출 + 화면 캡처
const psScript = `
$ErrorActionPreference = "Stop"

# UTF8 출력 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$docPath = "${docPath.replace(/\\/g, '\\\\')}"
$outputDir = "${outputDir.replace(/\\/g, '\\\\')}"
$screenshotDir = "${screenshotDir.replace(/\\/g, '\\\\')}"

Write-Host "🚀 Word COM 객체 생성 중..."

# Word COM 객체 생성 (화면 표시)
$word = New-Object -ComObject Word.Application
$word.Visible = $true
$word.WindowState = 1  # wdWindowStateNormal

try {
  Write-Host "📖 문서 여는 중..."
  $doc = $word.Documents.Open($docPath, $false, $true)  # 읽기 전용
  
  # 페이지 수 확인
  $pageCount = $doc.ComputeStatistics(2)  # wdStatisticPages
  Write-Host "📊 총 페이지: $pageCount 페이지"
  Write-Host ""
  
  # 1. 텍스트 추출
  Write-Host "📝 텍스트 추출 중..."
  $textFile = Join-Path $outputDir "$(Split-Path $docPath -LeafBase)-text.txt"
  $fullText = $doc.Content.Text
  [System.IO.File]::WriteAllText($textFile, $fullText, [System.Text.UTF8Encoding]::new($true))
  Write-Host "   ✅ 텍스트 저장: $textFile"
  Write-Host "   📊 텍스트 양: $($fullText.Length) 자"
  Write-Host ""
  
  # 2. 페이지별 캡처
  Write-Host "📸 페이지별 캡처 중..."
  
  # Word 창 활성화
  $word.Activate()
  Start-Sleep -Milliseconds 500
  
  # 현재 페이지 정보 가져오기
  $currentPage = 1
  
  for ($i = 1; $i -le $pageCount; $i++) {
    Write-Host "   페이지 $i/$pageCount 캡처 중..."
    
    # 해당 페이지로 이동
    $selection = $word.Selection
    $selection.GoTo(-1, 1, $i)  # wdGoToPage
    
    Start-Sleep -Milliseconds 300
    
    # 화면 캡처 (PowerShell)
    $screenshotPath = Join-Path $screenshotDir "page_$(printf "%03d" $i).jpg"
    
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    
    # 활성화된 창 캡처
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Bounds.X, $screen.Bounds.Y, 0, 0, $bitmap.Size)
    
    # JPG 로 저장
    $bitmap.Save($screenshotPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $graphics.Dispose()
    $bitmap.Dispose()
    
    Write-Host "   ✅ $screenshotPath"
  }
  
  Write-Host ""
  Write-Host "✅ 완료!"
  Write-Host "   텍스트: $textFile"
  Write-Host "   캡처: $screenshotDir (총 $pageCount 개)"
  
} catch {
  Write-Host "❌ 오류: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
} finally {
  # Word 종료
  if ($doc) {
    $doc.Close($false)
  }
  if ($word) {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
  }
  [System.GC]::Collect()
  [System.GC]::WaitForPendingFinalizers()
}
`;

// PowerShell 실행
try {
  const result = execSync(`powershell -ExecutionPolicy Bypass -Command "${psScript}"`, {
    encoding: 'utf8',
    stdio: 'inherit'
  });
} catch (error) {
  console.error('실행 중 오류 발생:', error.message);
  process.exit(1);
}