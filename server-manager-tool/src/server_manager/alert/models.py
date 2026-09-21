"""Alert Domain Models — Phase 11C.

Alert lifecycle, severity, and classification models.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
    """Alert lifecycle status."""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    """Alert classification types."""
    HEALTH_CRITICAL = "HEALTH_CRITICAL"
    HEALTH_WARNING = "HEALTH_WARNING"
    VERIFICATION_DISCREPANCY = "VERIFICATION_DISCREPANCY"
    COLLECTION_FAILURE = "COLLECTION_FAILURE"
    SCHEDULER_FAILURE = "SCHEDULER_FAILURE"


class ResourceType(str, Enum):
    """Resource classification types."""
    SYSTEM = "system"
    STORAGE_CONTROLLER = "storage_controller"
    PHYSICAL_DISK = "physical_disk"
    VIRTUAL_DISK = "virtual_disk"
    NETWORK_INTERFACE = "network_interface"
    MEMORY = "memory"
    CPU = "cpu"
    SERVICE = "service"


class Alert(BaseModel):
    """Alert domain model.
    
    Attributes:
        alert_id: Unique identifier for this alert.
        fingerprint: SHA-256 hash for deduplication (64 hex chars).
        fingerprint_version: Fingerprint algorithm version (default: 1).
        server_id: Reference to server.
        alert_type: Alert classification.
        resource_type: Resource classification.
        resource_id: Resource identifier (optional).
        condition: Condition expression.
        severity: Alert severity (INFO, WARNING, CRITICAL).
        status: Alert lifecycle status (OPEN, ACKNOWLEDGED, RESOLVED).
        created_at: ISO 8601 timestamp of creation.
        updated_at: ISO 8601 timestamp of last update.
        acknowledged_at: ISO 8601 timestamp of acknowledgement (nullable).
        acknowledged_by: User ID or "system" (nullable).
        acknowledge_note: Optional acknowledgement note (nullable).
        resolved_at: ISO 8601 timestamp of resolution (nullable).
        resolution_note: Resolution reason (nullable).
        consecutive_failure_count: N threshold tracking counter.
        consecutive_ok_count: M threshold tracking counter.
        first_snapshot_id: First detection snapshot reference.
        last_snapshot_id: Most recent detection snapshot reference.
        recovery_count: Recovery operation count.
        metadata_json: Additional metadata (JSON).
    """
    alert_id: str
    fingerprint: str
    fingerprint_version: int = 1
    server_id: str
    alert_type: AlertType
    resource_type: ResourceType
    resource_id: Optional[str] = None
    condition: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN
    created_at: str = ""
    updated_at: str = ""
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledge_note: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_note: Optional[str] = None
    consecutive_failure_count: int = 0
    consecutive_ok_count: int = 0
    first_snapshot_id: Optional[str] = None
    last_snapshot_id: Optional[str] = None
    recovery_count: int = 0
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"extra": "forbid"}
