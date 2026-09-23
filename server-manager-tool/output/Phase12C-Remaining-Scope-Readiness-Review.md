# PHASE 12C — REMAINING SCOPE & IMPLEMENTATION READINESS REVIEW

## 📋 BASELINE

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD Commit | `9dbf469d7eb9e9e7c0d7bbe59fb77698bc0040e2` |
| Modified Files | `src/server_manager/alert/store.py` (Phase 12B) |
| Test Suite | 337 passed, 1 failed |
| Failed Test | `tests/test_scheduler.py::TestScheduleDefinition::test_is_due_past` (flaky time test) |

---

## ✅ PHASE 12A/12B IMPLEMENTATION VERIFICATION

### 1. AlertStore Transaction API

**Location**: `src/server_manager/alert/store.py`

| Method | Status | Notes |
|--------|--------|-------|
| `begin_transaction()` | ✅ Implemented | Idempotent, handles implicit transactions |
| `commit()` | ✅ Implemented | Respects `_in_transaction` flag |
| `rollback()` | ✅ Implemented | Resets `_in_transaction` flag |
| `_commit_if_standalone()` | ✅ Implemented | Only commits if not in explicit transaction |
| `_in_transaction` | ✅ Tracked | Initialized to `False` in `__init__` |

---

### 2. AlertEngine Transaction Ownership

**Location**: `src/server_manager/alert/engine.py:54-61`

```python
def evaluate(self, context: AlertEvaluationContext) -> AlertEngineResult:
    try:
        self.alert_store.begin_transaction()  # Line 55
        try:
            result = self.rule_engine.evaluate(context)  # Line 57
            self.alert_store.commit()  # Line 58
        except Exception:
            self.alert_store.rollback()  # Line 60
            raise
        return AlertEngineResult(success=True, evaluation_result=result)
    except Exception as e:
        return AlertEngineResult(success=False, error_message=str(e))
```

**Flow**: `AlertEngine.evaluate() → BEGIN → RuleEngine.evaluate() → COMMIT/ROLLBACK`

---

### 3. Snapshot Idempotency

**Location**: `src/server_manager/alert/rule_engine.py`

| Step | Location | Status |
|------|----------|--------|
| `_is_snapshot_evaluated()` | Line 71 | ✅ Inside transaction |
| `_register_evaluation()` | Line 77 | ✅ Inside transaction |
| `evaluation_log` UNIQUE constraint | `UNIQUE(server_id, snapshot_id)` | ✅ Maintained |

---

### 4. Fingerprint Active-Alert Duplicate Check

**Location**: `src/server_manager/alert/rule_engine.py:185-210`

**Flow**: `get_alert_by_fingerprint() → UPDATE or INSERT → COMMIT`

**Status**: ✅ Check and mutation inside same AlertEngine transaction

**Schema**:

---

## 🎯 NEXT PHASE CANDIDATES CLASSIFICATION

### GROUP 1 — MUST IMPLEMENT BEFORE PRODUCTION

| Item | Reason | Priority |
|------|--------|----------|
| **12F: Fingerprint Concurrent Dedup** | Data integrity risk under concurrent evaluation | CRITICAL |
| **Recovery Verification** | Alert evaluation may be skipped on crash | HIGH |

---

### GROUP 2 — PHASE 12 IMPLEMENTABLE FEATURES

| Item | Scope | Dependencies |
|------|-------|--------------|
| **Alert API (12C)** | 5 endpoints (list, get, ack, resolve, server alerts) | None |
| **Alert Lifecycle Operations** | ACK, RESOLVE via API | Alert API |
| **Minimum Authorization** | API key or token-based auth | Alert API |
| **PARTIAL Collection Policy** | Define and implement PARTIAL semantics | Schema change |

---

### GROUP 3 — DEFER TO LATER PHASES

