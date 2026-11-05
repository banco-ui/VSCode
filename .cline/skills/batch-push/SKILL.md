# GitHub 소규모 분할 push (사내망 프록시 403 대응)

> **목적**: 사내 프록시(168.219.61.252:8080)가 git push 전송을 차단할 때,
> 검증된 "작게 잘라서 push" 방식으로 커밋을 순차적으로 원격에 밀어 넣는다.

## 언제 사용하나

- `git push`가 `error: RPC failed; HTTP 403 curl 22` + `the remote end hung up unexpectedly` 로 실패할 때
- fetch/ls-remote(읽기)는 정상이고 push(POST)만 차단될 때
- 특히 커밋에 대용량 파일이 섞여 팩이 수십 MB 이상일 때 거의 항상 발생

## 방법 요약

1. **대용량 파일 먼저 제거** — push 실패의 1차 원인은 팩 크기다.
   - `git rev-list --objects <remote>/main..main | git cat-file --batch-check` 로 미푸시 커밋 내 대형 blob 확인
   - 빌드 산출물(win-unpacked, dist, DLL 등)은 `.gitignore` 추가 + `git filter-repo`로 미푸시 히스토리에서 제거
   - `git filter-repo --force --invert-paths --path <경로> --refs main` (미푸시 커밋이므로 안전)
2. **1커밋 단위 분할 push + 반복 재시도** — 프록시가 간헐적으로 허용하는 창을 노린다.
   ```powershell
   # 오래된 커밋부터 순서대로 (fast-forward 유지)
   $shas = @(git rev-list origin/main..main); [array]::Reverse($shas)
   git push origin ("{0}:refs/heads/main" -f $shas[0])
   ```
   - 실패해도 로컬에 커밋은 안전하므로 몇 번이고 재시도 가능
   - 성공하면 다음 커밋으로 전진. 프록시 상태에 따라 수 분~수 시간 걸릴 수 있음

## 자동 실행 (권장)

```powershell
# 백그라운드 상시 재시도 루프 (origin + upstream 모두, 최대 4시간)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\batch-push.ps1

# 진행 상황 확인
Get-Content .git\batch-push.log -Tail 20 -Wait

# 중단
New-Item .git\batch-push.stop -Force
```

- `scripts/batch-push.ps1`: 1커밋씩 origin/upstream 순차 push, 10회 재시도 후 60초 대기 재라운드.
  로그: `.git\batch-push.log`, 성공 시 `OK   <remote> <n>/<total> -> <sha>` 기록.

## 체크리스트 (효과 순)

1. 미푸시 커밋에서 빌드 산출물/대용량 바이너리 제거 (팩 5MB 이하 권장)
2. `git -c http.version=HTTP/1.1 push ...` 시도 (프록시 HTTP/2 처리 문제 회피, 효과 없을 수 있음)
3. `gh auth token` 으로 토큰 URL push — 단, 토큰 계정이 대상 저장소 소유자여야 함
4. 1커밋 단위 분할 push 반복 (batch-push.ps1)
5. 그래도 안 되면 외부망(테더링/집)에서 `git push origin main && git push upstream main` — 확실

## 주의

- `filter-repo`는 **미푸시 커밋에만** 사용 (이미 push된 커밋을 재작성하면 force-push 필요)
- 토큰 URL push 후 반드시 `git remote set-url <remote> <원래 URL>` 로 복원
- PowerShell에서 토큰 URL 문자열 연결은 `("https://user:" + $t + "@...")` 형태로
  (`"https://user:${$t}@..."`은 빈 값이 들어가므로 금지)

## 실적 기록

- 2026-11-05: 57MB 팩 → filter-repo로 빌드 산출물 제거 → 5.9MB. 사내망에서 1커밋 push도
  프록시가 전면 차단 중이라 batch-push.ps1 상시 루프로 대기 중. 외부망 push가 가장 확실.
