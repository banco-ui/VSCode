# LSM NE & Cell 증설 자동화 정리

## 1. 개요
이 문서는 **usm-automation** 프로젝트 내에서 LSM (Logical Service Manager) **NE(네트워크 장비)와 Cell(셀) 증설** 자동화 기능을 한눈에 파악할 수 있도록 정리한 Markdown 파일입니다.

## 2. 전체 아키텍처
| 구성 요소 | 역할 | 주요 파일/디렉터리 |
|-----------|------|-------------------|
| **Electron UI** | 사용자가 서버·CSV·옵션을 선택하고 실행/결과를 확인 | `dist-electron/index.html`, `dist-electron/assets/index-hYm_5Zj3.js` |
| **IPC (ipcRenderer ↔ ipcMain)** | UI ↔ Node 백엔드 간 메시지 전달 (스크립트 실행, 설정 읽기/쓰기, 로그 전송) | `dist-electron/assets/*.js` 내부 `window.electronAPI` |
| **설정 파일** | LSM 서버 목록·API 인증 정보 보관 | `config/usm-config.json` |
| **CSV 템플릿** | NE·Cell 증설에 필요한 파라미터 정의 | `csv_templates/sample.csv` |
| **스크립트 엔진** | 실제 증설 로직 수행 (`lsm-reprovision.js`, `lsm-cell-provision.js` 등) | 번들된 파일은 `dist-electron/assets/`에 포함 |
| **로그·리포트** | 실행 과정·에러·성공 결과를 파일·화면에 기록 | `logs/`, `output/reports/`, `output/screenshots/` |
| **Mosaic·USM PKG** | 별도 자동화 영역 (본 문서에서는 다루지 않음) | `mosaic_*`, `usm-pkg-upgrade/` |

**핵심 흐름**
1. UI → 서버·CSV·옵션 선택
2. `runScript` IPC 호출 → Node가 `lsm-reprovision.js`(NE) 혹은 `lsm-cell-provision.js`(Cell) 실행
3. 스크립트는 Chrome DevTools Protocol(CDP) 로 LSM GUI에 접속해 UI 자동화 수행
4. 로그는 `logs/`에 기록·IPC 로 UI에 실시간 전송
5. 작업 종료 시 JSON 리포트와 스크린샷을 `output/`에 저장하고 UI에 성공/실패 표시

## 3. 설정 파일 (`config/usm-config.json`)
```json
{
  "servers": [
    {
      "id": "usm-1661234567890",
      "name": "USM 운영 서버",
      "url": "https://10.251.175.31:7443",
      "mcmIp": "10.251.175.31",
      "apiPort": 7443
    }
  ],
  "api": {
    "auth": {
      "username": "ossuser",
      "password": "osspasswd"
    }
  }
}
```
* `url` 은 `https://<IP>:<PORT>` 형태이며 UI에서 선택 시 `--lsm-ip` 옵션에 매핑됩니다.
* 인증 정보는 Electron API `usmApiCall` 내부에서 Basic Auth 헤더로 전달됩니다.

## 4. CSV 템플릿 구조
### 4‑1) NE 증설 (`eNB_*.csv`)
| 컬럼 | 설명 | 예시 |
|------|------|------|
| `NE Name` | 증설할 NE 이름 | `NVGNB_13172` |
| `IP` | NE 관리 IP | `10.10.10.10` |
| `Vendor` | 제조사 | `KDDI` |
| … | 기타 파라미터 | |
> **주의** – 컬럼 순서는 `csv_templates/sample.csv` 와 동일해야 하며, 헤더 라인은 반드시 포함합니다.

### 4‑2) Cell 증설 (`cell_*.csv`)
| 컬럼 | 설명 | 예시 |
|------|------|------|
| `Cell Name` | 셀 식별자 | `CELL_001` |
| `Frequency` | 주파수(Hz) | `3500` |
| `Bandwidth` | 대역폭(MHz) | `20` |
| … | 기타 파라미터 | |

