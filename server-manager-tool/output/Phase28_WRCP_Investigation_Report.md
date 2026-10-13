# Phase 28 — WRCP Provider Integration: Investigation Report

## 1. Executive Summary

**Status**: `BLOCKED — WRCP API contract evidence NOT_FOUND`

조사 결과, repository 내에 WRCP의 실제 API, 객체 모델, endpoint, CLI,
authentication 방식, fixture, 또는 sample response가 **존재하지 않는다**.

기존 design 문서들(Phase 13)도 동일한 결론을 기록하고 있다:
- "WRCP Evidence: NOT_FOUND"
- "WRCP API spec UNKNOWN/DEFERRED"
- "No endpoint/CLI/schema guessing, no fake WRCP adapter"
- "실제 interface/class 파일 생성하지 않음"

Phase 28 작업 원칙에 따라 **추측 구현을 하지 않고 조사 결과를 보고하고 멈춘다**.

---

## 2. Investigation Scope

다음 항목을 전수 조사했다:

1. ProviderAdapter 및 RawProviderSnapshot 계약 (`providers/base.py`)
2. Kubernetes Adapter 및 Normalizer 실제 구현
3. OpenStack Adapter 및 Normalizer 실제 구현
4. Canonical entity, SourceEvidence, 관계 생성 및 ID 결정 규칙
5. Health extractor 등록 및 자원 정보 처리 방식
6. Discovery Service, Infrastructure Graph, Management API 연동 구조
7. 프로젝트 내부의 WRCP 관련 문서, fixture, 샘플 응답, 기존 코드 및 API 명세
8. 실제 WRCP 제품 버전과 API 호환성을 확인할 수 있는 근거

---

## 3. WRCP Evidence Audit

### 3.1 Repository 전체 검색 결과

| Search Target | Result |
|---------------|--------|
| WRCP adapter source code (`providers/wrcp.py`) | NOT_FOUND |
| WRCP normalizer (`normalizers/wrcp_normalizer.py`) | NOT_FOUND |
| WRCP health extractor (in `health/service.py`) | NOT_FOUND (only K8S, OPENSTACK registered) |
| WRCP fixture files (JSON/YAML) | NOT_FOUND |
| WRCP API specification document | NOT_FOUND |
| WRCP CLI command reference | NOT_FOUND |
| WRCP SDK / client library | NOT_FOUND |
| WRCP sample API responses | NOT_FOUND |
| WRCP authentication specification | NOT_FOUND |
| WRCP object model documentation | NOT_FOUND |
| WRCP-to-canonical entity mapping | NOT_FOUND |
| WRCP relationship evidence specification | NOT_FOUND |

### 3.2 존재하는 WRCP 관련 자료 (enum 및 문서만)

#### Enum 값 (사용 준비만 됨, 구현 없음)

| Enum | Value | Location |
|------|-------|----------|
| `ProviderType` | `WRCP = "WRCP"` | `models/canonical.py:49` |
| `PlatformType` | `WRCP = "WRCP"` | `models/canonical.py:60` |
| `ClusterType` | `WRCP_AIO_SX = "WRCP_AIO_SX"` | `models/canonical.py:70` |

#### Design 문서 (모두 "UNKNOWN/DEFERRED" 결론)

1. **Phase13-WRCP-Architecture-Integration-Readiness.md**:
   - "WRCP Evidence: NOT_FOUND"
   - "Repository source code 에 WRCP 관련 evidence 없음"
   - "DESIGN_DECISION_REQUIRED"
   - "WRCP interface 정의되지 않음 — REST API / CLI / SDK 중 어떤 interface 를 제공하는지 알 수 없음"

2. **Phase13-WRCP-Integration-Design-Gate.md**:
   - "DESIGN_READY_FOR_EXTERNAL_CONTRACT"
   - "WRCP 의 실제 API 나 동작을 추측하지 않으며"
   - "실제 interface/class 파일 생성하지 않음"
   - 모든 External Contract = UNKNOWN

3. **Phase13G-2-Provider-Adapter-Raw-Snapshot-Contract.md**:
   - "WRCP API spec UNKNOWN/DEFERRED. No endpoint/CLI/schema guessing, no fake WRCP adapter."

#### Test 파일 내 WRCP 참조 (generic contract 검증용)

