# Remove create_execution() calls
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'scheduler_store.create_execution(' in line:
        continue  # Skip this line
    new_lines.append(line)

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix 3 applied: Removed create_execution() calls")