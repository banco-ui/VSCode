# LSM NE 증설 자동화 Skill

## 개요
LSM (CognitiV) 서버에 접속하여 CSV 프로파일을 업로드하고 eNB를 자동 증설하는 스크립트입니다.

## 사전 준비
- Chrome 브라우저 설치 (`C:\Program Files\Google\Chrome\Application\chrome.exe`)
- Node.js 및 Playwright 설치
- `config/lsm-config.json`에 LSM 계정 정보 설정
- 증설할 NE의 CSV 프로파일 파일 준비

## 사용법

### 기본 명령어
```bash
node scripts/lsm-reprovision.js <csv_file> [--lsm-ip <IP>] [--dry-run] [--delete-only] [--create-only]
```

### 옵션
| 옵션 | 설명 |
|------|------|
| `<csv_file>` | 증설할 NE의 CSV 프로파일 파일 경로 (필수) |
| `--lsm-ip <IP>` | LSM 서버 IP 주소 (기본값: config의 첫 번째 서버) |
| `--dry-run` | 시뮬레이션 모드 (실제 작업 수행 안 함) |
| `--delete-only` | 감설만 수행 |
| `--create-only` | 증설만 수행 (감설 생략) |

### 사용 예시
```bash
# 특정 LSM 서버에 eNB 증설
node scripts/lsm-reprovision.js eNB_150201_26B.csv --lsm-ip 10.251.175.31 --create-only

# 다른 LSM 서버에 eNB 증설
node scripts/lsm-reprovision.js eNB_150202_26B.csv --lsm-ip 10.251.175.32 --create-only

# 감설만 수행
node scripts/lsm-reprovision.js eNB_150201_26B.csv --lsm-ip 10.251.175.31 --delete-only

# 시뮬레이션 (실제 작업 없음)
node scripts/lsm-reprovision.js eNB_150201_26B.csv --lsm-ip 10.251.175.31 --dry-run
```

## 자동화 플로우

### 증설 전체 순서 (약 1분 30초 소요)
1. **Chrome 브라우저 시작** (Playwright 제어)
2. **LSM 로그인**
   - SSO 체크박스 해제
   - ID/PW 입력
   - 중복 세션 "예" 클릭
   - 메인 페이지 로드 대기
3. **구성관리 → eNB 생성 메뉴 이동**
4. **점세개(⋮) 아이콘 클릭** → 드롭다운 메뉴 열기
5. **"Profile 가져오기" 메뉴 클릭** → Profile Import 다이얼로그 열기
6. **"조회" 버튼 클릭** → 프로파일 목록 조회
7. **CSV 파일 선택** → `#cm_profile_import_csvfileselector` 파일 입력
8. **"적용" 버튼 클릭** → CSV 에러 체크 (JavaScript로 직접 클릭)
9. **"가져오기" 버튼 클릭** → **eNB 증설 실행** (JavaScript로 직접 클릭)
10. **30초 증설 진행바 대기**
11. **"닫기" 버튼 클릭** → 완료
12. **브라우저 종료**

### 핵심 포인트
- **"가져오기" 버튼 = 증설 버튼**: "Submit" 버튼이 아님. "가져오기"를 클릭해야 실제 증설이 실행됨
- **"적용" / "가져오기" 버튼은 메인 페이지에 있음**: 다이얼로그 내부가 아님. JavaScript `page.evaluate()`로 직접 클릭
- **STEP2 / Submit / Create 이벤트 대기 불필요**: 가져오기 버튼 클릭 후 30초 대기 → 닫기 → 종료

## CSV 프로파일 형식
```
@SysInfo##ID,Type,Version,ProfileName,NeName,SerialNo,RelVersion,ShelfID,InterConnectionMode
150201,eNB,26.B.0,eNB_150201_26B,eNB_150201_26B,S615261317,r-01,1,CSCU
@CELL_INF##CELL_ID,PHY_CELL_ID,BAND_CLASS,BANDWIDTH,...
...
```

## 스크린샷
모든 단계별 스크린샷이 `output/screenshots/reprovision/`에 저장됩니다:
- `01-login-*.png`: 로그인 과정
- `06-create-enb-page.png`: eNB 생성 페이지
- `06a-option-clicked.png`: 점세개 메뉴
- `06b-profile-import.png`: Profile 가져오기 다이얼로그
- `06c-search-result.png`: 조회 결과
- `06d-applied.png`: 적용 후
- `06e-imported.png`: 증설 완료
- `06f-closed.png`: 닫기 후

## 리포트
실행 완료 후 JSON 리포트가 `output/reports/`에 저장됩니다:
- 파일명: `lsm-reprovision_<NE_NAME>_<timestamp>.json`
- 내용: 실행 시간, CSV 파일 경로, LSM IP, NE 정보, 결과

## 문제 해결

### "적용" 버튼이 클릭되지 않는 경우
- 버튼이 메인 페이지에 있으므로 JavaScript `page.evaluate()`로 직접 클릭
- `button:has-text("적용")` 셀렉터가 다른 숨겨진 버튼을 찾을 수 있음
- `offsetParent !== null`로 보이는 버튼만 필터링

### "가져오기" 버튼이 비활성화인 경우
- CSV 파일에 에러가 있는 경우 "가져오기" 버튼이 비활성화됨
- CSV 파일 형식을 확인하고 "적용" 버튼을 다시 클릭

### 로그인 실패
- `config/lsm-config.json`의 계정 정보 확인
- SSO 체크박스가 해제되었는지 확인
- 중복 세션 다이얼로그에서 "예" 클릭

## 관련 파일
- 스크립트: `scripts/lsm-reprovision.js`
- 설정: `config/lsm-config.json`
- CSV 템플릿: `csv_templates/lsm_enb_profile_sample.csv`
- 스크린샷: `output/screenshots/reprovision/`
- 리포트: `output/reports/`
- 로그: `logs/lsm-reprovision.log`
