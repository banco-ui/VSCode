# Phase 1 — Live Provider Connection Validation

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Status**: **BLOCKED — 사용자 확인 필요**

---

## 1. 사전 확인 완료

### 1.1 Git 상태

```
Branch: main
Working tree: clean
Local commits: 175 ahead of origin/main
```

**판단**: 사용자 변경 사항 보존됨 ✅

### 1.2 Phase 0.2 보안 강화 적용 확인

| 항목 | 적용 여부 |
|------|----------|
| Redfish `verify_ssl=True` 기본값 | ✅ 적용됨 |
| StarlingX `verify=True` 기본값 | ✅ 적용됨 |
| 인증정보 마스킹 (`_sanitize_error_message`) | ✅ 적용됨 |
| 제한적 재시도 로직 | ✅ 적용됨 |

### 1.3 Provider 구현 확인

| Provider | 구현 파일 | 읽기 전용 여부 |
|----------|----------|---------------|
| **Kubernetes** | `src/server_manager/providers/kubernetes.py` | ✅ Fixture 기반 (라이브 클라이언트 주입 가능) |
| **StarlingX** | `src/server_manager/providers/starlingx.py` | ✅ 6 REST GET + 3 CLI allowlist |
| **Redfish** | `src/server_manager/collectors/redfish.py` | ✅ GET-only, TLS 검증 활성화 |

---

## 2. 실환경 검증 전 사용자 확인 필요

실환경 검증을 시작하기 전에 다음 항목에 대한 **명시적 승인**이 필요합니다.

### 2.1 인증정보 확인

**출력 금지**: 비밀번호, 토큰, kubeconfig 내용, Authorization 헤더는 보고서에 기록하지 않습니다.

| Provider | 확인 항목 | 사용자 확인 |
|----------|----------|------------|
| **Kubernetes** | kubeconfig 또는 ServiceAccount 토큰 준비됨? | [ ] 예 / [ ] 아니오 |
| **StarlingX** | Keystone 토큰 발급 가능? | [ ] 예 / [ ] 아니오 |
| **Redfish** | BMC IP, 사용자명, 비밀번호 준비됨? | [ ] 예 / [ ] 아니오 |

### 2.2 네트워크 접근 확인

| 대상 | 포트 | 프로토콜 | 접근 가능? |
|------|------|----------|-----------|
| Kubernetes API | 6443 | HTTPS | [ ] 예 / [ ] 아니오 / [ ] 확인 필요 |
| WRCP AIO-SX (sysinv) | 6385 | HTTP | [ ] 예 / [ ] 아니오 / [ ] 확인 필요 |
| WRCP AIO-SX (FM) | 18002 | HTTP | [ ] 예 / [ ] 아니오 / [ ] 확인 필요 |
| WRCP AIO-SX (SMAPI) | 7777 | HTTP | [ ] 예 / [ ] 아니오 / [ ] 확인 필요 |
| BMC (Redfish) | 443 | HTTPS | [ ] 예 / [ ] 아니오 / [ ] 확인 필요 |

### 2.3 TLS 인증서 확인

| Provider | 인증서 종류 | `verify_ssl=True` 허용? |
|----------|------------|------------------------|
| **Kubernetes** | CA 발급 / 자체 서명 / 확인 필요 | [ ] 예 / [ ] 아니오 (자체 서명 시 `verify_ssl=False` 필요) |
| **Redfish** | CA 발급 / 자체 서명 / 확인 필요 | [ ] 예 / [ ] 아니오 (자체 서명 시 `verify_ssl=False` 필요) |
| **StarlingX** | HTTP 기본 (TLS 없음) | N/A |

**주의**: Phase 0.2 에서 TLS 검증 기본값이 `True` 로 변경되었습니다. 자체 서명 인증서 환경에서는 명시적으로 `verify_ssl=False` 를 전달해야 합니다.

---

## 3. 검증 예정 항목 (승인 시)

### 3.1 Kubernetes

