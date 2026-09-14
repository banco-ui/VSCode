# 삼성 사내 GitHub 산출물 공유 가이드

> 출처: axhub AI Community - "삼성 Github 활용 - 산출물 공유하기(Git ignore, Commit & Push)" (김지선, 2026-08-13)
> 원본: https://axhub.sec.samsung.net/AI_Community?ActionView=DETAIL&BoardId=AICrewActivityBoard&Id=POST00008055

## 핵심 요약

삼성 사내 **Enterprise GitHub** (`github.sec.samsung.net`)를 활용하면 사내망 프록시 제한 없이 산출물을 공유할 수 있습니다.

## 사내 GitHub vs 공개 GitHub

| 구분 | 사내 GitHub | 공개 GitHub |
|------|------------|------------|
| URL | github.sec.samsung.net | github.com |
| 프록시 | 사내망 직접 접속 (차단 없음) | 프록시 차단 (403 에러) |
| 인증 | SSO (전사 통합 인증) | gh CLI / PAT |
| 보안 | 사내망 내부 | 외부 노출 |

## 워크플로우

### 1. 저장소 복제 (Clone)

#### VS Code GUI 방식 (추천)
1. VS Code → Ctrl+Shift+P → `Git: Clone`
2. URL 입력: `https://github.sec.samsung.net/{조직}/{저장소명}.git`
3. 로컬 폴더 지정

#### PowerShell 방식
```powershell
cd C:\Users\Username\Projects
git clone https://github.sec.samsung.net/{조직}/{저장소명}.git
cd {저장소명}
```

### 2. 커밋 & 푸시

#### VS Code GUI
1. 좌측 Source Control 탭 (Ctrl+Shift+G)
2. 변경 파일 옆 + 버튼 → Stage Changes
3. 커밋 메시지 입력 → Commit
4. Sync Changes 버튼 클릭

#### PowerShell
```powershell
git status
git add .
git commit -m "feat: 기능 구현"
git push origin main
```

### 3. .gitignore (필수)

```
# 가상 환경 및 패키지
.venv/
node_modules/

# 빌드 결과물
dist/
build/
*.log

# 개인 설정 및 환경변수
.env
.vscode/
```

이미 추적 중인 파일 제거:
```powershell
git rm -r --cached .
git add .
git commit -m "fix: ignore 캐시 삭제 및 .gitignore 적용"
git push origin main
```

## AI 프롬프트 활용 팁

- "지금까지 수정한 내용 적절한 커밋 메시지 작성해서 바로 push해줘."
- "프로젝트에 임시 파일 정리하고 .gitignore 점검한 다음 커밋해서 푸시해줘."
- "내가 만든 변경 사항 보고 Conventional Commit 규칙에 맞게 커밋 메시지 써줘."
- "feat/login-page 브랜치 새로 생성해서 변경사항 올리고 원격 저장소에 push해줘."

## 우리 환경에 대한 제언

현재 공개 GitHub (github.com)를 사용하고 있으며, 사내망 프록시로 인해 push가 차단되는 문제가 있습니다.
사내 GitHub (`github.sec.samsung.net`)로 마이그레이션하면 이 문제를 해결할 수 있습니다.

### 마이그레이션 방법
```powershell
# 기존 원격 저장소 변경
git remote set-url origin https://github.sec.samsung.net/{조직}/{저장소명}.git
git push -u origin main
```
