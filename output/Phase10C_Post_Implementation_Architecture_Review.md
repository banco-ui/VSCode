# Phase 10C — Post-Implementation Architecture Review

## A. BASELINE

| 항목 | 값 |
|------|-----|
| Branch | `main` |
| HEAD | `a495314` |
| Working Tree | Modified (test file only) |
| Initial tests | 229 passed |
| Review test run #1 | **265 passed** |
| Review test run #2 | **265 passed** |

### Changed Files (Committed)

| File | Type | Purpose |
|------|------|---------|
| `src/server_manager/api/scheduler_schemas.py` | NEW | API schemas |
| `src/server_manager/api/scheduler_routes.py` | NEW | API routes |
| `src/server_manager/api/dependencies.py` | MODIFIED | DI for SchedulerStore |
| `src/server_manager/api/app.py` | MODIFIED | Router registration |
| `src/server_manager/scheduler/store.py` | MODIFIED | Execution query method |
| `tests/test_scheduler_api.py` | NEW | API tests (36 tests) |

---

## B. API VERIFICATION

All 10 endpoints verified:

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/api/v1/schedules` | ✅ Implemented |
| POST | `/api/v1/schedules` | ✅ Implemented |
| GET | `/api/v1/schedules/{schedule_id}` | ✅ Implemented |
| PUT | `/api/v1/schedules/{schedule_id}` | ✅ Implemented |
| DELETE | `/api/v1/schedules/{schedule_id}` | ✅ Implemented |
| POST | `/api/v1/schedules/{schedule_id}/enable` | ✅ Implemented |
| POST | `/api/v1/schedules/{schedule_id}/disable` | ✅ Implemented |
| GET | `/api/v1/schedules/{schedule_id}/executions` | ✅ Implemented |
| GET | `/api/v1/schedule-executions/{execution_id}` | ✅ Implemented |
| GET | `/api/v1/scheduler/status` | ✅ Implemented |

---

## C. ARCHITECTURE VERIFICATION

### Actual Dependency Flow

```
Client
  │
  ▼
FastAPI Router (/api/v1/schedules)
  │
  ▼
SchedulerStore (SQLite persistence)
  │
  ▼
ScheduleDefinition / ScheduleExecution (domain models)
```

### Boundary Verification

| Boundary | Status |
|----------|--------|
| API → SchedulerStore | ✅ Via dependency injection |
| SchedulerStore → Orchestrator | ✅ No direct dependency |
| SchedulerStore → Collector | ✅ No direct dependency |
| API → InventoryStore | ✅ No direct dependency |
| API → Collector/Normalizer/Verifier | ✅ No direct calls |

### No Reverse Dependencies

```python
# scheduler/ module does NOT import:
# - api.scheduler_routes
# - api.*

# api/ imports:
# - scheduler.store (SchedulerStore)
# - scheduler.models (ScheduleDefinition, ScheduleExecution)
```

**Verdict:** MATCH with design intent.

---

## D. SOFT DELETE VERIFICATION

### Actual Implementation

```python
# scheduler_routes.py:212-234
@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule(...):
    schedule = store.get_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, ...)
    
    # Soft delete: disable the schedule
    schedule.enabled = False
    schedule.updated_at = datetime.now(timezone.utc).isoformat()
    store.save_schedule(schedule)
```

### Semantics Analysis

| Aspect | Behavior |
|--------|----------|
| Database row removed | ❌ No |
| Schedule disabled | ✅ Yes |
| Execution history preserved | ✅ Yes |
| Schedule still queryable | ✅ Yes |
| Scheduler polling skips | ✅ Yes (enabled=False) |

### DELETE vs DISABLE Distinction

**Finding:** `DELETE /schedules/{id}` and `POST /schedules/{id}/disable` produce **identical state** (`enabled=False`).

**Impact:** Semantic ambiguity — DELETE does not provide additional value over DISABLE.

**Severity:** LOW (design choice, not a bug)

**Recommendation:** Document that DELETE is a soft delete (alias for disable + metadata).

---

## E. EXECUTION HISTORY PRESERVATION

### Verification

```python
# scheduler_routes.py:212-234
# Note: Execution history is preserved in schedule_executions table
# The schedule definition is disabled but not hard-deleted
```

### FK Constraint

```sql
CREATE TABLE schedule_executions (
    execution_id       TEXT PRIMARY KEY,
    schedule_id        TEXT NOT NULL,
    ...
    FOREIGN KEY (schedule_id) REFERENCES schedule_definitions(schedule_id)
);
```

**Verdict:** FK exists but no CASCADE DELETE — executions preserved.

### Running Execution Behavior

**Current Implementation:**

- DELETE does NOT cancel running executions
- Running executions complete normally
- Execution history preserved

**Verdict:** PASS (consistent with design)

---

## F. SCHEDULER STATUS

### Actual Response Fields

```python
# scheduler_routes.py:398-414
return SchedulerStatusResponse(
    enabled=False,       # Placeholder
    running=False,       # Placeholder
    worker_limit=2,      # Default from SchedulerConfig
    active_workers=0,    # Placeholder
    poll_interval=60,    # Default from SchedulerConfig
    last_poll_at=None,   # Placeholder
)
```

**Finding:** Current implementation is **placeholder** — does not reflect actual Scheduler runtime state.

**Severity:** MEDIUM

**Recommendation:** Phase 10D — inject actual Scheduler instance and report real state.

---

## G. DEPENDENCY INJECTION

### Actual Implementation

```python
# dependencies.py:67-75
def get_scheduler_store() -> SchedulerStore:
    """Get the SchedulerStore instance.
    
    Creates a fresh instance per request for thread safety in tests.
    """
    return SchedulerStore(":memory:")
