"""Monitoring package — Phase 17.

Provider-neutral observation and state change detection.

    HealthReport (Phase 15)
        ↓
    MonitoringService.monitor()
        ↓
    MonitoringReport (Observations + StateChanges)

READ_ONLY: No mutation, no alerts, no recovery, no persistence.
"""
from .models import (
    MonitoringReport,
    Observation,
    StateChange,
)
from .service import MonitoringService

__all__ = [
    # Models
    "Observation",
    "StateChange",
    "MonitoringReport",
    # Service
    "MonitoringService",
]
