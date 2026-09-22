# Fix test_alert_engine_exception_results_in_partial - proper patch
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_test = False
patch_added = False

for i, line in enumerate(lines):
    if 'def test_alert_engine_exception_results_in_partial' in line:
        in_test = True
        new_lines.append(line)
        continue
    
    if in_test and "with patch.object(AlertEngine, 'evaluate', side_effect=Exception" in line and not patch_added:
        # Add inventory patch before AlertEngine patch
        indent = '        '
        new_lines.append(f'{indent}with patch.object(inventory_store, \'save_orchestration_result\'):\n')
        new_lines.append(f'{indent}    {line.lstrip()}')
        patch_added = True
        continue
    
    if 'def test_worker_survives_alert_failure' in line:
        in_test = False
        patch_added = False
    
    new_lines.append(line)

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix 15d applied: Added inventory patch")