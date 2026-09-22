try:
    from server_manager.store.models import ServerInventory
    print("ServerInventory found in store.models")
except ImportError:
    print("ServerInventory not found in store.models")
    from server_manager.orchestrator.models import CanonicalInventory
    print("CanonicalInventory found in orchestrator.models")