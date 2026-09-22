# Fix test_alert_engine_exception_results_in_partial
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_test4 = '''    def test_alert_engine_exception_results_in_partial(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that AlertEngine exception results in PARTIAL status."""
        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.canonical_inventory = ServerInventory()
        mock_result.verification = VerificationResult()
        mock_orchestrator.run.return_value = mock_result
        
        with patch.object(AlertEngine, 'evaluate') as mock_evaluate:
            mock_evaluate.side_effect = Exception("Alert engine failed")
            
            scheduler = Scheduler(
                config=SchedulerConfig(db_path=":memory:", enabled=False),
                orchestrator_factory=lambda: mock_orchestrator,
                store_factory=lambda: inventory_store,
                alert_store_factory=lambda: alert_store,
            )
            scheduler._store = scheduler_store
            scheduler_store.save_schedule(schedule)
            
            scheduler._execute_collection(schedule, "server-001", execution)'''

new_test4 = '''    def test_alert_engine_exception_results_in_partial(
        self, scheduler_store, inventory_store, alert_store,
        mock_orchestrator, schedule, execution
    ):
        """Test that AlertEngine exception results in PARTIAL status."""
        mock_inventory = Mock()
        mock_inventory.health_status = "OK"
        mock_verification = Mock()
        mock_verification.has_discrepancy = False
        
        mock_result = OrchestrationResult.model_construct(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=mock_inventory,
            canonical_source="ssh",
            verification=mock_verification,
        )
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.total_duration_ms = 1000
        mock_orchestrator.run.return_value = mock_result
        
        with patch.object(inventory_store, 'save_orchestration_result'):
            with patch.object(AlertEngine, 'evaluate') as mock_evaluate:
                mock_evaluate.side_effect = Exception("Alert engine failed")
                
                scheduler = Scheduler(
                    config=SchedulerConfig(db_path=":memory:", enabled=False),
                    orchestrator_factory=lambda: mock_orchestrator,
                    store_factory=lambda: inventory_store,
                    alert_store_factory=lambda: alert_store,
                )
                scheduler._store = scheduler_store
                scheduler_store.save_schedule(schedule)
                
                scheduler._execute_collection(schedule, "server-001", execution)'''

content = content.replace(old_test4, new_test4)

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 15b applied: test_alert_engine_exception_results_in_partial")