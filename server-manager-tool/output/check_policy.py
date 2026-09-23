import sys
sys.stdout.reconfigure(encoding='utf-8')

# Check collection policy handling in RuleEngine
with open('src/server_manager/alert/rule_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== Collection policy handling ===")
if 'PARTIAL' in content:
    print("PARTIAL found in rule_engine.py")
else:
    print("PARTIAL NOT found in rule_engine.py")

if 'collection_success' in content:
    print("collection_success found in rule_engine.py")
    
# Check _evaluate_rules method
if '_evaluate_rules' in content:
    idx = content.find('def _evaluate_rules')
    snippet = content[idx:idx+800]
    print("\n=== _evaluate_rules method (first 800 chars) ===")
    print(snippet)
