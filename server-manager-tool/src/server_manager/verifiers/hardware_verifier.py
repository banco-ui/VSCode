"""Hardware Verifier (Phase 4).

Verify hardware fields across multiple source inventories.
"""
from __future__ import annotations

from typing import Optional

from ..models.inventory import ServerInventory
from .base import FieldResult, SourceEvidence, VerificationResult
from .comparators import FieldComparator


class HardwareVerifier:
    """Verify hardware fields (CPU, Memory, Storage, Network, GPU)."""

    # Fields to verify: (field_path, getter_fn)
    HARDWARE_FIELDS = [
        # CPU
        ("cpu.count", lambda inv: inv.hardware.cpu.count),
        ("cpu.total_cores", lambda inv: inv.hardware.cpu.total_cores),
        ("cpu.total_threads", lambda inv: inv.hardware.cpu.total_threads),
        # Memory
        ("memory.total_gb", lambda inv: inv.hardware.memory.total_gb),
        ("memory.dimm_count", lambda inv: inv.hardware.memory.dimm_count),
        ("memory.populated_slots", lambda inv: inv.hardware.memory.populated_slots),
        # Storage
        ("storage.physical_disk_count", lambda inv: len(inv.hardware.storage.physical_disks)),
        ("storage.controller_count", lambda inv: len(inv.hardware.storage.controllers)),
        # Network
        ("network.adapter_count", lambda inv: inv.hardware.network.adapter_count),
        # GPU
        ("gpu.count", lambda inv: inv.hardware.gpu.count),
    ]

    def verify(
        self,
        inventories: dict[str, ServerInventory],
    ) -> VerificationResult:
        """Verify hardware fields across multiple source inventories.

        Args:
            inventories: Dict of source_name → ServerInventory.
                         e.g. {"redfish": inv1, "ssh": inv2}

        Returns:
            VerificationResult with field-level results.
        """
        field_results: list[FieldResult] = []

        for field_path, getter in self.HARDWARE_FIELDS:
            evidences: list[SourceEvidence] = []
            for source_name, inv in inventories.items():
                try:
                    value = getter(inv)
                    evidences.append(
                        SourceEvidence(
                            source=source_name,
                            field_path=field_path,
                            value=value,
                            available=True,
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

        # Build summary
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
