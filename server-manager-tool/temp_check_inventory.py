import sys
sys.path.insert(0, 'src')

from server_manager.models.inventory import ServerInventory

# Get all fields
print("ServerInventory fields:")
for field_name in ServerInventory.model_fields:
    print(f"  - {field_name}")