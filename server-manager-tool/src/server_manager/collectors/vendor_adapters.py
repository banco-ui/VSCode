"""Vendor Adapters (Phase 2).

Vendor-specific extensions for Dell iDRAC and HPE iLO.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class VendorAdapter:
    """Base vendor adapter for vendor-specific data extraction."""

    VENDOR_NAME = "Generic"

    def __init__(self, raw_data: dict[str, Any]) -> None:
        self.raw_data = raw_data

    def get_vendor_ext(self) -> dict[str, Any]:
        """Return vendor-specific extension data."""
        return {}

    def get_service_tag(self) -> Optional[str]:
        """Return service tag (Dell) or serial number (HPE)."""
        return None

    def get_management_info(self) -> dict[str, Any]:
        """Return management controller info."""
        return {}


class DellAdapter(VendorAdapter):
    """Dell iDRAC specific adapter."""

    VENDOR_NAME = "Dell"

    def get_service_tag(self) -> Optional[str]:
        system = self.raw_data.get("system", {})
        # Dell service tag is in SKU field
        return system.get("SKU") or system.get("SerialNumber")

    def get_vendor_ext(self) -> dict[str, Any]:
        system = self.raw_data.get("system", {})
        return {
            "service_tag": system.get("SKU"),
            "system_id": system.get("SystemID") or system.get("PartNumber"),
            "iDRAC_firmware": self._get_idrac_version(),
        }

    def _get_idrac_version(self) -> Optional[str]:
        manager = self.raw_data.get("manager", {})
        return manager.get("FirmwareVersion")

    def get_management_info(self) -> dict[str, Any]:
        manager = self.raw_data.get("manager", {})
        return {
            "controller": "iDRAC",
            "firmware_version": manager.get("FirmwareVersion"),
            "model": manager.get("Model"),
        }


class HPEAdapter(VendorAdapter):
    """HPE iLO specific adapter."""

    VENDOR_NAME = "HPE"

    def get_service_tag(self) -> Optional[str]:
        system = self.raw_data.get("system", {})
        # HPE serial number
        return system.get("SerialNumber")

    def get_vendor_ext(self) -> dict[str, Any]:
        system = self.raw_data.get("system", {})
        return {
            "serial_number": system.get("SerialNumber"),
            "ilo_firmware": self._get_ilo_version(),
            "platform": system.get("Platform"),
        }

    def _get_ilo_version(self) -> Optional[str]:
        manager = self.raw_data.get("manager", {})
        return manager.get("FirmwareVersion")

    def get_management_info(self) -> dict[str, Any]:
        manager = self.raw_data.get("manager", {})
        return {
            "controller": "iLO",
            "firmware_version": manager.get("FirmwareVersion"),
            "model": manager.get("Model"),
        }


def get_vendor_adapter(vendor: str, raw_data: dict[str, Any]) -> VendorAdapter:
    """Factory to get the appropriate vendor adapter.

    Args:
        vendor: Vendor name ("Dell", "HPE", etc.)
        raw_data: Raw Redfish data.

    Returns:
        VendorAdapter instance.
    """
    vendor_lower = vendor.lower() if vendor else ""
    if "dell" in vendor_lower:
        return DellAdapter(raw_data)
    elif "hpe" in vendor_lower or "hp " in vendor_lower or "hpe" in vendor_lower:
        return HPEAdapter(raw_data)
    return VendorAdapter(raw_data)