| Test File | Usage | Nature |
|-----------|-------|--------|
| `test_provider_adapter.py` | `ProviderType.WRCP` with `FakeProviderAdapter` | Generic enum test — NOT WRCP adapter test |
| `test_provider_normalizer.py` | Canonical ID generation for WRCP | Generic ID determinism test |
| `test_platform_operations.py` | Asserts `"wrcp_cli" not in fields` | Negative test — verifies NO WRCP-specific fields |
| `test_platform_visibility.py` | `ProviderType.WRCP` for alert contract | Generic contract test |

#### Code comment 참조

| File | Reference | Nature |
|------|-----------|--------|
| `providers/base.py:183` | "WRCP CLI output, etc." | Docstring example — not actual CLI spec |
| `docs/phase-15-platform-health.md:164` | Pseudocode `WRCPHealthExtractor` example | Pseudocode only — not implementation |
| `docs/phase-15-platform-health.md:123` | "WRCP health (no credentials → DEFERRED)" | Deferred status note |

### 3.3 WRCP 정체성 모호성

| Source | WRCP Definition |
|--------|----------------|
| Phase13E design doc (search result) | "Wind River Cloud Platform" |
| Phase13 WRCP Architecture Readiness | "CaaS Recovery Wizard (WRCP)" |
| Phase13A (search result) | WRCP 24.09 installation files at `D:\WRCP\` |
| Phase 28 task | "WRCP" (정의 없음) |

WRCP가 무엇인지조차 문서 간에 불일치가 있다.
"Wind River Cloud Platform"인지 "CaaS Recovery Wizard"인지 확인되지 않았다.

---

## 4. 기존 Provider 구현 분석 (WRCP 구현에 필요한 정보 도출)

### 4.1 ProviderAdapter 계약 (`providers/base.py`)

```python
class ProviderAdapter(ABC):
    def __init__(self, provider_type: ProviderType, provider_id: Optional[str] = None)
    @property
    def provider_type(self) -> ProviderType
    @property
    def provider_id(self) -> Optional[str]
    @abstractmethod
    def capabilities(self) -> list[AdapterCapability]
    @abstractmethod
    def collect(self, ...) -> RawProviderSnapshot
    @abstractmethod
    def collect_safe(self, ...) -> RawProviderSnapshot
