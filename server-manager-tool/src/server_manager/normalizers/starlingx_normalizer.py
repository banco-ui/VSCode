"""StarlingX Provider Normalizer — Phase 28E.

Transforms StarlingX RawProviderSnapshot → Canonical Domain Model entities.

    RawProviderSnapshot (StarlingX raw data)
        ↓
    StarlingXProviderNormalizer
        ↓
    Canonical Domain Model (Platform, Cluster, Node)

Architecture:
    Inherits from GenericProviderNormalizer to reuse entity creation,
    enum mapping, ref resolution, and status determination.
    Overrides normalize() to transform StarlingX raw payload → generic
    payload format, then delegates to super().normalize().

StarlingX → Canonical mapping (deterministic, no inference):

    sysinv isystems → Platform(WRCP, version=sw_version)
    sysinv isystems → Cluster(WRCP_AIO_SX, platform_ref)
    sysinv ihosts   → Node(name=hostname, cluster_ref)
    sysinv imemorys → Node.metadata.platform_memory
    fm_alarms       → Node/Platform metadata (health evidence)
    fm_event_log    → Platform metadata (event history)
    smapi_nodes     → Node.metadata.smapi (service availability)
    system_health   → Platform.metadata.health_query
    software_list   → Platform.metadata.usm_releases

NOT created (no evidence from confirmed API/CLI):
    - Physical (bm_type=none — use Redfish separately)
    - OS, EE, Workload, Network, Storage, Accelerator

Identity: canon-wrcp-{kind}-{provider_ref} via CanonicalIdentityGenerator.
"""
from __future__ import annotations

import logging
from typing import Any

from ..models.canonical import ProviderType
from ..providers.base import RawProviderSnapshot
from .provider_normalizer import GenericProviderNormalizer, NormalizationResult

logger = logging.getLogger(__name__)


class StarlingXProviderNormalizer(GenericProviderNormalizer):
    """StarlingX-specific provider normalizer.

    Transforms StarlingX raw payload → generic format, then delegates
    to GenericProviderNormalizer.normalize().
    """

    def __init__(self) -> None:
        super().__init__(ProviderType.WRCP)

    def normalize(self, snapshot: RawProviderSnapshot) -> NormalizationResult:
        """Normalize a StarlingX raw snapshot into canonical entities."""
        generic_payload = self._transform_starlingx_to_generic(snapshot)
        generic_snapshot = self._wrap_generic(snapshot, generic_payload)
        return super().normalize(generic_snapshot)

    @staticmethod
    def _wrap_generic(
        snapshot: RawProviderSnapshot, payload: dict[str, Any]
    ) -> RawProviderSnapshot:
        """Create a new snapshot with transformed payload."""
        return RawProviderSnapshot(
            snapshot_id=snapshot.snapshot_id,
            provider_type=snapshot.provider_type,
            provider_id=snapshot.provider_id,
            collected_at=snapshot.collected_at,
            collection_status=snapshot.collection_status,
            declared_capabilities=snapshot.declared_capabilities,
            capability_results=snapshot.capability_results,
            payload=payload,
            relationship_evidence=snapshot.relationship_evidence,
            source_evidence=snapshot.source_evidence,
            errors=snapshot.errors,
            warnings=snapshot.warnings,
        )

    def _transform_starlingx_to_generic(
        self, snapshot: RawProviderSnapshot
    ) -> dict[str, Any]:
        """Transform StarlingX raw API data → generic canonical payload."""
        payload = snapshot.payload
        generic: dict[str, Any] = {
            "physicals": [], "os": [], "platforms": [], "clusters": [],
            "nodes": [], "execution_environments": [], "workloads": [],
            "networks": [], "storages": [], "accelerators": [],
        }

        systems = payload.get("sysinv_isystems", [])
        hosts = payload.get("sysinv_ihosts", [])
        imemorys = payload.get("sysinv_imemorys", {})
        alarms = payload.get("fm_alarms", [])
        event_log = payload.get("fm_event_log", [])
        smapi_nodes = payload.get("smapi_nodes", [])
        system_health = payload.get("system_health", {})
        software_list = payload.get("software_list", [])

        # ── sysinv isystems → Platform + Cluster ─────────────────────
        platform_pid = None
        for system in systems:
            if not isinstance(system, dict):
                continue
            system_uuid = system.get("uuid", "")
            if not system_uuid:
                continue
            platform_pid = system_uuid
            sw_version = str(system.get("sw_version", ""))
            system_mode = str(system.get("system_mode", ""))

            generic["platforms"].append({
                "provider_id": system_uuid,
                "platform_type": "WRCP",
                "version": sw_version,
                "metadata": {
                    "starlingx": {
                        "name": system.get("name", ""),
                        "system_mode": system_mode,
                        "system_type": system.get("system_type", ""),
                        "timezone": system.get("timezone", ""),
                        "software_list": software_list,
                        "system_health": system_health,
                        "fm_event_log": event_log,
                    },
                },
            })

            cluster_type = "WRCP_AIO_SX" if system_mode == "simplex" else "UNKNOWN"
            generic["clusters"].append({
                "provider_id": f"{system_uuid}-cluster",
                "cluster_type": cluster_type,
                "platform_ref": system_uuid,
                "metadata": {"starlingx": {"system_mode": system_mode}},
            })

        # ── sysinv ihosts → Nodes ────────────────────────────────────
        # Node ≠ Physical. bm_type=none → no Physical from sysinv.
        cluster_ref = f"{platform_pid}-cluster" if platform_pid else None

        for host in hosts:
            if not isinstance(host, dict):
                continue
            host_uuid = host.get("uuid", "")
            if not host_uuid:
                continue
            hostname = host.get("hostname", "")
            host_mem = imemorys.get(host_uuid, []) if isinstance(imemorys, dict) else []
            host_alarms = [
                a for a in alarms if isinstance(a, dict)
                and hostname and hostname in str(a.get("entity_instance_id", ""))
            ]
            # smapi match by name — NOT identity inference, just data preservation
            smapi_match = None
            for sn in smapi_nodes:
                if isinstance(sn, dict) and sn.get("name") == hostname:
                    smapi_match = sn
                    break

            generic["nodes"].append({
                "provider_id": host_uuid,
                "name": hostname,
                "cluster_ref": cluster_ref,
                "metadata": {
                    "starlingx": {
                        "hostname": hostname,
                        "personality": host.get("personality", ""),
                        "administrative": host.get("administrative", ""),
                        "operational": host.get("operational", ""),
                        "availability": host.get("availability", ""),
                        "subfunctions": host.get("subfunctions", ""),
                        "uptime": host.get("uptime", ""),
                        "reboot_needed": host.get("reboot_needed"),
                        "vim_progress_status": host.get("vim_progress_status", ""),
                        "clock_synchronization": host.get("clock_synchronization", ""),
                        "bm_type": host.get("bm_type", ""),
                        "bm_ip": host.get("bm_ip"),
                        "bm_hostname": host.get("bm_hostname"),
                        "capabilities": host.get("capabilities", {}),
                        "location": host.get("location", {}),
                        "platform_memory": host_mem,
                        "fm_alarms": host_alarms,
                        "smapi_node": smapi_match,
                    },
                },
            })

        return generic