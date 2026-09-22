c = open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8').read()
c = c.replace('add_schedule(', 'save_schedule(')
open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8').write(c)
print('Done')