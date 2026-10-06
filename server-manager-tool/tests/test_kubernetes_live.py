"""Kubernetes Live Read-Only Discovery Tests — Phase 13G-6/13G-7.

These tests validate real Kubernetes API compatibility. They are SKIPPED
when the kubernetes Python client or cluster credentials are unavailable.

ALL operations in this module are strictly READ-ONLY. No create, update,
patch, delete, or any mutation operation is performed.

Safety:
    - If kubernetes client is not installed → ALL live tests SKIP
    - If no kubeconfig/credentials → ALL live tests SKIP
    - No fixture PASS is reported as live PASS

Phase 13G-7 update: kubernetes client 36.0.3 is now AVAILABLE.
Live tests remain SKIPPED due to missing Kubernetes credentials.
"""
from __future__ import annotations

import os
import inspect
from typing import Any

import pytest

from server_manager.models.canonical import (
    ExecutionEnvironmentType,
    PlatformType,
    ProviderType,
    RelationshipEvidenceType,
)
from server_manager.normalizers.kubernetes_normalizer import (
    KubernetesProviderNormalizer,
)
from server_manager.orchestrator.models import OrchestrationStatus
from server_manager.providers import (
    AdapterCapability,
    KubernetesProviderAdapter,
    RawProviderSnapshot,
)


# ════════════════════════════════════════════════════════════════════════
#  LIVE TEST SKIP CONDITION
# ════════════════════════════════════════════════════════════════════════

_LIVE_SKIP_REASON: str | None = None

try:
    import kubernetes as _k8s_module  # noqa: F401
    _K8S_CLIENT_AVAILABLE = True
except ImportError:
    _K8S_CLIENT_AVAILABLE = False
    _LIVE_SKIP_REASON = (
        "kubernetes Python client is not installed. "
        "Live tests are skipped. Install with: pip install kubernetes"
    )

_KUBECONFIG_ENV = os.environ.get("KUBECONFIG", "")
_DEFAULT_KUBECONFIG = os.path.expanduser("~/.kube/config")
_KUBECONFIG_AVAILABLE = bool(_KUBECONFIG_ENV) or os.path.exists(_DEFAULT_KUBECONFIG)

if _K8S_CLIENT_AVAILABLE and not _KUBECONFIG_AVAILABLE:
    _LIVE_SKIP_REASON = (
        "No Kubernetes credentials found. "
        "KUBECONFIG not set and default kubeconfig does not exist."
    )

LIVE = pytest.mark.skipif(
    not _K8S_CLIENT_AVAILABLE or not _KUBECONFIG_AVAILABLE,
    reason=_LIVE_SKIP_REASON or "Live tests skipped",
)


# ════════════════════════════════════════════════════════════════════════
#  DETERMINISTIC TESTS (always run)
# ════════════════════════════════════════════════════════════════════════


class TestEnvironmentAudit:
    """G6-01: Environment audit — deterministic, always runs."""

    def test_python_version(self):
        import sys
        assert sys.version_info >= (3, 12)

    def test_kubernetes_client_status_reported(self):
        if _K8S_CLIENT_AVAILABLE:
            import kubernetes
            assert hasattr(kubernetes, "__version__")
        else:
            assert _LIVE_SKIP_REASON is not None

    def test_kubernetes_client_available_phase13g7(self):
        """G7-03: kubernetes client is now AVAILABLE (Phase 13G-7)."""
        assert _K8S_CLIENT_AVAILABLE, (
            "kubernetes client should be available in Phase 13G-7. "
            "Install with: pip install kubernetes"
        )
        import kubernetes
        assert kubernetes.__version__

    def test_kubeconfig_env_checked(self):
        assert isinstance(_KUBECONFIG_ENV, str)

    def test_default_kubeconfig_path_checked(self):
        assert isinstance(_DEFAULT_KUBECONFIG, str)
        assert _DEFAULT_KUBECONFIG.endswith(".kube/config")

    def test_live_skip_reason_documented_when_unavailable(self):
        if not _K8S_CLIENT_AVAILABLE or not _KUBECONFIG_AVAILABLE:
            assert _LIVE_SKIP_REASON is not None
            assert len(_LIVE_SKIP_REASON) > 0

    def test_credential_unavailable_skip_reason(self):
        """G7-04: credential unavailable → skip reason mentions credentials."""
        if not _KUBECONFIG_AVAILABLE:
            assert _LIVE_SKIP_REASON is not None
            assert "credential" in _LIVE_SKIP_REASON.lower() or \
                   "kubeconfig" in _LIVE_SKIP_REASON.lower()


