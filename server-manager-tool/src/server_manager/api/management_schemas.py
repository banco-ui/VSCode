"""Management API Schemas — Phase 22.

Pydantic response models for the Phase 22 Management API layer.

These schemas are thin wrappers that expose existing Phase 13-21
domain service results as JSON-serializable API responses.
No new domain models are introduced — these are API boundary models only.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── System ────────────────────────────────────────────────────────────

class SystemHealthResponse(BaseModel):
    """Liveness probe response."""
    status: str = "ok"


class SystemReadinessResponse(BaseModel):
    """Readiness probe response."""
    ready: bool
    components: dict[str, bool] = Field(default_factory=dict)


# ── Inventory ─────────────────────────────────────────────────────────

class InventorySummaryResponse(BaseModel):
    """Summary of the canonical inventory from the latest discovery run."""
    provider_type: str
    provider_id: Optional[str] = None
    snapshot_id: str
    discovered_at: str
    identified_platform_type: str = "UNKNOWN"
    total_entities: int = 0
    entity_counts: dict[str, int] = Field(default_factory=dict)


class EntityListResponse(BaseModel):
    """Generic list of canonical entities."""
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


# ── Health ────────────────────────────────────────────────────────────

class HealthReportResponse(BaseModel):
    """Health report summary."""
    provider_type: str
    provider_id: Optional[str] = None
    health_status: str
    checked_at: str
    entity_count: int = 0
    results: list[dict[str, Any]] = Field(default_factory=list)


# ── Graph ─────────────────────────────────────────────────────────────

class GraphSummaryResponse(BaseModel):
    """Summary of the infrastructure graph."""
    node_count: int = 0
    relationship_count: int = 0
    node_ids: list[str] = Field(default_factory=list)


# ── Monitoring ────────────────────────────────────────────────────────

class ObservationListResponse(BaseModel):
    """List of monitoring observations."""
    observations: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


# ── Faults ────────────────────────────────────────────────────────────

class FaultListResponse(BaseModel):
    """List of detected faults."""
    faults: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


# ── Visibility ────────────────────────────────────────────────────────

class OperationalSummaryResponse(BaseModel):
    """Operational visibility summary."""
    infrastructure: dict[str, Any]
    health: dict[str, Any]
    resources: dict[str, Any]
    faults: dict[str, Any]
    alerts: dict[str, Any]
    operations: dict[str, Any]
    generated_at: str


class EntityStatusResponse(BaseModel):
    """Operational status for a single entity."""
    entity_id: str
    entity_type: str = ""
    health_status: str = "UNKNOWN"
    availability_status: str = "UNKNOWN"
    active_faults: int = 0
    active_alerts: int = 0
    alert_ids: list[str] = Field(default_factory=list)
    fault_ids: list[str] = Field(default_factory=list)


# ── Operation Preview ─────────────────────────────────────────────────

class OperationPreviewRequest(BaseModel):
    """Request body for operation preview (no execution)."""
    operation_id: str
    operation_type: str
    target_canonical_id: str
    provider_type: str = "UNKNOWN"
    reason: str = ""


class OperationPreviewResponse(BaseModel):
    """Preview result of an operation (no mutation)."""
    operation_id: str
    operation_type: str
    target_canonical_id: str
    resolved: bool = False
    resolved_target_canonical_id: Optional[str] = None
    capability_decision: str = "UNKNOWN"
    expected_effect: str = ""
    safety_result: str = "BLOCKED"
    safety_reason: Optional[str] = None
    authorization_level: str = "READ_ONLY"
    execution_allowed: bool = False
    previewed_at: str


# ── Recovery Preview ──────────────────────────────────────────────────

class RecoveryPreviewRequest(BaseModel):
    """Request body for recovery preview (no execution)."""
    fault_id: str
    action_type: str = "RESTART"
    target_entity_id: Optional[str] = None
    provider_type: str = "UNKNOWN"
    reason: str = ""


class RecoveryPreviewResponse(BaseModel):
    """Preview result of a recovery action (no mutation)."""
    candidate_id: str
    action_id: str
    action_type: str
    target_entity_id: str
    fault_id: str
    expected_effect: str = ""
    safety_result: str = "BLOCKED"
    safety_reason: Optional[str] = None
    supported: bool = False
    previewed_at: str
