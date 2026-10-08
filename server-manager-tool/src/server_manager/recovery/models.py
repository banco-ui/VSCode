"""Recovery / Remediation Domain Models — Phase 18.

Provider-neutral recovery action models for safely defining, evaluating,
and executing remediation actions on canonical entities with detected faults.

Key principles:
- AUTOMATIC_RECOVERY = DISABLED by default
- Recovery requires explicit evidence — no inference
- UNKNOWN → no recovery
- Recovery != Fault Detection, != Alert, != Root Cause Analysis
- Execution requires explicit gate: candidate + safety PASS + authorization + execution_enabled
- Pod != Workload (Phase 13E policy preserved)
- No escalation: failure does not auto-trigger other actions
- Idempotency: same (fault_id, action_type, target_entity_id) → no duplicate

This module does NOT:
    ❌ Call provider APIs
    ❌ Perform automatic recovery
    ❌ Infer root cause
    ❌ Escalate on failure
    ❌ Persist recovery history to a database
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from server_manager.fault.models import Fault
from server_manager.models.canonical import ProviderType


# ════════════════════════════════════════════════════════════════════════
#  ENUMS
# ════════════════════════════════════════════════════════════════════════


class RecoveryActionType(str, Enum):
    """Type of recovery action.

    Only explicitly supported actions are listed.
    A provider must declare support for the action before execution.
    Not all providers support all action types.
    """
    RESTART = "RESTART"
    REDEPLOY = "REDEPLOY"
    RESTART_WORKLOAD = "RESTART_WORKLOAD"
    RESTART_EXECUTION_ENVIRONMENT = "RESTART_EXECUTION_ENVIRONMENT"


class RecoveryCandidateStatus(str, Enum):
    """Lifecycle status of a recovery candidate.

    PROPOSED:    Candidate created from a fault
    SUPPORTED:   Provider capability confirmed
    UNSUPPORTED: Provider does not support this action
    BLOCKED:     Safety gate blocked execution
    APPROVED:    Authorization granted
    EXECUTED:    Action was executed
    VERIFIED:    Post-action verification passed
    FAILED:      Execution or verification failed
    """
    PROPOSED = "PROPOSED"
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class RecoveryExecutionStatus(str, Enum):
    """Status of a recovery execution result.

    NOT_EXECUTED:          Action was not executed (blocked or not enabled)
    BLOCKED:               Safety gate or authorization blocked execution
    DRY_RUN:               Dry-run preview only, no mutation
    EXECUTED:              Action was executed but not yet verified
    FAILED:                Execution failed
    VERIFIED:              Post-action verification passed (requires evidence)
    VERIFICATION_FAILED:   Post-action verification failed
    """
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"
    DRY_RUN = "DRY_RUN"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    VERIFIED = "VERIFIED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class AuthorizationLevel(str, Enum):
    """Authorization levels for recovery operations.

    Levels are ordered: DISCOVERY < READ_ONLY < DRY_RUN < EXECUTE
    Only EXECUTE authorization permits actual mutation.
    """
    DISCOVERY = "DISCOVERY"
    READ_ONLY = "READ_ONLY"
    DRY_RUN = "DRY_RUN"
    EXECUTE = "EXECUTE"

    def __lt__(self, other: "AuthorizationLevel") -> bool:
        _order = {
            AuthorizationLevel.DISCOVERY: 0,
            AuthorizationLevel.READ_ONLY: 1,
            AuthorizationLevel.DRY_RUN: 2,
            AuthorizationLevel.EXECUTE: 3,
        }
        return _order[self] < _order[other]


class SafetyResult(str, Enum):
    """Safety gate evaluation result."""
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class SafetyBlockReason(str, Enum):
    """Reason for safety gate blocking."""
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNKNOWN_PROVIDER = "UNKNOWN_PROVIDER"
    UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
    INVALID_TARGET = "INVALID_TARGET"
    EXECUTION_NOT_ENABLED = "EXECUTION_NOT_ENABLED"
    AMBIGUOUS_TARGET = "AMBIGUOUS_TARGET"
    SAFETY_POLICY_BLOCKED = "SAFETY_POLICY_BLOCKED"
    DUPLICATE_RECOVERY = "DUPLICATE_RECOVERY"
    UNKNOWN_FAULT = "UNKNOWN_FAULT"
    MISSING_FAULT_EVIDENCE = "MISSING_FAULT_EVIDENCE"
    INSUFFICIENT_AUTHORIZATION = "INSUFFICIENT_AUTHORIZATION"
    FAULT_NOT_ACTIONABLE = "FAULT_NOT_ACTIONABLE"


# ════════════════════════════════════════════════════════════════════════
#  SAFETY GATE RESULT
# ════════════════════════════════════════════════════════════════════════


class SafetyGateResult(BaseModel):
    """Result of safety gate evaluation.

    Contains the overall result and individual check outcomes.
    """
    result: SafetyResult
    reason: Optional[SafetyBlockReason] = None
    checks_passed: list[str] = Field(default_factory=list)
    checks_failed: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  RECOVERY ACTION PARAMETERS
# ════════════════════════════════════════════════════════════════════════


class RecoveryActionParameters(BaseModel):
    """Typed parameters for a recovery action.

    No arbitrary provider command strings — all parameters are typed
    and explicitly constrained. This prevents injection of arbitrary
    provider commands.
    """
    namespace: Optional[str] = None
    force: bool = False
    timeout_seconds: Optional[int] = None
    grace_period_seconds: Optional[int] = None

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  RECOVERY ACTION
# ════════════════════════════════════════════════════════════════════════


class RecoveryAction(BaseModel):
    """A recovery action definition.

    Identity = action_id (deterministic: fault_id + action_type + target).
    A RecoveryAction is NOT authorization and NOT execution — it is
    the definition of what should happen.
    """
    action_id: str = Field(min_length=1)
    action_type: RecoveryActionType
    target_entity_id: str = Field(min_length=1)
    provider_type: ProviderType
    requested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    requested_by: str = "system"
    reason: str = ""
    fault_id: str = Field(min_length=1)
    parameters: RecoveryActionParameters = Field(
        default_factory=RecoveryActionParameters
    )

    model_config = {"extra": "forbid"}

    @property
    def identity_key(self) -> str:
        """Deterministic identity for deduplication.

        Same (fault_id, action_type, target_entity_id) → same identity.
        """
        return f"{self.fault_id}:{self.action_type.value}:{self.target_entity_id}"


# ════════════════════════════════════════════════════════════════════════
#  RECOVERY CANDIDATE
# ════════════════════════════════════════════════════════════════════════


class RecoveryCandidate(BaseModel):
    """A recovery candidate proposed from a fault.

    Candidate != Authorization, != Execution.
    A candidate is a *proposal* — it does not execute anything.
    """
    candidate_id: str = Field(min_length=1)
    fault: Fault
    action: RecoveryAction
    status: RecoveryCandidateStatus = RecoveryCandidateStatus.PROPOSED
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    block_reason: Optional[SafetyBlockReason] = None
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  RECOVERY PREVIEW
# ════════════════════════════════════════════════════════════════════════


class RecoveryPreview(BaseModel):
    """Preview of a recovery action without mutation.

    Preview does NOT call provider mutation APIs.
    It is deterministic: same action → same preview.
    """
    action: RecoveryAction
    expected_effect: str = ""
    safety_result: SafetyResult = SafetyResult.BLOCKED
    safety_reason: Optional[SafetyBlockReason] = None
    supported: bool = False
    previewed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  RECOVERY EXECUTION RESULT
# ════════════════════════════════════════════════════════════════════════


class RecoveryExecutionResult(BaseModel):
    """Result of executing a recovery action.

    NOT_EXECUTED and BLOCKED are NOT success.
    VERIFIED requires post-action verification evidence —
    a successful API call alone does NOT qualify as VERIFIED.

    Execution ≠ Verification:
        EXECUTED means the action ran.
        VERIFIED means post-action state was confirmed recovered.
    """
    action_id: str = Field(min_length=1)
    status: RecoveryExecutionStatus = RecoveryExecutionStatus.NOT_EXECUTED
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    provider: ProviderType = ProviderType.UNKNOWN
    target: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    model_config = {"extra": "forbid"}

    @property
    def is_success(self) -> bool:
        """True only if post-action verification passed."""
        return self.status == RecoveryExecutionStatus.VERIFIED

    @property
    def was_executed(self) -> bool:
        """True if the action was actually executed (not just previewed/blocked)."""
        return self.status in (
            RecoveryExecutionStatus.EXECUTED,
            RecoveryExecutionStatus.VERIFIED,
            RecoveryExecutionStatus.VERIFICATION_FAILED,
            RecoveryExecutionStatus.FAILED,
        )
