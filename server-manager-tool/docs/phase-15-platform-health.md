# Phase 15 — Platform Health & Resource Management

## Overview

Phase 15 implements READ_ONLY health, availability, resource status, and
capacity assessment for canonical entities discovered in Phase 14.

```
Inventory (Phase 14)
    ↓
Health
    ↓
Resource Status
    ↓
Availability
    ↓
Capacity
```

## Architecture

```
DiscoveryResult (Phase 14)
    ↓
HealthService.assess()
    ↓
HealthExtractor (provider-specific ABC)
    ↓
HealthReport (list[HealthResult])
```

The `HealthService` is provider-neutral. Provider-specific health
extraction is delegated to `HealthExtractor` implementations, following
the same pattern as `ProviderNormalizer` (ABC + concrete implementation).

New providers add a new `HealthExtractor` — the core `HealthService`
does not need modification.

## Key Design Decisions

### 1. Health ≠ Availability

Health and Availability are separate fields on `HealthResult`, never
merged into a single score.

Valid combinations:
- Health=DEGRADED, Availability=AVAILABLE (node has pressure but is ready)
- Health=UNKNOWN, Availability=UNKNOWN (no evidence)

### 2. UNKNOWN Policy

```
No evidence    ≠ Healthy
No metric      ≠ Zero
No capacity    ≠ Zero capacity
No availability ≠ Available
```

UNKNOWN is used actively. Missing conditions → UNKNOWN (not HEALTHY).
Missing used/utilization → None (not zero).

### 3. No Fake Capacity

- CPU threads ≠ capacity (unless source explicitly states it)
- NIC link speed ≠ available bandwidth
- GPU exists ≠ GPU capacity = 100%
- K8s list API `used`/`utilization` = None (requires metrics-server API)

### 4. Source Unit Preservation

Capacity values preserve source units (bytes, Ki, cores, Gi, etc.).
No arbitrary unit conversion.

### 5. Provenance Reuse

Health results reuse `SourceEvidence` from canonical models — no new
provenance system.

### 6. Canonical Identity

`HealthResult.entity_id` = canonical_id (not provider_id).
Directly links to canonical entities from Phase 14.

## Health Status Derivation

```
Explicit failure evidence    → UNHEALTHY
Explicit degraded evidence    → DEGRADED
Explicit healthy/ready        → HEALTHY
No sufficient evidence        → UNKNOWN
```

### Kubernetes Evidence Sources

| Entity  | Health Evidence | Resource/Capacity Evidence |
|---------|----------------|---------------------------|
| Node    | status.conditions (Ready, MemoryPressure, DiskPressure, PIDPressure, NetworkUnavailable) | status.capacity / status.allocatable (cpu, memory) |
| Pod     | status.phase (Running, Pending, Succeeded, Failed, Unknown) + status.conditions (Ready) | — |
| PV      | status.phase (Available, Bound, Released, Failed, Pending) | spec.capacity.storage |
| PVC     | status.phase (Bound, Pending, Lost) | — |
| Service | — (no explicit health evidence → UNKNOWN) | — |
| Platform | — (API accessibility → AVAILABLE) | — |
| Cluster | — (API accessibility → AVAILABLE) | — |

## Scope Boundaries

### IN SCOPE
- Health status (HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN)
- Availability status (AVAILABLE, UNAVAILABLE, UNKNOWN)
- Resource status (CPU, Memory, Storage, Network, Accelerator)
- Capacity (total, allocatable — source-preserved)
- Provenance preservation
- Canonical identity linkage
- Kubernetes fixture/mock-based contract validation

### OUT OF SCOPE (DEFERRED)
- Monitoring (time-series, Prometheus, historical metrics)
- Alert generation
- Recovery / remediation
- Persistence (health history database)
- Threshold alerting / anomaly detection
- Dashboard redesign
- WRCP health (no credentials → DEFERRED)

## READ_ONLY Safety

No mutation operations in the health pipeline:
- No create/update/delete/patch/scale/restart
- No connection to providers (data already in canonical entities)
- Verified by source inspection tests

## Files

### New Files
- `src/server_manager/health/__init__.py` — package exports
- `src/server_manager/health/models.py` — HealthStatus, AvailabilityStatus, ResourceType, ResourceStatus, CapacityInfo, HealthResult, HealthReport
- `src/server_manager/health/service.py` — HealthExtractor (ABC), KubernetesHealthExtractor, HealthService
- `tests/test_platform_health.py` — 42 tests (41 passed, 1 skipped)
- `docs/phase-15-platform-health.md` — this document

### No Modified Files
Phase 15 does not modify any existing Phase 14 or earlier files.

## Test Results

```
Phase 15 tests:  41 passed, 1 skipped
K8s tests:      239 passed, 16 skipped
Full regression: 920 passed, 18 skipped, 1 failed (pre-existing)
```

Pre-existing failure: `test_scheduler.py::test_is_due_past` (time-dependent, unrelated)

## Dependencies

No new dependencies added. Uses only existing:
- pydantic (models)
- Python standard library (datetime, enum, abc, typing)

## Provider Extensibility

```python
# New provider example:
class WRCPHealthExtractor(HealthExtractor):
    def extract_health(self, inventory):
        ...

HealthService.register_extractor(ProviderType.WRCP, WRCPHealthExtractor)
```

The core `HealthService` does not need modification for new providers.
