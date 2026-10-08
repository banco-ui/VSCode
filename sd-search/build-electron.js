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

// 빌드 결과물에서 완전히 제외할 패키지들 (빌드 도구, 실행 시 불필요)
// 주의: electron 패키지는 제외하지 않음 (require('electron')이 작동해야 함)
//       단, electron/dist (electron.exe 복사본)는 별도로 제거
const EXCLUDE_PACKAGES = [
    // electron-builder 관련 (빌드 도구, 실행 시 불필요)
    'electron-builder',
    'electron-builder-squirrel-windows',
    'electron-publish',
    'app-builder-bin',
    'app-builder-lib',
    '7zip-bin',
    '@electron-internal',
    // TypeScript (빌드 도구)
    'typescript',
    // 타입 정의 (실행 시 불필요)
    '@types',
    // node-gyp (빌드 도구)
    'node-gyp',
    // 기타 빌드 도구
    'dmg-builder',
    'builder-util',
    'builder-util-runtime',
    'fs-extra',
    'stat-mode',
    'dotenv',
    'globby',
];

// electron 패키지 내에서 제거할 하위 디렉토리 (electron.exe 복사본, 약 238MB)
const ELECTRON_DIST_TO_REMOVE = ['dist', 'path.txt', 'download-url.txt'];



// node_modules 내에서 제외할 하위 디렉토리들 (Playwright 브라우저 바이너리 등)
const EXCLUDE_DIRS = [
    '.local-browsers',    // Playwright 브라우저 바이너리 (CDP 연결만 사용하므로 불필요)
    '.bin',               // CLI 실행 파일
    '.cache',             // 캐시
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

// node_modules 위치 찾기 (sd-search 내부 또는 상위 디렉토리)
let nodeModulesSrc = path.join(rootDir, 'node_modules');
if (!fs.existsSync(nodeModulesSrc)) {
    nodeModulesSrc = path.join(path.dirname(rootDir), 'node_modules');
    if (!fs.existsSync(nodeModulesSrc)) {
        console.error('ERROR: node_modules not found!');
        process.exit(1);
    }
    console.log(`  Using parent node_modules: ${nodeModulesSrc}`);
}

const copyItems = [
    'electron',
    'gui',
    'adapters',
    'core',
    'config',
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

// node_modules 별도 복사 (상위 디렉토리일 수 있음)
const destNodeModules = path.join(appResourcesDir, 'node_modules');
console.log(`  Copying node_modules from: ${nodeModulesSrc}`);
execSync(`xcopy "${nodeModulesSrc}" "${destNodeModules}" /E /I /Q /Y`, { stdio: 'pipe' });
console.log('  Copied: node_modules');


// node_modules에서 제외 패키지 및 불필요한 디렉토리 삭제
console.log('\n  Excluding dev packages and large binaries...');
const nodeModulesDir = path.join(appResourcesDir, 'node_modules');
for (const pkg of EXCLUDE_PACKAGES) {
    const pkgPath = path.join(nodeModulesDir, pkg);
    if (fs.existsSync(pkgPath)) {
        fs.rmSync(pkgPath, { recursive: true, force: true });
        console.log(`  Removed: ${pkg}`);
    }
}

// Playwright 브라우저 바이너리 등 대용량 디렉토리 제거
function removeDirRecursive(dirPath) {
    if (fs.existsSync(dirPath)) {
        fs.rmSync(dirPath, { recursive: true, force: true });
        return true;
    }
    return false;
}

// node_modules 하위의 제외 디렉토리들
for (const dir of EXCLUDE_DIRS) {
    const dirPath = path.join(nodeModulesDir, dir);
    if (removeDirRecursive(dirPath)) {
        console.log(`  Removed: node_modules/${dir}`);
    }
}

// playwright-core 내의 브라우저 바이너리 경로 제거 (CDP 연결만 사용)
const playwrightCorePath = path.join(nodeModulesDir, 'playwright-core');
if (fs.existsSync(playwrightCorePath)) {
    const pwBinPath = path.join(playwrightCorePath, '.local-browsers');
    if (removeDirRecursive(pwBinPath)) {
        console.log('  Removed: playwright-core/.local-browsers');
    }
}

// electron 패키지 내의 dist 폴더 제거 (electron.exe 복사본, 약 238MB)
// require('electron')은 index.js만 필요하므로 dist는 불필요
const electronPkgPath = path.join(nodeModulesDir, 'electron');
if (fs.existsSync(electronPkgPath)) {
    for (const item of ELECTRON_DIST_TO_REMOVE) {
        const itemPath = path.join(electronPkgPath, item);
        if (removeDirRecursive(itemPath)) {
            console.log(`  Removed: electron/${item}`);
        } else if (fs.existsSync(itemPath)) {
            fs.unlinkSync(itemPath);
            console.log(`  Removed: electron/${item}`);
        }
    }
    // path.txt 재생성 (SDSearch.exe 경로로)
    const pathTxt = path.join(electronPkgPath, 'path.txt');
    fs.writeFileSync(pathTxt, '');
    console.log('  Created: electron/path.txt (empty)');
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
console.log(`  또는 start "" "${path.join(appDir, 'SDSearch.exe').replace(/\\/g, '\\\\')}"`);
