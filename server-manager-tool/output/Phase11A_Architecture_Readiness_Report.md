# Phase 11A — Alert Engine Architecture & Readiness Review

**Review Date:** 2026-09-21  
**Repository:** Server Manager (Server Management Platform)  
**Review Type:** READ-ONLY Architecture & Readiness  

---

## 1. Review Scope

본 검토는 Phase 11 — Alert Engine 구현 전, 현재 architecture 를 기반으로 다음을 확인한다:

- Alert Engine 이 기존 domain boundary 를 깨뜨리지 않는가?
- Schema v1.0 을 변경하지 않고 구현 가능한가?
- 기존 dependency direction 을 유지할 수 있는가?
- SQLite concurrency 에 미치는 영향은 무엇인가?
- Scheduler (Phase 10B/10C/10D) 와 어떻게 integration 되는가?

**주의:** 본 단계에서는 Alert Engine 을 구현하지 않는다.

---

## 2. Baseline

### Repository State
- **Branch:** main
- **HEAD:** ec6c5e481d5c72a2c96258467c50fefdf341cd78
- **Working Tree:** clean
- **Latest Commit:** Auto commit: 2026-09-21 19:45:14 (Phase 10D 완료 후 추가 작업)

### Test Baseline
- **Full Suite:** 277 passed / 1 failed (test_is_due_past — 기존 flaky test)
- **Scheduler Tests:** 38 passed / 1 failed
- **Phase 10D Recovery:** 10/10 passed

---

## 3. Current Architecture

### Repository Structure (실제 source 기준)

```
src/server_manager/
├── api/              # REST API
├── collectors/       # Hardware/OS collection
├── dashboard/        # Dashboard query service
├── models/           # Domain models (enums, inventory)
├── normalizers/      # Raw → Canonical
├── orchestrator/     # Pipeline orchestration
├── scheduler/        # Phase 10B/10C/10D scheduler
├── store/            # Inventory persistence
└── verifiers/        # Cross-source verification
```

### Domain Boundaries (FACT)

| Domain | Responsibility | Key Models |
|--------|----------------|------------|
| **collectors** | Raw data collection | SourceResult |
| **normalizers** | Raw → Canonical | ServerInventory |
| **verifiers** | Cross-source verification | VerificationResult |
| **orchestrator** | Pipeline orchestration | OrchestrationResult |
| **store** | Persistent storage | InventorySnapshot |
| **scheduler** | Time-based execution | ScheduleExecution |
| **dashboard** | Query/Presentation | ServerSummary |
| **api** | REST interface | CollectResponse |

---

## 4. Schema v1.0 Summary

**ServerInventory** 는 17 area 로 FROZEN:

1. Identity, 2. Topology, 3. CPU, 4. Memory, 5. GPU, 6. Storage, 7. Network, 8. Management, 9. OS, 10. Virtualization, 11. Containers, 12. DevelopmentEnvironment, 13. Compute, 14. **Health**, 15. Workload, 16. PowerThermal, 17. Verification

**HealthStatus Enum** (enums.py):
```python
class HealthStatus(str, Enum):
    OK = "OK"
    WARNING = "Warning"
    CRITICAL = "Critical"
    UNKNOWN = "Unknown"
```

**VerificationStatus Enum**:
```python
class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    DISCREPANCY = "DISCREPANCY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
```

---

## 5. Alert Domain Boundary

### Key Decisions (RECOMMENDATION)

| Question | Answer |
|----------|--------|
| Alert 가 Inventory field 인가? | **NO** — Alert 는 별도 domain entity |
| Alert 가 Event 와 동일한가? | **NO** — Alert 는 지속 조건 + 수명 주기 |
| Alert 와 Snapshot 관계? | Snapshot → Alert trigger source |
| Alert 가 Verification discrepancy 표현? | **NO** — Discrepancy 는 trigger, Alert 는 lifecycle 관리 |
| Alert 가 Scheduler failure 포함? | **NO** — Scheduler failure 는 operational issue |

### Architecture Principle

```
Inventory = 현재 상태 (state)
Alert     = 이상 감지 사건 (event with lifecycle)

Alert Engine = 별도 domain module
  - Inventory schema 변경하지 않음 (Schema v1.0 보호)
  - AlertStore = 별도 SQLite DB
  - Dependency: AlertEngine → InventoryStore (one-way)
```

---

## 6. Alert Lifecycle (RECOMMENDATION)

```
condition detected → DETECTED → OPEN → ACKNOWLEDGED → RESOLVED → CLOSED
```

