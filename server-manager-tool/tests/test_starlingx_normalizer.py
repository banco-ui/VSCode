"""Tests for StarlingX Provider Normalizer — Phase 28E.

Fixture-based tests. No live connection.
"""
from __future__ import annotations

import pytest

from server_manager.models.canonical import (
    ClusterType, PlatformType, ProviderType,
)
from server_manager.normalizers.starlingx_normalizer import (
    StarlingXProviderNormalizer,
)
from server_manager.providers.starlingx import StarlingXProviderAdapter

SYSTEM_UUID = "f3c8a1b2-1234-5678-9abc-def012345678"
HOST_UUID = "a7aa8774-c383-4641-ba1d-dc13c1dee91d"
ALARM_UUID = "fe7e9b1e-4a8e-4f76-9d6a-8c2c1a3b4c5d"


def _make_fixture():
    return {
        "sysinv_isystems": [{
            "uuid": SYSTEM_UUID, "name": "wrcp-ctrlr",
            "sw_version": "24.09", "system_mode": "simplex",
            "system_type": "All-in-one", "timezone": "UTC",
        }],
        "sysinv_ihosts": [{
            "uuid": HOST_UUID, "hostname": "controller-0",
            "personality": "controller", "administrative": "unlocked",
            "operational": "enabled", "availability": "degraded",
            "subfunctions": "controller,worker,lowlatency",
            "uptime": 15244220, "reboot_needed": False,
            "bm_type": "none", "capabilities": {},
            "location": {"locn": "samsung"},
        }],
        "sysinv_imemorys": {
            HOST_UUID: [{
                "platform_reserved_mib": 10000,
                "platform_total_mib": 16384,
                "platform_used_percent": 90.26,
            }],
        },
        "fm_alarms": [{
            "uuid": ALARM_UUID, "alarm_id": "100.103",
            "severity": "critical",
            "entity_instance_id": "host=controller-0",
            "reason_text": "platform memory threshold exceeded",
            "_sources": ["rest", "cli"],
        }],
        "fm_event_log": [{"event_log_id": "e1", "severity": "warning"}],
        "smapi_nodes": [{
            "id": 1, "name": "controller-0",
            "administrative_state": "unlocked",
            "operational_state": "enabled",
            "availability_status": "available",
        }],
        "system_health": {"System Health": "OK"},
        "software_list": [{"release": "wrcp-24.09.0", "state": "deployed"}],
    }


def _normalize(fixture):
    adapter = StarlingXProviderAdapter(fixture=fixture)
    snapshot = adapter.collect()
    return StarlingXProviderNormalizer().normalize(snapshot)


class TestPlatformMapping:
    def test_platform_created(self):
        assert len(_normalize(_make_fixture()).platforms) == 1

    def test_platform_type_wrcp(self):
        assert _normalize(_make_fixture()).platforms[0].platform_type == PlatformType.WRCP

    def test_platform_version(self):
        assert _normalize(_make_fixture()).platforms[0].version == "24.09"

    def test_platform_metadata_has_starlingx(self):
        assert "starlingx" in _normalize(_make_fixture()).platforms[0].metadata

    def test_canonical_id_not_provider_id(self):
        p = _normalize(_make_fixture()).platforms[0]
        assert p.canonical_id != p.provider_id

    def test_canonical_id_has_wrcp(self):
        assert "wrcp" in _normalize(_make_fixture()).platforms[0].canonical_id.lower()


class TestClusterMapping:
    def test_cluster_created(self):
        assert len(_normalize(_make_fixture()).clusters) == 1

    def test_cluster_type_aio_sx(self):
        assert _normalize(_make_fixture()).clusters[0].cluster_type == ClusterType.WRCP_AIO_SX

    def test_cluster_platform_ref_resolved(self):
        r = _normalize(_make_fixture())
        assert r.clusters[0].platform_ref == r.platforms[0].canonical_id


class TestNodeMapping:
    def test_node_created(self):
        assert len(_normalize(_make_fixture()).nodes) == 1

    def test_node_name(self):
        assert _normalize(_make_fixture()).nodes[0].name == "controller-0"

    def test_node_canonical_id_not_provider_id(self):
        n = _normalize(_make_fixture()).nodes[0]
        assert n.canonical_id != n.provider_id

    def test_node_cluster_ref_resolved(self):
        r = _normalize(_make_fixture())
        assert r.nodes[0].cluster_ref == r.clusters[0].canonical_id

    def test_node_metadata_availability(self):
        sx = _normalize(_make_fixture()).nodes[0].metadata.get("starlingx", {})
        assert sx.get("availability") == "degraded"

    def test_node_metadata_fm_alarms(self):
        sx = _normalize(_make_fixture()).nodes[0].metadata.get("starlingx", {})
        assert len(sx.get("fm_alarms", [])) == 1

    def test_node_metadata_platform_memory(self):
        sx = _normalize(_make_fixture()).nodes[0].metadata.get("starlingx", {})
        assert len(sx.get("platform_memory", [])) == 1

    def test_node_bm_type_none(self):
        sx = _normalize(_make_fixture()).nodes[0].metadata.get("starlingx", {})
        assert sx.get("bm_type") == "none"


class TestNodeNotPhysical:
    def test_no_physical(self):
        assert len(_normalize(_make_fixture()).physicals) == 0

    def test_no_os(self):
        assert len(_normalize(_make_fixture()).os_entities) == 0

    def test_no_workload(self):
        assert len(_normalize(_make_fixture()).workloads) == 0


class TestUnknownPreservation:
    def test_empty_availability_not_forced(self):
        f = _make_fixture()
        f["sysinv_ihosts"][0]["availability"] = ""
        sx = _normalize(f).nodes[0].metadata.get("starlingx", {})
        assert sx.get("availability") == ""

    def test_missing_availability_not_defaulted(self):
        f = _make_fixture()
        del f["sysinv_ihosts"][0]["availability"]
        sx = _normalize(f).nodes[0].metadata.get("starlingx", {})
        assert sx.get("availability") == ""


class TestRelationshipEvidence:
    def test_direct_evidence_preserved(self):
        r = _normalize(_make_fixture())
        assert len(r.relationship_evidence) >= 1
        assert r.relationship_evidence[0].evidence_type.value == "DIRECT"


class TestSourceEvidence:
    def test_platform_source_evidence(self):
        se = _normalize(_make_fixture()).platforms[0].source_evidence
        assert se.provider_type == ProviderType.WRCP

    def test_node_source_evidence(self):
        se = _normalize(_make_fixture()).nodes[0].source_evidence
        assert se is not None


class TestEmptyPayload:
    def test_empty_no_entities(self):
        r = _normalize({})
        assert r.entity_count == 0
        assert r.is_success

    def test_empty_isystems_no_platform(self):
        f = _make_fixture()
        f["sysinv_isystems"] = []
        r = _normalize(f)
        assert len(r.platforms) == 0
        assert len(r.nodes) == 1


class TestNormalizationStatus:
    def test_success(self):
        assert _normalize(_make_fixture()).is_success

    def test_provider_type_wrcp(self):
        assert _normalize(_make_fixture()).provider_type == ProviderType.WRCP