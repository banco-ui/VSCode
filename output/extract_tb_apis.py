import re

with open(r'd:\Data\AI\VSCode\output\tbms_app.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all URL-like strings containing tb or testbed
patterns = re.findall(r'["\'`](/[a-z][^"\'`\s,)]*)', content)
tb_urls = set()
for p in patterns:
    if 'tb' in p.lower() or 'testbed' in p.lower() or 'server' in p.lower() or 'switch' in p.lower() or 'topology' in p.lower() or 'rack' in p.lower() or 'port' in p.lower() or 'config' in p.lower() or 'backup' in p.lower() or 'restore' in p.lower() or 'recovery' in p.lower() or 'monitor' in p.lower() or 'alert' in p.lower():
        tb_urls.add(p)

print("=== TB/SERVER/SWITCH/TOPOLOGY URLS ===")
for u in sorted(tb_urls):
    print(u)

# Also find all unique API-like paths
all_paths = re.findall(r'["\'`](/api/[^"\'`\s,)]*)', content)
print("\n=== ALL /api/ PATHS ===")
for p in sorted(set(all_paths)):
    print(p)

# Find tb-management specific patterns
tb_mgmt = re.findall(r'tb-management[^"\'}\s]*', content)
print("\n=== tb-management patterns ===")
for t in sorted(set(tb_mgmt)):
    print(t)

# Find any references to switch/server/topology/rack/port in variable or component names
keywords = re.findall(r'["\'`](switch|server|topology|rack|port|config|backup|restore|golden|drift|recovery|cnf|caas|k8s|namespace|alert|monitor|health|power|reboot|shutdown)["\'`]', content, re.IGNORECASE)
print("\n=== KEYWORD FREQUENCY ===")
from collections import Counter
for kw, cnt in Counter(keywords).most_common(50):
    print(f"  {kw}: {cnt}")
