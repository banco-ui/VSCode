# Phase 1-RF — Redfish Live Validation

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Status**: **BLOCKED — 인증정보 확인 불가**

---

## 1. 실행 개요

### 1.1 검증 대상 서버

어제 Cline 에 전달된 기존 접속 정보:

| 서버 | iDRAC IP | 모델 |
|------|----------|------|
| Server 1 | 10.254.174.17 | Dell XR11 |
| Server 2 | 10.254.171.113 | Dell R750 |
| Server 3 | 10.254.170.196 | HPE e910t |

### 1.2 인증정보 확인 시도

| 확인 방법 | 결과 |
|----------|------|
| 환경 변수 (`REDFISH_*`, `IDRAC_*`, `BMC_*`) | ❌ 설정되지 않음 |
| `.env` 파일 | ❌ 없음 |
| 프로젝트 설정 파일 | ❌ 인증정보 없음 |
| Cline 대화 맥락 | ❌ 현재 세션에서 확인 불가 |

**판단**: 기존 인증정보를 현재 환경에서 확인할 수 없음.

---

## 2. 안전 점검 (코드 검토)

### 2.1 TLS 인증서 검증

**확인 위치**: `src/server_manager/collectors/redfish.py`

```python
# Line 36: TLS 검증 기본값
verify_ssl: bool = True  # Phase 0.2: Default to True for security

# Line 194-198: SSL 컨텍스트 설정
ctx = ssl.create_default_context()
if not self.verify_ssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
```

**판정**: ✅ **PASS** — TLS 인증서 검증이 기본적으로 활성화됨.

### 2.2 인증 방식

```python
# Line 190-192: HTTP Basic Auth
if self.username and self._password:
    creds = base64.b64encode(f"{self.username}:{self._password}".encode()).decode()
    req.add_header("Authorization", f"Basic {creds}")
```

**판정**: ✅ **PASS** — HTTP Basic Auth 사용 (표준 방식).

### 2.3 재시도 정책

```python
# Line 144-147: 401/403/4xx 재시도 안 함
if e.code < 500:
    logger.error("Redfish GET %s failed with %d (no retry)", path, e.code)
    return None
```

**판정**: ✅ **PASS** — 인증 오류 (401/403) 는 재시도하지 않음.

### 2.4 읽기 전용 보장

**확인된 메서드**:
- `_get()`, `_get_with_retry()`, `_get_once()` — 모두 GET 만 수행
- `collect()` — GET 만 호출

**판정**: ✅ **PASS** — POST/PUT/PATCH/DELETE 없음.

---

## 3. 서버별 검증 결과

### 3.1 Dell XR11 (10.254.174.17)

| 항목 | 결과 |
|------|------|
| **연결 상태** | **BLOCKED** |
| 인증정보 확인 | ❌ 사용자명/비밀번호 없음 |
| TLS 검증 | ⚠️ 테스트 안 함 (인증정보 없음) |
| 읽기 전용 요청 | ⚠️ 수행 안 함 |
| HTTP 상태 코드 | N/A |

**사유**: 인증정보를 확인할 수 없음.

**필요한 조치**:
- iDRAC 사용자명/비밀번호 준비
- TLS 인증서 종류 확인 (자체 서명 여부)

---

### 3.2 Dell R750 (10.254.171.113)

| 항목 | 결과 |
|------|------|
| **연결 상태** | **BLOCKED** |
| 인증정보 확인 | ❌ 사용자명/비밀번호 없음 |
| TLS 검증 | ⚠️ 테스트 안 함 (인증정보 없음) |
| 읽기 전용 요청 | ⚠️ 수행 안 함 |
| HTTP 상태 코드 | N/A |

**사유**: 인증정보를 확인할 수 없음.

**필요한 조치**:
- iDRAC 사용자명/비밀번호 준비
- TLS 인증서 종류 확인 (자체 서명 여부)

---

### 3.3 HPE e910t (10.254.170.196)

| 항목 | 결과 |
|------|------|
| **연결 상태** | **BLOCKED** |
| 인증정보 확인 | ❌ 사용자명/비밀번호 없음 |
| TLS 검증 | ⚠️ 테스트 안 함 (인증정보 없음) |
| 읽기 전용 요청 | ⚠️ 수행 안 함 |
| HTTP 상태 코드 | N/A |

**사유**: 인증정보를 확인할 수 없음.

**필요한 조치**:
- iLO 사용자명/비밀번호 준비
- TLS 인증서 종류 확인 (자체 서명 여부)

---

## 4. 보안 조건 준수 확인

### 4.1 TLS 인증서 검증