| State | Description | Automatic Transition |
|-------|-------------|---------------------|
| **DETECTED** | Initial detection | → OPEN (if persists) |
| **OPEN** | Confirmed alert | → ACKNOWLEDGED (manual) |
| **ACKNOWLEDGED** | Being handled | → RESOLVED (manual) |
| **RESOLVED** | Condition cleared | → CLOSED (auto after N collections) |

---

## 7. Alert Severity (RECOMMENDATION)

```
INFO     — Informational
WARNING  — Requires attention
CRITICAL — Immediate action required
```

**HealthStatus 재사용 가능** (현재: OK, WARNING, CRITICAL, UNKNOWN)

---

## 8. Rule Evaluation Architecture

### Rule Types
1. **Threshold Rules** — `HealthStatus == CRITICAL`
2. **Duration Rules** — `Condition persists for N collections`
3. **State Transition Rules** — `Health OK → CRITICAL`
4. **Verification Discrepancy Rules** — `discrepancy_count > 0`
5. **Collection Failure Rules** — `consecutive_failures >= N`

### Rule Location (RECOMMENDATION)

```
Alert Engine (독립적 위치)
  ↓
InventoryStore (snapshot 조회)
SchedulerStore (execution failure 조회)

Collector/Normalizer/Verifier 의존하지 않음 (dependency 역전 방지)
```

---

## 9. Deduplication / Fingerprint (RECOMMENDATION)

```python
alert_fingerprint = hash(
    server_id,
    alert_type,      # "HEALTH_CRITICAL", "VERIFICATION_DISCREPANCY"
    resource,        # "cpu", "memory", "storage"
    condition,       # "health == CRITICAL"
)
```

**Deduplication Logic:**
- OPEN alert 존재 시 동일 fingerprint → update (recovery_count++, last_seen_at)

---

## 14. Collection Failure Handling (RECOMMENDATION)

```
Single Failure       → Alert 생성 안 함 (transient, log only)
Consecutive (N=3 회)  → Alert WARNING
Persistent (M=5 회)   → Alert CRITICAL (escalation)
```

---

## 15. Verification Discrepancy Handling (RECOMMENDATION)

```
Single Discrepancy        → Alert 생성 안 함 (informational)
Critical Field            → Alert WARNING
Multiple (N 개 이상)       → Alert WARNING
Hardware Discrepancy      → Alert CRITICAL
OS Discrepancy            → Alert WARNING
```

---

## 16. REST API Boundary (RECOMMENDATION)

```
GET    /api/v1/alerts
GET    /api/v1/alerts/{alert_id}
POST   /api/v1/alerts/{alert_id}/acknowledge
POST   /api/v1/alerts/{alert_id}/resolve
```

기존 API convention 따름 (ErrorResponse, pagination)

---

## 17. Dashboard Integration (RECOMMENDATION)

**DashboardSummary 확장:**
- `active_alerts: int`
- `critical_alerts: int`
- `warning_alerts: int`

**주의:** Dashboard 는 Alert canonical state 소유하지 않음 (query 만)

---

## 18. Security Boundary (RECOMMENDATION)

**Alert 에 포함될 정보:**
- ✓ server_id, hostname, IP
- ✓ hardware/OS state
- ✓ error details (sanitized)

**Alert 에 포함되지 않아야 할 정보:**
- ✗ credentials
- ✗ raw collector output
- ✗ command output
- ✗ stack traces

---

## 19. Observability (RECOMMENDATION)

**Metrics:**
- `alerts_created`, `alerts_deduplicated`, `alerts_resolved`
- `alert_evaluation_failures`
- `rule_evaluation_duration_ms`

**Logging:**
```python
logger.info("Alert created: %s (server=%s, severity=%s)", alert_id, server_id, severity)
```

---

## 20. External Integration Boundary

**Future Phase:**
- Notification channels (Email, Slack, PagerDuty)
- External management systems (TBMS, Switch, CaaS)

**Current Phase:**
- Alert Engine 은 external system 의존하지 않음

---

## 21. Test Strategy (RECOMMENDATION)

1. Rule Evaluation
2. Fingerprint / Deduplication
3. Lifecycle
4. Severity
5. Persistence
6. Scheduler Integration
7. API
8. Security

---

## 22. Schema v1.0 Protection Gate

**Result: PASS**

```
Schema v1.0 modification NOT required

Alert Engine 은 ServerInventory schema 를 변경하지 않음.
Alert 은 별도 domain 으로 구현.
```

---

## 23. Dependency Direction Gate

**Result: PASS**

```
Alert Engine → InventoryStore (OK, one-way)
Alert Engine → SchedulerStore (OK, one-way)
No circular dependency
```

---

## 24. Architecture Risks

