# PHASE 13 — WRCP INTEGRATION DESIGN GATE

## 1. Executive Summary

**Status**: `DESIGN_READY_FOR_EXTERNAL_CONTRACT`

본 Design Gate 는 Server Manager 가 외부 CaaS Recovery Wizard (WRCP) 와 연동하기 위해 필요한 **최소 Integration Contract 와 책임 경계**를 정의한다.

**핵심 원칙**: Unknown WRCP behavior must remain Unknown.

WRCP 의 실제 API 나 동작을 추측하지 않으며, Server Manager 측 integration 요구사항과 boundary 만 정의한다.

---

## 2. Baseline

| Item | Value |
|------|-------|
| Platform | Windows (win32) |
| Python | 3.12.10 |
| SQLite | 3.49.1 |
| Repository | server-manager-tool (local) |
| Phase 13 Readiness | DESIGN_DECISION_REQUIRED |

---

## 3. CONFIRMED — Server Manager 가 이미 소유하는 영역

### 3.1 기존 구성요소 WRCP Integration 관련성

| 구성요소 | 관련성 | WRCP Integration 과의 관계 |
|----------|:------:|:--------------------------|
| **InventoryStore** | DIRECTLY_RELEVANT | recovery 대상 server 식별, post-recovery inventory 비교 |
| **Orchestrator** | INDIRECTLY_RELEVANT | recovery 후 verification 에 재사용 가능 |
| **Scheduler** | DIRECTLY_RELEVANT | recovery scheduling, operation tracking 과 유사 패턴 |
| **AlertEngine** | DIRECTLY_RELEVANT | recovery alert, recovery completion alert 가능 |
| **AlertStore** | DIRECTLY_RELEVANT | recovery operation 상태 tracking 에 활용 가능 |

---

## 4. PROPOSED — Server Manager 측 Integration 설계 후보

### 4.1 Responsibility Matrix (Server Manager 관점)

| Responsibility | Server Manager | WRCP | UNKNOWN |
|----------------|:--------------:|:----:|:-------:|
| Server inventory | ✅ | | |
| Server health verification | ✅ | | |
| Recovery request creation | ✅ | | |
| Recovery execution | | ✅ | |
| Operation tracking | | | ✅ |
| Recovery state ownership | | | ✅ |
| Retry (transport) | ✅ | | |
| Retry (operation) | | | ✅ |
| Timeout detection | ✅ | | |
| Rollback | | | ✅ |
| Recovery validation | ✅ | | |
| Alert generation | ✅ | | |
| Audit/history (internal) | ✅ | | |
| Authentication | | | ✅ |
| Credential ownership | | | ✅ |
| Idempotency | | | ✅ |

### 4.2 Integration Boundary 후보

#### Candidate A: API Adapter Pattern (권장)

```
Client → Server Manager API → Recovery Service → WRCP Adapter → External WRCP
```

**장점**: 기존 API architecture 와 일관됨, WRCP interface 변경 격리, Testing 용이
**단점**: 새로운 service layer 필요, Adapter 유지보수 필요

#### Candidate B: Scheduler Integration Pattern

