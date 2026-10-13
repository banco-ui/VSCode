# Phase 28F — StarlingX Health, Fault & Alert Integration Validation

**Date:** 2026-10-13  
**Phase:** 28F  
**Status:** ✅ Complete — All fixture-based validations pass  
**Live Validation:** Not performed (fixture-based only, per safety constraints)

---

## Executive Summary

Phase 28F validates that the Phase 28E StarlingX read-only provider
integrates correctly with the existing Health, Fault Detection, Alert,
Visibility, and Management API pipeline. All 7 required validation areas

## 1. HEALTH_VALIDATION

**Status:** ✅ Pass (11 tests)

| Fixture | Expected Health | Result |
|---------|----------------|--------|
| available + enabled, no alarms | HEALTHY | ✅ |
| availability=degraded | DEGRADED | ✅ |
| FM critical alarm (100.103) | UNHEALTHY | ✅ |
| FM warning alarm | DEGRADED | ✅ |
| Unrecognized availability | UNKNOWN | ✅ |
| availability=offline | UNHEALTHY | ✅ |
| operational=disabled (was healthy) | DEGRADED | ✅ |
| No fixture provided | FAILED | ✅ |
| Platform critical event_log | UNHEALTHY | ✅ |
| Memory >= 90% (otherwise healthy) | DEGRADED | ✅ |
| Critical alarm overall report | PARTIAL | ✅ |
| No alarms → no FM warnings | No warnings | ✅ |

- UNKNOWN is NOT treated as HEALTHY.
- FM Critical alarm → UNHEALTHY on Node.
- Collection failure → FAILED, not empty/HEALTHY.

## 2. FAULT_SEPARATION

**Status:** ✅ Pass (5 tests)

- FM Alarm 100.103 → `HEALTH_FAILURE` (CRITICAL) on Node.
- Offline Node → `AVAILABILITY_FAILURE` — separate fault, different fault_id.
- Multiple critical FM alarms on same Node → ONE fault (deterministic dedup).
- StarlingX fault entity_id is Node, never Physical (bm_type=none).
- Different fault_ids → different alert_ids.

## 3. ALERT_LIFECYCLE

**Status:** ✅ Pass (7 tests)

- First cycle: DETECTED. Second cycle: ONGOING. Alarm cleared: RESOLVED.
- Fault → Alert OPEN. Duplicate fault → no new alert (dedup).
- UNKNOWN health → no fault → no alert.
- OPEN → ACKNOWLEDGED → RESOLVED lifecycle works correctly.

## 4. DUPLICATE_HANDLING

**Status:** ✅ Pass (6 tests)

- REST + CLI same UUID → one alarm, `_sources = ["rest", "cli"]`.
- CLI fields supplement REST without overwriting REST values.
- REST-only → `_sources = ["rest"]`. CLI-only → `_sources = ["cli"]`.
- Normalizer preserves FM alarms in Node.metadata.starlingx.fm_alarms.
- SourceEvidence provider_type = WRCP.

## 5. API_ERROR_HANDLING

**Status:** ✅ Pass (6 tests)

- Auth error (401) → PARTIAL, not HEALTHY.

## 6. API_DASHBOARD_INTEGRATION

**Status:** ✅ Pass (8 tests)

- Full pipeline works: Adapter → Normalizer → HealthService →
  MonitoringService → FaultDetectionService → AlertService →
  OperationalVisibilityService.
- Entity counts: 0 Physical, 1 Platform, 1 Cluster, 1 Node.
- `HealthService._EXTRACTORS` contains both WRCP and KUBERNETES —
  StarlingX registration does not interfere with Kubernetes.
- `OperationalVisibilityService.get_summary()` correctly aggregates
  StarlingX health, faults, and alerts.
- Node.cluster_ref resolves to Cluster.canonical_id.
- Graph has ≥3 nodes (Platform + Cluster + Node).

## 7. GRAPH_RELATIONSHIP_RULES

**Status:** ✅ Pass (9 tests)

- Relationship evidence is DIRECT only (sub-resource URL pattern).
- No name/IP-based inference.
- imemorys evidence links host UUID to memory sub-resource.
- No Physical entity created (bm_type=none).
- Graph relationship types in allowed set: {RUNS_ON, CONTAINS,
  MEMBER_OF, HOSTS, USES, ATTACHED_TO}. No INFERRED type.

---

## TEST_RESULTS

### New Integration Tests (Phase 28F)

**File:** `tests/test_starlingx_integration.py` — 52 tests, all passing

| Test Class | Tests | Status |
|-----------|-------|--------|
| TestHealthValidation | 11 | ✅ All pass |
| TestFaultSeparation | 5 | ✅ All pass |
| TestDuplicateHandling | 6 | ✅ All pass |
| TestAlertLifecycle | 7 | ✅ All pass |
| TestApiErrorHandling | 6 | ✅ All pass |
| TestApiDashboardIntegration | 8 | ✅ All pass |
| TestGraphRelationshipRules | 9 | ✅ All pass |
| **Total** | **52** | **✅ All pass** |

