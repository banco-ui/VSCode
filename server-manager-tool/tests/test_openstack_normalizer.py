"""OpenStack Provider Normalizer Tests — Phase 26.

Tests for OpenStackProviderNormalizer:
    - Platform, Cluster, Node, EE, Network, Storage mapping
    - Enum mapping (PlatformType.OPENSTACK, ClusterType.OPENSTACK, etc.)
    - Reference resolution (Server→Hypervisor, Volume→Server)
    - Relationship evidence preservation
    - Empty fixture handling
    - Provenance (source_evidence)

NO live OpenStack connection. All fixtures are synthetic/in-memory.
"""
from __future__ import annotations

from typing import Any

import pytest

from server_manager.models.canonical import (
    ClusterType,
    ExecutionEnvironmentType,
    NetworkType,
    PlatformType,
    ProviderType,
    StorageType,
)
from server_manager.normalizers.openstack_normalizer import OpenStackProviderNormalizer
from server_manager.orchestrator.models import OrchestrationStatus
from server_manager.providers import OpenStackProviderAdapter, RawProviderSnapshot


def make_hypervisor(hostname: str = "compute-01") -> dict:
    return {
        "hypervisor_hostname": hostname, "id": 1,
        "state": "up", "status": "enabled",
        "vcpus": 32, "memory_mb": 131072, "local_gb": 500,
    }


def make_server(
    sid: str = "srv-001", name: str = "vm-01",
    status: str = "ACTIVE", hv: str | None = "compute-01",
) -> dict:
    srv: dict[str, Any] = {
        "id": sid, "name": name, "status": status,
        "flavor": {"id": "flavor-001"},
    }
    if hv:
        srv["OS-EXT-SRV-ATTR:hypervisor_hostname"] = hv
    return srv


def make_network(net_id: str = "net-001", name: str = "public") -> dict:
    return {"id": net_id, "name": name, "status": "ACTIVE"}


def make_volume(
    vid: str = "vol-001", name: str = "data-vol",
    status: str = "in-use", size: int = 100,
    attachments: list | None = None,
) -> dict:
    if attachments is None:
        attachments = [{"server_id": "srv-001"}]
    return {
        "id": vid, "name": name, "status": status, "size": size,
        "attachments": attachments,
    }


def make_az(name: str = "nova") -> dict:
    return {"zoneName": name, "zoneState": {"available": True}}


@pytest.fixture
def full_fixture() -> dict[str, Any]:
    return {
        "platform": {"name": "openstack-cloud", "version": "Yoga"},
        "availability_zones": [make_az("nova")],
        "hypervisors": [make_hypervisor("compute-01")],
        "servers": [make_server("srv-001", "vm-web-01", "ACTIVE", "compute-01")],
        "networks": [make_network("net-001", "public-net")],
        "volumes": [make_volume("vol-001", "data-vol", "in-use", 100,
                                [{"server_id": "srv-001"}])],
        "flavors": [{"id": "flavor-001", "name": "m1.small"}],
    }


@pytest.fixture
def snapshot(full_fixture) -> RawProviderSnapshot:
    adapter = OpenStackProviderAdapter(
        provider_id="test-cloud", fixture=full_fixture)
    return adapter.collect()


@pytest.fixture
def normalizer() -> OpenStackProviderNormalizer:
    return OpenStackProviderNormalizer()


# ════════════════════════════════════════════════════════════════════════
#  N1 — PLATFORM MAPPING
# ════════════════════════════════════════════════════════════════════════

