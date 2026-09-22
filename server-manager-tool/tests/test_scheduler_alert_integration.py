"""Scheduler-Alert Integration Tests — Phase 11D-2.

Tests for post-collection alert evaluation integration.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from server_manager.scheduler.models import ScheduleDefinition, ScheduleExecution, ScheduleStatus
from server_manager.scheduler.store import SchedulerStore
from server_manager.scheduler.scheduler import Scheduler, SchedulerConfig
from server_manager.orchestrator.orchestrator import Orchestrator
from server_manager.orchestrator.models import OrchestrationResult, OrchestrationStatus
from server_manager.store.store import InventoryStore
from server_manager.store.models import ServerRegistryEntry
from server_manager.models.enums import ServerLifecycle, Vendor
from server_manager.alert import AlertStore, AlertEngine, AlertEvaluationContext
from server_manager.alert.rule_engine import AlertEvaluationResult


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def scheduler_store():
    """Create an in-memory SchedulerStore for tests."""
    s = SchedulerStore(":memory:")
    yield s
    s.close()


@pytest.fixture
def inventory_store():
    """Create an in-memory InventoryStore for tests."""
    import json
    inv = InventoryStore(":memory:")
    entry = ServerRegistryEntry(
        server_id="server-001",
        display_name="Test Server",
        hardware_identity=json.dumps({}),
        vendor=Vendor.Unknown,
        model="Test Model",
    )
    inv.register_server(entry)
    yield inv
    inv.close()


@pytest.fixture
def alert_store():
    """Create an in-memory AlertStore for tests."""
    a = AlertStore(":memory:")
    yield a
    a.close()


@pytest.fixture
def mock_orchestrator():
    """Create a mock Orchestrator."""
    orch = Mock(spec=Orchestrator)
    return orch


@pytest.fixture
def schedule(scheduler_store):
    """Create a test schedule."""
    schedule = ScheduleDefinition(
        schedule_id="test-schedule",
        name="Test Schedule",
        server_ids=["server-001"],
        enabled=True,
        interval_seconds=3600,
    )
    scheduler_store.save_schedule(schedule)
    return schedule


@pytest.fixture
def execution(scheduler_store, schedule):
    """Create a test execution."""
    execution = scheduler_store.claim_execution(schedule, "server-001")
    return execution

# ── Basic Integration Tests ─────────────────────────────────────────────

class TestBasicIntegration:
    """Test basic Scheduler-Alert integration."""
    
    def test_alert_engine_called_after_collection(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that AlertEngine.evaluate() is called after collection."""
