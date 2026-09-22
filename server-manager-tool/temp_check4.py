import inspect
from server_manager.store.store import InventoryStore
methods = [m[0] for m in inspect.getmembers(InventoryStore, predicate=inspect.ismethod) if not m[0].startswith('_')]
print("InventoryStore methods:", methods)