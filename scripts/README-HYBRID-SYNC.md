# Hybrid Sync (GitHub + j5Create)

## 개요

코드/설정은 **GitHub**으로, 대용량 파일은 **j5Create**로 전달하는 하이브리드 방식입니다.

---

## 스크립트 목록

| 파일 | 용도 | 사용 PC |
|------|------|---------|
| `hybrid-sync.bat` | GitHub 상태 확인 + 대용량 파일 검색 | 무보안 PC (집) |
| `hybrid-receive.bat` | j5Create 파일 수신 + GitHub 동기화 | 보안 PC (회사) |

---

## 사용 방법

### 무보안 PC (집)

```batch
cd d:\Data\AI\VSCode\scripts
.\hybrid-sync.bat
```

**실행 결과:**
1. GitHub 변경사항 확인
2. 10MB 이상 대용량 파일 검색
3. j5Create 에 수동 복사할 파일 목록 표시

**다음 단계:**
- 표시된 파일들을 `E:\j5sync\to-security\` 에 수동 복사

---

### 보안 PC (회사)

```batch
REM hybrid-receive.bat 의 WORKSPACE 를 실제 경로로 수정
set WORKSPACE=d:\work\usm-automation

.\hybrid-receive.bat
```

**실행 결과:**
1. j5Create 에서 파일 자동 수신 (`j5-input\` 폴더)
2. GitHub 상태 확인
3. `output\` 폴더의 결과를 j5Create 로 전송

---

## 보안 PC 설정 (필수!)

`hybrid-receive.bat` 파일을 보안 PC 에 복사한 후, 다음을 수정하세요:

```batch
REM 14 줄: 보안 PC 의 실제 작업 경로로 변경
set WORKSPACE=d:\work\usm-automation
```

---

## 전체 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hybrid Sync Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [무보안 PC]                    [보안 PC]                       │
│  ┌─────────────┐               ┌─────────────┐                 │
│  │hybrid-sync  │               │hybrid-receive│                 │
│  └──────┬──────┘               └──────▲──────┘                 │
│         │                             │                         │
│         │ 1. GitHub push              │ 1. j5Create 수신        │
│         │    (코드/설정)              │    (대용량)             │
│         │                             │                         │
│         │ 2. j5Create 수동복사 ──────►│ 2. Cline SR 작업        │
│         │    (대용량)                 │                         │
│         │                             │ 3. j5Create 전송 ──────►│
│         │◄────────────────────────────│    (결과물)             │
│         │                             │                         │
│         │ 4. 결과 확인                │ 4. output\ 정리         │
│         │    output\ 폴더             │                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 파일 분류 기준

| 파일 타입 | 크기 | 동기화 방법 |
|-----------|------|-------------|
| 소스 코드 (*.js, *.py, *.ts) | Any | GitHub |
| 설정 (*.json, *.md) | Any | GitHub |
| 빌드 결과물 (*.exe, *.dll) | Any | j5Create |
| 모델 파일 (*.bin, *.onnx) | Any | j5Create |
| 데이터 (*.csv) | <10MB | GitHub |
| 데이터 (*.csv) | >10MB | j5Create |

---

## 문제 해결

### Q: "Not a Git repository" 에러

```
해결:
cd d:\Data\AI\VSCode
git init
git remote add origin https://github.com/사용자명/레포명.git
git pull origin main
```

### Q: "j5Create drive not found" 에러

```
해결:
1. j5Create USB 연결 확인
2. 드라이브 문자 확인 (E: 아닌 경우 스크립트 수정)
```

### Q: 대용량 파일이 검색되지 않음

```
해결:
hybrid-sync.bat 의 크기 기준 변경:
  $_.Length -gt 10MB   ← 현재 (10MB)
  $_.Length -gt 1MB    ← 1MB 로 변경
```

---

## 추가 파일 정리

다음 파일들은 더 이상 사용하지 않습니다 (삭제 권장):

- `j5create-to-security.bat`
- `j5create-from-security.bat`
- `j5sync-receive.bat`
- `j5sync-send.bat`
- `README-j5create.md`

대신 `hybrid-sync.bat` 과 `hybrid-receive.bat` 만 사용하세요.
