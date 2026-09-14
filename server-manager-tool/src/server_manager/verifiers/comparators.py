"""Field Comparators (Phase 4).

Compare field values from multiple sources and determine verification status.
"""
from __future__ import annotations

from typing import Any

from ..models.enums import Confidence, VerificationStatus
from .base import FieldResult, SourceEvidence


class FieldComparator:
    """Compare field values from multiple sources."""

    @staticmethod
    def compare(
        field_path: str,
        evidences: list[SourceEvidence],
    ) -> FieldResult:
        """Compare evidence from multiple sources for a single field.

        Args:
            field_path: Dotted path to the field (e.g. "cpu.total_cores").
            evidences: List of SourceEvidence from different sources.

        Returns:
            FieldResult with verification status and canonical value.
        """
        # Filter to available evidence
        available = [e for e in evidences if e.available]
        sources = [e.source for e in available]
        values = {e.source: e.value for e in available}

        # No evidence → unavailable
        if not available:
            return FieldResult(
                field_path=field_path,
                status=VerificationStatus.UNAVAILABLE,
                sources=[],
                values={},
                canonical_value=None,
                match=None,
                confidence=Confidence.NONE,
                note="No source available",
            )

        # Single source → SINGLE_SOURCE
        if len(available) == 1:
            ev = available[0]
            return FieldResult(
                field_path=field_path,
                status=VerificationStatus.SINGLE_SOURCE,
                sources=sources,
                values=values,
                canonical_value=ev.value,
                match=True,
                confidence=Confidence.MEDIUM,
                note="Single source only",
            )

        # Multiple sources → compare values
        distinct_values = FieldComparator._get_distinct_values(values)

        if len(distinct_values) == 1:
            # All sources agree → VERIFIED
            return FieldResult(
                field_path=field_path,
                status=VerificationStatus.VERIFIED,
                sources=sources,
                values=values,
                canonical_value=distinct_values[0],
                match=True,
                confidence=Confidence.HIGH,
                note=f"All {len(available)} sources agree",
            )

        # Discrepancy detected
        # Try to find canonical value (prefer Redfish)
        canonical = FieldComparator._select_canonical(available)
        discrepancies = [
            f"{s}={v!r}" for s, v in values.items() if not FieldComparator._values_equal(v, canonical)
        ]

        return FieldResult(
            field_path=field_path,
            status=VerificationStatus.DISCREPANCY,
            sources=sources,
            values=values,
            canonical_value=canonical,
            match=False,
            confidence=Confidence.LOW,
            note=f"Discrepancy across {len(available)} sources",
            discrepancies=discrepancies,
        )

    @staticmethod
    def _get_distinct_values(values: dict[str, Any]) -> list[Any]:
        """Get list of distinct values."""
        distinct: list[Any] = []
        for v in values.values():
            if not any(FieldComparator._values_equal(v, d) for d in distinct):
                distinct.append(v)
        return distinct

    @staticmethod
    def _values_equal(a: Any, b: Any) -> bool:
        """Compare two values for equality, handling type coercion."""
        if a == b:
            return True
        # Numeric comparison with tolerance
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(a - b) < 0.01
        # String comparison (case-insensitive for non-empty)
        if isinstance(a, str) and isinstance(b, str):
            return a.strip().lower() == b.strip().lower()
        return False

    @staticmethod
    def _select_canonical(evidences: list[SourceEvidence]) -> Any:
        """Select canonical value from multiple sources.

        Priority: Redfish > SSH > IPMI > SNMP > first available
        """
        priority = ["redfish", "ssh", "ipmi", "snmp"]
        for source in priority:
            for ev in evidences:
                if ev.source == source:
                    return ev.value
        return evidences[0].value