### All StarlingX Tests

| File | Tests | Status |

## REGRESSION_RESULTS

```
Result: 1913 passed, 27 skipped, 1 failed
  - 1 failure: test_scheduler.py::TestScheduleDefinition::test_is_due_past
    (pre-existing, NOT a new regression)

Previous baseline: 1861 passed, 27 skipped, 1 failed
New tests added:   +52 (test_starlingx_integration.py)
Current total:     1913 passed, 27 skipped, 1 failed
```

Pre-existing scheduler failure unchanged — NOT related to StarlingX.

## LIVE_VALIDATION_STATUS

**Status:** NOT PERFORMED

Live validation against WRCP 24.09 AIO-SX (10.254.174.70) was NOT
performed. All validations are fixture-based only.

Per safety constraints:
- No live environment changes
- No alarm acknowledge/clear, reboot, service restart, patch/upgrade
- No credential/kubeconfig/openrc changes

## SOURCE_FILES_MODIFIED

### Modified Source Files

| File | Change | Impact |
|------|--------|--------|
| `src/server_manager/providers/starlingx.py` | Removed 2 dead-code blocks | No behavioral change |

**Dead code removed:**

1. Duplicate `return merged` in `_merge_alarm_data()` (line 644, unreachable).
2. Unreachable code after `return OrchestrationStatus.SUCCESS` in
   `_determine_status()` (lines 759-766, appeared to be `_derive_provider_id`
   body misplaced).

Both issues were unreachable code with zero behavioral impact.

### New Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `tests/test_starlingx_integration.py` | 52 | Phase 28F integration validation |

### No Other Files Modified

No changes to health/service.py, health/starlingx_extractor.py,
normalizers/starlingx_normalizer.py, providers/__init__.py,
normalizers/__init__.py, or any other source file.

## KNOWN_LIMITATIONS

1. **Fixture-based only:** All validations use synthetic fixtures.
   Live API/CLI behavior is not validated.
2. **AlertEngine vs AlertService:** ManagementContext uses
   AlertService.create_alert(fault) (Phase 20, immediate), NOT
   AlertEngine.evaluate(context) (Phase 11D, N=3/M=5 threshold).
3. **Pre-existing scheduler failure:** test_is_due_past — not fixed
   per safety constraints.
4. **AIO-SX only:** Fixture represents simplex mode. AIO-DX defaults
   to UNKNOWN cluster type.
5. **No Physical/OS/Workload entities:** bm_type=none → no Physical.
   Redfish composition deferred.
6. **DashboardQueryService (Phase 7):** Operates on InventoryStore,
   separate from ManagementContext pipeline. Both coexist without
   interference.

## RECOMMENDED_NEXT_STEP

### Phase 28G — Live Validation & End-to-End Pipeline

1. Live API probe against WRCP 24.09 AIO-SX (10.254.174.70).
2. Live CLI validation (fm alarm-show, system health-query, software list).
3. Redfish composition for Physical entity (bm_type=none bypass).
4. Cross-source verification (sysinv vs smapi vs Redfish).
5. USM REST (5492) and VIM REST (4545) re-investigation for Phase 29.

---

## Summary

| Area | Tests | Status |
|------|-------|--------|
| HEALTH_VALIDATION | 11 | ✅ Pass |
| FAULT_SEPARATION | 5 | ✅ Pass |
| ALERT_LIFECYCLE | 7 | ✅ Pass |
| DUPLICATE_HANDLING | 6 | ✅ Pass |
| API_ERROR_HANDLING | 6 | ✅ Pass |
| API_DASHBOARD_INTEGRATION | 8 | ✅ Pass |
| GRAPH_RELATIONSHIP_RULES | 9 | ✅ Pass |
| **Total** | **52** | **✅ All pass** |

| Regression | Count | Status |
|-----------|-------|--------|
| Passed | 1913 | ✅ |
| Skipped | 27 | — |
| Failed | 1 | ⚠️ Pre-existing (scheduler) |
| **Total** | **1941** |

|------|-------|--------|
| test_starlingx_provider.py | 38 | ✅ |
| test_starlingx_normalizer.py | 29 | ✅ |
| test_starlingx_integration.py | 52 | ✅ |
| **Total** | **119** | **✅ All pass** |

- All endpoints failed → FAILED, not empty success.
- Partial collection preserves errors in snapshot.errors.
- Missing fm_alarms key → defaults to empty list (not None).
- Timeout error captured in errors list.

pass with 52 new integration tests. Two minor dead-code issues were
found and fixed in `providers/starlingx.py` (unreachable code, no
behavioral impact). Full regression passes with only the pre-existing
scheduler test failure unchanged.
