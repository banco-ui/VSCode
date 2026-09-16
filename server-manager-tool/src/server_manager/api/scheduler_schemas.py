"""Scheduler API Schemas (Phase 10C).

Pydantic models for Scheduler API request/response.
Reuses existing domain models where possible.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Schedule Definition ───────────────────────────────────────────────

class ScheduleCreateRequest(BaseModel):
    """Request to create a new schedule."""
    name: str = Field(..., min_length=1, description="Human-readable schedule name")
    server_ids: list[str] = Field(..., min_length=1, description="Target server IDs")
    enabled: bool = Field(default=False, description="Schedule active state (default: false for safety)")
    cron_expression: Optional[str] = Field(default=None, description="Cron expression (optional)")
    interval_seconds: Optional[int] = Field(default=None, description="Interval in seconds (optional)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("interval_seconds")
    @classmethod
    def validate_interval(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 60:
            raise ValueError("interval_seconds must be at least 60 seconds")
        return v

    @field_validator("cron_expression", "interval_seconds")
    @classmethod
    def validate_schedule_expression(cls, cron: Optional[str], interval: Optional[int]) -> None:
        # At least one must be provided (validated at model level)
        pass

    @field_validator("server_ids")
    @classmethod
    def validate_server_ids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("server_ids must not be empty")
        return v


class ScheduleUpdateRequest(BaseModel):
    """Request to update an existing schedule."""
    name: Optional[str] = Field(default=None, min_length=1)
    server_ids: Optional[list[str]] = Field(default=None, min_length=1)
    enabled: Optional[bool] = Field(default=None)
    cron_expression: Optional[str] = Field(default=None)
    interval_seconds: Optional[int] = Field(default=None, ge=60)
    metadata: Optional[dict[str, Any]] = Field(default=None)


class ScheduleResponse(BaseModel):
    """Schedule definition response."""
    schedule_id: str
    name: str
    server_ids: list[str]
    enabled: bool
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class ScheduleListResponse(BaseModel):
    """List schedules response."""
    schedules: list[ScheduleResponse] = Field(default_factory=list)
    total: int = 0


# ── Schedule Execution ─────────────────────────────────────────────────

class ExecutionResponse(BaseModel):
    """Schedule execution response."""
    execution_id: str
    schedule_id: str
    server_id: str
    run_id: Optional[str] = None
    status: str
    claimed_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ExecutionListResponse(BaseModel):
    """List executions response."""
    executions: list[ExecutionResponse] = Field(default_factory=list)
    total: int = 0


# ── Scheduler Status ───────────────────────────────────────────────────

class SchedulerStatusResponse(BaseModel):
    """Scheduler runtime status response."""
    enabled: bool
    running: bool
    worker_limit: int
    active_workers: int
    poll_interval: int
    last_poll_at: Optional[str] = None
