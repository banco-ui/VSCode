# PHASE 13 — CaaS Recovery Wizard (WRCP) Architecture & Integration Readiness Gate

## 1. Executive Summary

**Status**: `DESIGN_DECISION_REQUIRED`

WRCP (CaaS Recovery Wizard) 는 Server Manager 의 다음 구현 후보이나, **repository 내에 WRCP 관련 evidence 가 전혀 존재하지 않음**.

외부 시스템 (WRCP) 과 Server Manager 간의 integration contract 를 정의하기 위한 추가 설계 단계가 필요.

---

## 2. Baseline

| Item | Value |
|------|-------|
| Platform | Windows (win32) |
| Python | 3.12.10 |
| SQLite | 3.49.1 |
| Git Repository | N/A (local only) |
| WRCP Evidence | NOT_FOUND |

---

## 3. WRCP Evidence Audit

### Q1. WRCP 관련 코드/문서/설정 존재 여부

| Search Term | Result | Location |
|-------------|--------|----------|
| `WRCP` | NOT_FOUND | — |
| `wrcp` | NOT_FOUND | — |
| `CaaS` | NOT_FOUND | — |
| `caas` | NOT_FOUND | — |
| `recovery` | NOT_FOUND (source) | backup/restore test only |
| `restore` | FOUND (test only) | `test_store.py::TestBackupRestore` |
| `failover` | NOT_FOUND (source) | backup conversation history only |
| `rollback` | NOT_FOUND | — |
| `provision` | FOUND (context only) | usm-automation backup files |
| `redeploy` | NOT_FOUND | — |

**판정**: Repository source code 에 WRCP 관련 evidence 없음.

---

### Q2. WRCP Interface

---

## 4. 책임 경계 (Server Manager vs WRCP)

### Q4-Q5. 책임 경계

| Responsibility | Server Manager | WRCP | Unknown | 근거 |
|----------------|:--------------:|:----:|:-------:|------|
| Server inventory | ✅ | | | InventoryStore 존재 |
| Server health verification | ✅ | | | Orchestrator + Verifiers 존재 |
| Recovery request | | | ✅ | interface 정의 필요 |
| Recovery execution | | ✅ | | WRCP 외부 시스템 가정 |
| Operation tracking | | | ✅ | interface 정의 필요 |
| Recovery state | | | ✅ | interface 정의 필요 |
| Retry | | | ✅ | semantics 정의 필요 |
| Rollback | | | ✅ | semantics 정의 필요 |
| Recovery validation | ✅ | | | 기존 Verifiers 재사용 가능 |
| Alert generation | ✅ | | | AlertEngine 존재 |
| Audit/history | ✅ | | | InventoryStore append-only |
| Authentication | | | ✅ | credential boundary 정의 필요 |
| Credential storage | | | ✅ | security policy 정의 필요 |

---

### Q6. Authentication / Credential Boundary

**확인된 evidence**:

| Credential Type | Location | Usage |
|-----------------|----------|-------|
| Redfish | Test fixtures only | Collection source |
| SSH | Test fixtures only | Collection source |
| IPMI | Test fixtures only | Collection source |
| SNMP | Test fixtures only | Collection source |

**WRCP Credential**: NOT_FOUND

**판정**: WRCP authentication 방식 및 Server Manager 의 credential 소유 여부 정의 필요.

---

### Q7. Recovery Operation 상태/결과 Authoritative Source

**판정**: UNKNOWN

두 가지 설계 후보:

```
후보 A: WRCP authoritative
  Server Manager → WRCP (request)
  WRCP → Server Manager (callback/webhook)
  WRCP: operation state 저장
```

```
후보 B: Server Manager authoritative
  Server Manager → WRCP (request)
  Server Manager → WRCP (poll status)
  Server Manager: operation state 저장

---

## 5. 기존 Server Manager Architecture 와 Integration Point

### 5.1 기존 구성요소 WRCP 관련성

| 구성요소 | WRCP 관련성 | 근거 |
|----------|:-----------:|------|
| InventoryStore | DIRECTLY_RELEVANT | recovery 대상 server inventory |
| Orchestrator | INDIRECTLY_RELEVANT | collection/verification 전용 |
| Scheduler | DIRECTLY_RELEVANT | recovery scheduling 가능 |
| AlertEngine | DIRECTLY_RELEVANT | recovery trigger/alert linkage |
| AlertStore | DIRECTLY_RELEVANT | recovery alert tracking |
| DashboardQueryService | INDIRECTLY_RELEVANT | recovery status query |
| API layer | DIRECTLY_RELEVANT | WRCP integration API boundary |
| ServerDefinition | DIRECTLY_RELEVANT | recovery target definition |
| CollectionPolicy | INDIRECTLY_RELEVANT | recovery policy 와 유사 |
| VerificationResult | DIRECTLY_RELEVANT | post-recovery validation |
| ComputeEligibility | NOT_RELEVANT | compute allocation 전용 |

---

### 5.2 Integration Architecture 후보

#### 후보 A: API Adapter Pattern (권장)

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       v
┌─────────────────────────────────┐
│  Server Manager API             │
│  /api/v1/servers/{id}/recover   │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  Recovery Service (new)         │
│  - RecoveryRequest 생성         │
│  - Operation tracking           │
│  - WRCP adapter                 │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  WRCP Client Adapter            │
│  - REST / CLI / SDK             │
│  - Authentication               │
│  - Request/Response mapping     │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  WRCP (External)                │
└─────────────────────────────────┘
```

