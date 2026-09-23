import sys
sys.path.insert(0, 'src')
from server_manager.alert.store import AlertStore

s = AlertStore(':memory:')
print('begin_transaction:', hasattr(s, 'begin_transaction'))
print('commit:', hasattr(s, 'commit'))
print('rollback:', hasattr(s, 'rollback'))

# List all methods
methods = [m for m in dir(s) if not m.startswith('_')]
print('\nPublic methods:')
for m in methods:
    print(f'  {m}')
