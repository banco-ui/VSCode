# Phase 11D — Alert Rule Engine Architecture & Readiness Review

**Review Date:** 2026-09-21  
**Repository:** Server Manager  
**Review Type:** READ-ONLY Architecture & Readiness  

---

## 1. Executive Summary

Phase 11C-Fix 완료 후 AlertStore 구현이 검증된 상태에서, **Alert Rule Engine**의 architecture 와 readiness 를 평가한다.

**Result: READY_WITH_CONDITIONS**

핵심 결정사항:
- **Observation:** 1 collection run = 1 observation (per server)
- **N=3:** 3 consecutive failures → OPEN
- **M=5:** 5 consecutive OKs → RESOLVED
- **Counter Authority:** Rule Engine (stateless evaluation) + AlertStore (atomic persistence)
- **Rule Architecture:** Simple if/elif rules (over-engineering avoided)
- **Idempotency:** snapshot_id 기반 중복 evaluation 방지
- **Scheduler Integration:** Post-collection hook (orchestrator completion)
- **Failure Isolation:** Alert evaluation failure 는 primary pipeline 에 영향 없음

---

## 2. Baseline

### Repository State
- **Branch:** main
- **HEAD:** c76e3c42b857d4f15760a6627edcfb81656fab35
- **Working Tree:** Modified (output 파일만)
- **Latest Commit:** Auto commit: 2026-09-21 22:45:14

### Test Baseline
- **Full Suite:** 309 passed / 1 failed
- **Known Failure:** `test_is_due_past` (existing flaky test, Phase 11D 와 무관)
- **AlertStore Tests:** 32 passed

---

## 3. Current Alert Architecture

### Module Structure (FACT)

```
src/server_manager/alert/
├── __init__.py          # Exports
├── models.py            # Alert, AlertStatus, AlertSeverity, AlertType, ResourceType
├── fingerprint.py       # create_fingerprint, validate_fingerprint
└── store.py             # AlertStore (SQLite persistence)
```

### AlertStore API (FACT)

```python
class AlertStore:
    def create_alert(...) -> Alert  # Application-level deduplication
    def get_alert(alert_id: str) -> Alert
    def acknowledge_alert(alert_id, acknowledged_by, acknowledge_note) -> Alert
    def resolve_alert(alert_id, resolution_note) -> Alert
    def update_counters(alert_id, failure: bool, snapshot_id) -> Alert
    def get_all_alerts(limit, offset) -> list[Alert]
```

### Application-Level Deduplication (Phase 11C-Fix)

**Behavior:**
- OPEN + same fingerprint → AlertDuplicateError
- ACKNOWLEDGED + same fingerprint → AlertDuplicateError
- RESOLVED + same fingerprint → New alert created (new alert_id with UUID)

---

## 4. Phase 11C-Fix Verification Summary

### Changes Made

1. **Syntax Errors Fixed:** store.py 문법 오류 수정
2. **Application-Level Deduplication:** Partial unique index → Application logic
3. **Alert ID Generation:** RESOLVED alerts → UUID-based alert_id

### Test Results

- **AlertStore Tests:** 32/32 passed
- **Full Suite:** 309/310 passed (1 existing flaky test)

---

## 5. Rule Engine Boundary

### Responsibilities

| Responsibility | Owner | Rationale |
|----------------|-------|-----------|
| Observation input | Orchestrator | Collection completion trigger |
| Rule selection | Rule Engine | Condition matching logic |
| Condition evaluation | Rule Engine | Business logic |
| Fingerprint generation | Rule Engine | Alert identity |
| N=3 / M=5 threshold | Rule Engine | Stateful evaluation |
| AlertStore interaction | Rule Engine | Persistence |
| Counter persistence | AlertStore | Atomic update |
| Deduplication | AlertStore | create_alert responsibility |

### Key Design Decision

**Rule Engine 은 stateless evaluation + AlertStore 는 atomic persistence**

- Rule Engine: Business logic (N=3, M=5 判断)
- AlertStore: Atomic counter update, deduplication
- 경계 명확: Rule Engine 이 AlertStore API 사용 (단방향 dependency)

---

## 6. Evaluation Input Contract

### AlertEvaluationContext (PROPOSED)

```python
@dataclass
class AlertEvaluationContext:
    snapshot: ServerInventory
    snapshot_id: str
    collection_result: Optional[CollectionResult] = None
    verification_result: Optional[VerificationResult] = None
    execution_id: Optional[str] = None
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

### Q&A

**Q1: Rule Engine 이 raw collector result 를 직접 봐야 하는가?** → NO

**Q2: Canonical inventory snapshot 을 사용하는가?** → YES

**Q3: Verification discrepancy 는 어떤 source 를 기준으로 평가하는가?** → VerificationResult

**Q4: Collection failure 는 snapshot 이 없는 경우에도 평가할 수 있는가?** → YES

**Q5: 하나의 collection 에 여러 source failure 가 있으면 각각 Alert candidate 가 되는가?** → YES

**Q6: Alert Engine 은 OrchestrationResult 전체를 받아야 하는가?** → NO

**Q7: Scheduler execution context 가 필요한가?** → Optional (idempotency 용도)

---

## 7. Observation Definition

**Definition:**

```
1 observation = 1 collection run per server
```

**Rationale:**
- Collection 은 server 단위로 실행됨
- Batch collection (multiple servers) → multiple observations
- 각 observation 은 독립적인 N=3/M=5 카운터 가짐

---

## 8. N=3 Failure Threshold

### Semantics

```
consecutive_failure_count >= 3 → OPEN alert creation
```

### Reset Condition

```
Any OK observation → consecutive_failure_count = 0
```

---

## 9. M=5 Recovery Threshold

### Semantics

```
consecutive_ok_count >= 5 → RESOLVED alert
```

### Reset Condition

```
Any FAIL observation → consecutive_ok_count = 0
```

### RESOLVED → Reopen

```
RESOLVED 상태 + 동일 fingerprint FAIL × 3 → new OPEN alert (new alert_id)
```

---

## 10. Counter Authority

### Design Decision

**Option A: Rule Engine 계산 + AlertStore 저장**

**Rationale:**
- Rule Engine: Business logic (N=3, M=5 判断)
- AlertStore: Atomic persistence (lock retry, transaction)
- 경계 명확, 테스트 용이

### Race Condition Mitigation

**Current Guarantee:** Single-instance, multi-thread safe (lock retry).

---

## 11. Rule Architecture

### Design Decision

**Simple if/elif rules (not registry/strategy pattern)**

**Rationale:**
- Current scale: 5 alert types
- Over-engineering avoidance
- Easy to test and debug\"\"  
