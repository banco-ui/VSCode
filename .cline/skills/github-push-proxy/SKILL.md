# GitHub Push (사내망 프록시 대응)

## 상황
Samsung 사내망 프록시(`168.219.61.252:8080`)가 GitHub HTTPS git push를 간헐적으로 403 에러로 차단함.

## 원인
- 사내망 프록시가 git push의 HTTPS body 데이터를 가로채서 차단
- `gh` CLI API 요청은 통과하지만, git push 데이터 전송은 차단됨
- SSH (포트 22, 443)도 모두 차단됨
- 작은 커밋(~250 lines, ~4 files)은 간헐적으로 성공

## 해결 방법

### 방법 1: 토큰 URL 방식 (사내망에서 부분 성공)
```bash
# gh CLI에서 토큰 가져오기
TOKEN=$(gh auth token)

# 토큰을 URL에 포함하여 push
git remote set-url origin "https://shoutsky0705:${TOKEN}@github.com/shoutsky0705/VSCode.git"
git push origin main

# URL 복원 (보안)
git remote set-url origin "https://github.com/shoutsky0705/VSCode.git"
```

### 방법 2: 작은 커밋으로 분할 (사내망에서 부분 성공)
```bash
# 큰 커밋을 작게 나누기
git reset --soft HEAD~1
git reset HEAD .
git add <일부파일만>
git commit -m "small commit"
git push origin main
# 반복
```

### 방법 3: 외부망에서 push (가장 확실)
```bash
# 테더링/VPN/집 네트워크에서
cd d:\Data\AI\VSCode
git push origin main
```

### 방법 4: VS Code Source Control
- VS Code → Source Control (Ctrl+Shift+G) → Sync Changes
- 외부망에서 실행

## .gitignore 설정 (대용량 파일 제외)
```
*.docx
*.xlsx
*.pptx
*.odt
*.png
*.jpg
*.jpeg
*.pdf
*.tar.gz
*.zip
*.exe
```

## 자동 커밋 스크립트
- `scripts/git-auto-commit.ps1`: 토큰 URL 방식으로 push 시도, 실패 시 커밋만 로컬 유지
- `scripts/git-auto-commit.bat`: 작업 스케줄러용 (30분 간격)
- 로그: `%USERPROFILE%\git-auto-commit.log`

## 인증 설정
```bash
# gh CLI 인증
gh auth login

# git credential helper 설정
git config --global credential.https://github.com.helper "!gh auth git-credential"
```

## 두 가지 옵션 요약

### 옵션 A: 사내 GitHub (github.sec.samsung.net)
- **장점**: 사내망에서 push 차단 없음, SSO 인증, 보안
- **단점**: 외부 접근 불가, 사내망 내에서만 사용
- **적용**: 사내 협업, 보안이 중요한 산출물

### 옵션 B: 사외 GitHub (github.com) - 현재 사용 중
- **장점**: 어디서든 접근 가능, 외부 포트폴리오, 다양한 도구 연동
- **단점**: 사내망 프록시로 인해 push 제한 (토큰 URL 방식, 작은 커밋 분할, 외부망 push 필요)
- **적용**: 개인 학습, 포트폴리오, 외부 도구 연동

## 주의사항
- 토큰 URL 방식은 보안상 위험하므로 push 후 반드시 URL 복원
- 사내망에서는 push가 간헐적으로 실패할 수 있음
- 커밋은 로컬에 안전하게 저장되므로 외부망에서 push 가능
- 상황에 따라 사내 GitHub와 사외 GitHub를 선택적으로 사용