| ID | Severity | Area | Summary |
|----|----------|------|---------|
| A001 | HIGH | Deduplication | 복잡할 경우 Alert 누락/중복 |
| A002 | MEDIUM | Concurrency | SQLite lock contention 증가 |
| A003 | MEDIUM | Performance | Rule evaluation overhead |
| A004 | LOW | Lifecycle | State machine 복잡성 |
| A005 | LOW | Dashboard | Alert count inconsistency |

---

## 25. Readiness Gate

| Gate | Result |
|------|--------|
| A. Domain Boundary | PASS |
| B. Schema Compatibility | PASS |
| C. Alert Lifecycle | PASS_WITH_CONDITIONS |
| D. Severity Model | PASS |
| E. Rule Evaluation Architecture | PASS |
| F. Deduplication | PASS_WITH_CONDITIONS |
| G. Persistence | PASS |
| H. SQLite Concurrency | PASS_WITH_CONDITIONS |
| I. Scheduler Integration | PASS |
| J. Crash Recovery Interaction | PASS |
| K. Verification Integration | PASS |
| L. Collection Failure Handling | PASS |
| M. API Boundary | PASS |
| N. Dashboard Boundary | PASS |
| O. Security Boundary | PASS |
| P. Observability | PASS |
| Q. Test Strategy | PASS |
| R. Dependency Direction | PASS |
| S. External Integration Boundary | PASS |
| T. Scope Control | PASS |

---

## 26. Overall Architecture Gate

### **Result: READY_WITH_CONDITIONS**

### Conditions

1. **Alert Lifecycle 명확히 정의** — State transition table
2. **Fingerprint Algorithm 정의** — Hash components
3. **Rule Thresholds 정의** — Consecutive failures (N=3, M=5)
4. **AlertStore Schema 정의** — Table schema, indexes

---

## 27. Recommended Implementation Sequence

```
Phase 11A (Current) — Architecture & Readiness
        ↓
Phase 11B — Alert Domain Model
        ↓
Phase 11C — Alert Store / Persistence
        ↓
Phase 11D — Alert Evaluation Engine
        ↓
Phase 11E — Scheduler Integration
        ↓
Phase 11F — Alert API
        ↓
Phase 11G — Dashboard Integration
```

---

## 28. Final Decision

**PHASE 11A ARCHITECTURE REVIEW: READY_WITH_CONDITIONS**

### Summary

- ✅ Domain boundary 명확 (별도 Alert domain)
- ✅ Schema v1.0 보호 (Inventory schema 변경 없음)
- ✅ Dependency direction 유지 (circular dependency 없음)
- ✅ SQLite concurrency 관리 가능 (별도 DB)
- ✅ Scheduler integration 명확 (post-collection hook)
- ⚠️ 일부 design decision 필요 (조건 충족 시 구현 가능)

---

## 29. Safety Verification

- **Production server access:** NO
- **External TBMS access:** NO
- **Credentials exposed:** NO
- **Schema v1.0 modified:** NO
- **Production source modified:** NO
- **Test source modified:** NO
- **DB schema modified:** NO
- **Commit created:** NO

---

**Report Location:** `output/Phase11A_Architecture_Readiness_Report.md`  
**Review Completed:** 2026-09-21  
**Reviewer:** Cline SR (READ-ONLY verification)
- RESOLVED 후 동일 조건 → 새 Alert 생성
- ACKNOWLEDGED 상태 → update 만 수행

---

## 10. Persistence Architecture (RECOMMENDATION)

**Option B: 별도 AlertStore**

```python
AlertStore:
  - DB Path: `~/.server-manager/alerts.db`
  - Env Var: `ALERT_DB_PATH`
  - Pattern: Singleton (SchedulerStore 와 동일)
  - Schema: 별도 (Inventory schema 변경 없음)
```

---

## 11. SQLite / Concurrency (RECOMMENDATION)

1. **AlertStore 는 SCHEDULER_DB_PATH 와 별도 DB 사용** — Lock contention 분리
2. **Alert evaluation 은 Scheduler worker 외부에서 수행**
3. **Lock retry 공유** — `DEFAULT_LOCK_RETRY_COUNT` 재사용

---

## 12. Scheduler Integration (RECOMMENDATION)

**Option A: Post-Collection Hook**

```
Scheduler → Orchestrator → InventoryStore.save_snapshot()
                                     ↓
                              AlertEngine.evaluate(snapshot)
                                     ↓
                              AlertStore.save_alert()
```

---

## 13. Phase 10D Crash Recovery Interaction

**Recovery ≠ Alert**

- 정상적인 Recovery (1 회성) → Alert 생성 안 함
- Recovery 실패 (여러 번) → Alert 생성
- Recovery 후 collection 실패 → Alert 생성