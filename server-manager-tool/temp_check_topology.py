import sys
sys.path.insert(0, 'src')

from server_manager.models.inventory import Topology

print("=== Topology Fields ===")
print(list(Topology.model_fields.keys()))