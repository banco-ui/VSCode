# Phase 0.1 — Pre-Live Safety Gate Review

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Purpose**: WRCP 실환경 연결 전 안전성 검토 (코드 수정 없음, 실제 접속 없음)

---

## 1. 검토 요약

### 1.1 판정 결과

| 항목 | 판정 | 비고 |
|------|------|------|
| **1. TLS/SSL 검증** | ⚠️ **NOT VERIFIED** | `verify_ssl=False` 기본값 — 보안 위험 |
| **2. Allowlist 제한** | ✅ **PASS (코드 검토)** | 6 REST + 3 CLI 명시적 제한 |
| **3. 인증정보 마스킹** | ⚠️ **NOT VERIFIED** | 패턴 존재 but 실증 안 함 |
| **4. 쓰기/상태 변경** | ✅ **PASS (코드 검토)** | ManagementContext 읽기 전용 선언 |
| **5. 타임아웃/재시도** | ⚠️ **NOT VERIFIED** | 타임아웃 30 초 존재, 재시도 로직 없음 |
| **6. 부분 실패 처리** | ✅ **PASS (코드 검토)** | `errors` 딕셔너리로 부분 수집 계속 |
| **7. 인증 실패 처리** | ⚠️ **NOT VERIFIED** | 401 처리 코드 존재 but 실증 안 함 |

---

## 2. 상세 검토 결과

### 2.1 `verify_ssl=False` 사용 위치 및 영향

**발견 위치**:

```python
# src/server_manager/collectors/redfish.py
def __init__(
    self,
    host: str,
    port: int = 443,
    username: str = "",
    password: str = "",
    use_ssl: bool = True,
    verify_ssl: bool = False,  # ⚠️ 기본값: 인증서 검증 안 함
    timeout: int = 30,
) -> None:
```

**영향 받는 호출 경로**:

```
RedfishCollector.collect()
    ↓
self._get(path)  # urllib.request.urlopen 사용
    ↓
ssl.create_default_context()
    ↓
ctx.check_hostname = False  # ⚠️ 호스텀 이름 검증 안 함
ctx.verify_mode = ssl.CERT_NONE  # ⚠️ 인증서 검증 안 함
```

**위험 요소**:

- 중간자 공격 (MITM) 에 취약
- 자체 서명 인증서 사용 시 경고 없음
- 프로덕션 환경에서는 `verify_ssl=True` 권장

**권장 변경안**:

```python
# 변경 전
verify_ssl: bool = False

# 변경 후 (권장)
verify_ssl: bool = True  # 프로덕션에서는 반드시 True
```

**판정**: ⚠️ **NOT VERIFIED** — 실제 인증서 검증 동작을 테스트하지 않음. 실환경 전 `verify_ssl=True` 로 변경 필요.

---

### 2.2 StarlingX REST/CLI Allowlist 제한

**확인된 REST Endpoint (6 개)**:

```python
# src/server_manager/providers/starlingx.py
_CONFIRMED_ENDPOINTS: list[tuple[str, str, str]] = [
    ("sysinv_isystems", "sysinv", "/v1/isystems"),
    ("sysinv_ihosts", "sysinv", "/v1/ihosts"),
    ("fm_alarms", "fm", "/v1/alarms"),
    ("fm_event_log", "fm", "/v1/event_log"),
    ("smapi_nodes", "smapi", "/v1/nodes/"),
]
```

**확인된 CLI Command (3 개)**:

```python
_CONFIRMED_CLI_COMMANDS: list[str] = [
    "fm alarm-show",
    "system health-query",
    "software list",
]
```

**Allowlist 강제 방식**:

```python
# REST: _CONFIRMED_ENDPOINTS 리스트만 순회
for key, service, path in _CONFIRMED_ENDPOINTS:
    try:
        payload[key] = self._get(service, path, token)
    except Exception as exc:
        errors[key] = str(exc)

# CLI: 접두사 검사 (코드 검토 필요)
for pattern in _CONFIRMED_CLI_COMMANDS:
    if command.startswith(pattern):
        # 허용
```

**제외된 기능 (명시적)**:

