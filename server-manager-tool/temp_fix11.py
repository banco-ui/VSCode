# Add health_status mock to ServerInventory
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ServerInventory() with a Mock that has health_status
old_inv = '''        mock_result = OrchestrationResult(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=ServerInventory(),
            canonical_source="ssh",
            verification=VerificationResult(),
        )'''

new_inv = '''        mock_inventory = Mock()
        mock_inventory.health_status = "OK"
        
        mock_result = OrchestrationResult(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=mock_inventory,
            canonical_source="ssh",
            verification=VerificationResult(),
        )'''

content = content.replace(old_inv, new_inv)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 11 applied: Mock inventory with health_status")