# Check current test file content
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find lines around 110-120
for i in range(105, min(130, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')