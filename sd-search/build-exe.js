/**
 * SDSearch EXE 빌드 스크립트
 * 
 * Playwright(네이티브 모듈)를 사용하므로 pkg로 단일 EXE 빌드가 불가능합니다.
 * 대신 다음 방식으로 배포합니다:
 * 
 * 1.Portable Node.js + 프로젝트 파일을 하나의 폴더로 패키징
 * 2.Launcher BAT → 자동으로 Chrome CDP 체크 + 서버 실행 + 브라우저 열기
 * 3.BAT를 EXE로 변환 (Bat To Exe Converter 사용, 수동)
 * 
 * 또는 자동 빌드를 위해:
 * - npm install --production 으로 node_modules 생성
 * - portable node와 함께 zip으로 패키징
 * - start.bat 으로 실행
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const rootDir = __dirname;
const distDir = path.join(rootDir, 'dist');
const distAppDir = path.join(distDir, 'sd-search');

console.log('=== SDSearch EXE 빌드 시작 ===\n');

// 1. dist 폴더 정리
if (fs.existsSync(distAppDir)) {
    fs.rmSync(distAppDir, { recursive: true });
}
fs.mkdirSync(distAppDir, { recursive: true });

// 2. 파일 복사 (필요한 파일만)
const filesToCopy = [
    { src: 'gui/server.js', dest: 'gui/server.js' },
    { src: 'gui/public/index.html', dest: 'gui/public/index.html' },
    { src: 'gui/public/app.js', dest: 'gui/public/app.js' },
    { src: 'gui/public/style.css', dest: 'gui/public/style.css' },
    { src: 'adapters/mosaic-adapter.js', dest: 'adapters/mosaic-adapter.js' },
    { src: 'adapters/confluence-adapter.js', dest: 'adapters/confluence-adapter.js' },
    { src: 'adapters/axhub-adapter.js', dest: 'adapters/axhub-adapter.js' },
    { src: 'core/searcher.js', dest: 'core/searcher.js' },
    { src: 'core/cache.js', dest: 'core/cache.js' },
    { src: 'core/formatter.js', dest: 'core/formatter.js' },
    { src: 'config/search-config.json', dest: 'config/search-config.json' },
    { src: 'package.json', dest: 'package.json' },
];

console.log('[1/4] 파일 복사 중...');
for (const f of filesToCopy) {
    const srcPath = path.join(rootDir, f.src);
    const destPath = path.join(distAppDir, f.dest);
    if (fs.existsSync(srcPath)) {
        fs.mkdirSync(path.dirname(destPath), { recursive: true });
        fs.copyFileSync(srcPath, destPath);
        console.log(`  ✓ ${f.src}`);
    } else {
        console.log(`  ✗ ${f.src} (없음)`);
    }
}

// 3. node_modules 복사 (필수 패키지만)
console.log('\n[2/4] 의존성 설치 중...');
try {
    // 프로덕션 의존성만 설치
    execSync('npm install --production --omit=dev', { 
        cwd: distAppDir, 
        stdio: 'inherit' 
    });
    console.log('  ✓ 의존성 설치 완료');
} catch (e) {
    console.log('  ✗ 의존성 설치 실패:', e.message);
    // 기존 node_modules 복사 방식으로 폴백
    console.log('  기존 node_modules 복사 중...');
    const nodeModulesSrc = path.join(rootDir, 'node_modules');
    const nodeModulesDest = path.join(distAppDir, 'node_modules');
    if (fs.existsSync(nodeModulesSrc)) {
        execSync(`xcopy "${nodeModulesSrc}" "${nodeModulesDest}" /E /I /Q /Y`, { stdio: 'inherit' });
        console.log('  ✓ node_modules 복사 완료');
    }
}

// 4. Launcher BAT 파일 생성
console.log('\n[3/4] Launcher 스크립트 생성 중...');
const launcherBat = `@echo off
chcp 65001 >nul 2>&1
title SDSearch - Samsung Doc Search

echo ============================================
echo   SDSearch - Samsung Doc Search v1.0
echo ============================================
echo.

:: Chrome CDP 포트 확인
netstat -an | findstr ":9222" >nul 2>&1
if %errorlevel% neq 0 (
    echo [경고] Chrome이 CDP 포트(9222)로 실행되지 않았습니다.
    echo        Chrome을 다음 명령으로 실행하세요:
    echo        chrome.exe --remote-debugging-port=9222
    echo.
    echo 5초 후 서버만 시작합니다...
    timeout /t 5 /nobreak >nul
)

:: 서버 실행 (백그라운드)
echo [1/2] SDSearch 서버 시작 중...
start /B node "%~dp0gui\server.js" > "%~dp0sd-search.log" 2>&1

:: 서버 대기
timeout /t 3 /nobreak >nul

:: 브라우저 열기
echo [2/2] 브라우저 열기...
start http://localhost:3120

echo.
echo ============================================
echo  SDSearch가 실행 중입니다!
echo  브라우저: http://localhost:3120
echo  종료하려면 이 창을 닫으세요.
echo ============================================
echo.

:: 서버 프로세스 대기 (창을 닫을 때까지)
cmd /k
`;

fs.writeFileSync(path.join(distAppDir, 'start.bat'), launcherBat);
console.log('  ✓ start.bat 생성');

// 자동 종료 BAT
const stopBat = `@echo off
echo SDSearch 서버를 종료합니다...
taskkill /f /im node.exe 2>nul
echo 완료.
timeout /t 2 /nobreak >nul
`;

fs.writeFileSync(path.join(distAppDir, 'stop.bat'), stopBat);
console.log('  ✓ stop.bat 생성');

// Chrome 실행 BAT
const chromeBat = `@echo off
echo Chrome을 CDP 모드로 실행합니다...
start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\\chrome-cdp-profile"
echo Chrome이 실행되었습니다.
echo 로그인 후 start.bat을 실행하세요.
timeout /t 3 /nobreak >nul
`;

fs.writeFileSync(path.join(distAppDir, 'start-chrome.bat'), chromeBat);
console.log('  ✓ start-chrome.bat 생성');

// 5. 결과 출력
console.log('\n[4/4] 빌드 완료!\n');
console.log('=== 빌드 결과 ===');
console.log(`위치: ${distAppDir}`);
console.log('\n실행 방법:');
console.log('  1. start-chrome.bat 실행 (Chrome CDP 모드)');
console.log('  2. Chrome에서 Mosaic/Confluence/AX HUB 로그인');
console.log('  3. start.bat 실행 (서버 + 브라우저 자동 실행)');
console.log('  4. 종료 시 stop.bat 실행');
console.log('\nEXE 변환 (선택사항):');
console.log('  Bat To Exe Converter (https://www.battoexeconverter.com/) 사용');
console.log('  start.bat → SDSearch.exe로 변환');

// 파일 크기 확인
try {
    const stats = fs.statSync(path.join(distAppDir, 'node_modules'));
    console.log('\n=== 폴더 크기 ===');
    const sizeCmd = `powershell -Command "(Get-ChildItem -Recurse '${distAppDir}' | Measure-Object -Property Length -Sum).Sum / 1MB"`;
    const size = execSync(sizeCmd, { encoding: 'utf8' }).trim();
    console.log(`전체 크기: ${parseFloat(size).toFixed(1)} MB`);
} catch (e) {}