## 5. UI 화면·동작 흐름
| 화면 | 주요 UI 요소 | 동작 설명 |
|------|--------------|-----------|
| **서버 선택** | 드롭다운(서버 리스트) | `config/usm-config.json` 에 정의된 서버를 표시. 선택 시 내부 변수 `selectedServer` 로 저장 |
| **NE 증설** | CSV 파일 드래그·클릭, `+ 서버 추가` 버튼, 실행 버튼 | CSV 선택 → `runScript('lsm-reprovision.js', args)` 호출 |
| **Cell 증설** | NE 이름 입력, CSV 파일 선택, 실행 버튼 | NE 이름·CSV 전달 → `runScript('lsm-cell-provision.js', args)` 호출 |
| **NE 목록 조회** | 조회 버튼, 테이블 | `usmApiCall('/oss/neList')` 로 NE 리스트를 받아 테이블에 렌더링 |
| **실시간 로그** | 로그 창 (스크롤) | `onScriptOutput` 이벤트로 전달된 로그 라인을 실시간 추가 |
| **결과 표시** | 성공/실패 아이콘 + JSON 리포트 | 스크립트 종료 시 `onScriptExited` 로 성공 여부와 리포트 파일 경로 전달 |

## 6. 핵심 스크립트 상세
### 6‑1) `lsm-reprovision.js` (NE 증설)
```bash
node lsm-reprovision.js <csv_file> --lsm-ip <IP> [--create-only|--delete-only|--full|--dry-run]
```
| 옵션 | 의미 |
|------|------|
| `--create-only` | **증설만** 수행 (삭제는 하지 않음) – 기본값 |
| `--delete-only` | **감설만** 수행 |
| `--full` | **감설 → 재증설** 전체 흐름 |
| `--dry-run` | 실제 UI 조작 없이 **시뮬레이션** (로그·리포트만 생성) |
**동작 흐름**
1. CSV 파싱 → NE 객체 배열 생성
2. Chrome CDP 로 `https://<IP>/aceman/` 접속
3. 각 NE에 대해 **Create**(Add NE) 혹은 **Delete**(Remove NE) 수행
4. `console.log` 로 진행 상황 출력 (`[INFO]`, `[WARN]`, `[ERROR]` 등)
5. 작업 종료 시 `output/reports/lsm-reprovision_<NE>_<timestamp>.json` 와 스크린샷(`output/screenshots/reprovision/`) 저장

### 6‑2) `lsm-cell-provision.js` (Cell 증설)
> 실제 파일명은 프로젝트에 포함되지 않았지만 UI(`E` 컴포넌트)에서 호출되는 로직은 아래와 동일합니다.
```bash
node lsm-cell-provision.js <ne_name> <csv_file> --lsm-ip <IP> [--dry-run|--full|--create-only]
```
* 첫 번째 인자로 **NE 이름**을 받으며 해당 NE의 Cell 관리 페이지에 접속
* CSV 파싱 후 **Cell 추가**(Create) 혹은 **Cell 삭제**(Delete) 수행
* `--dry-run` 옵션 시 UI 조작 없이 파싱·리포트만 생성

### 6‑3) `lsm-gui-server.js`
* 로컬 HTTP 서버(포트 7443)를 띄워 브라우저에서도 UI에 접근 가능하게 함
* `scripts/lsm-gui-server.js` 은 `node` 로 실행되며 `dist-electron` 번들 UI와 동일한 기능 제공

## 7. 실행 단계 (사용자 입장에서)
1. **프로젝트 실행**
   ```bash
   npm install   # 필요 시
   npm run start   # Electron UI 실행 (dist-electron)
   ```
