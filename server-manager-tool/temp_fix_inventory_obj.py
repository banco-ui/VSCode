import sys
sys.path.insert(0, 'src')

# Read and fix the test file
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace the Mock inventory with proper ServerInventory mock that passes validation
old_inv = '''        from server_manager.models.inventory import Identity, Health
        from server_manager.models.enums import Vendor
        
        # Create proper nested ServerInventory structure
        # Mock canonical_inventory with required attributes
        mock_inventory = Mock()
        mock_inventory.health_status = "OK"'''

new_inv = '''        from server_manager.models.inventory import ServerInventory
        from server_manager.models.inventory import Identity, Health, Hardware, Management, OS, Virtualization, Containers, DevelopmentEnvironment, Compute, Workload, PowerThermal, VendorExt, Meta, Topology
        from server_manager.models.enums import Vendor
        
        # Create minimal valid ServerInventory (all required fields)
        mock_inventory = ServerInventory(
            schema_version="1.0",
            identity=Identity(server_id="server-001", vendor=Vendor.Unknown, model="Test", hostname="test"),
            topology=Topology(rack_id="rack-001"),
            hardware=Hardware(cpu=[], memory=[], storage=[], network=[]),
            management=Management(bmc_mac="00:00:00:00:00:00"),
            os=OS(name="Ubuntu", version="22.04"),
            virtualization=None,
            containers=None,
            development_environment=None,
            compute=Compute(cpu_cores=4, memory_total_gb=16),
            health=Health(system="OK", cpu="OK", memory="OK", storage="OK", thermal="OK", network="OK", psu="OK", fan="OK"),
            workload=None,
            power_thermal=None,
            vendor_ext=VendorExt(),
            meta=Meta(collected_at="2026-01-01T00:00:00Z"),
        )'''

content = content.replace(old_inv, new_inv)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed ServerInventory to be valid object")