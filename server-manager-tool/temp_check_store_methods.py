import sys
sys.path.insert(0, 'src')

from server_manager.scheduler.store import SchedulerStore

print("=== SchedulerStore Public Methods ===")
methods = [m for m in dir(SchedulerStore) if not m.startswith('_') and callable(getattr(SchedulerStore, m))]
for m in methods:
    print(m)