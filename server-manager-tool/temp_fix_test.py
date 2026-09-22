import sys

# Read the test file
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace all add_schedule with save_schedule
content = content.replace('scheduler_store.add_schedule(', 'scheduler_store.save_schedule(')

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all add_schedule() → save_schedule()")