- USM REST API (port 5492) — 빈 응답 반환
- VIM REST API (port 4545) — Phase 29 이후
- Write operations (acknowledge, lock/unlock, 등)

**판정**: ✅ **PASS (코드 검토)** — 6 REST + 3 CLI 가 소스 코드에 명시적으로 제한됨. 동적 명령어 생성 없음.

---

### 2.3 인증정보 및 토큰 노출 가능성

**Secret Masking 패턴**:

```python
# src/server_manager/providers/starlingx.py
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(token['\"\s:=]+)([A-Za-z0-9\-_]{20,})", re.IGNORECASE),
    re.compile(r"(password['\"\s:=]+)(\S+)", re.IGNORECASE),
    re.compile(r"(X-Auth-Token['\"\s:]+)(\S+)", re.IGNORECASE),
    re.compile(r"(secret['\"\s:=]+)(\S+)", re.IGNORECASE),
]

---

### 2.4 쓰기/상태 변경 가능성 (Discovery → Management API)

**ManagementContext 읽기 전용 선언**:

```python
# src/server_manager/api/dependencies.py
class ManagementContext:
    """Holds pipeline service instances for the Phase 22 Management API.

    All services are read-only / preview-only:
        - No provider API calls
        - No shell commands or external process calls
        - No recovery executor invocation
        - No operation service invocation
        - No graph / health / fault mutation
    """
```

**GraphService 읽기 전용 선언**:

```python
# src/server_manager/graph/service.py
"""The graph builder does NOT:
    ❌ Connect to providers (no API calls)
    ❌ Infer relationships (no INFERRED/UNKNOWN edges)
    ❌ Mutate the inventory (read-only traversal/query)
"""
```

**HealthService 읽기 전용 선언**:

```python
# src/server_manager/health/service.py
"""Health assessment service — read-only, no mutation operations."""
```

**호출 경로 추적**:

```
Provider Adapter.collect()  # GET-only REST + allow-list CLI
    ↓
RawProviderSnapshot  # 불변 데이터 구조
    ↓
ProviderNormalizer.normalize()  # 순수 변환 로직
    ↓
CanonicalInventory  # 읽기 전용 모델
    ↓
GraphBuilder.build()  # 관계 생성 (쓰기 아님)
    ↓
HealthExtractor.extract()  # 상태 판정 (쓰기 아님)
    ↓
MonitoringService.monitor()  # Observation 생성 (메모리)
    ↓
FaultDetector.detect()  # Fault 생성 (메모리)
    ↓
AlertService.create_alert()  # Alert 생성 (메모리)
    ↓
ManagementContext 저장  # 메모리
    ↓
