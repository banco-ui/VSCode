# Add missing total_duration_ms attribute
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add total_duration_ms to mock_result
old_attrs = '''        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.canonical_source = "ssh"
        mock_result.source_results = []'''

new_attrs = '''        mock_result = Mock(spec=OrchestrationResult)
        mock_result.run_id = "test-run-001"
        mock_result.server_id = "server-001"
        mock_result.status = OrchestrationStatus.SUCCESS
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.canonical_source = "ssh"
        mock_result.source_results = []
        mock_result.total_duration_ms = 1000
        mock_result.errors = []
        mock_result.warnings = []'''

content = content.replace(old_attrs, new_attrs)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 9 applied: Added total_duration_ms")