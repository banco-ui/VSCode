"""Discovery package — Phase 14.

Platform discovery and canonical inventory abstractions.

Composes existing Phase 13G contracts (ProviderAdapter →
RawProviderSnapshot → ProviderNormalizer → NormalizationResult)
into a discovery-level flow without duplicating any abstraction.
"""
from .models import CanonicalInventory, DiscoveryResult
from .service import PlatformDiscovery

__all__ = [
    "CanonicalInventory",
    "DiscoveryResult",
    "PlatformDiscovery",
]
