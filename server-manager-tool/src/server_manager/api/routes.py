"""API Routes (Phase 8).

FastAPI routes for the 5 API v1 endpoints.
Each route delegates to existing services (Orchestrator, InventoryStore, DashboardQueryService).
No business logic is implemented here — only HTTP boundary + response mapping.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from .dependencies import get_store, get_dashboard_query_service, get_orchestrator
from .schemas import (
    CollectRequest,
    CollectResponse,
    SourceResultResponse,
    VerificationResponse,
    VerificationSummaryResponse,
    InventoryResponse,
    HistoryResponse,
    SnapshotSummaryResponse,
    DiffResponse,
    FieldDiffResponse,
    ComputeCandidatesResponse,
    ComputeCandidateResponse,
)
from ..store.store import InventoryStore
from ..dashboard.query_service import DashboardQueryService
from ..orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["inventory"])


# ── Helpers ───────────────────────────────────────────────────────────

def _build_verification_response(
    verification: Any,
) -> VerificationResponse:
    """Map VerificationResult (or None) to API VerificationResponse."""
    if verification is None:
        return VerificationResponse(
            performed=False,
            success=False,
            discrepancy_count=0,
            summary=None,
        )

    summary = VerificationSummaryResponse(
        total_fields=getattr(verification, "total_fields", 0),
        verified=getattr(verification, "verified_count", 0),
        single_source=getattr(verification, "single_source_count", 0),
        discrepancy=getattr(verification, "discrepancy_count", 0),
    )

    return VerificationResponse(
        performed=True,
        success=getattr(verification, "discrepancy_count", 0) == 0,
        discrepancy_count=getattr(verification, "discrepancy_count", 0),
        summary=summary,
    )


# ── POST /api/v1/collect ──────────────────────────────────────────────

@router.post("/collect", response_model=CollectResponse)
def collect(
    request: CollectRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    store: InventoryStore = Depends(get_store),
) -> CollectResponse:
    """Trigger collection for a server.

    Delegates to Orchestrator.run() and persists the result via InventoryStore.
    """
    # Check server is registered
    entry = store.get_server(request.server_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Server '{request.server_id}' not found",
                "details": {},
            },
        )

    # Run orchestration
    try:
        result = orchestrator.run(request.server_id)
    except Exception as e:
        logger.error("Orchestration failed for %s: %s", request.server_id, e)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Collection failed due to an internal error",
                "details": {},
            },
        )

    # Persist result
    if result.canonical_inventory:
        store.save_orchestration_result(result)

    # Build response
    source_results = [
        SourceResultResponse(
            source=sr.source,
            collection_success=sr.collection_success,
            normalization_success=sr.normalization_success or False,
            duration_ms=sr.duration_ms,
        )
        for sr in result.source_results
    ]

    verification = _build_verification_response(result.verification)

    snapshot_id = f"snap-{result.run_id}" if result.canonical_inventory else None

    return CollectResponse(
        run_id=result.run_id,
        server_id=result.server_id,
        status=result.status.value,
        canonical_source=result.canonical_source,
        started_at=result.started_at,
        completed_at=result.completed_at,
        total_duration_ms=result.total_duration_ms,
        source_results=source_results,
        verification=verification,
        snapshot_id=snapshot_id,
        errors=result.errors,
        warnings=result.warnings,
    )


# ── GET /api/v1/inventory/{server_id} ─────────────────────────────────

@router.get("/inventory/{server_id}", response_model=InventoryResponse)
def get_inventory(
    server_id: str,
    store: InventoryStore = Depends(get_store),
) -> InventoryResponse:
    """Get current canonical inventory for a server."""
    entry = store.get_server(server_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Server '{server_id}' not found",
                "details": {},
            },
        )

    snapshot = store.get_current_snapshot(server_id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"No inventory snapshot found for server '{server_id}'",
                "details": {},
            },
        )

    # Get verification info
    verification = None
    verifications = store.list_verifications(server_id, limit=1)
    if verifications:
        v = verifications[0]
        verification = _build_verification_response(v.result if hasattr(v, "result") else None)

    # Serialize inventory using by_alias=True for _meta
    inventory_data = snapshot.inventory.model_dump(by_alias=True)

    return InventoryResponse(
        server_id=server_id,
        snapshot_id=snapshot.snapshot_id,
        collected_at=snapshot.collected_at,
        canonical_source=snapshot.canonical_source,
        schema_version=snapshot.schema_version,
        inventory=inventory_data,
        verification=verification,
    )


# ── GET /api/v1/inventory/{server_id}/history ────────────────────────

@router.get("/inventory/{server_id}/history", response_model=HistoryResponse)
def get_history(
    server_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    store: InventoryStore = Depends(get_store),
    dashboard: DashboardQueryService = Depends(get_dashboard_query_service),
) -> HistoryResponse:
    """Get snapshot history for a server."""
    entry = store.get_server(server_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Server '{server_id}' not found",
                "details": {},
            },
        )

    summaries = dashboard.get_snapshot_history(server_id, limit=limit)

    snapshot_responses = [
        SnapshotSummaryResponse(
            snapshot_id=s.snapshot_id,
            collected_at=s.collected_at,
            schema_version=s.schema_version,
            canonical_source=s.canonical_source,
            health=s.health.value,
            verification_discrepancy_count=s.verification_discrepancy_count,
        )
        for s in summaries
    ]

    return HistoryResponse(
        server_id=server_id,
        total=len(snapshot_responses),
        limit=limit,
        snapshots=snapshot_responses,
    )


# ── GET /api/v1/inventory/{server_id}/diff ────────────────────────────

@router.get("/inventory/{server_id}/diff", response_model=DiffResponse)
def get_diff(
    server_id: str,
    frm: str = Query(..., alias="from"),
    to: str = Query(...),
    store: InventoryStore = Depends(get_store),
    dashboard: DashboardQueryService = Depends(get_dashboard_query_service),
) -> DiffResponse:
    """Get diff between two snapshots."""
    entry = store.get_server(server_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Server '{server_id}' not found",
                "details": {},
            },
        )

    snapshot_diff = dashboard.get_snapshot_diff(frm, to)
    if snapshot_diff is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Snapshot '{frm}' or '{to}' not found",
                "details": {},
            },
        )

    # Map SnapshotDiff → DiffResponse
    all_diffs: list[FieldDiffResponse] = []

    for fd in snapshot_diff.changed_fields:
        all_diffs.append(FieldDiffResponse(
            field_path=fd.field_path,
            from_value=fd.old_value,
            to_value=fd.new_value,
            change_type="MODIFIED",
        ))
    for field_path in snapshot_diff.added_fields:
        all_diffs.append(FieldDiffResponse(
            field_path=field_path,
            from_value=None,
            to_value=None,
            change_type="ADDED",
        ))
    for field_path in snapshot_diff.removed_fields:
        all_diffs.append(FieldDiffResponse(
            field_path=field_path,
            from_value=None,
            to_value=None,
            change_type="REMOVED",
        ))

    return DiffResponse(
        server_id=server_id,
        from_snapshot_id=frm,
        to_snapshot_id=to,
        diffs=all_diffs,
        total_changes=len(all_diffs),
    )


# ── GET /api/v1/compute/candidates ────────────────────────────────────

@router.get("/compute/candidates", response_model=ComputeCandidatesResponse)
def get_compute_candidates(
    dashboard: DashboardQueryService = Depends(get_dashboard_query_service),
) -> ComputeCandidatesResponse:
    """Get weekend compute candidates."""
    candidates = dashboard.get_weekend_compute_candidates()

    candidate_responses = [
        ComputeCandidateResponse(
            server_id=c.server_id,
            display_name=c.display_name,
            vendor=c.vendor.value,
            model=c.model,
            lifecycle_state=c.lifecycle_state.value,
            health=c.health.value,
            compute_eligibility=c.compute_eligibility.value,
            cpu_count=c.cpu_count,
            cpu_cores=c.cpu_cores,
            memory_gb=c.memory_gb,
            gpu_count=c.gpu_count,
            last_collected_at=c.last_collected_at,
            current_snapshot_id=c.current_snapshot_id,
        )
        for c in candidates
    ]

    return ComputeCandidatesResponse(
        candidates=candidate_responses,
        total=len(candidate_responses),
    )
