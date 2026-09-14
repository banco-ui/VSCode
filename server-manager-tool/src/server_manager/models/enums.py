"""Schema v1.0 Enums — Phase 0.

All enums are string-based for JSON serialization compatibility.
"""
from __future__ import annotations

from enum import Enum


class HealthStatus(str, Enum):
    """Hardware health status."""
    OK = "OK"
    WARNING = "Warning"
    CRITICAL = "Critical"
    UNKNOWN = "Unknown"


class ComputePotential(str, Enum):
    """Overall compute resource potential of a server."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComputeEligibility(str, Enum):
    """Weekend compute eligibility state."""
    PRODUCTION = "PRODUCTION"
    EXCLUDED_USER_WORKLOAD = "EXCLUDED_USER_WORKLOAD"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED = "BLOCKED"
    IDLE = "IDLE"
    CANDIDATE = "CANDIDATE"
    COMPUTE_ELIGIBLE = "COMPUTE_ELIGIBLE"
    COMPUTING = "COMPUTING"
    DRAINING = "DRAINING"
    UNKNOWN = "UNKNOWN"


class VerificationStatus(str, Enum):
    """Cross-source verification result for a single field."""
    VERIFIED = "VERIFIED"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    DISCREPANCY = "DISCREPANCY"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class Confidence(str, Enum):
    """Confidence level for a verified field value."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class Vendor(str, Enum):
    """Server vendor."""
    Dell = "Dell"
    HPE = "HPE"
    Unknown = "Unknown"


class ControllerType(str, Enum):
    """Management controller type."""
    iDRAC = "iDRAC"
    iLO = "iLO"
    Unknown = "Unknown"


class Protocol(str, Enum):
    """Collection protocol."""
    Redfish = "Redfish"
    SSH = "SSH"
    IPMI = "IPMI"
    SNMP = "SNMP"


class MediaType(str, Enum):
    """Storage media type."""
    SSD = "SSD"
    HDD = "HDD"
    NVMe = "NVMe"
    Unknown = "Unknown"


class NetworkSpeed(str, Enum):
    """Network link speed."""
    GbE_1 = "1GbE"
    GbE_10 = "10GbE"
    GbE_25 = "25GbE"
    GbE_40 = "40GbE"
    GbE_100 = "100GbE"
    Unknown = "Unknown"


class DataClass(str, Enum):
    """Data classification for the inventory."""
    HARDWARE = "HARDWARE"
    OS = "OS"
    RUNTIME = "RUNTIME"


class ServerLifecycle(str, Enum):
    """Server lifecycle state (used in store/models)."""
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    UNREACHABLE = "UNREACHABLE"
    DECOMMISSIONED = "DECOMMISSIONED"
    PROVISIONING = "PROVISIONING"
