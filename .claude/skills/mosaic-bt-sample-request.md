
## 개요
Mosaic 포털(mosaic.sec.samsung.net)의 TELCO DATA CENTER 워크스페이스에 있는 "BT 시료 셋업 요청" 게시판에 게시글을 자동 등록하는 스크립트입니다.
CDP(Chrome DevTools Protocol)를 활용하여 Chrome 브라우저를 제어합니다.

## 대상 워크스페이스 정보
- **워크스페이스명**: TELCO DATA CENTER
- **comtyId**: 6654005
- **게시판명**: BT 시료 셋업 요청
- **menuId**: 1767722146
- **게시판 URL**: https://mosaic.sec.samsung.net/collaboration/workspace/6654005/list/1767722146

## 스크립트 위치
- **게시물 복사 등록**: `scripts/mosaic-cdp-copy-v3.js` (소스 게시물 내용을 복사하여 신규 등록)
- **신규 게시글 등록**: `scripts/mosaic-cdp-fvt-post.js` (제목/본문 직접 입력하여 등록)
- **API 분석**: `scripts/mosaic-cdp-lnb-boards.js` (워크스페이스 메뉴/권한 분석)
- **게시물 전체 추출**: `scripts/mosaic-cdp-extract-all.js` (페이지네이션으로 전체 게시물 추출, 상세 API에서 content 포함)
- **Excel 변환**: `scripts/mosaic-transform-excel.js` (JSON → 5개 시트 Excel, 참조 Excel 서식 적용)
- **BT 시료요청 GUI**: `scripts/mosaic-bt-gui-server.js` (Express + WebSocket 기반 GUI 서버)


## 사전 준비

### 1. Chrome CDP 모드 실행
```bash
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\mosaic-cdp-profile" --no-first-run --no-default-browser-check --disable-extensions https://mosaic.sec.samsung.net
```

### 2. Mosaic 로그인
Chrome 브라우저에서 Mosaic 포털에 수동 로그인합니다. (SSO 인증 필요)

### 3. CDP 연결 확인
```bash
curl -s http://127.0.0.1:9222/json/version
```

## 사용법

### 게시물 복사 등록 (소스 게시물 내용을 새 글로 등록)
```bash
# 소스 게시물(postId=5001827782)의 내용을 복사하여 신규 등록
node scripts/mosaic-cdp-copy-v3.js
```

### 스크립트 수정하여 다른 게시물 복사
`scripts/mosaic-cdp-copy-v3.js` 파일에서 다음 변수를 수정:
```javascript
const COMTY_ID = '6654005';        // 워크스페이스 ID
const MENU_ID = '1767722146';      // 게시판 메뉴 ID
const SOURCE_POST_ID = '5001827782'; // 복사할 소스 게시물 ID
```

## 핵심 API

### 1. 게시물 조회 API
```
GET /api/v1/workspace/gnr/gnr-bulletin-board/get-bbs-post?comtyId={comtyId}&menuId={menuId}&postId={postId}&isAnm=false&topCtgId=&subCtgId=
```
- **응답 필드**:
  - `postTtl`: 게시물 제목
  - `postCntnt`: 게시물 본문 HTML

### 2. 게시물 등록 API
```
POST /api/v1/workspace/gnr/gnr-bulletin-board/save-bbs-post?comtyId={comtyId}&menuId={menuId}
```
- **요청 Payload**:
```json
{
  "menuId": "1767722146",
  "comtyId": "6654005",
  "prntPostId": 0,
  "hideNm": "",
  "postTtl": "제목",
  "postMtxtCntnt": "<div id=\"cafe-note-contents\" ...>본문 HTML</div>",
  "postLvl": 0,
  "mode": "CREATE",
  "ctgId": "",
  "openYn": "Y",
  "filePreviewYn": "N",
  "postCommentYn": "Y",
  "emlRplyYn": "Y",
  "prntCtgId": "",
  "keywordList": [],
  "tagList": [],
  "fileGroupId": null,
  "thmbImgId": null,
  "isAiKeyowrd": true,
  "isPostCuEdt": false,
  "videoSignatures": [],
  "postChatbotYn": "N",
  "menuAutoMailType": "",
  "modifySendMailYn": "",
  "anmYn": "N"
}
```
- **응답**: 게시물 ID (숫자)

### 3. 사용자 역할 확인 API
```
GET /api/v1/workspace/home/user-role/{comtyId}
```
- **역할 값**: FLU(정회원), GST(손님), ADM(운영진)
- 쓰기 권한: FLU 이상 필요

### 4. LNB 메뉴 목록 API
```
GET /api/v1/workspace/home/menu/lnb-list/{comtyId}
```

## UI 자동화 기술

### 제목 입력
```javascript
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(input, titleText);
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
```

### 본문 입력 (iframe 기반 에디터)
```javascript
const iframes = document.querySelectorAll('iframe');
for (let i = 0; i < iframes.length; i++) {
    const doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
    const body = doc.body;
    if (body) {
        body.innerHTML = contentHTML;
        body.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        body.dispatchEvent(new Event('input', { bubbles: true }));
    }
}
```

