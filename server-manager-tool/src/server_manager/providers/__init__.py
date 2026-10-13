"""Providers (Phase 13G-2 + 13G-4 + 28E).

Provider adapter contract, raw snapshot model, Kubernetes adapter,
OpenStack adapter, and StarlingX adapter.
"""
from .base import (
    AdapterCapability,
    CapabilityResult,
    ProviderAdapter,
    RawProviderSnapshot,
    RawRelationshipEvidence,
)
from .kubernetes import KubernetesProviderAdapter
from .openstack import OpenStackProviderAdapter
from .starlingx import StarlingXProviderAdapter

__all__ = [
    "AdapterCapability",
    "CapabilityResult",
    "ProviderAdapter",
    "RawProviderSnapshot",
    "RawRelationshipEvidence",
    # Phase 13G-4
    "KubernetesProviderAdapter",
    # Phase 26
    "OpenStackProviderAdapter",
    # Phase 28E
    "StarlingXProviderAdapter",
]