class TestPlatformMapping:
    def test_platform_created(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.platforms) == 1

    def test_platform_type_openstack(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.platforms[0].platform_type == PlatformType.OPENSTACK

    def test_platform_version(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.platforms[0].version == "Yoga"

    def test_platform_provider_type(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.platforms[0].provider_type == ProviderType.OPENSTACK


# ════════════════════════════════════════════════════════════════════════
#  N2 — CLUSTER MAPPING
# ════════════════════════════════════════════════════════════════════════

class TestClusterMapping:
    def test_cluster_created_from_az(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.clusters) == 1

    def test_cluster_type_openstack(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.clusters[0].cluster_type == ClusterType.OPENSTACK

    def test_cluster_platform_ref(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.clusters[0].platform_ref is not None


# ════════════════════════════════════════════════════════════════════════
#  N3 — NODE (HYPERVISOR) MAPPING
# ════════════════════════════════════════════════════════════════════════

class TestNodeMapping:
    def test_node_created(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.nodes) == 1

    def test_node_name(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.nodes[0].name == "compute-01"

    def test_node_provider_type(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.nodes[0].provider_type == ProviderType.OPENSTACK

    def test_node_cluster_ref(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.nodes[0].cluster_ref is not None

    def test_node_metadata_openstack(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert "openstack" in result.nodes[0].metadata
        assert "raw" in result.nodes[0].metadata["openstack"]


# ════════════════════════════════════════════════════════════════════════
#  N4 — EXECUTION ENVIRONMENT (SERVER/VM) MAPPING
# ════════════════════════════════════════════════════════════════════════

class TestExecutionEnvironmentMapping:
    def test_ee_created(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.execution_environments) == 1

    def test_ee_type_vm(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.execution_environments[0].ee_type == ExecutionEnvironmentType.VM

    def test_ee_name(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.execution_environments[0].name == "vm-web-01"

    def test_ee_node_ref_resolved(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        ee = result.execution_environments[0]
        assert ee.node_ref is not None
        # node_ref should be resolved to canonical_id
        node = result.nodes[0]
        assert ee.node_ref == node.canonical_id

    def test_ee_metadata_openstack(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert "openstack" in result.execution_environments[0].metadata


# ════════════════════════════════════════════════════════════════════════
#  N5 — NETWORK MAPPING
# ════════════════════════════════════════════════════════════════════════

class TestNetworkMapping:
    def test_network_created(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.networks) == 1

    def test_network_type_virtual(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.networks[0].network_type == NetworkType.VIRTUAL

    def test_network_name(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.networks[0].name == "public-net"


# ════════════════════════════════════════════════════════════════════════
#  N6 — STORAGE (VOLUME) MAPPING
# ════════════════════════════════════════════════════════════════════════

class TestStorageMapping:
    def test_storage_created(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.storages) == 1

    def test_storage_type_volume(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.storages[0].storage_type == StorageType.VOLUME

    def test_storage_name(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert result.storages[0].name == "data-vol"


# ════════════════════════════════════════════════════════════════════════
#  N7 — RELATIONSHIP EVIDENCE
# ════════════════════════════════════════════════════════════════════════

class TestRelationshipEvidence:
    def test_relationships_preserved(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.relationship_evidence) >= 2

    def test_runs_on_evidence(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        runs_on = [e for e in result.relationship_evidence
                   if e.relationship_type == "runs_on"]
        assert len(runs_on) == 1

    def test_attached_to_evidence(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        attached = [e for e in result.relationship_evidence
                    if e.relationship_type == "attached_to"]
        assert len(attached) == 1


# ════════════════════════════════════════════════════════════════════════
#  N8 — EMPTY FIXTURE
# ════════════════════════════════════════════════════════════════════════

class TestEmptyFixture:
    def test_empty_fixture_platform_only(self):
        adapter = OpenStackProviderAdapter(fixture={})
        snap = adapter.collect()
        normalizer = OpenStackProviderNormalizer()
        result = normalizer.normalize(snap)
        assert len(result.platforms) == 1
        assert len(result.nodes) == 0
        assert len(result.execution_environments) == 0

    def test_empty_fixture_status(self):
        adapter = OpenStackProviderAdapter(fixture={})
        snap = adapter.collect()
        normalizer = OpenStackProviderNormalizer()
        result = normalizer.normalize(snap)
        assert result.status == OrchestrationStatus.SUCCESS


# ════════════════════════════════════════════════════════════════════════
#  N9 — PROVENANCE
# ════════════════════════════════════════════════════════════════════════

class TestProvenance:
    def test_source_evidence_set(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        for platform in result.platforms:
            assert platform.source_evidence is not None
            assert platform.source_evidence.provider_type == ProviderType.OPENSTACK

    def test_source_evidence_provider_id(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        for node in result.nodes:
            assert node.source_evidence is not None
            assert node.source_evidence.provider_id == "test-cloud"


# ════════════════════════════════════════════════════════════════════════
#  N10 — NOT CREATED
# ════════════════════════════════════════════════════════════════════════

class TestNotCreated:
    def test_no_physical(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.physicals) == 0

    def test_no_os(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.os_entities) == 0

    def test_no_workload(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.workloads) == 0

    def test_no_accelerator(self, snapshot, normalizer):
        result = normalizer.normalize(snapshot)
        assert len(result.accelerators) == 0