| 항목 | 준수 여부 |
|------|----------|
| `verify_ssl=True` 기본값 | ✅ 준수 (코드 Line 36) |
| 인증서 검증 우회 안 함 | ✅ 준수 (코드 Line 196-198) |
| HTTPS 사용 | ✅ 준수 (코드 Line 50-51) |

### 4.2 민감정보 비노출

| 항목 | 준수 여부 |
|------|----------|
| 비밀번호 출력 안 함 | ✅ 준수 (출력된 값 없음) |
| 토큰 값 출력 안 함 | ✅ 준수 (토큰 사용 안 함) |
| Authorization 헤더 출력 안 함 | ✅ 준수 (헤더 값 기록 안 함) |
| 환경 변수 값 출력 안 함 | ✅ 준수 (값을 출력하지 않음) |

### 4.3 읽기 전용 범위

| 항목 | 준수 여부 |
|------|----------|
| POST/PUT/PATCH/DELETE 금지 | ✅ 준수 (코드에 없음) |
| 전원 제어 금지 | ✅ 준수 (수행 안 함) |
| 설정 변경 금지 | ✅ 준수 (수행 안 함) |
| Discovery 파이프라인 금지 | ✅ 준수 (수행 안 함) |
| Operations/Recovery 금지 | ✅ 준수 (수행 안 함) |

---

## 5. 종합 판정

### 5.1 서버별 결과

| 서버 | IP | 판정 | 사유 |
|------|-----|------|------|
| **Dell XR11** | 10.254.174.17 | **BLOCKED** | 인증정보 확인 불가 |
| **Dell R750** | 10.254.171.113 | **BLOCKED** | 인증정보 확인 불가 |
| **HPE e910t** | 10.254.170.196 | **BLOCKED** | 인증정보 확인 불가 |

### 5.2 코드 안전성

| 항목 | 판정 |
|------|------|
| TLS 인증서 검증 | ✅ PASS |
| 인증 방식 | ✅ PASS |
| 재시도 정책 | ✅ PASS |
| 읽기 전용 보장 | ✅ PASS |
| 민감정보 처리 | ✅ PASS |

---

## 6. 필요한 조치

### 6.1 인증정보 제공

다음 형식으로 인증정보를 제공하세요 (보고서에 기록되지 않음):

```
Server 1 (Dell XR11):
  - Username: <사용자명>
  - Password: <비밀번호>
  - TLS: CA 발급 / 자체 서명

Server 2 (Dell R750):
  - Username: <사용자명>
  - Password: <비밀번호>
  - TLS: CA 발급 / 자체 서명

Server 3 (HPE e910t):
  - Username: <사용자명>
  - Password: <비밀번호>
  - TLS: CA 발급 / 자체 서명
```

### 6.2 TLS 인증서 확인

**자체 서명 인증서인 경우**:
- `verify_ssl=False` 를 명시적으로 전달할 코드 수정 필요
- 또는 CA 인증서로 교체 권장

**CA 발급 인증서인 경우**:
- 기본 설정 (`verify_ssl=True`) 으로 연결 가능

---

## 7. 다음 단계

1. **인증정보 제공** — 사용자명/비밀번호 전달 (보안 채널)
2. **TLS 인증서 확인** — 자체 서명 여부 확인
3. **코드 수정 (필요 시)** — `verify_ssl=False` 전달
4. **Phase 1-RF 재실행** — 실제 연결 테스트

---

## 8. 결론

**Phase 1-RF — Redfish Live Validation** 은 모든 서버가 **BLOCKED**로 판정되었습니다.

**사유**: 인증정보를 현재 환경에서 확인할 수 없음.

**코드 안전성**: 모든 보안 조건을 준수함 (TLS 검증, 재시도 정책, 읽기 전용 보장).

**다음 단계**: 인증정보 제공 후 Phase 1-RF 재실행.

---

## 부록: 코드 검토 요약

### RedfishCollector 주요 설정

```python
# Line 25-42: __init__ 시그니처
def __init__(
    self,
    host: str,
    port: int = 443,
    username: str = "",
    password: str = "",
    use_ssl: bool = True,
    verify_ssl: bool = True,  # Phase 0.2: Default to True
    timeout: int = 30,
) -> None:
```

### 재시도 상수

```python
# Line 20-23
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
RETRY_BACKOFF_MAX = 10.0  # cap
RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})
```

### Git 상태

```
Branch: main
Working tree: clean
Local commits: 175 ahead of origin/main
```

**판단**: 사용자 변경 사항 보존됨 ✅

### Phase 29 금지

**Phase 29 는 시작하지 않음** — Phase 1-RF 이 BLOCKED 이므로 Phase 29 로 진행 불가.