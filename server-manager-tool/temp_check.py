with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(35, min(50, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')