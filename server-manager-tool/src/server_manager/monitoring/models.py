"""Monitoring Domain Models — Phase 17.

Provider-neutral observation models for monitoring the state of canonical
entities discovered in Phase 14 and assessed in Phase 15.

Key principles:
- Observation wraps HealthResult data — does NOT duplicate Phase 15 models
- ResourceStatus (Phase 15) is reused as the metric observation model
- UNKNOWN is NOT treated as HEALTHY or FAILURE
- Missing metric is NOT treated as zero
- State changes are detected by comparing consecutive observations
- No time-series persistence — in-memory observation sequence only
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from server_manager.health.models import (
    AvailabilityStatus,
    CapacityInfo,
    HealthResult,
    HealthStatus,
    ResourceStatus,
)
from server_manager.models.canonical import SourceEvidence


class Observation(BaseModel):
    """A point-in-time observation of a canonical entity's state.

    Captures health, availability, resource metrics, and evidence at a
    specific moment. Identity = observation_id.

    The observation does NOT:
        - Duplicate HealthResult — it extracts and preserves its data
        - Infer health — status comes directly from HealthResult
        - Convert UNKNOWN to HEALTHY
        - Treat missing metrics as zero
    """
    observation_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    entity_type: str = ""
    observed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: Optional[SourceEvidence] = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    resource_statuses: list[ResourceStatus] = Field(default_factory=list)
    capacity_infos: list[CapacityInfo] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @classmethod
    def from_health_result(
        cls,
        result: HealthResult,
        observation_id: str,
    ) -> "Observation":
        """Create an Observation from a Phase 15 HealthResult.

        This is the ONLY construction path from health assessment data.
        """
        return cls(
            observation_id=observation_id,
            entity_id=result.entity_id,
            entity_type=result.entity_type,
            observed_at=result.checked_at,
            source=result.source_evidence,
            health_status=result.status,
            availability_status=result.availability,
            resource_statuses=list(result.resource_statuses),
            capacity_infos=list(result.capacity_infos),
            evidence={
                "warnings": list(result.warnings),
                "errors": list(result.errors),
            },
        )


class StateChange(BaseModel):
    """A detected state transition between two consecutive observations.

    Only created when status actually changed (no change → no StateChange).
    State changes are NOT faults — they are evidence for FaultDetectionService.
    """
    entity_id: str = Field(min_length=1)
    previous_health: HealthStatus
    current_health: HealthStatus
    previous_availability: AvailabilityStatus
    current_availability: AvailabilityStatus
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @property
    def health_changed(self) -> bool:
        return self.previous_health != self.current_health

    @property
    def availability_changed(self) -> bool:
        return self.previous_availability != self.current_availability

    @property
    def is_degradation(self) -> bool:
        """True if the transition represents a degradation.

        Transitions to/from UNKNOWN are NOT degradations.
        """
        _order = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.UNKNOWN: 1,
            HealthStatus.DEGRADED: 2,
            HealthStatus.UNHEALTHY: 3,
        }
        prev_h = _order.get(self.previous_health, 1)
        curr_h = _order.get(self.current_health, 1)
        if curr_h > prev_h and self.current_health != HealthStatus.UNKNOWN:
            return True
        if (
            self.previous_availability == AvailabilityStatus.AVAILABLE
            and self.current_availability == AvailabilityStatus.UNAVAILABLE
        ):
            return True
        return False


class MonitoringReport(BaseModel):
    """Result of a monitoring cycle.

    Contains observations created in this cycle and state changes
    detected from comparing with previous observations.
    """
    observations: list[Observation] = Field(default_factory=list)
    state_changes: list[StateChange] = Field(default_factory=list)
    monitored_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    @property
    def state_change_count(self) -> int:
        return len(self.state_changes)

    @property
    def has_state_changes(self) -> bool:
        return len(self.state_changes) > 0
