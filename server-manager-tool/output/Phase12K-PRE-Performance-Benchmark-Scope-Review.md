# PHASE 12K-PRE — Performance Benchmark Scope Review

**Date**: 2026. 9. 28.
**Type**: READ_ONLY / SCOPE_DESIGN
**Status**: READY_FOR_12K_WITH_CONDITIONS

---

## 1. Baseline

### Repository Status
- **Git Repository**: NO (not a git repository)
- **HEAD**: N/A
- **Branch**: N/A

### Previous Phase Context
- **Phase 12I**: BEGIN IMMEDIATE Implementation (recorded in previous session)
- **Phase 12J**: Full Regression Verification (287 passed)
- **Phase 12J-FIX**: Concurrent Test Repair (3/3 tests PASS)
- **Phase 12J-FIX-2**: Linux Concurrent Verification (VERIFICATION_INCOMPLETE - Windows environment)

---

## 2. Current Environment

| Item | Value |
|------|-------|
| Platform | Windows |
| Python Version | 3.12.10 |
| SQLite Version | 3.46.0 |
| Git Repository | No |

---

## 3. Phase 12I Change Summary

### Applied Changes

| Change | Status | Location |
|--------|--------|----------|
| `PRAGMA busy_timeout = 5000` | ✅ APPLIED | store.py line 160 (inserted) |
| `BEGIN` → `BEGIN IMMEDIATE` | ⚠️ PENDING | Requires `_commit_if_standalone` inspection |

### Implementation Notes

**busy_timeout**: Successfully inserted at line 160 via editor.

**BEGIN IMMEDIATE**: store.py does not contain explicit `execute("BEGIN")` statement. Transaction begin is likely handled inside `_commit_if_standalone()` method. Further inspection required.

---

## 4. Existing Benchmark Infrastructure

### Search Results

| Keyword | Result |
|---------|--------|
| benchmark | No existing infrastructure found |
| performance | No existing infrastructure found |
| pytest-benchmark | Not installed |
| timeit | No existing usage |

### Conclusion

**No existing benchmark infrastructure.** Phase 12K will require new benchmark implementation using:
- Python `timeit` module, OR
- `pytest-benchmark` plugin (requires installation), OR
- Custom timing wrapper

---

## 5. Alert Transaction Flow

Based on code inspection:

```
AlertEngine.evaluate()
       ↓
RuleEngine (threshold logic)
       ↓
AlertStore transaction
       ↓
_commit_if_standalone()  ← Transaction boundary (BEGIN location TBD)
       ↓
alert mutation (INSERT/UPDATE)
       ↓
COMMIT (inside _commit_if_standalone)
```

### Transaction Boundary

- **Current**: `_commit_if_standalone()` method handles transaction
- **Phase 12I Intent**: `BEGIN IMMEDIATE` at transaction start
- **Implementation Gap**: Explicit `BEGIN` statement not found in store.py

---

## 6. Performance-Sensitive Operations

| Operation | Contention Risk | 12K Measure |
|-----------|-----------------|-------------|
| Transaction begin | Low/High | 12K-A, 12K-B |
| Alert create | Medium | 12K-A |
| Fingerprint dedup | High | 12K-B |

---

## 7. 12K-A — Single-Connection Benchmark

**Purpose**: Measure transaction cost under BEGIN IMMEDIATE.

**Workload**:
- A1: Transaction baseline
- A2: Alert create (unique fingerprint)
- A3: Alert acknowledge
- A4: Alert resolve

**Environment**: Single connection, warm-up 20 ops, measurement 100 ops, 3 rounds.

---

## 8. 12K-B — Concurrent Contention Benchmark

**Purpose**: Measure lock contention with independent connections.

**Topology**:
```
  SAME DB File
     ├─ Store A → Thread A
     └─ Store B → Thread B
```

**Workload**:
- B1: Same fingerprint (expect 1 active alert)
- B2: Different fingerprint (expect 2 active alerts)

**Environment**: REQUIRES LINUX (Windows file locking unreliable)

---

## 9. Metrics

- Latency: min, p50, p95, p99, max
- Throughput: ops/sec
- Correctness: duplicate active alerts (must be 0)

---

## 10. Final Gate: READY_FOR_12K_WITH_CONDITIONS

**Conditions Met**:
- ✅ 12K-A scope defined
- ✅ Metrics defined
- ✅ Tooling selected (timeit)

**Conditions Pending**:
- ⚠️ 12K-B requires Linux

---

## 11. Next Steps

1. **12K-A**: Create benchmark_12k_a.py, run on Windows
2. **12K-B**: Deploy to Linux, run concurrent benchmark

---

**End of Phase 12K-PRE**