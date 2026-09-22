# Fix verification to use real VerificationResult
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add VerificationResult import
old_imports = '''from server_manager.orchestrator.models import OrchestrationResult, OrchestrationStatus'''

new_imports = '''from server_manager.orchestrator.models import OrchestrationResult, OrchestrationStatus
from server_manager.verifiers.base import VerificationResult'''

content = content.replace(old_imports, new_imports)

# Replace Mock verification with real VerificationResult
old_verif = '''        mock_result.verification = Mock()
        mock_result.verification.has_discrepancy = False'''

new_verif = '''        mock_result.verification = VerificationResult()'''

content = content.replace(old_verif, new_verif)

# Write back
with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix 8 applied: VerificationResult instead of Mock")