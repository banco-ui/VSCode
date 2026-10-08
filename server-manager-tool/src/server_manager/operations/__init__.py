"""Cross-Platform Operations package — Phase 19.

Provider-neutral operation layer for safely defining, resolving, previewing,
executing, and verifying infrastructure operations across heterogeneous providers.

    OperationRequest
        ↓
    Target Resolution (canonical_id)
        ↓
    Capability Resolution (SUPPORTED / UNSUPPORTED / UNKNOWN)
        ↓
    Safety / Authorization Gate
        ↓
    Preview (dry-run, no mutation)
        ↓
    Execution (if execution_enabled=True)
        ↓
    Post-Action Verification
        ↓
    OperationResult

SAFETY PRINCIPLES:
    - Execution disabled by default
    - No provider API calls unless execution_enabled=True AND safety PASS
    - No inference: target must be deterministically resolved
    - UNKNOWN capability is NOT SUPPORTED
    - No escalation: failure does not auto-trigger other operations
    - Idempotency: same (target, op_type, params) → no duplicate
    - Reuses Phase 18 AuthorizationLevel semantics
    - Graph used for context only — not causality
"""
from .models import (
    CapabilityDecision,
    OperationBlockReason,
    OperationParameters,
    OperationPreview,
    OperationRequest,
    OperationResult,
    OperationSafetyGateResult,
    OperationStatus,
    OperationType,
    TargetResolution,
)
from .service import (
    CapabilityResolver,
    MockOperationExecutor,
    OperationExecutor,
    OperationGraphContext,
    OperationSafetyGate,
    OperationService,
    TargetResolver,
)

__all__ = [
    # Enums
    "OperationType",
    "CapabilityDecision",
    "OperationBlockReason",
    "OperationStatus",
    # Models
    "OperationParameters",
    "OperationRequest",
    "OperationPreview",
    "OperationResult",
    "OperationSafetyGateResult",
    "TargetResolution",
    # Services
    "CapabilityResolver",
    "TargetResolver",
    "OperationSafetyGate",
    "OperationExecutor",
    "MockOperationExecutor",
    "OperationGraphContext",
    "OperationService",
]
