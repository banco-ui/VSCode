"""OS Verifier (Phase 4).

Verify OS-level fields across multiple source inventories.
"""
from __future__ import annotations

from ..models.inventory import ServerInventory
from .base import FieldResult, SourceEvidence, VerificationResult
from .comparators import FieldComparator


class OSVerifier:
    """Verify OS fields (distribution, version, kernel, hostname)."""

    OS_FIELDS = [
        ("os.distribution", lambda inv: inv.os.distribution),
        ("os.version", lambda inv: inv.os.version),
        ("os.kernel", lambda inv: inv.os.kernel),
        ("os.hostname", lambda inv: inv.os.hostname),
        ("os.architecture", lambda inv: inv.os.architecture),
    ]

    def verify(
        self,
        inventories: dict[str, ServerInventory],
    ) -> VerificationResult:
        """Verify OS fields across multiple source inventories.

        Args:
            inventories: Dict of source_name → ServerInventory.

        Returns:
            VerificationResult with field-level results.
        """
        field_results: list[FieldResult] = []

        for field_path, getter in self.OS_FIELDS:
            evidences: list[SourceEvidence] = []
            for source_name, inv in inventories.items():
                try:
                    value = getter(inv)
                    evidences.append(
                        SourceEvidence(
                            source=source_name,
                            field_path=field_path,
                            value=value,
                            available=value is not None and value != "",
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
