"""Threshold Policy — Phase 17.

Configurable resource threshold policy for fault detection.

No hardcoded defaults — all thresholds are None (disabled) by default.
Caller must explicitly set thresholds to enable resource threshold checking.

Threshold values are numeric utilization percentages (0-100).
A value of None means "no threshold check for this level/resource".
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from server_manager.health.models import ResourceType


class ThresholdPolicy(BaseModel):
    """Configurable resource threshold policy.

    All thresholds default to None — meaning no resource threshold
    faults are generated unless the caller explicitly configures them.

    Threshold values represent utilization percentages (0-100).
    Example: cpu_warning=80.0 means CPU utilization >= 80% → WARNING.

    The policy does NOT:
        - Hardcode default thresholds
        - Infer thresholds from capacity
        - Convert units
    """
    cpu_warning: Optional[float] = None
    cpu_critical: Optional[float] = None
    memory_warning: Optional[float] = None
    memory_critical: Optional[float] = None
    storage_warning: Optional[float] = None
    storage_critical: Optional[float] = None
    network_warning: Optional[float] = None
    network_critical: Optional[float] = None
    accelerator_warning: Optional[float] = None
    accelerator_critical: Optional[float] = None

    model_config = {"extra": "forbid"}

    def get_warning(self, resource_type: ResourceType) -> Optional[float]:
        """Get warning threshold for a resource type."""
        return getattr(self, f"{resource_type.value.lower()}_warning", None)

    def get_critical(self, resource_type: ResourceType) -> Optional[float]:
        """Get critical threshold for a resource type."""
        return getattr(self, f"{resource_type.value.lower()}_critical", None)

    @property
    def has_any_threshold(self) -> bool:
        """True if any threshold is configured."""
        return any(
            v is not None
            for v in [
                self.cpu_warning, self.cpu_critical,
                self.memory_warning, self.memory_critical,
                self.storage_warning, self.storage_critical,
                self.network_warning, self.network_critical,
                self.accelerator_warning, self.accelerator_critical,
            ]
        )


# ════════════════════════════════════════════════════════════════════════
#  FAULT DETECTION MODELS
# ════════════════════════════════════════════════════════════════════════
#
# Provider-neutral fault detection models for identifying infrastructure
# issues based on explicit evidence from monitoring observations.
#
# Key principles:
# - Faults require explicit evidence — no inference
# - UNKNOWN is NOT a fault (UNKNOWN != FAILURE, UNKNOWN != HEALTHY)
# - Missing metrics are NOT faults
# - Severity is evidence-based, not guessed
# - ThresholdPolicy is explicit — no hardcoded defaults
# - Fault lifecycle: DETECTED → ONGOING → RESOLVED
# - Deterministic deduplication: same (entity_id, fault_type) → same fault
#

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from server_manager.models.canonical import SourceEvidence


class FaultType(str, Enum):
    """Type of detected fault.

    HEALTH_FAILURE:        Entity health is UNHEALTHY (explicit failure)
    HEALTH_DEGRADED:       Entity health is DEGRADED (explicit degradation)
    AVAILABILITY_FAILURE:  Entity availability is UNAVAILABLE
    RESOURCE_THRESHOLD:    Resource utilization exceeds configured threshold
    STATE_CHANGE:          State transition indicates degradation
    """
    HEALTH_FAILURE = "HEALTH_FAILURE"
    HEALTH_DEGRADED = "HEALTH_DEGRADED"
    AVAILABILITY_FAILURE = "AVAILABILITY_FAILURE"
    RESOURCE_THRESHOLD = "RESOURCE_THRESHOLD"
    STATE_CHANGE = "STATE_CHANGE"


class Severity(str, Enum):
    """Fault severity level.

    INFO:     Informational (e.g., minor state change)
    WARNING:  Degraded state or threshold warning
    CRITICAL: Failure state or critical threshold
    """
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class FaultStatus(str, Enum):
    """Fault lifecycle status.

    DETECTED:  Newly detected in this evaluation cycle
    ONGOING:   Previously detected, still present
    RESOLVED:  Previously detected, no longer present
    """
    DETECTED = "DETECTED"
    ONGOING = "ONGOING"
    RESOLVED = "RESOLVED"


class Fault(BaseModel):
    """A detected infrastructure fault.

    Identity = fault_id (deterministic: based on entity_id + fault_type).

    A fault MUST have evidence. No evidence → no fault.
    """
    fault_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    fault_type: FaultType
    severity: Severity
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: FaultStatus = FaultStatus.DETECTED
    evidence: dict[str, Any] = Field(default_factory=dict)
    source: Optional[SourceEvidence] = None

    model_config = {"extra": "forbid"}


class FaultResult(BaseModel):
    """Result of a fault detection cycle.

    Contains all active faults (newly detected + ongoing), and IDs of
    faults that were resolved in this cycle.
    """
    faults: list[Fault] = Field(default_factory=list)
    newly_detected: list[Fault] = Field(default_factory=list)
    ongoing: list[Fault] = Field(default_factory=list)
    resolved_fault_ids: list[str] = Field(default_factory=list)
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def fault_count(self) -> int:
        return len(self.faults)

    @property
    def has_faults(self) -> bool:
        return len(self.faults) > 0

    @property
    def has_critical(self) -> bool:
        return any(f.severity == Severity.CRITICAL for f in self.faults)

    @property
    def has_warning(self) -> bool:
        return any(f.severity == Severity.WARNING for f in self.faults)