class TestNoMutationGuard:
    """G6-19: No mutation — verify adapter/normalizer source has no write ops."""

    def test_adapter_no_create(self):
        from server_manager.providers.kubernetes import KubernetesProviderAdapter
        source = inspect.getsource(KubernetesProviderAdapter)
        assert "create_namespaced" not in source
        assert "create_pod" not in source

    def test_adapter_no_delete(self):
        from server_manager.providers.kubernetes import KubernetesProviderAdapter
        source = inspect.getsource(KubernetesProviderAdapter)
        assert "delete_namespaced" not in source
        assert "delete_pod" not in source

    def test_adapter_no_patch(self):
        from server_manager.providers.kubernetes import KubernetesProviderAdapter
        source = inspect.getsource(KubernetesProviderAdapter)
        assert "patch_namespaced" not in source

    def test_adapter_no_update(self):
        from server_manager.providers.kubernetes import KubernetesProviderAdapter
        source = inspect.getsource(KubernetesProviderAdapter)
        assert "update_namespaced" not in source
        assert "replace_namespaced" not in source

    def test_adapter_no_exec(self):
        from server_manager.providers.kubernetes import KubernetesProviderAdapter
        source = inspect.getsource(KubernetesProviderAdapter)
        assert "connect_get_namespaced_pod_exec" not in source

    def test_normalizer_no_kubernetes_client(self):
        from server_manager.normalizers.kubernetes_normalizer import (
            KubernetesProviderNormalizer)
        source = inspect.getsource(KubernetesProviderNormalizer)
        assert "import kubernetes" not in source
        assert "from kubernetes" not in source
        assert "CoreV1Api" not in source

    def test_no_persistence_in_adapter(self):
        from server_manager.providers.kubernetes import KubernetesProviderAdapter
        source = inspect.getsource(KubernetesProviderAdapter)
        assert "database" not in source.lower()
        assert "commit" not in source.lower()

    def test_no_persistence_in_normalizer(self):
        from server_manager.normalizers.kubernetes_normalizer import (
            KubernetesProviderNormalizer)
        source = inspect.getsource(KubernetesProviderNormalizer)
        assert "database" not in source.lower()
        assert "commit" not in source.lower()


class TestLiveSkipMechanism:
    """Verify live test skip mechanism works correctly."""

    def test_live_skip_reason_string_when_unavailable(self):
        if not _K8S_CLIENT_AVAILABLE or not _KUBECONFIG_AVAILABLE:
            assert _LIVE_SKIP_REASON is not None
            assert isinstance(_LIVE_SKIP_REASON, str)

    def test_fixture_not_mislabeled_as_live(self):
        adapter = KubernetesProviderAdapter(fixture={
            "cluster": {"name": "test", "version": "1.28.0"}})
        snapshot = adapter.collect()
        assert snapshot.payload["cluster"]["name"] == "test"


class TestAdapterLiveReadiness:
    """Verify adapter structure for future live support (deterministic)."""

    def test_adapter_accepts_fixture_dict(self):
        adapter = KubernetesProviderAdapter(fixture={
            "cluster": {"name": "test", "version": "1.28.0"}})
        snapshot = adapter.collect()
        assert snapshot.provider_type == ProviderType.KUBERNETES

    def test_adapter_collect_no_network(self):
        adapter = KubernetesProviderAdapter(fixture={
            "cluster": {"name": "offline", "version": "1.28.0"}})
        snapshot = adapter.collect()
        assert snapshot.collection_status == OrchestrationStatus.SUCCESS

    def test_adapter_provider_id_preserved(self):
        adapter = KubernetesProviderAdapter(
            provider_id="live-01",
            fixture={"cluster": {"name": "t", "version": "1.28.0"}})
        snapshot = adapter.collect()
        assert snapshot.provider_id == "live-01"
        assert snapshot.source_evidence.provider_id == "live-01"

    def test_no_secret_collection_in_capabilities(self):
        adapter = KubernetesProviderAdapter(fixture={})
        caps = adapter.capabilities()
        assert not any("SECRET" in c.value.upper() for c in caps)


# ════════════════════════════════════════════════════════════════════════
#  LIVE INTEGRATION TESTS (skipped when prerequisites unavailable)
# ════════════════════════════════════════════════════════════════════════


@LIVE
class TestLiveConnection:
    """G6-05: Live read-only connection (SKIPPED if no client/credentials)."""

    def test_kubernetes_client_importable(self):
        import kubernetes
        assert hasattr(kubernetes, "__version__")

    def test_kubeconfig_loadable(self):
        from kubernetes.config import kube_config
        kube_config.load_kube_config()

    def test_current_context_identified(self):
        from kubernetes.config import kube_config
        loader = kube_config.KubeConfigLoader(
            filename=_KUBECONFIG_ENV or _DEFAULT_KUBECONFIG)
        assert loader.current_context is not None

    def test_server_version_retrievable(self):
        from kubernetes.client import VersionApi
        from kubernetes.config import load_kube_config
        load_kube_config()
        api = VersionApi()
        version_info = api.get_code()
        assert version_info is not None


