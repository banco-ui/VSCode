"""Tests for StarlingX Provider Adapter — Phase 28E.

Fixture-based tests. No live connection.
"""
from __future__ import annotations

import pytest

from server_manager.models.canonical import ProviderType
from server_manager.orchestrator.models import OrchestrationStatus
from server_manager.providers.base import (
    AdapterCapability, RawProviderSnapshot,
)
from server_manager.providers.starlingx import (
    StarlingXAPICollector, StarlingXCLICollector, StarlingXCLIError,
    StarlingXProviderAdapter, _mask_secrets,
    _parse_fm_alarm_show, _parse_system_health, _parse_software_list,
)

SYSTEM_UUID = "f3c8a1b2-1234-5678-9abc-def012345678"
ALARM_UUID = "fe7e9b1e-4a8e-4f76-9d6a-8c2c1a3b4c5d"
HOST_UUID = "a7aa8774-c383-4641-ba1d-dc13c1dee91d"


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
        }],
        "fm_event_log": [{
            "event_log_id": "event-001", "severity": "warning",
        }],
        "smapi_nodes": [{
            "id": 1, "name": "controller-0",
            "administrative_state": "unlocked",
            "operational_state": "enabled",
            "availability_status": "available",
        }],
        "fm_alarm_detail": {
            ALARM_UUID: {
                "alarm_state": "set", "alarm_type": "equipment",
                "entity_type_id": "host", "probable_cause": "thresholdCrossed",
                "proposed_repair_action": "Increase platform memory",
                "service_affecting": "false", "suppression": "false",
            },
        },
        "system_health": {"System Health": "OK"},
        "software_list": [{"release": "wrcp-24.09.0", "state": "deployed"}],
    }


class TestAdapterIdentity:
    def test_provider_type_is_wrcp(self):
        adapter = StarlingXProviderAdapter()
        assert adapter.provider_type == ProviderType.WRCP

    def test_capabilities_declared(self):
        adapter = StarlingXProviderAdapter()
        caps = adapter.capabilities
        assert AdapterCapability.PLATFORM in caps
        assert AdapterCapability.CLUSTER in caps
        assert AdapterCapability.NODE in caps
        assert AdapterCapability.HEALTH in caps
        assert AdapterCapability.EVENTS in caps

    def test_physical_not_declared(self):
        adapter = StarlingXProviderAdapter()
        assert AdapterCapability.PHYSICAL not in adapter.capabilities

    def test_workload_not_declared(self):
        adapter = StarlingXProviderAdapter()
        assert AdapterCapability.WORKLOAD not in adapter.capabilities


class TestFixtureMode:
    def test_collect_returns_snapshot(self):
        adapter = StarlingXProviderAdapter(fixture=_make_fixture())
        snapshot = adapter.collect()
        assert isinstance(snapshot, RawProviderSnapshot)
        assert snapshot.provider_type == ProviderType.WRCP

    def test_provider_id_from_isystems(self):
        adapter = StarlingXProviderAdapter(fixture=_make_fixture())
        assert adapter.collect().provider_id == SYSTEM_UUID

    def test_payload_has_all_keys(self):
        snapshot = StarlingXProviderAdapter(fixture=_make_fixture()).collect()
        for key in ("sysinv_isystems", "sysinv_ihosts", "sysinv_imemorys",
                     "fm_alarms", "fm_event_log", "smapi_nodes",
                     "system_health", "software_list"):
            assert key in snapshot.payload

    def test_collection_status_success(self):
        adapter = StarlingXProviderAdapter(fixture=_make_fixture())
        assert adapter.collect().collection_status == OrchestrationStatus.SUCCESS

    def test_no_input_returns_failed(self):
        adapter = StarlingXProviderAdapter()
        assert adapter.collect().collection_status == OrchestrationStatus.FAILED