```

---

## 5. REQUIRED WRCP CAPABILITIES

| Capability | Required? | External Contract |
|------------|:---------:|:-----------------:|
| Recovery submission | REQUIRED | UNKNOWN |
| Operation identification | REQUIRED | UNKNOWN |
| Status retrieval | REQUIRED | UNKNOWN |
| Result retrieval | REQUIRED | UNKNOWN |
| Failure information | REQUIRED | UNKNOWN |
| Timeout behavior | REQUIRED | UNKNOWN |
| Idempotency | REQUIRED | UNKNOWN |
| Cancellation | OPTIONAL | UNKNOWN |
| Rollback | OPTIONAL | UNKNOWN |
| Validation | OPTIONAL | UNKNOWN |
| Audit | RECOMMENDED | UNKNOWN |

**Important**: 모든 External Contract 는 `UNKNOWN`.

---

## 6. REQUIRED SERVER MANAGER CAPABABILITIES

| Capability | Status |
|------------|:------:|
| Recovery request validation | REQUIRED_NEW_CAPABILITY |
| Target server identification | EXISTING |
| Current inventory lookup | EXISTING |
| Current verification lookup | EXISTING |
| Operation correlation | REQUIRED_NEW_CAPABILITY |
| Timeout monitoring | REQUIRED_NEW_CAPABILITY |
| Result normalization | REQUIRED_NEW_CAPABILITY |
| Recovery validation | EXISTING |
| Alert integration | EXISTING |
| Audit correlation | EXISTING_BUT_INSUFFICIENT |

---


---

## 8. OPERATION LIFECYCLE CONTRACT

### Required Lifecycle Semantics

| Semantic | Required? | External Contract |
|----------|:---------:|:-----------------:|
| Request accepted | REQUIRED | UNKNOWN |
| Operation identifier assigned | REQUIRED | UNKNOWN |
| Operation started | OPTIONAL | UNKNOWN |
| Operation running | OPTIONAL | UNKNOWN |
| Operation completed | REQUIRED | UNKNOWN |
| Operation failed | REQUIRED | UNKNOWN |
| Operation partially completed | OPTIONAL | UNKNOWN |
| Operation cancelled | OPTIONAL | UNKNOWN |
| Operation timed out | REQUIRED | UNKNOWN |
| Operation rolled back | OPTIONAL | UNKNOWN |

**Important**: 실제 WRCP 상태명은 외부 명세 확인 후 mapping.

---

## 9. FAILURE SEMANTICS CONTRACT

### Failure Cases

| Failure Case | Server Manager Detection | External Contract |
|--------------|:------------------------:|:-----------------:|
| Authentication failure | REQUIRED | UNKNOWN |
| Connection failure | EXISTING | N/A |
| Request rejection | REQUIRED | UNKNOWN |
| Invalid target | REQUIRED | UNKNOWN |
| Operation timeout | EXISTING | N/A |
| Operation failure | REQUIRED | UNKNOWN |
| Duplicate request | REQUIRED | UNKNOWN |
| Already-running recovery | REQUIRED | UNKNOWN |

### Required Failure Information

```
- failure_category
- operation_identifier
- target_server
- timestamp
- retryability
- terminal vs non-terminal
- recovery_state
```

---

## 10. RETRY SEMANTICS

| Retry Type | Responsibility |
|------------|:--------------:|
| Transport retry | Server Manager |
| Request retry | Server Manager |
| Status polling retry | Server Manager |

---

## 12. RECOVERY VALIDATION

```
WRCP Operation Result → Server Manager Recovery Validation
```

| Validation Check | Server Manager Capability |
|------------------|:-------------------------:|
| Server reachable | EXISTING |
| Inventory available | EXISTING |
| Hardware identity consistent | EXISTING |
| OS/runtime available | EXISTING |
| Verification successful | EXISTING |
| Expected service state | REQUIRED_NEW_CAPABILITY |
| Expected health state | REQUIRED_NEW_CAPABILITY |

---

## 13. ALERT INTEGRATION

### Recovery-Related Alert Candidates

| Alert Event | Status |
|-------------|:------:|
| Recovery requested | REQUIRED_NEW |
| Recovery started | REQUIRED_NEW |
| Recovery failed | REQUIRED_NEW |
| Recovery timed out | REQUIRED_NEW |
| Recovery partially completed | REQUIRED_NEW |
| Recovery succeeded, validation failed | REQUIRED_NEW |
| Recovery succeeded, validation passed | REQUIRED_NEW |

**현재 코드에 새 AlertType 추가하지 않음 — 설계 수준 검토.**

---

## 14. AUDIT / CORRELATION

### Correlation Identifiers

| Identifier | Status |
|------------|:------:|
| server_id | EXISTING |
| run_id | EXISTING |
| snapshot_id | EXISTING |
| alert_id | EXISTING |
| recovery_request_id | REQUIRED_NEW |
| external_operation_id | REQUIRED_NEW |

---

## 15. MOCK / STUB BOUNDARY

### Required Abstraction

```
RecoveryPort (interface):

---

## 17. IMPLEMENTATION ENTRY CRITERIA

| Criterion | Status | Blocking? |
|-----------|:------:|:---------:|
| External interface identified | NOT_STARTED | YES |
| Authentication boundary confirmed | NOT_STARTED | YES |
| Credential ownership confirmed | NOT_STARTED | YES |
| Recovery request contract confirmed | NOT_STARTED | YES |
| Operation lifecycle confirmed | NOT_STARTED | YES |
| Failure semantics confirmed | NOT_STARTED | YES |
| Idempotency semantics confirmed | NOT_STARTED | YES |
| Responsibility matrix approved | PROPOSED | NO |
| Adapter boundary approved | PROPOSED | NO |
| Test/sandbox strategy available | NOT_STARTED | YES |

---

## 18. Architecture Decision Summary

### CONFIRMED
- Server Manager 는 InventoryStore, Orchestrator, AlertEngine 보유
- 기존 API layer, dependency injection 재사용 가능
- Verification pipeline 재사용 가능

### PROPOSED
- API Adapter Pattern 이 최적 integration boundary
- Server Manager 가 recovery request initiator
- Server Manager 가 post-recovery validation 담당
- Correlation ID 로 operation tracking

### UNKNOWN / EXTERNAL CONTRACT REQUIRED
- WRCP interface type (REST/CLI/SDK)
- WRCP authentication mechanism
- WRCP operation lifecycle states
- WRCP error codes
- WRCP idempotency support
- Credential ownership

---

## 19. Final Design Gate Decision

### **DESIGN_READY_FOR_EXTERNAL_CONTRACT**

