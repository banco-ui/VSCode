import { useState, useEffect, useCallback, useRef } from 'react';

function Monitor() {
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState({ checkedIntervalSeconds: 30, failuresBeforeOffline: 3 });
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [checkProgress, setCheckProgress] = useState(null); // { current, total }
  const [showEditor, setShowEditor] = useState(false);

  const [editingDevice, setEditingDevice] = useState(null);
  const [formData, setFormData] = useState({ name: '', ip: '', enabled: true });

  const refreshTimer = useRef(null);

  const statusLabel = {
    online: '정상', offline: '장애', degraded: '재확인 중',
    checking: '검사 중', disabled: '중지됨',
  };

  const statusColor = {
    online: '#3fb950', offline: '#f85149', degraded: '#d29922',
    checking: '#74b9ff', disabled: '#636e72',
  };

  const formatTime = (value) => value
    ? new Intl.DateTimeFormat('ko-KR', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value))
    : '-';

  const refresh = useCallback(async () => {
    try {
      const result = await window.electronAPI?.monitorGetStatus();
      if (result?.success) {
        setRows(result.data.rows);
        setMeta({
          checkedIntervalSeconds: result.data.checkedIntervalSeconds,
          failuresBeforeOffline: result.data.failuresBeforeOffline,
        });
      }
    } catch (e) { console.error('상태 조회 오류:', e); }
  }, []);

  useEffect(() => {
    refresh();
    refreshTimer.current = setInterval(refresh, 5000);
    return () => { if (refreshTimer.current) clearInterval(refreshTimer.current); };
  }, [refresh]);

  const handleCheckNow = async () => {
    setIsChecking(true);
    // 검사 중 자동 새로고침 일시 중지
    if (refreshTimer.current) { clearInterval(refreshTimer.current); refreshTimer.current = null; }
    try {
      const result = await window.electronAPI?.monitorCheckNow();
      if (result?.success) {
        setRows(result.data.rows);
      }
    } catch (e) { console.error(e); }
    setIsChecking(false);
    // 자동 새로고침 재개
    refreshTimer.current = setInterval(refresh, 5000);
  };

  const handleStartMonitoring = async () => {
    setIsChecking(true);
    if (refreshTimer.current) { clearInterval(refreshTimer.current); refreshTimer.current = null; }
    try {
      const result = await window.electronAPI?.monitorStart();
      if (result?.success) {
        setIsMonitoring(true);
        setRows(result.data?.rows || []);
      }
    } catch (e) { console.error(e); }
    setIsChecking(false);
    refreshTimer.current = setInterval(refresh, 5000);
  };


  const handleStopMonitoring = async () => {
    await window.electronAPI?.monitorStop();
    setIsMonitoring(false);
  };

  const handlePingTest = async (ip) => {
    await window.electronAPI?.monitorPingTest(ip);
  };

  const openEditor = (device) => {
    setEditingDevice(device || null);
    setFormData(device ? { name: device.name, ip: device.ip, enabled: device.enabled } : { name: '', ip: '', enabled: true });
    setShowEditor(true);
  };

  const handleSaveDevice = async () => {
    const item = {
      id: editingDevice?.id || `${formData.name.trim()}-${formData.ip.trim()}`,
      name: formData.name.trim(),
      ip: formData.ip.trim(),
      enabled: formData.enabled,
    };
    const next = editingDevice
      ? rows.map(r => r.id === editingDevice.id ? item : r)
      : [...rows, item];
    await window.electronAPI?.monitorSaveDevices(next);
    setShowEditor(false);
    refresh();
  };

  const handleDeleteDevice = async (id) => {
    if (window.confirm('이 장비를 목록에서 삭제할까요?')) {
      await window.electronAPI?.monitorSaveDevices(rows.filter(r => r.id !== id));
      refresh();
    }
  };

  const handleToggleEnabled = async (device) => {
    const next = rows.map(r => r.id === device.id ? { ...r, enabled: !r.enabled } : r);
    await window.electronAPI?.monitorSaveDevices(next);
    refresh();
  };

  const online = rows.filter(r => r.status === 'online').length;
  const offline = rows.filter(r => r.status === 'offline').length;
  const checking = rows.length - online - offline;
  const offlineDevices = rows.filter(r => r.status === 'offline').map(r => r.name);

  return (
    <div style={styles.container}>
      {/* 헤더 */}
      <div style={styles.header}>
        <div>
          <p style={styles.eyebrow}>INTERNAL NETWORK</p>
          <h1 style={styles.title}>미니PC 상태 모니터</h1>
          <p style={styles.meta}>{meta.checkedIntervalSeconds}초마다 검사 · {meta.failuresBeforeOffline}회 연속 실패 시 장애</p>
        </div>
        <div style={styles.actions}>
          {!isMonitoring ? (
            <button onClick={handleStartMonitoring} style={styles.btnSecondary}>▶ 모니터링 시작</button>
          ) : (
            <button onClick={handleStopMonitoring} style={styles.btnDanger}>■ 모니터링 중지</button>
          )}
          <button onClick={handleCheckNow} style={styles.btnPrimary} disabled={isChecking}>
            {isChecking ? '검사 중…' : '🔍 지금 검사'}
          </button>
        </div>
      </div>

      {/* 요약 카드 */}
      <div style={styles.summary}>
        <div style={styles.summaryCard}>
          <span style={styles.summaryLabel}>전체</span>
          <strong style={styles.summaryValue}>{rows.length}</strong>
        </div>
        <div style={{ ...styles.summaryCard, borderColor: '#3fb950' }}>
          <span style={styles.summaryLabel}>정상</span>
          <strong style={{ ...styles.summaryValue, color: '#3fb950' }}>{online}</strong>
        </div>
        <div style={{ ...styles.summaryCard, borderColor: '#f85149' }}>
          <span style={styles.summaryLabel}>장애</span>
          <strong style={{ ...styles.summaryValue, color: '#f85149' }}>{offline}</strong>
        </div>
        <div style={{ ...styles.summaryCard, borderColor: '#d29922' }}>
          <span style={styles.summaryLabel}>확인 중</span>
          <strong style={{ ...styles.summaryValue, color: '#d29922' }}>{checking}</strong>
        </div>
      </div>

      {/* 장애 알림 */}
      {offline > 0 && (
        <div style={styles.alert}>
          ⚠️ 장애 감지: {offlineDevices.join(', ')}
        </div>
      )}

      {/* 장비 목록 */}
      <div style={styles.panel}>
        <div style={styles.panelHead}>
          <h2 style={styles.panelTitle}>장비 목록 ({rows.length}대)</h2>
          <button onClick={() => openEditor()} style={styles.btnAdd}>+ 장비 추가</button>
        </div>
        <div style={styles.deviceList}>
          {rows.length === 0 ? (
            <div style={styles.empty}>등록된 장비가 없습니다. '장비 추가' 버튼을 눌러 장비를 등록하세요.</div>
          ) : (
            rows.map((device, i) => (
              <div key={i} style={{
                ...styles.deviceCard,
                borderLeftColor: statusColor[device.status] || '#333',
              }}>
                <div style={styles.deviceMain}>
                  <span style={{ ...styles.dot, background: statusColor[device.status] || '#333' }} />
                  <div>
                    <h3 style={styles.deviceName}>{device.name}</h3>
                    <p style={styles.deviceIp}>{device.ip}</p>
                  </div>
                </div>
                <div style={styles.deviceStatus}>
                  <span style={{ ...styles.statusBadge, background: statusColor[device.status] || '#333' }}>
                    {statusLabel[device.status] || '알 수 없음'}
                  </span>
                </div>
                <div style={styles.deviceDetails}>
                  {device.status === 'online'
                    ? `${device.latency ?? '-'} ms · ${formatTime(device.checkedAt)}`
                    : `마지막 정상: ${formatTime(device.lastOnlineAt)}`}
                </div>
                <div style={styles.deviceEvents}>
                  {device.events?.slice(0, 3).map((ev, j) => (
                    <div key={j} style={styles.eventItem}>
                      <span style={{ color: ev.type === 'offline' ? '#f85149' : '#3fb950' }}>●</span>
                      <span>{ev.message}</span>
                      <span style={styles.eventTime}>{formatTime(ev.at)}</span>
                    </div>
                  ))}
                </div>
                <div style={styles.deviceActions}>
                  <button onClick={() => handlePingTest(device.ip)} style={styles.btnAction}>📡 Ping Test</button>
                  <button onClick={() => handleToggleEnabled(device)} style={styles.btnAction}>
                    {device.enabled ? '⏸ 비활성' : '▶ 활성'}
                  </button>
                  <button onClick={() => openEditor(device)} style={styles.btnAction}>✏️ 수정</button>
                  <button onClick={() => handleDeleteDevice(device.id)} style={styles.btnActionDanger}>🗑 삭제</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 장비 추가/수정 모달 */}
      {showEditor && (
        <div style={styles.modalOverlay} onClick={() => setShowEditor(false)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 style={styles.modalTitle}>{editingDevice ? '장비 수정' : '장비 추가'}</h2>
            <div style={styles.formGroup}>
              <label style={styles.formLabel}>표시 이름</label>
              <input
                type="text"
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                placeholder="예: 미니PC-01"
                style={styles.modalInput}
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.formLabel}>IP 주소 또는 호스트명</label>
              <input
                type="text"
                value={formData.ip}
                onChange={e => setFormData({ ...formData, ip: e.target.value })}
                placeholder="예: 192.168.0.101"
                style={styles.modalInput}
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={e => setFormData({ ...formData, enabled: e.target.checked })}
                />
                모니터링 사용
              </label>
            </div>
            <div style={styles.modalActions}>
              <button onClick={() => setShowEditor(false)} style={styles.btnCancel}>취소</button>
              <button onClick={handleSaveDevice} style={styles.btnSave}>저장</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: { maxWidth: '900px', margin: '0 auto' },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
    marginBottom: '20px', flexWrap: 'wrap', gap: '12px',
  },
  eyebrow: { fontSize: '11px', color: '#636e72', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 4px 0' },
  title: { fontSize: '22px', color: '#e94560', margin: '0 0 4px 0' },
  meta: { fontSize: '13px', color: '#888', margin: 0 },
  actions: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  btnPrimary: {
    padding: '10px 20px', background: '#e94560', border: 'none', borderRadius: '8px',
    color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px',
  },
  btnSecondary: {
    padding: '10px 20px', background: '#0f3460', border: 'none', borderRadius: '8px',
    color: '#74b9ff', cursor: 'pointer', fontSize: '14px',
  },
  btnDanger: {
    padding: '10px 20px', background: '#f85149', border: 'none', borderRadius: '8px',
    color: '#fff', cursor: 'pointer', fontSize: '14px',
  },
  summary: {
    display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px',
  },
  summaryCard: {
    background: '#16213e', border: '1px solid #0f3460', borderRadius: '10px',
    padding: '16px', textAlign: 'center',
  },
  summaryLabel: { fontSize: '12px', color: '#888', display: 'block', marginBottom: '4px' },
  summaryValue: { fontSize: '28px', fontWeight: 'bold', color: '#fff' },
  alert: {
    background: '#3b0d0d', border: '1px solid #7a1a1a', borderRadius: '8px',
    padding: '12px 16px', marginBottom: '16px', color: '#f85149', fontSize: '14px', fontWeight: 'bold',
  },
  panel: {
    background: '#16213e', borderRadius: '12px', border: '1px solid #0f3460', overflow: 'hidden',
  },
  panelHead: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 20px', borderBottom: '1px solid #0f3460',
  },
  panelTitle: { fontSize: '14px', color: '#74b9ff', margin: 0, textTransform: 'uppercase', letterSpacing: '1px' },
  btnAdd: {
    background: '#0f3460', border: 'none', color: '#74b9ff', padding: '6px 14px',
    borderRadius: '6px', cursor: 'pointer', fontSize: '13px',
  },
  deviceList: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
    gap: '12px', padding: '16px',
  },
  empty: {
    color: '#636e72', textAlign: 'center', padding: '40px', gridColumn: '1 / -1',
  },
  deviceCard: {
    background: '#1a1a2e', borderRadius: '10px', padding: '16px',
    borderLeft: '4px solid #333',
  },
  deviceMain: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' },
  dot: { width: '12px', height: '12px', borderRadius: '50%', flexShrink: 0 },
  deviceName: { fontSize: '15px', color: '#fff', margin: '0 0 2px 0' },
  deviceIp: { fontSize: '13px', color: '#888', margin: 0 },
  deviceStatus: { marginBottom: '8px' },
  statusBadge: {
    fontSize: '12px', color: '#fff', padding: '2px 10px', borderRadius: '10px', fontWeight: 'bold',
  },
  deviceDetails: { fontSize: '12px', color: '#a0a0a0', marginBottom: '8px' },
  deviceEvents: { marginBottom: '10px' },
  eventItem: {
    display: 'flex', gap: '6px', alignItems: 'center', fontSize: '11px', color: '#888', padding: '1px 0',
  },
  eventTime: { color: '#484f58', marginLeft: 'auto' },
  deviceActions: { display: 'flex', gap: '6px', flexWrap: 'wrap' },
  btnAction: {
    background: '#0f3460', border: 'none', color: '#74b9ff', padding: '4px 10px',
    borderRadius: '6px', cursor: 'pointer', fontSize: '12px',
  },
  btnActionDanger: {
    background: '#3b0d0d', border: 'none', color: '#f85149', padding: '4px 10px',
    borderRadius: '6px', cursor: 'pointer', fontSize: '12px',
  },
  modalOverlay: {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
  },
  modal: {
    background: '#16213e', borderRadius: '12px', padding: '24px',
    width: '400px', maxWidth: '90vw', border: '1px solid #0f3460',
  },
  modalTitle: { fontSize: '18px', color: '#e94560', margin: '0 0 20px 0' },
  formGroup: { marginBottom: '16px' },
  formLabel: { display: 'block', fontSize: '13px', color: '#a0a0a0', marginBottom: '6px' },
  modalInput: {
    width: '100%', padding: '10px 12px', background: '#1a1a2e', border: '1px solid #0f3460',
    borderRadius: '8px', color: '#fff', fontSize: '14px', outline: 'none',
  },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '8px', color: '#ccc', fontSize: '14px', cursor: 'pointer' },
  modalActions: { display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '20px' },
  btnCancel: {
    padding: '8px 16px', background: 'transparent', border: '1px solid #0f3460',
    color: '#a0a0a0', borderRadius: '8px', cursor: 'pointer', fontSize: '14px',
  },
  btnSave: {
    padding: '8px 16px', background: '#e94560', border: 'none',
    color: '#fff', borderRadius: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: 'bold',
  },
};

export default Monitor;
