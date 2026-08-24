로컬 네트워크에 연결된 미니 PC 들의 상태 (온라인/오프라인) 를 실시간으로 모니터링하는 대시보드입니다.

## 위치
```
d:\Data\AI\VSCode\mini-pc-monitor\
```

## 파일 구조
```
mini-pc-monitor/
├── server.js          # Express 서버 (Ping 기반 상태 확인)
├── devices.json       # 등록 장비 목록
├── package.json       # 의존성 설정
├── README.md          # 사용 가이드
└── public/
    ├── index.html     # 대시보드 HTML
    ├── style.css      # 다크 테마 스타일
    └── app.js         # 클라이언트 로직 (자동 새로고침, 알림)
```

## 실행 방법

### 방법 1: 숨김 배치 파일로 실행 (권장 - GUI 모드)
```bash
# start-hidden.bat 더블클릭
# - 백그라운드에서 서버 시작
# - 자동으로 브라우저에서 대시보드 열림
d:\Data\AI\VSCode\mini-pc-monitor\start-hidden.bat
```

### 방법 2: VBS 파일로 실행
```bash
# run.vbs 더블클릭 또는
wscript d:\Data\AI\VSCode\mini-pc-monitor\run.vbs
```

### 방법 3: 배치 파일로 실행 (CMD 창 표시)
```bash
# start.bat 더블클릭 또는
d:\Data\AI\VSCode\mini-pc-monitor\start.bat
```

### 방법 4: Node.js 로 직접 실행 (개발용)
```bash
# 1. 의존성 설치 (최초 1 회)
cd d:\Data\AI\VSCode\mini-pc-monitor
npm install

# 2. 서버 실행
node server.js

# 3. 브라우저에서 접속
# http://127.0.0.1:4310
```

## 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `MONITOR_PORT` | 4310 | 서버 포트 |
| `MONITOR_INTERVAL_MS` | 60000 | 상태 확인 주기 (ms) - 기본 1 분 |
| `MONITOR_FAILURES` | 3 | 오프라인으로 판단하기 전 실패 횟수 |

### 실행 예시
```bash
# 포트 변경
set MONITOR_PORT=8080 && node server.js

# 30 초마다 검사, 2 회 실패 시 장애
set MONITOR_INTERVAL_MS=30000
set MONITOR_FAILURES=2
node server.js
```

## 주요 기능

- **실시간 상태 모니터링**: Ping 을 통해 각 장비의 응답 상태를 확인
- **장애 알림**: 장비 오프라인 시 브라우저 알림 및 대시보드 경고 표시
- **상태 요약**: 전체, 정상, 장애, 확인 중 장비 수 표시
- **장비 관리**: 장비 추가/수정/삭제, 모니터링 활성화/비활성화
- **자동 검사**: 설정된 주기 (기본 60 초) 로 자동 상태 확인
- **Ping Test**: 각 장비별 "Ping Test" 버튼을 눌러 cmd 창에서 즉시 ping 테스트 실행 (4 회)

## API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| GET | `/api/status` | 현재 모든 장비 상태 조회 |
| PUT | `/api/devices` | 장비 목록 업데이트 |
| POST | `/api/check-now` | 즉시 상태 확인 실행 |
| POST | `/api/ping-test` | 지정 IP 에 대해 cmd 창에서 ping 테스트 실행 (4 회) |

## 기술 스택

- **Backend**: Node.js, Express
- **Frontend**: Vanilla JS, CSS
- **Protocol**: ICMP Ping (Windows `ping.exe`)

## 주의사항

- Windows 환경에서 동작합니다 (ping.exe 사용)
- 로컬호스트 전용 바인딩 (127.0.0.1)
- 관리자 권한 없이 실행 가능
