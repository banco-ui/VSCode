"""Graph package — Phase 16.

Unified Infrastructure Graph for representing canonical entities and
their relationships as a navigable graph structure.

    Canonical Inventory + Relationship Evidence
        ↓
    GraphBuilder
        ↓
    GraphReport (nodes + relationships)
        ↓
    GraphQuery (read-only traversal)

Key principles:
- Graph nodes = canonical entities (canonical_id = node identity)
- Graph edges = relationship evidence (DIRECT/DERIVED only)
- No inference: edges only from existing evidence
- No provider API calls: graph builds from inventory, not live data
"""
from .models import (
    EntityType,
    GraphNode,
    GraphRelationship,
    GraphReport,
    RelationshipType,
)
from .service import GraphBuilder, GraphQuery

__all__ = [
    "EntityType",
    "GraphNode",
    "GraphRelationship",
    "GraphReport",
    "RelationshipType",
    "GraphBuilder",
    "GraphQuery",
]
