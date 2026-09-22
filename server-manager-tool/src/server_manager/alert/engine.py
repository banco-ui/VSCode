"""Alert Engine — Phase 11D-2.

High-level alert evaluation engine for Scheduler integration.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .rule_engine import RuleEngine, AlertEvaluationContext, AlertEvaluationResult
from .store import AlertStore

logger = logging.getLogger(__name__)


@dataclass
class AlertEngineResult:
    """Result of alert engine evaluation."""
    success: bool = True
    error_message: Optional[str] = None
    evaluation_result: Optional[AlertEvaluationResult] = None


class AlertEngine:
    """Alert Engine — high-level interface for Scheduler integration.
    
    This class wraps RuleEngine and AlertStore to provide a simple
    evaluate() interface for the Scheduler.
    """
    
    def __init__(self, alert_store: AlertStore):
        self.alert_store = alert_store
        self.rule_engine = RuleEngine(alert_store)
    
    def evaluate(self, context: AlertEvaluationContext) -> AlertEngineResult:
        """Evaluate alert conditions for a collection result.
        
        Args:
            context: Alert evaluation context containing server_id, snapshot_id,
                    and collection status information.
        
        Returns:
            AlertEngineResult with success status and evaluation details.
        """
        try:
            logger.debug(
                "Evaluating alerts: server=%s snapshot=%s collection_success=%s",
                context.server_id,
                context.snapshot_id,
                context.collection_success,
            )
            
            result = self.rule_engine.evaluate(context)
            
            logger.debug(
                "Alert evaluation complete: server=%s created=%d updated=%d resolved=%d",
                context.server_id,
                result.alerts_created,
                result.alerts_updated,
                result.alerts_resolved,
            )
            
            return AlertEngineResult(
                success=True,
                evaluation_result=result,
            )
            
        except Exception as e:
            logger.exception(
                "Alert evaluation failed: server=%s snapshot=%s error=%s",
                context.server_id,
                context.snapshot_id,
                e,
            )
            return AlertEngineResult(
                success=False,
                error_message=str(e),
            )