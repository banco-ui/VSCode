import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('src/server_manager/alert/rule_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== RuleEngine.evaluate() method (lines 55-92) ===")
for i, line in enumerate(lines[54:92], start=55):
    print(f"{i}: {line}", end='')

print("\n\n=== _is_snapshot_evaluated (lines 95-115) ===")
for i, line in enumerate(lines[94:115], start=95):
    print(f"{i}: {line}", end='')

print("\n\n=== _handle_failure fingerprint check (lines 180-210) ===")
for i, line in enumerate(lines[179:210], start=180):
    print(f"{i}: {line}", end='')