| # | 검증 항목 | HTTP 메서드 | 예상 결과 | 중단 조건 |
|---|----------|-------------|----------|----------|
| K1 | API 서버 연결 | GET /version | 200 OK, 버전 정보 | 401/403/연결 실패 |
| K2 | Node 리스트 조회 | GET /api/v1/nodes | 200 OK, Node 리스트 | 401/403/연결 실패 |
| K3 | Pod 리스트 조회 (default namespace) | GET /api/v1/namespaces/default/pods | 200 OK, Pod 리스트 | 401/403/연결 실패 |

**금지**: 리소스 생성/수정/삭제, exec, port-forward, rollout

### 3.2 StarlingX

| # | 검증 항목 | 엔드포인트/명령 | 예상 결과 | 중단 조건 |
|---|----------|----------------|----------|----------|
| S1 | sysinv 시스템 조회 | GET /v1/isystems | 200 OK, 시스템 정보 | 401/404/연결 실패 |
| S2 | sysinv 호스트 조회 | GET /v1/ihosts | 200 OK, 호스트 리스트 | 401/404/연결 실패 |
| S3 | FM Alarm 조회 | GET /v1/alarms | 200 OK, Alarm 리스트 | 401/404/연결 실패 |
| S4 | CLI: system health-query | `system health-query` | Exit 0, 건강 상태 | Exit non-zero |

**금지**: 임의 CLI 명령, write operations (acknowledge, lock/unlock)

### 3.3 Redfish

| # | 검증 항목 | 엔드포인트 | 예상 결과 | 중단 조건 |
|---|----------|----------|----------|----------|
| R1 | Root 서비스 조회 | GET /redfish/v1/ | 200 OK, Redfish 버전 | 401/403/연결 실패 |
| R2 | System 조회 | GET /redfish/v1/Systems/{id} | 200 OK, 시스템 정보 | 401/403/연결 실패 |
| R3 | TLS 인증서 검증 | HTTPS 연결 | 검증 성공 | 검증 실패 (자체 서명) |

**금지**: POST/PATCH/DELETE, Reset Action, Write operations

---

## 4. 즉시 중단 조건

다음 중 하나라도 발생하면 **즉시 중단**하고 결과를 기록합니다:

1. **인증 실패** (401/403)
2. **TLS 인증서 검증 실패** (자체 서명 인증서)
3. **인증정보 노출 가능성** (로그/에러 메시지에 토큰/비밀번호 포함)
4. **예상 밖의 쓰기 요청** (POST/PUT/PATCH/DELETE 감지)
5. **승인 범위 이탈** (정의되지 않은 엔드포인트/명령)

---

## 5. 사용자 승인 요청

**실환경 검증을 시작하시겠습니까?**

다음 중 하나를 선택하세요:

1. **모든 Provider 검증 승인** — Kubernetes, StarlingX, Redfish 모두 실환경 검증 수행
2. **Kubernetes 만 승인** — Kubernetes 연결 검증만 수행
3. **StarlingX 만 승인** — StarlingX REST/CLI 검증만 수행
4. **Redfish 만 승인** — Redfish 하드웨어 조회 검증만 수행
5. **보류** — 인증정보/네트워크 준비 안 됨, 검증 보류

**승인 시 다음 정보를 알려주세요** (민감정보 제외):

- Kubernetes: kubeconfig 파일 경로 또는 "ServiceAccount 사용"
- StarlingX: "Keystone 토큰 준비됨" 또는 "토큰 발급 필요"
- Redfish: "BMC IP 준비됨" 또는 "IP 확인 필요"
- TLS: "자체 서명 인증서 포함" 여부 (include_self_signed=true/false)

---

## 6. 현재 상태

**Status**: `BLOCKED — 사용자 승인 대기`

**이유**: 실환경 접속 전 인증정보 및 네트워크 접근 확인 필요

**다음 단계**: 사용자 승인 후 해당 Provider 의 연결 검증 수행

---

**보고서 작성 예정**: `output/Phase1_Live_Provider_Connection_Validation.md`

**검증 방법**: 각 Provider 별 읽기 전용 GET/CLI 명령만 실행, HTTP 상태 코드 및TLS 검증 결과 기록 (민감정보 제외)
