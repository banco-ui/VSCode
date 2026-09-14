"""Dashboard Query Service (Phase 7).

Read-only query layer over InventoryStore.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..models.enums import (
    ComputeEligibility,
    HealthStatus,
    ServerLifecycle,
)
from ..store.store import InventoryStore
from .diff import compute_snapshot_diff
from .models import (
    DashboardSummary,
    FieldDiff,
    ServerDetail,
    ServerListResult,
    ServerSummary,
    SnapshotDiff,
    SnapshotSummary,
)

logger = logging.getLogger(__name__)


class DashboardQueryService:
    """Read-only query service for dashboard data."""

    def __init__(self, store: InventoryStore) -> None:
        self.store = store

    def get_server_list(
        self,
        filters: Optional[dict[str, Any]] = None,
    ) -> ServerListResult:
        """Get a list of all servers with summary info.

        Args:
            filters: Optional filters (vendor, lifecycle_state, health, etc.)

        Returns:
            ServerListResult with filtered server summaries.
        """
        entries = self.store.list_servers()
        filters_applied = filters or {}
        summaries: list[ServerSummary] = []

        for entry in entries:
            # Apply filters
            if filters:
                if "vendor" in filters and entry.vendor.value != filters["vendor"]:
                    continue
                if "lifecycle_state" in filters and entry.lifecycle_state.value != filters["lifecycle_state"]:
                    continue

            # Get current snapshot for health/compute info
            health = HealthStatus.UNKNOWN
            compute_eligibility = ComputeEligibility.UNKNOWN
            cpu_count = 0
            cpu_cores = 0
            memory_gb = 0.0
            gpu_count = 0
            last_collected = entry.last_collected_at

            snapshot = self.store.get_current_snapshot(entry.server_id)
            if snapshot:
                inv = snapshot.inventory
                health = inv.health.system
                compute_eligibility = inv.compute.eligibility
                cpu_count = inv.hardware.cpu.count
                cpu_cores = inv.hardware.cpu.total_cores
                memory_gb = inv.hardware.memory.total_gb
                gpu_count = inv.hardware.gpu.count
                last_collected = snapshot.collected_at

            # Apply health filter
            if filters and "health" in filters and health.value != filters["health"]:
                continue

            summaries.append(ServerSummary(
                server_id=entry.server_id,
                display_name=entry.display_name,
                vendor=entry.vendor,
                model=entry.model,
                lifecycle_state=entry.lifecycle_state,
                health=health,
                compute_eligibility=compute_eligibility,
                cpu_count=cpu_count,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                gpu_count=gpu_count,
                last_collected_at=last_collected,
                current_snapshot_id=entry.current_snapshot_id,
            ))

        return ServerListResult(
            servers=summaries,
            total=len(summaries),
            filters_applied=filters_applied,
        )

    def get_server_detail(self, server_id: str) -> Optional[ServerDetail]:
        """Get detailed information about a specific server.

        Args:
            server_id: Server ID.

        Returns:
            ServerDetail or None if not found.
        """
        entry = self.store.get_server(server_id)
        if entry is None:
            return None

        snapshot = self.store.get_current_snapshot(server_id)
        snapshots = self.store.list_snapshots(server_id)

        # Defaults
        health = HealthStatus.UNKNOWN
        compute_eligibility = ComputeEligibility.UNKNOWN
        cpu_count = 0
        cpu_cores = 0
        memory_gb = 0.0
        gpu_count = 0
        hostname = ""
        serial_number = None
        service_tag = None
        bios_version = None
        os_distribution = ""
        os_version = ""
        kernel = ""
        architecture = ""
        storage_disk_count = 0
        network_adapter_count = 0
        power_capacity_watts = None
        power_current_watts = None
        docker_installed = False
        kubernetes_installed = False
        vm_count = 0
        compute_potential = ""
        compute_reason = None
        verification_discrepancy_count = 0

        if snapshot:
            inv = snapshot.inventory
            health = inv.health.system
            compute_eligibility = inv.compute.eligibility
            cpu_count = inv.hardware.cpu.count
            cpu_cores = inv.hardware.cpu.total_cores
            memory_gb = inv.hardware.memory.total_gb
            gpu_count = inv.hardware.gpu.count
            hostname = inv.identity.hostname
            serial_number = inv.identity.serial_number
            service_tag = inv.identity.service_tag
            bios_version = inv.identity.bios_version
            os_distribution = inv.os.distribution
            os_version = inv.os.version
            kernel = inv.os.kernel
            architecture = inv.os.architecture
            storage_disk_count = len(inv.hardware.storage.physical_disks)
            network_adapter_count = inv.hardware.network.adapter_count
            power_capacity_watts = inv.power_thermal.power.capacity_watts
            power_current_watts = inv.power_thermal.power.current_watts
            docker_installed = inv.containers.docker.installed
            kubernetes_installed = inv.containers.kubernetes.installed
            vm_count = inv.virtualization.vms
            compute_potential = inv.compute.potential.value
            compute_reason = inv.compute.reason

            # Get verification discrepancy count
            verifications = self.store.list_verifications(server_id, limit=1)
            if verifications:
                v = verifications[0]
                if hasattr(v.result, "discrepancy_count"):
                    verification_discrepancy_count = v.result.discrepancy_count
                elif isinstance(v.result, dict):
                    verification_discrepancy_count = v.result.get("summary", {}).get("discrepancy_count", 0)

        return ServerDetail(
            server_id=entry.server_id,
            display_name=entry.display_name,
            vendor=entry.vendor,
            model=entry.model,
            lifecycle_state=entry.lifecycle_state,
            health=health,
            compute_eligibility=compute_eligibility,
            cpu_count=cpu_count,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            gpu_count=gpu_count,
            last_collected_at=entry.last_collected_at,
            current_snapshot_id=entry.current_snapshot_id,
            hostname=hostname,
            serial_number=serial_number,
            service_tag=service_tag,
            bios_version=bios_version,
            os_distribution=os_distribution,
            os_version=os_version,
            kernel=kernel,
            architecture=architecture,
            storage_disk_count=storage_disk_count,
            network_adapter_count=network_adapter_count,
            power_capacity_watts=power_capacity_watts,
            power_current_watts=power_current_watts,
            docker_installed=docker_installed,
            kubernetes_installed=kubernetes_installed,
            vm_count=vm_count,
            compute_potential=compute_potential,
            compute_reason=compute_reason,
            verification_discrepancy_count=verification_discrepancy_count,
            snapshot_count=len(snapshots),
        )

    def get_snapshot_history(
        self,
        server_id: str,
        limit: int = 10,
    ) -> list[SnapshotSummary]:
        """Get snapshot history for a server.

        Args:
            server_id: Server ID.
            limit: Maximum number of snapshots.

        Returns:
            List of SnapshotSummary.
        """
        snapshots = self.store.list_snapshots(server_id, limit=limit)
        summaries: list[SnapshotSummary] = []

        for snap in snapshots:
            health = snap.inventory.health.system
            discrepancy_count = 0

            # Try to find verification for this snapshot
            verifications = self.store.list_verifications(server_id, limit=limit * 2)
            for v in verifications:
                if v.snapshot_id == snap.snapshot_id:
                    if hasattr(v.result, "discrepancy_count"):
                        discrepancy_count = v.result.discrepancy_count
                    elif isinstance(v.result, dict):
                        discrepancy_count = v.result.get("summary", {}).get("discrepancy_count", 0)
                    break

            summaries.append(SnapshotSummary(
                snapshot_id=snap.snapshot_id,
                server_id=snap.server_id,
                collected_at=snap.collected_at,
                schema_version=snap.schema_version,
                canonical_source=snap.canonical_source,
                health=health,
                verification_discrepancy_count=discrepancy_count,
            ))

        return summaries

    def get_snapshot_diff(
        self,
        snapshot_id_a: str,
        snapshot_id_b: str,
    ) -> Optional[SnapshotDiff]:
        """Compute diff between two snapshots.

        Args:
            snapshot_id_a: Older snapshot ID.
            snapshot_id_b: Newer snapshot ID.

        Returns:
            SnapshotDiff or None if either snapshot not found.
        """
        snap_a = self.store.get_snapshot(snapshot_id_a)
        snap_b = self.store.get_snapshot(snapshot_id_b)

        if snap_a is None or snap_b is None:
            return None

        return compute_snapshot_diff(
            snapshot_id_a,
            snapshot_id_b,
            snap_a.inventory,
            snap_b.inventory,
        )

    def get_weekend_compute_candidates(self) -> list[ServerSummary]:
        """Get servers that are candidates for weekend compute.

        Returns servers with:
        - lifecycle_state == ACTIVE
        - compute.eligibility in {CANDIDATE, COMPUTE_ELIGIBLE, IDLE}
        """
        result = self.get_server_list()
        eligible_states = {
            ComputeEligibility.CANDIDATE,
            ComputeEligibility.COMPUTE_ELIGIBLE,
            ComputeEligibility.IDLE,
        }
        return [
            s for s in result.servers
            if s.lifecycle_state == ServerLifecycle.ACTIVE
            and s.compute_eligibility in eligible_states
        ]

    def get_dashboard_summary(self) -> DashboardSummary:
        """Get overall dashboard summary."""
        entries = self.store.list_servers()
        result = self.get_server_list()

        total_servers = len(entries)
        active = sum(1 for s in result.servers if s.lifecycle_state == ServerLifecycle.ACTIVE)
        unreachable = sum(1 for s in result.servers if s.lifecycle_state == ServerLifecycle.UNREACHABLE)
        maintenance = sum(1 for s in result.servers if s.lifecycle_state == ServerLifecycle.MAINTENANCE)
        warnings = sum(1 for s in result.servers if s.health == HealthStatus.WARNING)
        critical = sum(1 for s in result.servers if s.health == HealthStatus.CRITICAL)
        compute_candidates = len(self.get_weekend_compute_candidates())
        total_cpu = sum(s.cpu_cores for s in result.servers)
        total_mem = sum(s.memory_gb for s in result.servers)
        total_gpus = sum(s.gpu_count for s in result.servers)

        last_collection = max(
            (s.last_collected_at for s in result.servers if s.last_collected_at),
            default=None,
        )

        return DashboardSummary(
            total_servers=total_servers,
            active_servers=active,
            unreachable_servers=unreachable,
            maintenance_servers=maintenance,
            servers_with_warnings=warnings,
            servers_critical=critical,
            compute_candidates=compute_candidates,
            total_cpu_cores=total_cpu,
            total_memory_gb=round(total_mem, 2),
            total_gpus=total_gpus,
            last_collection_at=last_collection,
        )
