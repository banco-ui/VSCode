import re

# Read alert module files
files = [
    'src/server_manager/alert/rule_engine.py',
    'src/server_manager/alert/store.py',
    'src/server_manager/alert/models.py',
]

for filepath in files:
    print(f"\n=== {filepath} ===")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find classes and evaluate methods
    for i, line in enumerate(lines):
        if re.search(r'class|def evaluate', line):
            print(f"{i+1:3d}: {line}", end='')