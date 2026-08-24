import { useState, useEffect } from 'react';

function DRMUngroup() {
  const [docType, setDocType] = useState('word'); // word, excel, ppt, pdf
  const [mode, setMode] = useState('fast'); // fast, full
  const [selectedFile, setSelectedFile] = useState('');
  const [outputFolder, setOutputFolder] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState([]);
  const [processId, setProcessId] = useState(null);

  useEffect(() => {
    setupScriptListeners();
    return () => {
      window.electronAPI?.removeScriptListeners();
    };
  }, []);

  const setupScriptListeners = () => {
    window.electronAPI?.onScriptOutput((data) => {
      setOutput((prev) => [...prev, data.data]);
    });

    window.electronAPI?.onScriptExited((data) => {
      setIsRunning(false);
      setOutput((prev) => [
        ...prev,
        `\n=== 프로세스 종료 (코드: ${data.code}) ===`,
      ]);
    });
  };

  const docTypes = [
    { id: 'word', icon: '📄', name: 'Word 문서', exts: '.docx, .doc, .mht' },
    { id: 'excel', icon: '📊', name: 'Excel 스프레드시트', exts: '.xlsx, .xls, .csv' },
    { id: 'ppt', icon: '📽️', name: 'PowerPoint 프레젠테이션', exts: '.pptx, .ppt' },
    { id: 'pdf', icon: '📕', name: 'PDF 문서', exts: '.pdf' },
  ];

  const modes = [
    {
      id: 'fast',
      icon: '⚡',
      name: '빠른 텍스트 추출',
      features: [
        'Word/Excel/PowerPoint 라이브러리 사용',
        'PDF: pdf-parse 사용',
        '텍스트만 빠르게 추출',
        '30초 ~ 2분 소요',
      ],
    },
    {
      id: 'full',
      icon: '🔍',
      name: '완전 분석',
      features: [
        '텍스트 + 그림/표 캡처',
        'HTML 포맷으로 저장',
        '2 ~ 5분 소요',
        'Word/Excel/PPT/PDF 모두 지원',
      ],
    },
  ];

  const handleSelectFile = async () => {
    const typeMap = {
      word: { name: 'Word Documents', extensions: ['docx', 'doc', 'mht'] },
      excel: { name: 'Excel Files', extensions: ['xlsx', 'xls', 'csv'] },
      ppt: { name: 'PowerPoint Files', extensions: ['pptx', 'ppt'] },
      pdf: { name: 'PDF Files', extensions: ['pdf'] },
    };

    const result = await window.electronAPI?.openFileDialog({
      filters: [
        typeMap[docType],
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (result?.filePaths?.[0]) {
      setSelectedFile(result.filePaths[0]);
    }
  };

  const handleSelectOutputFolder = async () => {
    const result = await window.electronAPI?.openFolderDialog({
      defaultPath: await window.electronAPI?.getAppPath('output'),
    });

    if (result?.filePaths?.[0]) {
      setOutputFolder(result.filePaths[0]);
    }
  };

  const handleRun = async () => {
    if (!selectedFile) {
      alert('파일을 선택해주세요');
      return;
    }

    setIsRunning(true);
    setOutput([]);
    setOutput((prev) => [...prev, '=== DRM 문서 풀기 시작 ===']);
    setOutput((prev) => [...prev, `문서 종류: ${docTypes.find(d => d.id === docType)?.name}`]);
    setOutput((prev) => [...prev, `처리 방식: ${modes.find(m => m.id === mode)?.name}`]);
    setOutput((prev) => [...prev, `입력 파일: ${selectedFile}`]);
    setOutput((prev) => [...prev, '']);

    try {
      const result = await window.electronAPI?.runScript('drm-ungroup.js', [
        selectedFile,
        docType,
        mode,
        outputFolder || '',
      ]);

      if (result?.processId) {
        setProcessId(result.processId);
      }
    } catch (error) {
      setIsRunning(false);
      setOutput((prev) => [...prev, `오류: ${error.message}`]);
    }
  };

  const handleStop = async () => {
    if (processId) {
      await window.electronAPI?.stopScript(processId);
      setIsRunning(false);
      setOutput((prev) => [...prev, '\n=== 사용자에 의해 중지됨 ===']);
    }
  };

  const handleOpenOutput = async () => {
    const folder = outputFolder || (await window.electronAPI?.getAppPath('output')) + '\\drm-ungrouped';
    await window.electronAPI?.openPath(folder);
  };

  return (
    <div style={styles.container}>
      {/* 헤더 */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.headerIcon}>🔓</span>
          <div>
            <h2 style={styles.title}>DRM 문서 풀기</h2>
            <p style={styles.subtitle}>DRM 이 적용된 Office 문서를 빠르게 해독합니다</p>
          </div>
        </div>
      </div>

      {/* 사용 방법 안내 */}
      <div style={styles.guidePanel}>
        <div style={styles.guideTitle}>📖 사용 방법</div>
        <ul style={styles.guideList}>
          <li><b>1단계:</b> 문서 종류를 선택하세요 (Word, Excel, PowerPoint, PDF)</li>
          <li><b>2단계:</b> 처리 방식을 선택하세요 (빠른 텍스트 추출 / 완전 분석)</li>
          <li><b>3단계:</b> 파일을 선택하고 시작하기를 클릭하세요</li>
        </ul>
      </div>

      {/* 1️⃣ 문서 종류 선택 */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>1️⃣ 문서 종류 선택</h3>
        <div style={styles.cardGrid}>
          {docTypes.map((dt) => (
            <button
              key={dt.id}
              onClick={() => setDocType(dt.id)}
              style={docType === dt.id ? styles.cardActive : styles.card}
              disabled={isRunning}
            >
              <div style={styles.cardIcon}>{dt.icon}</div>
              <div style={styles.cardName}>{dt.name}</div>
              <div style={styles.cardExt}>{dt.exts}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 2️⃣ 처리 방식 선택 */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>2️⃣ 처리 방식 선택</h3>
        <div style={styles.modeGrid}>
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              style={mode === m.id ? styles.modeCardActive : styles.modeCard}
              disabled={isRunning}
            >
              <div style={styles.modeIcon}>{m.icon}</div>
              <div style={styles.modeName}>{m.name}</div>
              <ul style={styles.modeFeatures}>
                {m.features.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </button>
          ))}
        </div>
      </div>

      {/* 3️⃣ 파일 선택 */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>3️⃣ 파일 선택</h3>
        <div style={styles.fileRow}>
          <input
            type="text"
            value={selectedFile}
            readOnly
            placeholder="파일 경로를 입력하거나 찾아보기 버튼을 클릭하세요"
            style={styles.fileInput}
          />
          <button onClick={handleSelectFile} style={styles.browseBtn} disabled={isRunning}>
            📂 찾아보기
          </button>
        </div>

        {/* 출력 폴더 (선택사항) */}
        <div style={{ ...styles.fileRow, marginTop: '12px' }}>
          <input
            type="text"
            value={outputFolder}
            readOnly
            placeholder="출력 폴더 (선택사항, 미선택 시 기본 폴더)"
            style={styles.fileInput}
          />
          <button onClick={handleSelectOutputFolder} style={styles.browseBtn} disabled={isRunning}>
            📁 폴더 선택
          </button>
        </div>
      </div>

      {/* 시작 버튼 */}
      <div style={styles.actionArea}>
        {!isRunning ? (
          <button onClick={handleRun} style={styles.startBtn}>
            🚀 시작하기
          </button>
        ) : (
          <button onClick={handleStop} style={styles.stopBtn}>
            ⏹️ 중지
          </button>
        )}
      </div>

      {/* 출력 로그 */}
      <div style={styles.outputSection}>
        <div style={styles.outputHeader}>
          <span style={styles.outputLabel}>실시간 로그</span>
          {output.length > 0 && !isRunning && (
            <button onClick={handleOpenOutput} style={styles.openOutputBtn}>
              📂 출력 폴더 열기
            </button>
          )}
        </div>
        <div style={styles.output}>
          {output.length === 0 ? (
            <div style={styles.emptyOutput}>
              DRM 해제를 시작하면 로그가 표시됩니다
            </div>
          ) : (
            output.map((line, i) => (
              <div key={i} style={styles.outputLine}>{line}</div>
            ))
          )}
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
    background: 'linear-gradient(135deg, #4c1d95, #6d28d9)',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '20px',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  headerIcon: {
    fontSize: '40px',
  },
  title: {
    fontSize: '24px',
    color: '#fff',
    margin: '0 0 4px 0',
  },
  subtitle: {
    color: '#ddd6fe',
    fontSize: '14px',
    margin: 0,
  },
  guidePanel: {
    background: '#2a2440',
    borderLeft: '4px solid #f59e0b',
    borderRadius: '8px',
    padding: '16px 20px',
    marginBottom: '24px',
  },
  guideTitle: {
    fontWeight: 'bold',
    color: '#fbbf24',
    fontSize: '15px',
    marginBottom: '8px',
  },
  guideList: {
    color: '#ccc',
    fontSize: '13px',
    paddingLeft: '20px',
    margin: 0,
    lineHeight: '1.8',
  },
  section: {
    marginBottom: '24px',
  },
  sectionTitle: {
    color: '#a78bfa',
    fontSize: '16px',
    borderBottom: '2px solid #4c1d95',
    paddingBottom: '8px',
    marginBottom: '16px',
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '12px',
  },
  card: {
    background: '#1e1e30',
    border: '1px solid #333',
    borderRadius: '10px',
    padding: '16px',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'all 0.2s',
  },
  cardActive: {
    background: 'linear-gradient(135deg, #4c1d95, #6d28d9)',
    border: '2px solid #8b5cf6',
    borderRadius: '10px',
    padding: '16px',
    cursor: 'pointer',
    textAlign: 'center',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
  },
  cardIcon: {
    fontSize: '32px',
    marginBottom: '8px',
  },
  cardName: {
    color: '#fff',
    fontSize: '13px',
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  cardExt: {
    color: '#a78bfa',
    fontSize: '11px',
  },
  modeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '16px',
  },
  modeCard: {
    background: '#1e1e30',
    border: '1px solid #333',
    borderRadius: '10px',
    padding: '20px',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all 0.2s',
  },
  modeCardActive: {
    background: 'linear-gradient(135deg, #4c1d95, #6d28d9)',
    border: '2px solid #8b5cf6',
    borderRadius: '10px',
    padding: '20px',
    cursor: 'pointer',
    textAlign: 'left',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
  },
  modeIcon: {
    fontSize: '28px',
    marginBottom: '8px',
  },
  modeName: {
    color: '#fff',
    fontSize: '16px',
    fontWeight: 'bold',
    marginBottom: '8px',
  },
  modeFeatures: {
    color: '#ddd6fe',
    fontSize: '12px',
    paddingLeft: '16px',
    margin: 0,
    lineHeight: '1.8',
  },
  fileRow: {
    display: 'flex',
    gap: '12px',
  },
  fileInput: {
    flex: 1,
    padding: '12px 16px',
    background: '#1e1e30',
    border: '1px solid #333',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '14px',
  },
  browseBtn: {
    padding: '12px 24px',
    background: '#3b82f6',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  actionArea: {
    marginBottom: '24px',
  },
  startBtn: {
    width: '100%',
    padding: '16px',
    background: 'linear-gradient(135deg, #4c1d95, #6d28d9)',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '18px',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
  },
  stopBtn: {
    width: '100%',
    padding: '16px',
    background: '#ef4444',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '18px',
  },
  outputSection: {
    marginBottom: '20px',
  },
  outputHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  outputLabel: {
    color: '#aaa',
    fontSize: '14px',
  },
  openOutputBtn: {
    padding: '6px 16px',
    background: '#3a3a5a',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '12px',
  },
  output: {
    background: '#0d0d1a',
    borderRadius: '8px',
    padding: '16px',
    minHeight: '200px',
    maxHeight: '400px',
    overflow: 'auto',
    fontFamily: 'Consolas, monospace',
    fontSize: '12px',
  },
  emptyOutput: {
    color: '#666',
    textAlign: 'center',
    padding: '40px',
  },
  outputLine: {
    padding: '2px 0',
    color: '#ccc',
    whiteSpace: 'pre-wrap',
  },
};

export default DRMUngroup;
