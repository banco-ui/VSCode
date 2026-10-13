"""OpenStack Provider Normalizer — Phase 26.

Transforms OpenStack RawProviderSnapshot into canonical entities by:
1. Transforming OpenStack raw payload → generic payload format
2. Delegating to GenericProviderNormalizer.normalize()

OpenStack → Canonical mapping rules (deterministic, no inference):

    Platform:
        OpenStack platform info → Platform(platform_type=OPENSTACK, version=...)
        ProviderType.OPENSTACK → PlatformType.OPENSTACK (explicit)

    Cluster:
        OpenStack Availability Zone → Cluster(cluster_type=OPENSTACK)

    Node:
        OpenStack Hypervisor → Node(name=hypervisor_hostname, cluster_ref=az_pid)
        provider_id = hypervisor_hostname

    Server (VM):
        OpenStack Server → ExecutionEnvironment(ee_type=VM, name=server_name)
        provider_id = Server id
        node_ref = OS-EXT-SRV-ATTR:hypervisor_hostname (if present)

    Network:
        OpenStack Network → Network(network_type=VIRTUAL, name=network_name)

    Volume:
        OpenStack Volume → Storage(storage_type=VOLUME, name=volume_name)

    NOT created:
        - Physical (no hardware identity from OpenStack API)
        - OS (no host OS info from OpenStack API)
        - Workload (no workload concept in OpenStack)
        - Accelerator (no GPU info from OpenStack API)
"""
from __future__ import annotations

from typing import Any

from server_manager.models.canonical import ProviderType
from server_manager.normalizers.provider_normalizer import (
    GenericProviderNormalizer,
    NormalizationResult,
)
from server_manager.providers import RawProviderSnapshot


