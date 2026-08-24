import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import USMAutomation from './components/USMAutomation';
import LSMAutomation from './components/LSMAutomation';
import MosaicBTSampleRequest from './components/MosaicBTSampleRequest';

import ChatBackup from './components/ChatBackup';
import Monitor from './components/Monitor';
import DRMUngroup from './components/DRMUngroup';
import LSMPackageManager from './components/LSMPackageManager';
import USMPackageVersionChanger from './components/USMPackageVersionChanger';




// 아이콘 SVG 컴포넌트
const Icons = {
  Dashboard: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  USM: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  LSM: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 3a3 3 0 00-3 3v12a3 3 0 003 3 3 3 0 003-3 3 3 0 00-3-3H6a3 3 0 00-3 3 3 3 0 003 3 3 3 0 003-3V6a3 3 0 00-3-3 3 3 0 00-3 3 3 3 0 003 3h12a3 3 0 003-3 3 3 0 00-3-3z" />
    </svg>
  ),
  Mosaic: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </svg>
  ),
  Chat: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  ),
  Monitor: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
      <line x1="8" y1="21" x2="16" y2="21" />
      <line x1="12" y1="17" x2="12" y2="21" />
    </svg>
  ),
  DRM: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 9h6v6H9z" />
      <path d="M12 3v6M12 15v6M3 12h6M15 12h6" />
    </svg>
  ),
  Package: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
  VersionTag: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z" />
      <line x1="7" y1="7" x2="7.01" y2="7" />
    </svg>
  ),
  Cat: () => (



    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5-9c.83 0 1.5-.67 1.5-1.5S7.83 8 7 8s-1.5.67-1.5 1.5S6.17 11 7 11zm3.5 3c-.83 0-1.5.67-1.5 1.5S9.67 17 10.5 17s1.5-.67 1.5-1.5-.67-1.5-1.5-1.5zm3.5-3c.83 0 1.5-.67 1.5-1.5S14.83 8 14 8s-1.5.67-1.5 1.5.67 1.5 1.5 1.5zm3.5 3c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"/>
    </svg>
  ),
};

// 메뉴 항목 정의
const menuItems = [
  { id: 'dashboard', label: '대시보드', icon: Icons.Dashboard },
  { id: 'usm', label: 'USM NE 증설', icon: Icons.USM },
  { id: 'usm-pkg', label: 'USM NE PKG 버전 변경', icon: Icons.VersionTag },

  { id: 'lsm', label: 'LSM NE 증설', icon: Icons.LSM },

  { id: 'lsm-pkg', label: 'LSM eNB 패키지 설치', icon: Icons.Package },
  { id: 'mosaic', label: 'Mosaic BT시료요청', icon: Icons.Mosaic },


  { id: 'drm', label: 'DRM 문서 풀기', icon: Icons.DRM },
  { id: 'chat', label: 'Cline 대화 백업', icon: Icons.Chat },
  { id: 'monitor', label: '미니 PC 모니터링', icon: Icons.Monitor },
];


// 컴포넌트 매핑
const componentMap = {
  dashboard: Dashboard,
  usm: USMAutomation,
  'usm-pkg': USMPackageVersionChanger,
  lsm: LSMAutomation,

  'lsm-pkg': LSMPackageManager,
  mosaic: MosaicBTSampleRequest,


  drm: DRMUngroup,
  chat: ChatBackup,
  monitor: Monitor,
};


function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [appVersion, setAppVersion] = useState('1.0.0');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    // 앱 버전 가져오기
    window.electronAPI?.getAppVersion().then(setAppVersion);
  }, []);

  const ActiveComponent = componentMap[activeTab] || Dashboard;

  return (
    <div style={styles.appContainer}>
      {/* 사이드바 */}
      <aside style={{
        ...styles.sidebar,
        width: isSidebarOpen ? '240px' : '60px',
      }}>
        {/* 로고 */}
        <div style={styles.logo}>
          <Icons.Cat />
          {isSidebarOpen && <span style={styles.logoText}>Yaong Tools</span>}
        </div>

        {/* 메뉴 */}
        <nav style={styles.nav}>
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                ...styles.navItem,
                backgroundColor: activeTab === item.id ? '#4a4a6a' : 'transparent',
              }}
            >
              <item.icon />
              {isSidebarOpen && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* 버전 */}
        <div style={styles.version}>
          v{appVersion}
        </div>
      </aside>

      {/* 메인 컨텐츠 */}
      <main style={styles.main}>
        {/* 헤더 */}
        <header style={styles.header}>
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            style={styles.toggleBtn}
          >
            ☰
          </button>
          <h1 style={styles.title}>
            {menuItems.find(m => m.id === activeTab)?.label}
          </h1>
        </header>

        {/* 컨텐츠 */}
        <div style={styles.content}>
          <ActiveComponent />
        </div>
      </main>
    </div>
  );
}

const styles = {
  appContainer: {
    display: 'flex',
    width: '100vw',
    height: '100vh',
    background: '#1a1a2e',
  },
  sidebar: {
    background: '#16162a',
    borderRight: '1px solid #2a2a4a',
    display: 'flex',
    flexDirection: 'column',
    transition: 'width 0.3s ease',
    overflow: 'hidden',
  },
  logo: {
    padding: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    borderBottom: '1px solid #2a2a4a',
    color: '#fff',
  },
  logoText: {
    fontSize: '20px',
    fontWeight: 'bold',
  },
  nav: {
    flex: 1,
    padding: '10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    border: 'none',
    borderRadius: '8px',
    color: '#aaa',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontSize: '14px',
  },
  version: {
    padding: '16px',
    textAlign: 'center',
    color: '#666',
    fontSize: '12px',
    borderTop: '1px solid #2a2a4a',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '16px 24px',
    borderBottom: '1px solid #2a2a4a',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  toggleBtn: {
    background: 'none',
    border: 'none',
    color: '#aaa',
    fontSize: '20px',
    cursor: 'pointer',
    padding: '4px 8px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    overflow: 'auto',
    padding: '24px',
  },
};

export default App;
