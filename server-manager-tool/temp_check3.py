with open('tests/test_scheduler_alert_integration.py','r',encoding='utf-8') as f:
    lines = f.readlines()
print(f'Lines: {len(lines)}')
print(f'Last line: {lines[-1] if lines else "empty"}')