2. **서버 선택** – UI 좌측 “USM 서버 선택” 드롭다운에서 대상 LSM 서버 선택 혹은 “+ 서버 추가” 로 새 서버 입력.
3. **NE 증설** – “NE 증설” 탭 → CSV 파일 드래그/찾아보기 → 실행 모드 선택 → “NE 증설 실행” 클릭 → 로그 실시간 표시, 완료 시 리포트·스크린샷 저장.
4. **Cell 증설** – “Cell 증설” 탭 → NE 이름 입력, CSV 선택 → 실행 → 로그·리포트 확인.
5. **NE 목록 조회** – “NE 목록 조회” 탭 → “조회” 클릭 → 현재 LSM에 등록된 NE 리스트가 테이블에 표시.
6. **로그·리포트 확인** – UI 하단 “실행 로그” 창에서 상세 로그 확인, `output/reports/` 에 JSON 리포트, `output/screenshots/` 에 캡처 이미지 저장.

## 8. 로그·리포트 포맷
### 8‑1) 로그 (예시)
```
[2026-08-11T07:00:51.742Z] [LSM-REPROV] [WARN] ⚠️ Start 버튼을 찾지 못함
[2026-08-11T07:00:51.749Z] [LSM-REPROV] [INFO] 리포트 저장: d:\...\lsm-reprovision_eNB_150201_2026-08-11T07-00.json
[2026-08-11T07:00:51.751Z] [LSM-REPROV] [INFO] 브라우저 종료...
```
### 8‑2) 리포트 (JSON) 주요 필드
```json
{
  "neName": "eNB_150201",
  "timestamp": "2026-08-11T07:00:51.749Z",
  "result": "SUCCESS",   // 또는 "FAIL"
  "detail": {
    "created": 3,
    "deleted": 0,
    "errors": []
  },
  "logFile": "lsm-reprovision_eNB_150201_2026-08-11T07-00-51-746Z.json"
}
```
* `detail.errors` 배열에 발생한 에러 메시지가 들어가며, UI에서는 `result` 값에 따라 성공·실패 아이콘을 표시합니다.

## 9. 확장·커스터마이징 포인트
| 영역 | 확장 방법 | 참고 파일 |
|------|-----------|-----------|
| **새 증설 옵션** | `--full`, `--dry-run` 외에 `--force` 등 추가 옵션 구현 | 번들된 `lsm-reprovision.js` |
| **CSV 컬럼** | 템플릿에 새로운 컬럼 추가 → 파싱 로직(`csv-parse` 사용) 수정 | `csv_templates/` + 스크립트 파싱 부분 |
| **UI 디자인** | React 컴포넌트(`E`, `S`, `E` 등) 수정 → 색상·레이아웃 변경 | `dist-electron/assets/index-hYm_5Zj3.js` |
| **로그 저장 위치** | `logs/` 경로를 환경 변수(`LSM_LOG_DIR`) 로 지정 | `lsm-reprovision.js` 내부 `PATHS.logDir` |
| **보고서 포맷** | JSON → CSV·Excel 변환 로직 추가 (Node `xlsx` 라이브러리) | `output/reports/` 생성 부분 |
| **다중 서버 동시 실행** | UI에서 서버 체크박스 다중 선택 → `Promise.all` 로 병렬 실행 | `E` 컴포넌트 `runScript` 호출 부분 |

---
### 📌 마무리
- **NE·Cell 증설 자동화**는 **Electron UI → IPC → Node 스크립트 → Chrome CDP** 로 구성된 파이프라인이며, CSV 기반 입력·옵션 선택·실시간 로그·JSON 리포트까지 전 과정을 자동화합니다.
- UI에서 **서버·CSV·옵션**만 올바르게 지정하면 별도 코드 수정 없이도 증설·감설·시뮬레이션을 수행할 수 있습니다.
- 필요에 따라 **스크립트 옵션·CSV 컬럼·UI 레이아웃**을 자유롭게 확장·커스터마이징 할 수 있도록 설계돼 있습니다.

> 이 파일은 `usm-automation/LSM_NE_Cell_Provisioning.md` 로 저장되었습니다.
