"""Tests for Domain Models (Phase 1)."""
import pytest
from server_manager.models.enums import (
    HealthStatus,
    ComputePotential,
    ComputeEligibility,
    VerificationStatus,
    Confidence,
    Vendor,
    ControllerType,
    Protocol,
    MediaType,
    NetworkSpeed,
    DataClass,
    ServerLifecycle,
)
from server_manager.models.inventory import (
    ServerInventory,
    Identity,
    CPU,
    CPUProcessor,
    Memory,
    MemoryModule,
    GPU,
    GPUDevice,
    Storage,
    PhysicalDisk,
    Network,
    NetworkAdapter,
    Hardware,
    Management,
    OS,
    Health,
    Workload,
    PowerThermal,
    PSU,
    PowerInfo,
    TemperatureReading,
    FanReading,
    ThermalInfo,
    Containers,
    DockerInfo,
    KubernetesInfo,
    Virtualization,
    DevelopmentEnvironment,
    Compute,
    ComputeCapability,
    Topology,
)


class TestEnums:
    """Test enum values and string conversion."""

    def test_health_status_values(self):
        assert HealthStatus.OK == "OK"
        assert HealthStatus.WARNING == "Warning"
        assert HealthStatus.CRITICAL == "Critical"
        assert HealthStatus.UNKNOWN == "Unknown"

    def test_compute_potential_values(self):
        assert ComputePotential.VERY_HIGH == "VERY_HIGH"
        assert ComputePotential.HIGH == "HIGH"
        assert ComputePotential.MEDIUM == "MEDIUM"
        assert ComputePotential.LOW == "LOW"

    def test_compute_eligibility_values(self):
        assert ComputeEligibility.PRODUCTION == "PRODUCTION"
        assert ComputeEligibility.CANDIDATE == "CANDIDATE"
        assert ComputeEligibility.COMPUTE_ELIGIBLE == "COMPUTE_ELIGIBLE"
        assert ComputeEligibility.UNKNOWN == "UNKNOWN"

    def test_verification_status_values(self):
        assert VerificationStatus.VERIFIED == "VERIFIED"
        assert VerificationStatus.SINGLE_SOURCE == "SINGLE_SOURCE"
        assert VerificationStatus.DISCREPANCY == "DISCREPANCY"
        assert VerificationStatus.PARTIAL == "PARTIAL"
        assert VerificationStatus.UNAVAILABLE == "UNAVAILABLE"

    def test_confidence_values(self):
        assert Confidence.HIGH == "HIGH"
        assert Confidence.MEDIUM == "MEDIUM"
        assert Confidence.LOW == "LOW"
        assert Confidence.NONE == "NONE"

    def test_vendor_values(self):
        assert Vendor.Dell == "Dell"
        assert Vendor.HPE == "HPE"
        assert Vendor.Unknown == "Unknown"

    def test_controller_type_values(self):
        assert ControllerType.iDRAC == "iDRAC"
        assert ControllerType.iLO == "iLO"
        assert ControllerType.Unknown == "Unknown"

    def test_protocol_values(self):
        assert Protocol.Redfish == "Redfish"
        assert Protocol.SSH == "SSH"
        assert Protocol.IPMI == "IPMI"
        assert Protocol.SNMP == "SNMP"

    def test_media_type_values(self):
        assert MediaType.SSD == "SSD"
        assert MediaType.HDD == "HDD"
        assert MediaType.NVMe == "NVMe"
        assert MediaType.Unknown == "Unknown"

    def test_network_speed_values(self):
        assert NetworkSpeed.GbE_1 == "1GbE"
        assert NetworkSpeed.GbE_10 == "10GbE"
        assert NetworkSpeed.GbE_25 == "25GbE"
        assert NetworkSpeed.GbE_40 == "40GbE"
        assert NetworkSpeed.GbE_100 == "100GbE"
        assert NetworkSpeed.Unknown == "Unknown"

    def test_server_lifecycle_values(self):
        assert ServerLifecycle.ACTIVE == "ACTIVE"
        assert ServerLifecycle.MAINTENANCE == "MAINTENANCE"
        assert ServerLifecycle.UNREACHABLE == "UNREACHABLE"
        assert ServerLifecycle.DECOMMISSIONED == "DECOMMISSIONED"
        assert ServerLifecycle.PROVISIONING == "PROVISIONING"


