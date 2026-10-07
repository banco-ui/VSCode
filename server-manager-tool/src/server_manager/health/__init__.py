"""Health package — Phase 15.

Platform health, availability, resource status, and capacity assessment.

Composes Phase 14 DiscoveryResult into a health-level report without
duplicating any existing abstraction.

Pipeline:
    DiscoveryResult (Phase 14)
        ↓
    HealthService.assess()
        ↓
    HealthExtractor (provider-specific)
        ↓
    HealthReport (list[HealthResult])

READ_ONLY: No mutation, no monitoring, no alert, no recovery.
"""
from .models import (
    AvailabilityStatus,
    CapacityInfo,
    HealthReport,
    HealthResult,
    HealthStatus,
    ResourceType,
    ResourceStatus,
)
from .service import (
    HealthExtractor,
    HealthService,
    KubernetesHealthExtractor,
)

__all__ = [
    # Models
    "HealthStatus",
    "AvailabilityStatus",
    "ResourceType",
    "ResourceStatus",
    "CapacityInfo",
    "HealthResult",
    "HealthReport",
    # Service
    "HealthExtractor",
    "HealthService",
    "KubernetesHealthExtractor",
]
