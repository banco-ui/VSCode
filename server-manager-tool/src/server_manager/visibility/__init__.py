"""Alert & Operational Visibility package — Phase 20.

Provider-neutral Alert model and read-only operational visibility.

    Fault (Phase 17)
        ↓
    Alert (Phase 20)
        ↓
    Alert lifecycle (OPEN → ACKNOWLEDGED → RESOLVED → CLOSED)
        ↓
    Operational Visibility (read-only summary)

SAFETY PRINCIPLES:
    - Alert requires a source Fault — no alert without fault evidence
    - Alert identity is deterministic (derived from fault_id)
    - Fault evidence and severity are preserved
    - UNKNOWN fault does NOT create an alert
    - Missing evidence does NOT create an alert
    - No duplicate active alerts for the same fault
    - Alert lifecycle is deterministic — invalid transitions rejected
    - Operational visibility is 100% read-only
    - No inference: graph relationships ≠ recovery causality
    - In-memory only — no persistent storage
"""
from .models import (
    Alert,
    AlertCreationResult,
    AlertNotFoundError,
    AlertStatus,
    AlertTransitionError,
    EntityStatus,
    HealthSummary,
    InfrastructureSummary,
    OperationalSummary,
    OperationSummary,
    ResourceSummary,
    FaultSummary,
    AlertSummary,
)
from .service import AlertService, OperationalVisibilityService

__all__ = [
    # Models
    "Alert",
    "AlertStatus",
    "AlertCreationResult",
    "AlertTransitionError",
    "AlertNotFoundError",
    # Summary models
    "OperationalSummary",
    "InfrastructureSummary",
    "HealthSummary",
    "ResourceSummary",
    "FaultSummary",
    "AlertSummary",
    "OperationSummary",
    "EntityStatus",
    # Services
    "AlertService",
    "OperationalVisibilityService",
]
