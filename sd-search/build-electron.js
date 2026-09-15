/**
 * SDSearch Electron EXE 빌드 스크립트
 * 
 * electron-builder 없이 Electron 바이너리 + 폴더 형태로 직접 패키징
 * asar를 사용하지 않아 Playwright 등 네이티브 모듈 호환성 보장
 * 
 * 주의: node_modules에서 electron, electron-builder 등 devDependencies는 제외
 * 
 * 결과물: release/win-unpacked/SDSearch.exe
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const rootDir = __dirname;
const releaseDir = path.join(rootDir, 'release');
const appDir = path.join(releaseDir, 'win-unpacked');

// 상위 node_modules에서 electron 바이너리 찾기
let electronDist;
const localElectron = path.join(rootDir, 'node_modules', 'electron', 'dist');
const parentElectron = path.join(path.dirname(rootDir), 'node_modules', 'electron', 'dist');

if (fs.existsSync(path.join(localElectron, 'electron.exe'))) {
    electronDist = localElectron;
} else if (fs.existsSync(path.join(parentElectron, 'electron.exe'))) {
    electronDist = parentElectron;
} else {
    console.error('ERROR: electron.exe not found!');
    console.error(`  Checked: ${localElectron}`);
    console.error(`  Checked: ${parentElectron}`);
    process.exit(1);
}

// 빌드 결과물에서 제외할 패키지들 (devDependencies)
const EXCLUDE_PACKAGES = [
    'electron',
    'electron-builder',
    'electron-builder-squirrel-windows',
    'electron-publish',
];

console.log('=== SDSearch Electron Packaging (no asar) ===\n');
console.log(`Electron binary: ${electronDist}\n`);

// 1. release 폴더 정리
if (fs.existsSync(appDir)) {
    fs.rmSync(appDir, { recursive: true, force: true });
}
fs.mkdirSync(appDir, { recursive: true });

// 2. Electron 바이너리 복사
console.log('[1/3] Copying Electron binary...');
execSync(`xcopy "${electronDist}" "${appDir}" /E /I /Q /Y`, { stdio: 'inherit' });
console.log('  OK\n');

// 3. app 폴더에 앱 소스 직접 복사 (asar 없이)
console.log('[2/3] Copying app files...');
const appResourcesDir = path.join(appDir, 'resources', 'app');
if (!fs.existsSync(appResourcesDir)) {
    fs.mkdirSync(appResourcesDir, { recursive: true });
}

const copyItems = [
    'electron',
    'gui',
    'adapters',
    'core',
    'config',
    'node_modules',
    'package.json'
];

for (const item of copyItems) {
    const src = path.join(rootDir, item);
    const dest = path.join(appResourcesDir, item);
    if (fs.existsSync(src)) {
        if (fs.statSync(src).isDirectory()) {
            execSync(`xcopy "${src}" "${dest}" /E /I /Q /Y`, { stdio: 'pipe' });
        } else {
            fs.copyFileSync(src, dest);
        }
        console.log(`  Copied: ${item}`);
    }
}

// node_modules에서 제외 패키지 삭제
console.log('\n  Excluding dev packages...');
const nodeModulesDir = path.join(appResourcesDir, 'node_modules');
for (const pkg of EXCLUDE_PACKAGES) {
    const pkgPath = path.join(nodeModulesDir, pkg);
    if (fs.existsSync(pkgPath)) {
        fs.rmSync(pkgPath, { recursive: true, force: true });
        console.log(`  Removed: ${pkg}`);
    }
}
console.log('  OK\n');

// 4. 깨끗한 package.json 생성 (devDependencies 제거)
console.log('[3/3] Writing clean package.json...');
const cleanPkg = {
    name: 'sd-search',
    version: '1.0.0',
    description: 'Samsung Doc Search - Mosaic, Confluence, AX HUB integrated search tool',
    main: 'electron/main.js'
};
fs.writeFileSync(
    path.join(appResourcesDir, 'package.json'),
    JSON.stringify(cleanPkg, null, 2)
);
console.log('  OK\n');

// 5. electron.exe를 SDSearch.exe로 이름 변경
console.log('Renaming electron.exe to SDSearch.exe...');
const oldExe = path.join(appDir, 'electron.exe');
const newExe = path.join(appDir, 'SDSearch.exe');
fs.renameSync(oldExe, newExe);
console.log('  OK\n');

// 6. 결과 출력
console.log('=== Build complete! ===');
console.log(`Output: ${appDir}`);
console.log(`EXE: ${newExe}`);

// 폴더 크기
try {
    const size = execSync(`powershell -Command "(Get-ChildItem -Recurse '${appDir}' | Measure-Object -Property Length -Sum).Sum / 1MB"`, { encoding: 'utf8' }).trim();
    console.log(`Size: ${parseFloat(size).toFixed(1)} MB`);
} catch (e) {}

console.log('\n실행 방법:');
console.log(`  ${newExe}`);
console.log('  또는 start "" "C:\\sd-search-build\\release\\win-unpacked\\SDSearch.exe"');
