# DRM 문서 풀기 (DRM Document Reader)

## 개요
DRM 이 적용된 Office 문서 (Word, Excel, PowerPoint) 와 PDF 문서의 DRM 을 해제하고 텍스트/이미지를 추출하는 스킬입니다.

---

## 처리 방식 (2 가지)

### 1️⃣ 빠른 텍스트 추출 (Fast)
**텍스트만 빠르게 추출**

- **출력**: `output/drm-ungrouped/{문서명}_fast.txt`
- **처리 시간**: 30 초 ~ 2 분
- **장점**: 빠름, 간단한 텍스트 분석에 적합
- **단점**: 이미지/표 포함 안됨

### 2️⃣ 완전 분석 (Full)
**텍스트 + 그림/표를 HTML 로 통합 저장**

- **출력**: `output/drm-ungrouped/{문서명}_full/`
  - `{문서명}_full-text.txt` (텍스트)
  - `{문서명}_full.html` (HTML + 이미지)
- **처리 시간**: 2 ~ 5 분
- **장점**: 원본 레이아웃 유지, 웹 브라우저에서 바로 보기 가능
- **단점**: 파일 크기 큼, 처리 시간 김

---

## 사용 방법

### GUI 사용 (권장)
```bash
cd d:\Data\AI\VSCode\drm-unlocker
node drm-gui.js
```
브라우저에서 http://localhost:3456 접속

### 명령줄 사용
```bash
# 빠른 텍스트 추출
node scripts/drm-ungroup.js "D:\path\to\document.docx" word fast

# 완전 분석
node scripts/drm-ungroup.js "D:\path\to\document.docx" word full

# Excel 문서
node scripts/drm-ungroup.js "D:\path\to\spreadsheet.xlsx" excel fast

# PowerPoint 문서
node scripts/drm-ungroup.js "D:\path\to\presentation.pptx" ppt full

# PDF 문서
node scripts/drm-ungroup.js "D:\path\to\document.pdf" pdf fast
```

---

## 지원 문서

| 종류 | 확장자 | 빠른 추출 | 완전 분석 |
|------|--------|----------|-----------|
| Word | .docx, .doc, .mht | ✅ | ✅ |
| Excel | .xlsx, .xls, .csv | ✅ | ✅ |
| PowerPoint | .pptx, .ppt | ✅ | ✅ |
| PDF | .pdf | ✅ | ✅ |

---

## 출력 예시

### 빠른 텍스트 추출
```
output/drm-ungrouped/
└── 문서이름_fast.txt
```

### 완전 분석
```
output/drm-ungrouped/
└── 문서이름_full/
    ├── 문서이름_full-text.txt
    └── 문서이름_full.html
```