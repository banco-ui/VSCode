import sys
sys.path.insert(0, 'src')

from server_manager.models.inventory import Health, ServerInventory
# Create default Health
h = Health()
print("Default Health:", h)

# Check if ServerInventory can be created with defaults
try:
    inv = ServerInventory()
    print("Default ServerInventory created successfully")
    print("Inventory health:", inv.health)
except Exception as e:
    print("Error:", e)