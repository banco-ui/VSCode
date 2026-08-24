/**
 * Yaong Tools - Preload 스크립트
 * 보안 브릿지: 메인 프로세스와 렌더러 프로세스 연결
 */

const { contextBridge, ipcRenderer } = require('electron');

// API 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // 파일 다이얼로그
  openFileDialog: (options) => ipcRenderer.invoke('open-file-dialog', options),
  openFolderDialog: (options) => ipcRenderer.invoke('open-folder-dialog', options),
  saveFileDialog: (options) => ipcRenderer.invoke('save-file-dialog', options),
  
  // 외부 링크 열기
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // 폴더/파일 경로 열기 (탐색기)
  openPath: (filePath) => ipcRenderer.invoke('open-path', filePath),

  
  // 파일 조작
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  createDirectory: (dirPath) => ipcRenderer.invoke('create-directory', dirPath),
  readDirectory: (dirPath) => ipcRenderer.invoke('read-directory', dirPath),
  
  // 스크립트 실행
  runScript: (scriptName, args) => ipcRenderer.invoke('run-script', scriptName, args),
  stopScript: (processId) => ipcRenderer.invoke('stop-script', processId),
  
  // 스크립트 이벤트 리스너
  onScriptOutput: (callback) => {
    ipcRenderer.on('script-output', (event, data) => callback(data));
  },
  onScriptExited: (callback) => {
    ipcRenderer.on('script-exited', (event, data) => callback(data));
  },
  removeScriptListeners: () => {
    ipcRenderer.removeAllListeners('script-output');
    ipcRenderer.removeAllListeners('script-exited');
  },
  
  // 설정
  readConfig: (configName) => ipcRenderer.invoke('read-config', configName),
  saveConfig: (configName, content) => ipcRenderer.invoke('save-config', configName, content),
  
  // 앱 정보
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getAppPath: (name) => ipcRenderer.invoke('get-app-path', name),
  
  // 로그
  readLogs: (options) => ipcRenderer.invoke('read-logs', options),
  
  // CSV 파싱
  parseCSV: (filePath) => ipcRenderer.invoke('parse-csv', filePath),
  
  // USM API 호출 (메인 프로세스)
  usmApiCall: (options) => ipcRenderer.invoke('usm-api-call', options),
  
  // 미니 PC 모니터링
  monitorGetStatus: () => ipcRenderer.invoke('monitor-get-status'),
  monitorCheckNow: () => ipcRenderer.invoke('monitor-check-now'),
  monitorSaveDevices: (devices) => ipcRenderer.invoke('monitor-save-devices', devices),
  monitorStart: () => ipcRenderer.invoke('monitor-start'),
  monitorStop: () => ipcRenderer.invoke('monitor-stop'),
  monitorPingTest: (ip) => ipcRenderer.invoke('monitor-ping-test', ip),
  
  // 플랫폼 정보
  platform: process.platform,


});

// 개발 모드에서 콘솔에 API 노출 알림
if (process.env.NODE_ENV === 'development') {
  console.log('Yaong Tools API loaded');
}
