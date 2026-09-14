import re

with open(r'd:\Data\AI\VSCode\output\tbms_app.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all string literals that look like API paths with tb
tb_api = re.findall(r'["\'`](/api/tb[^"\'`\s,)]*)["\'`]', content)
print("=== /api/tb PATHS ===")
for p in sorted(set(tb_api)):
    print(p)

# Find all fetch/axios calls with template literals
fetch_calls = re.findall(r'(?:fetch|axios\.\w+|Tb\w+\.get|Tb\w+\.post)\s*\(\s*["\'`]([^"\'`]+)', content)
print("\n=== FETCH/AXIOS CALLS ===")
for f in sorted(set(fetch_calls)):
    print(f)

# Find all string patterns containing /tb-management/ or tb-be
tb_mgmt_refs = re.findall(r'["\'`]([^"\'`]*(?:tb-management|tb-be|/tb/)[^"\'`]*)["\'`]', content)
print("\n=== TB-MANAGEMENT/tb-be REFERENCES ===")
for t in sorted(set(tb_mgmt_refs)):
    print(t)

# Find all unique path-like strings starting with /
all_slash = re.findall(r'["\'`](/[a-z][a-z0-9/_-]+)["\'`]', content)
# Filter for interesting ones
interesting = [p for p in set(all_slash) if any(kw in p.lower() for kw in ['server', 'switch', 'topolog', 'rack', 'port', 'config', 'backup', 'restore', 'install', 'sdn', 'alert', 'monitor', 'health', 'power', 'reboot', 'golden', 'drift', 'diff', 'recovery', 'cnf', 'caas', 'k8s', 'namespace', 'physical'])]
print("\n=== INTERESTING PATHS ===")
for p in sorted(interesting):
    print(p)

# Find context around "switch" keyword
switch_ctx = []
for m in re.finditer(r'.{0,80}switch.{0,80}', content, re.IGNORECASE):
    s = m.group()
    if 'switch' in s.lower() and ('fetch' in s or '/api' in s or 'url' in s or 'path' in s or 'route' in s):
        switch_ctx.append(s)
print("\n=== SWITCH CONTEXT ===")
for s in switch_ctx[:20]:
    print(s)

# Find context around "topology"
topo_ctx = []
for m in re.finditer(r'.{0,80}topolog.{0,80}', content, re.IGNORECASE):
    s = m.group()
    topo_ctx.append(s)
print("\n=== TOPOLOGY CONTEXT ===")
for s in topo_ctx[:20]:
    print(s)

# Find context around "install"
install_ctx = []
for m in re.finditer(r'.{0,60}install.{0,60}', content, re.IGNORECASE):
    s = m.group()
    if '/api' in s or 'fetch' in s or 'url' in s or 'path' in s:
        install_ctx.append(s)
print("\n=== INSTALL CONTEXT ===")
for s in install_ctx[:20]:
    print(s)
