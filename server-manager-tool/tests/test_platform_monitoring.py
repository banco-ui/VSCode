"""Monitoring Tests — Phase 17.

Tests the monitoring observation pipeline:

    HealthReport (Phase 15)
        -> MonitoringService.monitor()
        -> MonitoringReport (Observations + StateChanges)

All fixtures are synthetic/in-memory. No live Kubernetes connection.
"""
from __future__ import annotations

import pytest

from server_manager.health import (
    AvailabilityStatus, HealthReport, HealthResult, HealthStatus,
    ResourceType, ResourceStatus,
)
from server_manager.models.canonical import ProviderType, SourceEvidence
from server_manager.models.enums import Confidence
from server_manager.monitoring import (
    MonitoringReport, MonitoringService, Observation, StateChange,
)
from server_manager.orchestrator.models import OrchestrationStatus


def make_source(provider=ProviderType.KUBERNETES):
    return SourceEvidence(provider_type=provider, confidence=Confidence.HIGH)


def make_health_result(
    entity_id="canon-node-01", entity_type="NODE",
    status=HealthStatus.HEALTHY,
    availability=AvailabilityStatus.AVAILABLE,
    resource_statuses=None, source=None,
):
    return HealthResult(
        entity_id=entity_id, entity_type=entity_type,
        status=status, availability=availability,
        source_evidence=source or make_source(),
        resource_statuses=resource_statuses or [],
    )


def make_health_report(results=None):
    return HealthReport(
        provider_type=ProviderType.KUBERNETES,
        health_status=OrchestrationStatus.SUCCESS,
        results=results or [],
    )


class TestObservation:
    """Observation model construction and field preservation."""

    def test_observation_from_health_result(self):
        result = make_health_result()
        obs = Observation.from_health_result(result, "obs-1")
        assert obs.observation_id == "obs-1"
        assert obs.entity_id == "canon-node-01"
        assert obs.entity_type == "NODE"
        assert obs.health_status == HealthStatus.HEALTHY
        assert obs.availability_status == AvailabilityStatus.AVAILABLE

    def test_observation_timestamp(self):
        result = make_health_result()
        result.checked_at = "2026-01-01T00:00:00+00:00"
        obs = Observation.from_health_result(result, "obs-1")
        assert obs.observed_at == "2026-01-01T00:00:00+00:00"

    def test_observation_canonical_id_association(self):
        result = make_health_result(entity_id="canon-k8s-node-abc")
        obs = Observation.from_health_result(result, "obs-1")
        assert obs.entity_id == "canon-k8s-node-abc"

    def test_observation_provenance(self):
        source = make_source(provider=ProviderType.VMWARE)
        result = make_health_result(source=source)
        obs = Observation.from_health_result(result, "obs-1")
        assert obs.source.provider_type == ProviderType.VMWARE

    def test_observation_health_status(self):
        for status in HealthStatus:
            result = make_health_result(status=status)
            obs = Observation.from_health_result(result, "obs-1")
            assert obs.health_status == status

    def test_observation_availability_status(self):
        for avail in AvailabilityStatus:
            result = make_health_result(availability=avail)
            obs = Observation.from_health_result(result, "obs-1")
            assert obs.availability_status == avail

    def test_observation_resource_statuses(self):
        rs = ResourceStatus(
            resource_type=ResourceType.CPU, utilization="45",
            unit="%", source_evidence=make_source(),
        )
        result = make_health_result(resource_statuses=[rs])
        obs = Observation.from_health_result(result, "obs-1")
        assert len(obs.resource_statuses) == 1
        assert obs.resource_statuses[0].utilization == "45"

    def test_observation_missing_metric_not_zero(self):
        rs = ResourceStatus(
            resource_type=ResourceType.MEMORY, utilization=None,
            source_evidence=make_source(),
        )
        result = make_health_result(resource_statuses=[rs])
        obs = Observation.from_health_result(result, "obs-1")
        assert obs.resource_statuses[0].utilization is None

    def test_observation_unknown_handling(self):
        result = make_health_result(
            status=HealthStatus.UNKNOWN,
            availability=AvailabilityStatus.UNKNOWN,
        )
        obs = Observation.from_health_result(result, "obs-1")
        assert obs.health_status == HealthStatus.UNKNOWN
        assert obs.availability_status == AvailabilityStatus.UNKNOWN

    def test_observation_evidence_preserved(self):
        result = make_health_result()
        result.warnings = ["disk pressure detected"]
        result.errors = ["node unreachable"]
        obs = Observation.from_health_result(result, "obs-1")
        assert "disk pressure detected" in obs.evidence["warnings"]
        assert "node unreachable" in obs.evidence["errors"]



