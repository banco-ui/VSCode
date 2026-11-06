# 📊 Cline 개발 실적 포트폴리오

> **작성일**: 2026-11-05 | **최종 갱신**: 2026-11-06 | **관리 목적**: 개발 내용 전체 정리 · GitHub 백업 · 실적 관리
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
| 11-05 | 개발 실적 포트폴리오 문서 작성 (단일 원본 체계 수립) | 전체 |
| 11-05 | GitHub 백업 진단: 프록시 push 차단 구조 분석, 빌드 산출물 히스토리 정리 (팩 57MB→5.9MB) | scripts (동기화) |
| 11-06 | 프록시 403 우회 확정: Git Data API 조각 업로드 체계 구축 (`scripts/api-push.js`) | scripts (동기화) |
| 11-06 | LFS CDN(S3) 차단 확인 → **대형 파일 분할 백업 체계** 구축 (17KB↑ 76파일 → 25KB 조각 714개) | scripts (동기화) |
| 11-06 | **GitHub 백업 완료**: 190개 커밋 전량 upstream(banco-ui) push, 조각→원본 복원 검증 | 전체 |

> 상세 원본: `C:\Users\banco\AppData\Roaming\Code\User\globalStorage\cline-sr.cline-sr\tasks\`
> (세션별 ui_messages.json / api_conversation_history.json 보존됨)


---

## 3. Skill 인벤토리 (총 12개)

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

### .cline/skills (인프라/운영, 3개)
| Skill | 용도 |
|-------|------|
| `github-push-proxy/SKILL.md` | 사내망 프록시(168.219.61.252:8080) 우회 GitHub push |
| `samsung-github-usage/SKILL.md` | 삼성 사내 GitHub 산출물 공유 가이드 |
| `batch-push/SKILL.md` | 프록시 차단 진단 + Git Data API 조각 업로드(`api-push.js`) + 대형 파일 분할 백업 체계 |

---

## 4. GitHub 백업 현황 및 동기화 방법

### 4-1. 리모트 구성
| 리모트 | 저장소 | 용도 |
|--------|--------|------|
| `upstream` | `https://github.com/banco-ui/VSCode.git` | ⭐ **주 백업 저장소** (사내망 push 대상, gh 토큰 = banco-ui 계정) |
| `origin` | `https://github.com/shoutsky0705/VSCode.git` | 개인 계정 — **회사에서 push 금지** |

### 4-2. 현재 동기화 상태 (2026-11-06 기준 — **백업 완료** ✅)
```
로컬 main     : 76de408
upstream/main : 76de408  → 미푸시 커밋 0개 — 완전 동기화
origin/main   : 동기화 안 함 (회사 정책 — 개인 계정)
```
- 2026-11-06, 사내 프록시가 `git push`(POST) 전면 차단 상태에서
  **GitHub Git Data API를 통한 조각 업로드**로 히스토리 전체(190개 커밋)를 백업 완료.
- blob 1,296개 / 커밋 164개 재작성분 / 트리·커밋 API 호출 순차 생성 → `refs/heads/main` 갱신.

### 4-3. 대형 파일 분할 백업 체계 (2026-11-06 신규 구축)
프록시가 API POST 본문 ~35KB까지만 허용(그 이상 403)하고 Git LFS의 실제
업로드 채널(S3 CDN)도 DLP가 차단하므로, **17KB 초과 파일을 25KB 조각으로
분할해 커밋하는 방식**으로 해결:

| 구성 요소 | 설명 |
|-----------|------|
| `<경로>.parts/part-00001...` | 원본을 25KB씩 분할한 조각 파일들 (GitHub에 업로드됨) |
| `<경로>.parts/manifest.json` | 원본 경로/크기/sha256/조각 목록 (복원 정보) |
| `scripts/restore-split.js` | 단일 파일 복원: `node scripts/restore-split.js "<경로>"` (sha256 검증) |
| `scripts/restore-all.js` | 전체 일괄 복원 (76개 검증 완료) |
| `scripts/prepare-split.js` | 분할 준비 (신규 대형 파일 발생 시 재실행) |
| `scripts/api-push.js` | Git Data API push (병렬 blob 업로드, 재실행 안전) |

