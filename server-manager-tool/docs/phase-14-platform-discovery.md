# Phase 14 — Platform Discovery & Inventory

**Status:** COMPLETE  
**Date:** 2026-10-07  
**Depends on:** Phase 13G (Provider Adapter, Normalizer, Canonical Model)

---

## 1. Overview

Phase 14 connects the existing Phase 13G pipeline into a
**DiscoveryService** that produces a **DiscoveryResult** containing:

- Discovery status (SUCCESS / PARTIAL / FAILED / SKIPPED)
- Canonical inventory (all entity types from the canonical model)
- Relationship evidence (DIRECT and DERIVED)
- Provenance (SourceEvidence on every entity)
- Capability summary (attempted / succeeded / failed)
- Errors and warnings aggregation

The discovery service is **stateless** and does not persist results.
It composes existing abstractions without duplicating them.

---

## 2. Architecture

```
Fixture / Mock / Live
      ↓
ProviderAdapter.collect()
      ↓
RawProviderSnapshot
      ↓
ProviderNormalizer.normalize()
      ↓
NormalizationResult
      ↓
CanonicalInventory.from_normalization()
      ↓
DiscoveryResult (status, inventory, relationships, provenance)
```

### 2.1 DiscoveryService (`service.py`)

`PlatformDiscovery.discover(adapter, normalizer) -> DiscoveryResult`

Pipeline steps:

1. **Collect** — `adapter.collect()` → `RawProviderSnapshot`
2. **SKIPPED check** — if `collection_status == SKIPPED`, return early with `inventory=None`
3. **FAILED check** — if `collection_status == FAILED`, return early with `inventory=None`
   (normalization is NOT run — no canonical entities from a failed collection)
4. **Normalize** — `normalizer.normalize(snapshot)` → `NormalizationResult`
5. **Build inventory** — `CanonicalInventory.from_normalization(norm_result)`
6. **Derive status** — `_derive_discovery_status(snapshot, norm_result)`
7. **Aggregate** — capabilities, errors, warnings, relationship evidence

### 2.2 DiscoveryResult (`models.py`)

```python
class DiscoveryResult(BaseModel):
    provider_type: ProviderType
    provider_id: Optional[str]
    discovery_status: OrchestrationStatus  # SUCCESS/PARTIAL/FAILED/SKIPPED
    snapshot_id: str
    collected_at: str
    identified_platform_type: PlatformType
    inventory: Optional[CanonicalInventory]  # None when SKIPPED/FAILED
    capabilities_attempted: list[AdapterCapability]
    capabilities_succeeded: list[AdapterCapability]
    capabilities_failed: list[AdapterCapability]
    relationship_evidence: list[RawRelationshipEvidence]
    errors: list[str]
    warnings: list[str]
```

### 2.3 CanonicalInventory (`models.py`)

```python
class CanonicalInventory(BaseModel):
    provider_type: ProviderType
    provider_id: Optional[str]
    snapshot_id: str
    discovered_at: str
    identified_platform_type: PlatformType

    physicals: list[Physical]
    os_entities: list[OS]
    platforms: list[Platform]
    clusters: list[Cluster]
    nodes: list[Node]
    execution_environments: list[ExecutionEnvironment]
    workloads: list[Workload]
    networks: list[Network]
    storages: list[Storage]
    accelerators: list[Accelerator]
    relationship_evidence: list[RawRelationshipEvidence]
```

The ONLY conversion path is `CanonicalInventory.from_normalization(result)`.

---

## 3. Status Derivation Rules

| collection_status | norm_result.errors | → DiscoveryStatus |
|---|---|---|
| SKIPPED | — | SKIPPED |
| FAILED | — | FAILED |
| PARTIAL | any | PARTIAL |
| SUCCESS | has errors | PARTIAL |
| SUCCESS | no errors | SUCCESS |

