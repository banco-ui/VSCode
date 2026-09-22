import sys

# Read and fix the test file
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: Add source_results to mock_result objects
old1 = '''        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_orchestrator.run.return_value = mock_result'''
new1 = '''        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False
        mock_result.source_results = []
        mock_orchestrator.run.return_value = mock_result'''
content = content.replace(old1, new1)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added source_results to tests")