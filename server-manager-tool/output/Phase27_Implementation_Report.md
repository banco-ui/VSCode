# Phase 27 — Cross-Provider Contract & Integration Validation Report

## Overview

Phase 27 validates that the existing Kubernetes and OpenStack providers
consistently implement the common Server Manager architecture contract.
No third provider was added. No working components were redesigned.
The phase focused on contract consistency, evidence integrity, graph
correctness, health/resource semantics, and Management API compatibility.

## Approach

### 1. Inspection

A thorough code-level inspection was performed across:

- **ProviderAdapter contract** (`providers/base.py`): ABC with `capabilities()`,
  `collect()`, `collect_safe()` methods; `RawProviderSnapshot`, `CapabilityResult`,
  `RawRelationshipEvidence` models.
- **Kubernetes adapter** (`providers/kubernetes.py`): fixture-based collection,
  client injection optional, per-capability results, DIRECT/DERIVED evidence only.
- **OpenStack adapter** (`providers/openstack.py`): same contract pattern,
  DIRECT evidence for Server->Hypervisor and Volume->Server.
- **Normalizers**: both inherit from `GenericProviderNormalizer`, transform
  provider-specific payload -> generic format, delegate to `super().normalize()`.
  `CanonicalIdentityGenerator` produces deterministic IDs (`canon-{pt}-{kind}-{ref}`).
- **Graph builder** (`graph/service.py`): validates DIRECT/DERIVED evidence only,
  deduplicates edges by `(source, target, type)`, validates endpoint existence.
- **Health extractors** (`health/service.py`): both registered in `_EXTRACTORS`,
  UNKNOWN used when evidence insufficient, missing metrics -> `None` (not zero).
- **Discovery service** (`discovery/service.py`): FAILED/SKIPPED -> empty inventory.
- **Management API** (`api/management_routes.py`): `discovery_factory` pattern,
  provider-neutral. No K8s-specific assumptions in shared paths.

### 2. Cross-Provider Contract Tests

Created `tests/test_cross_provider_contract.py` with **67 test methods**
(**105 test cases** including parametrized variants) covering all 14
contract areas from the spec:

1. Equivalent adapter contract behavior (6 tests x2 providers)
2. Deterministic Canonical IDs (3 tests)
3. Stable normalization of identical snapshots (3 tests x2)
4. Missing fields and unknown enum values (4 tests)
5. Missing metrics must not become zero (4 tests)
6. UNKNOWN must not become HEALTHY (3 tests)
7. Failed discovery must not produce fake inventory (6 tests)
8. Evidence and provenance must be preserved (6 tests)
9. Only supported DIRECT/DERIVED evidence (3 tests)
10. No INFERRED/UNKNOWN relationships promoted (2 tests x2)
11. Duplicate entities and relationships handled (2 tests x2)
12. Partial success and provider errors distinguishable (5 tests)
13. Health extraction registered and dispatched (5 tests)
14. Management API response contracts compatible (5 tests x2)

Plus graph/resource integrity (8 tests) and API/Dashboard integration (6 tests x2).

### 3. Graph and Resource Integrity

Verified with realistic fixtures:
- All edge endpoints refer to existing canonical IDs
- OpenStack VM->Hypervisor relationships preserve DIRECT evidence with raw_data
- OpenStack Volume->Server attachment relationships preserve DIRECT evidence
- K8s Pod->Node relationships retain DIRECT evidence semantics
- Missing capacity represented as None, not zero
- No inferred topology introduced

### 4. API and Dashboard Integration

Verified Management API endpoints work for both providers:
- GET /api/v1/inventory — correct provider_type, entity_counts
- GET /api/v1/health — valid health_status (no false healthy)
- GET /api/v1/graph/summary — node_count > 0
- GET /api/v1/inventory/{type} — entity list works for nodes/networks/storages
- POST /api/v1/discovery/run — valid DiscoveryRunResponse
- GET /api/v1/visibility/summary — operational summary works
- GET /api/v1/visibility/entities/{id} — entity status works
- POST /api/v1/operations/preview — execution_allowed is always False

No hard-coded K8s-only assumptions in shared paths.
No credentials or raw secrets exposed in responses.
No new mutation or execution routes.

### 5. Safety and Scope

- No provider resource mutations performed or added.
- No Operations or Recovery execute calls.
- No new provider added.
- No new dependencies added.
- No kubeconfig, credentials, or environment secrets modified.
- No tests deleted or weakened.
- Pre-existing test_is_due_past failure NOT modified.

## Findings

### Verified Correct (No Defects Found)

The existing implementation was found to be correct across all inspected areas.
No implementation changes were needed — only new tests were added.

Key verified behaviors:
1. Canonical IDs are deterministic — same provider_ref always produces same ID.
2. UNKNOWN is never promoted to HEALTHY.
3. Missing metrics are None, not zero.
4. Failed discovery produces no fake inventory (inventory=None, entity_count=0).
5. Only DIRECT/DERIVED evidence — graph builder rejects INFERRED/UNKNOWN.
6. Graph validation passes — validation_errors is empty for both providers.
7. Partial vs FAILED distinguishable — PARTIAL has entities + errors.
8. Health extractors registered for both K8S and OPENSTACK.
9. Management API is provider-neutral — no K8s-only assumptions.

### Test Adjustments

All-capabilities-fail results in PARTIAL (not FAILED): The PLATFORM capability
always succeeds from fixture data. When all resource capabilities fail but
PLATFORM succeeds, the collection status is correctly PARTIAL.

## Verification Results

### Cross-Provider Contract Tests
tests/test_cross_provider_contract.py: 105 passed, 0 failed

### Kubernetes Regression
All K8s provider, normalizer, and e2e tests passed.
Live tests: 16 skipped (require live K8s credentials).

### OpenStack Regression
All OpenStack provider, normalizer, and e2e tests passed.

### Management API and Dashboard Regression
All API and Dashboard tests passed for both provider types.

### Full Repository Test Suite
1794 passed, 27 skipped, 1 failed
1 failed = test_scheduler.py::test_is_due_past (pre-existing, timing-dependent)

## Modified Files
No source files were modified. Only test files were created.

## New Files
- tests/test_cross_provider_contract.py — 105 cross-provider contract tests
- output/Phase27_Implementation_Report.md — this report

## New Dependencies
None.

## Live Platform Tests
- tests/test_kubernetes_live.py — 16 tests SKIPPED (require live K8s credentials)
- tests/test_kubernetes_live_mock.py — mock-based tests passed
- No OpenStack live tests exist yet (Phase 26 added fixture-based tests only)
- All fixture/mock tests passed.

## Completion Status

Phase 27 is COMPLETE:
- Cross-provider contracts covered by tests (105 test cases)
- Both providers retain existing behavior (no source changes)
- Evidence, IDs, health, resources, and relationships verified correct
- API/UI compatibility verified for both provider types
- No new unexpected regression failure
- Safety and credential protections intact