"""Scheduler API Routes (Phase 10C).

FastAPI routes for Scheduler API endpoints.
Each route delegates to Scheduler Core and SchedulerStore.
No business logic is implemented here — only HTTP boundary + response mapping.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .dependencies import get_scheduler_store
from .scheduler_schemas import (
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
    ScheduleListResponse,
    ExecutionResponse,
    ExecutionListResponse,
    SchedulerStatusResponse,
)
from ..scheduler.store import SchedulerStore
from ..scheduler.scheduler import Scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scheduler"])


# ── Helpers ───────────────────────────────────────────────────────────

def _schedule_to_response(schedule) -> ScheduleResponse:
    """Convert ScheduleDefinition to ScheduleResponse."""
    return ScheduleResponse(
        schedule_id=schedule.schedule_id,
        name=schedule.name,
        server_ids=schedule.server_ids,
        enabled=schedule.enabled,
        cron_expression=schedule.cron_expression,
        interval_seconds=schedule.interval_seconds,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        metadata=schedule.metadata,
    )


def _execution_to_response(execution) -> ExecutionResponse:
    """Convert ScheduleExecution to ExecutionResponse."""
    return ExecutionResponse(
        execution_id=execution.execution_id,
        schedule_id=execution.schedule_id,
        server_id=execution.server_id,
        run_id=execution.run_id,
        status=execution.status,
        claimed_at=execution.claimed_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        error_message=execution.error_message,
    )


# ── Schedule Definition Endpoints ─────────────────────────────────────

@router.get("/schedules", response_model=ScheduleListResponse)
def list_schedules(
    enabled: Optional[bool] = Query(None, description="Filter by enabled state"),
    server_id: Optional[str] = Query(None, description="Filter by target server"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ScheduleListResponse:
    """List all schedule definitions.
    
    Args:
        enabled: Filter by enabled state (optional)
        server_id: Filter by target server (optional)
        limit: Maximum number of results (default: 100)
        offset: Pagination offset (default: 0)
    
    Returns:
        List of schedules with pagination metadata.
    """
    all_schedules = store.get_all_schedules()
    
    # Apply filters
    if enabled is not None:
        all_schedules = [s for s in all_schedules if s.enabled == enabled]
    
    if server_id is not None:
        all_schedules = [s for s in all_schedules if server_id in s.server_ids]
    
    # Apply pagination
    total = len(all_schedules)
    paginated = all_schedules[offset:offset + limit]
    
    return ScheduleListResponse(
        schedules=[_schedule_to_response(s) for s in paginated],
        total=total,
    )


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    request: ScheduleCreateRequest,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ScheduleResponse:
    """Create a new schedule.
    
    Args:
        request: Schedule creation request.
    
    Returns:
        Created schedule.
    
    Raises:
        HTTPException 409: Duplicate schedule_id.
    """
    from ..scheduler.models import ScheduleDefinition
    import uuid
    
    # Generate unique schedule_id
    schedule_id = f"schedule-{uuid.uuid4().hex[:12]}"
    
    schedule = ScheduleDefinition(
        schedule_id=schedule_id,
        name=request.name,
        server_ids=request.server_ids,
        enabled=request.enabled,  # Default False for safety
        cron_expression=request.cron_expression,
        interval_seconds=request.interval_seconds,
        metadata=request.metadata,
    )
    
    store.save_schedule(schedule)
    
    return _schedule_to_response(schedule)


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: str,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ScheduleResponse:
    """Get a schedule definition by ID.
    
    Args:
        schedule_id: Schedule identifier.
    
    Returns:
        Schedule definition.
    
    Raises:
        HTTPException 404: Schedule not found.
    """
    schedule = store.get_schedule(schedule_id)
    
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Schedule '{schedule_id}' not found",
                "details": {},
            },
        )
    
    return _schedule_to_response(schedule)


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateRequest,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ScheduleResponse:
    """Update an existing schedule.
    
    Args:
        schedule_id: Schedule identifier.
        request: Update request (partial update supported).
    
    Returns:
        Updated schedule.
    
    Raises:
        HTTPException 404: Schedule not found.
    """
    schedule = store.get_schedule(schedule_id)
    
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Schedule '{schedule_id}' not found",
                "details": {},
            },
        )
    
    # Apply updates (partial update)
    if request.name is not None:
        schedule.name = request.name
    if request.server_ids is not None:
        schedule.server_ids = request.server_ids
    if request.enabled is not None:
        schedule.enabled = request.enabled
    if request.cron_expression is not None:
        schedule.cron_expression = request.cron_expression
    if request.interval_seconds is not None:
        schedule.interval_seconds = request.interval_seconds
    if request.metadata is not None:
        schedule.metadata = request.metadata
    
    # Update timestamp
    from datetime import datetime, timezone
    schedule.updated_at = datetime.now(timezone.utc).isoformat()
    
    store.save_schedule(schedule)
    
    return _schedule_to_response(schedule)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: str,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> None:
    """Delete a schedule definition.
    
    Policy: Soft delete - marks schedule as disabled and removes from active scheduling.
    Execution history is preserved.
    
    Args:
        schedule_id: Schedule identifier.
    
    Raises:
        HTTPException 404: Schedule not found.
    """
    schedule = store.get_schedule(schedule_id)
    
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Schedule '{schedule_id}' not found",
                "details": {},
            },
        )
    
    # Soft delete: disable the schedule
    # Note: We don't actually delete from DB to preserve execution history
    # Instead, we disable it and let the store handle cleanup if needed
    schedule.enabled = False
    from datetime import datetime, timezone
    schedule.updated_at = datetime.now(timezone.utc).isoformat()
    store.save_schedule(schedule)
    
    # Note: Execution history is preserved in schedule_executions table
    # The schedule definition is disabled but not hard-deleted


@router.post("/schedules/{schedule_id}/enable", response_model=ScheduleResponse)
def enable_schedule(
    schedule_id: str,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ScheduleResponse:
    """Enable a schedule.
    
    Note: This enables the schedule definition but does not start the Scheduler process.
    The schedule will be picked up by the next polling cycle if Scheduler is running.
    
    Args:
        schedule_id: Schedule identifier.
    
    Returns:
        Updated schedule.
    
    Raises:
        HTTPException 404: Schedule not found.
        HTTPException 409: Schedule already enabled.
    """
    schedule = store.get_schedule(schedule_id)
    
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Schedule '{schedule_id}' not found",
                "details": {},
            },
        )
    
    if schedule.enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ALREADY_ENABLED",
                "message": f"Schedule '{schedule_id}' is already enabled",
                "details": {},
            },
        )
    
    schedule.enabled = True
    from datetime import datetime, timezone
    schedule.updated_at = datetime.now(timezone.utc).isoformat()
    store.save_schedule(schedule)
    
    return _schedule_to_response(schedule)


@router.post("/schedules/{schedule_id}/disable", response_model=ScheduleResponse)
def disable_schedule(
    schedule_id: str,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ScheduleResponse:
    """Disable a schedule.
    
    Note: This disables the schedule definition but does NOT cancel running executions.
    Running executions will complete normally.
    
    Args:
        schedule_id: Schedule identifier.
    
    Returns:
        Updated schedule.
    
    Raises:
        HTTPException 404: Schedule not found.
        HTTPException 409: Schedule already disabled.
    """
    schedule = store.get_schedule(schedule_id)
    
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Schedule '{schedule_id}' not found",
                "details": {},
            },
        )
    
    if not schedule.enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ALREADY_DISABLED",
                "message": f"Schedule '{schedule_id}' is already disabled",
                "details": {},
            },
        )
    
    schedule.enabled = False
    from datetime import datetime, timezone
    schedule.updated_at = datetime.now(timezone.utc).isoformat()
    store.save_schedule(schedule)
    
    return _schedule_to_response(schedule)


# ── Execution History Endpoints ───────────────────────────────────────

@router.get("/schedules/{schedule_id}/executions", response_model=ExecutionListResponse)
def list_executions(
    schedule_id: str,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    server_id: Optional[str] = Query(None, description="Filter by server"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ExecutionListResponse:
    """List executions for a schedule.
    
    Args:
        schedule_id: Schedule identifier.
        status: Filter by execution status (optional).
        server_id: Filter by target server (optional).
        limit: Maximum number of results (default: 100).
        offset: Pagination offset (default: 0).
    
    Returns:
        List of executions with pagination metadata.
    
    Raises:
        HTTPException 404: Schedule not found.
    """
    # Verify schedule exists
    schedule = store.get_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Schedule '{schedule_id}' not found",
                "details": {},
            },
        )
    
    # Get all executions for this schedule
    all_executions = store.get_executions_by_schedule(
        schedule_id=schedule_id,
        status_filter=status_filter,
        server_id=server_id,
        limit=limit,
        offset=offset,
    )
    
    # Apply filters
    if status_filter is not None:
        all_executions = [e for e in all_executions if e.status == status_filter]
    
    if server_id is not None:
        all_executions = [e for e in all_executions if e.server_id == server_id]
    
    # Apply pagination
    total = len(all_executions)
    paginated = all_executions[offset:offset + limit]
    
    return ExecutionListResponse(
        executions=[_execution_to_response(e) for e in paginated],
        total=total,
    )


@router.get("/schedule-executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: str,
    store: SchedulerStore = Depends(get_scheduler_store),
) -> ExecutionResponse:
    """Get execution detail by ID.
    
    Args:
        execution_id: Execution identifier.
    
    Returns:
        Execution detail.
    
    Raises:
        HTTPException 404: Execution not found.
    """
    execution = store.get_execution(execution_id)
    
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Execution '{execution_id}' not found",
                "details": {},
            },
        )
    
    return _execution_to_response(execution)


# ── Scheduler Status Endpoint ─────────────────────────────────────────

@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(
    scheduler: Optional[Scheduler] = Depends(lambda: None),  # Placeholder for scheduler instance
) -> SchedulerStatusResponse:
    """Get Scheduler runtime status.
    
    Note: This is a placeholder implementation. Full implementation requires
    Scheduler instance injection and runtime state tracking.
    
    Returns:
        Scheduler runtime status.
    """
    # Placeholder response - actual implementation requires Scheduler instance
    return SchedulerStatusResponse(
        enabled=False,  # Would come from Scheduler config
        running=False,  # Would come from Scheduler runtime state
        worker_limit=2,  # Default from SchedulerConfig
        active_workers=0,  # Would come from Scheduler runtime
        poll_interval=60,  # Default from SchedulerConfig
        last_poll_at=None,  # Would come from Scheduler runtime
    )
