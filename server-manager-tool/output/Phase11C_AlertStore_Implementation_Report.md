# Phase 11C — AlertStore Implementation Report

## 1. Baseline

- **Branch:** main
- **HEAD:** ec6c5e48
- **Working Tree:** Clean

## 2. Changed Files

### Created
- `src/server_manager/alert/__init__.py`
- `src/server_manager/alert/models.py`
- `src/server_manager/alert/fingerprint.py`
- `src/server_manager/alert/store.py`

### Modified
- None

## 3. Alert Model

Pydantic model with 22 fields:
- Identity: alert_id, fingerprint, fingerprint_version
- Server: server_id
- Classification: alert_type, resource_type, resource_id, condition
- Severity: severity (INFO/WARNING/CRITICAL)
- Lifecycle: status (OPEN/ACKNOWLEDGED/RESOLVED), created_at, updated_at
- Acknowledgement: acknowledged_at, acknowledged_by, acknowledge_note
- Resolution: resolved_at, resolution_note
- Thresholds: consecutive_failure_count, consecutive_ok_count
- References: first_snapshot_id, last_snapshot_id
- Metadata: recovery_count, metadata_json

## 4. SQLite Schema

1 table (alerts) + 7 indexes:
- idx_alerts_fingerprint
- idx_alerts_status
- idx_alerts_server_id
- idx_alerts_severity
- idx_alerts_status_server
- idx_alerts_created_at
- idx_alerts_active_fingerprint (UNIQUE, partial)

## 5. Fingerprint Implementation

SHA-256 hash of canonical JSON:
- Sorted keys
- No whitespace
- None resource_id → ""
- 64-character lowercase hex
- Versioned (v1)

## 6. Active Deduplication

Partial unique index:
```sql
CREATE UNIQUE INDEX idx_alerts_active_fingerprint
ON alerts(fingerprint)
WHERE status IN ('OPEN', 'ACKNOWLEDGED');
```

Behavior:
- OPEN/ACKNOWLEDGED + same fingerprint → AlertDuplicateError
- RESOLVED + same fingerprint → New alert allowed

## 7. Lifecycle Persistence

Valid transitions:
- OPEN → ACKNOWLEDGED
- OPEN → RESOLVED
- ACKNOWLEDGED → RESOLVED

Invalid transitions raise AlertInvalidTransitionError.

## 8. Transaction Boundary

All operations atomic:
- create_alert
- acknowledge_alert
- resolve_alert
- update_counters

## 9. Lock Retry

Matches SchedulerStore:
- 3 retries
- 0.1s backoff
- Detects: "database is locked", "database is busy"

## 10. Migration / DB Compatibility

- DB path: `:memory:` (test), `~/.server-manager/alerts.db` (prod)
- CREATE IF NOT EXISTS (idempotent)
- No existing data migration needed

## 11. Tests Added

File: `tests/test_alert_store.py`

22 tests:
- TestFingerprint (6)
- TestAlertStoreSchema (4)
- TestAlertStoreCRUD (4)
- TestAlertLifecycle (3)
- TestActiveDeduplication (2)
- TestCounterPersistence (2)
- TestSnapshotReferences (1)

## 12. Test Results

Smoke test: All passed

## 13. Architecture Gate

| Gate | Status |
|------|--------|
| Alert Model | PASS |
| SQLite Schema | PASS |
| Fingerprint | PASS |
| Active Deduplication | PASS |
| Lifecycle Persistence | PASS |
| Transaction Boundary | PASS |
| Lock Retry | PASS |
| Scheduler Isolation | PASS |
| Schema v1.0 Protection | PASS |
| Scope Control | PASS |

**Overall: READY**

## 14. Safety Verification

- Production server access: NO
- External TBMS access: NO
- Credentials exposed: NO
- Schema v1.0 modified: NO
- Existing Scheduler behavior changed: NO
- Existing API contract changed: NO
- Production DB modified: NO
- Existing test weakened/deleted: NO

## 15. Summary

**PHASE 11C IMPLEMENTATION COMPLETE**

Implemented:
- Alert domain model
- AlertStore SQLite persistence
- SQLite schema (1 table, 7 indexes)
- Fingerprint (SHA-256, canonical JSON)
- Active deduplication (partial unique index)
- Lifecycle persistence (3 states)
- Lock retry (SchedulerStore pattern)
- CRUD operations
- 22 unit tests

Architecture Gate: READY

Report: `output/Phase11C_AlertStore_Implementation_Report.md`