import ast
for f in ['src/server_manager/operations/models.py', 'src/server_manager/operations/service.py']:
    try:
        ast.parse(open(f, encoding='utf-8').read())
        print(f"{f}: OK")
    except SyntaxError as e:
        print(f"{f}: SYNTAX ERROR: {e}")
