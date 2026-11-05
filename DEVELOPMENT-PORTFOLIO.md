# 📊 Cline 개발 실적 포트폴리오

> **작성일**: 2026-11-05 | **관리 목적**: 개발 내용 전체 정리 · GitHub 백업 · 실적 관리
> **기간**: 2026-08-12 ~ 현재 (Cline SR 활용)
> 이 문서는 개발 실적의 "단일 원본(Single Source of Truth)"입니다. 새 작업을 마칠 때마다
> 「월별 실적 로그」 섹션에 한 줄을 추가하고 커밋하면 실적이 자동 축적됩니다.

---

## 1. 개발 프로젝트 요약 (총 7개)

| # | 프로젝트 | 위치 | 기술 스택 | 산출물 |
|---|---------|------|----------|--------|
| 1 | **Yaong Tools** (통합 자동화 허브) | 루트 (`electron/`, `scripts/`) | Electron + Vite + Node.js | `Yaong Tools.exe` 설치 빌드 |
| 2 | **USM 자동화 스위트** | `usm-automation/` | Node.js, CDP, REST API | NE/Cell 증설 스크립트, LSM 설치 자동화, `USM-PKG-Upgrade.exe` |
| 3 | **SDSearch** (Samsung Doc Search) | `sd-search/` | Node.js, Playwright, Express | `SDSearch Setup 1.0.0.exe` |
| 4 | **DRM Unlocker** | `drm-unlocker/` | Node.js, CDP | DRM 문서 텍스트 추출 GUI |
| 5 | **Mini PC Monitor** | `mini-pc-monitor/` | Node.js, Express | LAN 미니 PC 상태 대시보드 |
| 6 | **Server Manager Tool** | `server-manager-tool/` | Python (Phase 0~28, v0.7.0) | Redfish/K8s/OpenStack 서버 인벤토리 관리, Phase 보고서 다수 |
| 7 | **워크스페이스 자동화 스크립트** | `scripts/` | Batch/PowerShell/Node.js | git 자동 커밋 스케줄러, 하이브리드 동기화, 대화 백업 |

### 1-1. Yaong Tools — 통합 자동화 허브
- 개별 자동화 스크립트들을 하나의 데스크톱 툴로 통합한 메인 애플리케이션.
- `npm run electron:build` → 설치형 exe / `electron:build:portable` → 포터블 exe.
- 내장 기능: USM NE 증설 실행(`auto`), 미니 PC 모니터(`monitor`), 대화 백업(`backup` + Windows 스케줄러 등록).

### 1-2. USM 자동화 스위트 (이동통신 NE 운영 자동화)
- **USM NE 증설**: CSV 템플릿 → USM REST API(10.251.209.131:7443) 전송으로 NE 자동 증설
- **USM Cell 증설**: NE 증설 후 Cell 자동 증설
- **LSM NE/eNB/Cell 증설**: JIO/KDDI 사업자 환경 LSM(CognitiV) 자동화
- **LSM eNB 패키지 적용**: SSH/SFTP 접속 + `su` 전환 + tar.gz 설치 + Tomcat 재시작 전 과정 자동화
- **USM PKG Version Changer**: 원격 서버 `.tar.gz` 내 r-버전 폴더명 변경 (2단계 확인/실행 로직)
- **USM PKG Upgrade**: `usm-automation/usm-pkg-upgrade/dist/USM-PKG-Upgrade.exe` (실행 파일 산출물)
- **Mosaic BT 시료 셋업 요청**: Mosaic 포털 게시판 CDP 기반 자동 게시
- 산출 리포트: `usm-automation/output/reports/*.json` (lsm-reprovision, ne-provisioning 실행 기록)

### 1-3. SDSearch
- Mosaic · Confluence · AX HUB 3개 사내 포털 **통합 검색** 툴 (adapters 구조).
- GUI(Express) + CLI 모두 지원, Electron 설치 빌드 완료(`sd-search/release/`).

### 1-4. DRM Unlocker
- DRM 적용 문서(DOCX/DOC/PDF/MHT)를 브라우저에서 열어 캡처 → 텍스트화 → DRM 제한 없는 형태로 저장.
- CDP(Chrome DevTools Protocol) 기반 자동화, GUI 포함.

### 1-5. Mini PC Monitor
- 로컬 네트워크 미니 PC(Windows 10) 실시간 온라인/오프라인 상태 대시보드.
- 미니 PC 원격 제어 세팅 작업(2026-09-16)에서 파생.

