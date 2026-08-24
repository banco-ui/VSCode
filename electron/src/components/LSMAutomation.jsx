import { useState, useEffect, useRef } from 'react';

function LSMAutomation() {
  const [lsmIp, setLsmIp] = useState('10.251.175.31');
  const [csvFile, setCsvFile] = useState('');
  const [mode, setMode] = useState('create-only');
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, running, done, error
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

  const modes = [
    { value: 'create-only', label: '증설만 (--create-only)' },
    { value: 'delete-only', label: '감설만 (--delete-only)' },
    { value: 'full', label: '감설 → 재증설 (전체)' },
    { value: 'dry-run', label: '시뮬레이션 (--dry-run)' },
  ];

  useEffect(() => {
    setupScriptListeners();
    return () => {
      window.electronAPI?.removeScriptListeners();
    };
  }, []);

  // 로그 자동 스크롤
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [output]);

  const setupScriptListeners = () => {
    window.electronAPI?.onScriptOutput((data) => {
      const line = data.data;
      let level = 'INFO';
      let statusColor = null;

      if (line.includes('[ERROR]') || line.includes('에러') || line.includes('실패')) {
        level = 'ERROR';
        statusColor = 'error';
      } else if (line.includes('[WARN]')) {
        level = 'WARN';
        statusColor = 'warning';
      } else if (line.includes('✓') || line.includes('성공') || line.includes('완료')) {
        statusColor = 'success';
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
      title: 'CSV 프로파일 파일 선택',
      filters: [
        { name: 'CSV Files', extensions: ['csv'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (result?.filePaths?.[0]) {
      setCsvFile(result.filePaths[0]);
    }
  };

  const handleRun = async () => {
    if (!csvFile) {
      alert('CSV 파일을 선택해주세요.');
      return;
    }

    // 설정 저장
    try {
      const result = await window.electronAPI?.readConfig('lsm-config.json');
      if (result?.success) {
        const config = result.content;
        if (config.servers?.[0]) {
          config.servers[0].mcmIp = lsmIp;
          config.servers[0].url = `https://${lsmIp}:7443`;
        }
        if (config.gui) {
          config.gui.baseUrl = `https://${lsmIp}:7443/aceman/`;
        }
        await window.electronAPI?.saveConfig('lsm-config.json', config);
      }
    } catch (e) {}

    setIsRunning(true);
    setStatus('running');
    setOutput([]);

    const modeLabel = modes.find(m => m.value === mode)?.label || mode;
    setOutput([{
      timestamp: new Date().toLocaleTimeString('ko-KR'),
      level: 'INFO',
      message: `▶ 증설 시작: ${csvFile} (LSM: ${lsmIp}, 모드: ${modeLabel})`,
      status: null,
    }]);

    try {
      const args = [csvFile, '--lsm-ip', lsmIp];
      if (mode === 'create-only') {
        args.push('--create-only');
      } else if (mode === 'delete-only') {
        args.push('--delete-only');
      } else if (mode === 'dry-run') {
        args.push('--dry-run');
      }

      const result = await window.electronAPI?.runScript('lsm-reprovision.js', args);

      if (result?.processId) {
        setProcessId(result.processId);
      }
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

  const handleClearLog = () => {
    setOutput([]);
  };

  const statusConfig = {
    idle: { class: 'status-idle', text: '대기 중' },
    running: { class: 'status-running', text: '실행 중...' },
    done: { class: 'status-done', text: '완료' },
    error: { class: 'status-error', text: '실패' },
  };

  return (
    <div style={styles.container}>
      {/* 헤더 */}
      <div style={styles.header}>
        <h1 style={styles.headerTitle}>📡 LSM NE 증설 자동화</h1>
        <span style={{ ...styles.statusBadge, ...styles[statusConfig[status].class] }}>
          {statusConfig[status].text}
        </span>
      </div>

      {/* 설정 패널 */}
      <div style={styles.configPanel}>
        <h2 style={styles.panelTitle}>⚙️ 증설 설정</h2>
        <div style={styles.configGrid}>
          {/* LSM IP */}
          <div style={styles.formGroup}>
            <label style={styles.formLabel}>LSM 서버 IP</label>
            <input
              type="text"
              value={lsmIp}
              onChange={(e) => setLsmIp(e.target.value)}
              placeholder="10.251.175.31"
              style={styles.input}
              disabled={isRunning}
            />
          </div>

          {/* CSV 파일 */}
          <div style={styles.formGroup}>
            <label style={styles.formLabel}>CSV 프로파일 파일</label>
            <div style={styles.fileRow}>
              <input
                type="text"
                value={csvFile}
                readOnly
                placeholder="파일을 선택하세요"
                style={{
                  ...styles.input,
                  color: csvFile ? '#3fb950' : '#666',
                }}
              />
              <button
                onClick={handleBrowse}
                style={styles.btnBrowse}
                disabled={isRunning}
              >
                📁 찾아보기
              </button>
            </div>
          </div>

          {/* 실행 모드 */}
          <div style={styles.formGroup}>
            <label style={styles.formLabel}>실행 모드</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              style={styles.select}
              disabled={isRunning}
            >
              {modes.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* 실행/중지 버튼 */}
          <div style={styles.formGroup}>
            <label style={styles.formLabel}>&nbsp;</label>
            {!isRunning ? (
              <button onClick={handleRun} style={styles.btnRun}>
                ▶ 증설 실행
              </button>
            ) : (
              <button onClick={handleStop} style={styles.btnStop}>
                ■ 중지
              </button>
            )}
          </div>
        </div>

        {/* 빠른 IP 선택 */}
        <div style={styles.quickIps}>
          <span style={styles.quickIpLabel}>빠른 선택:</span>
          {quickIps.map((qip) => (
            <button
              key={qip.ip}
              onClick={() => setLsmIp(qip.ip)}
              style={{
                ...styles.quickIp,
                ...(lsmIp === qip.ip ? styles.quickIpActive : {}),
              }}
              disabled={isRunning}
            >
              {qip.label}
            </button>
          ))}
        </div>
      </div>

      {/* 로그 패널 */}
      <div style={styles.logPanel}>
        <div style={styles.logHeader}>
          <h2 style={styles.panelTitle}>📋 실시간 로그</h2>
          <button onClick={handleClearLog} style={styles.btnClear}>
            로그 지우기
          </button>
        </div>
        <div style={styles.logContent}>
          {output.length === 0 ? (
            <div style={styles.logEmpty}>
              LSM NE 증설 자동화가 시작되었습니다. 설정을 확인하고 '증설 실행' 버튼을 누르세요.
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
  container: {
    maxWidth: '900px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '20px',
  },
  headerTitle: {
    fontSize: '20px',
    color: '#e94560',
    margin: 0,
    whiteSpace: 'nowrap',
  },
  statusBadge: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  'status-idle': {
    background: '#2d3436',
    color: '#636e72',
  },
  'status-running': {
    background: '#0f3460',
    color: '#74b9ff',
  },
  'status-done': {
    background: '#00b894',
    color: '#fff',
  },
  'status-error': {
    background: '#e94560',
    color: '#fff',
  },
  configPanel: {
    background: '#16213e',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid #0f3460',
    marginBottom: '16px',
  },
  panelTitle: {
    fontSize: '14px',
    color: '#74b9ff',
    margin: '0 0 16px 0',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
  configGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1.5fr 1fr auto',
    gap: '12px',
    alignItems: 'end',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  formLabel: {
    fontSize: '12px',
    color: '#a0a0a0',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  input: {
    background: '#1a1a2e',
    border: '1px solid #0f3460',
    color: '#e0e0e0',
    padding: '10px 12px',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
  },
  select: {
    background: '#1a1a2e',
    border: '1px solid #0f3460',
    color: '#e0e0e0',
    padding: '10px 12px',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
  },
  fileRow: {
    display: 'flex',
    gap: '8px',
  },
  btnBrowse: {
    background: '#0f3460',
    color: '#74b9ff',
    border: '1px solid #0f3460',
    padding: '10px 16px',
    borderRadius: '8px',
    fontSize: '14px',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  btnRun: {
    background: '#e94560',
    color: '#fff',
    border: 'none',
    padding: '12px 28px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  btnStop: {
    background: '#e94560',
    color: '#fff',
    border: 'none',
    padding: '12px 28px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  quickIps: {
    display: 'flex',
    gap: '8px',
    marginTop: '12px',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  quickIpLabel: {
    color: '#636e72',
    fontSize: '12px',
  },
  quickIp: {
    background: '#1a1a2e',
    border: '1px solid #0f3460',
    color: '#74b9ff',
    padding: '4px 10px',
    borderRadius: '6px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  quickIpActive: {
    borderColor: '#e94560',
    color: '#e94560',
  },
  logPanel: {
    background: '#0d1117',
    borderRadius: '12px',
    border: '1px solid #0f3460',
    overflow: 'hidden',
  },
  logHeader: {
    background: '#161b22',
    padding: '12px 20px',
    borderBottom: '1px solid #0f3460',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  btnClear: {
    background: 'transparent',
    border: '1px solid #0f3460',
    color: '#a0a0a0',
    padding: '4px 12px',
    borderRadius: '6px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  logContent: {
    padding: '12px',
    fontFamily: 'Consolas, Courier New, monospace',
    fontSize: '13px',
    lineHeight: '1.6',
    minHeight: '300px',
    maxHeight: '500px',
    overflowY: 'auto',
  },
  logEmpty: {
    color: '#636e72',
    padding: '8px',
  },
  logLine: {
    padding: '2px 8px',
    borderRadius: '4px',
    display: 'flex',
    gap: '8px',
    alignItems: 'flex-start',
  },
  logTime: {
    color: '#484f58',
    whiteSpace: 'nowrap',
    fontSize: '11px',
    paddingTop: '2px',
  },
  logMsg: {
    flex: 1,
    wordBreak: 'break-word',
    color: '#c9d1d9',
  },
};

export default LSMAutomation;
