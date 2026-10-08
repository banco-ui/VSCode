"""Phase 21 Gate 1 — Read-only environment inspection."""
import os
import sys

# 1. Kubernetes Python client
try:
    import kubernetes
    print(f"KUBERNETES_CLIENT: AVAILABLE (v{kubernetes.__version__})")
except ImportError:
    print("KUBERNETES_CLIENT: NOT_AVAILABLE")

# 2. Kubeconfig availability
kubeconfig_env = os.environ.get("KUBECONFIG", "")
default_kubeconfig = os.path.expanduser("~/.kube/config")
kubeconfig_available = bool(kubeconfig_env) or os.path.exists(default_kubeconfig)
print(f"KUBECONFIG_AVAILABLE: {kubeconfig_available}")

# 3. Context availability
context_available = False
auth_available = False
if kubeconfig_available:
    try:
        from kubernetes.config import list_kube_config_contexts
        contexts, active_context = list_kube_config_contexts()
        context_available = len(contexts) > 0
        auth_available = True
        print(f"CONTEXT_AVAILABLE: {context_available}")
        if active_context:
            print(f"ACTIVE_CONTEXT: {active_context.get('name', 'unknown')}")
    except Exception as e:
        print(f"CONTEXT_AVAILABLE: ERROR ({type(e).__name__})")
else:
    print("CONTEXT_AVAILABLE: False (no kubeconfig)")

print(f"AUTHENTICATION_AVAILABLE: {auth_available if kubeconfig_available else False}")

# 4. API connectivity
if kubeconfig_available and context_available:
    try:
        from kubernetes.client import CoreV1Api
        from kubernetes.config import load_kube_config
        load_kube_config()
        api = CoreV1Api()
        version = api.get_api_version()
        git_ver = ""
        if hasattr(version, "git_version"):
            git_ver = version.git_version
        print(f"API_CONNECTIVITY: True (gitVersion={git_ver})")
    except Exception as e:
        print(f"API_CONNECTIVITY: False ({type(e).__name__})")
else:
    print("API_CONNECTIVITY: SKIPPED (no credentials)")

live = kubeconfig_available and context_available
print(f"\nLIVE_PATH: {'AVAILABLE' if live else 'SKIPPED_NO_CREDENTIAL'}")
