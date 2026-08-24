import { useState, useEffect, useRef } from 'react';

function USMPackageVersionChanger() {
  const [usmIp, setUsmIp] = useState('');
  const [packages, setPackages] = useState([]);
  const [selectedPkg, setSelectedPkg] = useState('');
  const [currentVersion, setCurrentVersion] = useState('-');
  const [newVersion, setNewVersion] = useState('r-0140');
  const [isPrepared, setIsPrepared] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState('idle');
  const [output, setOutput] = useState([]);
  const [processId, setProcessId] = useState(null);
  const logEndRef = useRef(null);

  const quickIps = [
    { ip: '10.251.175.31', label: '10.251.175.31' },
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

      if (line.includes('[ERROR]') || line.includes('오류') || line.includes('실패') || line.includes('중단')) {
        level = 'ERROR';
        statusColor = 'error';
      } else if (line.includes('[WARN]') || line.includes('경고')) {
        level = 'WARN';
        statusColor = 'warning';
      } else if (line.includes('완료') || line.includes('성공')) {
        statusColor = 'success';
      }

      // 패키지 목록 파싱
      if (line.startsWith('PACKAGES_JSON:')) {
        try {
          const pkgs = JSON.parse(line.replace('PACKAGES_JSON:', ''));
          setPackages(pkgs);
          if (pkgs.length > 0) setSelectedPkg(pkgs[0]);
        } catch (e) {}
      }

      // 현재 버전 파싱
      if (line.startsWith('CURRENT_VERSION:')) {
        const ver = line.replace('CURRENT_VERSION:', '').trim();
        setCurrentVersion(ver);
      }

      // 준비 완료 파싱
      if (line.startsWith('PREPARED:')) {
        const prepared = line.replace('PREPARED:', '').trim() === 'true';
        setIsPrepared(prepared);
      }

      // 적용 완료 파싱
      if (line.startsWith('APPLY_DONE:')) {
        const done = line.replace('APPLY_DONE:', '').trim() === 'true';
        if (done) {
          setIsPrepared(false);
          setCurrentVersion('-');
        }
      }

      const timestamp = new Date().toLocaleTimeString('ko-KR');
      setOutput((prev) => [...prev, { timestamp, level, message: line, status: statusColor }]);
    });

    window.electronAPI?.onScriptExited((data) => {
      setIsRunning(false);
      if (data.code === 0) {
        setStatus('done');
        setOutput((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString('ko-KR'),
            level: 'INFO',
            message: `■ 작업 완료 (종료 코드: ${data.code})`,
            status: 'success',
          },
        ]);
      } else {
        setStatus('error');
        setOutput((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString('ko-KR'),
            level: 'ERROR',
            message: `■ 작업 실패 (종료 코드: ${data.code})`,
            status: 'error',
          },
        ]);
      }
    });
  };

  // 패키지 목록 조회
  const handleFetchPackages = async () => {
    if (!usmIp) {
      alert('장비 주소를 입력해야 합니다.');
      return;
    }
    setIsPrepared(false);
    setIsRunning(true);
    setStatus('running');
    setOutput([
      {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'INFO',
        message: `▶ 패키지 목록 조회: ${usmIp}`,
        status: null,
      },
    ]);
    try {
      const result = await window.electronAPI?.runScript('usm-pkg-version-changer.js', [
        '--ip', usmIp, '--action', 'packages',
      ]);
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setStatus('error');
      setOutput((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString('ko-KR'),
          level: 'ERROR',
          message: `오류: ${error.message}`,
          status: 'error',
        },
      ]);
    }
  };

  // [1단계] 현재 버전명 확인
  const handlePrepareCheck = async () => {
    if (!usmIp) {
      alert('장비 주소를 입력해야 합니다.');
      return;
    }
    if (!selectedPkg || selectedPkg.includes('패키지')) {
      alert('먼저 패키지를 선택해야 합니다.');
      return;
    }
    setIsPrepared(false);
    setIsRunning(true);
    setStatus('running');
    setOutput([
      {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'INFO',
        message: `▶ [1단계] 버전 확인 및 준비: ${selectedPkg} (${usmIp})`,
        status: null,
      },
    ]);
    try {
      const result = await window.electronAPI?.runScript('usm-pkg-version-changer.js', [
        '--ip', usmIp, '--action', 'prepare', '--pkg', selectedPkg,
      ]);
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setStatus('error');
      setOutput((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString('ko-KR'),
          level: 'ERROR',
          message: `오류: ${error.message}`,
          status: 'error',
        },
      ]);
    }
  };

  // [2단계] 패키지 버전 변경
  const handleApplyChange = async () => {
    if (!isPrepared) {
      alert("'현재 버전명 확인'을 먼저 실행하여 준비 작업을 완료해야 합니다.");
      return;
    }
    if (!usmIp || !selectedPkg || !currentVersion || !newVersion) {
      alert('모든 필드를 입력해야 합니다.');
      return;
    }
    const confirmed = window.confirm(
      `준비된 패키지의 버전을 변경하고 다시 압축합니다.\n` +
      `현재 버전: ${currentVersion} → 새 버전: ${newVersion}\n` +
      `계속하시겠습니까?`
    );
    if (!confirmed) return;

    setIsRunning(true);
    setStatus('running');
    setOutput([
      {
        timestamp: new Date().toLocaleTimeString('ko-KR'),
        level: 'INFO',
        message: `▶ [2단계] 버전 변경: ${currentVersion} → ${newVersion} (${usmIp})`,
        status: null,
      },
    ]);
    try {
      const result = await window.electronAPI?.runScript('usm-pkg-version-changer.js', [
        '--ip', usmIp, '--action', 'apply',
        '--pkg', selectedPkg, '--current', currentVersion, '--new', newVersion,
      ]);
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setStatus('error');
      setOutput((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString('ko-KR'),
          level: 'ERROR',
          message: `오류: ${error.message}`,
          status: 'error',
        },
      ]);
    }
  };

  const handleStop = async () => {
    if (processId) {
      await window.electronAPI?.stopScript(processId);
      setIsRunning(false);
      setStatus('idle');
      setOutput((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString('ko-KR'),
          level: 'WARN',
          message: '■ 작업 중지됨',
          status: 'warning',
        },
      ]);
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
        <h1 style={styles.headerTitle}>📦 USM PKG 버전명 변경</h1>
        <span style={{ ...styles.statusBadge, ...styles[statusConfig[status].class] }}>
          {statusConfig[status].text}
        </span>
        {isPrepared && (
          <span style={{ ...styles.statusBadge, ...styles.statusPrepared }}>
            ✓ 1단계 준비 완료
          </span>
        )}
      </div>

      {/* 1. 원격 장비 정보 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>1. 원격 장비 정보</h2>
        <div style={styles.formRow}>
          <label style={styles.formLabel}>USM MCMA 주소 (IP)</label>
          <input
            type="text"
            value={usmIp}
            onChange={(e) => setUsmIp(e.target.value)}
            placeholder="예: 10.251.175.31"
            style={styles.input}
            disabled={isRunning}
          />
        </div>
        <div style={styles.quickIps}>
          <span style={styles.quickIpLabel}>빠른 선택:</span>
          {quickIps.map((qip) => (
            <button
              key={qip.ip}
              onClick={() => setUsmIp(qip.ip)}
              style={{ ...styles.quickIp, ...(usmIp === qip.ip ? styles.quickIpActive : {}) }}
              disabled={isRunning}
            >
              {qip.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. 패키지 선택 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>2. 패키지 선택</h2>
        <button onClick={handleFetchPackages} style={styles.btnAction} disabled={isRunning}>
          📋 변경할 패키지 확인
        </button>
        <div style={styles.formRow}>
          <label style={styles.formLabel}>변경할 PKG</label>
          <select
            value={selectedPkg}
            onChange={(e) => setSelectedPkg(e.target.value)}
            style={styles.select}
            disabled={isRunning || packages.length === 0}
          >
            {packages.length === 0 ? (
              <option value="">패키지를 먼저 확인하세요</option>
            ) : (
              packages.map((p) => <option key={p} value={p}>{p}</option>)
            )}
          </select>
        </div>
      </div>

      {/* 3. 버전 변경 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>3. 버전 변경</h2>
        <div style={styles.versionRow}>
          <div style={styles.versionCol}>
            <label style={styles.formLabel}>현재 버전</label>
            <div style={{
              ...styles.versionDisplay,
              ...(currentVersion !== '-' ? { color: '#3fb950', borderColor: '#3fb950' } : {}),
            }}>
              {currentVersion}
            </div>
          </div>
          <div style={styles.versionCol}>
            <label style={styles.formLabel}>변경할 버전명</label>
            <input
              type="text"
              value={newVersion}
              onChange={(e) => setNewVersion(e.target.value)}
              placeholder="r-0140"
              style={styles.input}
              disabled={isRunning}
            />
          </div>
          <button
            onClick={handlePrepareCheck}
            style={styles.btnPrepare}
            disabled={isRunning || !selectedPkg || selectedPkg.includes('패키지')}
          >
            🔍 현재 버전명 확인
          </button>
        </div>
      </div>

      {/* 4. 실행 */}
      <div style={styles.panel}>
        <h2 style={styles.panelTitle}>4. 실행</h2>
        {!isRunning ? (
          <button
            onClick={handleApplyChange}
            style={{
              ...styles.btnRun,
              ...(!isPrepared ? { opacity: 0.5, cursor: 'not-allowed' } : {}),
            }}
            disabled={!isPrepared}
          >
            ▶ 패키지 버전 변경
          </button>
        ) : (
          <button onClick={handleStop} style={styles.btnStop}>
            ■ 중지
          </button>
        )}
        {!isPrepared && (
          <p style={styles.hintText}>
            💡 "현재 버전명 확인"을 먼저 실행하여 준비 작업을 완료해야 합니다.
          </p>
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
              USM PKG 버전명 변경 도구입니다. 장비 IP를 입력하고 패키지를 확인하세요.
              <br />
              작업 순서: 패키지 확인 → [1단계] 현재 버전 확인 → [2단계] 버전 변경
            </div>
          ) : (
            output.map((log, i) => (
              <div key={i} style={styles.logLine}>
                <span style={styles.logTime}>{log.timestamp}</span>
                <span
                  style={{
                    ...styles.logMsg,
                    ...(log.status === 'success' ? { color: '#3fb950' } : {}),
                    ...(log.status === 'warning' ? { color: '#d29922' } : {}),
                    ...(log.status === 'error' ? { color: '#f85149' } : {}),
                    ...(log.level === 'ERROR' && !log.status ? { color: '#f85149' } : {}),
                    ...(log.level === 'WARN' && !log.status ? { color: '#d29922' } : {}),
                  }}
                >
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
  header: { display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' },
  headerTitle: { fontSize: '20px', color: '#e94560', margin: 0, whiteSpace: 'nowrap' },
  statusBadge: { padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' },
  'status-idle': { background: '#2d3436', color: '#636e72' },
  'status-running': { background: '#0f3460', color: '#74b9ff' },
  'status-done': { background: '#00b894', color: '#fff' },
  'status-error': { background: '#e94560', color: '#fff' },
  statusPrepared: { background: '#1a6b3a', color: '#3fb950' },
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
  versionRow: { display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' },
  versionCol: { display: 'flex', flexDirection: 'column', gap: '6px', flex: '1', minWidth: '150px' },
  versionDisplay: {
    background: '#1a1a2e', border: '1px solid #0f3460', color: '#636e72',
    padding: '10px 12px', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold',
    minHeight: '40px', display: 'flex', alignItems: 'center',
  },
  btnAction: {
    background: '#0f3460', color: '#74b9ff', border: '1px solid #0f3460',
    padding: '10px 20px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer',
    marginBottom: '12px',
  },
  btnPrepare: {
    background: '#0f3460', color: '#74b9ff', border: '1px solid #0f3460',
    padding: '10px 20px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer',
    whiteSpace: 'nowrap', height: '42px',
  },
  btnRun: {
    background: '#e94560', color: '#fff', border: 'none',
    padding: '12px 28px', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer',
  },
  btnStop: {
    background: '#e94560', color: '#fff', border: 'none',
    padding: '12px 28px', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer',
  },
  hintText: { color: '#636e72', fontSize: '12px', marginTop: '8px' },
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

export default USMPackageVersionChanger;
