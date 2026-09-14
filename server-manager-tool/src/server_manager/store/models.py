"""Store Models (Phase 6).

Database-level models for server registry, snapshots, and verification records.
Credentials are excluded from all models.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from ..models.enums import ServerLifecycle, Vendor
from ..models.inventory import ServerInventory
from ..models.enums import VerificationStatus


# ── Re-export ServerLifecycle for convenience ──────────────────────
# ServerLifecycle is defined in models/enums.py and re-exported here
# so store consumers can import from either location.
__all__ = [
    "ServerLifecycle",
    "EndpointRef",
    "ManagementEndpoints",
    "ServerRegistryEntry",
    "InventorySnapshot",
    "VerificationRecord",
]


class EndpointRef(BaseModel):
    """Network endpoint reference (credentials excluded)."""
    host: str
    port: int = 443
    username: Optional[str] = None
    credential_env: Optional[str] = None  # env var name, NOT the credential itself

    model_config = {"extra": "forbid"}


class ManagementEndpoints(BaseModel):
    """Management protocol endpoints for a server."""
    redfish: Optional[EndpointRef] = None
    ssh: Optional[EndpointRef] = None
    snmp: Optional[EndpointRef] = None

    model_config = {"extra": "forbid"}


class ServerRegistryEntry(BaseModel):
    """Server registry entry — one row per managed server."""
    server_id: str
    display_name: str
    hardware_identity: Optional[str] = None
    vendor: Vendor = Vendor.Unknown
    model: str = ""
    lifecycle_state: ServerLifecycle = ServerLifecycle.ACTIVE
    endpoints: ManagementEndpoints = Field(default_factory=ManagementEndpoints)
    current_snapshot_id: Optional[str] = None
    registered_at: str = ""
    last_collected_at: Optional[str] = None
    last_collection_status: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"extra": "forbid"}


class InventorySnapshot(BaseModel):
    """Append-only inventory snapshot."""
    snapshot_id: str
    server_id: str
    orchestration_run_id: str
    collected_at: str
    schema_version: str = "1.0"
    inventory: ServerInventory
    canonical_source: Optional[str] = None
    source_results_summary: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class VerificationRecord(BaseModel):
    """Verification result record."""
    verification_id: str
    server_id: str
    snapshot_id: str
    run_id: str
    verified_at: str
    result: Any  # VerificationResult (avoid circular import)
    summary: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}