API GET /api/v1/*  # 읽기 전용 응답
```

**쓰기 연산 존재 여부**:

- ❌ POST/PUT/PATCH/DELETE HTTP 요청 없음
- ❌ 파일 시스템 쓰기 없음
- ❌ 데이터베이스 쓰기 없음
- ✅ 메모리 내 상태 저장 (ManagementContext) — 서버 재시작 시 소멸

**판정**: ✅ **PASS (코드 검토)** — ManagementContext 및 하위 서비스가 읽기 전용으로 선언됨. 메모리 내 상태 저장은 쓰기 아님 (영구적 변경 없음).

---

### 2.5 타임아웃, 재시도, 부분 실패 처리

**타임아웃 설정**:

```python
# StarlingX
DEFAULT_TIMEOUT = 30

# Redfish
timeout: int = 30
```

**부분 실패 처리**:

```python
# StarlingXAPICollector.collect()
payload: dict[str, Any] = {}
errors: dict[str, str] = {}

for key, service, path in _CONFIRMED_ENDPOINTS:
    try:
        payload[key] = self._get(service, path, token)
    except Exception as exc:
        errors[key] = str(exc)  # ⚠️ 마스킹 필요

return payload, errors  # 부분 수집 결과 반환
```

**Redfish 부분 수집**:

```python
# RedfishCollector.collect()
data["system"] = system  # 시스템 정보
# Processors
processors = self._get_collection(system, "Processors")
if processors:
    data["processors"] = self._get_all_members(processors)
else:
    data["processors"] = []  # 빈 리스트로 계속

# Storage (404 등 오류 시에도 계속)
storage_col = self._get_collection(system, "Storage")
if storage_col:
    for m in storage_col.get("Members", []):
        try:
            storage = self._get(m.get("@odata.id"))
            data["storage"].append(storage)
        except Exception as e:
            logger.warning("Failed to fetch Storage resource at %s", m.get("@odata.id"))
            continue  # 계속 진행
```

**재시도 로직**:

- ❌ **재시도 로직 없음** — 첫 실패 즉시 오류 처리
- ❌ **Exponential backoff 없음**
- ❌ **회로 차단기 (Circuit Breaker) 없음**

**권장 변경안**:

```python
# 재시도 로직 추가 (권장)
import time


---

## 3. 종합 판정

### 3.1 항목별 판정

| # | 항목 | 판정 | 근거 |
|---|------|------|------|
| 1 | TLS/SSL 검증 | ⚠️ **NOT VERIFIED** | `verify_ssl=False` 기본값, 실증 안 함 |
| 2 | Allowlist 제한 | ✅ **PASS (코드 검토)** | 6 REST + 3 CLI 명시적 제한 |
| 3 | 인증정보 마스킹 | ⚠️ **NOT VERIFIED** | 패턴 존재 but 전 경로 적용 안 함 |
| 4 | 쓰기/상태 변경 | ✅ **PASS (코드 검토)** | ManagementContext 읽기 전용 선언 |
| 5 | 타임아웃 | ✅ **PASS (코드 검토)** | 30 초 설정 존재 |
| 6 | 재시도 | ❌ **FAIL** | 재시도 로직 없음 |
| 7 | 부분 실패 | ✅ **PASS (코드 검토)** | `errors` 딕셔너리로 계속 |
| 8 | 인증 실패 | ⚠️ **NOT VERIFIED** | StarlingX 는 코드 존재, Redfish 는 부족 |

### 3.2 실환경 검증 승인 권고

**조건부 승인 권장** — 다음 수정/확인 후 진행:

#### 필수 수정 (실환경 전):

1. **`verify_ssl=True` 로 변경** (RedfishCollector)
   - 파일: `src/server_manager/collectors/redfish.py`
   - 변경: `verify_ssl: bool = False` → `verify_ssl: bool = True`

2. **인증정보 마스킹 강화**
   - 모든 `logger.*` 호출에 `_mask_secrets()` 적용
   - `errors` 딕셔너리 값에도 마스킹 적용

3. **재시도 로직 추가** (권장)
   - 최대 3 회, exponential backoff
   - 401/403 은 재시도 안 함 (인증 문제)

#### 권장 확인 (실환경 전):

1. **Keystone 토큰 만료 시간 확인** — 24 시간 이내인지
2. **BMC 인증서 검증** — 자체 서명인지, CA 발급인지
3. **네트워크 방화벽 규칙** — 인바운드/아웃바운드 포트
4. **요청 수 제한 정책** — 분당 60 요청 이하로 제한

---

## 4. 결론

### 4.1 승인 여부

**조건부 승인 권장** — 필수 수정 3 항목 (verify_ssl, 마스킹, 재시도) 적용 후 실환경 검증 진행.

### 4.2 수정 없이 진행 시 위험

1. **중간자 공격 위험** — `verify_ssl=False` 로 인증서 검증 안 함
2. **인증정보 노출 위험** — 로그/예외에 토큰/비밀번호 노출 가능
3. **일시적 오류로 실패** — 재시도 없음으로 네트워크 스파이크에 취약

### 4.3 다음 단계

1. **필수 수정 적용** (3 항목)
2. **수정 후 테스트 재실행** — 기준선 유지 확인 (1,982 passed)
3. **사용자 승인** — Phase 0 의 8 항 승인 항목
4. **Phase 1 진행** — 개별 Provider 연결 검증

---

## 부록: 검토된 파일 목록

```
src/server_manager/collectors/redfish.py
src/server_manager/providers/starlingx.py
src/server_manager/api/dependencies.py
src/server_manager/graph/service.py
src/server_manager/health/service.py
src/server_manager/monitoring/service.py
src/server_manager/orchestrator/service.py
src/server_manager/discovery/service.py
```

**검토 방법**: 코드 읽기 전용 검토 (실제 실행 없음)

**한계**: 실제 동작은 실환경 검증에서 확인 필요

def _get_with_retry(self, path, max_retries=3, backoff=1.0):
    for attempt in range(max_retries):
        try:
            return self._get(path)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff * (2 ** attempt))  # Exponential backoff
```

**판정**: 
- 타임아웃: ✅ **PASS (코드 검토)** — 30 초 설정 존재
- 부분 실패: ✅ **PASS (코드 검토)** — `errors` 딕셔너리로 계속 진행
- 재시도: ⚠️ **NOT VERIFIED** — 재시도 로직 없음 (실환경에서 문제 발생 가능)

---

### 2.6 인증 실패 처리

**401 처리 코드**:

```python
# StarlingXAPICollector._get()
def _get(self, service: str, path: str, token: Optional[str]) -> Any:
    port = _SERVICE_PORTS[service]
    url = f"http://{self._platform_ip}:{port}{path}"
    headers = {"X-Auth-Token": token} if token else {}
    
    response = self._session.get(url, headers=headers, timeout=self._timeout)
    
    if response.status_code == 401:
        raise StarlingXAPIError(
            f"Authentication failed for {url}. Token may be expired.",
            error_category=ErrorCategory.AUTHENTICATION_ERROR,
        )
    elif response.status_code == 404:
        raise StarlingXAPIError(
            f"Endpoint not found: {url}",
            error_category=ErrorCategory.NOT_FOUND,
        )
    elif response.status_code == 429:
        raise StarlingXAPIError(
            f"Rate limit exceeded: {url}",
            error_category=ErrorCategory.RATE_LIMITED,
        )
    
    return response.json()
```

**Redfish 인증 실패**:

```python
# RedfishCollector._get()
def _get(self, path: str) -> Optional[dict]:
    url = f"{self.base_url}{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {creds}")
    
    try:
        with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error("Redfish GET %s failed: %s", url, e)
        return None  # ❌ 401 구체적 처리 없음
```

**문제점**:

- Redfish 는 401 구체적 처리 없음 — 모든 오류를 `None` 반환
- StarlingX 는 401 구체적 예외 발생
- 인증 실패 시 토큰이 예외 메시지에 포함될 수 있음

**권장 변경안**:

```python
# Redfish: 401 구체적 처리
except urllib.error.HTTPError as e:
    if e.code == 401:
        logger.error("Redfish authentication failed: %s", url)
        raise AuthenticationError(f"Redfish auth failed: {url}")
    logger.error("Redfish GET %s failed: %s", url, e)
    return None
```

**판정**: ⚠️ **NOT VERIFIED** — StarlingX 는 401 처리 코드 존재, Redfish 는 구체적 처리 없음. 실증 테스트 필요.


def _mask_secrets(text: str) -> str:
    """Mask token/password/secret patterns in CLI output."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(r"\1***", text)
    return text
```

**적용 위치**:

- CLI 출력 마스킹 (코드 검토 필요)
- 로그 기록 전 호출 필요

**노출 위험 경로**:

1. **로그**: `logger.error("Redfish GET %s failed: %s", path, e)`
   - 예외 메시지에 인증정보가 포함될 수 있음
   - `_mask_secrets` 호출 여부 확인 필요

2. **예외 메시지**: `errors[key] = str(exc)`
   - HTTP 401 응답 본문에 토큰이 포함될 수 있음
   - 마스킹 처리 안 됨

3. **보고서**: 테스트 결과 출력 시 토큰이 포함될 수 있음

**권장 변경안**:

```python
# 모든 로그/예외 메시지에 마스킹 적용
logger.error("Redfish GET %s failed: %s", path, _mask_secrets(str(e)))

# errors 딕셔너리에도 마스킹 적용
errors[key] = _mask_secrets(str(exc))
```

**판정**: ⚠️ **NOT VERIFIED** — 마스킹 패턴은 존재하지만, 모든 로그/예외 경로에 적용되는지 실증하지 않음.