#### 후보 B: Scheduler Integration Pattern

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       v
┌─────────────────────────────────┐
│  Server Manager API             │
│  /api/v1/schedules              │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  Scheduler                      │
│  - Schedule execution           │
│  - Recovery job dispatch        │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  Recovery Worker (new)          │
│  - WRCP integration             │
│  - Status polling               │
└──────┬──────────────────────────┘
       │
       v

---

## 6. 기존 재사용 가능 코드

| 구성요소 | 재사용 가능성 | 근거 |
|----------|:-------------:|------|
| HTTP client | EXISTING_AND_REUSABLE | FastAPI HTTP stack |
| subprocess wrapper | NOT_FOUND | — |
| SSH client | NOT_FOUND | collectors only |
| credential provider | NOT_FOUND | — |
| retry utility | EXISTING_AND_REUSABLE | AlertStore lock retry |
| operation tracking | EXISTING_BUT_NOT_SUFFICIENT | Scheduler execution tracking |
| background worker | EXISTING_BUT_NOT_SUFFICIENT | Scheduler worker |
| scheduler | EXISTING_AND_REUSABLE | SchedulerStore + Scheduler |
| logging | EXISTING_AND_REUSABLE | Python logging |
| error model | EXISTING_AND_REUSABLE | API ErrorResponse |
| API dependency injection | EXISTING_AND_REUSABLE | dependencies.py |

---

## 7. Evidence Table

| Finding | Evidence | Confidence | Impact |
|---------|----------|------------|--------|
| WRCP interface | NOT_FOUND | NOT_FOUND | HIGH |
| Authentication | NOT_FOUND | NOT_FOUND | HIGH |
| Recovery lifecycle | NOT_FOUND | NOT_FOUND | HIGH |
| Operation status | NOT_FOUND | NOT_FOUND | HIGH |
| Failure semantics | NOT_FOUND | NOT_FOUND | HIGH |
| Rollback | NOT_FOUND | NOT_FOUND | HIGH |
| Server Manager boundary | INFERRED (architecture analysis) | INFERRED | HIGH |
| Existing reusable code | CONFIRMED (code review) | CONFIRMED | MEDIUM |
| WRCP in repository | NOT_FOUND | NOT_FOUND | HIGH |

---

## 8. Readiness 판정

### **DESIGN_DECISION_REQUIRED**

**이유**:

1. **WRCP interface 정의되지 않음**
   - REST API / CLI / SDK 중 어떤 interface 를 제공하는지 알 수 없음
   - external evidence (문서, 명세, 협의) 필요

2. **책임 경계 불명확**
   - Operation tracking 을 누가 담당할지 정의 필요
   - Recovery state authoritative source 정의 필요

3. **Security boundary 불명확**
   - WRCP credential 을 Server Manager 가 소유하는지
   - 별도 integration layer 가 담당하는지 정의 필요

4. **Failure semantics 정의되지 않음**
   - timeout, retry, rollback, partial recovery 등 모든 시나리오 정의 필요

---

## 9. Blocking Conditions

| 조건 | 설명 | 해결 방법 |
|------|------|-----------|
| WRCP interface 정의 없음 | REST/CLI/SDK/기타 | WRCP 팀과 협의 또는 문서 요청 |
| Authentication 방식 없음 | API token / cert / 기타 | Security team 과 협의 |
| Operation lifecycle 정의 없음 | 상태 전이, 완료 조건 | WRCP team 과 설계 협의 |
| Credential boundary 없음 | 誰가 credential 소유 | Security architecture review |

---

## 10. Non-Blocking Conditions

| 조건 | 설명 | 영향 |
|------|------|------|
| WRCP 코드 repository 없음 | 외부 시스템 가정 | 설계만 가능, 구현 불가 |
| Test environment 없음 | WRCP mock/stub 필요 | Integration test 지연 |
| Historical baseline 없음 | Git unavailable | 성능 비교 불가 |

---

## 11. Next Step

### **NEXT = WRCP_DESIGN_GATE**

**권장 활동**:

1. **WRCP Interface 명세 확보**
   - REST API 문서
   - CLI command 참조
   - SDK API 참조
   - 또는 WRCP team 과 interface 협의

2. **Responsibility Matrix 정의**
   - Server Manager 책임
   - WRCP 책임
   - Shared 책임

3. **Security Architecture Review**
   - Credential ownership
   - Authentication flow
   - Audit logging

4. **Integration Design Document 작성**
   - Architecture pattern 선택 (API Adapter 권장)
   - Request/Response schema
   - Error handling semantics
   - Operation lifecycle

5. **Mock/Stub Implementation Plan**
   - Integration test 를 위한 WRCP mock
   - Development 를 위한 stub

---

## 12. Summary

| Aspect | Status |
|--------|--------|
| WRCP Evidence | NOT_FOUND |
| Interface Definition | UNKNOWN |
| Responsibility Boundary | DESIGN_DECISION_REQUIRED |
| Security Boundary | DESIGN_DECISION_REQUIRED |
| Existing Reusable Code | CONFIRMED (sufficient) |
| Readiness | DESIGN_DECISION_REQUIRED |
| Next | WRCP_DESIGN_GATE |

---

## 13. Important Principle

> **WRCP 의 실제 동작을 추측하지 않는다.**

Repository evidence 가 없으면 `UNKNOWN` 또는 `NOT_FOUND` 로 기록한다.

구현 가능성보다 **책임 경계와 external interface 의 확실성**을 우선한다.

---

**End of Phase 13 WRCP Readiness Gate**