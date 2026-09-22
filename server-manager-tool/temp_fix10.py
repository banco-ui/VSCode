# Replace Mock with real OrchestrationResult
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Mock with real OrchestrationResult
old_mock = '''        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.canonical_source = "ssh"
        mock_result.source_results = []
        mock_result.total_duration_ms = 1000
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.canonical_inventory = ServerInventory()
        mock_result.verification = VerificationResult()'''

new_result = '''        mock_result = OrchestrationResult(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=ServerInventory(),
            canonical_source="ssh",
            verification=VerificationResult(),
        )
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.total_duration_ms = 1000'''

content = content.replace(old_mock, new_result)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 10 applied: Real OrchestrationResult")