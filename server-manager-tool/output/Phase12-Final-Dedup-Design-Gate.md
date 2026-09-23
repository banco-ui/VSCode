============================================================
PHASE 12 FINAL DEDUP DESIGN GATE
============================================================

## 1. BASELINE
branch: main
HEAD: 2f7d6fcba42ba514d2069d37fc7ca57a71390d78
working_tree: CLEAN
python: 3.12.10
sqlite: 3.x

## 2. CURRENT SCHEMA
alerts table:
  - alert_id TEXT PRIMARY KEY
  - fingerprint TEXT NOT NULL (NO UNIQUE)
  - status TEXT NOT NULL
  - ... (22 fields)

unique constraints: NONE on fingerprint
indexes: idx_alerts_fingerprint (REGULAR, NOT UNIQUE)
partial indexes: NONE

## 3. PHASE 11C HISTORY
attempted partial unique: YES
reason removed: "SQLite 호환성 문제" (Phase 11C report line 59)
replaced with: Application-level deduplication (line 60-61)
still applicable: YES

## 4. CURRENT DEDUP FLOW
lookup: rule_engine.py line 185-188 (SELECT active alert)
insert: store.py line 254-272 (INSERT + commit)
commit: INSIDE create_alert() line 272 (PROBLEM!)
transaction owner: AlertStore (each method commits)
## 6. STRATEGY COMPARISON

| Strategy | Active Dup | RESOLVED Reappear | Atomic | Suitable |
|----------|-----------|-------------------|--------|----------|
| A: GLOBAL UNIQUE | ✅ | ❌ BLOCKED | ✅ | ❌ |
| B: Partial UNIQUE | ✅ | ✅ | ✅ | ⚠️ (complex) |
| C: INSERT OR IGNORE (NO UNIQUE) | ❌ RACE | ✅ | ❌ | ❌ |
| D: App-level + Transaction | ⚠️ Small race | ✅ | ⚠️ | ✅ |
| E: active_alert_keys table | ✅ | ✅ | ✅ | ✅ |

## 7. RESOLVED → REAPPEARANCE
Lifecycle: OPEN → ACKNOWLEDGED → RESOLVED → NEW alert (same fingerprint)

Strategy A: FAILS (UNIQUE blocks)
Strategy B: WORKS (partial UNIQUE allows)
Strategy C: WORKS but no dedup
Strategy D: WORKS (app logic allows)
Strategy E: WORKS (key deleted on RESOLVE)

## 8. CONCURRENT INSERT ANALYSIS
Scenario: Two workers SELECT → INSERT same fingerprint

WITHOUT UNIQUE: Both INSERT succeed → DUPLICATE ALERTS ❌
WITH UNIQUE: First succeeds, second ignored → ONE alert ✅
WITH TRANSACTION: First commits, second SELECT finds it → ONE alert ✅

## 9. TRANSACTION INTERACTION
Current: AlertStore methods call commit() independently
Phase 12: AlertEngine owns transaction

REQUIRED:
1. AlertStore: Add begin/commit/rollback methods
2. AlertStore: Remove internal commit() calls
3. AlertEngine: Wrap evaluate() in transaction

## 10. API COMPATIBILITY
Alert API does NOT create alerts (system-generated only)
API only transitions lifecycle (ack, resolve)
NO CONFLICT with dedup mechanism

## 11. TEST COVERAGE
existing: test_resolved_allows_new_alert, TestActiveDeduplication ✅
missing: Concurrent evaluation, concurrent alert creation ❌

## 12. FINAL DESIGN

dedup mechanism: Strategy D - App-level dedup + AlertEngine Transaction

required: 
  - NO UNIQUE constraint (preserves lifecycle)
  - AlertEngine transaction ownership (closes race)
  - NO INSERT OR IGNORE (invalid without UNIQUE)

transaction owner: AlertEngine

resolved reappearance: Application logic allows (store.py line 246-249)

## 13. IMPLEMENTATION IMPACT
12A: AlertStore begin/commit/rollback methods
12B: AlertEngine evaluate() transaction wrapper
12C: NO INSERT OR IGNORE (remove from plan)
     Keep app-level dedup, transaction closes race

## 14. FINAL GATE

READY_WITH_DEDUP_DESIGN_CHANGE

REASON:
Phase 12 proposal "INSERT OR IGNORE + affected rows check" is INVALID.

INSERT OR IGNORE requires UNIQUE constraint to work.
- Without UNIQUE: INSERT OR IGNORE = regular INSERT (duplicates!)
- With GLOBAL UNIQUE: Blocks RESOLVED → reappearance (lifecycle violation)
- With PARTIAL UNIQUE: Removed in Phase 11C due to SQLite complexity

CORRECTED DESIGN:
✅ Keep application-level dedup (current logic correct)
✅ Implement AlertEngine transaction ownership (closes race window)
❌ DO NOT use INSERT OR IGNORE (invalid without UNIQUE)
❌ DO NOT add UNIQUE constraint (breaks lifecycle)

This design:
- Preserves RESOLVED → reappearance
- Closes race via transaction serialization
- Avoids SQLite partial unique complexity
- Minimal migration (no schema change)

## 15. SAFETY CONFIRMATION
Production code modified: NO
Test code modified: NO
Schema modified: NO
Database modified: NO
External systems accessed: NO
Credentials exposed: NO
============================================================
END OF PHASE 12 FINAL DEDUP DESIGN GATE
============================================================

race window: SELECT → INSERT (concurrent workers can both pass)

## 5. INSERT OR IGNORE VERDICT
WITHOUT UNIQUE: INSERT OR IGNORE = regular INSERT (DUPLICATES!)
WITH GLOBAL UNIQUE: Prevents duplicates BUT blocks RESOLVED → reappearance
WITH ACTIVE-ONLY UNIQUE: Correct BUT requires partial unique index

CRITICAL FINDING:
"INSERT OR IGNORE + affected rows check" is INVALID without UNIQUE constraint.
INSERT OR IGNORE only ignores when there's a conflict to ignore.
