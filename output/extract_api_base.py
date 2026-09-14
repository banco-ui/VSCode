import re

with open(r'd:\Data\AI\VSCode\output\tbms_mock_app.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find context around fetch/axios calls - look for API base URL construction
api_base_patterns = re.findall(r'.{0,100}(?:fetch|axios|\.get\(|\.post\(|apiBase|baseURL|API_BASE|REACT_APP).{0,100}', content)
print("=== API BASE URL CONTEXT ===")
for p in api_base_patterns[:30]:
    print(p)
    print("---")

# Find all strings containing 'api' or 'svc'
svc_patterns = re.findall(r'["\'`]([^"\'`]*(?:_svc|api|/v1|/v2)[^"\'`]*)["\'`]', content)
print("\n=== SVC/API STRINGS ===")
for s in sorted(set(svc_patterns)):
    print(s)

# Find context around /servers path usage
server_ctx = []
for m in re.finditer(r'.{0,80}/servers.{0,80}', content):
    s = m.group()
    if 'fetch' in s or 'get' in s or 'post' in s or 'url' in s or 'api' in s:
        server_ctx.append(s)
print("\n=== /servers API CONTEXT ===")
for s in server_ctx[:15]:
    print(s)
    print("---")

# Find context around /switch path usage
switch_ctx = []
for m in re.finditer(r'.{0,80}/switch(?:es|/).{0,80}', content):
    s = m.group()
    if 'fetch' in s or 'get' in s or 'post' in s or 'url' in s or 'api' in s or 'backup' in s or 'config' in s:
        switch_ctx.append(s)
print("\n=== /switch API CONTEXT ===")
for s in switch_ctx[:15]:
    print(s)
    print("---")