class OpenStackProviderNormalizer(GenericProviderNormalizer):
    """OpenStack-specific provider normalizer.

    Transforms OpenStack RawProviderSnapshot into canonical entities by:
    1. Transforming OpenStack raw payload → generic payload format
    2. Delegating to GenericProviderNormalizer.normalize()

    This reuses all existing infrastructure:
    - CanonicalIdentityGenerator for canonical IDs
    - _make_source_evidence for provenance
    - _map_enum for enum mapping
    - _resolve_all_refs for ref resolution
    - _determine_status for result status
    """

    def __init__(self) -> None:
        super().__init__(ProviderType.OPENSTACK)

    def normalize(self, snapshot: RawProviderSnapshot) -> NormalizationResult:
        """Normalize an OpenStack snapshot into canonical entities.

        Transforms OpenStack raw payload → generic payload format, then
        delegates to GenericProviderNormalizer.normalize().

        Args:
            snapshot: RawProviderSnapshot with OpenStack raw data in payload.

        Returns:
            NormalizationResult with canonical entities.
        """
        generic_payload = self._transform_openstack_to_generic(snapshot)

        generic_snapshot = RawProviderSnapshot(
            snapshot_id=snapshot.snapshot_id,
            provider_type=snapshot.provider_type,
            provider_id=snapshot.provider_id,
            collected_at=snapshot.collected_at,
            collection_status=snapshot.collection_status,
            declared_capabilities=snapshot.declared_capabilities,
            capability_results=snapshot.capability_results,
            payload=generic_payload,
            relationship_evidence=snapshot.relationship_evidence,
            source_evidence=snapshot.source_evidence,
            errors=list(snapshot.errors),
            warnings=list(snapshot.warnings),
        )

        return super().normalize(generic_snapshot)

    def _transform_openstack_to_generic(
        self, snapshot: RawProviderSnapshot,
    ) -> dict[str, Any]:
        """Transform OpenStack raw payload to generic canonical payload.

        The GenericProviderNormalizer expects payload keys:
            platforms, clusters, nodes, execution_environments,
            workloads, networks, storages, accelerators, physicals, os

        Each item is a dict with provider_id and entity-specific fields.
        Refs are provider_id strings (resolved in second pass).

        OpenStack objects are preserved in metadata.openstack where appropriate.
        """
        payload = snapshot.payload
        platform_info = payload.get("platform", {})
        if not isinstance(platform_info, dict):
            platform_info = {}

        platform_name = platform_info.get("name", "openstack-cloud")
        platform_version = platform_info.get("version", "")
        platform_pid = f"platform-{platform_name}"

        generic: dict[str, Any] = {
            "platforms": [],
            "clusters": [],
            "nodes": [],
            "execution_environments": [],
            "workloads": [],
            "networks": [],
            "storages": [],
            "accelerators": [],
            "physicals": [],
            "os": [],
        }

        # ── Platform: OpenStack → Platform(OPENSTACK) ───────────────
        generic["platforms"].append({
            "provider_id": platform_pid,
            "platform_type": "OPENSTACK",
            "version": platform_version,
            "metadata": {
                "openstack": {
                    "name": platform_name,
                    "version": platform_version,
                },
            },
        })

        # ── Availability Zones → Clusters(OPENSTACK) ────────────────
        # Use platform as default cluster ref
        default_cluster_pid = platform_pid
        az_list = payload.get("availability_zones", [])
        if not isinstance(az_list, list):
            az_list = []

        az_pids: list[str] = []
        for az in az_list:
            if not isinstance(az, dict):
                continue
            az_name = az.get("zoneName", "")
            if not az_name:
                continue
            az_pid = f"az-{az_name}"
            az_pids.append(az_pid)
            generic["clusters"].append({
                "provider_id": az_pid,
                "cluster_type": "OPENSTACK",
                "platform_ref": platform_pid,
                "metadata": {
                    "openstack": {
                        "zone_name": az_name,
                        "zone_state": az.get("zoneState", {}),
                        "raw": az,
                    },
                },
            })

        # If no AZs found, create a default cluster for hypervisor refs
        if not az_pids:
            az_pids = [default_cluster_pid]

        # ── Hypervisors → Nodes ──────────────────────────────────────
        # provider_id = hypervisor_hostname (referenced by Server)
        for hv in payload.get("hypervisors", []):
            if not isinstance(hv, dict):
                continue
            hv_name = hv.get("hypervisor_hostname", "")
            if not hv_name:
                continue
            hv_id = hv.get("id", hv_name)
            # Assign to first AZ cluster (or default platform)
            cluster_ref = az_pids[0] if az_pids else default_cluster_pid
            generic["nodes"].append({
                "provider_id": hv_name,
                "name": hv_name,
                "cluster_ref": cluster_ref,
                "metadata": {
                    "openstack": {
                        "id": hv_id,
                        "state": hv.get("state", ""),
                        "status": hv.get("status", ""),
                        "vcpus": hv.get("vcpus"),
                        "memory_mb": hv.get("memory_mb"),
                        "local_gb": hv.get("local_gb"),
                        "vcpus_used": hv.get("vcpus_used"),
                        "memory_mb_used": hv.get("memory_mb_used"),
                        "local_gb_used": hv.get("local_gb_used"),
                        "raw": hv,
                    },
                },
            })

        # ── Servers → ExecutionEnvironment(VM) ───────────────────────
        # OpenStack Server → EE(type=VM)
        # provider_id = Server id
        # node_ref = OS-EXT-SRV-ATTR:hypervisor_hostname (if present)
        for server in payload.get("servers", []):
            if not isinstance(server, dict):
                continue
            server_id = server.get("id", "")
            if not server_id:
                continue

            server_name = server.get("name", "")
            hv_host = server.get("OS-EXT-SRV-ATTR:hypervisor_hostname")

            ee_item: dict[str, Any] = {
                "provider_id": server_id,
                "ee_type": "VM",
                "name": server_name,
                "metadata": {
                    "openstack": {
                        "id": server_id,
                        "name": server_name,
                        "status": server.get("status", ""),
                        "flavor": server.get("flavor", {}),
                        "addresses": server.get("addresses", {}),
                        "raw": server,
                    },
                },
            }
            if hv_host:
                ee_item["node_ref"] = hv_host
            generic["execution_environments"].append(ee_item)

        # ── Networks → Network(VIRTUAL) ─────────────────────────────
        for net in payload.get("networks", []):
            if not isinstance(net, dict):
                continue
            net_id = net.get("id", "")
            if not net_id:
                continue
            net_name = net.get("name", "")
            generic["networks"].append({
                "provider_id": net_id,
                "network_type": "VIRTUAL",
                "name": net_name,
                "metadata": {
                    "openstack": {
                        "id": net_id,
                        "name": net_name,
                        "status": net.get("status", ""),
                        "provider_network_type": net.get("provider:network_type", ""),
                        "raw": net,
                    },
                },
            })

        # ── Volumes → Storage(VOLUME) ───────────────────────────────
        for vol in payload.get("volumes", []):
            if not isinstance(vol, dict):
                continue
            vol_id = vol.get("id", "")
            if not vol_id:
                continue
            vol_name = vol.get("name", "")
            generic["storages"].append({
                "provider_id": vol_id,
                "storage_type": "VOLUME",
                "name": vol_name,
                "metadata": {
                    "openstack": {
                        "id": vol_id,
                        "name": vol_name,
                        "status": vol.get("status", ""),
                        "size": vol.get("size"),
                        "attachments": vol.get("attachments", []),
                        "raw": vol,
                    },
                },
            })

        # Flavors, images, projects are NOT mapped to canonical entities.
        # They are preserved in the raw payload for future use.
        # No Physical, OS, Accelerator, or Workload entities are created.

        return generic
