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
        
        # Process conditions - failures
        for alert_type, resource_type, condition, severity in conditions:
            self._handle_failure(ctx, alert_type, resource_type, condition, severity, result)
        
        # Handle OK condition (no failures)
        if not conditions:
            # All clear - check for recovery
            self._handle_ok_all(ctx, result)
        
        return result
    
    def _handle_ok_all(self, ctx: AlertEvaluationContext, result: AlertEvaluationResult) -> None:
        """Handle all-clear condition (OK observation)."""
        # Reset ALL failure tracking for this server on OK
        self.alert_store.reset_all_failure_tracking(ctx.server_id)
        
        # Get all active alerts for this server
        open_alerts = self.alert_store.list_alerts(
            server_id=ctx.server_id,
            status_filter=AlertStatus.OPEN,
        )
        
        ack_alerts = self.alert_store.list_alerts(
            server_id=ctx.server_id,
            status_filter=AlertStatus.ACKNOWLEDGED,
        )
        
        all_alerts = open_alerts + ack_alerts
        
        for alert in all_alerts:
            ok_count = self.alert_store.increment_ok_count(alert.alert_id, ctx.snapshot_id)
            result.alerts_updated += 1
            result.updated_alert_ids.append(alert.alert_id)
            
            # Check if recovery threshold reached
            if ok_count >= RECOVERY_THRESHOLD:
                self.alert_store.resolve_alert(
                    alert.alert_id,
                    resolution_note=f"Recovered after {ok_count} consecutive OK observations",
                )
                result.alerts_resolved += 1
                result.resolved_alert_ids.append(alert.alert_id)
    
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
            # Reset OK counter on failure
            self.alert_store.reset_ok_count(existing.alert_id)
            
            # Increment failure counter
            self.alert_store.update_counters(
                existing.alert_id,
                failure=True,
                snapshot_id=ctx.snapshot_id,
            )
            result.alerts_updated += 1
            result.updated_alert_ids.append(existing.alert_id)
        else:
            # Check for resolved alert with same fingerprint
            resolved = self.alert_store.get_alert_by_fingerprint(
                fingerprint,
                status_filter=[AlertStatus.RESOLVED],
            )
            
            if resolved:
                # RESOLVED alert exists - track failure for new alert
                # But don't count towards threshold yet
                count = self.alert_store.increment_failure_count(
                    server_id=ctx.server_id,
                    fingerprint=fingerprint,
                    alert_type=alert_type,
                    resource_type=resource_type,
                    condition=condition,
                    snapshot_id=ctx.snapshot_id,
                )
                
                if count >= FAILURE_THRESHOLD:
                    # Create new alert
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
            else:
                # No active or resolved alert - track failure count
                count = self.alert_store.increment_failure_count(
                    server_id=ctx.server_id,
                    fingerprint=fingerprint,
                    alert_type=alert_type,
                    resource_type=resource_type,
                    condition=condition,
                    snapshot_id=ctx.snapshot_id,
                )
                
                if count >= FAILURE_THRESHOLD:
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
    
    def _handle_ok(
        self,
        ctx: AlertEvaluationContext,
        alert_type: AlertType,
        resource_type: ResourceType,
        condition: str,
        result: AlertEvaluationResult,
    ) -> None:
        """Handle OK condition with M=5 recovery threshold."""
        fingerprint = create_fingerprint(
            server_id=ctx.server_id,
            alert_type=alert_type.value,
            resource_type=resource_type.value,
            resource_id=None,
            condition=condition,
            version=1,
        )
        
        # Reset failure tracking on OK
        self.alert_store.reset_failure_count(ctx.server_id, fingerprint)
        
        # Check for existing active alert
        existing = self.alert_store.get_alert_by_fingerprint(
            fingerprint,
            status_filter=[AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED],
        )
        
        if existing:
            # Increment OK counter
            ok_count = self.alert_store.increment_ok_count(
                existing.alert_id,
                ctx.snapshot_id,
            )
            result.alerts_updated += 1
            result.updated_alert_ids.append(existing.alert_id)
            
            # Check if recovery threshold reached
            if ok_count >= RECOVERY_THRESHOLD:
                # Resolve alert
                self.alert_store.resolve_alert(
                    existing.alert_id,
                    resolution_note=f"Recovered after {ok_count} consecutive OK observations",
                )
                result.alerts_resolved += 1
                result.resolved_alert_ids.append(existing.alert_id)