class TestMonitoringService:
    """MonitoringService observation and state change detection."""

    def test_monitor_creates_observations(self):
        report = make_health_report([
            make_health_result(entity_id="e1"),
            make_health_result(entity_id="e2"),
        ])
        service = MonitoringService()
        mon_report = service.monitor(report)
        assert mon_report.observation_count == 2

    def test_monitor_no_state_changes_first_cycle(self):
        report = make_health_report([make_health_result()])
        service = MonitoringService()
        mon_report = service.monitor(report)
        assert mon_report.state_change_count == 0

    def test_monitor_detects_health_state_change(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(entity_id="e1", status=HealthStatus.HEALTHY),
        ]))
        mon_report = service.monitor(make_health_report([
            make_health_result(entity_id="e1", status=HealthStatus.UNHEALTHY),
        ]))
        assert mon_report.state_change_count == 1
        change = mon_report.state_changes[0]
        assert change.previous_health == HealthStatus.HEALTHY
        assert change.current_health == HealthStatus.UNHEALTHY

    def test_monitor_detects_availability_state_change(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(availability=AvailabilityStatus.AVAILABLE),
        ]))
        mon_report = service.monitor(make_health_report([
            make_health_result(availability=AvailabilityStatus.UNAVAILABLE),
        ]))
        assert mon_report.state_change_count == 1
        change = mon_report.state_changes[0]
        assert change.previous_availability == AvailabilityStatus.AVAILABLE
        assert change.current_availability == AvailabilityStatus.UNAVAILABLE

    def test_monitor_no_change_same_state(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(status=HealthStatus.HEALTHY),
        ]))
        mon_report = service.monitor(make_health_report([
            make_health_result(status=HealthStatus.HEALTHY),
        ]))
        assert mon_report.state_change_count == 0

    def test_monitor_preserves_unknown(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(status=HealthStatus.UNKNOWN),
        ]))
        mon_report = service.monitor(make_health_report([
            make_health_result(status=HealthStatus.UNKNOWN),
        ]))
        assert mon_report.state_change_count == 0

    def test_monitor_multiple_entities(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(entity_id="e1", status=HealthStatus.HEALTHY),
            make_health_result(entity_id="e2", status=HealthStatus.HEALTHY),
        ]))
        mon_report = service.monitor(make_health_report([
            make_health_result(entity_id="e1", status=HealthStatus.DEGRADED),
            make_health_result(entity_id="e2", status=HealthStatus.HEALTHY),
        ]))
        assert mon_report.state_change_count == 1
        assert mon_report.state_changes[0].entity_id == "e1"

    def test_monitor_get_observations_history(self):
        service = MonitoringService()
        for _ in range(3):
            service.monitor(make_health_report([
                make_health_result(entity_id="e1"),
            ]))
        history = service.get_observations("e1")
        assert len(history) == 3

    def test_monitor_get_latest(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(entity_id="e1", status=HealthStatus.HEALTHY),
        ]))
        service.monitor(make_health_report([
            make_health_result(entity_id="e1", status=HealthStatus.DEGRADED),
        ]))
        latest = service.get_latest("e1")
        assert latest is not None
        assert latest.health_status == HealthStatus.DEGRADED

    def test_monitor_entity_count(self):
        service = MonitoringService()
        service.monitor(make_health_report([
            make_health_result(entity_id="e1"),
            make_health_result(entity_id="e2"),
        ]))
        assert service.entity_count == 2

    def test_state_change_is_degradation_property(self):
        change = StateChange(
            entity_id="e1",
            previous_health=HealthStatus.HEALTHY,
            current_health=HealthStatus.UNHEALTHY,
            previous_availability=AvailabilityStatus.AVAILABLE,
            current_availability=AvailabilityStatus.AVAILABLE,
        )
        assert change.is_degradation is True

    def test_state_change_not_degradation_for_unknown(self):
        change = StateChange(
            entity_id="e1",
            previous_health=HealthStatus.HEALTHY,
            current_health=HealthStatus.UNKNOWN,
            previous_availability=AvailabilityStatus.AVAILABLE,
            current_availability=AvailabilityStatus.UNKNOWN,
        )
        assert change.is_degradation is False

    def test_state_change_not_degradation_for_recovery(self):
        change = StateChange(
            entity_id="e1",
            previous_health=HealthStatus.UNHEALTHY,
            current_health=HealthStatus.HEALTHY,
            previous_availability=AvailabilityStatus.UNAVAILABLE,
            current_availability=AvailabilityStatus.AVAILABLE,
        )
        assert change.is_degradation is False
