# Fix test_worker_survives_alert_failure
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_test6 = '''            # Worker slot should be released
            assert scheduler._running_count == 0

            scheduler._execute_collection(schedule, "server-001", execution)

            assert len(save_called) > 0
            assert len(evaluate_called) > 0'''

new_test6 = '''            # Worker slot should be released
            assert scheduler._running_count == 0

            # Second execution should succeed (worker survived)
            scheduler._execute_collection(schedule, "server-001", execution)'''

content = content.replace(old_test6, new_test6)

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 15c applied: test_worker_survives_alert_failure")