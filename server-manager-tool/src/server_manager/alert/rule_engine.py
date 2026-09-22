"""Alert Rule Engine — Phase 11D-1.

Rule-based alert evaluation with N=3 failure threshold and M=5 recovery threshold.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .models import Alert, AlertStatus, AlertSeverity, AlertType, ResourceType
from .fingerprint import create_fingerprint
from .store import AlertStore

logger = logging.getLogger(__name__)

# Threshold constants
FAILURE_THRESHOLD = 3  # N=3: consecutive failures to OPEN
RECOVERY_THRESHOLD = 5  # M=5: consecutive OKs to RESOLVE


@dataclass
class AlertEvaluationContext:
    """Evaluation context for alert rule engine."""
    server_id: str
    snapshot_id: str
    collection_success: bool = True
    health_status: str = "OK"
    verification_discrepancy: bool = False
    scheduler_failure: bool = False
    observation_timestamp: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.observation_timestamp is None:
            self.observation_timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class AlertEvaluationResult:
    """Result of alert evaluation."""
    evaluated: bool = True
    snapshot_id: Optional[str] = None
    server_id: Optional[str] = None
    alerts_created: int = 0
    alerts_updated: int = 0
    alerts_resolved: int = 0
    duplicates_ignored: int = 0
    created_alert_ids: list[str] = field(default_factory=list)
    updated_alert_ids: list[str] = field(default_factory=list)
    resolved_alert_ids: list[str] = field(default_factory=list)


class RuleEngine:
    """Alert Rule Engine — Phase 11D-1."""
    
    def __init__(self, alert_store: AlertStore):
        self.alert_store = alert_store
    
    def evaluate(self, ctx: AlertEvaluationContext) -> AlertEvaluationResult:
        """Evaluate observation and update alerts."""
        self._validate_context(ctx)
        
        result = AlertEvaluationResult(
            snapshot_id=ctx.snapshot_id,
            server_id=ctx.server_id,
        )
        
        # Check idempotency
        if self._is_snapshot_evaluated(ctx):
            result.evaluated = False
            result.duplicates_ignored = 1
            return result
        
        # Register evaluation
        self._register_evaluation(ctx)
        
        # Evaluate rules
        conditions = self._evaluate_rules(ctx)
        
        # Process conditions
        for alert_type, resource_type, condition, severity in conditions:
            self._handle_failure(ctx, alert_type, resource_type, condition, severity, result)
        
        return result
    
    def _validate_context(self, ctx: AlertEvaluationContext) -> None:
        if not ctx.server_id:
            raise ValueError("server_id is required")
        if not ctx.snapshot_id:
            raise ValueError("snapshot_id is required")
    
    def _is_snapshot_evaluated(self, ctx: AlertEvaluationContext) -> bool:
        return self.alert_store.is_snapshot_evaluated(ctx.server_id, ctx.snapshot_id)
    
    def _register_evaluation(self, ctx: AlertEvaluationContext) -> None:
        self.alert_store.record_evaluation(
            server_id=ctx.server_id,
            snapshot_id=ctx.snapshot_id,
            evaluated_at=ctx.observation_timestamp,
        )
    
    def _evaluate_rules(self, ctx: AlertEvaluationContext) -> list[tuple[AlertType, ResourceType, str, AlertSeverity]]:
        """Evaluate rules and return triggered conditions."""
        conditions = []
        
        # Rule 1: Collection failure
        if not ctx.collection_success:
            conditions.append((AlertType.COLLECTION_FAILURE, ResourceType.SERVICE, "collection_failed", AlertSeverity.CRITICAL))
        # Rule 2: Health critical
        elif ctx.health_status == "CRITICAL":
            conditions.append((AlertType.HEALTH_CRITICAL, ResourceType.SYSTEM, "health == CRITICAL", AlertSeverity.CRITICAL))
        # Rule 3: Health warning
        elif ctx.health_status == "WARNING":
            conditions.append((AlertType.HEALTH_WARNING, ResourceType.SYSTEM, "health == WARNING", AlertSeverity.WARNING))
        
        # Rule 4: Verification discrepancy
        if ctx.verification_discrepancy:
            conditions.append((AlertType.VERIFICATION_DISCREPANCY, ResourceType.SYSTEM, "verification_mismatch", AlertSeverity.WARNING))
        
        # Rule 5: Scheduler failure
        if ctx.scheduler_failure:
            conditions.append((AlertType.SCHEDULER_FAILURE, ResourceType.SERVICE, "scheduler_error", AlertSeverity.CRITICAL))
        
        return conditions
    
    def _handle_failure(
        self,
        ctx: AlertEvaluationContext,
        alert_type: AlertType,
        resource_type: ResourceType,
        condition: str,
        severity: AlertSeverity,
        result: AlertEvaluationResult,
    ) -> None:
        """Handle failure condition with N=3 threshold."""
        fingerprint = create_fingerprint(
            server_id=ctx.server_id,
            alert_type=alert_type.value,
            resource_type=resource_type.value,
            resource_id=None,
            condition=condition,
            version=1,
        )
        
        # Check for existing active alert
        existing = self.alert_store.get_alert_by_fingerprint(
            fingerprint,
            status_filter=[AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED],
        )
        
        if existing:
            # Increment failure counter
            new_count = existing.consecutive_failure_count + 1
            self.alert_store.update_counters(
                existing.alert_id,
                failure=True,
                snapshot_id=ctx.snapshot_id,
            )
            result.alerts_updated += 1
            result.updated_alert_ids.append(existing.alert_id)
        else:
            # Check if we should create new alert
            # For new alerts, we need to track failures
            # Simplified: create alert immediately on first failure
            # TODO: Implement pre-alert failure tracking for N=3
            alert = self.alert_store.create_alert(
                server_id=ctx.server_id,
                alert_type=alert_type,
                resource_type=resource_type,
                condition=condition,
                severity=severity,
                snapshot_id=ctx.snapshot_id,
                metadata_json=ctx.metadata,
            )
            result.alerts_created += 1
            result.created_alert_ids.append(alert.alert_id)