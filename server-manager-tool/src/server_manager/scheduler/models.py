"""Scheduler domain models — Phase 10B.

ScheduleDefinition: Persistent schedule definition.
ScheduleExecution: Individual execution record.
ScheduleStatus: Schedule lifecycle status.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScheduleStatus(str, Enum):
    """Schedule lifecycle status."""
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    RUNNING = "RUNNING"  # Currently executing
    FAILED = "FAILED"  # Last execution failed


class ScheduleDefinition(BaseModel):
    """Persistent schedule definition.
    
    Attributes:
        schedule_id: Unique identifier for this schedule.
        name: Human-readable name/description.
        server_ids: List of target server IDs to collect.
        enabled: Whether this schedule is active.
        cron_expression: Cron expression for scheduling (e.g., "0 */6 * * *").
        interval_seconds: Alternative to cron — run every N seconds.
        last_run_at: ISO timestamp of last successful execution.
        next_run_at: ISO timestamp of next scheduled execution.
        created_at: ISO timestamp of creation.
        updated_at: ISO timestamp of last update.
        metadata: Optional additional metadata.
    """
    schedule_id: str
    name: str
    server_ids: list[str] = Field(default_factory=list)
    enabled: bool = True
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"extra": "forbid"}
    
    def is_due(self, current_time: Optional[datetime] = None) -> bool:
        """Check if this schedule is due for execution.
        
        Args:
            current_time: Time to check against (defaults to now).
            
        Returns:
            True if the schedule should run now.
        """
        if not self.enabled:
            return False
        
        if self.next_run_at is None:
            # No next run time set — should run immediately
            return True
        
        current = current_time or datetime.now(timezone.utc)
        try:
            next_run = datetime.fromisoformat(self.next_run_at.replace("Z", "+00:00"))
            return current >= next_run
        except (ValueError, AttributeError):
            # Invalid timestamp — treat as due
            return True
    
    def calculate_next_run(self, current_time: Optional[datetime] = None) -> datetime:
        """Calculate the next run time based on interval or cron.
        
        Args:
            current_time: Base time for calculation (defaults to now).
            
        Returns:
            Next scheduled run time.
        """
        current = current_time or datetime.now(timezone.utc)
        
        if self.interval_seconds:
            # Simple interval-based scheduling
            from datetime import timedelta
            return current + timedelta(seconds=self.interval_seconds)
        
        # Default: 6 hour interval if no cron or interval specified
        if not self.cron_expression:
            from datetime import timedelta
            return current + timedelta(hours=6)
        
        # Cron parsing would require external library
        # For now, default to 6 hours
        from datetime import timedelta
        return current + timedelta(hours=6)


class ScheduleExecution(BaseModel):
    """Record of a single schedule execution.
    
    Attributes:
        execution_id: Unique identifier for this execution.
        schedule_id: Reference to parent schedule.
        server_id: Target server for this execution.
        run_id: Reference to orchestration run_id.
        status: Execution status.
        claimed_at: When execution was claimed.
        started_at: When execution started.
        completed_at: When execution completed.
        error_message: Error message if failed.
        recovery_id: Optional recovery operation identifier (Phase 10D).
        recovery_count: Number of times this execution was recovered (Phase 10D).
    """
    execution_id: str
    schedule_id: str
    server_id: str
    run_id: Optional[str] = None
    status: str = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED, SKIPPED, CLAIMED, RECOVERED
    claimed_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    recovery_id: Optional[str] = None  # Phase 10D: Recovery operation identifier
    recovery_count: int = 0  # Phase 10D: Number of recovery attempts
    
    model_config = {"extra": "forbid"}
