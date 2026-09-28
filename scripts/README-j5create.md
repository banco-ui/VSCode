# j5Create 자동화 스크립트 사용 가이드

## 📁 스크립트 구성

```
scripts/
├── j5create-to-security.bat    # [무보안 PC] 보안 PC 로 파일 전달
├── j5create-from-security.bat  # [무보안 PC] 보안 PC 로부터 파일 수신
├── j5sync-receive.bat          # [보안 PC] j5Create 에서 파일 수신
├── j5sync-send.bat             # [보안 PC] 작업 결과를 j5Create 로 전송
└── README-j5create.md          # 이 파일
```

---

## 🔧 설치 및 초기 설정

### 1 단계: j5Create 폴더 구조 생성

스크립트를 처음 실행하면 자동으로 생성되지만, 수동으로 만들 수도 있습니다:

```
E:\j5sync\
├── to-security\       # 무보안 PC → 보안 PC 전달용
└── from-security\     # 보안 PC → 무보안 PC 전달용
```

### 2 단계: 보안 PC 스크립트 설정 수정

`j5sync-receive.bat`과 `j5sync-send.bat` 의 작업 디렉토리를 보안 PC 환경에 맞게 수정하세요:

```batch
REM 보안 PC 작업 디렉토리 (실제 경로로 수정)
set WORKSPACE=d:\work\usm-automation
```

### 3 단계: j5Create 드라이브 문자 확인

현재 스크립트는 `E:` 드라이브로 설정되어 있습니다. 실제 j5Create 드라이브 문자로 수정하세요:

```batch
set J5DRIVE=E:   ← 실제 드라이브 문자로 변경
```

---

## 📋 사용 방법

### [무보안 PC] 보안 PC 로 파일 전달하기

```
1. j5Create USB 가 연결되었는지 확인
2. 스크립트 실행: j5create-to-security.bat
3. 자동 복사 완료 메시지 확인
4. j5Create USB 를 보안 PC 에 연결
```

**복사되는 파일:**
- `*.js` - JavaScript 파일
- `*.md` - Markdown 문서
- `*.json` - JSON 설정 파일
- `usm-automation\` - 전체 폴더

---

### [무보안 PC] 보안 PC 로부터 파일 수신하기

```
1. 보안 PC 에서 작업 후 j5Create USB 연결
2. 스크립트 실행: j5create-from-security.bat
3. output\ 폴더에서 결과 파일 확인
```

**수신 위치:**
- `d:\Data\AI\VSCode\output\` 폴더

---

### [보안 PC] j5Create 에서 파일 받기

```
1. j5Create USB 가 연결되었는지 확인
2. 스크립트 실행: j5sync-receive.bat
3. 입력 폴더 (d:\work\usm-automation\j5sync-input\) 에서 파일 확인
4. 작업 폴더로 복사하여 작업 시작
```

---

### [보안 PC] 작업 결과를 j5Create 로 보내기

```
1. 작업 완료 후 결과를 output\ 폴더에 저장
2. 스크립트 실행: j5sync-send.bat
3. 자동 전송 완료 메시지 확인
4. j5Create USB 를 무보안 PC 에 연결
```

**전송 위치:**
- `E:\j5sync\from-security\` 폴더

---

## 🔄 전체 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                     j5Create 파일 흐름                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [무보안 PC]                    [보안 PC]                       │
│  ┌─────────────┐               ┌─────────────┐                 │
│  │ 원본 파일   │               │  작업 결과   │                 │
│  │ usm-automation\ │               │  output\    │                 │
│  └──────┬──────┘               └──────▲──────┘                 │
│         │ 1. to-security.bat          │ 4. send.bat             │
│         ▼                             │                         │
│  ┌─────────────┐               ┌──────┴──────┐                 │
│  │E:\j5sync\   │───── j5Create ─►│E:\j5sync\   │                 │
│  │ to-security\│    USB 이동     │ from-security\│                │
│  └──────┬──────┘               └──────▲──────┘                 │
│         │                             │                         │
│         │ 3. from-security.bat        │ 2. receive.bat          │
│         ▼                             │                         │
│  ┌─────────────┐               ┌──────┴──────┐                 │
│  │ output\     │               │ j5sync-input\│                 │
│  │ (결과 확인) │               │ (작업 시작) │                 │
│  └─────────────┘               └─────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ 주의사항

### 보안 관련
- j5Create USB 분실 시 즉시 보고
- 민감한 정보는 암호화하여 전달
- 사용 후 j5sync 폴더 정리 권장

### 파일 충돌 방지
- 동일한 파일을 양쪽에서 동시 편집하지 않기
- 작업 완료 후 반드시 `from-security` 로 결과 반환
- GitHub 과 병행使用时 충돌 주의

### 드라이브 문자
- j5Create 드라이브 문자는 환경에 따라 다름
- `wmic logicaldisk get deviceid,volumename` 명령으로 확인 가능

---

## 🔍 문제 해결

### Q1. "드라이브를 찾을 수 없습니다"
```
해결: j5Create 가 제대로 연결되었는지 확인
- USB 재연결
- 내 PC 에서 드라이브 문자 확인
- 스크립트의 J5DRIVE 변수 수정
```

### Q2. "액세스가 거부되었습니다"
```
해결: 관리자 권한으로 실행
- 스크립트 우클릭 → "관리자 권한으로 실행"
- 또는 파일 속성 → 차단 해제
```

### Q3. 파일이 복사되지 않음
```
해결: 경로 확인
- 원본 파일이 실제로 있는지 확인
- 경로에 한글/공백이 없는지 확인
- xcopy 대신 robocopy 사용 고려
```

---

## 🛠️ 고급 설정

### robocopy 사용 (대용량 파일)

```batch
REM j5create-to-security.bat 의 xcopy 를 robocopy 로 변경 예시:
robocopy "%WORKSPACE%\usm-automation" "%J5_TO%\usm-automation" /MIR /R:3 /W:5
```

### 자동 백업 추가

```batch
REM 복사 전 백업 생성
set BACKUP_DIR=%WORKSPACE%\backup\%date:~0,4%%date:~5,2%%date:~8,2%
mkdir "%BACKUP_DIR%"
xcopy "%WORKSPACE%\*.js" "%BACKUP_DIR%\" /Y /S
```

### 로그 파일 생성

```batch
REM 스크립트 시작 부분에 추가:
set LOGFILE=%WORKSPACE%\logs\j5sync-%date:~0,4%%date:~5,2%%date:~8,2%.log
echo [%time%] 시작 >> "%LOGFILE%"
```

---

## 📞 지원

문제 발생 시 다음 정보를 확인하세요:

1. j5Create 드라이브 문자
2. Windows 버전
3. 에러 메시지 전체
4. 스크립트 실행 위치
