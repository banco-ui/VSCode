import ast
with open('tests/test_platform_recovery.py', encoding='utf-8') as f:
    ast.parse(f.read())
print('Syntax OK')
