with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing attributes to all mock_result objects
content = content.replace(
    '''        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result''',
    '''        mock_result.verification.has_discrepancy = False
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.canonical_source = "ssh"
        mock_result.source_results = []
        mock_result.total_duration_ms = 1000
        mock_result.errors = []
        mock_result.warnings = []
        mock_orchestrator.run.return_value = mock_result'''
)

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added missing attributes")