"""SSH Normalizer (Phase 3).

Transforms raw SSH command outputs into ServerInventory.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..models.enums import (
    HealthStatus,
    NetworkSpeed,
    Protocol,
    Vendor,
)
from ..models.inventory import (
    CPU,
    CPUProcessor,
    Containers,
    DockerInfo,
    GPU,
    GPUDevice,
    Hardware,
    Identity,
    KubernetesInfo,
    Management,
    Memory,
    Network,
    NetworkAdapter,
    OS,
    ServerInventory,
    SSHInfo,
    Topology,
    Virtualization,
    DevelopmentEnvironment,
    Workload,
)
from .base import BaseNormalizer

logger = logging.getLogger(__name__)


class SSHNormalizer(BaseNormalizer):
    """Normalize SSH raw data into ServerInventory."""

    @property
    def source_name(self) -> str:
        return "ssh"

    def normalize(self, raw_data: dict[str, Any]) -> ServerInventory:
        """Transform SSH data into ServerInventory."""
        os_data = raw_data.get("os", {})
        cpu_data = raw_data.get("cpu", {})
        mem_data = raw_data.get("memory", {})
        docker_data = raw_data.get("docker", {})
        k8s_data = raw_data.get("kubernetes", {})
        dev_data = raw_data.get("dev_tools", {})
        workload_data = raw_data.get("workload", {})
        virt_data = raw_data.get("virtualization", {})

        # Identity
        identity = Identity(
            server_id=self.safe_str(os_data.get("hostname") or "unknown"),
            hostname=self.safe_str(os_data.get("hostname")),
        )

        # OS
        os_info = OS(
            distribution=self.safe_str(os_data.get("distribution")),
            kernel=self.safe_str(os_data.get("kernel")),
            hostname=self.safe_str(os_data.get("hostname")),
            architecture=self.safe_str(os_data.get("architecture")),
            uptime=self.safe_str(os_data.get("uptime")),
        )

        # CPU
        cpu_cores = self.safe_int(cpu_data.get("cores"))
        cpu = CPU(
            count=1,
            total_cores=cpu_cores,
            total_threads=cpu_cores,
            processors=[CPUProcessor(
                model=self.safe_str(cpu_data.get("model")),
                cores=cpu_cores,
                threads=cpu_cores,
            )],
        )

        # Memory
        mem_bytes = self.safe_float(mem_data.get("total_bytes"))
        mem_gb = round(mem_bytes / (1024**3), 2) if mem_bytes else 0.0
        memory = Memory(
            total_gb=mem_gb,
            os_reported=mem_gb,
        )

        # Network
        network = Network(
            adapter_count=0,
            active_interfaces=0,
        )

        # GPU
        gpu_str = self.safe_str(raw_data.get("gpu"))
        gpu_devices: list[GPUDevice] = []
        if gpu_str and gpu_str != "''":
            for line in gpu_str.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    vram_str = parts[2].replace("MiB", "").strip()
                    gpu_devices.append(GPUDevice(
                        vendor="NVIDIA" if "nvidia" in parts[0].lower() else "",
                        model=parts[0],
                        vram_gb=round(self.safe_float(vram_str) / 1024, 2) if vram_str else None,
                        driver_version=parts[1] if len(parts) > 1 else None,
                    ))
        gpu = GPU(
            dedicated_compute_gpu=len(gpu_devices) > 0,
            count=len(gpu_devices),
            devices=gpu_devices,
        )

        # Hardware
        hardware = Hardware(cpu=cpu, memory=memory, gpu=gpu, network=network)

        # Virtualization
        virt = Virtualization(
            kvm_modules_loaded=bool(virt_data.get("kvm_loaded")),
            virsh_available=self.parse_bool(virt_data.get("virsh_available")),
            vms=self.safe_int(virt_data.get("vm_count")),
        )

        # Containers
        docker_info = DockerInfo(
            installed=self.parse_bool(docker_data.get("installed")),
            version=self.safe_str(docker_data.get("version")),
            running_containers=self.safe_int(docker_data.get("containers")),
        )
        k8s_info = KubernetesInfo(
            installed=self.parse_bool(k8s_data.get("installed")),
            version=self.safe_str(k8s_data.get("version")),
        )
        containers = Containers(docker=docker_info, kubernetes=k8s_info)

        # Dev environment
        dev_env = DevelopmentEnvironment(
            git_installed=self.parse_bool(dev_data.get("git")),
            python3_installed=self.parse_bool(dev_data.get("python3")),
            node_installed=self.parse_bool(dev_data.get("node")),
            npm_installed=self.parse_bool(dev_data.get("npm")),
            gcc_installed=self.parse_bool(dev_data.get("gcc")),
            gpp_installed=self.parse_bool(dev_data.get("gpp")),
            pm2_installed=self.parse_bool(dev_data.get("pm2")),
        )

        # Workload
        load_str = self.safe_str(workload_data.get("load_average"))
        load_avg: Optional[list[float]] = None
        if load_str:
            parts = load_str.split()[:3]
            try:
                load_avg = [float(p) for p in parts]
            except ValueError:
                pass

        workload = Workload(
            cpu_utilization=self.safe_float(workload_data.get("cpu_utilization")),
            memory_utilization=self.safe_float(workload_data.get("memory_utilization")),
            load_average=load_avg,
            process_count=self.safe_int(workload_data.get("process_count")),
        )

        # Management
        management = Management(
            protocols=[Protocol.SSH],
            ssh=SSHInfo(available=True, port=22),
        )

        return ServerInventory(
            identity=identity,
            os=os_info,
            hardware=hardware,
            management=management,
            virtualization=virt,
            containers=containers,
            development_environment=dev_env,
            workload=workload,
        )
