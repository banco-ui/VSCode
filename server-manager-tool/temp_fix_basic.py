"""Simple fix script."""
with open('tests/test_scheduler_alert_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
content = content.replace(
    'from server_manager.models.enums import ServerLifecycle, Vendor',
    'from server_manager.models.enums import ServerLifecycle, Vendor\nfrom server_manager.orchestrator.models import OrchestrationResult, OrchestrationStatus'
)

# Fix fixture
content = content.replace(
    '''        inv.register_server(
            ServerRegistryEntry(
                server_id="server-001",
                name="Test Server",
                lifecycle=ServerLifecycle.ACTIVE,
                vendor=Vendor.Unknown,
            )
        )''',
    '''        inv.register_server(
            ServerRegistryEntry(
                server_id="server-001",
                display_name="Test Server",
                vendor=Vendor.Unknown,
                model="Test Model",
            )
        )'''
)

# Fix API
content = content.replace('add_schedule(', 'save_schedule(')

# Remove create_execution
content = '\n'.join([line for line in content.split('\n') if 'scheduler_store.create_execution(' not in line])

with open('tests/test_scheduler_alert_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Basic fixes applied")