### 1차 분류 선택 (있는 경우)
```javascript
const dd = document.querySelector('[msg-select="1차 분류"]');
dd.querySelector('.ur-dropdown__title').dispatchEvent(new MouseEvent('click', { bubbles: true }));
// 드롭다운 아이템 선택
const items = document.querySelectorAll('.ur-dropdown__item');
items[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
```

## 권한 요구사항
- **TELCO DATA CENTER** (comtyId: 6654005): 쓰기 권한 필요
- 사용자 역할이 FLU(정회원) 이상이어야 게시글 등록 가능
- GST(손님) 권한으로는 등록 불가 (에러: COL_COM_0003 "권한이 없습니다")

## 문제 해결

### 본문 입력 실패 시
- iframe 기반 에디터가 로드될 때까지 충분한 대기 시간 필요 (15초 이상)
- `contentEditable` 속성 확인 후 입력
- iframe body에 `innerHTML` 설정 후 `keyup`, `input` 이벤트 dispatch

### 권한 에러 (COL_COM_0003)
- 워크스페이스 관리자에게 정회원 권한 요청
- `user-role` API로 현재 권한 확인 가능

### SPA 로딩 이슈
- Mosaic은 SPA이므로 페이지 이동 후 충분한 대기 시간 필요 (15-20초)
- `Page.navigate` 후 `sleep(15000)` 권장

## 게시물 추출 및 Excel 변환

### 게시물 목록 API
```
GET /api/v1/workspace/gnr/gnr-bulletin-board/list-general-bulletin-board-post?comtyId={comtyId}&menuId={menuId}&postIds=&sortCond=1&isFav=false&isDetail=false&searchCondTopCategory=&searchCondSubCategory=&menuPostType=LIST&menuContentViewYn=N&searchDateType=5&searchStartDate=&searchEndDate=&searchResolve=&isSearch=false&isBlogOpen=false&isExcel=false&blogIsAdmin=false&page={page}&size=100&topCtgId=&subCtgId=&oderby=desc
```
- **응답 필드**:
  - `postId`: 게시물 ID
  - `postTtl`: 제목
  - `fstRegUserNm`: 작성자 이름
  - `fstRegDtm`: 등록일시 (예: 2026-08-19)
  - `fstRegDeptName`: 부서명
  - `postCntnt`: 본문 HTML (목록 API에는 없고 상세 API에만 있음)

### 페이지네이션 주의사항
- `size=100`으로 설정해도 실제로는 103개씩 반환됨
- page 0~5까지 조회하여 전체 수집 필요 (누락 방지)
- 8/19일 게시물의 경우 총 83개 (page 0~1에 걸쳐 있음)

### 게시물 분류 로직
- **원본 요청 (main)**: BT Member가 작성하지 않은 게시물
- **제외 (excluded)**: BT Member가 작성했거나 제목이 다음 접두어로 시작:
  - `준비완료`, `RE]`, `연장확인`, `반납확인`, `할당불가`, `반납]`
- **BT Members**: 김대목, 노민식, 강윤식, 강남욱, 김상웅, 지동환, 배정호, 송명준

### Excel 변환 (5개 시트)
1. **요약**: 월별 요청 건수, 조회 기간 (파란색/초록색/연두색 헤더)
2. **2026년 8월**: 원본 요청 게시물 (제목, 등록자, 부서명, 등록일, 답변여부, 구분, 사업자, PKG Version 등)
3. **시료 요청자**: 등록자별 요청 건수
4. **제외게시글**: BT Member 응답 게시물 (담당자, 응답일시, 셋업일정, 할당현황, 할당시료No, 할당시료IP, 할당일정, 반납확인, 정상유무확인, 비고 — 본문 HTML 테이블에서 자동 추출)
5. **시료 대응 현황**: Member별 대응 통계

### 제외게시글 본문 테이블 파싱
BT Member 응답 게시물의 본문에 포함된 HTML 테이블에서 다음 헤더를 찾아 데이터 추출:
```
No. | 담당자 | 응답 일시 | 셋업일정 | 할당현황 | 할당시료 No | 할당 시료 IP | 할당 일정 | 반납 확인 | 정상유무 확인 | 비고
```

## BT 시료요청 GUI

### GUI 구조 (MyEasyTools 참조)
- **상단 패널**: 조회 기간 (달력 2개), 제목 제외 키워드, BT Center 담당자 목록
- **중간 패널**: 게시물 목록 테이블 (번호, 제목, 등록자, 진행상황, 등록일)
- **하단 패널**: 콘솔 로그 (실행 시간, 게시물 수, 저장 경로)
- **버튼**: 시작, 제외된 항목 보기, 모자익 화면 보기 체크박스

### GUI 실행
```bash
node scripts/mosaic-bt-gui-server.js
# http://localhost:3110 접속
```


