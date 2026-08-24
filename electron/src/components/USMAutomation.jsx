import { useState, useEffect, useRef, useCallback } from 'react';

function USMAutomation() {
  // 탭 상태
  const [activeTab, setActiveTab] = useState('ne'); // 'ne', 'cell', 'list'

  // 서버 관련 상태
  const [servers, setServers] = useState([]);
  const [selectedServerId, setSelectedServerId] = useState('');
  const [newServerName, setNewServerName] = useState('');
  const [newServerIp, setNewServerIp] = useState('');
  const [newServerPort, setNewServerPort] = useState('7443');

  // NE 증설 상태
  const [neCsvContent, setNeCsvContent] = useState('');
  const [neFileName, setNeFileName] = useState('');
  const [neLoading, setNeLoading] = useState(false);
  const [neResult, setNeResult] = useState(null);

  // Cell 증설 상태
  const [cellNeName, setCellNeName] = useState('');
  const [cellCsvContent, setCellCsvContent] = useState('');
  const [cellFileName, setCellFileName] = useState('');
  const [cellLoading, setCellLoading] = useState(false);
  const [cellResult, setCellResult] = useState(null);

  // NE 목록 조회 상태
  const [listLoading, setListLoading] = useState(false);
  const [listResult, setListResult] = useState(null);
  const [neList, setNeList] = useState([]);

  // 로그
  const [output, setOutput] = useState([]);

  // 파일 input refs
  const neFileInputRef = useRef(null);
  const cellFileInputRef = useRef(null);

  // 설정 로드
  const loadConfig = useCallback(async () => {
    try {
      const result = await window.electronAPI?.readConfig('usm-config.json');
      if (result?.success && result.content?.servers) {
        setServers(result.content.servers);
        if (result.content.servers.length > 0) {
          setSelectedServerId(result.content.servers[0].id);
        }
      }
    } catch (error) {
      console.error('설정 로딩 오류:', error);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // 서버 추가
  const handleAddServer = async () => {
    if (!newServerName.trim() || !newServerIp.trim()) {
      alert('서버 이름과 IP를 입력하세요');
      return;
    }

    const newServer = {
      id: `usm-${Date.now()}`,
      name: newServerName.trim(),
      url: `https://${newServerIp.trim()}:${newServerPort || '7443'}`,
      mcmIp: newServerIp.trim(),
      apiPort: parseInt(newServerPort) || 7443,
    };

    try {
      const result = await window.electronAPI?.readConfig('usm-config.json');
      const config = result?.success ? result.content : { servers: [], api: { auth: { username: 'ossuser', password: 'osspasswd' } } };
      config.servers.push(newServer);
      await window.electronAPI?.saveConfig('usm-config.json', config);
      setServers(config.servers);
      setSelectedServerId(newServer.id);
      setNewServerName('');
      setNewServerIp('');
      setOutput(prev => [...prev, `[INFO] 서버 추가됨: ${newServer.name} (${newServer.mcmIp}:${newServer.apiPort})`]);
    } catch (error) {
      alert('서버 추가 실패: ' + error.message);
    }
  };

  // 선택된 서버 정보 가져오기
  const getSelectedServer = () => {
    const server = servers.find(s => s.id === selectedServerId);
    if (!server) {
      alert('USM 서버를 선택하세요');
      return null;
    }
    return server;
  };

  // USM API 호출 (Electron 메인 프로세스를 통해 - CORS/인증서 문제 회피)
  const callUSMApi = async (endpoint, method = 'GET', body = null, timeout = 30000) => {
    const server = getSelectedServer();
    if (!server) return null;

    const url = `${server.url}${endpoint}`;

    const result = await window.electronAPI?.usmApiCall({
      url,
      method,
      body: body || undefined,
      timeout,
    });

    if (!result?.success) {
      throw new Error(result?.error || 'API 호출 실패');
    }

    return { statusCode: result.statusCode, body: result.body };
  };


  // CSV 섹션 파서
  const parseCSVLine = (line) => {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') { current += '"'; i++; }
        else { inQuotes = !inQuotes; }
      } else if (char === ',' && !inQuotes) {
        result.push(current); current = '';
      } else { current += char; }
    }
    result.push(current);
    return result.map(s => s.trim());
  };

  const parseSectionCSV = (content) => {
    const lines = content.split(/\r?\n/);
    const sections = {};
    let currentSection = null;
    let currentHeaders = null;
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) { currentSection = null; currentHeaders = null; continue; }
      const unquoted = trimmed.replace(/^"(.*)"$/, '$1');
      if (unquoted.startsWith('@')) {
        currentSection = unquoted;
        currentHeaders = null;
        if (!sections[currentSection]) sections[currentSection] = [];
        continue;
      }
      if (currentSection) {
        const values = parseCSVLine(trimmed);
        if (!currentHeaders) {
          currentHeaders = values;
        } else {
          const row = {};
          currentHeaders.forEach((h, idx) => { row[h] = values[idx] || ''; });
          sections[currentSection].push(row);
        }
      }
    }
    return sections;
  };

  const buildJson = (sections) => {
    const result = {};
    for (const [sectionName, rows] of Object.entries(sections)) {
      if (rows.length === 0) continue;
      const validRows = rows.filter(r => !(r.State && r.State.toUpperCase() === 'NONE'));
      if (validRows.length === 0) continue;
      if (validRows.length === 1) {
        const row = validRows[0];
        result[sectionName] = {};
        for (const [key, value] of Object.entries(row)) result[sectionName][key] = [value];
      } else {
        result[sectionName] = {};
        const headers = Object.keys(validRows[0]);
        for (const header of headers) result[sectionName][header] = validRows.map(r => r[header] || '');
      }
    }
    return result;
  };

  // 파일 선택 처리
  const handleFileSelect = (e, setFileName, setCsvContent) => {
    const file = e.target.files[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => setCsvContent(ev.target.result);
    reader.readAsText(file);
  };

  // 드래그 앤 드롭 처리
  const handleDrop = (e, setFileName, setCsvContent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => setCsvContent(ev.target.result);
    reader.readAsText(file);
  };

  // NE 증설 실행
  const handleProvisionNE = async () => {
    if (!getSelectedServer()) return;
    if (!neCsvContent) { alert('CSV 파일을 첨부하세요'); return; }
    if (!window.confirm('NE 증설을 실행하시겠습니까?')) return;

    setNeLoading(true);
    setNeResult(null);
    setOutput(prev => [...prev, `=== NE 증설 시작 ===`]);

    try {
      const sections = parseSectionCSV(neCsvContent);
      const neJson = buildJson(sections);
      const neName = sections['@NVGNB']?.[0]?.['NE Name'] || sections['@ENB']?.[0]?.['NE Name'] || 'Unknown';

      setOutput(prev => [...prev, `[INFO] NE: ${neName}, 서버: ${getSelectedServer().name}`]);

      const response = await callUSMApi('/oss/ne', 'POST', neJson, 120000);

      if (response.statusCode === 200) {
        const result = typeof response.body === 'object' ? response.body.RESULT || 'OK' : 'OK';
        setNeResult({
          success: true,
          neName,
          result,
          body: response.body,
        });
        setOutput(prev => [...prev, `[OK] NE 증설 성공: ${neName} → ${result}`]);
      } else {
        setNeResult({
          success: false,
          neName,
          statusCode: response.statusCode,
          body: response.body,
        });
        setOutput(prev => [...prev, `[FAIL] NE 증설 실패 (HTTP ${response.statusCode})`]);
      }
    } catch (error) {
      setNeResult({ success: false, error: error.message });
      setOutput(prev => [...prev, `[ERROR] ${error.message}`]);
    }
    setNeLoading(false);
  };

  // Cell 증설 실행
  const handleProvisionCell = async () => {
    if (!getSelectedServer()) return;
    if (!cellNeName.trim()) { alert('NE Name을 입력하세요'); return; }
    if (!cellCsvContent) { alert('CSV 파일을 첨부하세요'); return; }
    if (!window.confirm('Cell 증설을 실행하시겠습니까?\n(최대 30분까지 소요될 수 있습니다)')) return;

    setCellLoading(true);
    setCellResult(null);
    setOutput(prev => [...prev, `=== Cell 증설 시작 ===`]);

    try {
      const sections = parseSectionCSV(cellCsvContent);
      const cellJson = buildJson(sections);
      const cellCount = sections['@CELL_INFORMATION']?.length || 0;

      setOutput(prev => [...prev, `[INFO] NE: ${cellNeName}, Cell: ${cellCount}개, 서버: ${getSelectedServer().name}`]);

      const endpoint = `/oss/ne/${encodeURIComponent(cellNeName.trim())}/cells`;
      const response = await callUSMApi(endpoint, 'POST', cellJson, 1800000);

      if (response.statusCode === 200) {
        const result = typeof response.body === 'object' ? response.body.RESULT || 'OK' : 'OK';
        setCellResult({
          success: true,
          neName: cellNeName,
          cellCount,
          result,
          body: response.body,
        });
        setOutput(prev => [...prev, `[OK] Cell 증설 성공: ${cellNeName} → ${result}`]);
      } else {
        setCellResult({
          success: false,
          neName: cellNeName,
          statusCode: response.statusCode,
          body: response.body,
        });
        setOutput(prev => [...prev, `[FAIL] Cell 증설 실패 (HTTP ${response.statusCode})`]);
      }
    } catch (error) {
      setCellResult({ success: false, error: error.message });
      setOutput(prev => [...prev, `[ERROR] ${error.message}`]);
    }
    setCellLoading(false);
  };

  // NE 목록 조회
  const handleGetNEList = async () => {
    if (!getSelectedServer()) return;

    setListLoading(true);
    setListResult(null);
    setNeList([]);
    setOutput(prev => [...prev, `=== NE 목록 조회 ===`]);

    try {
      const response = await callUSMApi('/oss/neList', 'GET', null, 30000);

      let neListData;
      try {
        const parsed = typeof response.body === 'string' ? JSON.parse(response.body) : response.body;
        neListData = typeof parsed.neList === 'string' ? JSON.parse(parsed.neList) : parsed.neList;
      } catch (e) {
        neListData = response.body;
      }

      if (response.statusCode === 200 && Array.isArray(neListData)) {
        setNeList(neListData);
        setListResult({ success: true, count: neListData.length });
        setOutput(prev => [...prev, `[OK] 총 ${neListData.length}개 NE 조회됨`]);
      } else {
        setListResult({ success: false, body: response.body });
        setOutput(prev => [...prev, `[FAIL] 조회 실패`]);
      }
    } catch (error) {
      setListResult({ success: false, error: error.message });
      setOutput(prev => [...prev, `[ERROR] ${error.message}`]);
    }
    setListLoading(false);
  };

  return (
    <div style={styles.container}>
      {/* 헤더 */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.headerIcon}>🔧</span>
          <div>
            <h2 style={styles.title}>USM 자동화 도구</h2>
            <p style={styles.subtitle}>NE 증설 / Cell 증설 / NE 목록 조회</p>
          </div>
        </div>
      </div>

      {/* USM 서버 선택 카드 */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>📡 USM 서버 선택</h3>
        <div style={styles.formGroup}>
          <label style={styles.label}>대상 USM 서버</label>
          <select
            value={selectedServerId}
            onChange={(e) => setSelectedServerId(e.target.value)}
            style={styles.select}
          >
            <option value="">서버를 선택하세요</option>
            {servers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.mcmIp}:{s.apiPort})
              </option>
            ))}
          </select>
        </div>
        <div style={styles.serverAddRow}>
          <input
            type="text"
            value={newServerName}
            onChange={(e) => setNewServerName(e.target.value)}
            placeholder="서버 이름 (예: USM 운용 서버)"
            style={{ ...styles.input, maxWidth: '200px' }}
          />
          <input
            type="text"
            value={newServerIp}
            onChange={(e) => setNewServerIp(e.target.value)}
            placeholder="IP 주소 (예: 10.251.209.131)"
            style={{ ...styles.input, maxWidth: '200px' }}
          />
          <input
            type="number"
            value={newServerPort}
            onChange={(e) => setNewServerPort(e.target.value)}
            placeholder="포트"
            style={{ ...styles.input, maxWidth: '80px' }}
          />
          <button onClick={handleAddServer} style={styles.btnSecondary}>
            + 서버 추가
          </button>
        </div>
      </div>

      {/* 탭 메뉴 */}
      <div style={styles.tabs}>
        <button
          onClick={() => setActiveTab('ne')}
          style={activeTab === 'ne' ? styles.tabActive : styles.tab}
        >
          NE 증설
        </button>
        <button
          onClick={() => setActiveTab('cell')}
          style={activeTab === 'cell' ? styles.tabActive : styles.tab}
        >
          Cell 증설
        </button>
        <button
          onClick={() => setActiveTab('list')}
          style={activeTab === 'list' ? styles.tabActive : styles.tab}
        >
          NE 목록 조회
        </button>
      </div>

      {/* NE 증설 탭 */}
      {activeTab === 'ne' && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>📋 NE 증설</h3>
          <div style={styles.formGroup}>
            <label style={styles.label}>NE 증설 CSV 파일</label>
            <div
              style={styles.fileDrop}
              onClick={() => neFileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = '#e94560'; }}
              onDragLeave={(e) => { e.currentTarget.style.borderColor = '#3a3a5a'; }}
              onDrop={(e) => handleDrop(e, setNeFileName, setNeCsvContent)}
            >
              <p style={styles.fileDropText}>📁 CSV 파일을 클릭하거나 드래그하여 첨부하세요</p>
              {neFileName && <p style={styles.fileName}>✓ {neFileName}</p>}
            </div>
            <input
              ref={neFileInputRef}
              type="file"
              accept=".csv"
              style={{ display: 'none' }}
              onChange={(e) => handleFileSelect(e, setNeFileName, setNeCsvContent)}
            />
          </div>
          <button
            onClick={handleProvisionNE}
            style={styles.btnPrimary}
            disabled={neLoading}
          >
            {neLoading ? '⏳ 실행 중...' : 'NE 증설 실행'}
          </button>
          {neLoading && (
            <div style={styles.loading}>
              <div style={styles.spinner} />
              <p>USM API 호출 중... (최대 2분)</p>
            </div>
          )}
          {neResult && (
            <div style={neResult.success ? styles.resultSuccess : styles.resultError}>
              <div style={styles.resultTitle}>
                {neResult.success ? '✅' : '❌'} NE 증설 {neResult.success ? '성공' : '실패'}
                {neResult.neName ? `: ${neResult.neName}` : ''}
              </div>
              {neResult.result && <div>결과: {neResult.result}</div>}
              {neResult.statusCode && <div>HTTP: {neResult.statusCode}</div>}
              {neResult.error && <div>오류: {neResult.error}</div>}
              {neResult.body && (
                <pre style={styles.pre}>{JSON.stringify(neResult.body, null, 2)}</pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Cell 증설 탭 */}
      {activeTab === 'cell' && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>📋 Cell 증설</h3>
          <div style={styles.formGroup}>
            <label style={styles.label}>대상 NE Name</label>
            <input
              type="text"
              value={cellNeName}
              onChange={(e) => setCellNeName(e.target.value)}
              placeholder="예: NVGNB_13172"
              style={styles.input}
            />
          </div>
          <div style={styles.formGroup}>
            <label style={styles.label}>Cell 증설 CSV 파일</label>
            <div
              style={styles.fileDrop}
              onClick={() => cellFileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = '#e94560'; }}
              onDragLeave={(e) => { e.currentTarget.style.borderColor = '#3a3a5a'; }}
              onDrop={(e) => handleDrop(e, setCellFileName, setCellCsvContent)}
            >
              <p style={styles.fileDropText}>📁 CSV 파일을 클릭하거나 드래그하여 첨부하세요</p>
              {cellFileName && <p style={styles.fileName}>✓ {cellFileName}</p>}
            </div>
            <input
              ref={cellFileInputRef}
              type="file"
              accept=".csv"
              style={{ display: 'none' }}
              onChange={(e) => handleFileSelect(e, setCellFileName, setCellCsvContent)}
            />
          </div>
          <button
            onClick={handleProvisionCell}
            style={styles.btnPrimary}
            disabled={cellLoading}
          >
            {cellLoading ? '⏳ 실행 중...' : 'Cell 증설 실행'}
          </button>
          {cellLoading && (
            <div style={styles.loading}>
              <div style={styles.spinner} />
              <p>USM API 호출 중... (최대 30분 소요 가능)</p>
            </div>
          )}
          {cellResult && (
            <div style={cellResult.success ? styles.resultSuccess : styles.resultError}>
              <div style={styles.resultTitle}>
                {cellResult.success ? '✅' : '❌'} Cell 증설 {cellResult.success ? '성공' : '실패'}
                {cellResult.neName ? `: ${cellResult.neName}` : ''}
                {cellResult.cellCount ? ` (Cell ${cellResult.cellCount}개)` : ''}
              </div>
              {cellResult.result && <div>결과: {cellResult.result}</div>}
              {cellResult.statusCode && <div>HTTP: {cellResult.statusCode}</div>}
              {cellResult.error && <div>오류: {cellResult.error}</div>}
              {cellResult.body && (
                <pre style={styles.pre}>{JSON.stringify(cellResult.body, null, 2)}</pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* NE 목록 조회 탭 */}
      {activeTab === 'list' && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>📋 NE 목록 조회</h3>
          <button
            onClick={handleGetNEList}
            style={styles.btnPrimary}
            disabled={listLoading}
          >
            {listLoading ? '⏳ 조회 중...' : '🔍 조회'}
          </button>
          {listLoading && (
            <div style={styles.loading}>
              <div style={styles.spinner} />
              <p>조회 중...</p>
            </div>
          )}
          {listResult && (
            <div style={listResult.success ? styles.resultSuccess : styles.resultError}>
              <div style={styles.resultTitle}>
                {listResult.success ? '✅' : '❌'} {listResult.success ? `총 ${listResult.count}개 NE` : '조회 실패'}
              </div>
              {listResult.error && <div>오류: {listResult.error}</div>}
              {listResult.body && (
                <pre style={styles.pre}>{JSON.stringify(listResult.body, null, 2)}</pre>
              )}
            </div>
          )}
          {neList.length > 0 && (
            <div style={styles.neListTable}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>NE Name</th>
                    <th style={styles.th}>Type</th>
                    <th style={styles.th}>Version</th>
                    <th style={styles.th}>IP</th>
                    <th style={styles.th}>State</th>
                  </tr>
                </thead>
                <tbody>
                  {neList.map((ne, i) => (
                    <tr key={i}>
                      <td style={styles.td}>{ne.neName || ne.neId || ''}</td>
                      <td style={styles.td}>{ne.neType || ''}</td>
                      <td style={styles.td}>{ne.version || ''}</td>
                      <td style={styles.td}>{ne.ip_addr || ''}</td>
                      <td style={styles.td}>{ne.conn_state || ''}/{ne.admin_state || ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 로그 영역 */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>📝 실행 로그</h3>
        <div style={styles.output}>
          {output.length === 0 ? (
            <div style={styles.emptyOutput}>실행 로그가 여기에 표시됩니다</div>
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
    background: 'linear-gradient(135deg, #16213e, #0f3460)',
    borderRadius: '12px',
    padding: '20px 24px',
    marginBottom: '20px',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  headerIcon: {
    fontSize: '36px',
  },
  title: {
    fontSize: '22px',
    color: '#e94560',
    margin: '0 0 4px 0',
  },
  subtitle: {
    fontSize: '13px',
    color: '#888',
    margin: 0,
  },
  card: {
    background: '#16213e',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '20px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
  },
  cardTitle: {
    fontSize: '18px',
    marginBottom: '16px',
    color: '#e94560',
    borderBottom: '1px solid #0f3460',
    paddingBottom: '8px',
  },
  formGroup: {
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    fontSize: '14px',
    marginBottom: '6px',
    color: '#aaa',
  },
  select: {
    width: '100%',
    padding: '10px 14px',
    background: '#1a1a2e',
    border: '1px solid #0f3460',
    borderRadius: '8px',
    color: '#eee',
    fontSize: '14px',
    outline: 'none',
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    background: '#1a1a2e',
    border: '1px solid #0f3460',
    borderRadius: '8px',
    color: '#eee',
    fontSize: '14px',
    outline: 'none',
  },
  serverAddRow: {
    display: 'flex',
    gap: '8px',
    marginTop: '10px',
  },
  fileDrop: {
    border: '2px dashed #3a3a5a',
    borderRadius: '10px',
    padding: '30px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s',
    background: '#1a1a2e',
  },
  fileDropText: {
    color: '#888',
    fontSize: '14px',
  },
  fileName: {
    color: '#e94560',
    fontWeight: 'bold',
    marginTop: '8px',
  },
  tabs: {
    display: 'flex',
    gap: '4px',
    marginBottom: '20px',
  },
  tab: {
    flex: 1,
    padding: '12px',
    background: '#16213e',
    border: 'none',
    borderRadius: '8px 8px 0 0',
    color: '#888',
    cursor: 'pointer',
    fontSize: '14px',
    borderBottom: '2px solid transparent',
  },
  tabActive: {
    flex: 1,
    padding: '12px',
    background: '#16213e',
    border: 'none',
    borderRadius: '8px 8px 0 0',
    color: '#e94560',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold',
    borderBottom: '3px solid #e94560',
  },
  btnPrimary: {
    padding: '12px 28px',
    background: '#e94560',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  btnSecondary: {
    padding: '10px 20px',
    background: '#0f3460',
    border: 'none',
    borderRadius: '8px',
    color: '#eee',
    fontSize: '14px',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  loading: {
    textAlign: 'center',
    padding: '20px',
    color: '#888',
  },
  spinner: {
    width: '36px',
    height: '36px',
    border: '4px solid #0f3460',
    borderTop: '4px solid #e94560',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    margin: '0 auto 10px',
  },
  resultSuccess: {
    marginTop: '16px',
    padding: '16px',
    borderRadius: '8px',
    background: '#0d3b1f',
    border: '1px solid #1a7a3a',
    fontSize: '14px',
    color: '#4ade80',
  },
  resultError: {
    marginTop: '16px',
    padding: '16px',
    borderRadius: '8px',
    background: '#3b0d0d',
    border: '1px solid #7a1a1a',
    fontSize: '14px',
    color: '#f87171',
  },
  resultTitle: {
    fontWeight: 'bold',
    marginBottom: '8px',
  },
  pre: {
    background: 'rgba(0,0,0,0.3)',
    padding: '12px',
    borderRadius: '6px',
    overflowX: 'auto',
    fontSize: '13px',
    marginTop: '8px',
    color: '#ccc',
  },
  neListTable: {
    marginTop: '16px',
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    background: '#0f3460',
    padding: '10px',
    textAlign: 'left',
    borderRadius: '4px',
    color: '#aaa',
  },
  td: {
    padding: '8px 10px',
    borderBottom: '1px solid #0f3460',
    color: '#ccc',
  },
  output: {
    background: '#0d0d1a',
    borderRadius: '8px',
    padding: '16px',
    minHeight: '120px',
    maxHeight: '300px',
    overflow: 'auto',
    fontFamily: 'Consolas, monospace',
    fontSize: '12px',
  },
  emptyOutput: {
    color: '#555',
    textAlign: 'center',
    padding: '20px',
  },
  outputLine: {
    padding: '2px 0',
    color: '#aaa',
    whiteSpace: 'pre-wrap',
  },
};

export default USMAutomation;
