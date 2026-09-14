# SDSearch - Samsung Doc Search

삼성 사내 문서 검색 도구 (Mosaic, Confluence, AX HUB 통합 검색)

## 기능

### 🔍 통합 검색
- Mosaic, Confluence, AX HUB를 한 번에 검색
- 랭킹 알고리즘으로 관련도 순 정렬

### 🟦 Mosaic 검색
- Mosaic 통합검색 API (itg-search) 사용
- 카테고리 필터 (Workspace, Board, M Cast, Mind Map 등)
- **게시글 추출**: 검색 결과 각 항목에서 "📥 추출" 버튼 클릭 시 본문 내용 추출
  - 가입한 Workspace: CDP로 API 응답을 가로채서 전체 내용 추출
  - 미가입 Workspace: 검색 API의 미리보기(~959자)만 추출 가능
- 출력 형식: TXT, Markdown, JSON 지원
- 클립보드 복사 및 파일 저장 기능

### 🟩 Confluence 검색
- Confluence REST API (CQL) 기반 검색
- Chrome CDP를 통해 로그인된 브라우저의 쿠키 자동 추출
- confluence-nw.sec.samsung.net 대상

### 🟧 AX HUB 검색
- Playwright CDP를 통한 OutSystems SPA 스크래핑
- 검색 입력창에 키워드 입력 후 결과 파싱
- 각 행을 클릭하여 게시글 ID(POST000XXXXX) 추출
- 정확한 게시글 URL 생성

## 아키텍처

```
sd-search/
├── config/
│   └── search-config.json      # 플랫폼별 설정
├── adapters/
│   ├── mosaic-adapter.js        # Mosaic API 어댑터
│   ├── confluence-adapter.js    # Confluence REST API 어댑터
│   └── axhub-adapter.js         # AX HUB CDP 스크래핑 어댑터
├── core/
│   ├── searcher.js              # 통합 검색 엔진
│   ├── cache.js                 # 캐시 관리
│   └── formatter.js             # 출력 포맷터
├── gui/
│   ├── server.js                # Express 웹 서버 (포트 3120)
│   └── public/
│       ├── index.html           # 메인 UI
│       ├── app.js               # 프론트엔드 JavaScript
│       └── style.css            # 스타일시트
├── package.json
└── README.md
```

## 사전 요구사항

1. **Chrome 브라우저** (CDP 포트 9222로 실행)
   ```bash
   chrome.exe --remote-debugging-port=9222
   ```
2. **Node.js 18+**
3. Chrome에서 Mosaic, Confluence, AX HUB에 로그인되어 있어야 함

## 설치 및 실행

```bash
# 의존성 설치
cd sd-search
npm install

# 서버 실행
node gui/server.js

# 브라우저 접속
# http://localhost:3120
```

## EXE 빌드

```bash
# pkg 또는 nexe를 사용한 EXE 빌드
npm run build:exe
```

## 기술 스택

- **백엔드**: Node.js, Express
- **프론트엔드**: Vanilla JavaScript, HTML/CSS
- **브라우저 자동화**: Playwright (CDP 연결)
- **HTTP 클라이언트**: Axios
- **검색 API**: Mosaic itg-search, Confluence CQL, AX HUB SPA 스크래핑

## 주의사항

- Chrome이 `--remote-debugging-port=9222`로 실행되어야 CDP 기능이 작동합니다
- 사내 네트워크(VPN) 연결이 필요합니다
- TLS 인증서 검증을 비활성화하므로 사내 환경에서만 사용하세요
