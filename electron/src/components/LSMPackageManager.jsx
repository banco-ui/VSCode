import { useState, useEffect, useRef } from 'react';

function LSMPackageManager() {
  const [lsmIp, setLsmIp] = useState('10.251.175.31');
  const [packageFile, setPackageFile] = useState('');
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState('idle');
  const [output, setOutput] = useState([]);
  const [processId, setProcessId] = useState(null);
  const fileInputRef = useRef(null);
  const logEndRef = useRef(null);

  const quickIps = [
    { ip: '10.251.175.31', label: '10.251.175.31 (개발)' },
    { ip: '10.251.175.32', label: '10.251.175.32' },
    { ip: '10.251.175.33', label: '10.251.175.33' },
    { ip: '10.251.175.34', label: '10.251.175.34' },
  ];

  useEffect(() => {
    setupScriptListeners();
    return () => {
      window.electronAPI?.removeScriptListeners();
    };
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [output]);

  const setupScriptListeners = () => {
    window.electronAPI?.onScriptOutput((data) => {
      const line = data.data;
      let level = 'INFO';
      let statusColor = null;

      if (line.includes('[ERROR]') || line.includes('오류') || line.includes('실패')) {
        level = 'ERROR';
        statusColor = 'error';
      } else if (line.includes('[WARN]')) {
        level = 'WARN';
        statusColor = 'warning';
      } else if (line.includes('완료') || line.includes('성공')) {
        statusColor = 'success';
      }

      // 버전 목록 파싱
      if (line.startsWith('VERSIONS_JSON:')) {
        try {
          const v = JSON.parse(line.replace('VERSIONS_JSON:', ''));
          setVersions(v);
          if (v.length > 0) setSelectedVersion(v[0]);
        } catch (e) {}
      }

      const timestamp = new Date().toLocaleTimeString('ko-KR');
      setOutput((prev) => [...prev, { timestamp, level, message: line, status: statusColor }]);
    });

    window.electronAPI?.onScriptExited((data) => {
      setIsRunning(false);
      if (data.code === 0) {
        setStatus('done');
        setOutput((prev) => [...prev, {
          timestamp: new Date().toLocaleTimeString('ko-KR'),
          level: 'INFO',
          message: `■ 작업 완료 (종료 코드: ${data.code})`,
          status: 'success',
        }]);
      } else {
        setStatus('error');
        setOutput((prev) => [...prev, {
          timestamp: new Date().toLocaleTimeString('ko-KR'),
          level: 'ERROR',
          message: `■ 작업 실패 (종료 코드: ${data.code})`,
          status: 'error',
        }]);
      }
    });
  };

  const handleBrowse = async () => {
    const result = await window.electronAPI?.openFileDialog({
      title: '설치할 패키지 파일을 선택하세요',
      filters: [
        { name: 'TAR GZ files', extensions: ['tar.gz'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });
    if (result?.filePaths?.[0]) {
      setPackageFile(result.filePaths[0]);
    }
  };

  const handleUpload = async () => {
    if (!lsmIp || !packageFile) {
      alert('장비 주소와 패키지 파일을 모두 입력해야 합니다.');
      return;
    }
    setIsRunning(true);
    setStatus('running');
    setOutput([{
      timestamp: new Date().toLocaleTimeString('ko-KR'),
      level: 'INFO',
      message: `▶ 파일 업로드 시작: ${packageFile} -> ${lsmIp}`,
      status: null,
    }]);
    try {
      const result = await window.electronAPI?.runScript('lsm-package-manager.js', [
        '--ip', lsmIp, '--action', 'upload', '--file', packageFile,
      ]);
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setStatus('error');
      setOutput((prev) => [...prev, {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'ERROR',
        message: `오류: ${error.message}`,
        status: 'error',
      }]);
    }
  };

  const handleFetchVersions = async () => {
    if (!lsmIp) {
      alert('장비 주소를 입력해야 합니다.');
      return;
    }
    setIsRunning(true);
    setStatus('running');
    setOutput([{
      timestamp: new Date().toLocaleTimeString('ko-KR'),
      level: 'INFO',
      message: `▶ 버전 목록 조회: ${lsmIp}`,
      status: null,
    }]);
    try {
      const result = await window.electronAPI?.runScript('lsm-package-manager.js', [
        '--ip', lsmIp, '--action', 'versions',
      ]);
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setStatus('error');
      setOutput((prev) => [...prev, {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'ERROR',
        message: `오류: ${error.message}`,
        status: 'error',
      }]);
    }
  };

  const handleApply = async () => {
    if (!lsmIp || !selectedVersion || !packageFile) {
      alert('장비 주소, 적용 버전, 패키지 파일이 모두 필요합니다.');
      return;
    }
    const confirmed = window.confirm(
      `원격 장비에 선택한 패키지를 적용합니다.\n` +
      `이 작업은 시스템 설정을 변경하며 시간이 걸릴 수 있습니다.\n` +
      `계속하시겠습니까?`
    );
    if (!confirmed) return;

    setIsRunning(true);
    setStatus('running');
    setOutput([{
      timestamp: new Date().toLocaleTimeString('ko-KR'),
      level: 'INFO',
      message: `▶ 패키지 적용 시작: ${selectedVersion} (${lsmIp})`,
      status: null,
    }]);
    try {
      const result = await window.electronAPI?.runScript('lsm-package-manager.js', [
        '--ip', lsmIp, '--action', 'apply', '--version', selectedVersion, '--file', packageFile,
      ]);
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setStatus('error');
      setOutput((prev) => [...prev, {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'ERROR',
        message: `오류: ${error.message}`,
        status: 'error',
      }]);
    }
  };

  const handleStop = async () => {
    if (processId) {
      await window.electronAPI?.stopScript(processId);
      setIsRunning(false);
      setStatus('idle');
      setOutput((prev) => [...prev, {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'WARN',
        message: '■ 작업 중지됨',
        status: 'warning',
      }]);
    }
  };

  const handleClearLog = () => setOutput([]);

  const statusConfig = {
    idle: { class: 'status-idle', text: '대기 중' },
    running: { class: 'status-running', text: '실행 중...' },
    done: { class: 'status-done', text: '완료' },
    error: { class: 'status-error', text: '실패' },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.headerTitle}>📦 LSM eNB 패키지 적용</h1>
        <span style={{ ...styles.statusBadge, ...styles[statusConfig[status].class] }}>
          {statusConfig[status].text}
        </span>
      </div>

      {/* 1. 원격 장비 정보 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>1. 원격 장비 정보</h2>
        <div style={styles.formRow}>
          <label style={styles.formLabel}>장비 주소 (IP)</label>
          <input
            type="text"
            value={lsmIp}
            onChange={(e) => setLsmIp(e.target.value)}
            placeholder="10.251.175.31"
            style={styles.input}
            disabled={isRunning}
          />
        </div>
        <div style={styles.quickIps}>
          <span style={styles.quickIpLabel}>빠른 선택:</span>
          {quickIps.map((qip) => (
            <button
              key={qip.ip}
              onClick={() => setLsmIp(qip.ip)}
              style={{ ...styles.quickIp, ...(lsmIp === qip.ip ? styles.quickIpActive : {}) }}
              disabled={isRunning}
            >
              {qip.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. 패키지 파일 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>2. 패키지 파일</h2>
        <div style={styles.formRow}>
          <label style={styles.formLabel}>설치 패키지 (.tar.gz)</label>
          <div style={styles.fileRow}>
            <input
              type="text"
              value={packageFile}
              readOnly
              placeholder="파일을 선택하세요"
              style={{ ...styles.input, color: packageFile ? '#3fb950' : '#666' }}
            />
            <button onClick={handleBrowse} style={styles.btnBrowse} disabled={isRunning}>
              📁 파일 찾기
            </button>
          </div>
        </div>
        <button onClick={handleUpload} style={styles.btnAction} disabled={isRunning || !packageFile}>
          ⬆ File Upload
        </button>
      </div>

      {/* 3. 적용 버전 선택 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>3. 적용 버전 선택</h2>
        <button onClick={handleFetchVersions} style={styles.btnAction} disabled={isRunning}>
          📋 적용 패키지 버전 가져오기
        </button>
        <div style={styles.formRow}>
          <label style={styles.formLabel}>적용할 버전</label>
          <select
            value={selectedVersion}
            onChange={(e) => setSelectedVersion(e.target.value)}
            style={styles.select}
            disabled={isRunning || versions.length === 0}
          >
            {versions.length === 0 ? (
              <option value="">버전을 먼저 가져오세요</option>
            ) : (
              versions.map((v) => <option key={v} value={v}>{v}</option>)
            )}
          </select>
        </div>
      </div>

      {/* 4. 패키지 적용 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>4. 패키지 적용</h2>
        {!isRunning ? (
          <button onClick={handleApply} style={styles.btnRun} disabled={!selectedVersion || !packageFile}>
            ▶ 패키지 적용
          </button>
        ) : (
          <button onClick={handleStop} style={styles.btnStop}>
            ■ 중지
          </button>
        )}
      </div>

      {/* 로그 패널 */}
      <div style={styles.logPanel}>
        <div style={styles.logHeader}>
          <h2 style={styles.panelTitle}>📋 진행 상태 및 로그</h2>
          <button onClick={handleClearLog} style={styles.btnClear}>
            로그 지우기
          </button>
        </div>
        <div style={styles.logContent}>
          {output.length === 0 ? (
            <div style={styles.logEmpty}>
              LSM eNB 패키지 적용 도구입니다. 장비 IP를 입력하고 패키지 파일을 선택하세요.
            </div>
          ) : (
            output.map((log, i) => (
              <div key={i} style={styles.logLine}>
                <span style={styles.logTime}>{log.timestamp}</span>
                <span style={{
                  ...styles.logMsg,
                  ...(log.status === 'success' ? { color: '#3fb950' } : {}),
                  ...(log.status === 'warning' ? { color: '#d29922' } : {}),
                  ...(log.status === 'error' ? { color: '#f85149' } : {}),
                  ...(log.level === 'ERROR' && !log.status ? { color: '#f85149' } : {}),
                  ...(log.level === 'WARN' && !log.status ? { color: '#d29922' } : {}),
                }}>
                  {log.message}
                </span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: '900px', margin: '0 auto' },
  header: { display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' },
  headerTitle: { fontSize: '20px', color: '#e94560', margin: 0, whiteSpace: 'nowrap' },
  statusBadge: { padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' },
  'status-idle': { background: '#2d3436', color: '#636e72' },
  'status-running': { background: '#0f3460', color: '#74b9ff' },
  'status-done': { background: '#00b894', color: '#fff' },
  'status-error': { background: '#e94560', color: '#fff' },
  panel: {
    background: '#16213e', borderRadius: '12px', padding: '20px',
    border: '1px solid #0f3460', marginBottom: '16px',
  },
  panelTitle: {
    fontSize: '14px', color: '#74b9ff', margin: '0 0 16px 0',
    textTransform: 'uppercase', letterSpacing: '1px',
  },
  formRow: { display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' },
  formLabel: {
    fontSize: '12px', color: '#a0a0a0', textTransform: 'uppercase', letterSpacing: '0.5px',
  },
  input: {
    background: '#1a1a2e', border: '1px solid #0f3460', color: '#e0e0e0',
    padding: '10px 12px', borderRadius: '8px', fontSize: '14px', outline: 'none',
  },
  select: {
    background: '#1a1a2e', border: '1px solid #0f3460', color: '#e0e0e0',
    padding: '10px 12px', borderRadius: '8px', fontSize: '14px', outline: 'none',
  },
  fileRow: { display: 'flex', gap: '8px' },
  btnBrowse: {
    background: '#0f3460', color: '#74b9ff', border: '1px solid #0f3460',
    padding: '10px 16px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer', whiteSpace: 'nowrap',
  },
  btnAction: {
    background: '#0f3460', color: '#74b9ff', border: '1px solid #0f3460',
    padding: '10px 20px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer',
  },
  btnRun: {
    background: '#e94560', color: '#fff', border: 'none',
    padding: '12px 28px', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer',
  },
  btnStop: {
    background: '#e94560', color: '#fff', border: 'none',
    padding: '12px 28px', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer',
  },
  quickIps: { display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap', alignItems: 'center' },
  quickIpLabel: { color: '#636e72', fontSize: '12px' },
  quickIp: {
    background: '#1a1a2e', border: '1px solid #0f3460', color: '#74b9ff',
    padding: '4px 10px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
  },
  quickIpActive: { borderColor: '#e94560', color: '#e94560' },
  logPanel: {
    background: '#0d1117', borderRadius: '12px', border: '1px solid #0f3460', overflow: 'hidden',
  },
  logHeader: {
    background: '#161b22', padding: '12px 20px', borderBottom: '1px solid #0f3460',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  btnClear: {
    background: 'transparent', border: '1px solid #0f3460', color: '#a0a0a0',
    padding: '4px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
  },
  logContent: {
    padding: '12px', fontFamily: 'Consolas, Courier New, monospace', fontSize: '13px',
    lineHeight: '1.6', minHeight: '300px', maxHeight: '500px', overflowY: 'auto',
  },
  logEmpty: { color: '#636e72', padding: '8px' },
  logLine: { padding: '2px 8px', borderRadius: '4px', display: 'flex', gap: '8px', alignItems: 'flex-start' },
  logTime: { color: '#484f58', whiteSpace: 'nowrap', fontSize: '11px', paddingTop: '2px' },
  logMsg: { flex: 1, wordBreak: 'break-word', color: '#c9d1d9' },
};

export default LSMPackageManager;
