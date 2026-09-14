import re

with open(r'd:\Data\AI\VSCode\output\tbms_mock_app.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Extract all API paths
api_paths = re.findall(r'["\'`](/api/[^"\'`\s,)]+)["\'`]', content)
print("=== API PATHS in Mock App ===")
for p in sorted(set(api_paths)):
    print(p)

# Extract all URL-like strings
urls = re.findall(r'["\'`](/[^"\'`\s,)]{3,})["\'`]', content)
print("\n=== ALL PATHS in Mock App ===")
for u in sorted(set(urls)):
    print(u)

# Extract menu/label texts
labels = re.findall(r'(?:label|title|text|primary|secondary):\s*"([^"]{2,60})"', content)
print("\n=== LABELS/MENU TEXTS ===")
for l in sorted(set(labels)):
    print(l)

# Extract mock data field names
fields = re.findall(r'"(\w+)":', content)
from collections import Counter
print("\n=== TOP FIELD NAMES (frequency) ===")
for f, c in Counter(fields).most_common(60):
    print(f"  {f}: {c}")

# Extract route paths
routes = re.findall(r'path:"([^"]+)"', content)
print("\n=== ROUTES ===")
for r in sorted(set(routes)):
    print(r)
