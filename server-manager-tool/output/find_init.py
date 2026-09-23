import re

with open('src/server_manager/alert/store.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find _in_transaction assignments
matches = re.findall(r'self\._in_transaction\s*=\s*(True|False|None)', content)
print("self._in_transaction assignments found:", matches)

# Find __init__ method
init_match = re.search(r'def __init__\(self.*?\n(.*?)(?=\n    def |\n\nclass |\Z)', content, re.DOTALL)
if init_match:
    print("\n=== __init__ method ===")
    print(init_match.group(1)[:800])

# Find init method
init_method = re.search(r'def init\(self\).*?:\n(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
if init_method:
    print("\n=== init() method ===")
    print(init_method.group(1)[:500])
