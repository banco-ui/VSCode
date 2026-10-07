"""Fault Detection Service — Phase 17.

Provider-neutral fault detection service that consumes monitoring
observations and state changes, applies deterministic fault rules,
and produces FaultResult.

    Monitoring Observations + State Changes
        ↓
    FaultDetectionService.detect()
        ↓
    Evidence validation → Fault rules → FaultResult

The service does NOT:
    ❌ Infer root cause
    ❌ Call provider APIs
    ❌ Perform recovery
    ❌ Generate alerts
    ❌ Create graph edges
    ❌ Treat UNKNOWN as fault
    ❌ Treat missing metrics as fault

Deterministic: same input → same output.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from server_manager.graph.models import GraphRelationship
from server_manager.graph.service import GraphQuery
from server_manager.health.models import (
    AvailabilityStatus,
    HealthStatus,
    ResourceType,
)

from .models import (
    Fault,
    FaultResult,
    FaultStatus,
    FaultType,
    Severity,
    ThresholdPolicy,
)
from ..monitoring.models import Observation, StateChange

logger = logging.getLogger(__name__)


def _parse_utilization(value: Optional[str]) -> Optional[float]:
    """Parse utilization string to float. Returns None if not parseable."""
    if value is None:
        return None
    try:
        return float(str(value).rstrip("%").strip())
    except (ValueError, TypeError):
        return None


def _make_fault_id(
    entity_id: str,
    fault_type: FaultType,
    resource_type: Optional[str] = None,
) -> str:
    """Generate deterministic fault ID for deduplication."""
    parts = [entity_id, fault_type.value]
    if resource_type:
        parts.append(resource_type)
    return ":".join(parts)



class FaultDetectionService:
    """Provider-neutral fault detection service.

    Fault rules (evidence-based, no inference):
        UNHEALTHY        → HEALTH_FAILURE (CRITICAL)
        DEGRADED         → HEALTH_DEGRADED (WARNING)
        UNAVAILABLE      → AVAILABILITY_FAILURE (CRITICAL)
        Threshold exceed → RESOURCE_THRESHOLD (WARNING/CRITICAL)
        State degradation→ STATE_CHANGE (CRITICAL/WARNING)

    UNKNOWN → NO FAULT
    Missing metric → NO FAULT
    Missing capacity → NO FAULT
    """

    def __init__(
        self,
        threshold_policy: Optional[ThresholdPolicy] = None,
    ) -> None:
        self._threshold_policy = threshold_policy or ThresholdPolicy()
        self._active_faults: dict[str, Fault] = {}

    def detect(
        self,
        observations: list[Observation],
        state_changes: Optional[list[StateChange]] = None,
    ) -> FaultResult:
        """Detect faults from observations and state changes."""
        if state_changes is None:
            state_changes = []

        current_issues: dict[str, Fault] = {}

        for obs in observations:
            for fault in self._evaluate_observation(obs):
                current_issues[fault.fault_id] = fault

        for change in state_changes:
            for fault in self._evaluate_state_change(change):
                current_issues[fault.fault_id] = fault

        newly_detected: list[Fault] = []
        ongoing: list[Fault] = []
        resolved_ids: list[str] = []

        for fault_id, new_fault in current_issues.items():
            if fault_id in self._active_faults:
                existing = self._active_faults[fault_id]
                existing.status = FaultStatus.ONGOING
                ongoing.append(existing)
            else:
                new_fault.status = FaultStatus.DETECTED
                self._active_faults[fault_id] = new_fault
                newly_detected.append(new_fault)

        for fault_id in list(self._active_faults.keys()):
            if fault_id not in current_issues:
                existing = self._active_faults[fault_id]
                existing.status = FaultStatus.RESOLVED
                resolved_ids.append(existing.fault_id)
                del self._active_faults[fault_id]

        all_faults = newly_detected + ongoing

        return FaultResult(
            faults=all_faults,

    def _evaluate_observation(self, obs: Observation) -> list[Fault]:
        """Evaluate a single observation for fault conditions.

        UNKNOWN → NO FAULT
        """
        faults: list[Fault] = []
        detected_at = obs.observed_at
        source = obs.source
        base_ev = {
            "entity_type": obs.entity_type,
            "observation_id": obs.observation_id,
            **obs.evidence,
        }

        # HEALTH_FAILURE — explicit UNHEALTHY evidence
        if obs.health_status == HealthStatus.UNHEALTHY:
            faults.append(Fault(
                fault_id=_make_fault_id(obs.entity_id, FaultType.HEALTH_FAILURE),
                entity_id=obs.entity_id,
                fault_type=FaultType.HEALTH_FAILURE,
                severity=Severity.CRITICAL,
                detected_at=detected_at,
                evidence={"health_status": obs.health_status.value, **base_ev},
                source=source,
            ))
        elif obs.health_status == HealthStatus.DEGRADED:
            # HEALTH_DEGRADED — explicit DEGRADED evidence
            faults.append(Fault(
                fault_id=_make_fault_id(obs.entity_id, FaultType.HEALTH_DEGRADED),
                entity_id=obs.entity_id,
                fault_type=FaultType.HEALTH_DEGRADED,
                severity=Severity.WARNING,
                detected_at=detected_at,
                evidence={"health_status": obs.health_status.value, **base_ev},
                source=source,
            ))

        # AVAILABILITY_FAILURE — explicit UNAVAILABLE evidence
        if obs.availability_status == AvailabilityStatus.UNAVAILABLE:
            faults.append(Fault(
                fault_id=_make_fault_id(obs.entity_id, FaultType.AVAILABILITY_FAILURE),
                entity_id=obs.entity_id,
                fault_type=FaultType.AVAILABILITY_FAILURE,
                severity=Severity.CRITICAL,
                detected_at=detected_at,
                evidence={"availability_status": obs.availability_status.value, **base_ev},
                source=source,
            ))


    def _check_thresholds(self, obs: Observation) -> list[Fault]:
        """Check resource utilization against configured thresholds.

        Missing utilization (None) → NO FAULT.
        Unparseable utilization → NO FAULT.
        No threshold configured → NO FAULT.
        """
        faults: list[Fault] = []

        for rs in obs.resource_statuses:
            util = _parse_utilization(rs.utilization)
            if util is None:
                continue

            rt = rs.resource_type
            warning = self._threshold_policy.get_warning(rt)
            critical = self._threshold_policy.get_critical(rt)

            if critical is not None and util >= critical:
                faults.append(Fault(
                    fault_id=_make_fault_id(
                        obs.entity_id, FaultType.RESOURCE_THRESHOLD,
                        resource_type=rt.value,
                    ),
                    entity_id=obs.entity_id,
                    fault_type=FaultType.RESOURCE_THRESHOLD,
                    severity=Severity.CRITICAL,
                    detected_at=obs.observed_at,
                    evidence={
                        "resource_type": rt.value,
                        "utilization": rs.utilization,
                        "threshold_critical": critical,
                        "threshold_exceeded": "critical",
                        "observation_id": obs.observation_id,
                    },
                    source=obs.source,
                ))
            elif warning is not None and util >= warning:
                faults.append(Fault(
                    fault_id=_make_fault_id(
                        obs.entity_id, FaultType.RESOURCE_THRESHOLD,
                        resource_type=rt.value,
                    ),
                    entity_id=obs.entity_id,
                    fault_type=FaultType.RESOURCE_THRESHOLD,
                    severity=Severity.WARNING,
                    detected_at=obs.observed_at,
                    evidence={
                        "resource_type": rt.value,
                        "utilization": rs.utilization,
                        "threshold_warning": warning,
                        "threshold_exceeded": "warning",
                        "observation_id": obs.observation_id,
                    },
                    source=obs.source,
                ))

        return faults

        # RESOURCE_THRESHOLD — only if policy is configured
        if self._threshold_policy.has_any_threshold:
            faults.extend(self._check_thresholds(obs))

        return faults

            newly_detected=newly_detected,
            ongoing=ongoing,
            resolved_fault_ids=resolved_ids,
        )
