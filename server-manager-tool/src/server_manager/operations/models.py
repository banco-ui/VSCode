"""Cross-Platform Operations Domain Models — Phase 19.

Provider-neutral operation layer for safely defining, evaluating, and
executing infrastructure operations across heterogeneous providers.

    Canonical Target
        ↓
    OperationRequest
        ↓
    Target Resolution
        ↓
    Provider / Capability Resolution
        ↓
    Safety / Authorization Gate
        ↓
    Preview (dry-run)
        ↓
    Execute (if enabled)
        ↓
    Post-Action Verification
        ↓
    OperationResult

Key principles:
- Reuses Phase 18 AuthorizationLevel, SafetyResult
- OperationType includes START, STOP, RESTART, REDEPLOY, SCALE, QUERY_STATUS
- RESTART/REDEPLOY overlap with RecoveryActionType — mapping provided
- No arbitrary shell commands or untyped dicts as primary interface
- No inference: target must be deterministically resolved
- UNKNOWN remains UNKNOWN — not converted to SUPPORTED
- Execution disabled by default
- Idempotency: target + operation_type + normalized parameters → identity
- No persistent database — in-memory only
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from server_manager.models.canonical import ProviderType
from server_manager.recovery.models import (
    AuthorizationLevel,
    RecoveryActionType,
    SafetyResult,
)


# ════════════════════════════════════════════════════════════════════════
#  ENUMS
# ════════════════════════════════════════════════════════════════════════


class OperationType(str, Enum):
    """Type of cross-platform operation.

    Only operations with a meaningful cross-platform contract are listed.
    Not every provider supports every operation — capability resolution
    determines support.

    Relationship to Phase 18 RecoveryActionType:
        RESTART   ↔ RecoveryActionType.RESTART
        REDEPLOY  ↔ RecoveryActionType.REDEPLOY
        START, STOP, SCALE, QUERY_STATUS are operation-layer additions.
    """
    START = "START"
    STOP = "STOP"
    RESTART = "RESTART"
    REDEPLOY = "REDEPLOY"
    SCALE = "SCALE"
    QUERY_STATUS = "QUERY_STATUS"

    @property
    def is_mutating(self) -> bool:
        """QUERY_STATUS is the only non-mutating operation."""
        return self != OperationType.QUERY_STATUS

    @property
    def requires_execute_auth(self) -> bool:
        """Mutating operations require EXECUTE authorization."""
        return self != OperationType.QUERY_STATUS

    @staticmethod
    def from_recovery_action_type(
        action_type: RecoveryActionType,
    ) -> Optional["OperationType"]:
        """Map a Phase 18 RecoveryActionType to an OperationType."""
        _MAP = {
            RecoveryActionType.RESTART: OperationType.RESTART,
            RecoveryActionType.REDEPLOY: OperationType.REDEPLOY,
            RecoveryActionType.RESTART_WORKLOAD: OperationType.RESTART,
            RecoveryActionType.RESTART_EXECUTION_ENVIRONMENT: OperationType.RESTART,
        }
        return _MAP.get(action_type)


class CapabilityDecision(str, Enum):
    """Provider capability resolution result.

    SUPPORTED:    Provider explicitly advertises support
    UNSUPPORTED:  Provider explicitly does not support
    UNKNOWN:      Provider capability not established — NOT SUPPORTED
    UNAVAILABLE:  Provider not reachable or credential unavailable
    """
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"

    @property
    def is_supported(self) -> bool:
        return self == CapabilityDecision.SUPPORTED


class OperationBlockReason(str, Enum):
    """Reasons for operation safety gate blocking."""
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNKNOWN_PROVIDER = "UNKNOWN_PROVIDER"
    UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
    INVALID_TARGET = "INVALID_TARGET"
    EXECUTION_NOT_ENABLED = "EXECUTION_NOT_ENABLED"
    AMBIGUOUS_TARGET = "AMBIGUOUS_TARGET"
    SAFETY_POLICY_BLOCKED = "SAFETY_POLICY_BLOCKED"
    DUPLICATE_OPERATION = "DUPLICATE_OPERATION"
    INSUFFICIENT_AUTHORIZATION = "INSUFFICIENT_AUTHORIZATION"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    TARGET_UNRESOLVED = "TARGET_UNRESOLVED"


class OperationStatus(str, Enum):
    """Status of an operation result.

    NOT_EXECUTED:          Operation was not executed (blocked or not enabled)
    BLOCKED:               Safety gate blocked execution
    DRY_RUN:               Dry-run preview only, no mutation
    EXECUTED:              Operation ran but not yet verified
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

    @property
    def is_success(self) -> bool:
        return self == OperationStatus.VERIFIED

    @property
    def was_executed(self) -> bool:
        return self in (
            OperationStatus.EXECUTED,
            OperationStatus.VERIFIED,
            OperationStatus.VERIFICATION_FAILED,
            OperationStatus.FAILED,
        )


