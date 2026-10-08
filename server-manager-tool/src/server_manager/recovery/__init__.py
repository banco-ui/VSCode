"""Recovery / Remediation package — Phase 18.

Provider-neutral recovery framework for safely defining, evaluating,
and executing remediation actions on canonical entities with detected faults.

    Fault (Phase 17)
        ↓
    RecoveryCandidate
        ↓
    Safety / Authorization Gate
        ↓
    Provider Capability Check
        ↓
    Preview / Dry-Run
        ↓
    Execution (if explicitly enabled)
        ↓
    Post-Action Verification
        ↓
    RecoveryExecutionResult

SAFETY PRINCIPLES:
    - AUTOMATIC_RECOVERY = DISABLED by default
    - No provider API calls unless execution_enabled=True
    - No inference: fault evidence required
    - Pod != Workload (Phase 13E policy preserved)
    - No escalation on failure
    - Idempotency: same (fault_id, action_type, target) → no duplicate
"""
from .models import (
    AuthorizationLevel,
    RecoveryAction,
    RecoveryActionParameters,
    RecoveryActionType,
    RecoveryCandidate,
    RecoveryCandidateStatus,
    RecoveryExecutionResult,
    RecoveryExecutionStatus,
    RecoveryPreview,
    SafetyBlockReason,
    SafetyGateResult,
    SafetyResult,
)
from .service import (
    MockRecoveryExecutor,
    RecoveryExecutor,
    RecoveryGraphContext,
    RecoverySafetyGate,
    RecoveryService,
)

__all__ = [
    # Enums
    "RecoveryActionType",
    "RecoveryCandidateStatus",
    "RecoveryExecutionStatus",
    "AuthorizationLevel",
    "SafetyResult",
    "SafetyBlockReason",
    # Models
    "RecoveryActionParameters",
    "RecoveryAction",
    "RecoveryCandidate",
    "RecoveryPreview",
    "RecoveryExecutionResult",
    "SafetyGateResult",
    # Services
    "RecoverySafetyGate",
    "RecoveryExecutor",
    "MockRecoveryExecutor",
    "RecoveryGraphContext",
    "RecoveryService",
]
