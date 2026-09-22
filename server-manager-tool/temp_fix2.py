# Fix add_schedule -> save_schedule
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('scheduler_store.add_schedule(', 'scheduler_store.save_schedule(')

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 2 applied: add_schedule -> save_schedule")