# SDSearch - Samsung Doc Search

> Mosaic, Confluence, axhub 3개 사내 문서 플랫폼 통합 검색 툴

## 📋 개요

SDSearch는 삼성 사내 문서 플랫폼인 Mosaic, Confluence, axhub를 통합 검색하는 CLI 도구입니다. 
각 플랫폼의 API 또는 웹 스크래핑을 통해 검색 결과를 수집하고, 랭킹을 매겨 통합 출력합니다.

## 🏗️ 아키텍처

```
sd-search/
├── index.js                 # CLI 메인
├── package.json
├── config/
│   └── search-config.json   # 플랫폼별 설정
├── adapters/
│   ├── mosaic-adapter.js     # Mosaic API (axios + 쿠키)
│   ├── confluence-adapter.js # Confluence REST API
│   └── axhub-adapter.js     # axhub (Playwright CDP)
└── core/
    ├── searcher.js          # 통합 검색 엔진
    ├── formatter.js         # 결과 포맷터 (table/json/markdown)
    └── cache.js             # 검색 결과 캐시
```

## 🚀 설치

```bash
cd sd-search
npm install
```

## 📖 사용법

### 통합 검색
```bash
# 모든 플랫폼에서 검색
node index.js search "GitHub"

# 특정 플랫폼만 검색
node index.js search "USM" --platform mosaic,confluence

# JSON 형식 출력
node index.js search "자동화" --format json

# Markdown 형식 출력
node index.js search "자동화" --format markdown

# 최대 결과 수 지정
node index.js search "5G" --max 30
```

### 상세 조회
```bash
# 특정 문서 상세 내용
node index.js detail mosaic <workspace-id>
node index.js detail confluence <page-id>
node index.js detail axhub POST00008055 --board AICrewActivityBoard
```

### 통계
```bash
# 플랫폼별 검색 결과 건수
node index.js stats "5G"
```

### 캐시 관리
```bash
# 캐시 삭제
node index.js cache clear
```

## 🔧 플랫폼별 인증

### Mosaic
- `config/mosaic-session.json`에 쿠키 저장
- API 실패 시 기존 캐시 파일에서 검색 (fallback)

### Confluence
- `config/confluence-session.json`에 쿠키/토큰 저장
- REST API (CQL) 사용

### axhub
- Chrome CDP (포트 9222) 연결
- SSO 세션으로 인증 (별도 로그인 불필요)
- CDP 연결 실패 시 기존 캐시에서 검색

## 📊 검색 결과 랭킹

검색 결과는 다음 기준으로 랭킹됩니다:
- 제목 매칭: +1.0점
- 내용 매칭: +0.5점
- 실시간 결과 (캐시 아님): +0.3점
- 플랫폼 기본 점수: Mosaic(0.7), Confluence(0.8), axhub(0.7)

## 🔗 Yaong Tools 통합 (예정)

이 도구는 향후 Yaong Tools 통합 툴에 포함될 예정입니다.
