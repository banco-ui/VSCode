with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Lines 1-60 ===")
for i in range(min(60, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')