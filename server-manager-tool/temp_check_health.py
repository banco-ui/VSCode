import sys
sys.path.insert(0, 'src')

from server_manager.models.inventory import Health
print("Health fields:", list(Health.model_fields.keys()))