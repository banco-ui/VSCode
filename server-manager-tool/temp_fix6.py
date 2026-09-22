# Fix canonical_inventory to use real ServerInventory object
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Replace mock_result.canonical_inventory = Mock() and next line
    if 'mock_result.canonical_inventory = Mock()' in line:
        # Skip this line and the next one
        new_lines.append('        mock_result.canonical_inventory = ServerInventory(\n')
        new_lines.append('            identity=Identity(server_id="server-001"),\n')
        new_lines.append('            topology=Topology(),\n')
        new_lines.append('            hardware=Hardware(),\n')
        new_lines.append('            management=Management(),\n')
        new_lines.append('            os=OS(),\n')
        new_lines.append('            virtualization=Virtualization(),\n')
        new_lines.append('            containers=Containers(),\n')
        new_lines.append('            development_environment=DevelopmentEnvironment(),\n')
        new_lines.append('            compute=Compute(),\n')
        new_lines.append('            health=Health(health_status="OK"),\n')
        new_lines.append('            workload=Workload(),\n')
        new_lines.append('            power_thermal=PowerThermal(),\n')
        new_lines.append('            vendor_ext=VendorExt(),\n')
        new_lines.append('            meta=Meta(),\n')
        new_lines.append('        )\n')
        i += 2  # Skip original two lines
        continue
    
    new_lines.append(line)
    i += 1

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fix 6 applied: ServerInventory with real object")