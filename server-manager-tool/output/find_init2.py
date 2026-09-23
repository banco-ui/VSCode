import re

with open('src/server_manager/alert/store.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find __init__ method
print("=== __init__ method (lines 141-165) ===")
for i, line in enumerate(lines[140:165], start=141):
    print(f"{i}: {line}", end='')

print("\n\n=== init() method ===")
for i, line in enumerate(lines[165:175], start=166):
    print(f"{i}: {line}", end='')
