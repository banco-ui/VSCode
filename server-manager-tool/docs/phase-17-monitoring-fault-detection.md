# Phase 17 — Monitoring & Fault Detection

## Overview

Provider-neutral monitoring and fault detection layer for Server Manager.
Consumes Phase 15 HealthReport to create observations, detects state
changes, and generates evidence-based faults with lifecycle management.

```
Discovery (Phase 14)
    ↓
Health / Resource (Phase 15)
    ↓
Unified Infrastructure Graph (Phase 16)
    ↓
Monitoring (Phase 17)           ← NEW
    ↓
Fault Detection (Phase 17)      ← NEW
    ↓
Detection Result
```

## Key Principles

1. **Evidence-first**: Faults require explicit evidence. No inference.
2. **UNKNOWN != FAILURE**: UNKNOWN health/availability is NOT a fault.
3. **Missing metric != 0**: Missing utilization is NOT treated as zero.
4. **No root cause inference**: Pod unavailable does NOT imply Node fault.
5. **Graph context only**: Graph relationships are NOT fault causality.
6. **Deterministic**: Same input → same output. Fault IDs are deterministic.
7. **No mutation**: No create/update/patch/delete/scale/restart operations.
8. **No provider API calls**: Monitoring consumes HealthReport, not live data.

## Architecture

### Monitoring Package (`server_manager.monitoring`)

- **Observation**: Point-in-time snapshot of entity state (health, availability,
  resource statuses, evidence). Created from `HealthResult` via
  `Observation.from_health_result()`.
- **StateChange**: Detected transition between two consecutive observations.
  Only created when status actually changed.
- **MonitoringReport**: Result of a monitoring cycle (observations + state changes).
- **MonitoringService**: Creates observations from `HealthReport`, maintains
  in-memory observation history, detects state changes.

### Fault Package (`server_manager.fault`)

- **FaultType**: HEALTH_FAILURE, HEALTH_DEGRADED, AVAILABILITY_FAILURE,
  RESOURCE_THRESHOLD, STATE_CHANGE
- **Severity**: INFO, WARNING, CRITICAL
- **FaultStatus**: DETECTED, ONGOING, RESOLVED (lifecycle)
- **Fault**: Detected infrastructure fault with evidence, severity, and lifecycle.
- **FaultResult**: Result of a detection cycle (faults + resolved IDs).
- **ThresholdPolicy**: Configurable resource thresholds (all None by default —
  no hardcoded defaults).
- **FaultDetectionService**: Evaluates observations and state changes,
  produces faults with deterministic deduplication and lifecycle management.
- **FaultGraphContext**: Read-only graph context lookup via Phase 16 GraphQuery.

## Fault Rules

| Condition | Fault Type | Severity |
|---|---|---|
| Health = UNHEALTHY | HEALTH_FAILURE | CRITICAL |
| Health = DEGRADED | HEALTH_DEGRADED | WARNING |
| Availability = UNAVAILABLE | AVAILABILITY_FAILURE | CRITICAL |
| Utilization >= critical | RESOURCE_THRESHOLD | CRITICAL |
| Utilization >= warning | RESOURCE_THRESHOLD | WARNING |
| HEALTHY → UNHEALTHY | STATE_CHANGE | CRITICAL |
| HEALTHY → DEGRADED | STATE_CHANGE | WARNING |
| AVAILABLE → UNAVAILABLE | STATE_CHANGE | CRITICAL |

### No-Fault Conditions

- Health = UNKNOWN → no fault
- Availability = UNKNOWN → no fault
- Missing utilization → no fault
- Missing capacity → no fault
- Transition to/from UNKNOWN → no STATE_CHANGE fault
- No threshold policy configured → no RESOURCE_THRESHOLD fault

## Fault Lifecycle

```
HEALTHY → UNHEALTHY  →  DETECTED
UNHEALTHY → UNHEALTHY →  ONGOING
UNHEALTHY → HEALTHY  →  RESOLVED
```

## Deduplication

- Fault ID is deterministic: `{entity_id}:{fault_type}[:{resource_type}]`
- Same (entity_id, fault_type) → same fault_id → no duplicate
- Repeated observations of the same issue → fault transitions DETECTED → ONGOING
- Issue resolved → fault marked RESOLVED

## Graph Integration

- `FaultGraphContext` wraps `GraphQuery` for read-only context lookup
- `get_entity_node(fault)` → graph node for fault's entity
- `get_related_entities(fault)` → neighbor entity IDs
- `get_relationships(fault)` → all graph relationships
- Does NOT create new graph edges or infer causality

## Files

### New Files

- `src/server_manager/monitoring/__init__.py`
- `src/server_manager/monitoring/models.py` — Observation, StateChange, MonitoringReport
- `src/server_manager/monitoring/service.py` — MonitoringService
- `src/server_manager/fault/__init__.py`
- `src/server_manager/fault/models.py` — FaultType, Severity, FaultStatus, Fault,
  FaultResult, ThresholdPolicy
- `src/server_manager/fault/service.py` — FaultDetectionService, FaultGraphContext
- `tests/test_platform_monitoring.py` — 23 tests
- `tests/test_platform_fault.py` — 33 tests
- `docs/phase-17-monitoring-fault-detection.md` — this document

### Modified Files

None — Phase 17 is purely additive.

## Test Results

- Phase 17 tests: 56 passed (23 monitoring + 33 fault)
- Full regression: 1006 passed, 18 skipped, 1 pre-existing failure

## Deferred

- Alert delivery (email, Slack, Teams, SMS, webhook)
- Auto-remediation / recovery / restart / scale / rollout
- Time-series persistence / monitoring database
- Prometheus / Grafana / Elasticsearch / Kafka integration
- Machine Learning anomaly detection
- Predictive maintenance
- Root cause analysis
- Dashboard / topology UI
- Long-term metrics storage
