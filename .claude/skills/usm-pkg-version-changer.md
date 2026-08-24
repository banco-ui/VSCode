# USM PKG 버전명 변경 Skill

## 개요
USM (Universal Session Manager) 장비의 원격 서버에 있는 `.tar.gz` 패키지 파일을 임시 폴더에 압축 풀고, 내부의 `r-버전` (예: r-0130) 폴더 이름을 사용자가 원하는 새 버전(예: r-0140)으로 변경한 뒤 다시 압축해 주는 Python Tkinter 기반의 UI 툴입니다.
안전한 작업을 위해 **[1단계] 확인(준비)**과 **[2단계] 실행**이 명확히 분리된 2단계 로직이 핵심입니다.

## 기술 스택
- **언어**: Python 3
- **GUI**: Tkinter (표준 라이브러리)
- **SSH**: paramiko
- **빌드**: PyInstaller (실행 파일 생성용)

## 파일 위치
- **메인 애플리케이션**: `usm_app_v2.py`
- **의존성**: `requirements.txt`

## 의존성 설치
```bash
pip install -r requirements.txt
```
또는
```bash
pip install paramiko pyinstaller
```

## 실행 방법
```bash
python usm_app_v2.py
```

## GUI 구성
1. **원격 장비 정보**: USM MCMA 장비 IP 주소 입력
2. **패키지 선택**: `/log/swm/nepkgmgr` 경로의 `.tar.gz` 패키지 목록 조회 및 선택
3. **버전 변경**: 현재 버전 확인 + 변경할 버전명 입력
4. **실행**: 패키지 버전 변경 실행
5. **진행 상태 및 로그**: 실시간 로그 출력 (ScrolledText)

## 계정 정보
| 계정 | 비밀번호 | 용도 |
|------|----------|------|
| `vsm` | `nmslab123` | SSH 접속, 패키지 조작 (이동/압축해제/재압축) |

## 핵심 경로
| 경로 | 설명 |
|------|------|
| `/log/swm/nepkgmgr` | 패키지 원본 디렉토리 (base_dir) |
| `/log/swm/nepkgmgr/tmp` | 임시 작업 디렉토리 (tmp_dir) |
| `/log/swm/nepkgmgr/tmp/pkg` | 압축 해제 후 패키지 내부 경로 |

## 2단계 분리 로직 (핵심)

### [1단계] 현재 버전명 확인 (`prepare_and_check_version`)
1. `tmp` 디렉토리 생성 (`rm -rf tmp; mkdir -p tmp`)
2. 원본 패키지를 `tmp`로 이동 (`mv`)
3. 패키지 압축 해제 (`tar -zxvf`)
4. `find` 명령으로 내부 `r-*` 폴더 찾기 → 현재 버전 UI 표시
5. 작업 일시 정지 (`is_prepared = True`)

### [2단계] 패키지 버전 변경 (`apply_version_change`)
1. `is_prepared == True` 상태에서만 실행 가능
2. 현재 버전 폴더를 새 버전명으로 이름 변경 (`mv`)
3. 새 이름으로 재압축: `(새버전명)_(원본패키지명).tar.gz` (`tar -zcvf`)
4. 결과물을 원본 경로로 이동 (`mv`)
5. `tmp` 폴더 삭제 (`rm -rf`)
6. 패키지 목록 자동 새로고침

### 버전명 규칙
- 형식: `r-숫자` (예: `r-0130`, `r-0140`)
- 정규식 검증: `^r-\d+$`
- 새 패키지명 생성: `r-` 접두사 제거 후 원본 패키지명 앞에 붙임
  - 예: `r-0140` + `USM_PKG.tar.gz` → `0140_USM_PKG.tar.gz`

## 주요 메서드

| 메서드 | 설명 |
|--------|------|
| `fetch_packages()` | `/log/swm/nepkgmgr`에서 `.tar.gz` 패키지 목록 조회 |
| `prepare_and_check_version()` | 1단계: 압축 해제 및 현재 버전 확인 |
| `apply_version_change()` | 2단계: 버전명 변경 및 재압축 |
| `_validate_and_connect(ip)` | IP 유효성 검사 + SSH 연결 |
| `_connect(ip, user, password)` | paramiko SSH 연결 |
| `_disconnect()` | SSH 연결 종료 |
| `_run_command(command, timeout)` | 원격 명령 실행 (exec_command) |
| `log(message)` | 로그 창에 메시지 추가 |

## 작업 플로우

```
[시작]
  │
  ├─ 패키지 확인 (fetch_packages)
  │    └─ ls -1 /log/swm/nepkgmgr/*.tar.gz
  │
  ├─ [1단계] 현재 버전명 확인 (prepare_and_check_version)
  │    ├─ rm -rf tmp; mkdir -p tmp
  │    ├─ mv {패키지} tmp/
  │    ├─ tar -zxvf {패키지} -C tmp/
  │    ├─ find tmp/pkg -type d -name 'r-*'
  │    └─ ⏸ 일시정지 (is_prepared = True)
  │
  ├─ [2단계] 패키지 버전 변경 (apply_version_change)
  │    ├─ find tmp/pkg -type d -name '{현재버전}'
  │    ├─ mv {현재버전} {새버전}
  │    ├─ cd tmp && tar -zcvf {새버전}_{원본패키지명} pkg
  │    ├─ mv {새패키지} /log/swm/nepkgmgr/
  │    ├─ rm -rf tmp
  │    └─ 패키지 목록 새로고침
  │
[완료]
```

## PyInstaller 빌드 (실행 파일 생성)
```bash
pyinstaller --onefile --windowed --name "USM_PKG_Version_Changer" usm_app_v2.py
```
- `--onefile`: 단일 실행 파일로 패키징
- `--windowed`: 콘솔 창 없이 GUI만 실행

## 문제 해결

### SSH 연결 실패
- IP 주소 형식 확인 (IPv4 정규식 검증)
- 네트워크 연결 상태 확인
- 방화벽에서 SSH 포트(22) 개방 여부

### 패키지 압축 해제 실패
- 디스크 여유 공간 확인
- 패키지 파일 무결성 확인
- `tar` 명령어 타임아웃 증가 (기본 120초)

### r-버전 디렉토리를 찾지 못함
- 패키지 내부 구조 확인 (`pkg/r-*` 경로)
- `find` 명령어 경로 확인

### 재압축 실패
- 디스크 여유 공간 확인
- `tar` 명령어 타임아웃 증가 (기본 180초)

## 보안 주의사항
- ⚠️ 비밀번호가 소스 코드에 하드코딩되어 있음 (`vsm: nmslab123`)
- ⚠️ SSH 호스트 키 자동 승인 (`AutoAddPolicy`) 사용 중
- 프로덕션 환경에서는 환경 변수 또는 설정 파일로 분리 권장

## 관련 파일
- 메인 스크립트: `usm_app_v2.py`
- 의존성: `requirements.txt`
- Yaong Tools 통합 가이드: `output/USM_PKG_버전변경_YaongTools_통합가이드.md`
