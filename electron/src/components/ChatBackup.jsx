import { useState, useEffect } from 'react';

const DEFAULT_BACKUP_DIR = 'd:\\Data\\AI\\VSCode\\logs\\chat-backups';

function formatDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function ChatBackup() {
  const [backupDir, setBackupDir] = useState(DEFAULT_BACKUP_DIR);
  const [backupStatus, setBackupStatus] = useState({ totalBackups: 0, lastBackup: null });
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState([]);
  const [backupFiles, setBackupFiles] = useState([]);
  const [schedulerStatus, setSchedulerStatus] = useState('unknown');
  const [dateMode, setDateMode] = useState('single'); // 'single' | 'range'
  const [selectedDate, setSelectedDate] = useState(() => formatDate(new Date()));
  const [dateFrom, setDateFrom] = useState(() => formatDate(new Date()));
  const [dateTo, setDateTo] = useState(() => formatDate(new Date()));

  useEffect(() => {
    loadBackupDir();
    setupScriptListeners();
    checkSchedulerStatus();
    return () => { window.electronAPI?.removeScriptListeners(); };
  }, []);

  useEffect(() => {
    if (backupDir) loadBackupFiles();
  }, [backupDir]);

  const setupScriptListeners = () => {
    window.electronAPI?.onScriptOutput((data) => {
      setOutput((prev) => [...prev, data.data]);
    });
    window.electronAPI?.onScriptExited((data) => {
      setIsRunning(false);
      loadBackupFiles();
      setOutput((prev) => [...prev, `\n=== 백업 완료 (코드: ${data.code}) ===`]);
    });
  };

  const loadBackupDir = async () => {
    try {
      const result = await window.electronAPI?.readConfig('chat-backup-config.json');
      if (result?.success && result.content?.backupDir) {
        setBackupDir(result.content.backupDir);
      }
    } catch (e) { console.error(e); }
  };

  const saveBackupDir = async (dir) => {
    await window.electronAPI?.saveConfig('chat-backup-config.json', { backupDir: dir });
    setBackupDir(dir);
  };

  const loadBackupFiles = async () => {
    try {
      const result = await window.electronAPI?.readDirectory(backupDir);
      if (result?.success) {
        const mdFiles = result.files.filter((f) => f.endsWith('.md')).sort().reverse().slice(0, 30);
        setBackupFiles(mdFiles);
        setBackupStatus({
          totalBackups: result.files.filter(f => f.endsWith('.md')).length,
          lastBackup: mdFiles.length > 0 ? mdFiles[0] : null,
        });
      } else {
        setBackupFiles([]);
        setBackupStatus({ totalBackups: 0, lastBackup: null });
      }
    } catch (e) { console.error(e); }
  };

  const checkSchedulerStatus = async () => {
    try {
      const result = await window.electronAPI?.runScript('check-scheduler.bat', []);
      if (result?.output?.includes('ClineDailyChatBackup')) {
        setSchedulerStatus('registered');
      } else {
        setSchedulerStatus('unregistered');
      }
    } catch { setSchedulerStatus('unknown'); }
  };

  const handleRunBackup = async () => {
    setIsRunning(true);
    setOutput([]);
    const dateDesc = dateMode === 'range' ? `${dateFrom} ~ ${dateTo}` : selectedDate;
    setOutput((prev) => [...prev, `=== 채팅 백업 시작 (날짜: ${dateDesc}) ===`]);

    const args = dateMode === 'range'
      ? [`--from=${dateFrom}`, `--to=${dateTo}`]
      : [`--date=${selectedDate}`];

    try {
      await window.electronAPI?.runScript('save-daily-chat.js', args, { BACKUP_DIR: backupDir });
    } catch (error) {
      setIsRunning(false);
      setOutput((prev) => [...prev, `오류: ${error.message}`]);
    }
  };

  const handleRegisterScheduler = async () => {
    try {
      await window.electronAPI?.runScript('register-scheduler.bat', []);
      setSchedulerStatus('registered');
      alert('스케줄러가 등록되었습니다. 매일 (월~금) 밤 11시에 백업이 실행됩니다.');
    } catch { alert('스케줄러 등록 중 오류가 발생했습니다.'); }
  };

  const handleUnregisterScheduler = async () => {
    if (confirm('스케줄러를 해제하시겠습니까?')) {
      try {
        await window.electronAPI?.runScript('unregister-scheduler.bat', []);
        setSchedulerStatus('unregistered');
        alert('스케줄러가 해제되었습니다.');
      } catch { alert('스케줄러 해제 중 오류가 발생했습니다.'); }
    }
  };

  const handleViewBackup = async (fileName) => {
    try {
      const result = await window.electronAPI?.readFile(`${backupDir}\\${fileName}`);
      if (result?.success) {
        alert(result.content.slice(0, 3000) + (result.content.length > 3000 ? '\n...(계속)' : ''));
      }
    } catch (e) { console.error(e); }
  };

  const handleOpenBackupFolder = async () => {
    try { await window.electronAPI?.openPath(backupDir); } catch (e) { console.error(e); }
  };

  const handleSelectBackupFolder = async () => {
    try {
      const result = await window.electronAPI?.openFolderDialog({ title: '백업 폴더 선택' });
      if (result?.filePaths?.[0]) {
        await saveBackupDir(result.filePaths[0]);
        loadBackupFiles();
      }
    } catch (e) { console.error(e); }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Cline 대화 백업</h2>
        <p style={styles.description}>Cline SR 대화 기록을 읽기 쉬운 Markdown으로 백업합니다</p>
      </div>

      {/* 백업 폴더 경로 표시 */}
      <div style={styles.folderCard}>
        <div style={styles.folderRow}>
          <span style={styles.folderLabel}>📁 백업 폴더:</span>
          <span style={styles.folderPath}>{backupDir}</span>
        </div>
        <div style={styles.folderActions}>
          <button onClick={handleOpenBackupFolder} style={styles.btnSecondary}>📂 폴더 열기</button>
          <button onClick={handleSelectBackupFolder} style={styles.btnSecondary}>🔄 폴더 변경</button>
        </div>
      </div>

      {/* 백업 상태 */}
      <div style={styles.statusCard}>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>백업 파일 수:</span>
          <span style={styles.statusValue}>{backupStatus.totalBackups}개</span>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>최신 백업:</span>
          <span style={styles.statusValue}>{backupStatus.lastBackup || '없음'}</span>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>스케줄러:</span>
          <span style={{ ...styles.statusValue, color: schedulerStatus === 'registered' ? '#4ade80' : '#888' }}>
            {schedulerStatus === 'registered' ? '✅ 활성화 (매일 밤 11시)' : '❌ 비활성화'}
          </span>
        </div>
      </div>

      {/* 백업 실행 컨트롤 */}
      <div style={styles.controls}>
        {/* 모드 토글 */}
        <div style={styles.modeToggle}>
          <button
            onClick={() => setDateMode('single')}
            style={dateMode === 'single' ? styles.modeBtnActive : styles.modeBtn}
          >단일 날짜</button>
          <button
            onClick={() => setDateMode('range')}
            style={dateMode === 'range' ? styles.modeBtnActive : styles.modeBtn}
          >날짜 범위</button>
        </div>

        {/* 날짜 선택 */}
        {dateMode === 'single' ? (
          <div style={styles.datePicker}>
            <label style={styles.dateLabel}>백업 날짜:</label>
            <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} style={styles.dateInput} />
          </div>
        ) : (
          <div style={styles.datePicker}>
            <label style={styles.dateLabel}>시작:</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={styles.dateInput} />
            <span style={styles.dateSep}>~</span>
            <label style={styles.dateLabel}>종료:</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={styles.dateInput} />
          </div>
        )}

        {!isRunning ? (
          <button onClick={handleRunBackup} style={styles.btnPrimary}>💾 지금 백업</button>
        ) : (
          <button disabled style={styles.btnDisabled}>⏳ 백업 중...</button>
        )}
      </div>

      {/* 스케줄러 설정 */}
      <div style={styles.section}>
        <label style={styles.label}>자동 백업 스케줄러</label>
        <div style={styles.schedulerControls}>
          {schedulerStatus === 'registered' ? (
            <>
              <span style={styles.schedulerInfo}>✅ 매일 (월~금) 밤 11시에 자동 백업됩니다</span>
              <button onClick={handleUnregisterScheduler} style={styles.btnDanger}>스케줄러 해제</button>
            </>
          ) : (
            <>
              <span style={styles.schedulerInfo}>❌ 자동 백업이 비활성화되어 있습니다</span>
              <button onClick={handleRegisterScheduler} style={styles.btnPrimary}>스케줄러 등록</button>
            </>
          )}
        </div>
      </div>

      {/* 출력 로그 */}
      <div style={styles.outputSection}>
        <label style={styles.label}>실시간 로그</label>
        <div style={styles.output}>
          {output.length === 0 ? (
            <div style={styles.emptyOutput}>백업을 시작하면 로그가 표시됩니다</div>
          ) : (
            output.map((line, i) => <div key={i} style={styles.outputLine}>{line}</div>)
          )}
        </div>
      </div>

      {/* 백업 파일 목록 */}
      <div style={styles.section}>
        <label style={styles.label}>백업 파일 목록 ({backupFiles.length}개)</label>
        <div style={styles.fileList}>
          {backupFiles.length > 0 ? (
            backupFiles.map((file) => (
              <button key={file} onClick={() => handleViewBackup(file)} style={styles.fileBtn}>📄 {file}</button>
            ))
          ) : (
            <div style={styles.emptyFile}>백업 파일이 없습니다</div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: '900px', margin: '0 auto' },
  header: { marginBottom: '24px' },
  title: { fontSize: '20px', marginBottom: '8px', color: '#fff' },
  description: { color: '#888', fontSize: '14px' },
  folderCard: { background: '#1a1a2e', borderRadius: '8px', padding: '16px', marginBottom: '16px', border: '1px solid #0f3460' },
  folderRow: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' },
  folderLabel: { color: '#74b9ff', fontSize: '14px', fontWeight: 'bold', flexShrink: 0 },
  folderPath: { color: '#e0e0e0', fontSize: '13px', wordBreak: 'break-all' },
  folderActions: { display: 'flex', gap: '8px' },
  statusCard: { background: '#2a2a4a', borderRadius: '8px', padding: '20px', marginBottom: '20px' },
  statusRow: { display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #3a3a5a' },
  statusLabel: { color: '#aaa' },
  statusValue: { color: '#fff', fontWeight: 'bold' },
  section: { marginBottom: '20px' },
  label: { display: 'block', marginBottom: '8px', color: '#aaa', fontSize: '14px' },
  schedulerControls: { display: 'flex', alignItems: 'center', gap: '16px', padding: '16px', background: '#1a1a2e', borderRadius: '6px' },
  schedulerInfo: { flex: 1, color: '#aaa' },
  controls: { display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'center', flexWrap: 'wrap' },
  modeToggle: { display: 'flex', gap: '4px', background: '#1a1a2e', borderRadius: '6px', padding: '4px' },
  modeBtn: { padding: '6px 14px', background: 'transparent', border: 'none', borderRadius: '4px', color: '#888', cursor: 'pointer', fontSize: '13px' },
  modeBtnActive: { padding: '6px 14px', background: '#0f3460', border: 'none', borderRadius: '4px', color: '#74b9ff', cursor: 'pointer', fontSize: '13px', fontWeight: 'bold' },
  datePicker: { display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' },
  dateLabel: { color: '#aaa', fontSize: '14px' },
  dateSep: { color: '#aaa', fontSize: '14px' },
  dateInput: { padding: '8px 12px', background: '#1a1a2e', border: '1px solid #0f3460', borderRadius: '6px', color: '#fff', fontSize: '14px', outline: 'none' },
  btnPrimary: { padding: '12px 24px', background: '#fbbf24', border: 'none', borderRadius: '6px', color: '#000', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' },
  btnDanger: { padding: '12px 24px', background: '#f87171', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' },
  btnSecondary: { padding: '8px 16px', background: '#0f3460', border: 'none', borderRadius: '6px', color: '#74b9ff', cursor: 'pointer', fontSize: '13px' },
  btnDisabled: { padding: '12px 24px', background: '#3a3a5a', border: 'none', borderRadius: '6px', color: '#888', cursor: 'not-allowed', fontSize: '14px' },
  outputSection: { marginBottom: '20px' },
  output: { background: '#0d0d1a', borderRadius: '8px', padding: '16px', minHeight: '150px', maxHeight: '250px', overflow: 'auto', fontFamily: 'Consolas, monospace', fontSize: '12px' },
  emptyOutput: { color: '#666', textAlign: 'center', padding: '40px' },
  outputLine: { padding: '2px 0', color: '#888', whiteSpace: 'pre-wrap' },
  fileList: { display: 'flex', flexWrap: 'wrap', gap: '8px' },
  fileBtn: { padding: '8px 16px', background: '#2a2a4a', border: '1px solid #3a3a5a', borderRadius: '4px', color: '#aaa', cursor: 'pointer', fontSize: '12px' },
  emptyFile: { color: '#666', padding: '20px' },
};

export default ChatBackup;
