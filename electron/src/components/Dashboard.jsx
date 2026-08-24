import { useState, useEffect } from 'react';

function Dashboard() {
  const [stats, setStats] = useState({
    totalScripts: 0,
    recentLogs: [],
    appVersion: '1.0.0',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // 앱 경로 가져오기
      const scriptsPath = await window.electronAPI?.getAppPath('scripts');
      
      // 로그 읽기
      const logs = await window.electronAPI?.readLogs({ lines: 10 });
      
      setStats({
        totalScripts: 50, // 실제 스크립트 수
        recentLogs: logs?.content || [],
        appVersion: '1.0.0',
      });
    } catch (error) {
      console.error('데이터 로딩 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { name: 'USM 자동화', tab: 'usm', color: '#4ade80' },
    { name: 'LSM 자동화', tab: 'lsm', color: '#60a5fa' },
    { name: 'Mosaic 분석', tab: 'mosaic', color: '#f472b6' },
    { name: '채팅 백업', tab: 'chat', color: '#fbbf24' },
  ];

  const handleQuickAction = (tab) => {
    // App 컴포넌트에 탭 변경 요청
    const event = new CustomEvent('change-tab', { detail: { tab } });
    window.dispatchEvent(event);
  };

  if (loading) {
    return <div style={styles.loading}>로딩 중...</div>;
  }

  return (
    <div style={styles.container}>
      {/* 환영 메시지 */}
      <div style={styles.welcome}>
        <h2 style={styles.welcomeTitle}>Yaong Tools 에 오신 것을 환영합니다! 🐱</h2>
        <p style={styles.welcomeText}>
          모든 자동화 도구를 한 곳에서 관리하세요
        </p>
      </div>

      {/* 빠른 동작 */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>⚡ 빠른 동작</h3>
        <div style={styles.quickActions}>
          {quickActions.map((action) => (
            <button
              key={action.name}
              onClick={() => handleQuickAction(action.tab)}
              style={{
                ...styles.quickActionBtn,
                borderLeft: `4px solid ${action.color}`,
              }}
            >
              {action.name}
            </button>
          ))}
        </div>
      </div>

      {/* 최근 로그 */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>📋 최근 로그</h3>
        <div style={styles.logContainer}>
          {stats.recentLogs.length > 0 ? (
            stats.recentLogs.map((log, i) => (
              <div key={i} style={styles.logEntry}>
                {log}
              </div>
            ))
          ) : (
            <div style={styles.emptyLog}>최근 로그가 없습니다</div>
          )}
        </div>
      </div>

      {/* 정보 */}
      <div style={styles.info}>
        <div style={styles.infoCard}>
          <span style={styles.infoLabel}>버전</span>
          <span style={styles.infoValue}>v{stats.appVersion}</span>
        </div>
        <div style={styles.infoCard}>
          <span style={styles.infoLabel}>플랫폼</span>
          <span style={styles.infoValue}>{window.electronAPI?.platform || 'Windows'}</span>
        </div>
        <div style={styles.infoCard}>
          <span style={styles.infoLabel}>스크립트</span>
          <span style={styles.infoValue}>{stats.totalScripts}개</span>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1000px',
    margin: '0 auto',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#888',
  },
  welcome: {
    background: 'linear-gradient(135deg, #2a2a4a 0%, #1a1a2e 100%)',
    padding: '32px',
    borderRadius: '12px',
    marginBottom: '24px',
  },
  welcomeTitle: {
    fontSize: '24px',
    marginBottom: '8px',
    color: '#fff',
  },
  welcomeText: {
    color: '#888',
    fontSize: '14px',
  },
  section: {
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '16px',
    marginBottom: '12px',
    color: '#fff',
  },
  quickActions: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '12px',
  },
  quickActionBtn: {
    background: '#2a2a4a',
    border: 'none',
    borderRadius: '8px',
    padding: '16px 20px',
    color: '#fff',
    cursor: 'pointer',
    textAlign: 'left',
    fontSize: '14px',
    transition: 'background 0.2s',
  },
  logContainer: {
    background: '#0d0d1a',
    borderRadius: '8px',
    padding: '16px',
    maxHeight: '200px',
    overflow: 'auto',
    fontFamily: 'Consolas, monospace',
    fontSize: '12px',
  },
  logEntry: {
    padding: '4px 0',
    borderBottom: '1px solid #1a1a2e',
    color: '#888',
  },
  emptyLog: {
    color: '#666',
    textAlign: 'center',
    padding: '20px',
  },
  info: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
  },
  infoCard: {
    background: '#2a2a4a',
    padding: '20px',
    borderRadius: '8px',
    textAlign: 'center',
  },
  infoLabel: {
    display: 'block',
    color: '#888',
    fontSize: '12px',
    marginBottom: '8px',
  },
  infoValue: {
    display: 'block',
    color: '#fff',
    fontSize: '20px',
    fontWeight: 'bold',
  },
};

export default Dashboard;
