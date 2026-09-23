# Phase 12B - Current Transaction Flow Analysis

## Current Flow (Phase 12A state)

### AlertEngine.evaluate()
```
AlertEngine.evaluate(context)
    ↓
RuleEngine.evaluate(context)  ← No transaction boundary
    ↓
    1. _is_snapshot_evaluated(ctx)
         ↓
       SELECT FROM evaluation_log
         ↓
       if exists: return (duplicate)
    
    2. _register_evaluation(ctx)
         ↓
       INSERT INTO evaluation_log
         ↓
       self._commit_if_standalone()  ← Auto-commit (standalone)
    
    3. _handle_failure(...) - for each condition
         ↓
       get_alert_by_fingerprint()  ← SELECT
         ↓
       if exists:
           update_alert()  ← UPDATE + commit
       else:
           get_failure_tracking_count()  ← SELECT
           if count >= 3:
               create_alert()  ← INSERT + commit
           else:
               increment_failure_count()  ← UPDATE + commit
    
    4. _handle_ok_all(ctx)
         ↓
       reset_all_failure_tracking()  ← DELETE + commit
       list_alerts(status=OPEN)  ← SELECT
       for each alert:
           increment_ok_count()  ← UPDATE + commit
           if ok_count >= 5:
               resolve_alert()  ← UPDATE + commit
```

## Problem: Multiple Independent Transactions

Each AlertStore method currently:
1. Opens implicit transaction (SQLite default)
2. Performs operation
3. Calls _commit_if_standalone() → commits immediately
4. Transaction ends

Result: **No atomic evaluation boundary**

## Phase 12B Target Flow

```
AlertEngine.evaluate(context)
    ↓
alert_store.begin_transaction()  ← NEW
    ↓
RuleEngine.evaluate(context)
    ↓
    1. _is_snapshot_evaluated(ctx)
    2. _register_evaluation(ctx)  ← No commit
    3. _handle_failure(...)  ← No commit
    4. _handle_ok_all(ctx)  ← No commit
    ↓
alert_store.commit()  ← NEW - single commit for all
```

## Duplicate Check Locations

### 1. Snapshot Duplicate (Idempotency)
**Location**: `RuleEngine._is_snapshot_evaluated()`
**Current**: SELECT only (no mutation)
**Phase 12B**: Inside AlertEngine transaction ✓

### 2. Fingerprint Duplicate (Active Alert)
**Location**: `RuleEngine._handle_failure()` line 185-188
**Current**: 
```python
existing = self.alert_store.get_alert_by_fingerprint(
    fingerprint,
    status_filter=[AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED],
)
```
**Phase 12B**: Inside AlertEngine transaction ✓

## Implementation Plan

1. Wrap `AlertEngine.evaluate()` with begin/commit/rollback
2. Remove any remaining standalone commits from called methods (already done in 12A)
3. Verify flow matches target

print("Analysis complete")
