# 🔄 Hybrid 동기화 가이드 (GitHub + j5Create)

## 📋 개요

코드/설정은 **GitHub**으로, 대용량 파일은 **j5Create**로 전달하는 하이브리드 방식입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hybrid 동기화 흐름                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [코드/설정 파일]              [대용량 파일]                    │
│  ├─ *.js, *.ts, *.py         ├─ 빌드 결과물 (*.exe, *.dll)    │
│  ├─ *.md, *.json             ├─ 모델 파일 (*.bin, *.onnx)     │
│  └─ *.html, *.css            └─ 데이터셋 (*.csv, *.parquet)   │
│         │                            │                         │
│         ▼                            ▼                         │
│  ┌─────────────┐            ┌─────────────┐                   │
│  │   GitHub    │            │  j5Create   │                   │
│  │  (자동화)   │            │  (수동복사) │                   │
│  └─────────────┘            └─────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 스크립트 구성

```
scripts/
├── hybrid-sync.bat        # [무보안 PC] GitHub + j5Create 확인
├── hybrid-receive.bat     # [보안 PC] j5Create 수신 + GitHub 동기화
└── HYBRID-SYNC-GUIDE.md   # 이 파일
```

---

## 🚀 사용 방법

### [무보안 PC] 작업 시작

```
1. hybrid-sync.bat 실행

2. GitHub 변경사항 확인
   - 변경 파일이 있으면 git push 실행

3. 대용량 파일 확인 (10MB 이상)
   - 목록이 표시되면 j5Create 로 수동 복사
   - E:\j5sync\to-security\ 폴더에 붙여넣기

4. j5Create USB 를 보안 PC 에 연결
```

---

### [보안 PC] 작업 수신

```
1. hybrid-receive.bat 실행

2. j5Create 에서 파일 자동 수신
   - E:\j5sync\to-security\ → d:\work\usm-automation\j5-input\

3. GitHub 상태 확인
   - git pull 로 최신 코드 동기화

4. Cline SR 로 작업 시작
```

---

### [보안 PC] 작업 결과 전송

```
1. hybrid-receive.bat 재실행 (또는 hybrid-send.bat)

2. output\ 폴더의 결과가 j5Create 로 자동 복사
   - d:\work\usm-automation\output\ → E:\j5sync\from-security\

3. j5Create USB 를 무보안 PC 에 연결
```

---

### [무보안 PC] 결과 수신

```
1. hybrid-sync.bat 실행

2. j5Create 에서 결과 파일 확인
   - E:\j5sync\from-security\ 폴더

3. 파일들을 적절한 위치로 복사
   - output\ 폴더 등

4. GitHub 에 결과 push (선택사항)
```

---

## 📊 파일 분류 기준

| 파일 타입 | 크기 | 동기화 방법 |
|-----------|------|-------------|
| 소스 코드 (*.js, *.py) | Any | GitHub |
| 설정 (*.json, *.md) | Any | GitHub |
| 문서 (*.md, *.txt) | Any | GitHub |
| 빌드 결과물 (*.exe, *.dll) | Any | j5Create |
| 모델 파일 (*.bin, *.onnx) | Any | j5Create |
| 데이터 (*.csv, *.parquet) | <10MB | GitHub |
| 데이터 (*.csv, *.parquet) | >10MB | j5Create |

---

## ⚙️ 설정 수정

### hybrid-receive.bat (보안 PC)

```batch
REM 보안 PC 의 실제 경로로 수정
set WORKSPACE=d:\work\usm-automation

REM j5Create 드라이브 문자 확인
set J5DRIVE=E:
```

### hybrid-sync.bat (무보안 PC)

```batch
REM 자동 커밋을 원하면 주석 해제
REM git add .
REM git commit -m "Auto: %date% %time%"
REM git push origin main
```

---

## 🔍 대용량 파일 자동 감지

hybrid-sync.bat 은 10MB 이상 파일을 자동으로 찾아줍니다.

```
검색 기준 변경:

현재: 10MB 이상
변경: powershell 명령에서 크기 조정

  Where-Object { $_.Length -gt 50MB }   ← 50MB 로 변경
  Where-Object { $_.Length -gt 5MB }    ← 5MB 로 변경
```

---

## 📋 체크리스트

### 매일 작업 시작 전

```
[무보안 PC]
□ hybrid-sync.bat 실행
□ GitHub push 필요 확인
□ 대용량 파일 j5Create 에 복사

[보안 PC]
□ hybrid-receive.bat 실행
□ j5-input\ 폴더에서 파일 확인
□ git pull 로 최신 코드 동기화
```

### 매일 작업 종료 후

```
[보안 PC]
□ output\ 폴더에 결과 정리
□ hybrid-receive.bat 재실행 (j5Create 전송)

[무보안 PC]
□ j5Create 에서 결과 파일 확인
□ 적절한 위치로 복사
□ GitHub 에 push
```

---

## ⚠️ 주의사항

### 파일 충돌 방지

```
❌ 하지 말 것:
- 양쪽 PC 에서 동일 파일 동시 수정
- j5Create 와 GitHub 으로 동일 파일 중복 전송

✅ 할 것:
- 한쪽에서만 수정 후 동기화
- 코드: GitHub, 대용량: j5Create 명확히 구분
```

### 보안

```
- j5Create 분실 시 즉시 보고
- 민감한 파일은 암호화
- 사용 후 j5sync 폴더 정리
```

---

## 🛠️ 문제 해결

### Q1. "j5Create 드라이브를 찾을 수 없습니다"

```
해결:
1. USB 연결 확인
2. j5Create Connect 소프트웨어 실행
3. 드라이브 문자 확인 (E: 아닌 경우 스크립트 수정)
```

### Q2. "Git 저장소가 아닙니다"

```
해결:
cd d:\Data\AI\VSCode
git init
git remote add origin https://github.com/사용자명/repo.git
git pull origin main
```

### Q3. "대용량 파일이 표시되지 않습니다"

```
해결:
hybrid-sync.bat 의 powershell 명령 확인:
  Where-Object { $_.Length -gt 10MB }

크기 기준을 낮추세요:
  Where-Object { $_.Length -gt 1MB }
```

---

## 📈 고급: 자동화 확장

### Windows 작업 스케줄러 등록

```
매일 출근 전 자동 동기화:

1. 작업 스케줄러 → 작업 만들기
2. 트리거: 매일 08:00
3. 작업: hybrid-sync.bat 실행
4. 조건: 네트워크 연결 시
```

### Git 후크 자동화

```
.git/hooks/post-commit 에 추가:

#!/bin/bash
/scripts/hybrid-sync.bat
```

---

## 📞 지원

문제 발생 시 다음 정보 준비:

1. OS 버전 (Windows 10/11)
2. j5Create 드라이브 문자
3. Git 저장소 여부
4. 에러 메시지 전체
