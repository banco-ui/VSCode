# 🚀 USM NE 증설 자동화 — AI 기반 솔루션

> **당신만의 AI 자동화 방식**  
> Claude Code + devtools MCP를 사용한 GUI 자동화  
> 반복적인 NE 증설 작업을 AI가 자동으로 수행합니다.

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Version](https://img.shields.io/badge/Version-v1.0-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Automation](https://img.shields.io/badge/Automation-AI-red)

---

## 📋 개요

### 문제
- 📌 반복적인 USM GUI 작업 (증설/감설/관리)
- 📌 수동 클릭과 파라미터 입력의 번거로움
- 📌 배치 작업 시 시간 소요

### 해결책
- ✅ **devtools MCP**: Chrome 자동화 (GUI 조작)
- ✅ **Claude Code**: AI 에이전트 (작업 오케스트레이션)
- ✅ **Python/Node.js**: 스크립트 실행 (로직 구현)

### 결과
- 🎯 정형화된 절차를 **자동으로 반복** 실행
- 🎯 각 단계에서 **사용자 확인** (Human-in-the-loop)
- 🎯 상세한 **로그 및 리포트** 생성
- 🎯 당신만의 **커스텀 자동화**

---

## ⚡ 빠른 시작 (5분)

### 1. 환경 준비

```bash
# VS Code 확장 확인
# - Claude Code (Anthropic 공식)
# - devtools MCP (chrome-devtools 활성화)

# USM 로그인 (브라우저에서)
# Chrome → https://your-usm-server.com → 로그인
```

### 2. CSV 파일 준비

`csv_templates/plan.csv` 생성:

```csv
target_usm,ne_type,template_name,param_1,param_2,pkg
USM-TEST-01,gNB-LSM,LSM_기본증설,VALUE1,VALUE2,pkg_A
USM-TEST-01,gNB-LSM,LSM_기본증설,VALUE1,VALUE2,pkg_A
```

### 3. 자동화 시작

**VS Code에서:**

```
Claude Code와 대화:

"csv_templates/plan.csv를 읽어서 NE를 증설해줘.
 각 단계마다 나한테 물어보고 go/stop 대기해."
```

**또는 커맨드라인:**

```bash
node scripts/usm-ne-provisioning.js csv_templates/plan.csv
```

### 4. 결과 확인

```
output/
├── screenshots/  ← 각 단계 스크린샷
└── reports/      ← 최종 결과 (JSON)

logs/
└── provisioning.log  ← 상세 로그
```

---

## 📁 디렉토리 구조

```
usm-automation/
│
├── scripts/                          # 자동화 스크립트
│   ├── usm-ne-provisioning.js       # 핵심 오케스트레이션
│   ├── login.js                      # 로그인 로직 (선택)
│   └── utils.js                      # 유틸리티 함수
│
├── config/                           # 설정 파일
│   ├── usm-config.json              # USM 서버/템플릿 설정
│   └── credentials.json             # 인증 정보 (선택)
│
├── csv_templates/                    # CSV 입력 파일
│   ├── sample.csv                   # 샘플
│   └── plan.csv                     # 실제 작업 파일
│
├── logs/                             # 실행 로그
│   └── provisioning.log             # 작업 로그
│
├── output/                           # 실행 결과
│   ├── screenshots/                 # 단계별 스크린샷
│   └── reports/                     # 최종 리포트 (JSON)
│
├── .vscode/                          # VS Code 설정
│   ├── settings.json                # 에디터 설정
│   ├── tasks.json                   # 작업 정의
│   └── extensions.json              # 권장 확장
│
├── .claude/                          # Claude Code 설정
│   └── settings.json                # AI 자동화 설정
│
├── AUTOMATION_GUIDE.md              # 📖 상세 사용 가이드
├── README.md                         # 이 파일
├── USM_NE_자동화_플레이북.md        # AI 프롬프트 플레이북
└── 회사_VSCODE_DEVTOOLS_셋업가이드.md # 초기 셋업

```

---

## 🎯 사용 시나리오

### 시나리오 1: 단일 NE 증설

```
1. CSV에 1행 입력
2. Claude Code: "CSV 읽고 증설해줘"
3. AI: 각 단계 진행 + 확인 대기
4. 당신: "go" 입력 → 실행
5. 결과 확인
```

### 시나리오 2: 배치 증설 (여러 NE)

```
1. CSV에 10행 입력
2. Claude Code: "배치 증설 시작"
3. AI: 행 1 처리 → 확인 대기
   당신: "go" 또는 "skip"
   AI: 행 2, 3, ... 반복
4. 모든 행 완료 → 리포트
```

### 시나리오 3: 수동 단계별 제어

```
Claude Code:
"지금 USM 탭에서:
1. NE 관리 → 증설 메뉴 클릭
2. 템플릿 'LSM_기본증설' 선택
3. CELL_ID 필드에 'CELL_001' 입력
4. 증설 시작 버튼 클릭
5. 스크린샷 찍어줘"
```

---

## 🛠️ devtools MCP 명령어

당신이 Claude Code를 통해 사용할 수 있는 **Chrome 자동화 명령어**:

| 명령 | 기능 | 예시 |
|------|------|------|
| `new_page` | 새 탭 열기 | `https://usm-server.com` |
| `navigate_page` | 페이지 이동 | 증설 페이지로 이동 |
| `type_text` | 텍스트 입력 | 로그인 ID/PW |
| `click` | 버튼 클릭 | "증설 시작" 버튼 |
| `fill_form` | 폼 작성 | 여러 필드 한번에 |
| `wait_for` | 요소 대기 | 로딩 완료 대기 |
| `take_screenshot` | 스크린샷 | 결과 저장 |
| `handle_dialog` | 대화상자 처리 | 확인/취소 |
| `list_network_requests` | 네트워크 모니터링 | API 호출 추적 |
| `list_console_messages` | 콘솔 에러 | 에러 로그 수집 |

더 자세한 내용: [AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md#-devtools-mcp-활용)

---

## ⚙️ 설정

### 1. Claude Code 설정 (`.claude/settings.json`)

```json
{
  "model": "claude-opus-5",
  "permissions": {
    "mcp_tools": [
      "mcp__chrome-devtools__*"
    ]
  }
}
```

### 2. USM 서버 설정 (`config/usm-config.json`)

```json
{
  "servers": [
    {
      "id": "usm-test",
      "url": "https://your-usm-test.com",
      "environment": "testing"
    }
  ]
}
```

### 3. DOM 셀렉터 커스터마이징

실제 USM 화면에 맞게 수정:

```json
{
  "selectors": {
    "templateDropdown": "select[name='template']",
    "startButton": "button.provisioning-start",
    "confirmButton": "button.provisioning-confirm"
  }
}
```

더 자세한 내용: [AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md#-설정-커스터마이징)

---

## 📊 결과 예시

### 로그 출력

```
[2026-08-10T09:30:00Z] [INFO] === 자동화 시작 ===
[2026-08-10T09:30:01Z] [INFO] CSV 읽기 성공: 3행
[2026-08-10T09:30:05Z] [INFO] 행 1 - 증설 메뉴로 이동
[2026-08-10T09:30:08Z] [INFO] 행 1 - 템플릿 불러오기: LSM_기본증설
[2026-08-10T09:30:12Z] [INFO] 행 1 - ★ 확인 대기 중
[2026-08-10T09:30:15Z] [INFO] 행 1 - 확인 버튼 클릭
[2026-08-10T09:30:45Z] [INFO] 행 1 - ✅ 완료
```

### 최종 리포트 (JSON)

```json
{
  "totalRows": 3,
  "success": 2,
  "error": 0,
  "skipped": 1,
  "timestamp": "2026-08-10T09:31:00Z",
  "results": [
    { "status": "success", "rowNumber": 1 },
    { "status": "skipped", "rowNumber": 2 },
    { "status": "success", "rowNumber": 3 }
  ]
}
```

---

## ⚠️ 중요: Human-in-the-loop 원칙

```
🔐 안전장치: 자동화는 "증설 확인" 버튼 직전에서 멈춥니다

당신이 명시적으로 "실행" 또는 "go"를 입력해야만
실제 NE 증설이 실행됩니다.

❌ AI가 자동으로 확인 버튼을 누르지 않습니다
❌ 이는 네트워크 변경 방지를 위한 안전장치입니다

✅ 각 행마다 당신의 승인을 받고 진행합니다
✅ 이상 감지 시 즉시 "stop" 또는 "skip" 입력 가능
```

---

## 🚀 VS Code 작업 (단축키)

```
Ctrl+Shift+P → "작업 실행" 후 선택:

1. "USM NE 증설 자동화 실행 (대화형)"
   ↳ 각 단계마다 확인 요청

2. "USM NE 증설 자동화 (자동 확인)"
   ↳ 모든 단계 자동 실행 (⚠️ 주의!)

3. "최근 로그 보기"
   ↳ 마지막 50줄 로그

4. "최근 리포트 보기"
   ↳ 최신 결과 JSON

5. "스크린샷 디렉토리 열기"
   ↳ 단계별 스크린샷 폴더
```

---

## 🐛 문제 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| devtools MCP 못 찾음 | MCP 비활성화 | `.vscode/mcp.json` 확인 |
| 요소 못 찾음 | 셀렉터 오류 | `config/usm-config.json` 수정 |
| 로딩 계속됨 | 타임아웃 | `provisioning.timeouts` 증가 |
| CSV 읽기 오류 | 파일 인코딩/경로 | UTF-8 인코딩 + 상대경로 |
| 권한 부족 | 설정 미구성 | `.claude/settings.json` 권한 확인 |

더 자세한 내용: [AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md#-트러블슈팅)

---

## 📚 관련 문서

| 문서 | 내용 |
|------|------|
| [AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md) | 📖 상세 사용 가이드 (꼭 읽기!) |
| [USM_NE_자동화_플레이북.md](./USM_NE_자동화_플레이북.md) | 💬 AI 프롬프트 플레이북 |
| [회사_VSCODE_DEVTOOLS_셋업가이드.md](./회사_VSCODE_DEVTOOLS_셋업가이드.md) | 🔧 초기 셋업 |

---

## 🎓 학습 흐름

```
1️⃣ README.md 읽기
   ↓
2️⃣ AUTOMATION_GUIDE.md 읽기 (상세 가이드)
   ↓
3️⃣ csv_templates/sample.csv 확인
   ↓
4️⃣ Claude Code와 대화 시작
   "CSV 읽고 증설해줘"
   ↓
5️⃣ 첫 번째 행 "go" 클릭
   ↓
6️⃣ 결과 확인 (screenshots/ + reports/)
   ↓
7️⃣ 반복 및 커스터마이징
```

---

## 🔑 핵심 개념

### devtools MCP (Chrome DevTools Protocol via MCP)
- VS Code에서 **직접 Chrome을 조작**
- GUI 기반 작업을 **프로그래밍 방식**으로 자동화
- **보안**: 브라우저의 보안 모델 준수

### Human-in-the-loop
- 반복 작업 중 **위험한 단계에서 멈춤**
- 사용자의 **명시적 승인** 필요
- 네트워크 변경 **오류 방지**

### AI 오케스트레이션
- Claude Code가 **작업 흐름 조율**
- 각 단계마다 **상황 판단**
- 에러 발생 시 **즉시 보고**

---

## 💡 다음 단계

### 이미 준비된 것
- ✅ 기본 자동화 스크립트
- ✅ VS Code 작업 통합
- ✅ 로깅 및 리포팅
- ✅ 설정 템플릿

### 당신이 해야 할 것
- [ ] 실제 USM URL 및 셀렉터 확인
- [ ] `config/usm-config.json` 업데이트
- [ ] 첫 CSV 파일 작성
- [ ] Claude Code와 첫 대화
- [ ] 결과 검증 및 개선

### 선택사항 (향후)
- [ ] Python 버전 구현
- [ ] API 기반 자동화 (GUI 대신)
- [ ] 감설 자동화 추가
- [ ] 스케줄 자동화

---

## 📞 지원

- 🤝 **Claude Code와 대화**: 직접 질문하며 스크립트 수정
- 📖 **문서**: AUTOMATION_GUIDE.md에서 상세 답변
- 🔍 **로그**: `logs/provisioning.log` 에서 상세 정보
- 📸 **스크린샷**: `output/screenshots/` 에서 각 단계 확인

---

## 📝 라이선스

개인 사용 (Samsung 내부)

---

## 🎉 Summary

```
당신만의 AI 기반 USM 자동화 시스템이 준비되었습니다!

1️⃣ CSV 파일 준비
2️⃣ Claude Code 실행
3️⃣ 각 단계 확인 (go/skip)
4️⃣ 자동으로 NE 증설
5️⃣ 로그 및 리포트 확인

시작하려면:
"csv_templates/plan.csv를 읽어서 NE를 증설해줘.
 각 단계마다 나한테 물어봐."

Happy Automation! 🚀
```

---

**Last Updated**: 2026-08-10  
**Version**: v1.0  
**Status**: Active ✅
