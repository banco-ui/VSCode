# Read test file lines 85-175
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Lines 85-175 ===")
for i in range(84, min(175, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')