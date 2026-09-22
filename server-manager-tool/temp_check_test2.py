with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find lines around 90-110
for i in range(88, min(110, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')