### 1-6. Server Manager Tool (가장 최근 주력, 2026-09-17~10-15)
- Dell PowerEdge R750 iDRAC **Redfish API** 기반 읽기 전용 하드웨어/상태 조사에서 출발.
- v0.7.0, Phase 0~28 단계적 개발: 인벤토리 → collectors → normalizers → alert/rules →
  dashboard → scheduler → Kubernetes/OpenStack/StarlingX 멀티 프로바이더 → 모니터링/그래프.
- 테스트 44개, Phase별 설계/검증 보고서 100+ 건 (`server-manager-tool/output/`).
- 최근 커밋: "Management Dashboard readiness, monitoring, and observation fix" (2026-10-15).

---

## 2. Cline 작업 히스토리 (27개 세션, 2026-08-12 ~ 09-17)

| 날짜 | 주제 | 프로젝트 |
|------|------|---------|
| 08-12 | MCP 설치 확인 및 유용한 MCP 조사 | 환경 설정 |
| 08-12 | PDF 캡처 자동화 GUI 디버깅/완성 (포트 3200) | usm-automation |
| 08-14 | YouTube 쇼츠 제작 지원 | 기타 |
| 08-18 | 매일 밤 11시 대화 기록 자동 저장 cron 설정 | scripts (백업 자동화) |
| 08-19 | DRM 문서 풀기 프로젝트 설계 + skill 등록 | drm-unlocker |
| 08-19 | USM 자동화 세션 문제 진단 | usm-automation |
| 08-21 | Gemini 개발분 이관: LSM eNB Package Manager 데스크톱앱 | usm-automation |
| 08-24 | Gemini 개발분 이관: USM PKG Version Changer v2 | usm-automation |
| 08-24 | GitHub 연동 확인 | 환경 설정 |
| 08-26 | Mosaic BT 시료 신청 게시판 읽기/쓰기 자동화 | usm-automation |
| 08-26 | 워크스페이스 분리 전략 상담 | 환경 설정 |
| 08-27 | /usm-pkg-upgrade 스킬 실행 | usm-automation |
| 09-07 | Yaong Tools를 24시간 서버(ProLiant e910t) 서비스형으로 전환 검토 | Yaong Tools |
| 09-09 | 지금까지 만든 기능/자동화를 하나의 툴로 통합 방안 → Yaong Tools 기획 | Yaong Tools |
| 09-10 | Mosaic 포털 API 분석 및 연동 | usm-automation |
| 09-14 | GitHub MCP / Honcho MCP / Confluence 내용 txt 저장 확인 | 환경 설정 |
| 09-15 | USM NE 증설/감설 자동화 전략 정립 (2 세션) | usm-automation |
| 09-15 | Cline vs Cline SR 차이 비교 | 기타 |
| 09-16 | 미니 PC(Windows 10) 리모트 컨트롤 세팅 | mini-pc-monitor |
| 09-16 | Mosaic workspace AI 읽기/쓰기 권한 탐색 (CDP 미사용) | usm-automation |
| 09-16 | 집에서 무료 모델 한계 → 회사 Cline SR 원격 사용 방안 | 환경 설정 |
| 09-17 | Dell R750 iDRAC Redfish API 하드웨어 조사 → server-manager-tool 시작 | server-manager-tool |

> 상세 원본: `C:\Users\banco\AppData\Roaming\Code\User\globalStorage\cline-sr.cline-sr\tasks\`
> (세션별 ui_messages.json / api_conversation_history.json 보존됨)


---

## 3. Skill 인벤토리 (총 11개)

### .claude/skills (프로젝트 자동화, 9개)
| Skill | 용도 |
|-------|------|
| `ne-provisioning.md` | USM REST API로 NE 증설 (CSV 템플릿) |
| `cell-provisioning.md` | USM Cell 증설 (NE 선행 필요) |
| `lsm-provisioning.md` | LSM LTE/eNodeB NE+Cell 증설 (JIO 환경) |
| `lsm-ne-provisioning.md` | LSM(CognitiV) CSV 프로파일 업로드 및 eNB 증설 |
| `lsm-enb-package-manager.md` | LSM eNB 패키지 업로드/설치/Tomcat 재시작 자동화 |
| `usm-pkg-version-changer.md` | USM 패키지 r-버전 폴더명 변경 (2단계 확인/실행) |
| `mosaic-bt-sample-request.md` | Mosaic BT 시료 셋업 요청 게시판 자동 등록 (CDP) |
| `drm-document-reader.md` | DRM 문서 텍스트 추출 |
| `mini-pc-monitor.md` | 미니 PC 상태 모니터링 대시보드 |

### .cline/skills (인프라/운영, 2개)
| Skill | 용도 |
|-------|------|
| `github-push-proxy/SKILL.md` | 사내망 프록시(168.219.61.252:8080) 우회 GitHub push |
| `samsung-github-usage/SKILL.md` | 삼성 사내 GitHub 산출물 공유 가이드 |

---

## 4. GitHub 백업 현황 및 동기화 방법

### 4-1. 리모트 구성
| 리모트 | 저장소 | 용도 |
|--------|--------|------|
| `origin` | `https://github.com/shoutsky0705/VSCode.git` | 내 백업 저장소 |
| `upstream` | `https://github.com/banco-ui/VSCode.git` | 연계 GitHub (동기 대상) |

