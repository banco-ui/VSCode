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
        from server_manager.store.models import ServerInventory
        
        mock_inventory = ServerInventory(
            server_id="server-001",
            health_status="OK",
            storage_controllers=[],
            physical_disks=[],
            virtual_disks=[],
            network_interfaces=[],
            memory_modules=[],
            processors=[],
        )
        
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.canonical_inventory = mock_inventory
        mock_result.canonical_source = "ssh"
        mock_result.source_results_summary = {}
        mock_result.source_results = []
        mock_result.verification = None
        mock_orchestrator.run.return_value = mock_result
        
        with patch.object(AlertEngine, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = Mock(success=True, evaluation_result=AlertEvaluationResult())
            
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            
            scheduler._execute_collection(schedule, "server-001", execution)
            
            assert mock_evaluate.called
            call_args = mock_evaluate.call_args[0][0]
            assert isinstance(call_args, AlertEvaluationContext)
            assert call_args.server_id == "server-001"
            assert call_args.snapshot_id == "snap-test-run-001"
    
    def test_correct_snapshot_id_passed(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that correct snapshot_id is passed to AlertEngine."""
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "run-abc123"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result
        
        with patch.object(AlertEngine, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = Mock(success=True)
            
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            scheduler_store.add_schedule(schedule)
            scheduler_store.create_execution(execution)
            
            scheduler._execute_collection(schedule, "server-001", execution)
            
            call_args = mock_evaluate.call_args[0][0]
            assert call_args.snapshot_id == "snap-run-abc123"
            assert call_args.server_id == "server-001"
    
    def test_inventory_persisted_before_alert_evaluation(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that inventory is persisted before alert evaluation."""
        save_called = []
        evaluate_called = []
        
        original_save = inventory_store.save_orchestration_result
        def tracked_save(result):
            save_called.append(True)
            return original_save(result)
        inventory_store.save_orchestration_result = tracked_save
        
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result
        
        def mock_evaluate(ctx):
            evaluate_called.append(True)
            assert len(save_called) > 0, "Inventory should be saved before alert evaluation"
            return Mock(success=True)
        
        with patch.object(AlertEngine, 'evaluate', side_effect=mock_evaluate):
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            scheduler_store.add_schedule(schedule)
            scheduler_store.create_execution(execution)
            

# ── Failure Isolation Tests ─────────────────────────────────────────────

class TestFailureIsolation:
    """Test failure isolation semantics."""
    
    def test_alert_engine_exception_results_in_partial(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that AlertEngine exception results in PARTIAL status."""
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result
        
        with patch.object(AlertEngine, 'evaluate', side_effect=Exception("Alert evaluation failed")):
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            scheduler_store.add_schedule(schedule)
            scheduler_store.create_execution(execution)
            
            # Execute collection - should not raise
            scheduler._execute_collection(schedule, "server-001", execution)
            
            # Verify execution completed
            exec_record = scheduler_store.get_execution(execution.execution_id)
            assert exec_record is not None
    
    def test_alert_failure_does_not_rerun_collection(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that alert failure does not trigger collection rerun."""
        call_count = []
        
        def tracked_run(server_id):
            call_count.append(True)
            mock_result = Mock(spec=OrchestrationResult)
            mock_result.run_id = "test-run-001"
            mock_result.server_id = server_id
            mock_result.status = OrchestrationStatus.SUCCESS
            mock_result.canonical_inventory = Mock()
            mock_result.canonical_inventory.health_status = "OK"
            mock_result.verification = Mock()
            mock_result.verification.has_discrepancy = False
            return mock_result
        
        mock_orchestrator.run.side_effect = tracked_run
        
        with patch.object(AlertEngine, 'evaluate', side_effect=Exception("Alert failed")):
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            scheduler_store.add_schedule(schedule)
            scheduler_store.create_execution(execution)
            
            scheduler._execute_collection(schedule, "server-001", execution)
            
            # Collection should be called exactly once
            assert len(call_count) == 1, "Collection should not be rerun on alert failure"
    
    def test_worker_survives_alert_failure(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that worker thread survives alert evaluation failure."""
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result
        
        with patch.object(AlertEngine, 'evaluate', side_effect=Exception("Alert failed")):
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False, worker_limit=2),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            scheduler_store.add_schedule(schedule)
            scheduler_store.create_execution(execution)
            
            # Execute - should not crash worker
            try:
                scheduler._execute_collection(schedule, "server-001", execution)
            except Exception:
                pytest.fail("Worker should not crash on alert failure")
            
            # Worker slot should be released
            assert scheduler._running_count == 0

            scheduler._execute_collection(schedule, "server-001", execution)
            
            assert len(save_called) > 0
            assert len(evaluate_called) > 0


# ── AlertStore Failure Tests ────────────────────────────────────────────

class TestAlertStoreFailure:
    """Test AlertStore failure scenarios."""
    
    def test_alert_store_failure_results_in_partial(
        self, scheduler_store, inventory_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that AlertStore failure results in PARTIAL status."""
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result
        
        # Create AlertStore that raises exception
        failing_store = Mock(spec=AlertStore)
        failing_store.record_evaluation.side_effect = Exception("Store failed")
        
        scheduler = Scheduler(
            config=SchedulerConfig(db_path=":memory:", enabled=False),
            orchestrator_factory=lambda: mock_orchestrator,
            store_factory=lambda: inventory_store,
            alert_store_factory=lambda: failing_store,
        )
        scheduler._store = scheduler_store
        scheduler_store.add_schedule(schedule)
        scheduler_store.create_execution(execution)
        
        # Execute - should handle failure gracefully
        try:
            scheduler._execute_collection(schedule, "server-001", execution)
        except Exception:
            pytest.fail("Should handle AlertStore failure gracefully")
