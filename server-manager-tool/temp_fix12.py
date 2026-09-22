# Use model_construct to bypass validation
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace OrchestrationResult constructor with model_construct
old_result = '''        mock_inventory = Mock()
        mock_inventory.health_status = "OK"
        
        mock_result = OrchestrationResult(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=mock_inventory,
            canonical_source="ssh",
            verification=VerificationResult(),
        )'''

new_result = '''        mock_inventory = Mock()
        mock_inventory.health_status = "OK"
        
        mock_result = OrchestrationResult.model_construct(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=mock_inventory,
            canonical_source="ssh",
            verification=VerificationResult(),
        )'''

content = content.replace(old_result, new_result)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 12 applied: model_construct")