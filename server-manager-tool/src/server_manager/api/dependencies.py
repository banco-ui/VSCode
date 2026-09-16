"""API Dependencies (Phase 8/10C).

Service wiring for InventoryStore, Orchestrator, DashboardQueryService, and SchedulerStore.
Uses FastAPI dependency injection to provide service instances.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Depends

from ..store.store import InventoryStore
from ..dashboard.query_service import DashboardQueryService
from ..orchestrator.orchestrator import Orchestrator
from ..scheduler.store import SchedulerStore


# ── Service singletons ───────────────────────────────────────────────

_store: Optional[InventoryStore] = None
_dashboard: Optional[DashboardQueryService] = None
_scheduler_store: Optional[SchedulerStore] = None

# Orchestrator factory: callers register collectors/normalizers
_orchestrator_factory: Optional[Callable[[], Orchestrator]] = None


def configure(
    store: InventoryStore,
    orchestrator_factory: Optional[Callable[[], Orchestrator]] = None,
    scheduler_store: Optional[SchedulerStore] = None,
) -> None:
    """Configure service dependencies.

    Args:
        store: InventoryStore instance.
        orchestrator_factory: Callable that returns a configured Orchestrator.
        scheduler_store: SchedulerStore instance (optional, created lazily if not provided).
    """
    global _store, _dashboard, _orchestrator_factory, _scheduler_store
    _store = store
    _dashboard = DashboardQueryService(store)
    _orchestrator_factory = orchestrator_factory
    _scheduler_store = scheduler_store


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
    
    Creates a fresh instance per request for thread safety in tests.
    This mirrors the pattern used for InventoryStore in Phase 8.5.
    """
    # Create a new instance per request to avoid thread safety issues
    # Each request gets its own connection, avoiding cross-thread SQLite usage
    return SchedulerStore(":memory:")


def is_configured() -> bool:
    """Check if dependencies are configured."""
    return _store is not None and _dashboard is not None
