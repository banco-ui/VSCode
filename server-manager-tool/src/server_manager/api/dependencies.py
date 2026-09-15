"""API Dependencies (Phase 8).

Service wiring for InventoryStore, Orchestrator, and DashboardQueryService.
Uses FastAPI dependency injection to provide service instances.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Depends

from ..store.store import InventoryStore
from ..dashboard.query_service import DashboardQueryService
from ..orchestrator.orchestrator import Orchestrator


# ── Service singletons ───────────────────────────────────────────────

_store: Optional[InventoryStore] = None
_dashboard: Optional[DashboardQueryService] = None

# Orchestrator factory: callers register collectors/normalizers
_orchestrator_factory: Optional[Callable[[], Orchestrator]] = None


def configure(
    store: InventoryStore,
    orchestrator_factory: Optional[Callable[[], Orchestrator]] = None,
) -> None:
    """Configure service dependencies.

    Args:
        store: InventoryStore instance.
        orchestrator_factory: Callable that returns a configured Orchestrator.
    """
    global _store, _dashboard, _orchestrator_factory
    _store = store
    _dashboard = DashboardQueryService(store)
    _orchestrator_factory = orchestrator_factory


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


def is_configured() -> bool:
    """Check if dependencies are configured."""
    return _store is not None and _dashboard is not None
