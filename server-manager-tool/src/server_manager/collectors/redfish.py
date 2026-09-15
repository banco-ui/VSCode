"""Redfish Collector (Phase 2).

Collects hardware inventory data via Redfish API.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from .base import BaseCollector

logger = logging.getLogger(__name__)


class RedfishCollector(BaseCollector):
    """Collect server hardware data via DMTF Redfish API."""

    def __init__(
        self,
        host: str,
        port: int = 443,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
        verify_ssl: bool = False,
        timeout: int = 30,
    ) -> None:
        super().__init__(host, port, username, password)
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    @property
    def source_name(self) -> str:
        return "redfish"

    @property
    def base_url(self) -> str:
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}"

    def collect(self) -> dict[str, Any]:
        """Collect Redfish data.

        Returns:
            Dict with raw Redfish data including:
            - System info
            - Processor info
            - Memory info
            - Storage info
            - Network info
            - Power/Thermal info
        """
        # Import urllib here to avoid hard dependency at module level
        import json
        import urllib.request

        data: dict[str, Any] = {
            "source": "redfish",
            "endpoint": self.base_url,
        }

        # Fetch root
        root = self._get("/redfish/v1/")
        if root is None:
            raise ConnectionError(f"Failed to connect to Redfish at {self.base_url}")

        data["redfish_version"] = root.get("RedfishVersion", "unknown")

        # Fetch systems
        systems_data = self._get_collection(root, "Systems")
        if systems_data:
            system = self._get_first_member(systems_data)
            if system:
                data["system"] = system
                # Processors
                proc_data = self._get_collection(system, "Processors")
                if proc_data:
                    data["processors"] = self._get_all_members(proc_data)
                # Memory
                mem_data = self._get_collection(system, "Memory")
                if mem_data:
                    data["memory"] = self._get_all_members(mem_data)
                # Network interfaces
                net_data = self._get_collection(system, "NetworkInterfaces")
                if net_data:
                    data["network_interfaces"] = self._get_all_members(net_data)
                # PCIe devices
                pcie_data = self._get_collection(system, "PCIeDevices")
                if pcie_data:
                    data["pcie_devices"] = self._get_all_members(pcie_data)
                # Storage
                storage_data = self._get_collection(system, "Storage")
                if storage_data:
                    data["storage"] = self._collect_storage(storage_data)

        # Fetch chassis

        chassis_data = self._get_collection(root, "Chassis")
        if chassis_data:
            chassis = self._get_first_member(chassis_data)
            if chassis:
                data["chassis"] = chassis
                # Power
                power = self._get_from_ref(chassis, "Power")
                if power:
                    data["power"] = power
                # Thermal
                thermal = self._get_from_ref(chassis, "Thermal")
                if thermal:
                    data["thermal"] = thermal

        # Fetch managers (iDRAC/iLO)
        managers_data = self._get_collection(root, "Managers")
        if managers_data:
            manager = self._get_first_member(managers_data)
            if manager:
                data["manager"] = manager

        return data

    def _get(self, path: str) -> Optional[dict[str, Any]]:
        """Make a GET request to the Redfish API."""
        import base64
        import urllib.request

        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")

        if self.username and self._password:
            creds = base64.b64encode(f"{self.username}:{self._password}".encode()).decode()
            req.add_header("Authorization", f"Basic {creds}")

        import ssl
        ctx = ssl.create_default_context()
        if not self.verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                import json
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error("Redfish GET %s failed: %s", path, e)
            return None

    def _get_collection(self, parent: dict, key: str) -> Optional[dict]:
        """Get a collection reference from a parent object."""
        ref = parent.get(key)
        if ref is None:
            return None
        if isinstance(ref, dict) and "@odata.id" in ref:
            return self._get(ref["@odata.id"])
        return ref

    def _get_from_ref(self, parent: dict, key: str) -> Optional[dict]:
        """Get a resource from a reference in parent."""
        ref = parent.get(key)
        if ref is None:
            return None
        if isinstance(ref, dict) and "@odata.id" in ref:
            return self._get(ref["@odata.id"])
        return ref

    def _get_first_member(self, collection: dict) -> Optional[dict]:
        """Get the first member of a collection."""
        members = collection.get("Members", [])
        if not members:
            return None
        first = members[0]
        if isinstance(first, dict) and "@odata.id" in first:
            return self._get(first["@odata.id"])
        return first

    def _get_all_members(self, collection: dict) -> list[dict]:
        """Get all members of a collection."""
        members = collection.get("Members", [])
        results = []
        for m in members:
            if isinstance(m, dict) and "@odata.id" in m:
                data = self._get(m["@odata.id"])
                if data:
                    results.append(data)
        return results

    def _collect_storage(self, storage_collection: dict) -> list[dict]:
        """Collect storage resources from a Storage collection.

        Fetches each Storage member, along with its Drives and Volumes.
        Partial failures are logged and skipped — one storage subsystem
        failure does not prevent collection of others.

        Args:
            storage_collection: The Storage collection response.

        Returns:
            List of storage resource dicts, each containing:
            - controller info (StorageControllers)
            - drives (list of drive dicts)
            - volumes (list of volume dicts)
        """
        results: list[dict] = []
        members = storage_collection.get("Members", [])
        for m in members:
            if not isinstance(m, dict) or "@odata.id" not in m:
                continue
            storage = self._get(m["@odata.id"])
            if storage is None:
                logger.warning("Failed to fetch Storage resource at %s", m.get("@odata.id"))
                continue

            entry: dict[str, Any] = {
                "@odata.id": storage.get("@odata.id", m["@odata.id"]),
                "controllers": storage.get("StorageControllers", []),
            }

            # Collect Drives
            drives_ref = storage.get("Drives")
            if drives_ref and isinstance(drives_ref, list):
                drives: list[dict] = []
                for d in drives_ref:
                    if isinstance(d, dict) and "@odata.id" in d:
                        drive = self._get(d["@odata.id"])
                        if drive:
                            drives.append(drive)
                        else:
                            logger.warning("Failed to fetch Drive at %s", d.get("@odata.id"))
                entry["drives"] = drives
            else:
                entry["drives"] = []

            # Collect Volumes
            volumes_ref = storage.get("Volumes")
            if isinstance(volumes_ref, dict) and "@odata.id" in volumes_ref:
                vol_collection = self._get(volumes_ref["@odata.id"])
                if vol_collection:
                    volumes: list[dict] = []
                    for v in vol_collection.get("Members", []):
                        if isinstance(v, dict) and "@odata.id" in v:
                            vol = self._get(v["@odata.id"])
                            if vol:
                                volumes.append(vol)
                            else:
                                logger.warning("Failed to fetch Volume at %s", v.get("@odata.id"))
                    entry["volumes"] = volumes
                else:
                    entry["volumes"] = []
            else:
                entry["volumes"] = []

            results.append(entry)

        return results


