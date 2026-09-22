# Fix canonical_inventory to use default ServerInventory
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the complex ServerInventory with a simple default one
old_inv = '''        mock_result.canonical_inventory = ServerInventory(
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

new_inv = '''        mock_result.canonical_inventory = ServerInventory()'''

content = content.replace(old_inv, new_inv)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 7 applied: Simplified ServerInventory")