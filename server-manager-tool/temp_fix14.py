# Mock verification result as well
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace VerificationResult with Mock
old_verif = '''        mock_result = OrchestrationResult.model_construct(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=mock_inventory,
            canonical_source="ssh",
            verification=VerificationResult(),
        )'''

new_verif = '''        mock_verification = Mock()
        mock_verification.has_discrepancy = False
        
        mock_result = OrchestrationResult.model_construct(
            run_id="test-run-001",
            server_id="server-001",
            status=OrchestrationStatus.SUCCESS,
            canonical_inventory=mock_inventory,
            canonical_source="ssh",
            verification=mock_verification,
        )'''

content = content.replace(old_verif, new_verif)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 14 applied: Mock verification")