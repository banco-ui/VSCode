"""Runtime Verifier (Phase 4).

Verify runtime fields (containers, dev environment, workload).
"""
from __future__ import annotations

from ..models.inventory import ServerInventory
from .base import FieldResult, SourceEvidence, VerificationResult
from .comparators import FieldComparator


class RuntimeVerifier:
    """Verify runtime fields (Docker, Kubernetes, dev tools, workload)."""

    RUNTIME_FIELDS = [
        # Containers
        ("containers.docker.installed", lambda inv: inv.containers.docker.installed),
        ("containers.docker.running_containers", lambda inv: inv.containers.docker.running_containers),
        ("containers.kubernetes.installed", lambda inv: inv.containers.kubernetes.installed),
        # Dev environment
        ("dev.git_installed", lambda inv: inv.development_environment.git_installed),
        ("dev.python3_installed", lambda inv: inv.development_environment.python3_installed),
        ("dev.node_installed", lambda inv: inv.development_environment.node_installed),
        ("dev.pm2_installed", lambda inv: inv.development_environment.pm2_installed),
        # Workload
        ("workload.cpu_utilization", lambda inv: inv.workload.cpu_utilization),
        ("workload.memory_utilization", lambda inv: inv.workload.memory_utilization),
    ]

    def verify(
        self,
        inventories: dict[str, ServerInventory],
    ) -> VerificationResult:
        """Verify runtime fields across multiple source inventories.

        Args:
            inventories: Dict of source_name → ServerInventory.

        Returns:
            VerificationResult with field-level results.
        """
        field_results: list[FieldResult] = []

        for field_path, getter in self.RUNTIME_FIELDS:
            evidences: list[SourceEvidence] = []
            for source_name, inv in inventories.items():
                try:
                    value = getter(inv)
                    evidences.append(
                        SourceEvidence(
                            source=source_name,
                            field_path=field_path,
                            value=value,
                            available=value is not None,
                        )
                    )
                except Exception:
                    evidences.append(
                        SourceEvidence(
                            source=source_name,
                            field_path=field_path,
                            value=None,
                            available=False,
                        )
                    )

            result = FieldComparator.compare(field_path, evidences)
            field_results.append(result)

        result = VerificationResult(field_results=field_results)
        result.summary = {
            "total_fields": result.total_fields,
            "verified": result.verified_count,
            "single_source": result.single_source_count,
            "discrepancy": result.discrepancy_count,
            "partial": result.partial_count,
            "unavailable": result.unavailable_count,
        }
        return result
