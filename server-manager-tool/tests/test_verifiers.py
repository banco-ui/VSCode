"""Tests for Verifiers (Phase 4)."""
import pytest
from server_manager.verifiers.base import (
    SourceEvidence, FieldResult, VerificationResult,
)
from server_manager.verifiers.comparators import FieldComparator
from server_manager.verifiers.hardware_verifier import HardwareVerifier
from server_manager.verifiers.os_verifier import OSVerifier
from server_manager.verifiers.runtime_verifier import RuntimeVerifier
from server_manager.models.enums import (
    VerificationStatus, Confidence, HealthStatus,
)
from server_manager.models.inventory import (
    ServerInventory, Hardware, CPU, Memory, OS, Identity,
)


class TestSourceEvidence:
    def test_default(self):
        ev = SourceEvidence(source="redfish", field_path="cpu.count")
        assert ev.source == "redfish"
        assert ev.available is True

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            SourceEvidence(source="redfish", field_path="x", extra="bad")


class TestFieldComparator:
    def test_no_evidence(self):
        result = FieldComparator.compare("cpu.count", [])
        assert result.status == VerificationStatus.UNAVAILABLE
        assert result.confidence == Confidence.NONE

    def test_single_source(self):
        ev = SourceEvidence(source="redfish", field_path="cpu.count", value=2)
        result = FieldComparator.compare("cpu.count", [ev])
        assert result.status == VerificationStatus.SINGLE_SOURCE
        assert result.confidence == Confidence.MEDIUM
        assert result.canonical_value == 2

    def test_all_agree(self):
        ev1 = SourceEvidence(source="redfish", field_path="cpu.count", value=2)
        ev2 = SourceEvidence(source="ssh", field_path="cpu.count", value=2)
        result = FieldComparator.compare("cpu.count", [ev1, ev2])
        assert result.status == VerificationStatus.VERIFIED
        assert result.confidence == Confidence.HIGH
        assert result.canonical_value == 2

    def test_discrepancy(self):
        ev1 = SourceEvidence(source="redfish", field_path="cpu.count", value=2)
        ev2 = SourceEvidence(source="ssh", field_path="cpu.count", value=4)
        result = FieldComparator.compare("cpu.count", [ev1, ev2])
        assert result.status == VerificationStatus.DISCREPANCY
        assert result.confidence == Confidence.LOW
        assert result.canonical_value == 2  # Redfish priority

    def test_numeric_tolerance(self):
        ev1 = SourceEvidence(source="redfish", field_path="mem.total", value=256.0)
        ev2 = SourceEvidence(source="ssh", field_path="mem.total", value=256.005)
        result = FieldComparator.compare("mem.total", [ev1, ev2])
        assert result.status == VerificationStatus.VERIFIED

    def test_string_case_insensitive(self):
        ev1 = SourceEvidence(source="redfish", field_path="os", value="Ubuntu")
        ev2 = SourceEvidence(source="ssh", field_path="os", value="ubuntu")
        result = FieldComparator.compare("os", [ev1, ev2])
        assert result.status == VerificationStatus.VERIFIED

    def test_unavailable_evidence_filtered(self):
        ev1 = SourceEvidence(source="redfish", field_path="x", value=1, available=True)
        ev2 = SourceEvidence(source="ssh", field_path="x", value=None, available=False)
        result = FieldComparator.compare("x", [ev1, ev2])
        assert result.status == VerificationStatus.SINGLE_SOURCE


class TestVerificationResult:
    def test_counts(self):
        result = VerificationResult(field_results=[
            FieldResult(field_path="a", status=VerificationStatus.VERIFIED),
            FieldResult(field_path="b", status=VerificationStatus.VERIFIED),
            FieldResult(field_path="c", status=VerificationStatus.DISCREPANCY),
            FieldResult(field_path="d", status=VerificationStatus.SINGLE_SOURCE),
            FieldResult(field_path="e", status=VerificationStatus.PARTIAL),
            FieldResult(field_path="f", status=VerificationStatus.UNAVAILABLE),
        ])
        assert result.total_fields == 6
        assert result.verified_count == 2
        assert result.discrepancy_count == 1
        assert result.single_source_count == 1
        assert result.partial_count == 1
        assert result.unavailable_count == 1

    def test_get_field(self):
        result = VerificationResult(field_results=[
            FieldResult(field_path="cpu.count", status=VerificationStatus.VERIFIED),
        ])
        fr = result.get_field("cpu.count")
        assert fr is not None
        assert fr.status == VerificationStatus.VERIFIED
        assert result.get_field("nonexistent") is None


class TestHardwareVerifier:
    def test_verify_single_source(self):
        inv = ServerInventory(hardware=Hardware(cpu=CPU(count=2, total_cores=48)))
        verifier = HardwareVerifier()
        result = verifier.verify({"redfish": inv})
        assert result.total_fields > 0
        # Single source fields should be SINGLE_SOURCE
        assert result.single_source_count > 0

    def test_verify_matching_sources(self):
        inv1 = ServerInventory(hardware=Hardware(cpu=CPU(count=2, total_cores=48, total_threads=96)))
        inv2 = ServerInventory(hardware=Hardware(cpu=CPU(count=2, total_cores=48, total_threads=96)))
        verifier = HardwareVerifier()
        result = verifier.verify({"redfish": inv1, "ssh": inv2})
        assert result.verified_count > 0
        assert result.discrepancy_count == 0

    def test_verify_discrepancy(self):
        inv1 = ServerInventory(hardware=Hardware(cpu=CPU(count=2, total_cores=48)))
        inv2 = ServerInventory(hardware=Hardware(cpu=CPU(count=2, total_cores=24)))
        verifier = HardwareVerifier()
        result = verifier.verify({"redfish": inv1, "ssh": inv2})
        assert result.discrepancy_count > 0


class TestOSVerifier:
    def test_verify_matching(self):
        inv1 = ServerInventory(os=OS(distribution="Ubuntu", kernel="5.15.0"))
        inv2 = ServerInventory(os=OS(distribution="Ubuntu", kernel="5.15.0"))
        verifier = OSVerifier()
        result = verifier.verify({"redfish": inv1, "ssh": inv2})
        assert result.verified_count > 0

    def test_verify_discrepancy(self):
        inv1 = ServerInventory(os=OS(distribution="Ubuntu"))
        inv2 = ServerInventory(os=OS(distribution="CentOS"))
        verifier = OSVerifier()
        result = verifier.verify({"redfish": inv1, "ssh": inv2})
        assert result.discrepancy_count > 0


class TestRuntimeVerifier:
    def test_verify_matching(self):
        from server_manager.models.inventory import Containers, DockerInfo
        inv1 = ServerInventory(containers=Containers(docker=DockerInfo(installed=True, running_containers=3)))
        inv2 = ServerInventory(containers=Containers(docker=DockerInfo(installed=True, running_containers=3)))
        verifier = RuntimeVerifier()
        result = verifier.verify({"redfish": inv1, "ssh": inv2})
        assert result.verified_count > 0

    def test_verify_discrepancy(self):
        from server_manager.models.inventory import Containers, DockerInfo
        inv1 = ServerInventory(containers=Containers(docker=DockerInfo(installed=True)))
        inv2 = ServerInventory(containers=Containers(docker=DockerInfo(installed=False)))
        verifier = RuntimeVerifier()
        result = verifier.verify({"redfish": inv1, "ssh": inv2})
        assert result.discrepancy_count > 0
