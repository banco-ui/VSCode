"""Fault Detection package — Phase 17.

Provider-neutral fault detection from monitoring observations.

    Monitoring Observations + State Changes
        ↓
    FaultDetectionService.detect()
        ↓
    FaultResult (Faults with lifecycle)

    FaultGraphContext (read-only graph context lookup via Phase 16)

READ_ONLY: No mutation, no alerts, no recovery, no inference.
"""
from .models import (
    Fault,
    FaultResult,
    FaultStatus,
    FaultType,
    Severity,
    ThresholdPolicy,
)
from .service import FaultDetectionService, FaultGraphContext

__all__ = [
    # Models
    "Fault",
    "FaultType",
    "Severity",
    "FaultStatus",
    "FaultResult",
    "ThresholdPolicy",
    # Service
    "FaultDetectionService",
    "FaultGraphContext",
]
