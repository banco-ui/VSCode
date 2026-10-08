/**
 * CDP Launcher
 * Chrome을 --remote-debugging-port 로 자동 실행하여 CDP 연결을 보장.
 *
 * 동작 흐름:
 * 1. 포트 9222에 CDP가 이미 열려 있으면 OK
 * 2. Chrome이 실행 중이 아니면 사용자 기본 프로필 + CDP 포트로 실행
 * 3. Chrome이 이미 실행 중이면 전용 SDSearch 프로필 + CDP 포트로 별도 실행
 * 4. CDP 가 준비될 때까지 최대 15초 대기
 */
const { exec, execFile, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');

// ── Chrome 실행 파일 탐색 ──────────────────────────────────────
function findChrome() {
    const candidates = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        path.join(os.homedir(), 'AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'),
        // Edge fallback
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    ];
    for (const p of candidates) {
        if (fs.existsSync(p)) return p;
    }
    return null;
}

// ── Chrome 프로세스 실행 여부 확인 ────────────────────────────
function isChromeRunning() {
    return new Promise((resolve) => {
        exec('tasklist /FI "IMAGENAME eq chrome.exe" /NH', (err, stdout) => {
            if (err) {
                // Edge 도 확인
                exec('tasklist /FI "IMAGENAME eq msedge.exe" /NH', (e2, s2) => {
                    resolve(!e2 && s2 && !s2.includes('INFO: No tasks'));
                });
                return;
            }
            resolve(stdout && !stdout.includes('INFO: No tasks'));
        });
    });
}

// ── CDP 포트 사용 가능 여부 확인 ───────────────────────────────
function isCDPReady(port, timeout = 3000) {
    return new Promise((resolve) => {
        let settled = false;
        const done = (val) => { if (!settled) { settled = true; resolve(val); } };
        const req = http.get(
            `http://127.0.0.1:${port}/json/version`,
            { timeout },
            (res) => {
                let data = '';
                res.on('data', (c) => { data += c; });
                res.on('end', () => {
                    try {
                        const json = JSON.parse(data);
                        done(!!json.webSocketDebuggerUrl);
                    } catch {
                        done(false);
                    }
                });
            }
        );
        req.on('error', () => done(false));
        req.on('timeout', () => { req.destroy(); done(false); });
    });
}

// ── Chrome 실행 (CDP 포트 활성화) ─────────────────────────────
function launchChromeWithCDP(port, useDefaultProfile) {
    const chromePath = findChrome();
    if (!chromePath) {
        console.error('[CDP-Launcher] Chrome 실행 파일을 찾을 수 없습니다.');
        return false;
    }

    const args = [
        `--remote-debugging-port=${port}`,
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-features=Translate',
    ];

    if (useDefaultProfile) {
        // 사용자 기본 Chrome 프로필 (기존 로그인 세션 유지)
        const defaultProfile = path.join(os.homedir(), 'AppData\\Local\\Google\\Chrome\\User Data');
        if (fs.existsSync(defaultProfile)) {
            args.push(`--user-data-dir=${defaultProfile}`);
        }
    } else {
        // 전용 SDSearch 프로필 (Chrome이 이미 실행 중일 때)
        const sdsearchProfile = path.join(os.homedir(), 'AppData\\Local\\sdsearch\\chrome-profile');
        if (!fs.existsSync(sdsearchProfile)) {
            fs.mkdirSync(sdsearchProfile, { recursive: true });
        }
        args.push(`--user-data-dir=${sdsearchProfile}`);
    }

    try {
        // detached 로 실행 (앱이 종료되어도 Chrome 유지)
        const child = spawn(chromePath, args, {
            detached: true,
            stdio: 'ignore',
            windowsHide: false,
        });
        child.unref();
        // spawn 에러 감지 (프로세스 시작 실패 시)
        child.on('error', (e) => {
            console.error('[CDP-Launcher] Chrome 프로세스 시작 실패:', e.message);
        });
        console.log(`[CDP-Launcher] Chrome 실행: ${chromePath} (포트 ${port}, ${useDefaultProfile ? '기본 프로필' : 'SDSearch 전용 프로필'})`);
        return true;
    } catch (e) {
        console.error('[CDP-Launcher] Chrome 실행 실패:', e.message);
        return false;
    }
}

// ── CDP 보장 (메인 함수) ───────────────────────────────────────
let _ensurePromise = null;

async function ensureCDP(port = 9222) {
    // 이미 실행 중이면 대기
    if (_ensurePromise) return _ensurePromise;
    _ensurePromise = _doEnsureCDP(port).finally(() => { _ensurePromise = null; });
    return _ensurePromise;
}

async function _doEnsureCDP(port) {
    // 1. 이미 CDP 가 열려 있으면 OK
    if (await isCDPReady(port)) {
        console.log(`[CDP-Launcher] CDP 이미 실행 중 (포트 ${port})`);
        return true;
    }

    console.log(`[CDP-Launcher] CDP 포트 ${port} 연결 안됨. Chrome 자동 실행 시도...`);

    // 2. Chrome 이 실행 중인지 확인
    const chromeRunning = await isChromeRunning();

    // 3. Chrome 실행
    //    - Chrome 이 실행 중이 아니면 기본 프로필 사용 (기존 로그인 세션 활용)
    //    - Chrome 이 이미 실행 중이면 전용 프로필 사용 (CDP 활성화 보장)
    const launched = launchChromeWithCDP(port, !chromeRunning);
    if (!launched) return false;

    // 4. CDP 준비될 때까지 대기 (최대 60초, 새 프로필 초기화 시 시간 소요)
    for (let i = 0; i < 60; i++) {
        await new Promise(r => setTimeout(r, 1000));
        if (await isCDPReady(port)) {
            console.log(`[CDP-Launcher] CDP 준비 완료 (포트 ${port}, ${(i + 1)}초 대기)`);
            if (chromeRunning) {
                console.log('[CDP-Launcher] 전용 프로필로 실행됨. 최초 1회 로그인이 필요할 수 있습니다.');
            }
            return true;
        }
    }

    console.error(`[CDP-Launcher] CDP 준비 시간 초과 (포트 ${port})`);
    return false;
}

module.exports = { ensureCDP, isCDPReady, findChrome };
