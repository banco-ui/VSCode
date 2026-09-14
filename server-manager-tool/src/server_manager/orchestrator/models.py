"""Orchestrator Models (Phase 5).

OrchestrationStatus, PipelineStage, ErrorCategory, SourceResult, OrchestrationResult.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..models.inventory import ServerInventory
from ..verifiers.base import VerificationResult


class OrchestrationStatus(str, Enum):
    """Overall orchestration pipeline status."""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PipelineStage(str, Enum):
    """Pipeline stage tracking."""
    COLLECTION = "COLLECTION"
    NORMALIZATION = "NORMALIZATION"
    VERIFICATION = "VERIFICATION"
    COMPLETE = "COMPLETE"


class ErrorCategory(str, Enum):
    """Categorized error types for fault isolation."""
    CONNECTION_ERROR = "CONNECTION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    TIMEOUT = "TIMEOUT"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    UNSUPPORTED = "UNSUPPORTED"
    PARSING_ERROR = "PARSING_ERROR"
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    @classmethod
    def from_exception(cls, exc: Exception) -> "ErrorCategory":
        """Classify an exception into an ErrorCategory."""
        exc_type = type(exc).__name__.lower()
        exc_msg = str(exc).lower()

        if "connection" in exc_type or "connection" in exc_msg or "refused" in exc_msg:
            return cls.CONNECTION_ERROR
        if "auth" in exc_type or "auth" in exc_msg or "permission" in exc_msg or "denied" in exc_msg:
            return cls.AUTHENTICATION_ERROR
        if "timeout" in exc_type or "timeout" in exc_msg or "timed out" in exc_msg:
            return cls.TIMEOUT
        if "protocol" in exc_type or "protocol" in exc_msg:
            return cls.PROTOCOL_ERROR
        if "unsupport" in exc_type or "unsupport" in exc_msg:
            return cls.UNSUPPORTED
        if "parse" in exc_type or "parse" in exc_msg or "json" in exc_msg:
            return cls.PARSING_ERROR
        if "normaliz" in exc_type or "normaliz" in exc_msg:
            return cls.NORMALIZATION_ERROR
        if "verif" in exc_type or "verif" in exc_msg:
            return cls.VERIFICATION_ERROR
        return cls.UNKNOWN_ERROR

    @classmethod
    def from_error_string(cls, error_str: str) -> "ErrorCategory":
        """Classify an error string into an ErrorCategory."""
        error_lower = error_str.lower()
        if "connection" in error_lower or "refused" in error_lower:
            return cls.CONNECTION_ERROR
        if "auth" in error_lower or "permission" in error_lower or "denied" in error_lower:
            return cls.AUTHENTICATION_ERROR
        if "timeout" in error_lower or "timed out" in error_lower:
            return cls.TIMEOUT
        if "protocol" in error_lower:
            return cls.PROTOCOL_ERROR
        if "unsupport" in error_lower:
            return cls.UNSUPPORTED
        if "parse" in error_lower or "json" in error_lower:
            return cls.PARSING_ERROR
        if "normaliz" in error_lower:
            return cls.NORMALIZATION_ERROR
        if "verif" in error_lower:
            return cls.VERIFICATION_ERROR
        return cls.UNKNOWN_ERROR


class SourceResult(BaseModel):
    """Result from a single source collection + normalization."""
    source: str  # "redfish", "ssh"
    collection_success: bool = False
    normalization_success: Optional[bool] = None
    inventory: Optional[ServerInventory] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration_ms: int = 0

    model_config = {"extra": "forbid"}


class OrchestrationResult(BaseModel):
    """Full orchestration pipeline result."""
    run_id: str
    server_id: str
    status: OrchestrationStatus = OrchestrationStatus.FAILED
    source_results: list[SourceResult] = Field(default_factory=list)
    canonical_inventory: Optional[ServerInventory] = None
    canonical_source: Optional[str] = None
    verification: Optional[VerificationResult] = None
    verification_success: bool = False
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    total_duration_ms: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
