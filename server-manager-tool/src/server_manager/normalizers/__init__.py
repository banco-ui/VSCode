"""Normalizers (Phase 3)."""
from .base import BaseNormalizer
from .redfish_normalizer import RedfishNormalizer
from .ssh_normalizer import SSHNormalizer
from .legacy_adapter import LegacyAdapter

__all__ = [
    "BaseNormalizer",
    "RedfishNormalizer",
    "SSHNormalizer",
    "LegacyAdapter",
]
