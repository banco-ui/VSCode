"""Monitoring Service — Phase 17.

Provider-neutral monitoring service that creates observations from
Phase 15 HealthReports and detects state changes.

    HealthReport (Phase 15)
        ↓
    MonitoringService.monitor()
        ↓
    MonitoringReport (Observations + StateChanges)

The service does NOT:
    ❌ Call provider APIs
    ❌ Generate alerts
    ❌ Perform recovery
    ❌ Persist to database
    ❌ Infer health states
"""
from __future__ import annotations

import logging

from server_manager.health.models import HealthReport

from .models import (
    MonitoringReport,
    Observation,
    StateChange,
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """Provider-neutral monitoring service.

    Consumes HealthReport, creates Observations, and detects StateChanges
    by comparing consecutive observations for the same entity.

    In-memory observation history — no persistence. The history is a
    dict[entity_id → list[Observation]] maintained for the lifetime of
    the service instance.

    Usage::

        service = MonitoringService()
        report = service.monitor(health_report)
        # report.observations — new observations
        # report.state_changes — detected transitions
    """

    def __init__(self) -> None:
        self._observations: dict[str, list[Observation]] = {}
        self._counter: int = 0

    def monitor(self, health_report: HealthReport) -> MonitoringReport:
        """Monitor a health report: create observations + detect state changes.

        Args:
            health_report: Phase 15 HealthReport from health assessment.

        Returns:
            MonitoringReport with new observations and detected state changes.
        """
        new_observations: list[Observation] = []
        state_changes: list[StateChange] = []

        for result in health_report.results:
            entity_id = result.entity_id

            # Get previous observation (if any)
            history = self._observations.get(entity_id, [])
            prev = history[-1] if history else None

            # Create new observation
            self._counter += 1
            obs = Observation.from_health_result(
                result, f"obs-{self._counter}"
            )
            new_observations.append(obs)

            # Store in history
            self._observations.setdefault(entity_id, []).append(obs)

            # Detect state change
            if prev is not None:
                change = self._detect_change(prev, obs)
                if change is not None:
                    state_changes.append(change)

        return MonitoringReport(
            observations=new_observations,
            state_changes=state_changes,
        )

    def observe(self, health_report: HealthReport) -> list[Observation]:
        """Create observations from a health report without state change detection.

        Convenience method for callers that only need observations.
        """
        report = self.monitor(health_report)
        return report.observations

    def get_observations(self, entity_id: str) -> list[Observation]:
        """Get full observation history for an entity."""
        return list(self._observations.get(entity_id, []))

    def get_latest(self, entity_id: str):
        """Get the latest observation for an entity, or None."""
        history = self._observations.get(entity_id, [])
        return history[-1] if history else None

    def get_all_latest(self) -> list[Observation]:
        """Get the latest observation for every observed entity."""
        latest: list[Observation] = []
        for history in self._observations.values():
            if history:
                latest.append(history[-1])
        return latest

    @property
    def entity_count(self) -> int:
        """Number of entities with observation history."""
        return len(self._observations)

    @staticmethod
    def _detect_change(
        prev: Observation, curr: Observation
    ) -> StateChange | None:
        """Detect a state change between two observations.

        Returns None if health and availability are unchanged.
        """
        if (
            prev.health_status == curr.health_status
            and prev.availability_status == curr.availability_status
        ):
            return None

        return StateChange(
            entity_id=curr.entity_id,
            previous_health=prev.health_status,
            current_health=curr.health_status,
            previous_availability=prev.availability_status,
            current_availability=curr.availability_status,
            detected_at=curr.observed_at,
            evidence={
                "previous_observation_id": prev.observation_id,
                "current_observation_id": curr.observation_id,
            },
        )
