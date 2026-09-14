"""Tests for Orchestrator (Phase 5)."""
import pytest
from server_manager.orchestrator.models import (
    OrchestrationStatus, PipelineStage, ErrorCategory,
    SourceResult, OrchestrationResult,
)
from server_manager.orchestrator.orchestrator import Orchestrator
from server_manager.models.inventory import (
    ServerInventory, Hardware, CPU, Memory, OS, Identity, Health,
)
from server_manager.models.enums import HealthStatus, Vendor


class TestOrchestrationModels:
    def test_status_values(self):
        assert OrchestrationStatus.SUCCESS == "SUCCESS"
        assert OrchestrationStatus.PARTIAL == "PARTIAL"
        assert OrchestrationStatus.FAILED == "FAILED"
        assert OrchestrationStatus.SKIPPED == "SKIPPED"

    def test_pipeline_stages(self):
        assert PipelineStage.COLLECTION == "COLLECTION"
        assert PipelineStage.NORMALIZATION == "NORMALIZATION"
        assert PipelineStage.VERIFICATION == "VERIFICATION"
        assert PipelineStage.COMPLETE == "COMPLETE"

    def test_error_category_from_exception(self):
        assert ErrorCategory.from_exception(ConnectionError("refused")) == ErrorCategory.CONNECTION_ERROR
        assert ErrorCategory.from_exception(PermissionError("denied")) == ErrorCategory.AUTHENTICATION_ERROR
        assert ErrorCategory.from_exception(TimeoutError("timed out")) == ErrorCategory.TIMEOUT
        assert ErrorCategory.from_exception(ValueError("parse error")) == ErrorCategory.PARSING_ERROR

    def test_error_category_from_error_string(self):
        assert ErrorCategory.from_error_string("connection refused") == ErrorCategory.CONNECTION_ERROR
        assert ErrorCategory.from_error_string("authentication failed") == ErrorCategory.AUTHENTICATION_ERROR
        assert ErrorCategory.from_error_string("timeout reached") == ErrorCategory.TIMEOUT

    def test_source_result_default(self):
        sr = SourceResult(source="redfish")
        assert sr.collection_success is False
        assert sr.normalization_success is None
        assert sr.errors == []

    def test_orchestration_result_default(self):
        result = OrchestrationResult(run_id="run-1", server_id="srv-1")
        assert result.status == OrchestrationStatus.FAILED
        assert result.source_results == []
        assert result.canonical_inventory is None

    def test_source_result_extra_forbid(self):
        with pytest.raises(Exception):
            SourceResult(source="x", extra="bad")

    def test_orchestration_result_extra_forbid(self):
        with pytest.raises(Exception):
            OrchestrationResult(run_id="r", server_id="s", extra="bad")


class TestOrchestrator:
    def _make_inventory(self, cpu_count=2, cores=48, distro="Ubuntu"):
        return ServerInventory(
            identity=Identity(server_id="R750-001", vendor=Vendor.Dell, hostname="srv-1"),
            hardware=Hardware(
                cpu=CPU(count=cpu_count, total_cores=cores, total_threads=cores * 2),
                memory=Memory(total_gb=256.0),
            ),
            os=OS(distribution=distro, kernel="5.15.0", hostname="srv-1"),
        )

    def test_run_from_inventories_success(self):
        inv1 = self._make_inventory()
        inv2 = self._make_inventory()
        orch = Orchestrator()
        result = orch.run_from_inventories("R750-001", {"redfish": inv1, "ssh": inv2})

        assert result.status == OrchestrationStatus.SUCCESS
        assert result.canonical_source == "redfish"
        assert result.canonical_inventory is not None
        assert result.verification is not None
        assert result.run_id.startswith("run-")

    def test_run_from_inventories_single_source(self):
        inv = self._make_inventory()
        orch = Orchestrator()
        result = orch.run_from_inventories("R750-001", {"ssh": inv})

        assert result.status == OrchestrationStatus.SUCCESS
        assert result.canonical_source == "ssh"
        assert "Single source" in " ".join(result.warnings)

    def test_run_from_inventories_discrepancy(self):
        inv1 = self._make_inventory(cpu_count=2, cores=48)
        inv2 = self._make_inventory(cpu_count=2, cores=24)
        orch = Orchestrator()
        result = orch.run_from_inventories("R750-001", {"redfish": inv1, "ssh": inv2})

        assert result.verification is not None
        assert result.verification.discrepancy_count > 0
        assert result.verification_success is False

    def test_run_with_collectors_success(self):
        def coll1():
            return {"source": "redfish", "system": {"Manufacturer": "Dell Inc."}}

        def coll2():
            return {"source": "ssh", "os": {"hostname": "srv-1"}}

        def norm1(raw):
            return self._make_inventory()

        def norm2(raw):
            return self._make_inventory()

        orch = Orchestrator()
        result = orch.run("R750-001", {"redfish": coll1, "ssh": coll2}, {"redfish": norm1, "ssh": norm2})

        assert result.status == OrchestrationStatus.SUCCESS
        assert len(result.source_results) == 2

    def test_run_with_collector_failure(self):
        def coll_fail():
            raise ConnectionError("Connection refused")

        def coll_ok():
            return {"source": "ssh"}

        def norm_ok(raw):
            return self._make_inventory()

        orch = Orchestrator()
        result = orch.run("R750-001", {"redfish": coll_fail, "ssh": coll_ok}, {"ssh": norm_ok})

        assert result.status == OrchestrationStatus.PARTIAL
        assert len(result.source_results) == 2
        redfish_sr = [sr for sr in result.source_results if sr.source == "redfish"][0]
        assert redfish_sr.collection_success is False
        assert len(redfish_sr.errors) > 0

    def test_run_all_fail(self):
        def coll_fail():
            raise ConnectionError("failed")

        orch = Orchestrator()
        result = orch.run("R750-001", {"redfish": coll_fail}, {})

        assert result.status == OrchestrationStatus.FAILED
        assert result.canonical_inventory is None

    def test_run_id_is_unique(self):
        inv = self._make_inventory()
        orch = Orchestrator()
        r1 = orch.run_from_inventories("srv", {"ssh": inv})
        r2 = orch.run_from_inventories("srv", {"ssh": inv})
        assert r1.run_id != r2.run_id

    def test_canonical_selection_priority(self):
        inv1 = self._make_inventory(distro="Ubuntu")
        inv2 = self._make_inventory(distro="Ubuntu")
        inv3 = self._make_inventory(distro="Ubuntu")
        orch = Orchestrator()
        result = orch.run_from_inventories("srv", {"snmp": inv3, "ssh": inv2, "redfish": inv1})
        assert result.canonical_source == "redfish"

    def test_duration_tracked(self):
        inv = self._make_inventory()
        orch = Orchestrator()
        result = orch.run_from_inventories("srv", {"ssh": inv})
        assert result.total_duration_ms >= 0
        assert result.started_at is not None
        assert result.completed_at is not None
