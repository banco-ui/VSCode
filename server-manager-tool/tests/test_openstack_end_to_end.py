"""OpenStack End-to-End Discovery Tests — Phase 26.

Integration tests for the full OpenStack discovery pipeline:
    OpenStackProviderAdapter → RawProviderSnapshot
        → OpenStackProviderNormalizer → NormalizationResult
        → PlatformDiscovery → DiscoveryResult
        → HealthService → HealthReport

NO live OpenStack connection. All fixtures are synthetic/in-memory.
"""
from __future__ import annotations

from typing import Any

import pytest

from server_manager.discovery.service import PlatformDiscovery
from server_manager.health.models import HealthStatus, AvailabilityStatus
from server_manager.health.service import HealthService
from server_manager.models.canonical import (
    ExecutionEnvironmentType,
    NetworkType,
    PlatformType,
    ProviderType,
    StorageType,
)
from server_manager.normalizers.openstack_normalizer import OpenStackProviderNormalizer
from server_manager.orchestrator.models import OrchestrationStatus
from server_manager.providers import OpenStackProviderAdapter


def make_full_topology() -> dict[str, Any]:
    return {
        "platform": {"name": "openstack-cloud", "version": "Yoga"},
        "availability_zones": [
            {"zoneName": "nova", "zoneState": {"available": True}},
        ],
        "hypervisors": [
            {"hypervisor_hostname": "compute-01", "id": 1,
             "state": "up", "status": "enabled",
             "vcpus": 32, "memory_mb": 131072, "local_gb": 500},
        ],
        "servers": [
            {"id": "srv-001", "name": "vm-web-01", "status": "ACTIVE",
             "OS-EXT-SRV-ATTR:hypervisor_hostname": "compute-01",
             "flavor": {"id": "flavor-001"}},
        ],
        "networks": [
            {"id": "net-001", "name": "public-net", "status": "ACTIVE"},
        ],
        "volumes": [
            {"id": "vol-001", "name": "data-vol", "status": "in-use",
             "size": 100, "attachments": [{"server_id": "srv-001"}]},
        ],
        "flavors": [{"id": "flavor-001", "name": "m1.small"}],
    }


def make_empty_topology() -> dict[str, Any]:
    return {"platform": {"name": "empty-cloud", "version": ""}}


def make_unhealthy_topology() -> dict[str, Any]:
    return {
        "platform": {"name": "openstack-cloud", "version": "Yoga"},
        "hypervisors": [
            {"hypervisor_hostname": "compute-01", "id": 1,
             "state": "down", "status": "disabled",
             "vcpus": 16, "memory_mb": 65536, "local_gb": 200},
        ],
        "servers": [
            {"id": "srv-001", "name": "vm-01", "status": "ERROR",
             "OS-EXT-SRV-ATTR:hypervisor_hostname": "compute-01",
             "flavor": {"id": "flavor-001"}},
        ],
        "networks": [
            {"id": "net-001", "name": "net-01", "status": "DOWN"},
        ],
        "volumes": [
            {"id": "vol-001", "name": "vol-01", "status": "error",
             "size": 50, "attachments": []},
        ],
    }


# ════════════════════════════════════════════════════════════════════════
#  E1 — FULL DISCOVERY PIPELINE
# ════════════════════════════════════════════════════════════════════════

class TestFullDiscovery:
    def test_discover_returns_result(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert result is not None

    def test_discover_success_status(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert result.discovery_status == OrchestrationStatus.SUCCESS

    def test_discover_provider_type(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert result.provider_type == ProviderType.OPENSTACK

    def test_discover_inventory_has_platform(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert len(result.inventory.platforms) == 1
        assert result.inventory.platforms[0].platform_type == PlatformType.OPENSTACK

    def test_discover_inventory_has_node(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert len(result.inventory.nodes) == 1

    def test_discover_inventory_has_ee(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert len(result.inventory.execution_environments) == 1
        assert result.inventory.execution_environments[0].ee_type == ExecutionEnvironmentType.VM


# ════════════════════════════════════════════════════════════════════════
#  E2 — EMPTY DISCOVERY
# ════════════════════════════════════════════════════════════════════════

class TestEmptyDiscovery:
    def test_empty_discover_success(self):
        adapter = OpenStackProviderAdapter(
            provider_id="empty-cloud", fixture=make_empty_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert result.discovery_status == OrchestrationStatus.SUCCESS

    def test_empty_discover_platform_only(self):
        adapter = OpenStackProviderAdapter(
            provider_id="empty-cloud", fixture=make_empty_topology())
        normalizer = OpenStackProviderNormalizer()
        result = PlatformDiscovery().discover(adapter, normalizer)
        assert len(result.inventory.platforms) == 1
        assert len(result.inventory.nodes) == 0


# ════════════════════════════════════════════════════════════════════════
#  E3 — HEALTH ASSESSMENT
# ════════════════════════════════════════════════════════════════════════

class TestHealthAssessment:
    def test_health_report_created(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        assert report is not None

    def test_health_report_provider_type(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        assert report.provider_type == ProviderType.OPENSTACK

    def test_health_report_has_results(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        assert len(report.results) > 0

    def test_healthy_node_status(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        node_results = report.results_for_type("NODE")
        assert len(node_results) == 1
        assert node_results[0].status == HealthStatus.HEALTHY

    def test_healthy_ee_status(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_full_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        ee_results = report.results_for_type("EXECUTION_ENVIRONMENT")
        assert len(ee_results) == 1
        assert ee_results[0].status == HealthStatus.HEALTHY


# ════════════════════════════════════════════════════════════════════════
#  E4 — UNHEALTHY TOPOLOGY
# ════════════════════════════════════════════════════════════════════════

class TestUnhealthyTopology:
    def test_unhealthy_node(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_unhealthy_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        node_results = report.results_for_type("NODE")
        assert len(node_results) == 1
        assert node_results[0].status == HealthStatus.UNHEALTHY

    def test_unhealthy_ee(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_unhealthy_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        ee_results = report.results_for_type("EXECUTION_ENVIRONMENT")
        assert len(ee_results) == 1
        assert ee_results[0].status == HealthStatus.UNHEALTHY

    def test_unhealthy_network(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_unhealthy_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        net_results = report.results_for_type("NETWORK")
        assert len(net_results) == 1
        assert net_results[0].status == HealthStatus.UNHEALTHY

    def test_unhealthy_report_partial(self):
        adapter = OpenStackProviderAdapter(
            provider_id="test-cloud", fixture=make_unhealthy_topology())
        normalizer = OpenStackProviderNormalizer()
        dr = PlatformDiscovery().discover(adapter, normalizer)
        report = HealthService().assess(dr)
        assert report.health_status == OrchestrationStatus.PARTIAL


# ════════════════════════════════════════════════════════════════════════
#  E5 — MULTI-PROVIDER COEXISTENCE
# ════════════════════════════════════════════════════════════════════════

class TestMultiProviderCoexistence:
    def test_openstack_and_kubernetes_both_registered(self):
        from server_manager.health.service import HealthService
        extractors = HealthService._EXTRACTORS
        assert ProviderType.OPENSTACK in extractors
        assert ProviderType.KUBERNETES in extractors

    def test_openstack_extractor_is_correct_class(self):
        from server_manager.health.service import HealthService, OpenStackHealthExtractor
        extractors = HealthService._EXTRACTORS
        assert extractors[ProviderType.OPENSTACK] is OpenStackHealthExtractor
