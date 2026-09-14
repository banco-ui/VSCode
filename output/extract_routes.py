import re, sys

with open(r'd:\Data\AI\VSCode\output\tbms_app.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Extract route paths
routes = set()
for m in re.finditer(r'path:"([^"]+)"', content):
    routes.add(m.group(1))

print("=== ROUTES ===")
for r in sorted(routes):
    print(r)

# Extract API endpoints
api_patterns = re.findall(r'["\']/(api[^"\']*)["\']', content)
api_set = set(api_patterns)
print("\n=== API ENDPOINTS ===")
for a in sorted(api_set):
    print(f"/{a}")

# Extract fetch/axios URLs
fetch_patterns = re.findall(r'(?:fetch|axios\.get|axios\.post|axios\.put|axios\.delete)\s*\(\s*["\`]([^"\`]+)', content)
print("\n=== FETCH/AXIOS CALLS ===")
for f in sorted(set(fetch_patterns)):
    print(f)

# Extract menu/label text patterns
menu_items = re.findall(r'(?:label|title|text):\s*"([^"]{3,50})"', content)
print("\n=== MENU/LABEL TEXTS ===")
for m in sorted(set(menu_items)):
    print(m)

# Extract element component references in routes
elements = re.findall(r'element:\s*\w+\.jsx\([^,]+,\s*(?:\w+\.)?(\w+)', content)
print("\n=== ROUTE ELEMENTS ===")
for e in sorted(set(elements)):
    print(e)
