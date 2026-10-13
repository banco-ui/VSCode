"""StarlingX Health Extractor — Phase 28E.

Extracts health from StarlingX canonical entities (Platform, Node).

    CanonicalInventory (Phase 14)
        ↓
    StarlingXHealthExtractor.extract_health()
        ↓
    HealthResult per entity

Health evidence sources (stored in entity metadata by normalizer):
    1. FM alarms → entity health (critical → UNHEALTHY, warning → DEGRADED)
    2. sysinv host availability → node health
    3. sysinv host operational state → node health
    4. Platform memory threshold → node resource status

Key principles:
    - UNKNOWN is NOT treated as HEALTHY (no evidence ≠ healthy)
    - Missing metrics are NOT faults
    - FM Critical and Redfish Critical are SEPARATE health results
      (independent lifecycles — do NOT merge)
"""
from __future__ import annotations

import logging
from typing import Any

from server_manager.discovery.models import CanonicalInventory
from server_manager.health.models import (
    AvailabilityStatus,
    HealthResult,
    HealthStatus,
    ResourceStatus,
    ResourceType,
)
from server_manager.models.canonical import Node, Platform

from .service import HealthExtractor

logger = logging.getLogger(__name__)

_SEVERITY_TO_HEALTH: dict[str, HealthStatus] = {
    "critical": HealthStatus.UNHEALTHY,
    "major": HealthStatus.UNHEALTHY,
    "warning": HealthStatus.DEGRADED,
    "minor": HealthStatus.DEGRADED,
    "info": HealthStatus.HEALTHY,
}

_AVAILABILITY_TO_HEALTH: dict[str, HealthStatus] = {
    "available": HealthStatus.HEALTHY,
    "degraded": HealthStatus.DEGRADED,
    "offline": HealthStatus.UNHEALTHY,
    "in-test": HealthStatus.UNKNOWN,
    "intest": HealthStatus.UNKNOWN,
}

_AVAILABILITY_TO_AVAIL: dict[str, AvailabilityStatus] = {
    "available": AvailabilityStatus.AVAILABLE,
    "degraded": AvailabilityStatus.AVAILABLE,
    "offline": AvailabilityStatus.UNAVAILABLE,
    "in-test": AvailabilityStatus.UNKNOWN,
    "intest": AvailabilityStatus.UNKNOWN,
}


class StarlingXHealthExtractor(HealthExtractor):
    """StarlingX-specific health extractor.

    FM Critical and Redfish Critical are NOT merged — they produce
    independent HealthResults with different evidence sources.
    """

    def extract_health(
        self, inventory: CanonicalInventory
    ) -> list[HealthResult]:
        """Extract health results from all StarlingX entities."""
        results: list[HealthResult] = []
        for platform in inventory.platforms:
            results.append(self._assess_platform(platform))
        for node in inventory.nodes:
            results.append(self._assess_node(node))
        return results

    def _assess_platform(self, platform: Platform) -> HealthResult:
        """Assess platform health from FM event log in metadata."""
        starlingx_data = platform.metadata.get("starlingx", {})
        event_log = starlingx_data.get("fm_event_log", [])
        critical_events = [
            e for e in event_log if isinstance(e, dict)
            and str(e.get("severity", "")).lower() in ("critical", "major")
        ]
        warning_events = [
            e for e in event_log if isinstance(e, dict)
            and str(e.get("severity", "")).lower() in ("warning", "minor")
        ]
        if critical_events:
            status = HealthStatus.UNHEALTHY
        elif warning_events:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNKNOWN  # NOT HEALTHY
        return HealthResult(
            entity_id=platform.canonical_id,
            entity_type="Platform",
            status=status,
            availability=AvailabilityStatus.UNKNOWN,
            source_evidence=platform.source_evidence,
            warnings=[
                f"{len(critical_events)} critical, "
                f"{len(warning_events)} warning events"
            ] if (critical_events or warning_events) else [],
        )

    def _assess_node(self, node: Node) -> HealthResult:
        """Assess node health from sysinv availability + FM alarms."""
        starlingx_data = node.metadata.get("starlingx", {})
        availability_str = str(
            starlingx_data.get("availability", "")).lower()
        operational_str = str(
            starlingx_data.get("operational", "")).lower()
        fm_alarms = starlingx_data.get("fm_alarms", [])
        platform_memory = starlingx_data.get("platform_memory", [])

        # ── Health from availability ─────────────────────────────────
        health_status = _AVAILABILITY_TO_HEALTH.get(
            availability_str, HealthStatus.UNKNOWN)
        avail_status = _AVAILABILITY_TO_AVAIL.get(
            availability_str, AvailabilityStatus.UNKNOWN)

        if operational_str == "disabled" and health_status == HealthStatus.HEALTHY:
            health_status = HealthStatus.DEGRADED

        # ── FM alarms ────────────────────────────────────────────────
        resource_statuses: list[ResourceStatus] = []
        warnings: list[str] = []

        for alarm in fm_alarms:
            if not isinstance(alarm, dict):
                continue
            severity = str(alarm.get("severity", "")).lower()
            alarm_health = _SEVERITY_TO_HEALTH.get(severity)
            if alarm_health == HealthStatus.UNHEALTHY:
                health_status = HealthStatus.UNHEALTHY
            elif alarm_health == HealthStatus.DEGRADED:
                if health_status != HealthStatus.UNHEALTHY:
                    health_status = HealthStatus.DEGRADED
            alarm_id = alarm.get("alarm_id", "")
            if alarm_id:
                warnings.append(
                    f"FM alarm {alarm_id} ({severity}): "
                    f"{alarm.get('reason_text', '')}")

        # ── Platform memory resource status ──────────────────────────
        for mem in platform_memory:
            if not isinstance(mem, dict):
                continue
            reserved = mem.get("platform_reserved_mib")
            total = mem.get("platform_total_mib")
            used_pct = mem.get("platform_used_percent")
            if used_pct is not None:
                try:
                    pct = float(used_pct)
                    if pct >= 90.0:
                        if health_status != HealthStatus.UNHEALTHY:
                            health_status = HealthStatus.DEGRADED
                        warnings.append(
                            f"Platform memory {pct}% used")
                except (ValueError, TypeError):
                    pass
            resource_statuses.append(ResourceStatus(
                resource_type=ResourceType.MEMORY,
                total=str(total) if total is not None else None,
                used=str(reserved) if reserved is not None else None,
                utilization=str(used_pct) if used_pct is not None else None,
                unit="MiB",
            ))

        return HealthResult(
            entity_id=node.canonical_id,
            entity_type="Node",
            status=health_status,
            availability=avail_status,
            source_evidence=node.source_evidence,
            resource_statuses=resource_statuses,
            warnings=warnings,
        )