class TestAlarmDeduplication:
    def test_rest_cli_merge_by_uuid(self):
        rest = [{"uuid": "a1", "alarm_id": "100.103", "severity": "critical"}]
        cli = {"a1": {"alarm_state": "set", "alarm_type": "equipment"}}
        merged = StarlingXProviderAdapter._merge_alarm_data(rest, cli)
        assert len(merged) == 1
        assert merged[0]["alarm_state"] == "set"
        assert merged[0]["_sources"] == ["rest", "cli"]

    def test_rest_only(self):
        merged = StarlingXProviderAdapter._merge_alarm_data(
            [{"uuid": "a1"}], {})
        assert merged[0]["_sources"] == ["rest"]

    def test_cli_only(self):
        merged = StarlingXProviderAdapter._merge_alarm_data(
            [], {"a2": {"alarm_state": "set"}})
        assert len(merged) == 1
        assert merged[0]["uuid"] == "a2"
        assert merged[0]["_sources"] == ["cli"]

    def test_no_duplicate(self):
        rest = [{"uuid": "a1", "severity": "critical"}]
        cli = {"a1": {"alarm_state": "set"}}
        merged = StarlingXProviderAdapter._merge_alarm_data(rest, cli)
        assert len(merged) == 1


class TestRelationshipEvidence:
    def test_direct_evidence_for_imemorys(self):
        snapshot = StarlingXProviderAdapter(fixture=_make_fixture()).collect()
        assert len(snapshot.relationship_evidence) >= 1
        ev = snapshot.relationship_evidence[0]
        assert ev.source_entity_ref == HOST_UUID
        assert ev.evidence_type.value == "DIRECT"

    def test_no_name_based_inference(self):
        snapshot = StarlingXProviderAdapter(fixture=_make_fixture()).collect()
        for ev in snapshot.relationship_evidence:
            assert "smapi" not in ev.relationship_type


class TestCLIAllowList:
    def test_allowed_fm_alarm_show(self):
        assert StarlingXCLICollector._is_allowed("fm alarm-show uuid-123")

    def test_allowed_system_health_query(self):
        assert StarlingXCLICollector._is_allowed("system health-query")

    def test_allowed_software_list(self):
        assert StarlingXCLICollector._is_allowed("software list")

    def test_disallowed_reboot(self):
        assert not StarlingXCLICollector._is_allowed("system host-reboot controller-0")

    def test_disallowed_alarm_ack(self):
        assert not StarlingXCLICollector._is_allowed("fm alarm-ack uuid-123")

    def test_disallowed_lock(self):
        assert not StarlingXCLICollector._is_allowed("system host-lock controller-0")


class TestSecretMasking:
    def test_mask_token(self):
        result = _mask_secrets("token: gAAAAABm1234567890abcdefghij")
        assert "gAAAAABm1234567890abcdefghij" not in result

    def test_mask_password(self):
        assert "mysecret123" not in _mask_secrets("password: mysecret123")

    def test_no_mask_normal_text(self):
        assert _mask_secrets("System Health: OK") == "System Health: OK"


class TestParsers:
    def test_parse_fm_alarm_show(self):
        stdout = "| uuid | fe7e9b1e |\n| alarm_id | 100.103 |"
        r = _parse_fm_alarm_show(stdout)
        assert r["uuid"] == "fe7e9b1e"
        assert r["alarm_id"] == "100.103"

    def test_parse_system_health(self):
        r = _parse_system_health("System Health: OK")
        assert r["System Health"] == "OK"

    def test_parse_software_list(self):
        stdout = "| release | state |\n| wrcp-24.09.0 | deployed |"
        r = _parse_software_list(stdout)
        assert len(r) == 1
        assert r[0]["release"] == "wrcp-24.09.0"


class MockResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = ""
    def json(self):
        return self._json


class MockHttpSession:
    def __init__(self, responses):
        self._responses = responses
    def get(self, url, *, headers=None, timeout=None, verify=True):
        return self._responses.get(url, MockResponse(404))