**이유**:
1. ✅ Server Manager 측 integration contract 설계 완료
2. ✅ Responsibility boundary 명확히 구분
3. ✅ Required capability 목록 정의
4. ✅ Preferred architecture pattern 제안
5. ✅ External evidence checklist 작성
6. ✅ Implementation entry criteria 정의

**다음 단계**: WRCP external contract 확보 및 대조

---

## 20. Blocking Conditions

| Condition | Resolution |
|-----------|------------|
| WRCP API spec unavailable | WRCP team contact |
| Authentication mechanism unknown | Security team + WRCP team |
| Credential ownership undefined | Security architecture review |
| Test environment unavailable | WRCP team sandbox request |

---

## 21. Next Step

### **EXTERNAL_CONTRACT_INVESTIGATION**

**활동**:
1. WRCP team contact → API/CLI specification 요청
2. Security team contact → Authentication/Credential policy 확인
3. WRCP sandbox environment 요청
4. Received specification 과 본 설계 문서 대조
5. Gap analysis → design adjustment

---

**End of Phase 13 WRCP Integration Design Gate**
  - submit(RecoveryRequest) → RecoverySubmissionResult
  - getStatus(OperationId) → OperationStatus
```

### Test Stub Requirements

- Configurable responses
- Configurable delays
- Configurable failures
- Operation state tracking
- Request recording

**실제 interface/class 파일 생성하지 않음.**

---

## 16. EXTERNAL EVIDENCE CHECKLIST

| Item | Priority |
|------|:--------:|
| WRCP API / CLI specification | REQUIRED |
| Authentication specification | REQUIRED |
| Credential management specification | REQUIRED |
| Recovery request schema | REQUIRED |
| Operation status specification | REQUIRED |
| Operation result specification | REQUIRED |
| Error code specification | REQUIRED |
| Timeout behavior | REQUIRED |
| Idempotency behavior | REQUIRED |
| Test/sandbox environment | REQUIRED |
| Retry behavior | RECOMMENDED |
| Cancellation behavior | RECOMMENDED |
| Rollback behavior | OPTIONAL |
| Audit/logging behavior | RECOMMENDED |
| Recovery operation retry | UNKNOWN |
| Rollback retry | UNKNOWN |

---

## 11. IDEMPOTENCY

| Concept | Status |
|---------|:------:|
| Recovery Request Identity | REQUIRED_NEW_CAPABILITY |
| Operation Identity | REQUIRED_NEW_CAPABILITY |
| Target Identity | EXISTING |
| Idempotency Key | REQUIRED_NEW_CAPABILITY |
| Duplicate Request Detection | REQUIRED_NEW_CAPABILITY |

**WRCP idempotency support 확인 필요.**
## 7. AUTHENTICATION BOUNDARY

| Question | Status |
|----------|:------:|
| Who authenticates to WRCP? | UNKNOWN |
| Who owns the credential? | UNKNOWN |
| Where is the credential stored? | UNKNOWN |
| Does Server Manager see raw credential? | UNKNOWN |
| How is credential rotation handled? | UNKNOWN |

**모든 항목은 Security team 과 WRCP team 협의 필요.**
Client → Server Manager API → Scheduler → Recovery Worker → External WRCP
```

**장점**: 기존 Scheduler 재사용, Background execution native 지원
**단점**: Recovery 가 schedule 로 제한됨, On-demand recovery 에 부적합

#### Candidate C: Alert-Triggered Pattern

```
AlertEngine → Recovery Trigger → External WRCP
```

**장점**: Automatic recovery native 지원
**단점**: Manual recovery 에 별도 경로 필요

### 4.3 Preferred Design Candidate

**PREFERRED_DESIGN_CANDIDATE = Candidate A (API Adapter Pattern)**

**이유**:
1. 기존 Server Manager API architecture 와 가장 일관됨
2. WRCP interface 변경에 대한 격리 제공
3. Scheduler/Alert 과 느슨한 결합
4. Testing 용이 (adapter mock)
5. On-demand + Scheduled recovery 모두 지원 가능

**단, 이는 구현 승인이 아니다.**
| **DashboardQueryService** | INDIRECTLY_RELEVANT | recovery status query 에 활용 가능 |
| **API layer** | DIRECTLY_RELEVANT | WRCP integration API boundary |
| **ServerDefinition** | DIRECTLY_RELEVANT | recovery target definition |
| **VerificationResult** | DIRECTLY_RELEVANT | post-recovery validation 에 직접 활용 |

### 3.2 기존 재사용 가능 코드

| 구성요소 | 재사용 가능성 |
|----------|:-------------:|
| HTTP client (FastAPI) | EXISTING_AND_REUSABLE |
| retry utility (AlertStore) | EXISTING_AND_REUSABLE |
| SchedulerStore | EXISTING_AND_REUSABLE |
| Python logging | EXISTING_AND_REUSABLE |
| API ErrorResponse | EXISTING_AND_REUSABLE |
| dependency injection | EXISTING_AND_REUSABLE |
| BEGIN IMMEDIATE transaction | EXISTING_AND_REUSABLE |