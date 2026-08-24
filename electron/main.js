/**
 * Yaong Tools - Electron 메인 프로세스
 * USM Automation Hub
 */

const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

// 개발 모드 감지
const isDev = process.argv.includes('--dev') || process.env.NODE_ENV === 'development';

let mainWindow;
let runningProcesses = new Map();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    title: 'Yaong Tools',
  });

  // 개발 모드에서는 로컬 서버, 프로덕션에서는 빌드된 파일 로드
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist-electron/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // 모든 실행 중인 프로세스 정리
  runningProcesses.forEach((proc, id) => {
    if (proc && !proc.killed) {
      proc.kill();
    }
  });
  runningProcesses.clear();
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// ============================================
// IPC Handlers
// ============================================

// 파일 다이얼로그 열기
ipcMain.handle('open-file-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

// 폴더 다이얼로그 열기
ipcMain.handle('open-folder-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    ...options,
    properties: ['openDirectory'],
  });
  return result;
});

// 파일 저장 다이얼로그
ipcMain.handle('save-file-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

// 외부 URL 열기
ipcMain.handle('open-external', async (event, url) => {
  await shell.openExternal(url);
});

// 폴더/파일 경로 열기 (탐색기)
ipcMain.handle('open-path', async (event, filePath) => {
  try {
    await shell.openPath(filePath);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});


// 파일 내용 읽기
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return { success: true, content };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 파일 쓰기
ipcMain.handle('write-file', async (event, filePath, content) => {
  try {
    fs.writeFileSync(filePath, content, 'utf-8');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 디렉토리 생성
ipcMain.handle('create-directory', async (event, dirPath) => {
  try {
    fs.mkdirSync(dirPath, { recursive: true });
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 디렉토리 목록 읽기
ipcMain.handle('read-directory', async (event, dirPath) => {
  try {
    const files = fs.readdirSync(dirPath);
    return { success: true, files };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 스크립트 실행 (env 옵션 지원: run-script(scriptName, args, env))
ipcMain.handle('run-script', async (event, scriptName, args = [], extraEnv = {}) => {
  return new Promise((resolve) => {

    // scripts/ 폴더 또는 프로젝트 루트 하위 경로 모두 지원
    // asar 환경에서는 app.asar.unpacked 경로 사용
    let scriptPath;
    const rootPath = path.join(__dirname, '..');
    // asar.unpacked 경로 처리 (패키징 환경)
    const unpackedRoot = rootPath.includes('app.asar')
      ? rootPath.replace('app.asar', 'app.asar.unpacked')
      : rootPath;
    const scriptsPath = path.join(rootPath, 'scripts', scriptName);
    const scriptsPathUnpacked = path.join(unpackedRoot, 'scripts', scriptName);
    const directPath = path.join(rootPath, scriptName);
    const directPathUnpacked = path.join(unpackedRoot, scriptName);


    // unpacked 경로를 우선 확인 (패키징 환경에서 스크립트가 asar 밖에 있음)
    if (fs.existsSync(scriptsPathUnpacked)) {
      scriptPath = scriptsPathUnpacked;
    } else if (fs.existsSync(directPathUnpacked)) {
      scriptPath = directPathUnpacked;
    } else if (fs.existsSync(scriptsPath)) {
      // asar 내부에 있으면 unpacked 경로로 강제 리다이렉트
      scriptPath = scriptsPath.includes('app.asar') ? scriptsPathUnpacked : scriptsPath;
    } else if (fs.existsSync(directPath)) {
      scriptPath = directPath.includes('app.asar') ? directPathUnpacked : directPath;
    } else {
      // 경로에 디렉토리 구분자가 있으면 unpacked 또는 루트 기준으로 처리
      if (scriptName.includes('\\') || scriptName.includes('/')) {
        const unpackedSubPath = path.join(unpackedRoot, scriptName);
        scriptPath = fs.existsSync(unpackedSubPath) ? unpackedSubPath : path.join(rootPath, scriptName);
      } else {
        scriptPath = scriptsPathUnpacked;
      }
    }

    // 디버깅: 스크립트 경로 로그
    console.log(`[DRM-DEBUG] scriptName: ${scriptName}`);
    console.log(`[DRM-DEBUG] rootPath: ${rootPath}`);
    console.log(`[DRM-DEBUG] unpackedRoot: ${unpackedRoot}`);
    console.log(`[DRM-DEBUG] scriptsPath: ${scriptsPath}`);
    console.log(`[DRM-DEBUG] scriptsPathUnpacked: ${scriptsPathUnpacked}`);
    console.log(`[DRM-DEBUG] selected scriptPath: ${scriptPath}`);
    console.log(`[DRM-DEBUG] scriptPath exists: ${fs.existsSync(scriptPath)}`);



    const processId = `${scriptName}-${Date.now()}`;
    
    // .bat 파일은 cmd로 실행, .js 파일은 node로 실행
    const isBat = scriptPath.toLowerCase().endsWith('.bat');
    
    // 시스템 node 실행파일 찾기 (Electron의 ELECTRON_RUN_AS_NODE 대신 실제 node 사용)
    const nodeExe = process.env.NODE_EXE || 'node';
    
    const proc = isBat
      ? spawn('cmd', ['/c', scriptPath, ...args], {
          cwd: unpackedRoot,
          env: { ...process.env, FORCE_COLOR: '0', ...extraEnv },
        })
      : spawn(nodeExe, [scriptPath, ...args], {
          cwd: unpackedRoot,
          env: { ...process.env, FORCE_COLOR: '0', ...extraEnv },
        });





    runningProcesses.set(processId, proc);

    let output = '';
    let errorOutput = '';

    proc.stdout.on('data', (data) => {
      output += data.toString();
      mainWindow.webContents.send('script-output', {
        processId,
        type: 'stdout',
        data: data.toString(),
      });
    });

    proc.stderr.on('data', (data) => {
      errorOutput += data.toString();
      mainWindow.webContents.send('script-output', {
        processId,
        type: 'stderr',
        data: data.toString(),
      });
    });

    proc.on('close', (code) => {
      runningProcesses.delete(processId);
      mainWindow.webContents.send('script-exited', {
        processId,
        code,
        output,
        error: errorOutput,
      });
      resolve({
        success: code === 0,
        code,
        output,
        error: errorOutput,
        processId,
      });
    });

    proc.on('error', (err) => {
      runningProcesses.delete(processId);
      resolve({
        success: false,
        error: err.message,
        processId,
      });
    });

    // 프로세스 ID 즉시 반환
    setTimeout(() => {
      resolve({ success: true, processId });
    }, 100);
  });
});

// 프로세스 중지
ipcMain.handle('stop-script', async (event, processId) => {
  const proc = runningProcesses.get(processId);
  if (proc) {
    proc.kill();
    runningProcesses.delete(processId);
    return { success: true };
  }
  return { success: false, error: 'Process not found' };
});

// 설정 파일 읽기
ipcMain.handle('read-config', async (event, configName) => {
  try {
    const configPath = path.join(__dirname, '../config', configName);
    if (fs.existsSync(configPath)) {
      const content = fs.readFileSync(configPath, 'utf-8');
      return { success: true, content: JSON.parse(content) };
    }
    return { success: true, content: {} };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 설정 파일 저장
ipcMain.handle('save-config', async (event, configName, content) => {
  try {
    const configPath = path.join(__dirname, '../config', configName);
    fs.writeFileSync(configPath, JSON.stringify(content, null, 2), 'utf-8');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 앱 버전 가져오기
ipcMain.handle('get-app-version', async () => {
  try {
    const pkgPath = path.join(__dirname, '../package.json');
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    return pkg.version;
  } catch {
    return '1.0.0';
  }
});

// 로그 파일 읽기
ipcMain.handle('read-logs', async (event, options = {}) => {
  try {
    const { file = 'provisioning.log', lines = 100 } = options;
    const logPath = path.join(__dirname, '../logs', file);
    
    if (!fs.existsSync(logPath)) {
      return { success: true, content: [] };
    }

    const content = fs.readFileSync(logPath, 'utf-8');
    const allLines = content.split('\n');
    const recentLines = allLines.slice(-lines);
    
    return { success: true, content: recentLines };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// CSV 파일 파싱
ipcMain.handle('parse-csv', async (event, filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    const rows = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const row = {};
      headers.forEach((header, i) => {
        row[header] = values[i] || '';
      });
      return row;
    });
    return { success: true, headers, rows };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 앱 경로 가져오기
ipcMain.handle('get-app-path', async (event, name) => {
  const paths = {
    root: path.join(__dirname, '..'),
    scripts: path.join(__dirname, '../scripts'),
    config: path.join(__dirname, '../config'),
    logs: path.join(__dirname, '../logs'),
    output: path.join(__dirname, '../output'),
    templates: path.join(__dirname, '../csv_templates'),
  };
  return paths[name] || paths.root;
});

// USM API 호출 (메인 프로세스에서 fetch 사용 - CORS/인증서 문제 회피)
ipcMain.handle('usm-api-call', async (event, options) => {
  const https = require('https');
  const http = require('http');

  const { url, method = 'GET', body, timeout = 30000 } = options;

  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const lib = isHttps ? https : http;

    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method,
      headers: {
        'Authorization': 'Basic ' + Buffer.from('ossuser:osspasswd').toString('base64'),
        'Content-Type': 'application/json',
      },
      rejectUnauthorized: false, // 자체 서명 인증서 허용
    };

    if (body) {
      const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
      requestOptions.headers['Content-Length'] = Buffer.byteLength(bodyStr);
    }

    const req = lib.request(requestOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        let parsed;
        try {
          parsed = JSON.parse(data);
        } catch {
          parsed = data;
        }
        resolve({ success: true, statusCode: res.statusCode, body: parsed });
      });
    });

    req.on('error', (err) => {
      resolve({ success: false, error: err.message });
    });

    req.setTimeout(timeout, () => {
      req.destroy();
      resolve({ success: false, error: 'Request timeout' });
    });

    if (body) {
      const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
      req.write(bodyStr);
    }
    req.end();
  });
});

// ============================================
// 미니 PC 모니터링 IPC 핸들러
// ============================================

const monitorDevicesFile = path.join(__dirname, '..', 'mini-pc-monitor', 'devices.json');
const monitorStates = new Map();
let monitorInterval = null;
const MONITOR_INTERVAL_MS = 30000;
const MONITOR_FAILURES = 3;

function loadMonitorDevices() {
  try {
    if (fs.existsSync(monitorDevicesFile)) {
      const data = JSON.parse(fs.readFileSync(monitorDevicesFile, 'utf8'));
      return Array.isArray(data) ? data : [];
    }
  } catch (e) { console.error('장비 목록 읽기 오류:', e.message); }
  return [];
}

function saveMonitorDevices(devices) {
  try {
    fs.writeFileSync(monitorDevicesFile, JSON.stringify(devices, null, 2) + '\n', 'utf8');
  } catch (e) { console.error('장비 목록 저장 오류:', e.message); }
}

function pingDevice(ip) {
  return new Promise((resolve) => {
    const { execFile } = require('child_process');
    execFile('ping.exe', ['-n', '1', '-w', '1500', ip], { windowsHide: true, timeout: 3000 }, (error, stdout) => {
      const ok = !error && /TTL=/i.test(stdout);
      const latency = ok ? Number((stdout.match(/(?:time|시간)[=<](\d+)ms/i) || [])[1]) : null;
      resolve({ ok, latency });
    });
  });
}

async function checkMonitorDevice(device) {
  if (!device.enabled) return;
  const previous = monitorStates.get(device.id) || { failures: 0, status: 'unknown', events: [] };
  const result = await pingDevice(device.ip);
  const now = new Date().toISOString();
  const failures = result.ok ? 0 : previous.failures + 1;
  const status = result.ok ? 'online' : (failures >= MONITOR_FAILURES ? 'offline' : 'degraded');
  const events = previous.events || [];
  if (previous.status !== status && status !== 'degraded') {
    events.unshift({ at: now, type: status, message: status === 'offline' ? '장애 감지' : '정상 복구' });
    events.splice(30);
  }
  monitorStates.set(device.id, {
    status, failures, latency: result.latency, checkedAt: now,
    lastOnlineAt: result.ok ? now : previous.lastOnlineAt || null, events,
  });
}

async function checkAllMonitorDevices() {
  const devices = loadMonitorDevices();
  const enabled = devices.filter(d => d.enabled);
  // 동시 ping 개수 제한 (한 번에 최대 10대)
  const BATCH_SIZE = 10;
  for (let i = 0; i < enabled.length; i += BATCH_SIZE) {
    const batch = enabled.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(checkMonitorDevice));
  }
}


function getMonitorStatus() {
  const devices = loadMonitorDevices();
  const rows = devices.map((device) => {
    const state = monitorStates.get(device.id);
    return {
      ...device,
      status: device.enabled ? (state?.status || 'checking') : 'disabled',
      failures: state?.failures || 0,
      latency: state?.latency ?? null,
      checkedAt: state?.checkedAt || null,
      lastOnlineAt: state?.lastOnlineAt || null,
      events: state?.events || [],
    };
  });
  return { rows, checkedIntervalSeconds: MONITOR_INTERVAL_MS / 1000, failuresBeforeOffline: MONITOR_FAILURES, serverTime: new Date().toISOString() };
}

// 모니터 장비 상태 조회
ipcMain.handle('monitor-get-status', async () => {
  return { success: true, data: getMonitorStatus() };
});

// 즉시 검사
ipcMain.handle('monitor-check-now', async () => {
  await checkAllMonitorDevices();
  return { success: true, data: getMonitorStatus() };
});

// 장비 목록 저장
ipcMain.handle('monitor-save-devices', async (event, devices) => {
  saveMonitorDevices(devices);
  await checkAllMonitorDevices();
  return { success: true, data: getMonitorStatus() };
});

// 모니터링 시작
ipcMain.handle('monitor-start', async () => {
  if (monitorInterval) return { success: true, message: 'already running' };
  await checkAllMonitorDevices();
  monitorInterval = setInterval(checkAllMonitorDevices, MONITOR_INTERVAL_MS);
  return { success: true, message: 'started' };
});

// 모니터링 중지
ipcMain.handle('monitor-stop', async () => {
  if (monitorInterval) {
    clearInterval(monitorInterval);
    monitorInterval = null;
  }
  return { success: true, message: 'stopped' };
});

// Ping 테스트 (cmd 창 열기)
ipcMain.handle('monitor-ping-test', async (event, ip) => {
  const { spawn } = require('child_process');
  spawn('cmd', ['/c', `start cmd /k ping ${ip} -n 4`], { detached: true, shell: true });
  return { success: true };
});



