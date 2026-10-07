# Phase 16 — Unified Infrastructure Graph

## Overview

Phase 16 implements a **Unified Infrastructure Graph** that connects canonical
entities and their relationship evidence into a single navigable structure.

```
Canonical Inventory
       +
Relationship Evidence
       ↓
Unified Infrastructure Graph
       ↓
Read-Only Traversal
```

## Core Principles

1. **No Inference** — Relationships are created ONLY from existing evidence.
   `DIRECT` and `DERIVED` evidence types are allowed; `INFERRED` and `UNKNOWN`
   are prohibited.

2. **Canonical ID = Graph Node ID** — Graph nodes use the canonical entity's
   `canonical_id` as their identity. No separate graph IDs are generated.

3. **No Provider API Calls** — The graph builder consumes `CanonicalInventory`
   and relationship evidence. It does NOT call Kubernetes, WRCP, VMware, or any
   other provider API.

4. **No Mutation** — The graph builder is purely read-only. It does not create,
   update, patch, delete, scale, or restart any entity.

5. **No Graph Database** — In-memory representation using standard Python
   data structures (dict, set, list). No Neo4j, NetworkX, or other external
   graph database dependency.

## Architecture

```
DiscoveryResult (Phase 14)
    ↓
GraphBuilder.build()
    ↓
GraphReport (nodes + relationships)
    ↓
GraphQuery (read-only traversal)
```

### Two Sources of Relationship Evidence

1. **Entity Ref Fields** (DERIVED)
   - Canonical entities have typed ref fields (`node_ref`, `cluster_ref`, etc.)
   - These are already resolved to `canonical_id` by the normalizer
   - Evidence type: `DERIVED` (computed from provider data)

2. **RawRelationshipEvidence** (DIRECT/DERIVED)
   - Provider-stated relationships (e.g., Pod→Node from `spec.nodeName`)
   - Uses provider_id refs, resolved to canonical_id via id_map
   - Evidence type preserved from source (`DIRECT` or `DERIVED`)

### Deduplication

When the same edge `(source_id, target_id, relationship_type)` appears from
both sources, `DIRECT` evidence is preferred over `DERIVED`.

## Graph Model

### RelationshipType

| Type | Description |
|------|-------------|
| `RUNS_ON` | Entity runs on target (Pod→Node, Node→Physical) |
| `CONTAINS` | Source contains target (Cluster→Node, Pod→Container) |
| `MEMBER_OF` | Source is member of target (Node→Cluster, Cluster→Platform) |
| `HOSTS` | Source hosts target (Node→EE, OS→EE) |
| `USES` | Source uses target (Workload→Network, EE→OS) |
| `ATTACHED_TO` | Source attached to target (Accelerator→Physical) |

### GraphNode

| Field | Description |
|-------|-------------|
| `canonical_id` | Identity (same as canonical entity) |
| `entity_type` | EntityType enum (PHYSICAL, NODE, etc.) |
| `provider_type` | ProviderType (KUBERNETES, WRCP, etc.) |
| `source_evidence` | SourceEvidence (provenance) |

### GraphRelationship

| Field | Description |
|-------|-------------|
| `source_id` | Source node canonical_id |
| `target_id` | Target node canonical_id |
| `relationship_type` | RelationshipType enum |
| `evidence_type` | DIRECT or DERIVED |
| `source_evidence` | SourceEvidence (provenance) |
| `raw_data` | Optional raw evidence data |

## Kubernetes Graph

The K8s fixture produces:

```
Platform
   ↑ MEMBER_OF
Cluster
   ↑ MEMBER_OF
Node
   ↑ RUNS_ON (DIRECT)
Pod (EE)
   ↓ CONTAINS (DERIVED)
   ├── Container1 (EE)
   └── Container2 (EE)

Orphan nodes (no relationship evidence):
  Network (Service)
  Storage (PV)
  Storage (PVC)
```

### Edges

| Source | Target | Type | Evidence |
|--------|--------|------|----------|
| Cluster | Platform | MEMBER_OF | DERIVED |
| Node | Cluster | MEMBER_OF | DERIVED |
| Pod | Node | RUNS_ON | DIRECT |
| Pod | Container1 | CONTAINS | DERIVED |
| Pod | Container2 | CONTAINS | DERIVED |

## Graph Validation

| Check | Status |
|-------|--------|
| Every node has canonical_id | PASS |
| Every edge source exists | PASS |
| Every edge target exists | PASS |
| No duplicate edge | PASS |
| No INFERRED edge | PASS |
| No UNKNOWN edge | PASS |
| Provenance preserved | PASS |

## Orphan Policy

- **Orphan Node**: Canonical entity with no relationships → ALLOWED
  (e.g., Network, Storage in K8s fixture)
- **Orphan Relationship**: Edge with missing source or target → REJECTED
  (no fake nodes created)

## Health/Resource Integration

The graph does NOT duplicate HealthResult or ResourceStatus data.
Instead, it uses `canonical_id` as the lookup key:

```
Graph Node → canonical_id → HealthResult lookup (Phase 15)
Graph Node → canonical_id → ResourceStatus lookup (Phase 15)
```

## Provider Extensibility

The graph builder is provider-neutral. New providers register through the
existing discovery pipeline:

```
Any Provider → CanonicalInventory → GraphBuilder → Graph
```

## Files

| File | Lines | Description |
|------|-------|-------------|
| `src/server_manager/graph/models.py` | ~140 | GraphNode, GraphRelationship, GraphReport, RelationshipType, EntityType |
| `src/server_manager/graph/service.py` | ~550 | GraphBuilder, GraphQuery |
| `src/server_manager/graph/__init__.py` | ~35 | Package exports |
| `tests/test_platform_graph.py` | ~560 | 30 tests |

## Test Results

- Phase 16 tests: **30 passed**
- Phase 13G tests: **passed**
- Phase 14 tests: **passed**
- Phase 15 tests: **passed**
- K8s tests: **passed**
- Full regression: **950 passed, 18 skipped, 1 pre-existing failure**
