import sys

# Read the test file
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: Remove create_execution calls (execution is already created by fixture)
content = content.replace('            scheduler_store.create_execution(execution)\n', '')
content = content.replace('        scheduler_store.create_execution(execution)\n', '')

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed all create_execution() calls")