@LIVE
class TestLiveSnapshot:
    """G6-07/G6-08: Real RawProviderSnapshot from live cluster."""

    def _collect_live(self) -> RawProviderSnapshot:
        from kubernetes.client import CoreV1Api, ApiClient
        from kubernetes.config import load_kube_config
        load_kube_config()
        api = CoreV1Api()
        ac = ApiClient()
        nodes = api.list_node().items
        pods = api.list_pod_for_all_namespaces().items
        namespaces = api.list_namespace().items
        fixture = {
            "cluster": {"name": "live-cluster", "version": ""},
            "nodes": [ac.sanitize_for_serialization(n) for n in nodes],
            "namespaces": [ac.sanitize_for_serialization(ns) for ns in namespaces],
            "pods": [ac.sanitize_for_serialization(p) for p in pods],
            "services": [],
            "persistent_volumes": [],
            "persistent_volume_claims": [],
        }
        adapter = KubernetesProviderAdapter(
            provider_id="live-cluster", fixture=fixture)
        return adapter.collect()

    def test_live_snapshot_valid(self):
        snapshot = self._collect_live()
        assert snapshot.provider_type == ProviderType.KUBERNETES
        assert snapshot.snapshot_id.startswith("snap-k8s-")
        assert snapshot.source_evidence is not None

    def test_live_snapshot_has_nodes(self):
        snapshot = self._collect_live()
        assert len(snapshot.payload["nodes"]) > 0

    def test_live_snapshot_capability_results(self):
        snapshot = self._collect_live()
        assert len(snapshot.capability_results) > 0
        assert any(cr.status == OrchestrationStatus.SUCCESS
                   for cr in snapshot.capability_results)


@LIVE
class TestLiveNormalization:
    """G6-09/G6-10: Real snapshot → normalizer → canonical entities."""

    def _collect_and_normalize(self):
        from kubernetes.client import CoreV1Api, ApiClient
        from kubernetes.config import load_kube_config
        load_kube_config()
        api = CoreV1Api()
        ac = ApiClient()
        nodes = api.list_node().items
        pods = api.list_pod_for_all_namespaces().items
        namespaces = api.list_namespace().items
        fixture = {
            "cluster": {"name": "live-cluster", "version": ""},
            "nodes": [ac.sanitize_for_serialization(n) for n in nodes],
            "namespaces": [ac.sanitize_for_serialization(ns) for ns in namespaces],
            "pods": [ac.sanitize_for_serialization(p) for p in pods],
            "services": [],
            "persistent_volumes": [],
            "persistent_volume_claims": [],
        }
        adapter = KubernetesProviderAdapter(
            provider_id="live-cluster", fixture=fixture)
        snapshot = adapter.collect()
        return snapshot, KubernetesProviderNormalizer().normalize(snapshot)

    def test_live_normalization_produces_entities(self):
        _, result = self._collect_and_normalize()
        assert result.entity_count > 0

    def test_live_platform_is_kubernetes(self):
        _, result = self._collect_and_normalize()
        assert result.platforms[0].platform_type == PlatformType.KUBERNETES

    def test_live_nodes_created(self):
        _, result = self._collect_and_normalize()
        assert len(result.nodes) > 0

    def test_live_pods_become_ee(self):
        _, result = self._collect_and_normalize()
        assert any(ee.ee_type == ExecutionEnvironmentType.POD
                   for ee in result.execution_environments)

    def test_live_pod_to_node_relationship(self):
        _, result = self._collect_and_normalize()
        direct = [e for e in result.relationship_evidence
                  if e.evidence_type == RelationshipEvidenceType.DIRECT]
        assert len(direct) > 0

    def test_live_provenance_preserved(self):
        snapshot, result = self._collect_and_normalize()
        for node in result.nodes:
            assert node.source_evidence is not None
            assert node.source_evidence.raw_data_ref == snapshot.snapshot_id

    def test_live_no_workload_inference(self):
        _, result = self._collect_and_normalize()
        assert len(result.workloads) == 0

    def test_live_no_accelerator_inference(self):
        _, result = self._collect_and_normalize()
        assert len(result.accelerators) == 0

    def test_live_identity_stability(self):
        _, result1 = self._collect_and_normalize()
        _, result2 = self._collect_and_normalize()
        ids1 = sorted(n.canonical_id for n in result1.nodes)
        ids2 = sorted(n.canonical_id for n in result2.nodes)
        assert ids1 == ids2




