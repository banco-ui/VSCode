"""Domain Models (Phase 0-1)."""
from .enums import (
    HealthStatus,
    ComputePotential,
    ComputeEligibility,
    VerificationStatus,
    Confidence,
    Vendor,
    ControllerType,
    Protocol,
    MediaType,
    NetworkSpeed,
    DataClass,
    ServerLifecycle,
)
from .inventory import ServerInventory

__all__ = [
    "HealthStatus",
    "ComputePotential",
    "ComputeEligibility",
    "VerificationStatus",
    "Confidence",
    "Vendor",
    "ControllerType",
    "Protocol",
    "MediaType",
    "NetworkSpeed",
    "DataClass",
    "ServerLifecycle",
    "ServerInventory",
]