**Key design decision:** When `collection_status == FAILED`, normalization
is NOT run. The discovery returns `inventory=None` and `DiscoveryStatus.FAILED`.
This prevents the K8s normalizer from creating Platform/Cluster entities
from an empty payload when the collection itself failed (e.g., authentication
error, API server unreachable).

---

## 4. Files Created / Modified

### Created (Phase 14)

| File | Description |
|---|---|
| `src/server_manager/discovery/__init__.py` | Package exports |
| `src/server_manager/discovery/models.py` | `DiscoveryResult`, `CanonicalInventory` |
| `src/server_manager/discovery/service.py` | `PlatformDiscovery` orchestrator |
| `tests/test_platform_discovery.py` | 27 tests (26 passed, 1 skipped) |
| `docs/phase-14-platform-discovery.md` | This document |

### Modified (Phase 14)

| File | Change |
|---|---|
| `service.py` | Added `_build_failed_result()` — FAILED returns `inventory=None` without normalization |

---

## 5. Test Coverage

### Test Classes (27 tests)

| Class | Tests | Description |
|---|---|---|
| `TestDiscoverySuccess` | 3 | Full fixture → SUCCESS |
| `TestDiscoveryPartial` | 4 | Partial fixture → PARTIAL |
| `TestDiscoveryFailed` | 2 | Failed collection → FAILED, inventory=None |
| `TestDiscoverySkipped` | 2 | SKIPPED → inventory=None |
| `TestKubernetesIdentification` | 3 | Platform type / version identification |
| `TestCanonicalInventoryGeneration` | 3 | All entity types, CanonicalInventory type |
| `TestWorkloadNotInferred` | 2 | No Workload from K8s objects |
| `TestIdentityStability` | 1 | Same fixture → same canonical_ids |
| `TestProvenance` | 1 | All entities have source_evidence |
| `TestRelationships` | 2 | Pod→Node DIRECT, Pod→Container DERIVED |
| `TestProviderPath` | 2 | Fixture path + mock client path |
| `TestLiveDiscovery` | 1 | Live skip (no credentials) |
| `TestMutationSafety` | 1 | No create/update/delete/patch in adapter |

### Test Results

```
tests/test_platform_discovery.py: 26 passed, 1 skipped
K8s tests (5 files): 239 passed, 16 skipped
Full regression: 879 passed, 17 skipped, 1 failed (pre-existing, unrelated)
```

**Pre-existing failure:** `tests/test_scheduler.py::TestScheduleDefinition::test_is_due_past`
— time-dependent, unrelated to Phase 14.

---

## 6. Mutation Safety

The discovery pipeline is **read-only**:

- `KubernetesProviderAdapter` calls only `list_*` and `get_*` methods
- No `create_*`, `update_*`, `delete_*`, `patch_*`, `replace_*`, `scale`, `rollout`
- `TestMutationSafety::test_no_kubernetes_mutation` verifies via source inspection

---

## 7. Provider Paths

### Fixture Path

```python
adapter = KubernetesProviderAdapter(fixture=fixture_dict)
normalizer = KubernetesProviderNormalizer()
result = PlatformDiscovery().discover(adapter, normalizer)
```

### Mock Client Path

```python
adapter = KubernetesProviderAdapter(fixture=cluster_info, client=mock_client)
normalizer = KubernetesProviderNormalizer()
result = PlatformDiscovery().discover(adapter, normalizer)
```

The mock client must implement:
- `get_api_version()` → object with `to_dict()` returning `{"gitVersion": "..."}`
- `list_node()`, `list_pod_for_all_namespaces()`, `list_namespace()`,
  `list_service_for_all_namespaces()`, `list_persistent_volume()`,
  `list_persistent_volume_claim_for_all_namespaces()`

Each list method returns an object with `to_dict()` returning
`{"items": [item.to_dict(), ...]}`.

### Live Path

Live Kubernetes discovery requires credentials (kubeconfig).
Without credentials, discovery is SKIPPED.