```

**Finding:** Creates new `:memory:` SQLite database per request.

**Impact:** Each API request sees empty database in production.

**Severity:** CRITICAL

**Evidence:** Production API will not persist schedules across requests.

**Recommendation:** Fix to use shared database path (e.g., `./scheduler.db`) or singleton pattern.

---

## H. SQLITE CONCURRENCY

### Current State

| Aspect | Implementation |
|--------|----------------|
| Worker limit | 2 (Phase 10B) |
| Lock retry | 3 × 0.1s (Phase 10B) |
| Atomic claim | `INSERT OR IGNORE` (Phase 10B) |
| Test fixture | `check_same_thread=False` |

### API + Scheduler Interaction

| Scenario | Behavior |
|----------|----------|
| API CRUD + Scheduler polling | Separate transactions |
| API enable/disable + running execution | Disable doesn't cancel running |
| API delete + pending execution | Soft delete preserves execution |
| Concurrent API updates | SQLite row-level locking |

**Verdict:** PASS (consistent with Phase 10B design)

---

## I. SECURITY BOUNDARY

### Credential Safety

| Check | Status |
|-------|--------|
| Credentials in request | ✅ None |
| Credentials in response | ✅ None |
| Credentials in logs | ✅ None |
| Password/token/secret exposure | ✅ None |

### Authentication/Authorization

**Status:** Not implemented (deferred to global auth phase)

**Verdict:** Consistent with Phase 8 API boundary.

### Error Sanitization

| Check | Status |
|-------|--------|
| No traceback in response | ✅ |
| No SQLite internals leaked | ✅ |
| Generic error messages | ✅ |

---

## J. ERROR CONTRACT

### Actual Response Format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "...",
    "details": {}
  }
}
```

**Verdict:** Consistent with Phase 8 API convention.

### HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 OK | Read, enable, disable |
| 201 Created | Create schedule |
| 204 No Content | Delete schedule |
| 404 Not Found | Schedule/execution not found |
| 409 Conflict | Already enabled/disabled |
| 422 Validation Error | Schema validation failed |

**Verdict:** PASS (consistent with REST conventions)

---

## K. SCHEMA V1.0 PROTECTION

### Verification

| Schema | Changed |
|--------|---------|
| Canonical Inventory | ❌ No |
| Verification | ❌ No |
| Monitoring | ❌ No |
| Compute | ❌ No |
| Storage | ❌ No |

**Verdict:** Schema v1.0 unchanged.

---

## L. TEST QUALITY

### Test Categories

| Category | Tests |
|----------|-------|
| Route Registration | 10 |
| Schedule CRUD | 10 |
| Schedule Lifecycle | 6 |
| Execution History | 3 |
| Scheduler Status | 1 |
| List Schedules | 2 |
| Error Contract | 3 |
| Security | 2 |
| **Total** | **36** |

### Test Results

| Run | Passed | Failed |
|-----|--------|--------|
| Run #1 | 265 | 0 |
| Run #2 | 265 | 0 |

### Test Quality Findings

| Finding | Severity |
|---------|----------|
| Happy path coverage | ✅ Good |
| Negative path coverage | ✅ Good (404, 409, 422) |
| Error contract tests | ✅ Present |
| Security tests | ✅ Present |
| Concurrency tests | ❌ Missing |
| SQLite thread safety tests | ⚠️ Fixture-based only |
| Running execution + delete | ❌ Missing |
| Scheduler polling + API mutation | ❌ Missing |

