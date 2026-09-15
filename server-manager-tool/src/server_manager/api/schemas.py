"""API Schemas (Phase 8).

Pydantic models for API request/response.
Reuses existing domain models where possible.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Error ────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ── Collect ───────────────────────────────────────────────────────────

class CollectRequest(BaseModel):
    server_id: str
    sources: Optional[list[str]] = None


class SourceResultResponse(BaseModel):
    source: str
    collection_success: bool
    normalization_success: bool
    duration_ms: int = 0


class VerificationSummaryResponse(BaseModel):
    total_fields: int = 0
    verified: int = 0
    single_source: int = 0
    discrepancy: int = 0


class VerificationResponse(BaseModel):
    performed: bool
    success: bool
    discrepancy_count: int = 0
    summary: Optional[VerificationSummaryResponse] = None


class CollectResponse(BaseModel):
    run_id: str
    server_id: str
    status: str
    canonical_source: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_ms: int = 0
    source_results: list[SourceResultResponse] = Field(default_factory=list)
    verification: VerificationResponse
    snapshot_id: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ── Inventory ─────────────────────────────────────────────────────────

class InventoryResponse(BaseModel):
    server_id: str
    snapshot_id: str
    collected_at: str
    canonical_source: Optional[str] = None
    schema_version: str = "1.0"
    inventory: dict[str, Any]
    verification: Optional[VerificationResponse] = None


# ── History ───────────────────────────────────────────────────────────

class SnapshotSummaryResponse(BaseModel):
    snapshot_id: str
    collected_at: str
    schema_version: str = "1.0"
    canonical_source: Optional[str] = None
    health: str
    verification_discrepancy_count: int = 0


class HistoryResponse(BaseModel):
    server_id: str
    total: int
    limit: int
    snapshots: list[SnapshotSummaryResponse] = Field(default_factory=list)


# ── Diff ──────────────────────────────────────────────────────────────

class FieldDiffResponse(BaseModel):
    field_path: str
    from_value: Any
    to_value: Any
    change_type: str


class DiffResponse(BaseModel):
    server_id: str
    from_snapshot_id: str
    to_snapshot_id: str
    diffs: list[FieldDiffResponse] = Field(default_factory=list)
    total_changes: int = 0


# ── Compute ───────────────────────────────────────────────────────────

class ComputeCandidateResponse(BaseModel):
    server_id: str
    display_name: str
    vendor: str
    model: str
    lifecycle_state: str
    health: str
    compute_eligibility: str
    cpu_count: int = 0
    cpu_cores: int = 0
    memory_gb: float = 0.0
    gpu_count: int = 0
    last_collected_at: Optional[str] = None
    current_snapshot_id: Optional[str] = None


class ComputeCandidatesResponse(BaseModel):
    candidates: list[ComputeCandidateResponse] = Field(default_factory=list)
    total: int = 0
