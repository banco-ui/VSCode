with open('src/server_manager/alert/store.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== begin_transaction ===")
for i, line in enumerate(lines[168:190], start=169):
    print(f"{i}: {line}", end='')

print("\n\n=== _commit_if_standalone ===")
for i, line in enumerate(lines[190:210], start=191):
    print(f"{i}: {line}", end='')

print("\n\n=== _in_transaction initialization ===")
for i, line in enumerate(lines[115:145], start=116):
    print(f"{i}: {line}", end='')
