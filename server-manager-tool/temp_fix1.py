import re

# Read the test file
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix 1: ServerInventory - replace lines 89-101 with Mock
in_first_test = False
new_lines = []
skip_lines = False
skip_count = 0

for i, line in enumerate(lines):
    # Detect the ServerInventory block in first test
    if 'def test_alert_engine_called_after_collection' in line:
        in_first_test = True
        new_lines.append(line)
        continue
    
    if in_first_test and 'from server_manager.store.models import ServerInventory' in line:
        # Skip this line and the next 12 lines (ServerInventory creation)
        skip_lines = True
        skip_count = 13
        # Add the Mock replacement
        new_lines.append('        mock_inventory = Mock()\n')
        new_lines.append('        mock_inventory.health_status = "OK"\n')
        continue
    
    if skip_lines:
        skip_count -= 1
        if skip_count <= 0:
            skip_lines = False
        continue
    
    new_lines.append(line)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix 1 applied: ServerInventory -> Mock")