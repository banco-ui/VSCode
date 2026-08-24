import { useState, useEffect } from 'react';

const DEFAULT_EXCLUDE_KEYWORDS = ['RE', '공지', '반납', '준비완료', '연장확인', '할당불가'];
const DEFAULT_BT_MEMBERS = ['김대목', '노민식', '강윤식', '강남욱', '김상웅', '지동환', '배정호', '송명준', '차정호', '김주영'];

function formatDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function MosaicBTSampleRequest() {
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState([]);
  const [processId, setProcessId] = useState(null);
  const [posts, setPosts] = useState([]);
  const [showExcluded, setShowExcluded] = useState(false);
  const [showMosaic, setShowMosaic] = useState(false);

  // 조회 기간
  const today = new Date();
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  const [startDate, setStartDate] = useState(formatDate(weekAgo));
  const [endDate, setEndDate] = useState(formatDate(today));

  // 제외 키워드
  const [excludeKeywords, setExcludeKeywords] = useState(DEFAULT_EXCLUDE_KEYWORDS);
  const [newKeyword, setNewKeyword] = useState('');

  // BT 담당자
  const [btMembers, setBtMembers] = useState(DEFAULT_BT_MEMBERS);
  const [newMember, setNewMember] = useState('');

  useEffect(() => {
    setupScriptListeners();
    return () => { window.electronAPI?.removeScriptListeners(); };
  }, []);

  const setupScriptListeners = () => {
    window.electronAPI?.onScriptOutput((data) => {
      setOutput((prev) => [...prev, data.data]);
    });
    window.electronAPI?.onScriptExited((data) => {
      setIsRunning(false);
      setProcessId(null);
      setOutput((prev) => [...prev, `\n=== 완료 (코드: ${data.code}) ===`]);
      loadPosts();
    });
  };

  const loadPosts = async () => {
    try {
      const outputPath = await window.electronAPI?.getAppPath('output');
      const result = await window.electronAPI?.readDirectory(outputPath);
      if (result?.success) {
        const jsonFiles = result.files
          .filter(f => f.startsWith('mosaic-posts-') && f.endsWith('.json'))
          .sort().reverse();
        if (jsonFiles.length > 0) {
          const fileResult = await window.electronAPI?.readFile(`${outputPath}\\${jsonFiles[0]}`);
          if (fileResult?.success) {
            try { setPosts(JSON.parse(fileResult.content)); } catch {}
          }
        }
      }
    } catch (e) { console.error(e); }
  };

  // Chrome CDP 모드 실행
  const handleStartChrome = async () => {
    setOutput((prev) => [...prev, '=== Chrome CDP 모드 실행 중... ===']);
    try {
      await window.electronAPI?.openExternal('chrome.exe --remote-debugging-port=9222 --user-data-dir="%TEMP%\\mosaic-cdp-profile" --no-first-run --no-default-browser-check https://mosaic.sec.samsung.net');
      setOutput((prev) => [...prev, 'Chrome CDP 모드 실행 요청됨 (포트 9222)']);
    } catch (e) {
      setOutput((prev) => [...prev, `오류: ${e.message}`]);
    }
  };

  // Mosaic 포털 열기
  const handleOpenMosaic = async () => {
    await window.electronAPI?.openExternal('https://mosaic.sec.samsung.net/collaboration/workspace/6654005/list/1767722146');
  };

  // 게시물 추출 (시작 버튼)
  const handleExtract = async () => {
    setIsRunning(true);
    setOutput([]);
    setOutput((prev) => [...prev, `[${new Date().toLocaleString('ko-KR')}] 게시물 추출 시작: ${startDate} ~ ${endDate}`]);
    setOutput((prev) => [...prev, `제외 키워드: ${excludeKeywords.join(', ')}`]);
    setOutput((prev) => [...prev, `BT 담당자: ${btMembers.join(', ')}`]);
    setOutput((prev) => [...prev, '']);
    setOutput((prev) => [...prev, '⚠️ Chrome이 CDP 모드(포트 9222)로 실행되어 있고, Mosaic에 로그인되어 있어야 합니다.']);
    setOutput((prev) => [...prev, '']);

    try {
      const outputPath = await window.electronAPI?.getAppPath('output');
      const result = await window.electronAPI?.runScript(
        'mosaic-cdp-extract-all.js',
        [`--start=${startDate}`, `--end=${endDate}`],
        { OUTPUT_DIR: outputPath }
      );
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setOutput((prev) => [...prev, `오류: ${error.message}`]);
    }
  };

  // Excel 변환
  const handleTransformExcel = async () => {
    setIsRunning(true);
    setOutput([]);
    setOutput((prev) => [...prev, `[${new Date().toLocaleString('ko-KR')}] Excel 변환 시작`]);
    try {
      const outputPath = await window.electronAPI?.getAppPath('output');
      const result = await window.electronAPI?.runScript(
        'mosaic-transform-excel.js',
        [],
        { OUTPUT_DIR: outputPath }
      );
      if (result?.processId) setProcessId(result.processId);
    } catch (error) {
      setIsRunning(false);
      setOutput((prev) => [...prev, `오류: ${error.message}`]);
    }
  };

  // 중지
  const handleStop = async () => {
    if (processId) {
      await window.electronAPI?.stopScript(processId);
      setIsRunning(false);
      setOutput((prev) => [...prev, '\n=== 사용자에 의해 중지됨 ===']);
    }
  };

  // 결과 폴더 열기
  const handleOpenOutput = async () => {
    const outputPath = await window.electronAPI?.getAppPath('output');
    await window.electronAPI?.openPath(outputPath);
  };

  // 키워드 추가/삭제
  const addKeyword = () => {
    if (newKeyword && !excludeKeywords.includes(newKeyword)) {
      setExcludeKeywords([...excludeKeywords, newKeyword]);
      setNewKeyword('');
    }
  };
  const removeKeyword = (kw) => setExcludeKeywords(excludeKeywords.filter(k => k !== kw));

  // 담당자 추가/삭제
  const addMember = () => {
    if (newMember && !btMembers.includes(newMember)) {
      setBtMembers([...btMembers, newMember]);
      setNewMember('');
    }
  };
  const removeMember = (m) => setBtMembers(btMembers.filter(x => x !== m));

  // 게시물 분류
  const isExcluded = (post) => {
    if (btMembers.includes(post.writer)) return true;
    for (const prefix of ['준비완료', 'RE]', '연장확인', '반납확인', '할당불가', '반납]']) {
      if (post.title && (post.title.startsWith('[' + prefix) || post.title.startsWith(prefix))) return true;
    }
    for (const kw of excludeKeywords) {
      if (post.title && post.title.includes(kw)) return true;
    }
    return false;
  };

  const mainPosts = posts.filter(p => !isExcluded(p));
  const excludedPosts = posts.filter(p => isExcluded(p));
  const displayPosts = showExcluded ? excludedPosts : mainPosts;

  return (
    <div style={styles.container}>
      {/* 다크블루 헤더 */}
      <div style={styles.header}>
        <h2 style={styles.headerTitle}>Mosaic BT 시료요청 관리</h2>
        <p style={styles.headerSubtitle}>개요 - 시료 요청 정보 수집</p>
      </div>

      {/* 메인 컨텐츠 (흰색 배경) */}
      <div style={styles.mainContent}>
        {/* 상단: 조회 기간 + 키워드 + 담당자 */}
        <div style={styles.topRow}>
          {/* 조회 기간 */}
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>조회 기간</label>
            <div style={styles.dateRow}>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} style={styles.dateInput} />
              <span style={styles.dateSep}>~</span>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} style={styles.dateInput} />
            </div>
          </div>

          {/* 제외 키워드 */}
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>제목 제외 키워드</label>
            <div style={styles.inputWithBtn}>
              <input
                type="text" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                placeholder="키워드 입력" style={styles.textInput}
              />
              <button onClick={addKeyword} style={styles.btnAdd}>추가</button>
            </div>
            <div style={styles.listBox}>
              {excludeKeywords.map(kw => (
                <div key={kw} style={styles.listItem}>
                  <span>{kw}</span>
                  <button onClick={() => removeKeyword(kw)} style={styles.btnDelete}>✕</button>
                </div>
              ))}
            </div>
          </div>

          {/* BT 담당자 */}
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>BT Center 담당자</label>
            <div style={styles.inputWithBtn}>
              <input
                type="text" value={newMember} onChange={(e) => setNewMember(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addMember()}
                placeholder="담당자 입력" style={styles.textInput}
              />
              <button onClick={addMember} style={styles.btnAdd}>추가</button>
            </div>
            <div style={styles.listBox}>
              {btMembers.map(m => (
                <div key={m} style={styles.listItem}>
                  <span>{m}</span>
                  <button onClick={() => removeMember(m)} style={styles.btnDelete}>✕</button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 버튼 행 */}
        <div style={styles.buttonRow}>
          {!isRunning ? (
            <button onClick={handleExtract} style={styles.btnStart}>시작</button>
          ) : (
            <button onClick={handleStop} style={styles.btnStop}>중지</button>
          )}
          <button onClick={() => setShowExcluded(!showExcluded)} style={styles.btnGray}>
            {showExcluded ? '전체 보기' : '제외된 항목 보기'}
          </button>
          <button onClick={handleTransformExcel} style={styles.btnExcel}>Excel 저장</button>
          <label style={styles.checkboxLabel}>
            <input type="checkbox" checked={showMosaic} onChange={(e) => setShowMosaic(e.target.checked)} />
            모자익 화면 보기
          </label>
          <button onClick={handleStartChrome} style={styles.btnLink}>🌐 Chrome CDP</button>
          <button onClick={handleOpenMosaic} style={styles.btnLink}>🔗 Mosaic</button>
          <button onClick={handleOpenOutput} style={styles.btnLink}>📂 폴더</button>
        </div>

        {/* 데이터 테이블 */}
        <div style={styles.tableContainer}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>번호</th>
                <th style={styles.th}>제목</th>
                <th style={styles.th}>등록자</th>
                <th style={styles.th}>진행상황</th>
                <th style={styles.th}>등록일</th>
              </tr>
            </thead>
            <tbody>
              {displayPosts.length > 0 ? (
                displayPosts.map((post, i) => (
                  <tr key={i} style={styles.tr}>
                    <td style={styles.td}>{i + 1}</td>
                    <td style={styles.tdTitle}>
                      <a href={post.url} onClick={(e) => { e.preventDefault(); window.electronAPI?.openExternal(post.url); }} style={styles.link}>
                        {post.title}
                      </a>
                    </td>
                    <td style={styles.td}>{post.writer}</td>
                    <td style={styles.td}>{isExcluded(post) ? '제외' : '요청'}</td>
                    <td style={styles.td}>{post.regDtm}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={styles.emptyTd}>
                    {posts.length === 0 ? '시작 버튼을 눌러 데이터를 가져오세요' : '표시할 데이터가 없습니다'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* 요약 정보 */}
        {posts.length > 0 && (
          <div style={styles.summaryRow}>
            <span style={styles.summaryItem}>전체: {posts.length}건</span>
            <span style={styles.summaryItem}>원본 요청: {mainPosts.length}건</span>
            <span style={styles.summaryItem}>제외: {excludedPosts.length}건</span>
          </div>
        )}
      </div>

      {/* 콘솔 (검은색 배경, 녹색 텍스트) */}
      <div style={styles.console}>
        {output.length === 0 ? (
          <div style={styles.consoleReady}>Mosaic BT 시료요청 관리 GUI 준비됨</div>
        ) : (
          output.map((line, i) => <div key={i} style={styles.consoleLine}>{line}</div>)
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', background: '#1a1a2e' },
  // 다크블루 헤더
  header: { background: '#2c3e50', padding: '16px 20px', borderBottom: '2px solid #3498db' },
  headerTitle: { color: '#fff', fontSize: '18px', margin: '0 0 4px 0' },
  headerSubtitle: { color: '#bdc3c7', fontSize: '13px', margin: 0 },
  // 메인 컨텐츠 (흰색 배경)
  mainContent: { background: '#fff', padding: '16px', flex: 1, overflow: 'auto', borderRadius: '8px 8px 0 0', margin: '0 12px' },
  // 상단 행
  topRow: { display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' },
  filterGroup: { flex: 1, minWidth: '200px' },
  filterLabel: { display: 'block', fontSize: '13px', fontWeight: 'bold', color: '#2c3e50', marginBottom: '6px' },
  dateRow: { display: 'flex', alignItems: 'center', gap: '6px' },
  dateInput: { padding: '6px 10px', border: '1px solid #bdc3c7', borderRadius: '4px', fontSize: '13px', color: '#2c3e50' },
  dateSep: { color: '#7f8c8d', fontSize: '13px' },
  inputWithBtn: { display: 'flex', gap: '6px', marginBottom: '6px' },
  textInput: { flex: 1, padding: '6px 10px', border: '1px solid #bdc3c7', borderRadius: '4px', fontSize: '13px', color: '#2c3e50' },
  btnAdd: { padding: '6px 14px', background: '#3498db', border: 'none', borderRadius: '4px', color: '#fff', cursor: 'pointer', fontSize: '12px' },
  listBox: { border: '1px solid #bdc3c7', borderRadius: '4px', maxHeight: '100px', overflowY: 'auto', background: '#f8f9fa' },
  listItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 10px', borderBottom: '1px solid #ecf0f1', fontSize: '12px', color: '#2c3e50' },
  btnDelete: { background: 'none', border: 'none', color: '#e74c3c', cursor: 'pointer', fontSize: '12px', padding: '0' },
  // 버튼 행
  buttonRow: { display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap' },
  btnStart: { padding: '8px 24px', background: '#2ecc71', border: 'none', borderRadius: '4px', color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' },
  btnStop: { padding: '8px 24px', background: '#e74c3c', border: 'none', borderRadius: '4px', color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' },
  btnGray: { padding: '8px 16px', background: '#95a5a6', border: 'none', borderRadius: '4px', color: '#fff', cursor: 'pointer', fontSize: '13px' },
  btnExcel: { padding: '8px 16px', background: '#e67e22', border: 'none', borderRadius: '4px', color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', color: '#2c3e50', cursor: 'pointer' },
  btnLink: { padding: '6px 12px', background: '#ecf0f1', border: '1px solid #bdc3c7', borderRadius: '4px', color: '#2c3e50', cursor: 'pointer', fontSize: '12px' },
  // 테이블
  tableContainer: { border: '1px solid #bdc3c7', borderRadius: '4px', overflow: 'auto', maxHeight: '300px' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { background: '#3498db', color: '#fff', padding: '8px 12px', fontSize: '12px', fontWeight: 'bold', textAlign: 'left', position: 'sticky', top: 0, zIndex: 1 },
  tr: { borderBottom: '1px solid #ecf0f1' },
  td: { padding: '8px 12px', fontSize: '12px', color: '#2c3e50' },
  tdTitle: { padding: '8px 12px', fontSize: '12px', color: '#2c3e50', maxWidth: '400px' },
  link: { color: '#3498db', textDecoration: 'none', cursor: 'pointer' },
  emptyTd: { padding: '40px', textAlign: 'center', color: '#95a5a6', fontSize: '13px' },
  // 요약
  summaryRow: { display: 'flex', gap: '16px', marginTop: '8px', padding: '8px 0' },
  summaryItem: { fontSize: '12px', color: '#7f8c8d' },
  // 콘솔
  console: { background: '#000', padding: '12px', height: '120px', overflowY: 'auto', margin: '0 12px 12px 12px', borderRadius: '0 0 8px 8px', fontFamily: 'Consolas, monospace', fontSize: '11px' },
  consoleReady: { color: '#00ff00' },
  consoleLine: { color: '#00ff00', whiteSpace: 'pre-wrap' },
};

export default MosaicBTSampleRequest;
