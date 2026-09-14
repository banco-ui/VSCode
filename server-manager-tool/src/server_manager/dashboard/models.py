"""Dashboard Models (Phase 7).

Presentation-layer models for dashboard queries.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from ..models.enums import (
    ComputeEligibility,
    HealthStatus,
    ServerLifecycle,
    Vendor,
)


class ServerSummary(BaseModel):
    """Summary of a server for list views."""
    server_id: str
    display_name: str
    vendor: Vendor = Vendor.Unknown
    model: str = ""
    lifecycle_state: ServerLifecycle = ServerLifecycle.ACTIVE
    health: HealthStatus = HealthStatus.UNKNOWN
    compute_eligibility: ComputeEligibility = ComputeEligibility.UNKNOWN
    cpu_count: int = 0
    cpu_cores: int = 0
    memory_gb: float = 0.0
    gpu_count: int = 0
    last_collected_at: Optional[str] = None
    current_snapshot_id: Optional[str] = None

    model_config = {"extra": "forbid"}


class ServerDetail(ServerSummary):
    """Detailed server view."""
    hostname: str = ""
    serial_number: Optional[str] = None
    service_tag: Optional[str] = None
    bios_version: Optional[str] = None
    os_distribution: str = ""
    os_version: str = ""
    kernel: str = ""
    architecture: str = ""
    storage_disk_count: int = 0
    network_adapter_count: int = 0
    power_capacity_watts: Optional[float] = None
    power_current_watts: Optional[float] = None
    docker_installed: bool = False
    kubernetes_installed: bool = False
    vm_count: int = 0
    compute_potential: str = ""
    compute_reason: Optional[str] = None
    verification_discrepancy_count: int = 0
    snapshot_count: int = 0

    model_config = {"extra": "forbid"}


class ServerListResult(BaseModel):
    """Result of server list query."""
    servers: list[ServerSummary] = Field(default_factory=list)
    total: int = 0
    filters_applied: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class SnapshotSummary(BaseModel):
    """Summary of a snapshot for history views."""
    snapshot_id: str
    server_id: str
    collected_at: str
    schema_version: str = "1.0"
    canonical_source: Optional[str] = None
    health: HealthStatus = HealthStatus.UNKNOWN
    verification_discrepancy_count: int = 0

    model_config = {"extra": "forbid"}


class DashboardSummary(BaseModel):
    """Overall dashboard summary."""
    total_servers: int = 0
    active_servers: int = 0
    unreachable_servers: int = 0
    maintenance_servers: int = 0
    servers_with_warnings: int = 0
    servers_critical: int = 0
    compute_candidates: int = 0
    total_cpu_cores: int = 0
    total_memory_gb: float = 0.0
    total_gpus: int = 0
    last_collection_at: Optional[str] = None

    model_config = {"extra": "forbid"}


class FieldDiff(BaseModel):
    """Difference for a single field between two snapshots."""
    field_path: str
    old_value: Any = None
    new_value: Any = None
    change_type: str = "CHANGED"  # CHANGED, ADDED, REMOVED

    model_config = {"extra": "forbid"}


class SnapshotDiff(BaseModel):
    """Diff between two snapshots."""
    snapshot_a_id: str
    snapshot_b_id: str
    changed_fields: list[FieldDiff] = Field(default_factory=list)
    added_fields: list[str] = Field(default_factory=list)
    removed_fields: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def has_changes(self) -> bool:
        """Whether any changes exist."""
        return bool(self.changed_fields or self.added_fields or self.removed_fields)

    @property
    def change_count(self) -> int:
        """Total number of changes."""
        return len(self.changed_fields) + len(self.added_fields) + len(self.removed_fields)
