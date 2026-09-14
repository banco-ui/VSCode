"""SSH Collector (Phase 2).

Collects OS-level and runtime inventory data via SSH.
"""
from __future__ import annotations

import logging
import shlex
from typing import Any, Optional

from .base import BaseCollector

logger = logging.getLogger(__name__)


class SSHCollector(BaseCollector):
    """Collect server OS and runtime data via SSH commands."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        key_file: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        super().__init__(host, port, username, password)
        self.key_file = key_file
        self.timeout = timeout

    @property
    def source_name(self) -> str:
        return "ssh"

    def collect(self) -> dict[str, Any]:
        """Collect OS and runtime data via SSH.

        Returns:
            Dict with raw SSH command outputs.
        """
        data: dict[str, Any] = {
            "source": "ssh",
            "endpoint": f"{self.host}:{self.port}",
        }

        # OS info
        data["os"] = {
            "distribution": self._run("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'"),
            "kernel": self._run("uname -r"),
            "hostname": self._run("hostname"),
            "architecture": self._run("uname -m"),
            "uptime": self._run("uptime -p 2>/dev/null || uptime"),
        }

        # CPU info
        cpu_model = self._run("cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | sed 's/^ //'")
        cpu_cores = self._run("nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo")
        data["cpu"] = {
            "model": cpu_model,
            "cores": cpu_cores,
        }

        # Memory info
        mem_total = self._run("free -b | awk '/^Mem:/{print $2}'")
        data["memory"] = {
            "total_bytes": mem_total,
        }

        # Disk info
        data["disks"] = self._run("lsblk -b -d -o NAME,SIZE,TYPE,ROTA 2>/dev/null || echo ''")

        # Network info
        data["network"] = self._run("ip -o link show | awk -F': ' '{print $2}' 2>/dev/null || echo ''")

        # Virtualization
        data["virtualization"] = {
            "kvm_loaded": self._run("lsmod | grep kvm | head -1 || echo ''"),
            "virsh_available": self._run("which virsh 2>/dev/null && echo 'yes' || echo 'no'"),
            "vm_count": self._run("virsh list --all 2>/dev/null | tail -n +3 | head -n -1 | wc -l || echo '0'"),
        }

        # Docker
        data["docker"] = {
            "installed": self._run("which docker 2>/dev/null && echo 'yes' || echo 'no'"),
            "version": self._run("docker --version 2>/dev/null | cut -d' ' -f3 || echo ''"),
            "containers": self._run("docker ps -q 2>/dev/null | wc -l || echo '0'"),
        }

        # Kubernetes
        data["kubernetes"] = {
            "installed": self._run("which kubectl 2>/dev/null && echo 'yes' || echo 'no'"),
            "version": self._run("kubectl version --client --short 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo ''"),
        }

        # Dev tools
        data["dev_tools"] = {
            "git": self._run("which git 2>/dev/null && echo 'yes' || echo 'no'"),
            "python3": self._run("which python3 2>/dev/null && echo 'yes' || echo 'no'"),
            "node": self._run("which node 2>/dev/null && echo 'yes' || echo 'no'"),
            "npm": self._run("which npm 2>/dev/null && echo 'yes' || echo 'no'"),
            "gcc": self._run("which gcc 2>/dev/null && echo 'yes' || echo 'no'"),
            "gpp": self._run("which g++ 2>/dev/null && echo 'yes' || echo 'no'"),
            "pm2": self._run("which pm2 2>/dev/null && echo 'yes' || echo 'no'"),
        }

        # Workload
        data["workload"] = {
            "cpu_utilization": self._run("top -bn1 | awk '/^%Cpu/ {print $2}' 2>/dev/null || echo ''"),
            "memory_utilization": self._run("free | awk '/^Mem:/ {printf \"%.1f\", $3/$2*100}' 2>/dev/null || echo ''"),
            "load_average": self._run("cat /proc/loadavg 2>/dev/null || echo ''"),
            "process_count": self._run("ps aux | wc -l 2>/dev/null || echo '0'"),
        }

        # GPU (nvidia-smi)
        data["gpu"] = self._run("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || echo ''")

        # LSI/RAID controller
        data["raid"] = self._run("which storcli 2>/dev/null && storcli /c0 show 2>/dev/null || echo ''")

        return data

    def _run(self, command: str) -> str:
        """Run a command via SSH and return stripped output.

        This is a placeholder implementation. In production, this would
        use paramiko or subprocess with ssh.
        """
        # For testing: if host is "localhost" or "127.0.0.1", run locally
        if self.host in ("localhost", "127.0.0.1", "0.0.0.0"):
            import subprocess
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                return result.stdout.strip()
            except Exception as e:
                logger.error("Local command failed: %s — %s", command, e)
                return ""
        else:
            # Use subprocess with ssh command
            import subprocess
            ssh_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", f"ConnectTimeout={self.timeout}",
                "-p", str(self.port),
            ]
            if self.key_file:
                ssh_cmd.extend(["-i", self.key_file])
            ssh_cmd.append(f"{self.username}@{self.host}")
            ssh_cmd.append(command)

            try:
                result = subprocess.run(
                    ssh_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                return result.stdout.strip()
            except Exception as e:
                logger.error("SSH command failed: %s — %s", command, e)
                return ""
