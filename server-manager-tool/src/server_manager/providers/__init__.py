"""Providers (Phase 13G-2 + 13G-4).

Provider adapter contract, raw snapshot model, and Kubernetes adapter.
"""
from .base import (
    AdapterCapability,
    CapabilityResult,
    ProviderAdapter,
    RawProviderSnapshot,
    RawRelationshipEvidence,
)
from .kubernetes import KubernetesProviderAdapter

__all__ = [
    "AdapterCapability",
    "CapabilityResult",
    "ProviderAdapter",
    "RawProviderSnapshot",
    "RawRelationshipEvidence",
    # Phase 13G-4
    "KubernetesProviderAdapter",
]
