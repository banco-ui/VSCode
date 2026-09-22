# Fix canonical_inventory to use real ServerInventory object
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import for ServerInventory at the top
old_imports = '''from server_manager.store.models import ServerRegistryEntry
from server_manager.models.enums import ServerLifecycle, Vendor'''

new_imports = '''from server_manager.store.models import ServerRegistryEntry
from server_manager.models.enums import ServerLifecycle, Vendor
from server_manager.models.inventory import ServerInventory, Identity, Topology, Hardware, Management, OS, Virtualization, Containers, DevelopmentEnvironment, Compute, Health, Workload, PowerThermal, VendorExt, Meta'''

content = content.replace(old_imports, new_imports)

# Fix 1: Replace Mock inventory with real ServerInventory in first test
old_inv1 = '''        mock_inventory = Mock()
        mock_inventory.health_status = "OK"'''

new_inv1 = '''        mock_inventory = ServerInventory(
            identity=Identity(server_id="server-001"),
            topology=Topology(),
            hardware=Hardware(),
            management=Management(),
            os=OS(),
            virtualization=Virtualization(),
            containers=Containers(),
            development_environment=DevelopmentEnvironment(),
            compute=Compute(),
            health=Health(health_status="OK"),
            workload=Workload(),
            power_thermal=PowerThermal(),
            vendor_ext=VendorExt(),
            meta=Meta(),
        )'''

content = content.replace(old_inv1, new_inv1)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 5 applied: ServerInventory with real object")