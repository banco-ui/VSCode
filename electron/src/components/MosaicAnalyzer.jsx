import { useState, useEffect } from 'react';

function MosaicAnalyzer() {
  const [analysisType, setAnalysisType] = useState('api');
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState([]);
  const [processId, setProcessId] = useState(null);
  const [results, setResults] = useState([]);

  useEffect(() => {
    setupScriptListeners();
    loadPreviousResults();

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
        `\n=== 분석 완료 (코드: ${data.code}) ===`,
      ]);
      
      // 결과 파일 다시 읽기
      loadPreviousResults();
    });
  };

  const loadPreviousResults = async () => {
    try {
      const outputPath = await window.electronAPI?.getAppPath('output');
      const result = await window.electronAPI?.readDirectory(outputPath);
      
      if (result?.success) {
        const jsonFiles = result.files
          .filter((f) => f.endsWith('.json') && f.includes('mosaic'))
          .slice(-10);
        setResults(jsonFiles);
      }
    } catch (error) {
      console.error('결과 로딩 오류:', error);
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    setOutput([]);
    setOutput((prev) => [...prev, `=== Mosaic ${analysisType} 분석 시작 ===`]);

    const scriptMap = {
      api: 'mosaic-api.js',
      analyze: 'mosaic-analyze.js',
      'write-api': 'extract-write-api.js',
      'bbs-api': 'mosaic-cdp-bbs-api.js',
    };

    const scriptName = scriptMap[analysisType] || 'mosaic-api.js';

    try {
      const result = await window.electronAPI?.runScript(scriptName, []);
      
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

  const handleViewResult = async (fileName) => {
    try {
      const outputPath = await window.electronAPI?.getAppPath('output');
      const result = await window.electronAPI?.readFile(`${outputPath}\\${fileName}`);
      
      if (result?.success) {
        const content = JSON.parse(result.content);
        alert(JSON.stringify(content, null, 2).slice(0, 2000) + '...');
      }
    } catch (error) {
      console.error('결과 보기 오류:', error);
    }
  };

  const handleOpenOutputFolder = async () => {
    try {
      const outputPath = await window.electronAPI?.getAppPath('output');
      await window.electronAPI?.openExternal(`file://${outputPath}`);
    } catch (error) {
      console.error('폴더 열기 오류:', error);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Mosaic 분석 도구</h2>
        <p style={styles.description}>
          Mosaic GUI 자동화 및 API 분석 도구입니다
        </p>
      </div>

      {/* 분석 타입 선택 */}
      <div style={styles.section}>
        <label style={styles.label}>분석 타입</label>
        <div style={styles.typeGrid}>
          {[
            { id: 'api', label: '🔌 API 분석', desc: 'Mosaic API 호출 분석' },
            { id: 'analyze', label: '📊 종합 분석', desc: 'GUI 요소 및 메뉴 분석' },
            { id: 'write-api', label: '✏️ 작성 API', desc: '게시글 작성 API 추출' },
            { id: 'bbs-api', label: '📋 게시판 API', desc: '게시판 정보 수집' },
          ].map((type) => (
            <button
              key={type.id}
              onClick={() => setAnalysisType(type.id)}
              style={analysisType === type.id ? styles.typeCardActive : styles.typeCard}
            >
              <div style={styles.typeLabel}>{type.label}</div>
              <div style={styles.typeDesc}>{type.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 실행 컨트롤 */}
      <div style={styles.controls}>
        {!isRunning ? (
          <button onClick={handleRun} style={styles.btnPrimary}>
            ▶️ 분석 시작
          </button>
        ) : (
          <button onClick={handleStop} style={styles.btnDanger}>
            ⏹️ 중지
          </button>
        )}
        <button onClick={handleOpenOutputFolder} style={styles.btnSecondary}>
          📂 결과 폴더 열기
        </button>
      </div>

      {/* 출력 로그 */}
      <div style={styles.outputSection}>
        <label style={styles.label}>실시간 로그</label>
        <div style={styles.output}>
          {output.length === 0 ? (
            <div style={styles.emptyOutput}>
              분석을 시작하면 로그가 표시됩니다
            </div>
          ) : (
            output.map((line, i) => (
              <div key={i} style={styles.outputLine}>
                {line}
              </div>
            ))
          )}
        </div>
      </div>

      {/* 이전 결과 */}
      <div style={styles.section}>
        <label style={styles.label}>이전 분석 결과</label>
        <div style={styles.resultList}>
          {results.length > 0 ? (
            results.map((file) => (
              <button
                key={file}
                onClick={() => handleViewResult(file)}
                style={styles.resultBtn}
              >
                📄 {file}
              </button>
            ))
          ) : (
            <div style={styles.emptyResult}>이전 결과가 없습니다</div>
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
    marginBottom: '24px',
  },
  title: {
    fontSize: '20px',
    marginBottom: '8px',
    color: '#fff',
  },
  description: {
    color: '#888',
    fontSize: '14px',
  },
  section: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    color: '#aaa',
    fontSize: '14px',
  },
  typeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
  },
  typeCard: {
    padding: '16px',
    background: '#2a2a4a',
    border: '1px solid #3a3a5a',
    borderRadius: '8px',
    textAlign: 'left',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  typeCardActive: {
    padding: '16px',
    background: '#f472b6',
    border: '1px solid #f472b6',
    borderRadius: '8px',
    textAlign: 'left',
    cursor: 'pointer',
  },
  typeLabel: {
    color: '#fff',
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  typeDesc: {
    color: '#ccc',
    fontSize: '12px',
  },
  controls: {
    display: 'flex',
    gap: '12px',
    marginBottom: '20px',
  },
  btnPrimary: {
    padding: '12px 32px',
    background: '#f472b6',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '14px',
  },
  btnDanger: {
    padding: '12px 32px',
    background: '#f87171',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '14px',
  },
  btnSecondary: {
    padding: '12px 20px',
    background: '#3a3a5a',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '14px',
  },
  outputSection: {
    marginBottom: '20px',
  },
  output: {
    background: '#0d0d1a',
    borderRadius: '8px',
    padding: '16px',
    minHeight: '200px',
    maxHeight: '300px',
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
    color: '#888',
    whiteSpace: 'pre-wrap',
  },
  resultList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  resultBtn: {
    padding: '8px 16px',
    background: '#2a2a4a',
    border: '1px solid #3a3a5a',
    borderRadius: '4px',
    color: '#aaa',
    cursor: 'pointer',
    fontSize: '12px',
  },
  emptyResult: {
    color: '#666',
    padding: '20px',
  },
};

export default MosaicAnalyzer;
