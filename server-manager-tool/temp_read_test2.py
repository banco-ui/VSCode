# Read test lines 280-320
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Lines 280-320 ===")
for i in range(279, min(320, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')