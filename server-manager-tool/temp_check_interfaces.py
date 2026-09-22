import sys
sys.path.insert(0, 'src')

from server_manager.store.models import ServerInventory
from server_manager.scheduler.store import SchedulerStore

print("=== ServerInventory Fields ===")
print(list(ServerInventory.model_fields.keys()))

print("\n=== SchedulerStore Methods ===")
methods = [m for m in dir(SchedulerStore) if not m.startswith('_') and callable(getattr(SchedulerStore, m))]
print(methods)