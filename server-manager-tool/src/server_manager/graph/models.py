"""Graph models — Phase 16.

Unified Infrastructure Graph models for representing canonical entities
and their relationships as a navigable graph structure.

Key principles:
- Graph nodes = canonical entities (canonical_id = node identity)
- Graph edges = relationship evidence (DIRECT/DERIVED only)
- No inference: edges only from existing evidence
- No provider API calls: graph builds from inventory, not live data

    Canonical Inventory
        +
    Relationship Evidence
        ↓
    Graph Builder
        ↓
    Unified Infrastructure Graph
        ↓
    Graph Query / Traversal
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from server_manager.models.canonical import (
    ProviderType,
    RelationshipEvidenceType,
    SourceEvidence,
)


# ════════════════════════════════════════════════════════════════════════
#  ENUMS
# ════════════════════════════════════════════════════════════════════════


class RelationshipType(str, Enum):
    """Typed relationship between canonical entities in the graph.

    Only DIRECT and DERIVED evidence is allowed.
    INFERRED and UNKNOWN are prohibited.
    """
    RUNS_ON = "RUNS_ON"
    CONTAINS = "CONTAINS"
    MEMBER_OF = "MEMBER_OF"
    HOSTS = "HOSTS"
    USES = "USES"
    ATTACHED_TO = "ATTACHED_TO"


class EntityType(str, Enum):
    """Canonical entity type for graph node classification.

    Maps 1:1 to the 10 canonical entity domains from Phase 13G-1.
    """
    PHYSICAL = "PHYSICAL"
    OS = "OS"
    PLATFORM = "PLATFORM"
    CLUSTER = "CLUSTER"
    NODE = "NODE"
    EXECUTION_ENVIRONMENT = "EXECUTION_ENVIRONMENT"
    WORKLOAD = "WORKLOAD"
    NETWORK = "NETWORK"
    STORAGE = "STORAGE"
    ACCELERATOR = "ACCELERATOR"


# ════════════════════════════════════════════════════════════════════════
#  GRAPH NODE
# ════════════════════════════════════════════════════════════════════════


class GraphNode(BaseModel):
    """A node in the infrastructure graph.

    Identity = canonical_id (never a separate graph ID).
    Canonical Entity ID == Graph Node ID is the fundamental principle.

    The node is a thin wrapper around the canonical entity's identity
    and provenance. It does NOT duplicate health or resource data —
    those are looked up via canonical_id.
    """
    canonical_id: str = Field(min_length=1)
    entity_type: EntityType
    provider_type: ProviderType
    source_evidence: SourceEvidence

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  GRAPH RELATIONSHIP
# ════════════════════════════════════════════════════════════════════════


class GraphRelationship(BaseModel):
    """A directed edge in the infrastructure graph.

    Identity = (source_id, target_id, relationship_type).
    Duplicates are prevented by the graph builder.

    Evidence type is preserved:
        DIRECT  — explicitly stated by provider (e.g., Pod.spec.nodeName)
        DERIVED — computed from provider data without inference

    INFERRED and UNKNOWN evidence types are NOT allowed.
    """
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    relationship_type: RelationshipType
    evidence_type: RelationshipEvidenceType = RelationshipEvidenceType.DERIVED
    source_evidence: Optional[SourceEvidence] = None
    raw_data: Optional[dict[str, Any]] = None

    model_config = {"extra": "forbid"}

    @property
    def edge_key(self) -> tuple[str, str, RelationshipType]:
        """Unique identity for deduplication."""
        return (self.source_id, self.target_id, self.relationship_type)


# ════════════════════════════════════════════════════════════════════════
#  GRAPH REPORT
# ════════════════════════════════════════════════════════════════════════


class GraphReport(BaseModel):
    """Result of building a unified infrastructure graph.

    Contains graph nodes, relationships, and validation results.

    Graph validation rules:
        [PASS] every node has canonical_id
        [PASS] every edge source exists
        [PASS] every edge target exists
        [PASS] no duplicate edge
        [PASS] no INFERRED edge
        [PASS] no UNKNOWN edge
        [PASS] provenance preserved
    """
    nodes: list[GraphNode] = Field(default_factory=list)
    relationships: list[GraphRelationship] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)

    @property
    def is_valid(self) -> bool:
        return len(self.validation_errors) == 0

    @property
    def has_nodes(self) -> bool:
        return self.node_count > 0

    @property
    def node_ids(self) -> set[str]:
        """Set of all canonical_ids in the graph."""
        return {n.canonical_id for n in self.nodes}
