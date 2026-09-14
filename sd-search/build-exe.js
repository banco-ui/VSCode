/**
 * SDSearch EXE 빌드 스크립트 v3
 * 
 * 1. 프로젝트 파일 + node_modules를 dist/sd-search 폴더로 패키징
 * 2. PowerShell을 사용해 ZIP으로 압축
 * 3. start.bat을 자동 실행하는 래퍼 생성
 * 
 * 결과물: dist/sd-search/ 폴더 (start.bat 실행)
 *         dist/SDSearch.zip (배포용)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const rootDir = __dirname;
const distDir = path.join(rootDir, 'dist');
const distAppDir = path.join(distDir, 'sd-search');

console.log('=== SDSearch 빌드 시작 ===\n');

// 1. dist 폴더 정리
if (fs.existsSync(distAppDir)) {
    fs.rmSync(distAppDir, { recursive: true });
}
fs.mkdirSync(distAppDir, { recursive: true });

// 2. 파일 복사
console.log('[1/4] 파일 복사 중...');
const filesToCopy = [
    'gui/server.js',
    'gui/public/index.html',
    'gui/public/app.js',
    'gui/public/style.css',
    'adapters/mosaic-adapter.js',
    'adapters/confluence-adapter.js',
    'adapters/axhub-adapter.js',
    'core/searcher.js',
    'core/cache.js',
    'core/formatter.js',
    'config/search-config.json',
    'package.json',
];

for (const f of filesToCopy) {
    const srcPath = path.join(rootDir, f);
    const destPath = path.join(distAppDir, f);
    if (fs.existsSync(srcPath)) {
        fs.mkdirSync(path.dirname(destPath), { recursive: true });
        fs.copyFileSync(srcPath, destPath);
        console.log(`  ✓ ${f}`);
    }
}

// 3. 의존성 설치
console.log('\n[2/4] 의존성 설치 중...');
try {
    execSync('npm install --production --omit=dev', { 
        cwd: distAppDir, 
        stdio: 'inherit',
        timeout: 120000
    });
    console.log('  ✓ 의존성 설치 완료');
} catch (e) {
    console.log('  npm install 실패, 기존 node_modules 복사...');
    execSync(`xcopy "${path.join(rootDir, 'node_modules')}" "${path.join(distAppDir, 'node_modules')}" /E /I /Q /Y`, { stdio: 'inherit' });
    console.log('  ✓ node_modules 복사 완료');
}

// 4. Launcher 스크립트 생성
console.log('\n[3/4] Launcher 스크립트 생성 중...');

// start.bat - 메인 실행 스크립트 (ASCII only to avoid encoding issues)
fs.writeFileSync(path.join(distAppDir, 'start.bat'), `@echo off
title SDSearch - Samsung Doc Search
echo ============================================
echo   SDSearch - Samsung Doc Search v1.0
echo ============================================
echo.

:: Check Chrome CDP port
netstat -an | findstr ":9222" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Chrome is not running with CDP port 9222.
    echo           Run start-chrome.bat first.
    echo.
    timeout /t 3 /nobreak >nul
)

echo Starting server...
start /B node "%~dp0gui\\server.js" > "%~dp0sd-search.log" 2>&1
timeout /t 3 /nobreak >nul
start http://localhost:3120
echo.
echo  SDSearch is running! Browser: http://localhost:3120
echo  Close this window to stop.
echo.
cmd /k
`);

// stop.bat
fs.writeFileSync(path.join(distAppDir, 'stop.bat'), `@echo off
taskkill /f /im node.exe 2>nul
echo SDSearch stopped.
timeout /t 2 /nobreak >nul
`);

// start-chrome.bat
fs.writeFileSync(path.join(distAppDir, 'start-chrome.bat'), `@echo off
echo Starting Chrome in CDP mode...
start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\\chrome-cdp-profile"
echo Chrome started. Login to internal sites, then run start.bat
timeout /t 3 /nobreak >nul
`);


console.log('  ✓ start.bat, stop.bat, start-chrome.bat 생성');

// 5. ZIP 압축
console.log('\n[4/4] ZIP 패키징 중...');
const zipPath = path.join(distDir, 'SDSearch.zip');
try {
    if (fs.existsSync(zipPath)) fs.unlinkSync(zipPath);
    execSync(`powershell -Command "Compress-Archive -Path '${distAppDir}\\*' -DestinationPath '${zipPath}' -Force"`, { stdio: 'inherit' });
    const stats = fs.statSync(zipPath);
    console.log(`  ✓ ZIP 생성: ${zipPath} (${(stats.size / 1024 / 1024).toFixed(1)} MB)`);
} catch (e) {
    console.log('  ✗ ZIP 생성 실패:', e.message);
}

// 결과
console.log('\n=== 빌드 완료 ===');
console.log(`폴더: ${distAppDir}`);
console.log(`ZIP:  ${zipPath}`);
console.log('\n실행 방법:');
console.log('  1. start-chrome.bat 실행 (Chrome CDP 모드)');
console.log('  2. Chrome에서 사내 사이트 로그인');
console.log('  3. start.bat 실행 (서버 + 브라우저 자동 실행)');
console.log('  4. 종료: stop.bat 또는 창 닫기');

// 폴더 크기
try {
    const size = execSync(`powershell -Command "(Get-ChildItem -Recurse '${distAppDir}' | Measure-Object -Property Length -Sum).Sum / 1MB"`, { encoding: 'utf8' }).trim();
    console.log(`\n폴더 크기: ${parseFloat(size).toFixed(1)} MB`);
} catch (e) {}
