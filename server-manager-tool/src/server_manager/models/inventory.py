"""Schema v1.0 — ServerInventory Domain Model (Phase 0-1).

17 areas, FROZEN. All credentials excluded.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .enums import (
    ComputeEligibility,
    ComputePotential,
    Confidence,
    ControllerType,
    DataClass,
    HealthStatus,
    MediaType,
    NetworkSpeed,
    Protocol,
    ServerLifecycle,
    Vendor,
    VerificationStatus,
)

# ── Default factory helpers ──────────────────────────────────────────


def _now() -> Optional[str]:
    """Placeholder for ISO 8601 timestamp; defaults to None."""
    return None


# ── 1. Identity ───────────────────────────────────────────────────────


class Identity(BaseModel):
    server_id: str = ""
    vendor: Vendor = Vendor.Unknown
    model: str = ""
    hostname: str = ""
    hostname_management: Optional[str] = None
    serial_number: Optional[str] = None
    service_tag: Optional[str] = None
    bios_version: Optional[str] = None
    bios_date: Optional[str] = None
    uuid_present: bool = False
    asset_tag: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── 2. Topology ────────────────────────────────────────────────────────


class Topology(BaseModel):
    physical_servers: int = 1
    computer_systems: int = 1
    chassis: int = 1
    multi_node: bool = False

    model_config = {"extra": "forbid"}


# ── 3. CPU ─────────────────────────────────────────────────────────────


class CPUProcessor(BaseModel):
    model: str = ""
    cores: int = 0
    threads: int = 0
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class CPU(BaseModel):
    count: int = 0
    total_cores: int = 0
    total_threads: int = 0
    processors: list[CPUProcessor] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


# ── 4. Memory ─────────────────────────────────────────────────────────


class MemoryModule(BaseModel):
    slot: str = ""
    capacity_gb: Optional[float] = None  # P1-RF.18: None = missing/unparseable; 0.0 = real zero
    type: str = ""
    speed_mhz: int = 0
    manufacturer: str = ""
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class Memory(BaseModel):
    total_gb: float = 0.0
    dimm_count: int = 0
    populated_slots: int = 0
    empty_slots: int = 0
    modules: list[MemoryModule] = Field(default_factory=list)
    os_reported: Optional[float] = None

    model_config = {"extra": "forbid"}


# ── 5. GPU ─────────────────────────────────────────────────────────────


class GPUDevice(BaseModel):
    vendor: str = ""
    model: str = ""
    vram_gb: Optional[float] = None
    driver_version: Optional[str] = None
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class GPU(BaseModel):
    dedicated_compute_gpu: bool = False
    count: int = 0
    devices: list[GPUDevice] = Field(default_factory=list)
    integrated_gpu: bool = False

    model_config = {"extra": "forbid"}


# ── 6. Storage ────────────────────────────────────────────────────────


class StorageController(BaseModel):
    name: str = ""
    model: str = ""
    health: HealthStatus = HealthStatus.UNKNOWN
    raid_support: bool = False

    model_config = {"extra": "forbid"}


class PhysicalDisk(BaseModel):
    name: str = ""
    model: str = ""
    capacity_gb: Optional[float] = None  # P1-RF.18: None = missing/unparseable; 0.0 = real zero
    media_type: MediaType = MediaType.Unknown
    protocol: Optional[str] = None
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class VirtualDisk(BaseModel):
    name: str = ""
    raid_type: Optional[str] = None
    capacity_gb: Optional[float] = None  # P1-RF.18: None = missing/unparseable; 0.0 = real zero
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class Storage(BaseModel):
    controllers: list[StorageController] = Field(default_factory=list)
    physical_disks: list[PhysicalDisk] = Field(default_factory=list)
    virtual_disks: list[VirtualDisk] = Field(default_factory=list)
    no_hardware_raid: bool = False

    model_config = {"extra": "forbid"}


# ── 7. Network ────────────────────────────────────────────────────────


class NetworkAdapter(BaseModel):
    vendor: str = ""
    model: str = ""
    speed: NetworkSpeed = NetworkSpeed.Unknown
    ports: int = 0
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class Network(BaseModel):
    adapter_count: int = 0
    adapters: list[NetworkAdapter] = Field(default_factory=list)
    highest_link_speed: NetworkSpeed = NetworkSpeed.Unknown
    active_interfaces: int = 0

    model_config = {"extra": "forbid"}


# ── 8. Hardware (aggregate) ───────────────────────────────────────────


class Hardware(BaseModel):
    cpu: CPU = Field(default_factory=CPU)
    memory: Memory = Field(default_factory=Memory)
    gpu: GPU = Field(default_factory=GPU)
    storage: Storage = Field(default_factory=Storage)
    network: Network = Field(default_factory=Network)

    model_config = {"extra": "forbid"}


# ── 9. Management ──────────────────────────────────────────────────────


class RedfishInfo(BaseModel):
    reachable: bool = False
    api_version: Optional[str] = None
    endpoint: Optional[str] = None

    model_config = {"extra": "forbid"}


class IPMIInfo(BaseModel):
    available: bool = False
    tool_installed: bool = False

    model_config = {"extra": "forbid"}


class SSHInfo(BaseModel):
    available: bool = False
    port: int = 22

    model_config = {"extra": "forbid"}


class Management(BaseModel):
    vendor: Vendor = Vendor.Unknown
    controller: ControllerType = ControllerType.Unknown
    controller_model: Optional[str] = None
    firmware_version: Optional[str] = None
    protocols: list[Protocol] = Field(default_factory=list)
    redfish: RedfishInfo = Field(default_factory=RedfishInfo)
    ipmi: IPMIInfo = Field(default_factory=IPMIInfo)
    ssh: SSHInfo = Field(default_factory=SSHInfo)

    model_config = {"extra": "forbid"}


# ── 10. OS ─────────────────────────────────────────────────────────────


class OS(BaseModel):
    distribution: str = ""
    version: str = ""
    kernel: str = ""
    architecture: str = ""
    virtualization: Optional[str] = None
    hostname: str = ""
    uptime: Optional[str] = None
    platform: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── 11. Virtualization ────────────────────────────────────────────────


class Virtualization(BaseModel):
    type: Optional[str] = None
    kvm_modules_loaded: bool = False
    virsh_available: bool = False
    vms: int = 0

    model_config = {"extra": "forbid"}


class DockerInfo(BaseModel):
    installed: bool = False
    version: Optional[str] = None
    running_containers: int = 0

    model_config = {"extra": "forbid"}


class KubernetesInfo(BaseModel):
    installed: bool = False
    version: Optional[str] = None
    nodes: int = 0
    pods: int = 0
    platform: Optional[str] = None

    model_config = {"extra": "forbid"}


class Containers(BaseModel):
    docker: DockerInfo = Field(default_factory=DockerInfo)
    kubernetes: KubernetesInfo = Field(default_factory=KubernetesInfo)

    model_config = {"extra": "forbid"}


# ── 12. DevelopmentEnvironment ────────────────────────────────────────


class DevelopmentEnvironment(BaseModel):
    git_installed: bool = False
    python3_installed: bool = False
    node_installed: bool = False
    npm_installed: bool = False
    gcc_installed: bool = False
    gpp_installed: bool = False
    pm2_installed: bool = False
    vscode_server_running: bool = False

    model_config = {"extra": "forbid"}


# ── 13. Compute ────────────────────────────────────────────────────────


class ComputeCapability(BaseModel):
    resource: str = ""
    available: bool = False
    quantity: Optional[float] = None
    unit: str = ""
    health: HealthStatus = HealthStatus.UNKNOWN
    notes: Optional[str] = None

    model_config = {"extra": "forbid"}


class Compute(BaseModel):
    potential: ComputePotential = ComputePotential.LOW
    eligibility: ComputeEligibility = ComputeEligibility.UNKNOWN
    reason: Optional[str] = None
    restrictions: list[str] = Field(default_factory=list)
    capabilities: dict[str, Optional[ComputeCapability]] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


# ── 14. Health ────────────────────────────────────────────────────────


class Health(BaseModel):
    system: HealthStatus = HealthStatus.UNKNOWN
    cpu: HealthStatus = HealthStatus.UNKNOWN
    memory: HealthStatus = HealthStatus.UNKNOWN
    storage: HealthStatus = HealthStatus.UNKNOWN
    thermal: HealthStatus = HealthStatus.UNKNOWN
    network: HealthStatus = HealthStatus.UNKNOWN
    psu: HealthStatus = HealthStatus.UNKNOWN
    fan: HealthStatus = HealthStatus.UNKNOWN
    kernel_errors: Optional[str] = None
    collected_at: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── 15. Workload ──────────────────────────────────────────────────────


class Workload(BaseModel):
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    load_average: Optional[list[float]] = None
    main_processes_cpu: list[dict[str, Any]] = Field(default_factory=list)
    main_processes_mem: list[dict[str, Any]] = Field(default_factory=list)
    process_count: Optional[int] = None
    collected_at: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── 16. PowerThermal ─────────────────────────────────────────────────


class PSU(BaseModel):
    name: str = ""
    capacity_w: Optional[float] = None
    health: HealthStatus = HealthStatus.UNKNOWN
    state: Optional[str] = None

    model_config = {"extra": "forbid"}


class PowerInfo(BaseModel):
    current_watts: Optional[float] = None
    capacity_watts: Optional[float] = None
    psus: list[PSU] = Field(default_factory=list)
    redundancy: Optional[str] = None

    model_config = {"extra": "forbid"}


class TemperatureReading(BaseModel):
    name: str = ""
    reading_c: Optional[float] = None
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class FanReading(BaseModel):
    name: str = ""
    reading_rpm: Optional[int] = None
    health: HealthStatus = HealthStatus.UNKNOWN

    model_config = {"extra": "forbid"}


class ThermalInfo(BaseModel):
    temperatures: list[TemperatureReading] = Field(default_factory=list)
    fans: list[FanReading] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PowerThermal(BaseModel):
    power: PowerInfo = Field(default_factory=PowerInfo)
    thermal: ThermalInfo = Field(default_factory=ThermalInfo)
    collected_at: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── 17. Verification (inline field-level) ─────────────────────────────


class FieldVerification(BaseModel):
    status: VerificationStatus = VerificationStatus.UNAVAILABLE
    sources: list[str] = Field(default_factory=list)
    values: dict[str, Any] = Field(default_factory=dict)
    canonical_value: Optional[Any] = None
    match: Optional[bool] = None
    note: Optional[str] = None

    model_config = {"extra": "forbid"}


class Verification(BaseModel):
    cpu: FieldVerification = Field(default_factory=FieldVerification)
    memory: FieldVerification = Field(default_factory=FieldVerification)
    storage: FieldVerification = Field(default_factory=FieldVerification)
    power: FieldVerification = Field(default_factory=FieldVerification)

    model_config = {"extra": "forbid"}


# ── Meta / Sources ────────────────────────────────────────────────────


class SourceInfo(BaseModel):
    available: bool = False
    confidence: Confidence = Confidence.NONE

    model_config = {"extra": "forbid"}


class Sources(BaseModel):
    redfish: SourceInfo = Field(default_factory=SourceInfo)
    ssh: SourceInfo = Field(default_factory=SourceInfo)
    snmp: SourceInfo = Field(default_factory=SourceInfo)
    ipmi: SourceInfo = Field(default_factory=SourceInfo)

    model_config = {"extra": "forbid"}


class Meta(BaseModel):
    schema_version: str = "1.0"
    collected_at: Optional[str] = None
    data_class: DataClass = DataClass.HARDWARE
    sources: Sources = Field(default_factory=Sources)
    verification: Verification = Field(default_factory=Verification)
    raw_path: Optional[str] = None

    model_config = {"extra": "forbid"}


# ── Vendor Extensions ─────────────────────────────────────────────────


class DellExt(BaseModel):
    model_config = {"extra": "allow"}


class HPEExt(BaseModel):
    model_config = {"extra": "allow"}


class VendorExt(BaseModel):
    dell: Optional[DellExt] = None
    hpe: Optional[HPEExt] = None

    model_config = {"extra": "forbid"}


# ── ServerInventory (Root) ────────────────────────────────────────────


class ServerInventory(BaseModel):
    """Schema v1.0 — Root inventory model. FROZEN."""

    schema_version: str = "1.0"
    identity: Identity = Field(default_factory=Identity)
    topology: Topology = Field(default_factory=Topology)
    hardware: Hardware = Field(default_factory=Hardware)
    management: Management = Field(default_factory=Management)
    os: OS = Field(default_factory=OS)
    virtualization: Virtualization = Field(default_factory=Virtualization)
    containers: Containers = Field(default_factory=Containers)
    development_environment: DevelopmentEnvironment = Field(default_factory=DevelopmentEnvironment)
    compute: Compute = Field(default_factory=Compute)
    health: Health = Field(default_factory=Health)
    workload: Workload = Field(default_factory=Workload)
    power_thermal: PowerThermal = Field(default_factory=PowerThermal)
    vendor_ext: VendorExt = Field(default_factory=VendorExt)
    meta: Meta = Field(default_factory=Meta, alias="_meta")

    model_config = {"extra": "forbid", "populate_by_name": True}
