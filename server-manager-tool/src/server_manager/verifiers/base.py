"""Verifier Base Models (Phase 4).

SourceEvidence, FieldResult, VerificationResult.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..models.enums import Confidence, VerificationStatus


class SourceEvidence(BaseModel):
    """Evidence from a single source for a single field."""
    source: str  # "redfish", "ssh", etc.
    field_path: str
    value: Any = None
    raw_value: Any = None
    collected_at: Optional[str] = None
    available: bool = True

    model_config = {"extra": "forbid"}


class FieldResult(BaseModel):
    """Verification result for a single field across multiple sources."""
    field_path: str
    status: VerificationStatus = VerificationStatus.UNAVAILABLE
    sources: list[str] = Field(default_factory=list)
    values: dict[str, Any] = Field(default_factory=dict)
    canonical_value: Optional[Any] = None
    match: Optional[bool] = None
    confidence: Confidence = Confidence.NONE
    note: Optional[str] = None
    discrepancies: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class VerificationResult(BaseModel):
    """Full verification result across all fields."""
    field_results: list[FieldResult] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"extra": "forbid"}

    def get_field(self, field_path: str) -> Optional[FieldResult]:
        """Get a specific field result by path."""
        for fr in self.field_results:
            if fr.field_path == field_path:
                return fr
        return None

    @property
    def total_fields(self) -> int:
        """Total number of verified fields."""
        return len(self.field_results)

    @property
    def discrepancy_count(self) -> int:
        """Number of fields with discrepancy status."""
        return sum(
            1 for fr in self.field_results if fr.status == VerificationStatus.DISCREPANCY
        )

    @property
    def verified_count(self) -> int:
        """Number of fields verified across multiple sources."""
        return sum(
            1 for fr in self.field_results if fr.status == VerificationStatus.VERIFIED
        )

    @property
    def single_source_count(self) -> int:
        """Number of fields with only a single source."""
        return sum(
            1 for fr in self.field_results if fr.status == VerificationStatus.SINGLE_SOURCE
        )

    @property
    def partial_count(self) -> int:
        """Number of fields with partial verification."""
        return sum(
            1 for fr in self.field_results if fr.status == VerificationStatus.PARTIAL
        )

    @property
    def unavailable_count(self) -> int:
        """Number of fields with unavailable status."""
        return sum(
            1 for fr in self.field_results if fr.status == VerificationStatus.UNAVAILABLE
        )
