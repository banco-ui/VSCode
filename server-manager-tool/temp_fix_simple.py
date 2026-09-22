import sys

# Read and fix the test file completely
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the problematic test_alert_engine_called_after_collection function
# Replace the ServerInventory creation with a simpler Mock that has health_status

in_first_test = False
new_lines = []
skip_until_mock_result = False

for i, line in enumerate(lines):
    # Fix test_alert_engine_called_after_collection
    if 'def test_alert_engine_called_after_collection' in line:
        in_first_test = True
        new_lines.append(line)
        continue
    
    if in_first_test and 'from server_manager.models.inventory import ServerInventory' in line:
        # Skip all the import lines until mock_inventory
        skip_until_mock_result = True
        continue
    
    if skip_until_mock_result and 'mock_inventory = Mock()' in line:
        # Replace with simple mock
        new_lines.append('        mock_inventory = Mock()\n')
        new_lines.append('        mock_inventory.health_status = "OK"\n')
        skip_until_mock_result = False
        in_first_test = False
        continue
    
    if skip_until_mock_result:
        continue
    
    # Fix test_correct_snapshot_id_passed - add canonical_source
    if 'mock_result.canonical_inventory = Mock()' in line and i > 150 and i < 180:
        new_lines.append(line)
        new_lines.append('        mock_result.canonical_inventory.health_status = "OK"\n')
        new_lines.append('        mock_result.canonical_source = "ssh"\n')
        new_lines.append('        mock_result.source_results = []\n')
        # Skip the next few lines that we just replaced
        continue
    
    if 'mock_result.canonical_inventory.health_status = "OK"' in line and i > 150 and i < 180:
        continue
    if 'mock_result.canonical_source = "ssh"' in line and i > 150 and i < 180:
        continue
    if 'mock_result.source_results = []' in line and i > 150 and i < 180:
        continue
    
    new_lines.append(line)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed tests with simpler approach")