# ════════════════════════════════════════════════════════════════════════
#  SAFETY GATE RESULT
# ════════════════════════════════════════════════════════════════════════


class OperationSafetyGateResult(BaseModel):
    """Result of operation safety gate evaluation."""
    result: SafetyResult
    reason: Optional[OperationBlockReason] = None
    checks_passed: list[str] = Field(default_factory=list)
    checks_failed: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  TARGET RESOLUTION
# ════════════════════════════════════════════════════════════════════════


class TargetResolution(BaseModel):
    """Result of resolving an operation target.

    Primary identity is canonical_id.
    provider_id used only when explicitly established by evidence.
    If resolved=False, target could not be deterministically resolved.
    """
    resolved: bool = False
    canonical_id: str = ""
    provider_id: Optional[str] = None
    provider_type: ProviderType = ProviderType.UNKNOWN
    entity_type: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    ambiguous: bool = False

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  OPERATION PARAMETERS
# ════════════════════════════════════════════════════════════════════════


class OperationParameters(BaseModel):
    """Typed parameters for a cross-platform operation.

    No arbitrary shell commands — all parameters are typed and
    explicitly constrained. This prevents injection of arbitrary
    provider commands.
    """
    namespace: Optional[str] = None
    force: bool = False
    timeout_seconds: Optional[int] = None
    grace_period_seconds: Optional[int] = None
    replicas: Optional[int] = None

    model_config = {"extra": "forbid"}

    def normalized_hash(self) -> str:
        """Deterministic hash of parameters for idempotency identity."""
        parts = [
            f"ns={self.namespace or ''}",
            f"force={self.force}",
            f"to={self.timeout_seconds or ''}",
            f"gp={self.grace_period_seconds or ''}",
            f"rep={self.replicas or ''}",
        ]
        return "|".join(parts)



# ════════════════════════════════════════════════════════════════════════
#  OPERATION REQUEST
# ════════════════════════════════════════════════════════════════════════


class OperationRequest(BaseModel):
    """A typed operation request.

    Identity = operation_id (deterministic: target + op_type + params).
    A request is NOT authorization and NOT execution.
    """
    operation_id: str = Field(min_length=1)
    operation_type: OperationType
    target_canonical_id: str = Field(min_length=1)
    provider_type: ProviderType = ProviderType.UNKNOWN
    parameters: OperationParameters = Field(default_factory=OperationParameters)
    authorization: AuthorizationLevel = AuthorizationLevel.READ_ONLY
    execution_enabled: bool = False
    requested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    requested_by: str = "system"
    reason: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @property
    def identity_key(self) -> str:
        """Deterministic identity for idempotency."""
        return (
            f"{self.target_canonical_id}:"
            f"{self.operation_type.value}:"
            f"{self.parameters.normalized_hash()}"
        )

    @property
    def is_mutating(self) -> bool:
        return self.operation_type.is_mutating


# ════════════════════════════════════════════════════════════════════════
#  OPERATION PREVIEW
# ════════════════════════════════════════════════════════════════════════


class OperationPreview(BaseModel):
    """Preview of an operation without mutation.

    Deterministic: same request → same preview.
    Preview does NOT call provider mutation APIs.
    """
    request: OperationRequest
    resolved_target: Optional[TargetResolution] = None
    capability_decision: CapabilityDecision = CapabilityDecision.UNKNOWN
    expected_effect: str = ""
    safety_result: SafetyResult = SafetyResult.BLOCKED
    safety_reason: Optional[OperationBlockReason] = None
    authorization_level: AuthorizationLevel = AuthorizationLevel.READ_ONLY
    execution_allowed: bool = False
    previewed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  OPERATION RESULT
# ════════════════════════════════════════════════════════════════════════


class OperationResult(BaseModel):
    """Result of executing a cross-platform operation.

    Execution != Verification:
        EXECUTED means the operation ran.
        VERIFIED means post-action state was confirmed.

    NOT_EXECUTED and BLOCKED are NOT success.
    VERIFIED requires post-action verification evidence —
    a successful API call alone does NOT qualify as VERIFIED.
    """
    operation_id: str = Field(min_length=1)
    status: OperationStatus = OperationStatus.NOT_EXECUTED
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    provider: ProviderType = ProviderType.UNKNOWN
    target: str = ""
    resolved_target: Optional[TargetResolution] = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    model_config = {"extra": "forbid"}

    @property
    def is_success(self) -> bool:
        return self.status == OperationStatus.VERIFIED

    @property
    def was_executed(self) -> bool:
        return self.status.was_executed
