"""Collectors (Phase 2)."""
from .base import BaseCollector, CollectionResult
from .redfish import RedfishCollector
from .ssh import SSHCollector
from .vendor_adapters import VendorAdapter

__all__ = [
    "BaseCollector",
    "CollectionResult",
    "RedfishCollector",
    "SSHCollector",
    "VendorAdapter",
]