### 4-2. 현재 동기화 상태 (2026-11-05 기준)
```
로컬 main    : 최신 (2026-10-15 커밋까지)
origin/main  : 로컬보다 185 커밋 뒤쳐짐  → PUSH 필요
upstream/main: 로컬보다 186 커밋 뒤쳐짐 → PUSH 필요
전송 팩 크기  : 57MB → 5.9MB (Electron 빌드 산출물 히스토리 제거 완료)
```
- 백업을 위해서는 **로컬 → origin, upstream 양쪽 모두 push**가 필요합니다.
- 자동 커밋 스케줄러(`scripts/git-auto-commit.ps1` + `setup-git-auto-scheduler.ps1`)가 30분 간격 로컬 커밋은 유지 중.

### 4-3. 동기화 명령
```powershell
cd d:\Data\AI\VSCode     # 반드시 저장소로 이동 후 실행
git push origin main     # 내 GitHub 백업 (shoutsky0705)
git push upstream main   # 연계 GitHub 동기화 (banco-ui)
```
> ⚠️ 2026-11-05 진단: 사내 프록시가 GitHub **push(POST) 전체를 차단** 중.
> 1커밋·유효 토큰·소형 팩(5.9MB) 모두 403. fetch(읽기)는 정상.
> **외부망(테더링/집 네트워크)에서 위 명령 실행이 유일한 확실한 방법.**
> 참고: gh CLI 로그인 계정은 banco-ui이므로, origin(shoutsky0705) push 시
> 외부망에서 자격 증명 프롬프트가 뜨면 개인 계정으로 로그인할 것.

### 4-4. 관리 권장 사항
1. `.gitignore`에 Python 캐시(`__pycache__/`, `*.pyc`, `.pytest_cache/`)와 Electron 빌드 산출물(`sd-search/release/`, `win-unpacked/`) 추가 완료.
2. `git filter-repo`로 미푸시 186개 커밋에서 `sd-search/release/`(DLL 등 51MB) 히스토리 제거 완료 — 이제 push 팩이 5.9MB에 불과.
3. 사내 프록시로 push가 403이면 외부망에서 실행 (본 섹션 참조).

---

## 5. 월별 실적 로그 (실적 관리용)

| 월 | 개발 내용 | 산출물 | 상태 |
|----|----------|--------|------|
| 2026-08 | MCP 환경 구축, PDF 캡처 GUI, DRM Unlocker, LSM eNB Package Manager, USM PKG Version Changer, Mosaic BT 자동 게시 | drm-unlocker, usm 자동화 스크립트 + skill 6종 | 완료 |
| 2026-09 | Yaong Tools 통합 허브, SDSearch, Mini PC Monitor, USM/LSM 자동화 정비, Mosaic API 분석, 미니 PC 세팅, Redfish 조사 시작 | Yaong Tools, SDSearch 1.0.0, mini-pc-monitor | 완료 |
| 2026-10 | Server Manager Tool Phase 0~28 (Redfish/K8s/OpenStack/StarlingX, alert, dashboard), 대시보드 관측성 개선 | server-manager-tool v0.7.0 + 보고서 100+ | 진행 |
| 2026-11 | 개발 실적 포트폴리오 정리, GitHub 백업/동기화 | 본 문서 | 진행 |

### 실적 유지 규칙
- 새 프로젝트 완료 시: §1 표에 행 추가 → §5 로그에 월별 행 추가 → 커밋
- 신규 skill 등록 시: §3 표에 추가
- 매월 1회: §4-2 동기화 상태 갱신 + `git push origin main && git push upstream main`
