"""API Dependencies (Phase 8/10C/22).

Service wiring for InventoryStore, Orchestrator, DashboardQueryService,
SchedulerStore, AlertStore, and the Phase 22 ManagementContext.

Uses FastAPI dependency injection to provide service instances.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Depends

from ..store.store import InventoryStore
from ..dashboard.query_service import DashboardQueryService
from ..orchestrator.orchestrator import Orchestrator
from ..scheduler.store import SchedulerStore
from ..alert.store import AlertStore


# ── Service singletons ───────────────────────────────────────────────

_store: Optional[InventoryStore] = None
_dashboard: Optional[DashboardQueryService] = None
_scheduler_store: Optional[SchedulerStore] = None
_alert_store: Optional[AlertStore] = None

# Orchestrator factory: callers register collectors/normalizers
_orchestrator_factory: Optional[Callable[[], Orchestrator]] = None


# ── Phase 22: Management Context ──────────────────────────────────────

class ManagementContext:
    """Holds pipeline service instances for the Phase 22 Management API.

    All services are read-only / preview-only:
        - No provider API calls
        - No shell commands or external process calls
        - No recovery executor invocation
        - No operation service invocation
        - No graph / health / fault mutation

    The context is populated after a discovery pipeline run and exposes
    the resulting service objects to the Management API endpoints.
    """

    def __init__(self) -> None:
        from ..discovery.models import DiscoveryResult
        from ..health.models import HealthReport
        from ..graph.service import GraphQuery
        from ..monitoring.service import MonitoringService
        from ..monitoring.models import MonitoringReport
        from ..fault.models import FaultResult
        from ..visibility.service import AlertService, OperationalVisibilityService
        from ..operations.service import OperationService
        from ..recovery.service import RecoveryService

        self.discovery_result: Optional[DiscoveryResult] = None
        self.health_report: Optional[HealthReport] = None
        self.graph_query: Optional[GraphQuery] = None
        self.monitoring_service: Optional[MonitoringService] = None
        self.monitoring_report: Optional[MonitoringReport] = None
        self.fault_result: Optional[FaultResult] = None
        self.alert_service: Optional[AlertService] = None
        self.visibility: Optional[OperationalVisibilityService] = None
        self.operation_service: Optional[OperationService] = None
        self.recovery_service: Optional[RecoveryService] = None

    @property
    def inventory(self):
        """Shortcut to the CanonicalInventory from the discovery result."""
        if self.discovery_result is not None:
            return self.discovery_result.inventory
        return None

    @property
    def is_configured(self) -> bool:
        """True if at least the discovery result is available."""
        return self.discovery_result is not None


_management_context: Optional[ManagementContext] = None


def get_management_context() -> ManagementContext:
    """Get the ManagementContext singleton.

    Returns a shared ManagementContext instance.
    For tests, use app.dependency_overrides to inject a test-specific instance.
    """
    global _management_context
    if _management_context is None:
        _management_context = ManagementContext()
    return _management_context


def configure_management(context: ManagementContext) -> None:
    """Set the ManagementContext instance (for programmatic configuration)."""
    global _management_context
    _management_context = context


def configure(
    store: InventoryStore,
    orchestrator_factory: Optional[Callable[[], Orchestrator]] = None,
    scheduler_store: Optional[SchedulerStore] = None,
    alert_store: Optional[AlertStore] = None,
) -> None:
    """Configure service dependencies.

    Args:
        store: InventoryStore instance.
        orchestrator_factory: Callable that returns a configured Orchestrator.
        scheduler_store: SchedulerStore instance (optional, created lazily if not provided).
        alert_store: AlertStore instance (optional, created lazily if not provided).
    """
    global _store, _dashboard, _orchestrator_factory, _scheduler_store, _alert_store
    _store = store
    _dashboard = DashboardQueryService(store)
    _orchestrator_factory = orchestrator_factory
    _scheduler_store = scheduler_store
    _alert_store = alert_store


def get_store() -> InventoryStore:
    """Get the InventoryStore instance."""
    if _store is None:
        raise RuntimeError("InventoryStore not configured. Call configure() first.")
    return _store


def get_dashboard_query_service() -> DashboardQueryService:
    """Get the DashboardQueryService instance."""
    if _dashboard is None:
        raise RuntimeError("DashboardQueryService not configured. Call configure() first.")
    return _dashboard


def get_orchestrator() -> Orchestrator:
    """Get an Orchestrator instance."""
    if _orchestrator_factory is None:
        raise RuntimeError("Orchestrator factory not configured. Call configure() first.")
    return _orchestrator_factory()


def get_scheduler_store() -> SchedulerStore:
    """Get the SchedulerStore instance.
    
    Returns a shared persistent SchedulerStore instance.
    Uses singleton pattern to ensure all API requests share the same database.
    
    For tests, use app.dependency_overrides to inject a test-specific instance.
    """
    global _scheduler_store
    if _scheduler_store is None:
        # Use a persistent database file for production
        # Tests should override this via dependency_overrides
        import os
        from pathlib import Path
        
        # Get DB path from environment or use default
        db_path = os.environ.get("SCHEDULER_DB_PATH", None)
        if db_path is None:
            # Default to application data directory
            app_data = Path.home() / ".server-manager"
            app_data.mkdir(parents=True, exist_ok=True)
            db_path = str(app_data / "scheduler.db")
        
        _scheduler_store = SchedulerStore(db_path)
    
    return _scheduler_store


def get_alert_store() -> AlertStore:
    """Get the AlertStore instance.
    
    Returns a shared persistent AlertStore instance.
    Uses singleton pattern to ensure all API requests share the same database.
    
    For tests, use app.dependency_overrides to inject a test-specific instance.
    """
    global _alert_store
    if _alert_store is None:
        # Use a persistent database file for production
        # Tests should override this via dependency_overrides
        import os
        from pathlib import Path
        
        # Get DB path from environment or use default
        db_path = os.environ.get("ALERT_DB_PATH", None)
        if db_path is None:
            # Default to application data directory
            app_data = Path.home() / ".server-manager"
            app_data.mkdir(parents=True, exist_ok=True)
            db_path = str(app_data / "alerts.db")
        
        _alert_store = AlertStore(db_path)
    
    return _alert_store


def is_configured() -> bool:
    """Check if dependencies are configured."""
    return _store is not None and _dashboard is not None