```

### 4.2 Kubernetes Adapter (fixture 기반)

- API: Kubernetes API (CoreV1Api)
- Fixture format: K8s API JSON (V1Node, V1Pod, V1Service, V1PersistentVolume, V1Namespace)
- Capabilities: PLATFORM, CLUSTER, NODE, EXECUTION_ENVIRONMENT, NETWORK, STORAGE
- Relationships: Pod→Node (spec.nodeName = DIRECT), Service→Pod (selector = DERIVED)
- Health: Node conditions → HEALTHY/UNHEALTHY/UNKNOWN

### 4.3 OpenStack Adapter (fixture 기반)

- API: OpenStack REST API
- Fixture format: OpenStack API JSON (os-hypervisors, compute/servers, network/v2.0/networks, volume/v3/volumes)
- Capabilities: PLATFORM, CLUSTER, NODE, EXECUTION_ENVIRONMENT, NETWORK, STORAGE
- Relationships: Server→Hypervisor (OS-EXT-SRV-ATTR = DIRECT), Volume→Server (attachments = DIRECT)
- Health: Hypervisor state/status, Server status → HEALTHY/UNHEALTHY/UNKNOWN

### 4.4 WRCP에 필요한 정보 (모두 UNKNOWN)

| Required Information | K8s | OpenStack | WRCP |
|---------------------|-----|-----------|------|
| API interface type | REST (K8s API) | REST (OpenStack API) | UNKNOWN |
| API endpoints | /api/v1/nodes, ... | /os-hypervisors, ... | UNKNOWN |
| Object model | V1Node, V1Pod, ... | Hypervisor, Server, ... | UNKNOWN |
| Authentication | kubeconfig | keystone token | UNKNOWN |
| Fixture format | K8s API JSON | OpenStack API JSON | NONE EXISTS |
| Canonical entity mapping | Node→Node, Pod→EE | Hypervisor→Node, Server→EE | UNKNOWN |
| Relationship evidence | spec.nodeName, selector | OS-EXT-SRV-ATTR, attachments | UNKNOWN |
| Health/status semantics | Node conditions | Hypervisor state, Server status | UNKNOWN |
| Client library | kubernetes python | (fixture-based) | UNKNOWN |
| Sample responses | Available (fixtures) | Available (fixtures) | NONE EXISTS |
   - "Implementation deferred until spec."


---

## 5. 구현 차단 원인

### 5.1 핵심 차단 조건

| # | Blocking Condition | Status | Impact |
|---|-------------------|--------|--------|
| 1 | WRCP API interface (REST/CLI/SDK) 미정의 | UNKNOWN | Adapter 구현 불가 |
| 2 | WRCP object model 미정의 | UNKNOWN | Normalizer 구현 불가 |
| 3 | WRCP authentication 방식 미정의 | UNKNOWN | Client 연결 불가 |
| 4 | WRCP fixture / sample response 부재 | NOT_FOUND | Fixture 기반 테스트 불가 |
| 5 | WRCP-to-canonical entity mapping 미정의 | UNKNOWN | Canonical 변환 불가 |
| 6 | WRCP relationship evidence 미정의 | UNKNOWN | 관계 생성 불가 |
| 7 | WRCP health/status semantics 미정의 | UNKNOWN | Health extractor 구현 불가 |
| 8 | WRCP 정체성 모호 (Wind River? CaaS Recovery?) | AMBIGUOUS | 요구사항 불명확 |

### 5.2 기존 문서의 차단 선언

Phase 13 design 문서들이 이미 동일한 결론을 내렸다:

> "WRCP interface 정의 없음 — REST/CLI/SDK/기타 — WRCP 팀과 협의 또는 문서 요청 필요"

> "WRCP API spec UNKNOWN/DEFERRED. No endpoint/CLI/schema guessing, no fake WRCP adapter."

> "실제 interface/class 파일 생성하지 않음."

---

## 6. 안전성 준수

- WRCP 리소스 생성·수정·삭제 금지 준수 (구현 시도 없음)
- 실제 운영 명령 실행 금지 준수 (구현 시도 없음)
- Operations/Recovery execute 경로 추가 금지 준수 (구현 시도 없음)
- 자격 증명, 환경 변수, 인증서, kubeconfig 변경 안 함
- 비밀 정보 노출 없음
- 새 의존성 추가 없음
- 기존 테스트 약화·삭제 없음
- test_is_due_past 기존 실패 수정 안 함
- Phase 29 미착수

---

## 7. 테스트 결과

### 기존 WRCP enum 관련 테스트 (모두 통과)

```
tests/test_provider_adapter.py::TestProviderTypeValidation::test_all_provider_types_supported[WRCP] PASSED
tests/test_provider_adapter.py::TestProviderNeutralContract::test_snapshot_for_wrcp PASSED
tests/test_platform_operations.py::TestCrossPlatform::test_wrcp_operation_contract PASSED
tests/test_platform_visibility.py::TestCrossPlatformAlertContract::test_alert_for_each_provider[WRCP] PASSED
```

이 테스트들은 WRCP adapter를 테스트하는 것이 아니라, generic contract가
WRCP enum 값에서도 작동하는지 검증하는 것이다.

### 전체 회귀 테스트

```
1794 passed, 27 skipped, 1 failed
1 failed = test_scheduler.py::test_is_due_past (pre-existing, timing-dependent)
```

코드 수정이 없었으므로 회귀 없음.

---

## 8. 구현을 위해 필요한 추가 입력

WRCP Provider 구현을 시작하려면 다음 정보가 필요하다:

### REQUIRED (필수 — 없으면 구현 불가)

1. **WRCP API specification** — REST API endpoint 목록 또는 CLI command reference, Request/Response schema, API 버전 정보
2. **WRCP object model** — WRCP가 노출하는 객체 목록, 각 객체의 field 구조, 객체 간 관계 구조
3. **WRCP authentication specification** — 인증 방식, Credential 획득 방법, 갱신 주기
4. **WRCP sample API responses** — 각 endpoint의 실제 응답 예시 (fixture 구축용), 최소 1개 이상의 완전한 인벤토리 snapshot 예시
5. **WRCP-to-canonical entity mapping** — WRCP 객체 → Canonical entity 매핑, 각 매핑의 근거 (DIRECT/DERIVED evidence)

### RECOMMENDED (권장 — 있으면 구현 품질 향상)

6. WRCP test/sandbox environment 접근 권한
7. WRCP health/status semantics (status 값 → HealthStatus 매핑)
8. WRCP version compatibility 정보 (지원 버전 범위)

---

## 9. Modified Files

없음. 소스 코드 수정이 없었다.

## 10. New Files

- output/Phase28_WRCP_Investigation_Report.md — 본 보고서

## 11. New Dependencies

없음.