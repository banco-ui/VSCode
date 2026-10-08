import ast
files = [
    'src/server_manager/operations/models.py',
    'src/server_manager/operations/service.py',
    'src/server_manager/operations/__init__.py',
    'tests/test_platform_operations.py',
]
for f in files:
    try:
        ast.parse(open(f).read())
        print(f'OK: {f}')
    except SyntaxError as e:
        print(f'SYNTAX ERR: {f}: {e}')

# Count test classes and methods
lines = open('tests/test_platform_operations.py').readlines()
classes = [l.strip() for l in lines if l.strip().startswith('class Test')]
methods = [l.strip() for l in lines if l.strip().startswith('def test_')]
print(f'\nTotal lines: {len(lines)}')
print(f'Test classes: {len(classes)}')
for c in classes:
    print(f'  {c}')
print(f'Test methods: {len(methods)}')
