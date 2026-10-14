# Phase 0.2 — Security Hardening and Regression Report

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Purpose**: Phase 0.1 에서 확인된 보안 문제 수정 및 회귀 검증

---

## 1. 변경 사항 요약

### 1.1 변경된 파일

| 파일 | 변경 내용 | 사유 |
|------|----------|------|
| `src/server_manager/collectors/redfish.py` | `verify_ssl` 기본값 `False` → `True` | TLS 인증서 검증 보안 강화 |
| `src/server_manager/collectors/redfish.py` | 재시도 로직 추가 (`_get_with_retry`, `_get_once`) | 일시적 네트워크 오류 복구 |
| `src/server_manager/collectors/redfish.py` | `urllib.error` 모듈 레벨 import | 재시도 로직 예외 처리 |
| `src/server_manager/providers/starlingx.py` | `verify=False` → `verify=True` | TLS 인증서 검증 보안 강화 |
| `src/server_manager/providers/starlingx.py` | `_sanitize_error_message()` 함수 추가 | 인증정보 마스킹 |
| `src/server_manager/providers/starlingx.py` | API/CLI 오류 처리에 마스킹 적용 | 인증정보 노출 방지 |
| `tests/test_collectors.py` | Phase 0.2 보안 테스트 13 개 추가 | TLS/재시도/마스킹 검증 |

---

## 2. TLS 검증 강화

### 2.1 RedfishCollector

**변경 전**:
```python
verify_ssl: bool = False  # 인증서 검증 안 함
```

**변경 후**:
```python
verify_ssl: bool = True  # Phase 0.2: Default to True for security
```

**영향**:
- 자체 서명 인증서 사용 환경에서는 `verify_ssl=False` 명시적 전달 필요
- 프로덕션 환경에서는 CA 발급 인증서 사용 권장

### 2.2 StarlingXAPICollector

**변경 전**:
```python
response = self._session.get(
    url, headers=headers, timeout=self._timeout, verify=False
)
```

**변경 후**:
```python
# Phase 0.2: Default to verify=True for TLS security
# For self-signed certs, inject a custom session with verify=False
response = self._session.get(
    url, headers=headers, timeout=self._timeout, verify=True
)
```

**영향**:
- 자체 서명 인증서 환경에서는 custom session 주입 필요
- 기본 동작은 TLS 검증 활성화

---

## 3. 인증정보 마스킹 강화

### 3.1 새로운 함수

```python
def _sanitize_error_message(exc: Exception) -> str:
    """Sanitize exception messages to prevent credential leakage."""
    msg = str(exc)
    msg = _mask_secrets(msg)
    return msg
```

### 3.2 적용 위치


---

## 5. 테스트 결과

### 5.1 신규 보안 테스트 (13 개)

| 테스트 그룹 | 테스트 수 | 결과 |
|------------|----------|------|
| TLS Security | 3 | ✅ PASS |
| Retry Logic | 5 | ✅ PASS (2 개는 mock 테스트) |
| Credential Masking | 5 | ✅ PASS |

**신규 테스트**: 13 개 모두 통과

### 5.2 전체 테스트 결과

| 항목 | Phase 0.1 기준선 | Phase 0.2 결과 | 차이 |
|------|-----------------|---------------|------|
| **Passed** | 1,982 | **1,995** | +13 (신규 테스트) |
| **Skipped** | 27 | **27** | 0 |
| **Failed** | 1 | **1** | 0 |

**실패한 테스트**:
```
FAILED tests/test_scheduler.py::TestScheduleDefinition::test_is_due_past
  AssertionError: assert False is True
```

**판단**: 기존 scheduler 실패와 동일 — 신규 회귀 아님

---

## 6. 기준선 비교

### 6.1 테스트 기준선 유지

| 기준 | 결과 |
|------|------|
| 기존 1,982 개 테스트 통과 | ✅ 유지 |
| 기존 27 개 skipped | ✅ 유지 |
| 기존 1 개 실패 (scheduler) | ✅ 유지 |
| 신규 회귀 0 건 | ✅ 확인 |

### 6.2 보안 강화 항목

| 항목 | Phase 0.1 | Phase 0.2 | 상태 |
|------|-----------|-----------|------|
| TLS 기본값 | `verify_ssl=False` | `verify_ssl=True` | ✅ 수정됨 |
| StarlingX TLS | `verify=False` | `verify=True` | ✅ 수정됨 |
| 인증정보 마스킹 | 부분적 | 전 경로 적용 | ✅ 수정됨 |
| 재시도 로직 | 없음 | 제한적 재시도 | ✅ 추가됨 |

---

## 7. 결론

### 7.1 보안 강화 완료

Phase 0.1 에서 확인된 3 개 필수 수정 사항이 모두 적용되었습니다:

1. ✅ **TLS 기본값 변경**: `verify_ssl=False` → `True`
2. ✅ **인증정보 마스킹 강화**: 모든 오류 경로에 마스킹 적용
3. ✅ **제한적인 재시도 로직**: 3 회, exponential backoff, 4xx/TLS 실패 제외

### 7.2 회귀 없음

전체 테스트 결과 1,995 passed, 27 skipped, 1 failed 로 기준선이 유지되었습니다. 신규 회귀는 없습니다.

### 7.3 실환경 검증 승인 권고

**승인 권고** — 보안 강화가 완료되었고 회귀가 없습니다.

**다음 단계**: Phase 1 — 개별 Provider 연결 검증

---

## 부록: 실행된 테스트 명령

```bash
# 전체 테스트
python -m pytest --tb=line -q
# 결과: 1 failed, 1995 passed, 27 skipped in 36.89s

# 보안 테스트만
python -m pytest tests/test_collectors.py::TestPhase02_TLSSecurity \
  tests/test_collectors.py::TestPhase02_RetryLogic \
  tests/test_collectors.py::TestPhase02_CredentialMasking -v
# 결과: 13 passed in 8.59s
```

**StarlingX API/CLI Collector**:
- API 오류: `errors[key] = _sanitize_error_message(exc)`
- imemorys 오류: `errors[f"sysinv_imemorys/{host_uuid}"] = _sanitize_error_message(exc)`
- CLI 오류: `errors["fm_alarm_show/..."]`, `errors["system_health_query"]`, `errors["software_list"]`

### 3.3 마스킹 대상

- `token: <value>` → `token: ***`
- `password: <value>` → `password: ***`
- `X-Auth-Token: <value>` → `X-Auth-Token: ***`
- `secret: <value>` → `secret: ***`

---

## 4. 제한적인 재시도 정책

### 4.1 재시도 상수

```python
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
RETRY_BACKOFF_MAX = 10.0  # cap
RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})
```

### 4.2 재시도 대상

| 오류 유형 | 재시도 | 비고 |
|----------|--------|------|
| 연결 오류, 타임아웃 | ✅ | 네트워크 스파이크 |
| 500, 502, 503, 504 | ✅ | 서버 일시적 오류 |
| 401, 403, 4xx | ❌ | 인증/권한 문제 |
| TLS 검증 실패 | ❌ | 보안 문제 |

**총 지연 시간 상한**: 1.0 + 2.0 + 4.0 = 7.0 초 (최대)
