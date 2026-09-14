"""Legacy Adapter (Phase 3).

Adapts legacy JSON inventory format to new ServerInventory schema.
"""
from __future__ import annotations

import logging
from typing import Any

from ..models.inventory import ServerInventory
from .base import BaseNormalizer

logger = logging.getLogger(__name__)


class LegacyAdapter(BaseNormalizer):
    """Adapt legacy JSON inventory to ServerInventory.

    This adapter handles the old inventory format where fields may be
    named differently or structured differently.
    """

    @property
    def source_name(self) -> str:
        return "legacy"

    def normalize(self, raw_data: dict[str, Any]) -> ServerInventory:
        """Transform legacy data into ServerInventory.

        Handles common legacy field mappings:
        - "server_name" → identity.server_id
        - "ip_address" → identity.hostname
        - "cpu_model" → hardware.cpu.processors[0].model
        - "ram_gb" → hardware.memory.total_gb
        - etc.
        """
        # Try direct validation first (if the data is already schema-compliant)
        try:
            return ServerInventory.model_validate(raw_data)
        except Exception:
            pass

        # Map legacy fields
        mapped = self._map_legacy_fields(raw_data)
        return ServerInventory.model_validate(mapped)

    def _map_legacy_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map legacy field names to new schema."""
        result: dict[str, Any] = {}

        # Identity
        identity: dict[str, Any] = {}
        if "server_name" in data:
            identity["server_id"] = data["server_name"]
        if "server_id" in data:
            identity["server_id"] = data["server_id"]
        if "ip_address" in data:
            identity["hostname"] = data["ip_address"]
        if "hostname" in data:
            identity["hostname"] = data["hostname"]
        if "vendor" in data:
            identity["vendor"] = data["vendor"]
        if "model" in data:
            identity["model"] = data["model"]
        if "serial_number" in data:
            identity["serial_number"] = data["serial_number"]
        if "service_tag" in data:
            identity["service_tag"] = data["service_tag"]
        if identity:
            result["identity"] = identity

        # Hardware
        hardware: dict[str, Any] = {}

        # CPU
        cpu: dict[str, Any] = {}
        if "cpu_model" in data:
            cpu["count"] = 1
            cpu["processors"] = [{"model": data["cpu_model"]}]
        if "cpu_count" in data:
            cpu["count"] = data["cpu_count"]
        if "cpu_cores" in data:
            cpu["total_cores"] = data["cpu_cores"]
        if "cpu_threads" in data:
            cpu["total_threads"] = data["cpu_threads"]
        if cpu:
            hardware["cpu"] = cpu

        # Memory
        if "ram_gb" in data:
            hardware["memory"] = {"total_gb": data["ram_gb"]}
        elif "memory_gb" in data:
            hardware["memory"] = {"total_gb": data["memory_gb"]}

        # Storage
        if "disk_count" in data or "disks" in data:
            hardware.setdefault("storage", {})
            if "disks" in data and isinstance(data["disks"], list):
                hardware["storage"]["physical_disks"] = data["disks"]

        if hardware:
            result["hardware"] = hardware

        # OS
        os_info: dict[str, Any] = {}
        if "os" in data and isinstance(data["os"], str):
            os_info["distribution"] = data["os"]
        if "os_distribution" in data:
            os_info["distribution"] = data["os_distribution"]
        if "os_version" in data:
            os_info["version"] = data["os_version"]
        if "kernel" in data:
            os_info["kernel"] = data["kernel"]
        if "arch" in data:
            os_info["architecture"] = data["arch"]
        if os_info:
            result["os"] = os_info

        # Management
        mgmt: dict[str, Any] = {}
        if "idrac_ip" in data:
            mgmt.setdefault("redfish", {})["endpoint"] = data["idrac_ip"]
        if "ilo_ip" in data:
            mgmt.setdefault("redfish", {})["endpoint"] = data["ilo_ip"]
        if "management_ip" in data:
            mgmt.setdefault("redfish", {})["endpoint"] = data["management_ip"]
        if mgmt:
            result["management"] = mgmt

        # Copy any remaining fields that match the new schema
        for key in [
            "topology", "virtualization", "containers",
            "development_environment", "compute", "health",
            "workload", "power_thermal", "vendor_ext",
        ]:
            if key in data:
                result[key] = data[key]

        return result
