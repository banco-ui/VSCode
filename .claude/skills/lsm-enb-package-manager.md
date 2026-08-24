# LSM eNB 패키지 적용 자동화 Skill

## 개요
LSM (LTE System Manager) 서버에 패키지(.tar.gz)를 업로드하고, 압축 해제, 권한 변경, 셸 스크립트 실행 및 Tomcat 재시작 등 일련의 설치 절차를 순차적으로 자동화하는 Python Tkinter 데스크톱 애플리케이션입니다.
SSH/SFTP를 통해 원격 장비에 접속하여 대화형 쉘 세션으로 `su` 계정 전환을 수행하며, 패키지 적용 전 과정을 자동화합니다.

## 기술 스택
- **언어**: Python 3
- **GUI**: Tkinter (표준 라이브러리)
- **SSH/SFTP**: paramiko
- **빌드**: PyInstaller (실행 파일 생성용)

## 파일 위치
- **메인 애플리케이션**: `lsm_app.py`
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
python lsm_app.py
```

## GUI 구성
1. **원격 장비 정보**: 장비 IP 주소 입력
2. **패키지 파일**: 로컬 .tar.gz 파일 선택 및 업로드
3. **적용 버전 선택**: `/pkg` 디렉토리 내 패키지 버전 목록 조회 및 선택
4. **패키지 적용**: 전체 설치 절차 자동 실행
5. **진행 상태 및 로그**: 실시간 로그 출력 (ScrolledText)

## 계정 정보
| 계정 | 비밀번호 | 용도 |
|------|----------|------|
| `lsm` | `nmslab123` | SSH/SFTP 접속, 스크립트 실행, EMS 시작 |
| `root` | `root123` | 패키지 이동/압축해제, 권한 변경, nrm 생성 |
| `was` | `was123` | Tomcat 서버 재시작 |

## 패키지 적용 자동화 플로우

### 1. 파일 업로드 (SFTP)
- `lsm` 계정으로 SSH/SFTP 접속
- 로컬 `.tar.gz` 파일을 원격 `/pkg/` 디렉토리에 업로드

### 2. 버전 조회
- `ls -l /pkg | grep '^d'` 실행하여 디렉토리 목록 조회
- 드롭다운 메뉴에서 적용할 버전 선택

### 3. 패키지 적용 (전체 자동화)
적용 확인 다이얼로그 승인 후, 다음 순서로 자동 실행:

| 단계 | 작업 | 계정 | 대기 시간 |
|------|------|------|-----------|
| 1 | 기존 버전 백업 (`mv`) 및 삭제 (`rm -rf`) | lsm | - |
| 2 | `su - root` 전환, 패키지를 `/`로 이동, `tar -xvf` 압축 해제 | root | 2분 |
| 3 | `chmod -R 775`, `chown -R lsm:aceman` 권한 변경 | root | - |
| 4 | `su - lsm` 전환, `fetch_cdd.sh` 실행 | lsm | 2분 |
| 4 | `fetch_nrm.sh` 실행 | lsm | 2분 |
| 4 | `fetch_pmdoc.sh` 실행 | lsm | 1분 |
| 5 | `su - root` 전환, `create_nrm.sh` 실행 (nrm 생성) | root | 2분 |
| 6 | `su - lsm` 전환, `EMS start` 실행 | lsm | 2분 |
| 7 | `su - was` 전환, `tomcat/bin/shutdown.sh` 실행 | was | 2분 |
| 7 | `tomcat/bin/startup.sh` 실행 | was | 1분 |

### 핵심 기술: 대화형 쉘 세션
- `paramiko.SSHClient.invoke_shell()`을 사용하여 인터랙티브 쉘 채널 오픈
- `su - root` 등 비밀번호 입력이 필요한 명령어에 대해 `channel.send()`로 비밀번호 전송
- 각 단계별 지정된 대기 시간만큼 `time.sleep()`으로 블록
- 모든 작업은 백그라운드 스레드(`threading.Thread`)에서 실행하여 GUI 응답성 유지

## 주요 메서드

| 메서드 | 설명 |
|--------|------|
| `connect_ssh(ip, user, password)` | SSH 연결 및 SFTP 세션 오픈 |
| `disconnect_ssh()` | SSH/SFTP 연결 안전 종료 |
| `run_command(command, timeout)` | 단일 SSH 명령 실행 (exec_command) |
| `run_interactive_command(commands)` | 대화형 쉘 세션에서 su 전환 등 실행 |
| `upload_file()` | SFTP 파일 업로드 |
| `fetch_versions()` | `/pkg` 디렉토리 버전 목록 조회 |
| `apply_package()` | 전체 패키지 적용 절차 실행 |
| `log(message)` | 로그 창에 메시지 추가 |

## PyInstaller 빌드 (실행 파일 생성)
```bash
pyinstaller --onefile --windowed --name "LSM_Package_Manager" lsm_app.py
```
- `--onefile`: 단일 실행 파일로 패키징
- `--windowed`: 콘솔 창 없이 GUI만 실행

## 문제 해결

### SSH 연결 실패
- IP 주소 형식 확인 (IPv4 정규식 검증)
- 네트워크 연결 상태 확인
- 방화벽에서 SSH 포트(22) 개방 여부

### 대화형 명령 실패
- `su` 전환 시 비밀번호 입력 타이밍 확인 (1초 대기 후 전송)
- 각 명령어 실행 후 충분한 대기 시간 확보
- 쉘 프롬프트 형식 확인

### 파일 업로드 실패
- `/pkg` 디렉토리 쓰기 권한 확인
- 디스크 여유 공간 확인

## 보안 주의사항
- 비밀번호가 소스 코드에 하드코딩되어 있음 (`lsm: nmslab123`, `root: root123`, `was: was123`)
- 프로덕션 환경에서는 환경 변수 또는 설정 파일로 분리 권장
- SSH 호스트 키 자동 승인 (`AutoAddPolicy`) 사용 중

## 관련 파일
- 메인 스크립트: `lsm_app.py`
- 의존성: `requirements.txt`
- 관련 Skill: `lsm-provisioning.md` (NE/Cell 증설), `lsm-ne-provisioning.md` (NE 증설)