class TestServerInventory:
    """Test ServerInventory model."""

    def test_default_server_inventory(self):
        inv = ServerInventory()
        assert inv.schema_version == "1.0"
        assert inv.identity.server_id == ""
        assert inv.identity.vendor == Vendor.Unknown
        assert inv.hardware.cpu.count == 0
        assert inv.hardware.memory.total_gb == 0.0
        assert inv.health.system == HealthStatus.UNKNOWN

    def test_optional_capacity_serialization(self):
        """P1-RF.18: Missing capacity serializes as null; real zero as 0.0."""
        disk = PhysicalDisk(name="D0")
        assert disk.model_dump()["capacity_gb"] is None
        disk_zero = PhysicalDisk(name="D1", capacity_gb=0.0)
        assert disk_zero.model_dump()["capacity_gb"] == 0.0

    def test_inventory_with_cpu(self):
        inv = ServerInventory(
            hardware=Hardware(
                cpu=CPU(
                    count=2,
                    total_cores=48,
                    total_threads=96,
                    processors=[
                        CPUProcessor(model="Intel Xeon Gold 6248R", cores=24, threads=48),
                        CPUProcessor(model="Intel Xeon Gold 6248R", cores=24, threads=48),
                    ],
                )
            )
        )
        assert inv.hardware.cpu.count == 2
        assert inv.hardware.cpu.total_cores == 48
        assert len(inv.hardware.cpu.processors) == 2

    def test_inventory_with_memory(self):
        inv = ServerInventory(
            hardware=Hardware(
                memory=Memory(
                    total_gb=256.0,
                    dimm_count=16,
                    populated_slots=16,
                    empty_slots=0,
                    modules=[
                        MemoryModule(slot="A1", capacity_gb=16.0, type="DDR4", speed_mhz=3200),
                    ] * 16,
                )
            )
        )
        assert inv.hardware.memory.total_gb == 256.0
        assert inv.hardware.memory.dimm_count == 16

    def test_inventory_with_storage(self):
        inv = ServerInventory(
            hardware=Hardware(
                storage=Storage(
                    physical_disks=[
                        PhysicalDisk(name="Disk 0", capacity_gb=960.0, media_type=MediaType.SSD),
                        PhysicalDisk(name="Disk 1", capacity_gb=1920.0, media_type=MediaType.NVMe),
                    ],
                )
            )
        )
        assert len(inv.hardware.storage.physical_disks) == 2

    def test_inventory_with_gpu(self):
        inv = ServerInventory(
            hardware=Hardware(
                gpu=GPU(
                    dedicated_compute_gpu=True,
                    count=2,
                    devices=[
                        GPUDevice(vendor="NVIDIA", model="A100", vram_gb=80.0),
                        GPUDevice(vendor="NVIDIA", model="A100", vram_gb=80.0),
                    ],
                )
            )
        )
        assert inv.hardware.gpu.count == 2
        assert inv.hardware.gpu.dedicated_compute_gpu is True

    def test_inventory_extra_forbid(self):
        """Extra fields should be rejected."""
        with pytest.raises(Exception):
            ServerInventory(extra_field="not_allowed")

    def test_inventory_serialization(self):
        inv = ServerInventory(
            identity=Identity(server_id="R750-001", vendor=Vendor.Dell, model="PowerEdge R750"),
        )
        json_str = inv.model_dump_json()
        restored = ServerInventory.model_validate_json(json_str)
        assert restored.identity.server_id == "R750-001"
        assert restored.identity.vendor == Vendor.Dell

    def test_inventory_with_management(self):
        inv = ServerInventory(
            management=Management(
                vendor=Vendor.Dell,
                controller=ControllerType.iDRAC,
                firmware_version="7.10.30",
            )
        )
        assert inv.management.vendor == Vendor.Dell
        assert inv.management.controller == ControllerType.iDRAC

    def test_inventory_with_os(self):
        inv = ServerInventory(
            os=OS(
                distribution="Ubuntu",
                version="22.04 LTS",
                kernel="5.15.0-91-generic",
                architecture="x86_64",
                hostname="server-001",
            )
        )
        assert inv.os.distribution == "Ubuntu"
        assert inv.os.kernel == "5.15.0-91-generic"

    def test_inventory_with_power_thermal(self):
        inv = ServerInventory(
            power_thermal=PowerThermal(
                power=PowerInfo(
                    current_watts=450.0,
                    capacity_watts=1100.0,
                    psus=[
                        PSU(name="PSU1", capacity_w=550.0, health=HealthStatus.OK),
                        PSU(name="PSU2", capacity_w=550.0, health=HealthStatus.OK),
                    ],
                ),
                thermal=ThermalInfo(
                    temperatures=[
                        TemperatureReading(name="CPU1 Temp", reading_c=45.0, health=HealthStatus.OK),
                    ],
                    fans=[
                        FanReading(name="Fan1", reading_rpm=5000, health=HealthStatus.OK),
                    ],
                ),
            )
        )
        assert inv.power_thermal.power.current_watts == 450.0
        assert len(inv.power_thermal.power.psus) == 2

    def test_inventory_with_health(self):
        inv = ServerInventory(
            health=Health(
                system=HealthStatus.OK,
                cpu=HealthStatus.OK,
                memory=HealthStatus.OK,
                storage=HealthStatus.OK,
                thermal=HealthStatus.WARNING,
                network=HealthStatus.OK,
                psu=HealthStatus.OK,
                fan=HealthStatus.OK,
            )
        )
        assert inv.health.system == HealthStatus.OK
        assert inv.health.thermal == HealthStatus.WARNING

    def test_inventory_with_compute(self):
        inv = ServerInventory(
            compute=Compute(
                potential=ComputePotential.HIGH,
                eligibility=ComputeEligibility.CANDIDATE,
                reason="High CPU and GPU resources available",
            )
        )
        assert inv.compute.potential == ComputePotential.HIGH
        assert inv.compute.eligibility == ComputeEligibility.CANDIDATE

    def test_inventory_with_containers(self):
        inv = ServerInventory(
            containers=Containers(
                docker=DockerInfo(installed=True, version="24.0.7", running_containers=5),
                kubernetes=KubernetesInfo(installed=False),
            )
        )
        assert inv.containers.docker.installed is True
        assert inv.containers.docker.running_containers == 5
        assert inv.containers.kubernetes.installed is False

    def test_inventory_with_development_environment(self):
        inv = ServerInventory(
            development_environment=DevelopmentEnvironment(
                git_installed=True,
                python3_installed=True,
                node_installed=True,
                pm2_installed=True,
            )
        )
        assert inv.development_environment.git_installed is True
        assert inv.development_environment.python3_installed is True

    def test_identity_extra_forbid(self):
        with pytest.raises(Exception):
            Identity(extra_field="bad")

    def test_cpu_extra_forbid(self):
        with pytest.raises(Exception):
            CPU(extra_field="bad")

    def test_all_models_extra_forbid(self):
        """All schema models should reject extra fields."""
        models_to_test = [
            Identity, Topology, CPU, CPUProcessor, Memory, MemoryModule,
            GPU, GPUDevice, Storage, PhysicalDisk, Network, NetworkAdapter,
            Hardware, Management, OS, Virtualization, DockerInfo, KubernetesInfo,
            Containers, DevelopmentEnvironment, Compute, ComputeCapability,
            Health, Workload, PSU, PowerInfo, TemperatureReading, FanReading,
            ThermalInfo, PowerThermal,
        ]
        for model in models_to_test:
            with pytest.raises(Exception):
                model(extra_field="should_fail")

    # ── P1 Regression Tests ──────────────────────────────────────────

    def test_meta_alias_serialization(self):
        """P1: Assert _meta is the canonical serialized JSON key.

        Protects the P0 fix (alias="_meta", populate_by_name=True)
        from regression.
        """
        import json as _json

        inv = ServerInventory(
            identity=Identity(server_id="R750-001", vendor=Vendor.Dell),
        )

        # by_alias=True → "_meta" is the external key
        alias_dump = inv.model_dump(by_alias=True)
        assert "_meta" in alias_dump
        assert "meta" not in alias_dump

        # without by_alias → "meta" is the Python field name
        internal_dump = inv.model_dump()
        assert "meta" in internal_dump
        assert "_meta" not in internal_dump

        # JSON with by_alias → "_meta" key present
        alias_json = inv.model_dump_json(by_alias=True)
        parsed = _json.loads(alias_json)
        assert "_meta" in parsed
        assert "meta" not in parsed

        # JSON without by_alias → "meta" key (not "_meta")
        internal_json = inv.model_dump_json()
        parsed_internal = _json.loads(internal_json)
        assert "meta" in parsed_internal
        assert "_meta" not in parsed_internal

    def test_meta_alias_round_trip(self):
        """P1: Round-trip serialization preserves _meta alias contract."""
        inv = ServerInventory(
            identity=Identity(server_id="R750-001", vendor=Vendor.Dell),
        )

        # Serialize with by_alias, deserialize — meta intact
        json_str = inv.model_dump_json(by_alias=True)
        restored = ServerInventory.model_validate_json(json_str)
        assert restored.meta.schema_version == "1.0"

        # Serialize without by_alias, deserialize — meta intact
        json_str2 = inv.model_dump_json()
        restored2 = ServerInventory.model_validate_json(json_str2)
        assert restored2.meta.schema_version == "1.0"

        # Both _meta and meta keys accepted as input (populate_by_name)
        dict_alias = inv.model_dump(by_alias=True)
        restored3 = ServerInventory.model_validate(dict_alias)
        assert restored3.meta.schema_version == "1.0"

        dict_internal = inv.model_dump()
        restored4 = ServerInventory.model_validate(dict_internal)
        assert restored4.meta.schema_version == "1.0"


