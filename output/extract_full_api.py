import re

with open(r'd:\Data\AI\VSCode\output\tbms_mock_app.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find the Ue function definition to understand API base
ue_ctx = re.findall(r'.{0,200}function Ue.{0,200}', content)
print("=== Ue FUNCTION ===")
for u in ue_ctx[:5]:
    print(u)
    print("---")

# Find the API object definition (We = ...)
we_patterns = re.findall(r'(\w+):[^,]*=>Ue\(["\'`]([^"\'`]+)', content)
print("\n=== API METHOD DEFINITIONS ===")
api_methods = {}
for name, path in we_patterns:
    api_methods[name] = path
    print(f"  {name}: {path}")

# Find all Ue() calls with their paths
all_ue = re.findall(r'Ue\(["\'`]([^"\'`]+)["\'`](?:,\s*\{([^}]+)\})?', content)
print("\n=== ALL API CALLS ===")
for path, opts in sorted(set(all_ue)):
    if opts:
        print(f"  {path}  [{opts[:80]}]")
    else:
        print(f"  {path}")

# Find the API base URL - look for something like baseURL or _svc
base_ctx = re.findall(r'.{0,100}(?:baseURL|_svc|tb-management|API_BASE|apiBase|/api["\']).{0,100}', content)
print("\n=== BASE URL CONTEXT ===")
for b in base_ctx[:15]:
    print(b)
    print("---")
