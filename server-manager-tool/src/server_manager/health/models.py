"""Platform Health & Resource Models — Phase 15.

Provider-neutral health, availability, resource status, and capacity
models for canonical entities discovered in Phase 14.

Key principles:
- Health and Availability are SEPARATE concerns (not merged into one score)
- UNKNOWN is used actively — no evidence ≠ healthy, no metric ≠ zero
- Capacity values preserve source units (no arbitrary conversion)
- No fake capacity: CPU threads ≠ capacity, GPU exists ≠ 100% capacity
- Provenance reuses SourceEvidence from canonical models

This module does NOT implement:
    ❌ Monitoring (time-series, Prometheus, historical metrics)
    ❌ Alert generation
    ❌ Recovery / remediation
    ❌ Persistence (health history database)
    ❌ Threshold alerting / anomaly detection
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from server_manager.models.canonical import ProviderType, SourceEvidence
from server_manager.orchestrator.models import OrchestrationStatus


class HealthStatus(str, Enum):
    """Health status of a canonical entity.

    HEALTHY:   Collected evidence indicates normal operation.
    DEGRADED:  Service is possible but some resource/capability has issues
               or evidence deviates from normal.
    UNHEALTHY: Explicit failure evidence exists.
    UNKNOWN:   Insufficient evidence to determine health.

    UNKNOWN is NOT treated as HEALTHY.
    """
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class AvailabilityStatus(str, Enum):
    """Availability status — separate from health.

    Health = DEGRADED + Availability = AVAILABLE is a valid combination.
    Health = UNKNOWN + Availability = UNKNOWN is also valid.

    AVAILABLE:   Entity is reachable and can serve.
    UNAVAILABLE: Entity is not reachable or cannot serve.
    UNKNOWN:     No availability evidence.
    """
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ResourceType(str, Enum):
    """Resource type for resource status and capacity tracking."""
    CPU = "CPU"
    MEMORY = "MEMORY"
    STORAGE = "STORAGE"
    NETWORK = "NETWORK"
    ACCELERATOR = "ACCELERATOR"


class ResourceStatus(BaseModel):
    """Current resource status for a single resource type.

    Fields preserve source values as-is (strings) — no arbitrary
    unit conversion. Missing values are None (not zero).

    No fake values:
        - used = None when no usage metric available (K8s list API
          does not provide current usage — that requires metrics API)
        - utilization = None when not explicitly provided
        - NIC link speed is NOT treated as available bandwidth
    """
    resource_type: ResourceType
    total: Optional[str] = None
    used: Optional[str] = None
    available: Optional[str] = None
    utilization: Optional[str] = None
    unit: Optional[str] = None
    source_evidence: Optional[SourceEvidence] = None

    model_config = {"extra": "forbid"}


class CapacityInfo(BaseModel):
    """Capacity information for a single resource type.

    Capacity = total amount observable from provider evidence.
    Allocatable = amount available for allocation (provider-defined).

    Values preserve source units:
        bytes, GiB, cores, threads, Gbps, device_count, etc.

    No arbitrary unit conversion. No inference:
        - CPU threads ≠ capacity (unless source explicitly states it)
        - NIC link speed ≠ available bandwidth
        - GPU exists ≠ GPU capacity = 100%
    """
    resource_type: ResourceType
    capacity: Optional[str] = None
    allocatable: Optional[str] = None
    unit: Optional[str] = None
    source_evidence: Optional[SourceEvidence] = None

    model_config = {"extra": "forbid"}


class HealthResult(BaseModel):
    """Health assessment result for a single canonical entity.

    Links to canonical entity via entity_id (canonical_id, NOT provider_id).
    Health and availability are separate fields — never merged.

    Evidence priority for status derivation:
        1. Explicit failure evidence    -> UNHEALTHY
        2. Explicit degraded evidence   -> DEGRADED
        3. Explicit healthy/ready        -> HEALTHY
        4. No sufficient evidence        -> UNKNOWN
    """
    entity_id: str = Field(min_length=1)
    entity_type: str
    status: HealthStatus = HealthStatus.UNKNOWN
    availability: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    checked_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_evidence: Optional[SourceEvidence] = None
    resource_statuses: list[ResourceStatus] = Field(default_factory=list)
    capacity_infos: list[CapacityInfo] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class HealthReport(BaseModel):
    """Aggregate health report from a health assessment run.

    Wraps per-entity HealthResults into a report-level result.
    Reuses OrchestrationStatus for overall status (SUCCESS, PARTIAL,
    FAILED, SKIPPED) — consistent with DiscoveryResult semantics.

    Status semantics:
        SUCCESS: All entities assessed as HEALTHY/AVAILABLE
        PARTIAL: Some entities DEGRADED/UNHEALTHY/UNAVAILABLE
        FAILED:  Assessment could not be performed
        SKIPPED:  Provider not available (e.g., no credentials)
    """
    provider_type: ProviderType
    provider_id: Optional[str] = None
    health_status: OrchestrationStatus = OrchestrationStatus.FAILED
    checked_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    results: list[HealthResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def is_success(self) -> bool:
        return self.health_status == OrchestrationStatus.SUCCESS

    @property
    def is_partial(self) -> bool:
        return self.health_status == OrchestrationStatus.PARTIAL

    @property
    def is_skipped(self) -> bool:
        return self.health_status == OrchestrationStatus.SKIPPED

    @property
    def is_failed(self) -> bool:
        return self.health_status == OrchestrationStatus.FAILED

    @property
    def entity_count(self) -> int:
        return len(self.results)

    def results_for_type(self, entity_type: str) -> list[HealthResult]:
        """Get health results for a specific entity type."""
        return [r for r in self.results if r.entity_type == entity_type]

