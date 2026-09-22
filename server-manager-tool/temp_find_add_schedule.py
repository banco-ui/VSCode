# Find all add_schedule occurrences
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== add_schedule occurrences ===")
for i, line in enumerate(lines):
    if 'add_schedule' in line:
        print(f"{i+1:3d}: {line.rstrip()}")