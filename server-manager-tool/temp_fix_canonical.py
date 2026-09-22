import sys

# Read and fix the test file
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: Add canonical_source to all mock_result objects that are missing it
# Fix test_correct_snapshot_id_passed
old1 = '''        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.verification = Mock()'''
new1 = '''        mock_result.canonical_inventory = Mock()
        mock_result.canonical_inventory.health_status = "OK"
        mock_result.canonical_source = "ssh"
        mock_result.started_at = datetime.now(timezone.utc).isoformat()
        mock_result.completed_at = datetime.now(timezone.utc).isoformat()
        mock_result.verification = Mock()'''
content = content.replace(old1, new1)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added canonical_source to remaining tests")