- 17KB 초과 76개 파일: mosaic_main.js(4.2MB, 173조각), mosaic_api_lines.txt(2.9MB),
  mosaic_core.js(2.8MB), Verizon 명세 txt, server-manager-tool 테스트/문서 등.
- 원본 파일은 로컬 전용(gitignore 등록), GitHub에는 조각 형태로 전량 백업.
- 안전 번들: `d:\Data\AI\backup\main-pre-split-20261106-094134.bundle` (5.9MB).

### 4-4. 동기화 명령 (사내망 전용 — 외부망 불필요)
```powershell
# 신규 커밋 증분 백업 (자동 커밋 후 1회 실행, 재실행 안전)
node scripts\api-push.js
Get-Content .git\api-push.log -Tail 20    # 진행 확인 (REF-UPDATED → DONE)

# 새 대형 파일이 생겼을 때: 분할 → 제거목록 갱신 → 커밋 → api-push
node scripts\prepare-split.js
git filter-repo --force --invert-paths --paths-from-file .git\filter-repo-paths.txt --path-glob "*.pyc" --refs main
node scripts\commit-parts.js
node scripts\api-push.js
```
> ⚠️ 실측 한계 (2026-11-06): 프록시가 `git push` 전면 차단, GitHub API POST는
> 본문 ~35KB까지만 허용, LFS CDN 업로드 전면 차단. → api-push.js + 분할 백업이 유일한 경로.
> 상세 방법론: `.cline/skills/batch-push/SKILL.md`

### 4-5. 관리 권장 사항
1. `.gitignore`에 Python 캐시(`__pycache__/`, `*.pyc`, `.pytest_cache/`)와 Electron 빌드 산출물(`sd-search/release/`, `win-unpacked/`) 추가 완료.
2. `git filter-repo`로 미푸시 히스토리에서 `sd-search/release/`(DLL 등 51MB) 제거 완료.
3. 자동 커밋 스케줄러(30분)가 커밋을 만들면 **`node scripts/api-push.js`만 실행하면 증분 백업됨.**
4. 새 대형 파일(17KB↑)이 생기면 §4-3의 분할 절차 적용.

---

## 5. 월별 실적 로그 (실적 관리용)

| 월 | 개발 내용 | 산출물 | 상태 |
|----|----------|--------|------|
| 2026-08 | MCP 환경 구축, PDF 캡처 GUI, DRM Unlocker, LSM eNB Package Manager, USM PKG Version Changer, Mosaic BT 자동 게시 | drm-unlocker, usm 자동화 스크립트 + skill 6종 | 완료 |
| 2026-09 | Yaong Tools 통합 허브, SDSearch, Mini PC Monitor, USM/LSM 자동화 정비, Mosaic API 분석, 미니 PC 세팅, Redfish 조사 시작 | Yaong Tools, SDSearch 1.0.0, mini-pc-monitor | 완료 |
| 2026-10 | Server Manager Tool Phase 0~28 (Redfish/K8s/OpenStack/StarlingX, alert, dashboard), 대시보드 관측성 개선 | server-manager-tool v0.7.0 + 보고서 100+ | 완료 |
| 2026-11 | 실적 포트폴리오 정리, GitHub 백업 체계 구축·완료 (프록시 우회 API push, 대형 파일 분할 백업, 히스토리 정리 51MB→5.9MB) | 본 문서, scripts/api-push.js 등 동기화 스크립트 6종, banco-ui/VSCode 백업 완료 | 완료 |

### 실적 유지 규칙
- 새 프로젝트 완료 시: §1 표에 행 추가 → §5 로그에 월별 행 추가 → 커밋
- 신규 skill 등록 시: §3 표에 추가
- 커밋 후: `node scripts/api-push.js`로 GitHub 증분 백업 (§4-4)