class TestAPICollector:
    def test_collect_success(self):
        b = "http://192.168.204.1"
        r = {
            f"{b}:6385/v1/isystems": MockResponse(200, [{"uuid": SYSTEM_UUID}]),
            f"{b}:6385/v1/ihosts": MockResponse(200, [{"uuid": HOST_UUID, "hostname": "c-0"}]),
            f"{b}:18002/v1/alarms": MockResponse(200, [{"uuid": ALARM_UUID}]),
            f"{b}:18002/v1/event_log": MockResponse(200, []),
            f"{b}:7777/v1/nodes/": MockResponse(200, [{"name": "c-0"}]),
            f"{b}:6385/v1/ihosts/{HOST_UUID}/imemorys": MockResponse(200, [{"platform_reserved_mib": 10000}]),
        }
        c = StarlingXAPICollector("192.168.204.1", MockHttpSession(r))
        payload, errors = c.collect()
        assert "sysinv_isystems" in payload
        assert "sysinv_imemorys" in payload
        assert len(errors) == 0

    def test_auth_expired_401(self):
        b = "http://192.168.204.1"
        r = {
            f"{b}:6385/v1/isystems": MockResponse(401),
            f"{b}:6385/v1/ihosts": MockResponse(200, []),
            f"{b}:18002/v1/alarms": MockResponse(200, []),
            f"{b}:18002/v1/event_log": MockResponse(200, []),
            f"{b}:7777/v1/nodes/": MockResponse(200, []),
        }
        c = StarlingXAPICollector("192.168.204.1", MockHttpSession(r))
        payload, errors = c.collect()
        assert "sysinv_isystems" not in payload
        assert "Auth expired" in errors.get("sysinv_isystems", "")

    def test_partial_collection(self):
        b = "http://192.168.204.1"
        r = {
            f"{b}:6385/v1/isystems": MockResponse(200, []),
            f"{b}:6385/v1/ihosts": MockResponse(500),
            f"{b}:18002/v1/alarms": MockResponse(200, []),
            f"{b}:18002/v1/event_log": MockResponse(200, []),
            f"{b}:7777/v1/nodes/": MockResponse(200, []),
        }
        c = StarlingXAPICollector("192.168.204.1", MockHttpSession(r))
        payload, errors = c.collect()
        assert "sysinv_isystems" in payload
        assert "sysinv_ihosts" in errors


class MockSSHClient:
    def __init__(self, responses):
        self._responses = responses
    def exec_command(self, command, *, timeout=None):
        return self._responses.get(command, (1, "", "Not found"))


class TestCLICollector:
    def test_collect_success(self):
        ssh = MockSSHClient({
            f"fm alarm-show {ALARM_UUID}": (0, f"| uuid | {ALARM_UUID} |\n| alarm_state | set |", ""),
            "system health-query": (0, "System Health: OK", ""),
            "software list": (0, "| release | state |\n| wrcp-24.09.0 | deployed |", ""),
        })
        c = StarlingXCLICollector(ssh)
        payload, errors = c.collect([ALARM_UUID])
        assert ALARM_UUID in payload["fm_alarm_detail"]
        assert len(errors) == 0

    def test_cli_failure_nonzero_exit(self):
        ssh = MockSSHClient({
            "system health-query": (1, "", "Connection refused"),
            "software list": (0, "| release | state |\n| wrcp-24.09.0 | deployed |", ""),
        })
        c = StarlingXCLICollector(ssh)
        payload, errors = c.collect()
        assert "system_health_query" in errors
        assert "software_list" in payload

    def test_empty_output_not_error(self):
        ssh = MockSSHClient({
            "system health-query": (0, "", ""),
            "software list": (0, "", ""),
        })
        c = StarlingXCLICollector(ssh)
        _, errors = c.collect()
        assert "system_health_query" not in errors

    def test_disallowed_raises(self):
        c = StarlingXCLICollector(MockSSHClient({}))
        with pytest.raises(StarlingXCLIError, match="not in allow-list"):
            c._exec("system host-reboot controller-0")


class TestPartialCollection:
    def test_partial_status_with_errors(self):
        f = _make_fixture()
        f["errors"] = {"fm_alarms": "Connection refused"}
        assert StarlingXProviderAdapter(fixture=f).collect().collection_status == OrchestrationStatus.PARTIAL

    def test_all_failed_status(self):
        f = {"errors": {"sysinv_isystems": "fail", "sysinv_ihosts": "fail",
                         "fm_alarms": "fail", "fm_event_log": "fail"}}
        assert StarlingXProviderAdapter(fixture=f).collect().collection_status == OrchestrationStatus.FAILED


class TestCollectSafe:
    def test_collect_safe_with_fixture(self):
        a = StarlingXProviderAdapter(fixture=_make_fixture())
        assert a.collect_safe().provider_type == ProviderType.WRCP

    def test_collect_safe_no_input(self):
        assert StarlingXProviderAdapter().collect_safe().collection_status == OrchestrationStatus.FAILED
