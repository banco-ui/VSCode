
## 개요
DRM(Digital Rights Management) 이 적용된 문서 (DOCX, DOC, PDF, MHT 등) 를 읽고 텍스트 내용을 추출하는 스킬입니다. USM/LSM NE 자동화 작업 시 "KDDI gNB EMS-OSS Interface 사양서"와 같은 DRM 문서를 분석할 때 사용합니다.

**핵심 기능:**
- 화면 캡처 후 **자동으로 텍스트 추출**
- 캡처된 내용을 **메모리에 저장하여 즉시 반환**
- Vision AI 를 사용한 고정밀 텍스트 인식

---

## 주요 도구

### 1. `extract_text_with_word_com` (추천 - 최적의 방법)
**Word COM 객체**를 사용하여 DRM 문서에서 직접 텍스트를 추출합니다. **가장 확실하고 빠른 방법**입니다.

**사용 예시:**
```json
{
  "name": "extract_text_with_word_com",
  "arguments": {
    "documentPath": "d:\\Data\\AI\\VSCode\\usm-automation\\3) wrcp 설치 - 25.09-v10-20260814_162058.docx"
  }
}
```

**파라미터:**
| 이름 | 타입 | 설명 | 필수 |
|------|------|------|------|
| `documentPath` | string | 텍스트를 추출할 DOCX/DOC/MHT 파일 경로 | 필수 |
| `outputFile` | string | 출력 파일명 (선택, 기본값: 문서명-word-com.txt) | 선택 |

**특징:**
- ✅ **가장 확실한 방법** - Word 가 설치되어 있으면 항상 작동
- ✅ **DRM 직접 해제** - Word COM 이 DRM 을 자동으로 해제
- ✅ **빠른 처리** - 38,837 자 문서를 30 초 내에 완료
- ✅ **백그라운드 실행** - Word 창을 조작하지 않음
- ✅ **정확한 텍스트** - 원본 텍스트 그대로 추출
- ⚠️ **Word 필요** - MS Word 가 설치되어 있어야 함
- ⚠️ **Windows 전용** - Windows 환경에서만 작동

**반환 내용:**
- 추출된 텍스트: `output/text/{문서명}-word-com.txt`
- 문서 내용 미리보기 (2000 자)
- 총 텍스트 길이

**실제 성능:**
```
문서: 3) wrcp 설치 - 25.09-v10-20260814_162058.docx
텍스트 길이: 38,837 자
처리 시간: 약 30 초
```

---

### 2. `read_drm_document` (화면 캡처 방식)
DRM 문서를 캡처하고 **텍스트 내용을 즉시 반환**합니다.

**사용 예시 (MCP 도구 호출):**
```json
{
  "name": "read_drm_document",
  "arguments": {
    "windowTitle": "vDU deploy",
    "startPage": 1,
    "endPage": 30,
    "returnSummary": false
  }
}
```

**파라미터:**
| 이름 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `windowTitle` | string | 캡처할 창 제목 (Word 문서 등) | 선택 |
| `startPage` | number | 캡처 시작 페이지 | 1 |
| `endPage` | number | 캡처 종료 페이지 | 30 |
| `returnSummary` | boolean | true: 요약본, false: 전체 텍스트 | false |

**반환 내용:**
- 캡처된 스크린샷: `output/screenshots/`
- 추출된 텍스트: `output/text/merged-document.txt`
- **문서 내용 전체 (또는 요약본) 를 텍스트로 반환**

---

### 3. `capture_screen`
화면을 캡처하고 자동으로 텍스트를 추출합니다.

**사용 예시:**
```json
{
  "name": "capture_screen",
  "arguments": {
    "windowTitle": "문서명",
    "extractText": true
  }
}
```

**파라미터:**
| 이름 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `windowTitle` | string | 캡처할 창 제목 (일부만 입력) | 선택 |
| `startPage` | number | 캡처 시작 페이지 | 1 |
| `endPage` | number | 캡처 종료 페이지 | 30 |
| `scrollDelay` | number | 스크롤 후 대기 시간 (ms) | 1500 |
| `extractText` | boolean | 캡처 후 자동 텍스트 추출 | true |

---

### 4. `capture_drm_document`
Chrome CDP 를 사용하여 DRM 문서를 직접 캡처합니다.

**사용 예시:**
```json
{
  "name": "capture_drm_document",
  "arguments": {
    "documentPath": "C:\\Docs\\file.pdf",
    "cdpPort": "9222",
    "startPage": 1,
    "endPage": 30
  }
}
```

---

### 5. `extract_text_from_images`
캡처된 이미지에서 OCR 로 텍스트를 추출합니다.

---

### 6. `get_capture_status`
캡처 상태 및 결과를 확인합니다.

---

### 7. `launch_chrome_debug`
Chrome 을 디버깅 모드로 실행합니다.

---

## 사용 흐름

```
┌─────────────────────────────────────────────────────────┐
│  1. read_drm_document 호출                              │
│     - windowTitle: "문서명"                             │
│     - returnSummary: false (전체 텍스트)                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  2. 자동 수행 (내부)                                    │
│     - 화면 캡처 (drm-screen-capture.js)                 │
│     - Vision AI 텍스트 추출 (drm-vision-analyze.js)     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  3. 결과 반환                                           │
│     - 문서 내용 전체 텍스트                             │
│     - 스크린샷: output/screenshots/                     │
│     - 텍스트: output/text/merged-document.txt           │
└─────────────────────────────────────────────────────────┘
```

---

## 원리

### 화면 캡처 + Vision AI 방식
1. **화면 캡처**: Word 문서를 PageDown 키로 넘기며 캡처
2. **Vision AI 분석**: 캡처된 이미지를 Vision AI 로 텍스트 추출
3. **텍스트 병합**: 모든 페이지의 텍스트를 하나의 파일로 병합
4. **메모리 반환**: 추출된 텍스트를 MCP 응답으로 반환

### Chrome CDP 방식
- Chrome 이 DRM 문서를 렌더링할 때 **DOM 에 텍스트를 표시**함
- CDP(Chrome DevTools Protocol) 로 DOM 에 접근하여 텍스트 추출
- DRM 은 복사/인쇄를 막지만, 화면 표시는 막을 수 없음

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `drm-unlocker/scripts/drm-skill.js` | MCP 스킬 서버 |
| `drm-unlocker/scripts/drm-screen-capture.js` | 화면 캡처 |
| `drm-unlocker/scripts/drm-vision-analyze.js` | Vision AI 텍스트 추출 |
| `drm-unlocker/scripts/drm-capture.js` | Chrome CDP 캡처 |
| `drm-unlocker/scripts/drm-extract-text.js` | OCR 텍스트 추출 |
| `drm-unlocker/scripts/drm-word-com.js` | Word COM 텍스트 추출 |
| `drm-unlocker/scripts/zip-results.js` | ZIP 파일 생성 |
| `drm-unlocker/.mcp.json` | MCP 서버 설정 |

---

## 출력 디렉토리

```
drm-unlocker/output/
├── screenshots/     # 캡처된 페이지 이미지 (PNG)
├── text/            # 추출된 텍스트 (TXT)
│   └── merged-document.txt  # 병합된 전체 문서
└── drm-*.json       # 작업 결과 요약
```
