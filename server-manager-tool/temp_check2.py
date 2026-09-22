# Read test_scheduler.py
with open('tests/test_scheduler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Print first 60 lines
print("=== test_scheduler.py (first 60 lines) ===")
for i in range(min(60, len(lines))):
    print(f"{i+1:3d}: {lines[i]}", end='')