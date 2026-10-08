"""Alert & Operational Visibility Models — Phase 20.

Provider-neutral Alert model that represents Phase 17 detected Faults as
operational notifications, plus read-only operational summary models.

    Fault (Phase 17)
        ↓
    Alert (Phase 20)
        ↓
    Alert lifecycle (OPEN → ACKNOWLEDGED → RESOLVED → CLOSED)
        ↓
    Operational Visibility (read-only summary)

Key principles:
- Alert requires a source Fault — no alert without fault evidence
- Alert identity is deterministic (derived from fault_id)
- Fault evidence and severity are preserved — no alteration
- UNKNOWN fault does NOT create an alert
- Missing evidence does NOT create an alert
- No duplicate active alerts for the same fault
- Alert lifecycle is deterministic — invalid transitions rejected
- Alert acknowledgement is operational state, NOT infrastructure mutation
- Operational visibility is READ-ONLY — no mutation of any kind
- No inference: graph relationships ≠ recovery causality

This module does NOT implement:
    ❌ External alert delivery (email, Slack, PagerDuty, etc.)
    ❌ Persistent alert storage (database)
    ❌ Automatic recovery / automatic operation
    ❌ Alert-triggered operations
    ❌ Root cause analysis
    ❌ Time-series storage
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from server_manager.fault.models import Fault, FaultStatus, FaultType, Severity
from server_manager.models.canonical import ProviderType


# ════════════════════════════════════════════════════════════════════════
#  ALERT STATUS
# ════════════════════════════════════════════════════════════════════════


class AlertStatus(str, Enum):
    """Alert lifecycle status.

    Lifecycle:
        OPEN          — newly created from a detected fault
        ACKNOWLEDGED  — acknowledged by an operator (operational, not infra)
        RESOLVED      — underlying fault resolved or manually resolved
        CLOSED        — alert lifecycle complete

    Valid transitions:
        OPEN          → ACKNOWLEDGED
        OPEN          → RESOLVED
        ACKNOWLEDGED  → RESOLVED
        RESOLVED      → CLOSED

    All other transitions are rejected.
    Reopening is NOT supported (deferred to a future phase).
    """
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


# ════════════════════════════════════════════════════════════════════════
#  ALERT IDENTITY
# ════════════════════════════════════════════════════════════════════════


def _make_alert_id(fault_id: str) -> str:
    """Generate deterministic alert ID from fault_id.

    Prefixed with 'alert:' to distinguish from fault_id while
    maintaining traceability. Same fault_id → same alert_id.
    """
    return f"alert:{fault_id}"


# ════════════════════════════════════════════════════════════════════════
#  ALERT MODEL
# ════════════════════════════════════════════════════════════════════════


class Alert(BaseModel):
    """An operational alert derived from a detected fault.

    Identity = alert_id (deterministic: derived from fault_id).

    An alert MUST have:
        - fault_id (traceability to source fault)
        - entity_id (affected canonical entity)
        - fault_type (preserved from fault)
        - severity (preserved from fault)
        - evidence (preserved from fault)

    An alert does NOT:
        - Automatically trigger recovery or operations
        - Infer root cause
        - Modify infrastructure
        - Modify fault detection state
    """
    alert_id: str = Field(min_length=1)
    fault_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    fault_type: FaultType
    severity: Severity
    status: AlertStatus = AlertStatus.OPEN
    provider_type: ProviderType = ProviderType.UNKNOWN
    canonical_entity_type: str = ""
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    source: Optional[Any] = None  # SourceEvidence from fault
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None

    model_config = {"extra": "forbid"}

    @property
    def is_active(self) -> bool:
        """True if alert is OPEN or ACKNOWLEDGED."""
        return self.status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)

    @field_validator("alert_id")
    @classmethod
    def validate_alert_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("alert_id must be non-empty")
        return v


# ════════════════════════════════════════════════════════════════════════
#  ALERT CREATION RESULT
# ════════════════════════════════════════════════════════════════════════


class AlertCreationResult(BaseModel):
    """Result of attempting to create an alert from a fault.

    If the fault is not eligible (UNKNOWN, missing evidence, duplicate),
    alert will be None and reason will explain why.
    """
    alert: Optional[Alert] = None
    created: bool = False
    reason: str = ""

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  ALERT ERRORS
# ════════════════════════════════════════════════════════════════════════


class AlertTransitionError(Exception):
    """Raised when an invalid alert lifecycle transition is attempted."""

    def __init__(
        self,
        alert_id: str,
        from_status: AlertStatus,
        to_status: AlertStatus,
    ) -> None:
        self.alert_id = alert_id
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Invalid alert transition: {alert_id} "
            f"{from_status.value} → {to_status.value}"
        )


class AlertNotFoundError(Exception):
    """Raised when an alert is not found by alert_id."""

    def __init__(self, alert_id: str) -> None:
        self.alert_id = alert_id
        super().__init__(f"Alert not found: {alert_id}")


# ════════════════════════════════════════════════════════════════════════
#  OPERATIONAL VISIBILITY SUMMARY MODELS
# ════════════════════════════════════════════════════════════════════════


class InfrastructureSummary(BaseModel):
    """Read-only summary of known infrastructure entities.

    All counts come from actual CanonicalInventory data — no invented values.
    """
    total_entities: int = 0
    platforms: int = 0
    clusters: int = 0
    nodes: int = 0
    execution_environments: int = 0
    workloads: int = 0
    networks: int = 0
    storages: int = 0
    accelerators: int = 0
    physicals: int = 0
    os_entities: int = 0

    model_config = {"extra": "forbid"}


class HealthSummary(BaseModel):
    """Read-only summary of health status across entities.

    Exposes existing Phase 15 HealthReport results without recalculation.
    """
    total_assessed: int = 0
    healthy: int = 0
    degraded: int = 0
    unhealthy: int = 0
    unknown: int = 0

    model_config = {"extra": "forbid"}


class ResourceSummary(BaseModel):
    """Read-only summary of resource status.

    Exposes existing resource status/capacity without aggregation
    or time-series storage.
    """
    entities_with_resources: int = 0
    total_resource_statuses: int = 0
    total_capacity_infos: int = 0

    model_config = {"extra": "forbid"}


class FaultSummary(BaseModel):
    """Read-only summary of Phase 17 fault state.

    Exposes existing fault detection results without detecting new faults.
    """
    total_faults: int = 0
    detected: int = 0
    ongoing: int = 0
    resolved: int = 0

    model_config = {"extra": "forbid"}


class AlertSummary(BaseModel):
    """Read-only summary of Phase 20 alert state."""
    total_alerts: int = 0
    open: int = 0
    acknowledged: int = 0
    resolved: int = 0
    closed: int = 0

    model_config = {"extra": "forbid"}


class OperationSummary(BaseModel):
    """Read-only summary of Phase 18/19 operation/recovery state.

    Exposes existing recovery and operation results without execution.
    """
    total_recovery_candidates: int = 0
    recovery_executed: int = 0
    recovery_verified: int = 0
    recovery_failed: int = 0
    total_operation_results: int = 0
    operations_executed: int = 0
    operations_verified: int = 0
    operations_failed: int = 0

    model_config = {"extra": "forbid"}


class OperationalSummary(BaseModel):
    """Top-level read-only operational visibility summary.

    Aggregates all sub-summaries into a single view.
    All data comes from existing models/services — no mutation, no inference.
    """
    infrastructure: InfrastructureSummary = Field(
        default_factory=InfrastructureSummary
    )
    health: HealthSummary = Field(default_factory=HealthSummary)
    resources: ResourceSummary = Field(default_factory=ResourceSummary)
    faults: FaultSummary = Field(default_factory=FaultSummary)
    alerts: AlertSummary = Field(default_factory=AlertSummary)
    operations: OperationSummary = Field(default_factory=OperationSummary)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    model_config = {"extra": "forbid"}


class EntityStatus(BaseModel):
    """Read-only operational status for a single entity.

    Aggregates health, fault, and alert information for one entity.
    No mutation — pure read-only view.
    """
    entity_id: str = Field(min_length=1)
    entity_type: str = ""
    health_status: str = "UNKNOWN"
    availability_status: str = "UNKNOWN"
    active_faults: int = 0
    active_alerts: int = 0
    alert_ids: list[str] = Field(default_factory=list)
    fault_ids: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