---

## M. 10D COMPATIBILITY

### Current Capabilities

| Capability | Status |
|------------|--------|
| Persistent schedules | ✅ |
| Execution history | ✅ |
| `last_run_at` tracking | ✅ |
| `next_run_at` tracking | ✅ |
| Execution status | ✅ |

### Gaps for 10D

| Gap | Severity |
|-----|----------|
| Missed schedule detection | MEDIUM |
| Abandoned execution recovery | MEDIUM |
| Graceful shutdown | LOW |
| Multi-instance coordination | HIGH |

**Verdict:** Current persistence model is **sufficient** for 10D implementation.

---

## N. FINDINGS

| ID | Severity | Finding | Evidence | Impact | Recommendation | Phase |
|----|----------|---------|----------|--------|----------------|-------|
| **10C-F001** | CRITICAL | `get_scheduler_store()` creates new `:memory:` DB per request | `dependencies.py:75` | Production API will not persist schedules | Fix to use shared DB path or singleton | 10C fix |
| **10C-F002** | MEDIUM | Scheduler status is placeholder | `scheduler_routes.py:398-414` | Status endpoint returns static data | Inject actual Scheduler instance | 10D |
| **10C-F003** | LOW | DELETE vs DISABLE semantic duplication | Both produce `enabled=False` | API semantics ambiguity | Document soft delete behavior | Documentation |
| **10C-F004** | MEDIUM | Missing concurrency tests | No tests for API + Scheduler polling race | Undetected race conditions | Add concurrency tests | 10D |
| **10C-F005** | MEDIUM | Missing running execution + delete test | No test for delete during execution | Potential orphan execution | Add test case | 10D |

---

## O. ARCHITECTURE GATE

| 영역 | 판정 | 근거 |
|------|------|------|
| **API Contract** | PASS | All 10 endpoints implemented with consistent error contract |
| **Scheduler Boundary** | PASS | No direct Collector/Normalizer/Verifier calls |
| **Schedule CRUD** | PASS | CRUD operations functional |
| **Soft Delete Semantics** | PASS WITH CONDITIONS | Works, but DELETE ≡ DISABLE |
| **Execution History** | PASS | Preserved on delete, FK constraints intact |
| **Scheduler Status** | PASS WITH CONDITIONS | Placeholder implementation |
| **Dependency Injection** | FAIL | `:memory:` DB per request breaks persistence |
| **Persistence / Concurrency** | PASS | SQLite lock retry, atomic claim |
| **Security Boundary** | PASS | Credential safety verified |
| **Error Contract** | PASS | Consistent with Phase 8 |
| **Schema v1.0 Protection** | PASS | No changes to domain schema |
| **Test Quality / Stability** | PASS WITH CONDITIONS | 36 tests, but missing concurrency tests |
| **10D Compatibility** | PASS | Persistence model supports crash recovery |
| **Scope Control** | PASS | No 10D features implemented |

---

## P. OVERALL

**READY_WITH_CONDITIONS**

### 판정 이유

1. **All 10 API endpoints implemented and tested** — 36 tests passing
2. **Architecture boundary maintained** — No reverse dependencies
3. **Soft delete preserves execution history** — FK constraints intact
4. **CRITICAL: Dependency injection broken** — `:memory:` DB per request
5. **Scheduler status is placeholder** — Needs actual Scheduler instance
6. **Missing concurrency tests** — Race conditions not tested

### Required Fixes Before Production

1. **Fix `get_scheduler_store()`** — Use shared database path or singleton pattern
2. **Document DELETE semantics** — Clarify soft delete behavior
3. **Add concurrency tests** — API + Scheduler polling races

---

## Q. SAFETY CONFIRMATION

| 항목 | 상태 |
|------|------|
| Production code modified during review | ❌ NO |
| Test code modified during review | ❌ NO |
| Schema v1.0 modified during review | ❌ NO |
| Existing API contract modified | ❌ NO |
| TBMS accessed | ❌ NO |
| External server accessed | ❌ NO |
| Credentials accessed/exposed | ❌ NO |
| 10D implemented | ❌ NO |
| Multi-instance implemented | ❌ NO |
| Authentication implemented | ❌ NO |
| Commit created | ❌ NO |

---

## R. STATUS

**COMPLETE**

---

# END OF PHASE 10C POST-IMPLEMENTATION ARCHITECTURE REVIEW