| Item | Reason | Suggested Phase |
|------|--------|-----------------|
| Notification | Out of scope for alert management | Phase 13+ |
| Advanced Retry | Requires orchestration complexity | Phase 13+ |
| Metrics/Observability | Operational concern | Phase 14+ |
| Distributed Coordination | Over-engineering for single-node | Phase 15+ |

---

## 🔍 PHASE 12F POSITIONING

**Key Questions**:

1. **Should 12F be implementation-first?** → ❌ NO — Test design must come first
2. **Is concurrent READ-ONLY test design needed?** → ✅ YES
3. **Should SQLite connection topology be verified first?** → ✅ YES
4. **Is current transaction boundary sufficient?** → ❌ NO (single-threaded only)
5. **Which solution to choose?** → Decision deferred until after test design

**Recommendation**: 
```
12F-PHASE 1: Concurrent test design (READ-ONLY)
12F-PHASE 2: SQLite topology verification (READ-ONLY)
12F-PHASE 3: Solution implementation
```

---

## 📝 PHASE 12C RECOMMENDATION

```text
PHASE 12C RECOMMENDATION

Status: [READY_FOR_IMPLEMENTATION]

Recommended scope:
- Alert API endpoints (5 endpoints)
- Minimum authorization boundary (API key)
- Alert API tests

Reason:
- Alert management requires API for operational use
- Transaction boundary (12B) provides atomic evaluation foundation
- API implementation is independent of concurrent deduplication (12F)
- No schema changes required

Must not change:
- evaluation_log UNIQUE constraint
- fingerprint schema (no UNIQUE constraint yet)
- transaction boundary (12B)
- BEGIN mode

Dependencies:
- Phase 12A: AlertStore Transaction API ✅
- Phase 12B: AlertEngine Transaction Ownership ✅

Next phase:
- Phase 12D: Alert Recovery Verification
- Phase 12E: PARTIAL Collection Policy
- Phase 12F: Concurrent Fingerprint Deduplication
```

---

## ✅ CONCLUSION

**Phase 12A/12B**: ✅ Complete and verified

**Remaining Critical Items**:
1. **12F** — Concurrent fingerprint deduplication (CRITICAL)
2. **Recovery** — Crash-before-evaluation handling (HIGH)

**Phase 12C Candidate**: Alert API implementation (READY)

**Implementation Order**: `12C → 12D → 12E → 12F`

- `UNIQUE(fingerprint)`: ❌ NOT present (intentional, deferred to 12F)
- Partial unique index: ❌ NOT present
- Active-alert key table: ❌ NOT present
- Application lock: ❌ NOT present

---

## 📊 INCOMPLETE ITEMS

### A. PARTIAL Collection Policy

**Status**: ⚠️ **BINARY ONLY** (SUCCESS/FAILED)
- `collection_success: bool` only
- `PARTIAL` policy: NOT IMPLEMENTED

---

### B. Alert API Endpoints

**Required**:
```
GET  /api/v1/alerts
GET  /api/v1/alerts/{id}
POST /api/v1/alerts/{id}/ack
POST /api/v1/alerts/{id}/resolve
GET  /api/v1/servers/{id}/alerts
```

**Status**: ❌ **NOT IMPLEMENTED**

---

### C. API Authorization

**Status**: ❌ **NOT IMPLEMENTED**

---

### D. Alert Recovery

**Status**:
- `evaluation_log` idempotency: ✅ Implemented
- Explicit alert recovery mechanism: ❌ NOT IMPLEMENTED
- Crash-before-evaluation handling: ⚠️ NOT VERIFIED

---

### E. Alert Evaluation Retry

**Status**: ❌ **NOT IMPLEMENTED** (implicit via scheduler cycle only)

---

### F. Concurrent Evaluation Tests

**Status**: ❌ **NOT COVERED**

---

### G. Fingerprint Concurrent Dedup

**Status**: ⚠️ **NOT PROVEN SAFE**

- Transaction boundary: ✅ IMPLEMENTED (12B)
- Concurrent safety: ❌ NOT CLAIMED (deferred to 12F)
