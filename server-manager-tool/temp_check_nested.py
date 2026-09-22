import sys
sys.path.insert(0, 'src')

from server_manager.models.inventory import Identity, Health, Hardware

print("=== Identity Fields ===")
print(list(Identity.model_fields.keys()))

print("\n=== Health Fields ===")
print(list(Health.model_fields.keys()))

print("\n=== Hardware Fields ===")
print(list(Hardware.model_fields.keys()))