"""API Dependencies (Phase 8/10C/22).

Service wiring for InventoryStore, Orchestrator, DashboardQueryService,
SchedulerStore, AlertStore, and the Phase 22 ManagementContext.

Uses FastAPI dependency injection to provide service instances.
"""
from __future__ import annotations

import threading
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

        # Phase 24: Discovery run concurrency guard + factory
        self._discovery_lock = threading.Lock()
        self._discovery_running = False
        # A callable that returns (ProviderAdapter, ProviderNormalizer).
        # Registered by application bootstrap or tests.
        self.discovery_factory: Optional[Callable[[], tuple[Any, Any]]] = None

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

    @property
    def discovery_running(self) -> bool:
        """True if a discovery run is currently in progress."""
        return self._discovery_running

    def run_discovery(self):
        """Execute a discovery run and refresh all dependent context state.

        Read-only exploration: calls PlatformDiscovery.discover() with
        the registered adapter+normalizer, then rebuilds health, graph,
        monitoring, faults, alerts, visibility, operation, and recovery
        services from the fresh DiscoveryResult.

        Concurrency: uses a lock + flag to prevent duplicate runs.

        Returns:
            DiscoveryResult from the real discovery service.
        """
        from ..discovery.service import PlatformDiscovery

        if self.discovery_factory is None:
            raise RuntimeError(
                "No discovery factory registered. "
                "Call ctx.discovery_factory = <callable> first."
            )

        if not self._discovery_lock.acquire(blocking=False):
            raise DiscoveryAlreadyRunningError(
                "A discovery run is already in progress"
            )
        try:
            if self._discovery_running:
                raise DiscoveryAlreadyRunningError(
                    "A discovery run is already in progress"
                )
            self._discovery_running = True

            adapter, normalizer = self.discovery_factory()
            discovery = PlatformDiscovery()
            result = discovery.discover(adapter, normalizer)
            self._refresh_from_discovery(result)
            return result
        finally:
            self._discovery_running = False
            self._discovery_lock.release()

    def _refresh_from_discovery(self, result):
        """Rebuild all dependent services from a DiscoveryResult."""
        self.discovery_result = result

        if result.inventory is None:
            self.health_report = None
            self.graph_query = None
            self.monitoring_service = None
            self.monitoring_report = None
            self.fault_result = None
            self.alert_service = None
            self.visibility = None
            self.operation_service = None
            self.recovery_service = None
            return

        self._build_dependent_services(result)

    def _build_dependent_services(self, result):
        """Build health, graph, monitoring, fault, visibility, ops, recovery."""
        from ..health.service import HealthService
        from ..graph.service import GraphBuilder, GraphQuery
        from ..monitoring.service import MonitoringService
        from ..fault.service import FaultDetectionService
        from ..visibility.service import (
            AlertService, OperationalVisibilityService,
        )
        from ..operations.service import (
            CapabilityResolver, OperationExecutor,
            OperationGraphContext, OperationService, TargetResolver,
        )
        from ..operations.models import OperationType
        from ..recovery.service import RecoveryService
        from ..recovery.models import AuthorizationLevel, SafetyResult

        health_report = HealthService().assess(result)
        self.health_report = health_report

        graph_query = GraphQuery(GraphBuilder().build(result))
        self.graph_query = graph_query

        mon_svc = MonitoringService()
        mon_report = mon_svc.monitor(health_report)
        self.monitoring_service = mon_svc
        self.monitoring_report = mon_report

        fault_result = FaultDetectionService().detect(
            mon_report.observations, mon_report.state_changes)
        self.fault_result = fault_result

        alert_svc = AlertService()
        for fault in fault_result.faults:
            alert_svc.create_alert(fault)
        self.alert_service = alert_svc

        vis = OperationalVisibilityService(alert_service=alert_svc)
        vis.set_inventory(result.inventory)
        vis.set_health_report(health_report)
        vis.set_fault_result(fault_result)
        vis.set_graph_query(graph_query)
        self.visibility = vis

        provider_id = result.provider_id or "unknown"
        target_resolver = TargetResolver()
        for node in result.inventory.nodes:
            target_resolver.register_target(
                canonical_id=node.canonical_id,
                provider_type=result.provider_type,
                provider_id=provider_id, entity_type="Node")
        cap_resolver = CapabilityResolver()
        cap_resolver.register(
            result.provider_type,
            {OperationType.RESTART, OperationType.QUERY_STATUS})

        class _NoOpExecutor(OperationExecutor):
            def preview(self, request, target, capability):
                from ..operations.models import OperationPreview
                return OperationPreview(
                    request=request, resolved_target=target,
                    capability_decision=capability,
                    expected_effect="Query status preview",
                    safety_result=SafetyResult.BLOCKED,
                    execution_allowed=False)
            def execute(self, request, target):
                raise AssertionError("execute() should not be called")
            def verify(self, request, target, execution_result):
                raise AssertionError("verify() should not be called")

        self.operation_service = OperationService(
            target_resolver=target_resolver,
            capability_resolver=cap_resolver,
            executor=_NoOpExecutor(),
            graph_context=OperationGraphContext(graph_query))

        class _MockRecoveryExecutor:
            def preview(self, action):
                from ..recovery.models import RecoveryPreview
                return RecoveryPreview(
                    action=action, expected_effect="Restart preview")
            def execute(self, action):
                raise AssertionError("execute() should not be called")
            def verify(self, action, post_health=None):
                raise AssertionError("verify() should not be called")

        self.recovery_service = RecoveryService(
            executor=_MockRecoveryExecutor(), execution_enabled=False,
            authorization=AuthorizationLevel.READ_ONLY)


class DiscoveryAlreadyRunningError(RuntimeError):
    """Raised when a discovery run is requested while one is in progress."""


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
