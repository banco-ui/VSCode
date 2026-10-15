"""Phase 1-RF.3 — TLS Policy Analysis"""
import ssl, inspect

ctx = ssl.create_default_context()
print("=== ssl.create_default_context CAPABILITIES ===")
print("Has load_verify_locations:", hasattr(ctx, 'load_verify_locations'))
print("Has load_cert_chain:", hasattr(ctx, 'load_cert_chain'))
print("Has check_hostname:", hasattr(ctx, 'check_hostname'))
print("Has verify_mode:", hasattr(ctx, 'verify_mode'))

if hasattr(ctx, 'load_verify_locations'):
    sig = inspect.signature(ctx.load_verify_locations)
    print("\nload_verify_locations signature:", sig)
    print("  Parameters: cafile, capath, cadata")

print("\n=== CURRENT CODE ANALYSIS ===")
print("RedfishCollector.__init__ params:")
print("  - verify_ssl: bool = True (Phase 0.2)")
print("  - NO ca_bundle parameter")
print("  - NO cafile/capath support")

print("\n=== IMPLICATIONS ===")
print("1. System trust store ONLY (no custom CA bundle)")
print("2. Internal CA certs NOT trusted by default")
print("3. Self-signed certs FAIL verification")
print("4. To support custom CA: code change required")

print("\n=== MINIMAL CODE CHANGE FOR CA BUNDLE ===")
print("""
# Add to __init__:
def __init__(self, ..., ca_bundle: Optional[str] = None):
    ...
    self.ca_bundle = ca_bundle

# Modify _get_once:
ctx = ssl.create_default_context()
if self.ca_bundle:
    ctx.load_verify_locations(self.ca_bundle)
elif not self.verify_ssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
""")